"""Tests for evidence-aware report sections."""

from __future__ import annotations

from unittest.mock import MagicMock

from insights.evidence.entities import (
    EvidenceItem,
    EvidenceRegistry,
    ExecutionRisk,
    TechnicalClaim,
)
from insights.sections.claim_register import ClaimRegisterSection
from insights.sections.evidence_pack import EvidencePackSection
from insights.sections.risk_register import RiskRegisterSection
from insights.sections.sampling_rationale import SamplingRationaleSection


def _make_evidence(eid: str = "E-CCN-001", cat: str = "complexity") -> EvidenceItem:
    return EvidenceItem(
        evidence_id=eid,
        evidence_type="test",
        category=cat,  # type: ignore[arg-type]
        location="src/file.py",
        excerpt="test excerpt",
        observation="test observation",
        why_it_matters="test reason",
        tool_source="test-tool",
        run_pk=1,
    )


def _make_claim(cid: str = "CLM-COUP-001", eids: tuple[str, ...] = ("E-CCN-001",)) -> TechnicalClaim:
    return TechnicalClaim(
        claim_id=cid,
        category="coupling",
        statement="Test coupling claim",
        evidence_ids=eids,
        implication="Test implication",
        confidence="high",
        triggered_by="TestRule",
    )


def _make_risk(rid: str = "RISK-001", cids: tuple[str, ...] = ("CLM-COUP-001",)) -> ExecutionRisk:
    return ExecutionRisk(
        risk_id=rid,
        description="Test risk description",
        technical_cause="Test cause",
        claim_ids=cids,
        manifests_in=("src/file.py",),
        triggered_by="TestPattern",
        severity="high",
    )


def _make_registry() -> EvidenceRegistry:
    ev = _make_evidence()
    claim = _make_claim()
    risk = _make_risk()
    return EvidenceRegistry(evidence=[ev], claims=[claim], risks=[risk])


def _mock_fetcher() -> MagicMock:
    fetcher = MagicMock()
    fetcher.fetch.return_value = []
    return fetcher


# ---------------------------------------------------------------------------
# RiskRegisterSection
# ---------------------------------------------------------------------------


class TestRiskRegisterSection:
    def test_fetch_data_with_registry(self):
        section = RiskRegisterSection()
        section.set_evidence_registry(_make_registry())
        data = section.fetch_data(_mock_fetcher(), 1)
        assert data["has_data"] is True
        assert data["total_risks"] == 1
        assert len(data["risks"]) == 1

    def test_fetch_data_without_registry(self):
        section = RiskRegisterSection()
        data = section.fetch_data(_mock_fetcher(), 1)
        assert data["has_data"] is False



# ---------------------------------------------------------------------------
# EvidencePackSection
# ---------------------------------------------------------------------------


class TestEvidencePackSection:
    def test_fetch_data_with_registry(self):
        section = EvidencePackSection()
        section.set_evidence_registry(_make_registry())
        data = section.fetch_data(_mock_fetcher(), 1)
        assert data["has_data"] is True
        assert data["total_evidence"] == 1
        assert len(data["categories"]) == 10  # all 10 categories

    def test_categories_include_items(self):
        section = EvidencePackSection()
        section.set_evidence_registry(_make_registry())
        data = section.fetch_data(_mock_fetcher(), 1)
        complexity_cat = next(c for c in data["categories"] if c["category"] == "complexity")
        assert complexity_cat["total_count"] == 1
        assert len(complexity_cat["evidence_items"]) == 1


# ---------------------------------------------------------------------------
# ClaimRegisterSection
# ---------------------------------------------------------------------------


class TestClaimRegisterSection:
    def test_fetch_data_with_registry(self):
        section = ClaimRegisterSection()
        section.set_evidence_registry(_make_registry())
        data = section.fetch_data(_mock_fetcher(), 1)
        assert data["has_data"] is True
        assert data["total_claims"] == 1
        assert data["confidence_distribution"]["high"] == 1

    def test_fetch_data_without_registry(self):
        section = ClaimRegisterSection()
        data = section.fetch_data(_mock_fetcher(), 1)
        assert data["has_data"] is False


# ---------------------------------------------------------------------------
# SamplingRationaleSection
# ---------------------------------------------------------------------------


class TestSamplingRationaleSection:
    def test_fetch_data_with_targets(self):
        section = SamplingRationaleSection()
        section.set_evidence_registry(_make_registry())
        fetcher = MagicMock()
        fetcher.fetch.return_value = [
            {
                "relative_path": "src/heavy.py",
                "composite_score": 0.85,
                "ccn_score": 0.9,
                "coupling_score": 0.8,
                "ownership_score": 0.7,
                "coverage_score": 0.6,
                "quality_score": 0.5,
            },
        ]
        data = section.fetch_data(fetcher, 1)
        assert data["has_data"] is True
        assert data["target_count"] == 1
        assert "complexity" in data["formula"]

    def test_fetch_data_empty(self):
        section = SamplingRationaleSection()
        section.set_evidence_registry(EvidenceRegistry())
        data = section.fetch_data(_mock_fetcher(), 1)
        assert data["has_data"] is False

    def test_rationale_text(self):
        section = SamplingRationaleSection()
        section.set_evidence_registry(_make_registry())
        fetcher = MagicMock()
        fetcher.fetch.return_value = [
            {
                "relative_path": "src/file.py",
                "composite_score": 0.9,
                "ccn_score": 0.9,
                "coupling_score": 0.1,
                "ownership_score": 0.1,
                "coverage_score": 0.1,
                "quality_score": 0.1,
            },
        ]
        data = section.fetch_data(fetcher, 1)
        assert "high complexity" in data["targets"][0]["rationale"]
