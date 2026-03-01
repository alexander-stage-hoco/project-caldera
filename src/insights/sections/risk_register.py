"""Risk register section — aggregated execution risks grouped by severity."""

from __future__ import annotations

from typing import Any

from ..data_fetcher import DataFetcher
from .base import EvidenceAwareSection, SectionConfig


class RiskRegisterSection(EvidenceAwareSection):
    """Renders execution risks with technical causes and supporting claims."""

    config = SectionConfig(
        name="risk_register",
        title="Risk Register",
        description="Execution risks derived from auditable evidence and claims.",
        priority=1,  # Right after executive summary
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Collects execution risks from the evidence registry and organizes them by severity for template rendering.
        
        Returns:
            data (dict[str, Any]): A mapping with the following keys:
                - risks: List of risk entries in order of severity: "critical", "high", "medium", "low".
                - risks_by_severity: Dict mapping each severity ("critical", "high", "medium", "low") to a list of risk entries.
                - summary: Summary object returned by the evidence registry (e.g., totals for evidence, claims, risks).
                - total_risks: Total number of risks found.
                - critical_count: Number of risks with severity "critical".
                - high_count: Number of risks with severity "high".
                - medium_count: Number of risks with severity "medium".
                - low_count: Number of risks with severity "low".
                - has_data: `True` if any risks were found, `False` otherwise.
                - has_critical: `True` if any critical risks were found, `False` otherwise.
        
            Each risk entry is a dict containing:
                - risk_id: Risk identifier.
                - description: Human-readable description of the risk.
                - technical_cause: Technical root cause or explanation.
                - severity: Severity string ("critical", "high", "medium", "low").
                - triggered_by: Source or trigger for the risk.
                - claim_count: Number of associated claim IDs.
                - manifests_in: List (up to 5 items) of where the risk manifests.
                - owner: Owner of the risk.
                - action: Recommended or assigned action.
                - sla_date: SLA or target date related to the action.
                - status: Current status of the risk/action.
                - claims: List (up to 5) of supporting claims, each a dict with `claim_id`, `statement`, and `confidence`.
        """
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
            by_severity[risk.severity].append(entry)

        return {
            "risks": [r for sev in ("critical", "high", "medium", "low") for r in by_severity[sev]],
            "risks_by_severity": by_severity,
            "summary": summary,
            "total_risks": len(risks),
            "critical_count": len(by_severity["critical"]),
            "high_count": len(by_severity["high"]),
            "medium_count": len(by_severity["medium"]),
            "low_count": len(by_severity["low"]),
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
