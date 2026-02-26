"""Tests for RiskAggregator."""

from __future__ import annotations

import pytest

from insights.evidence.entities import EvidenceItem, ExecutionRisk, TechnicalClaim
from insights.evidence.risk_aggregator import RiskAggregator, RiskPattern


def _claim(cid: str, category: str, eids: tuple[str, ...] = ("E-CCN-001",)) -> TechnicalClaim:
    return TechnicalClaim(
        claim_id=cid,
        category=category,
        statement=f"Test claim {cid}",
        evidence_ids=eids,
        implication="Test implication",
        confidence="high",
        triggered_by="TestRule",
    )


def _evidence(eid: str, cat: str, location: str = "src/file.py") -> EvidenceItem:
    return EvidenceItem(
        evidence_id=eid,
        evidence_type="test",
        category=cat,  # type: ignore[arg-type]
        location=location,
        excerpt="test",
        observation="test",
        why_it_matters="test",
        tool_source="test-tool",
        run_pk=1,
    )


class TestRiskAggregator:
    def test_no_risks_when_insufficient_claims(self):
        agg = RiskAggregator()
        claims = [_claim("CLM-COUP-001", "coupling")]
        # Change amplification requires min 2 claims
        risks = agg.aggregate(claims)
        # Should NOT produce change amplification risk
        change_risks = [r for r in risks if "amplification" in r.description.lower()]
        assert len(change_risks) == 0

    def test_security_risk_fires_with_one_claim(self):
        agg = RiskAggregator()
        claims = [_claim("CLM-SECX-001", "security")]
        risks = agg.aggregate(claims)
        assert len(risks) >= 1
        sec_risks = [r for r in risks if r.severity == "critical"]
        assert len(sec_risks) == 1

    def test_change_amplification_requires_two(self):
        agg = RiskAggregator()
        claims = [
            _claim("CLM-COUP-001", "coupling"),
            _claim("CLM-COUP-002", "coupling"),
        ]
        risks = agg.aggregate(claims)
        change_risks = [r for r in risks if "coupling" in r.technical_cause.lower()]
        assert len(change_risks) == 1
        assert change_risks[0].severity == "high"

    def test_manifests_in_populated(self):
        agg = RiskAggregator()
        ev1 = _evidence("E-SEC-001", "security", "src/server.py")
        claims = [_claim("CLM-SECX-001", "security", ("E-SEC-001",))]
        risks = agg.aggregate(claims, evidence=[ev1])
        assert len(risks) >= 1
        sec_risk = [r for r in risks if r.severity == "critical"][0]
        assert "src/server.py" in sec_risk.manifests_in

    def test_severity_escalation(self):
        """Many claims should escalate severity."""
        agg = RiskAggregator()
        # Create 9 ownership claims (min 2 * 3 = 6 for escalation)
        claims = [
            _claim(f"CLM-SILO-{i:03d}", "ownership")
            for i in range(1, 10)
        ]
        risks = agg.aggregate(claims)
        own_risks = [r for r in risks if "bus factor" in r.description.lower()]
        assert len(own_risks) == 1
        assert own_risks[0].severity == "critical"  # escalated from high

    def test_custom_pattern(self):
        pattern = RiskPattern(
            name="Custom",
            description="Custom risk",
            technical_cause="Custom cause",
            categories=("quality",),
            min_claims=1,
            default_severity="low",
        )
        agg = RiskAggregator(patterns=(pattern,))
        claims = [_claim("CLM-DEBT-001", "quality")]
        risks = agg.aggregate(claims)
        assert len(risks) == 1
        assert risks[0].severity == "low"
        assert risks[0].triggered_by == "Custom"

    def test_empty_claims_produce_no_risks(self):
        agg = RiskAggregator()
        risks = agg.aggregate([])
        assert risks == []
