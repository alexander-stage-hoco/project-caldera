"""Tests for EvidenceRegistryBuilder."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from insights.evidence.builder import EvidenceRegistryBuilder
from insights.evidence.claim_generator import ClaimGenerator
from insights.evidence.collector import EvidenceCollector
from insights.evidence.entities import (
    EvidenceItem,
    EvidenceRegistry,
    ExecutionRisk,
    TechnicalClaim,
)
from insights.evidence.risk_aggregator import RiskAggregator


def _evidence(eid: str, cat: str, location: str = "src/file.py") -> EvidenceItem:
    return EvidenceItem(
        evidence_id=eid,
        evidence_type="test",
        category=cat,  # type: ignore[arg-type]
        location=location,
        excerpt="test excerpt",
        observation="test",
        why_it_matters="test",
        tool_source="test-tool",
        run_pk=1,
    )


def _claim(cid: str, cat: str, eids: tuple[str, ...] = ("E-CCN-001",)) -> TechnicalClaim:
    return TechnicalClaim(
        claim_id=cid,
        category=cat,
        statement=f"Test claim {cid}",
        evidence_ids=eids,
        implication="Test implication",
        confidence="high",
        triggered_by="TestRule",
    )


def _risk(rid: str, cids: tuple[str, ...] = ("CLM-COUP-001",)) -> ExecutionRisk:
    return ExecutionRisk(
        risk_id=rid,
        description="Test risk",
        technical_cause="Test cause",
        claim_ids=cids,
        manifests_in=("src/file.py",),
        triggered_by="TestPattern",
        severity="high",
    )


class TestEvidenceRegistryBuilder:
    def test_happy_path(self):
        """Full pipeline: collector → claims → risks → populated registry."""
        evidence = [_evidence("E-CCN-001", "complexity")]
        claims = [_claim("CLM-COUP-001", "coupling")]
        risks = [_risk("RISK-001")]

        collector = MagicMock(spec=EvidenceCollector)
        collector.collect.return_value = evidence

        generator = MagicMock(spec=ClaimGenerator)
        generator.generate.return_value = claims

        aggregator = MagicMock(spec=RiskAggregator)
        aggregator.aggregate.return_value = risks

        builder = EvidenceRegistryBuilder(
            collector=collector,
            claim_generator=generator,
            risk_aggregator=aggregator,
        )
        fetcher = MagicMock()
        registry = builder.build(fetcher, run_pk=1)

        assert len(registry.evidence) == 1
        assert len(registry.claims) == 1
        assert len(registry.risks) == 1
        collector.collect.assert_called_once_with(fetcher, 1)
        generator.generate.assert_called_once_with(evidence, fetcher, 1)
        aggregator.aggregate.assert_called_once_with(claims, evidence)

    def test_collector_failure_returns_empty_registry(self):
        """If collector raises, return empty registry — no crash."""
        collector = MagicMock(spec=EvidenceCollector)
        collector.collect.side_effect = RuntimeError("DB down")

        builder = EvidenceRegistryBuilder(collector=collector)
        fetcher = MagicMock()

        with pytest.warns(UserWarning, match="Evidence collection failed"):
            registry = builder.build(fetcher, run_pk=1)

        assert len(registry.evidence) == 0
        assert len(registry.claims) == 0
        assert len(registry.risks) == 0

    def test_claim_generator_failure_keeps_evidence(self):
        """If claim generation fails, registry has evidence but no claims/risks."""
        evidence = [_evidence("E-CCN-001", "complexity")]

        collector = MagicMock(spec=EvidenceCollector)
        collector.collect.return_value = evidence

        generator = MagicMock(spec=ClaimGenerator)
        generator.generate.side_effect = RuntimeError("rule exploded")

        aggregator = MagicMock(spec=RiskAggregator)
        aggregator.aggregate.return_value = []

        builder = EvidenceRegistryBuilder(
            collector=collector,
            claim_generator=generator,
            risk_aggregator=aggregator,
        )
        fetcher = MagicMock()

        with pytest.warns(UserWarning, match="Claim generation failed"):
            registry = builder.build(fetcher, run_pk=1)

        assert len(registry.evidence) == 1
        assert len(registry.claims) == 0
        # aggregator still called with empty claims
        aggregator.aggregate.assert_called_once_with([], evidence)

    def test_risk_aggregator_failure_keeps_evidence_and_claims(self):
        """If risk aggregation fails, registry has evidence + claims but no risks."""
        evidence = [_evidence("E-CCN-001", "complexity")]
        claims = [_claim("CLM-COUP-001", "coupling")]

        collector = MagicMock(spec=EvidenceCollector)
        collector.collect.return_value = evidence

        generator = MagicMock(spec=ClaimGenerator)
        generator.generate.return_value = claims

        aggregator = MagicMock(spec=RiskAggregator)
        aggregator.aggregate.side_effect = RuntimeError("aggregation boom")

        builder = EvidenceRegistryBuilder(
            collector=collector,
            claim_generator=generator,
            risk_aggregator=aggregator,
        )
        fetcher = MagicMock()

        with pytest.warns(UserWarning, match="Risk aggregation failed"):
            registry = builder.build(fetcher, run_pk=1)

        assert len(registry.evidence) == 1
        assert len(registry.claims) == 1
        assert len(registry.risks) == 0

    def test_custom_injection(self):
        """Custom collector/generator/aggregator are used when injected."""
        collector = MagicMock(spec=EvidenceCollector)
        collector.collect.return_value = []

        generator = MagicMock(spec=ClaimGenerator)
        generator.generate.return_value = []

        aggregator = MagicMock(spec=RiskAggregator)
        aggregator.aggregate.return_value = []

        builder = EvidenceRegistryBuilder(
            collector=collector,
            claim_generator=generator,
            risk_aggregator=aggregator,
        )
        fetcher = MagicMock()
        builder.build(fetcher, run_pk=42)

        collector.collect.assert_called_once_with(fetcher, 42)
        generator.generate.assert_called_once()
        aggregator.aggregate.assert_called_once()

    def test_empty_data_returns_valid_registry(self):
        """No data from any query → empty but valid registry."""
        builder = EvidenceRegistryBuilder()
        fetcher = MagicMock()
        fetcher.fetch.return_value = []

        registry = builder.build(fetcher, run_pk=1)

        assert isinstance(registry, EvidenceRegistry)
        assert len(registry.evidence) == 0
        assert len(registry.claims) == 0
        assert len(registry.risks) == 0
        summary = registry.summary()
        assert summary["total_evidence"] == 0

    def test_defaults_create_real_instances(self):
        """Without injection, builder creates real Collector/Generator/Aggregator."""
        builder = EvidenceRegistryBuilder()
        assert isinstance(builder._collector, EvidenceCollector)
        assert isinstance(builder._claim_generator, ClaimGenerator)
        assert isinstance(builder._risk_aggregator, RiskAggregator)
