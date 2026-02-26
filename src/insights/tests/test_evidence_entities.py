"""Tests for Evidence & Claim framework entities."""

from __future__ import annotations

import pytest

from insights.evidence.entities import (
    EvidenceItem,
    EvidenceRegistry,
    ExecutionRisk,
    TechnicalClaim,
)


# ---------------------------------------------------------------------------
# EvidenceItem
# ---------------------------------------------------------------------------


class TestEvidenceItem:
    def _make(self, **overrides) -> EvidenceItem:
        defaults = {
            "evidence_id": "E-CCN-001",
            "evidence_type": "file_complexity",
            "category": "complexity",
            "location": "src/main.py",
            "excerpt": "max_ccn=25",
            "observation": "High CCN",
            "why_it_matters": "Hard to test",
            "tool_source": "lizard",
            "run_pk": 1,
        }
        defaults.update(overrides)
        return EvidenceItem(**defaults)

    def test_valid_creation(self):
        item = self._make()
        assert item.evidence_id == "E-CCN-001"
        assert item.category == "complexity"

    def test_frozen(self):
        item = self._make()
        with pytest.raises(AttributeError):
            item.location = "other.py"  # type: ignore[misc]

    def test_invalid_id_format(self):
        with pytest.raises(ValueError, match="evidence_id must match"):
            self._make(evidence_id="BAD-ID")

    def test_invalid_category(self):
        with pytest.raises(ValueError, match="Invalid evidence category"):
            self._make(category="nonexistent")  # type: ignore[arg-type]

    def test_empty_location(self):
        with pytest.raises(ValueError, match="location must not be empty"):
            self._make(location="")

    def test_empty_tool_source(self):
        with pytest.raises(ValueError, match="tool_source must not be empty"):
            self._make(tool_source="")


# ---------------------------------------------------------------------------
# TechnicalClaim
# ---------------------------------------------------------------------------


class TestTechnicalClaim:
    def _make(self, **overrides) -> TechnicalClaim:
        defaults = {
            "claim_id": "CLM-COUP-001",
            "category": "coupling",
            "statement": "Module X exhibits high coupling",
            "evidence_ids": ("E-COUP-001",),
            "implication": "Change amplification",
            "confidence": "high",
            "triggered_by": "HighCouplingRule",
        }
        defaults.update(overrides)
        return TechnicalClaim(**defaults)

    def test_valid_creation(self):
        claim = self._make()
        assert claim.claim_id == "CLM-COUP-001"

    def test_frozen(self):
        claim = self._make()
        with pytest.raises(AttributeError):
            claim.statement = "other"  # type: ignore[misc]

    def test_invalid_id_format(self):
        with pytest.raises(ValueError, match="claim_id must match"):
            self._make(claim_id="BAD")

    def test_empty_evidence_ids(self):
        with pytest.raises(ValueError, match="at least one evidence_id"):
            self._make(evidence_ids=())

    def test_empty_statement(self):
        with pytest.raises(ValueError, match="statement must not be empty"):
            self._make(statement="")


# ---------------------------------------------------------------------------
# ExecutionRisk
# ---------------------------------------------------------------------------


class TestExecutionRisk:
    def _make(self, **overrides) -> ExecutionRisk:
        defaults = {
            "risk_id": "RISK-001",
            "description": "Security exposure",
            "technical_cause": "Unpatched deps",
            "claim_ids": ("CLM-SECX-001",),
            "manifests_in": ("src/server.py",),
            "triggered_by": "SecurityExposurePattern",
            "severity": "critical",
        }
        defaults.update(overrides)
        return ExecutionRisk(**defaults)

    def test_valid_creation(self):
        risk = self._make()
        assert risk.risk_id == "RISK-001"

    def test_frozen(self):
        risk = self._make()
        with pytest.raises(AttributeError):
            risk.severity = "low"  # type: ignore[misc]

    def test_invalid_id(self):
        with pytest.raises(ValueError, match="risk_id must match"):
            self._make(risk_id="R-1")

    def test_empty_claims(self):
        with pytest.raises(ValueError, match="at least one claim_id"):
            self._make(claim_ids=())


# ---------------------------------------------------------------------------
# EvidenceRegistry
# ---------------------------------------------------------------------------


class TestEvidenceRegistry:
    def _make_evidence(self, eid: str = "E-CCN-001", cat: str = "complexity") -> EvidenceItem:
        return EvidenceItem(
            evidence_id=eid,
            evidence_type="test",
            category=cat,  # type: ignore[arg-type]
            location="src/file.py",
            excerpt="test",
            observation="test obs",
            why_it_matters="test reason",
            tool_source="test-tool",
            run_pk=1,
        )

    def _make_claim(self, cid: str = "CLM-COUP-001", eids: tuple[str, ...] = ("E-CCN-001",)) -> TechnicalClaim:
        return TechnicalClaim(
            claim_id=cid,
            category="coupling",
            statement="Test claim",
            evidence_ids=eids,
            implication="Test implication",
            confidence="high",
            triggered_by="TestRule",
        )

    def test_empty_registry(self):
        reg = EvidenceRegistry()
        assert reg.evidence == []
        assert reg.claims == []
        assert reg.risks == []

    def test_lookup_by_id(self):
        ev = self._make_evidence()
        reg = EvidenceRegistry(evidence=[ev])
        assert reg.evidence_by_id("E-CCN-001") is ev
        assert reg.evidence_by_id("E-CCN-999") is None

    def test_filter_by_category(self):
        ev1 = self._make_evidence("E-CCN-001", "complexity")
        ev2 = self._make_evidence("E-SEC-001", "security")
        reg = EvidenceRegistry(evidence=[ev1, ev2])
        assert len(reg.evidence_by_category("complexity")) == 1
        assert len(reg.evidence_by_category("security")) == 1
        assert len(reg.evidence_by_category("coupling")) == 0

    def test_evidence_for_claim(self):
        ev = self._make_evidence("E-CCN-001")
        claim = self._make_claim("CLM-COUP-001", ("E-CCN-001",))
        reg = EvidenceRegistry(evidence=[ev], claims=[claim])
        linked = reg.evidence_for_claim(claim)
        assert len(linked) == 1
        assert linked[0] is ev

    def test_add_evidence(self):
        reg = EvidenceRegistry()
        ev = self._make_evidence()
        reg.add_evidence(ev)
        assert len(reg.evidence) == 1
        assert reg.evidence_by_id("E-CCN-001") is ev

    def test_summary(self):
        ev = self._make_evidence()
        reg = EvidenceRegistry(evidence=[ev])
        s = reg.summary()
        assert s["total_evidence"] == 1
        assert s["evidence_by_category"]["complexity"] == 1
