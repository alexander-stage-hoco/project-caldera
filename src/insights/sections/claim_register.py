"""Claim register section — all technical claims grouped by category."""

from __future__ import annotations

from typing import Any

from ..data_fetcher import DataFetcher
from .base import EvidenceAwareSection, SectionConfig


class ClaimRegisterSection(EvidenceAwareSection):
    """Renders claims grouped by category with evidence linkage."""

    config = SectionConfig(
        name="claim_register",
        title="Claim Register",
        description="Technical claims derived from evidence, grouped by category with confidence.",
        priority=99,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        registry = self._evidence_registry
        if not registry:
            return self.get_fallback_data()

        summary = registry.summary()
        categories_data: list[dict[str, Any]] = []

        for cat in ("security", "complexity", "coupling", "ownership", "coverage", "quality"):
            claims = registry.claims_by_category(cat)
            if not claims:
                continue

            claim_entries = []
            for c in claims:
                entry: dict[str, Any] = {
                    "claim_id": c.claim_id,
                    "statement": c.statement,
                    "confidence": c.confidence,
                    "triggered_by": c.triggered_by,
                    "implication": c.implication,
                    "evidence_count": len(c.evidence_ids),
                    "evidence_ids": list(c.evidence_ids[:5]),
                }
                evaluation = registry.evaluation_for(c.claim_id)
                if evaluation:
                    entry["validation_score"] = evaluation.score
                    entry["validation_reasoning"] = evaluation.reasoning
                claim_entries.append(entry)

            categories_data.append({
                "category": cat,
                "claim_count": len(claims),
                "claims": claim_entries,
            })

        # Confidence distribution
        all_claims = registry.claims
        confidence_dist = {
            "high": sum(1 for c in all_claims if c.confidence == "high"),
            "medium": sum(1 for c in all_claims if c.confidence == "medium"),
            "low": sum(1 for c in all_claims if c.confidence == "low"),
        }

        validation_summary = registry.validation_summary()

        eval_quality_passed = None
        if registry.eval_quality is not None:
            eval_quality_passed = registry.eval_quality.passed

        return {
            "categories": categories_data,
            "summary": summary,
            "total_claims": summary["total_claims"],
            "confidence_distribution": confidence_dist,
            "validation_summary": validation_summary,
            "eval_quality_passed": eval_quality_passed,
            "has_data": summary["total_claims"] > 0,
        }

    def get_template_name(self) -> str:
        return "claim_register.html.j2"

    def get_fallback_data(self) -> dict[str, Any]:
        return {
            "categories": [],
            "summary": {"total_evidence": 0, "total_claims": 0, "total_risks": 0},
            "total_claims": 0,
            "confidence_distribution": {"high": 0, "medium": 0, "low": 0},
            "has_data": False,
        }
