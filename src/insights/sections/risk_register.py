"""Risk register section — aggregated execution risks grouped by severity."""

from __future__ import annotations

from typing import Any

from ..data_fetcher import DataFetcher
from ..evidence.evaluator import extract_narrative
from .base import EvidenceAwareSection, NarrativeAwareSection, SectionConfig


class RiskRegisterSection(NarrativeAwareSection, EvidenceAwareSection):
    """Renders execution risks with technical causes and supporting claims."""

    config = SectionConfig(
        name="risk_register",
        title="Risk Register",
        description="Execution risks derived from auditable evidence and claims.",
        priority=1,  # Right after executive summary
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        registry = self._evidence_registry
        if not registry:
            return self.get_fallback_data()

        risks = registry.risks
        summary = registry.summary()

        # Group risks by severity
        by_severity: dict[str, list[dict[str, Any]]] = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
        }

        enriched_count = 0
        for risk in risks:
            supporting_claims = registry.claims_for_risk(risk)
            entry: dict[str, Any] = {
                "risk_id": risk.risk_id,
                "description": risk.description,
                "technical_cause": risk.technical_cause,
                "severity": risk.severity,
                "triggered_by": risk.triggered_by,
                "claim_count": len(risk.claim_ids),
                "manifests_in": list(risk.manifests_in[:5]),
                "owner": risk.owner,
                "action": risk.action,
                "sla_date": risk.sla_date,
                "status": risk.status,
                "claims": [
                    {
                        "claim_id": c.claim_id,
                        "statement": c.statement,
                        "confidence": c.confidence,
                    }
                    for c in supporting_claims[:5]
                ],
            }

            # Use evaluation narrative if available, fall back to enricher
            evaluation = registry.evaluation_for(risk.risk_id)
            if evaluation:
                entry["coherence_score"] = evaluation.score
                narrative = extract_narrative(evaluation)
                if narrative:
                    entry["description_narrative"] = narrative
                enriched_count += 1
            elif self._enricher and enriched_count < 5:
                narrative = self._enricher.enrich(
                    task=(
                        "Rewrite this risk description in 2 sentences, citing specific "
                        "files, CVE IDs, and metric values from the claims."
                    ),
                    data={
                        "risk_name": risk.triggered_by,
                        "generic_description": risk.description,
                        "severity": risk.severity,
                        "manifests_in": list(risk.manifests_in[:5]),
                        "supporting_claims": [c["statement"] for c in entry["claims"]],
                    },
                    max_tokens=150,
                )
                if narrative:
                    entry["description_narrative"] = narrative
                enriched_count += 1

            by_severity[risk.severity].append(entry)

        eval_quality_passed = None
        if registry.eval_quality is not None:
            eval_quality_passed = registry.eval_quality.passed

        return {
            "risks": [r for sev in ("critical", "high", "medium", "low") for r in by_severity[sev]],
            "risks_by_severity": by_severity,
            "summary": summary,
            "total_risks": len(risks),
            "critical_count": len(by_severity["critical"]),
            "high_count": len(by_severity["high"]),
            "medium_count": len(by_severity["medium"]),
            "low_count": len(by_severity["low"]),
            "eval_quality_passed": eval_quality_passed,
            "has_data": len(risks) > 0,
            "has_critical": len(by_severity["critical"]) > 0,
        }

    def get_template_name(self) -> str:
        return "risk_register.html.j2"

    def get_fallback_data(self) -> dict[str, Any]:
        return {
            "risks": [],
            "risks_by_severity": {"critical": [], "high": [], "medium": [], "low": []},
            "summary": {"total_evidence": 0, "total_claims": 0, "total_risks": 0},
            "total_risks": 0,
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "has_data": False,
            "has_critical": False,
        }
