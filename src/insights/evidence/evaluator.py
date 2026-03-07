"""EvidenceEvaluator — LLM-as-judge for evidence quality, claim validity, and risk coherence.

Follows the NarrativeEnricher pattern: same provider infrastructure, ObservableProvider
wrapping, fail-gracefully-to-None semantics. Returns structured EvaluationScore objects
instead of free text.

Batching strategy keeps LLM calls to ~15-30 per run:
- Evidence quality: 1 call per category (sample of 10 items)
- Claim validation: 1 call per batch of 5 claims
- Risk coherence: 1 call per risk
"""

from __future__ import annotations

import json
import logging
import os
import uuid
import warnings
from pathlib import Path
from typing import Any

from .entities import (
    EvaluationScore,
    EvidenceItem,
    EvidenceRegistry,
    ExecutionRisk,
    TechnicalClaim,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a senior code analysis quality auditor. You evaluate the quality, "
    "validity, and coherence of findings from automated code analysis tools. "
    "Be precise and factual. Respond with only the requested JSON."
)

DEFAULT_MODEL = "claude-sonnet-4"
_PROMPTS_DIR = Path(__file__).parent / "prompts"

EVIDENCE_SAMPLE_SIZE = 10
CLAIM_BATCH_SIZE = 5


def _load_prompt(name: str) -> str:
    """Load a prompt template from the prompts directory."""
    return (_PROMPTS_DIR / f"{name}.txt").read_text()


def _render_prompt(template_text: str, **kwargs: Any) -> str:
    """Minimal Jinja2-like rendering using basic string replacement.

    Supports ``{{ var }}`` and simple ``{% for %}`` / ``{% if %}`` blocks
    via the Jinja2 engine.
    """
    from jinja2 import Environment

    env = Environment()
    tmpl = env.from_string(template_text)
    return tmpl.render(**kwargs)


class EvidenceEvaluator:
    """LLM-powered evaluator for evidence items, claims, and risks.

    Provider selection mirrors NarrativeEnricher:
    - If ``ANTHROPIC_API_KEY`` is set -> ``AnthropicAPIProvider``
    - Otherwise -> ``ClaudeCodeHeadlessProvider``
    """

    def __init__(self, trace_id: str | None = None) -> None:
        self._trace_id = trace_id or str(uuid.uuid4())
        self._provider = self._create_provider()

    def _create_provider(self) -> Any:
        """Create and wrap the LLM provider."""
        from ..evaluation.llm.providers import LLMProvider
        from ..evaluation.llm.observability.observable_provider import ObservableProvider

        provider: LLMProvider
        if os.environ.get("ANTHROPIC_API_KEY"):
            from ..evaluation.llm.providers.anthropic import AnthropicAPIProvider

            provider = AnthropicAPIProvider(model=DEFAULT_MODEL)
        else:
            from ..evaluation.llm.providers.claude_code import ClaudeCodeHeadlessProvider

            provider = ClaudeCodeHeadlessProvider(model=DEFAULT_MODEL)

        return ObservableProvider(
            provider=provider,
            trace_id=self._trace_id,
            judge_name="EvidenceEvaluator",
        )

    @property
    def trace_id(self) -> str:
        return self._trace_id

    def _call_llm(self, prompt: str, max_tokens: int = 512) -> dict[str, Any] | None:
        """Call the LLM and parse JSON response. Returns None on failure."""
        try:
            response = self._provider.complete(
                prompt=prompt,
                system=SYSTEM_PROMPT,
                model=DEFAULT_MODEL,
                temperature=0.2,
                max_tokens=max_tokens,
            )
            content = response.content.strip()
            if not content:
                return None
            # Strip markdown fencing if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
            return json.loads(content)
        except Exception as exc:
            warnings.warn(
                f"[EvidenceEvaluator] LLM call failed: {exc}",
                stacklevel=3,
            )
            logger.debug("EvidenceEvaluator failure details", exc_info=True)
            return None

    # -- Evidence Quality ---------------------------------------------------

    def evaluate_evidence_quality(
        self, registry: EvidenceRegistry,
    ) -> list[EvaluationScore]:
        """Evaluate evidence quality per category (1 LLM call each)."""
        from .entities import EVIDENCE_CATEGORIES

        scores: list[EvaluationScore] = []
        template = _load_prompt("evidence_quality")

        for cat in EVIDENCE_CATEGORIES:
            items = registry.evidence_by_category(cat)
            if not items:
                continue

            sample = items[:EVIDENCE_SAMPLE_SIZE]
            batch_id = f"evq-{cat}-{uuid.uuid4().hex[:8]}"

            prompt = _render_prompt(
                template,
                category=cat,
                total_in_category=len(items),
                items=[
                    {
                        "evidence_id": e.evidence_id,
                        "evidence_type": e.evidence_type,
                        "location": e.location,
                        "observation": e.observation,
                        "excerpt": e.excerpt,
                        "confidence": e.confidence,
                        "tool_source": e.tool_source,
                    }
                    for e in sample
                ],
            )

            result = self._call_llm(prompt, max_tokens=256)
            if result and "score" in result:
                scores.append(EvaluationScore(
                    entity_id=f"CAT-{cat.upper()}",
                    entity_type="evidence",
                    dimension="quality",
                    score=max(1, min(5, int(result["score"]))),
                    confidence=max(0.0, min(1.0, float(result.get("confidence", 0.7)))),
                    reasoning=result.get("reasoning"),
                    batch_id=batch_id,
                ))

        return scores

    # -- Claim Validation ---------------------------------------------------

    def evaluate_claim_validity(
        self, registry: EvidenceRegistry,
    ) -> list[EvaluationScore]:
        """Evaluate claim validity in batches of CLAIM_BATCH_SIZE."""
        all_claims = registry.claims
        if not all_claims:
            return []

        scores: list[EvaluationScore] = []
        template = _load_prompt("claim_validity")

        for i in range(0, len(all_claims), CLAIM_BATCH_SIZE):
            batch = all_claims[i : i + CLAIM_BATCH_SIZE]
            batch_id = f"clv-{uuid.uuid4().hex[:8]}"

            claims_data = []
            for c in batch:
                evidence_summaries = []
                for eid in c.evidence_ids[:3]:
                    ev = registry.evidence_by_id(eid)
                    if ev:
                        evidence_summaries.append({
                            "evidence_id": ev.evidence_id,
                            "observation": ev.observation,
                        })

                claims_data.append({
                    "claim_id": c.claim_id,
                    "category": c.category,
                    "confidence": c.confidence,
                    "statement": c.statement,
                    "implication": c.implication,
                    "triggered_by": c.triggered_by,
                    "evidence_count": len(c.evidence_ids),
                    "evidence_ids": ", ".join(c.evidence_ids[:5]),
                    "evidence_summaries": evidence_summaries,
                })

            prompt = _render_prompt(template, claims=claims_data)
            result = self._call_llm(prompt, max_tokens=512)

            if result and "evaluations" in result:
                for ev in result["evaluations"]:
                    cid = ev.get("claim_id", "")
                    if cid and registry.claim_by_id(cid):
                        scores.append(EvaluationScore(
                            entity_id=cid,
                            entity_type="claim",
                            dimension="validity",
                            score=max(1, min(5, int(ev.get("score", 3)))),
                            confidence=max(0.0, min(1.0, float(ev.get("confidence", 0.7)))),
                            reasoning=ev.get("reasoning"),
                            batch_id=batch_id,
                        ))

        return scores

    # -- Risk Coherence -----------------------------------------------------

    def evaluate_risk_coherence(
        self, registry: EvidenceRegistry,
    ) -> list[EvaluationScore]:
        """Evaluate risk coherence (1 LLM call per risk)."""
        risks = registry.risks
        if not risks:
            return []

        scores: list[EvaluationScore] = []
        template = _load_prompt("risk_coherence")

        for risk in risks:
            supporting_claims = registry.claims_for_risk(risk)
            batch_id = f"rsk-{uuid.uuid4().hex[:8]}"

            prompt = _render_prompt(
                template,
                risk={
                    "risk_id": risk.risk_id,
                    "severity": risk.severity,
                    "description": risk.description,
                    "technical_cause": risk.technical_cause,
                    "triggered_by": risk.triggered_by,
                    "manifests_in": ", ".join(risk.manifests_in[:5]),
                },
                claims=[
                    {
                        "claim_id": c.claim_id,
                        "confidence": c.confidence,
                        "statement": c.statement,
                    }
                    for c in supporting_claims[:5]
                ],
            )

            result = self._call_llm(prompt, max_tokens=384)
            if result and "score" in result:
                # Store narrative in reasoning field, prefixed for extraction
                reasoning = result.get("reasoning", "")
                narrative = result.get("narrative")
                if narrative:
                    reasoning = f"{reasoning}\n---\n{narrative}"

                scores.append(EvaluationScore(
                    entity_id=risk.risk_id,
                    entity_type="risk",
                    dimension="coherence",
                    score=max(1, min(5, int(result["score"]))),
                    confidence=max(0.0, min(1.0, float(result.get("confidence", 0.7)))),
                    reasoning=reasoning,
                    batch_id=batch_id,
                ))

        return scores

    # -- Orchestrator -------------------------------------------------------

    def evaluate_all(self, registry: EvidenceRegistry) -> list[EvaluationScore]:
        """Run all three evaluation dimensions and return combined scores."""
        all_scores: list[EvaluationScore] = []

        try:
            all_scores.extend(self.evaluate_evidence_quality(registry))
        except Exception as exc:
            warnings.warn(
                f"[EvidenceEvaluator] Evidence quality evaluation failed: {exc}",
                stacklevel=2,
            )

        try:
            all_scores.extend(self.evaluate_claim_validity(registry))
        except Exception as exc:
            warnings.warn(
                f"[EvidenceEvaluator] Claim validity evaluation failed: {exc}",
                stacklevel=2,
            )

        try:
            all_scores.extend(self.evaluate_risk_coherence(registry))
        except Exception as exc:
            warnings.warn(
                f"[EvidenceEvaluator] Risk coherence evaluation failed: {exc}",
                stacklevel=2,
            )

        return all_scores


def extract_narrative(evaluation: EvaluationScore) -> str | None:
    """Extract the narrative portion from a risk coherence evaluation's reasoning."""
    if not evaluation or not evaluation.reasoning:
        return None
    if "\n---\n" in evaluation.reasoning:
        return evaluation.reasoning.split("\n---\n", 1)[1].strip() or None
    return None
