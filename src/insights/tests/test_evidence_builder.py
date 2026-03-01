"""Tests for EvidenceRegistryBuilder."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import duckdb
import pytest

from insights.evidence.builder import EvidenceRegistryBuilder
from insights.evidence.claim_generator import ClaimGenerator
from insights.evidence.collector import (
    CollectionResult,
    CollectorWarning,
    EvidenceCollector,
)
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
        collector.collect_with_warnings.return_value = CollectionResult(items=evidence)

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
        collector.collect_with_warnings.assert_called_once_with(fetcher, 1)
        generator.generate.assert_called_once_with(evidence, fetcher, 1)
        aggregator.aggregate.assert_called_once_with(claims, evidence)

    def test_collector_failure_returns_empty_registry(self):
        """If collector raises, return empty registry — no crash."""
        collector = MagicMock(spec=EvidenceCollector)
        collector.collect_with_warnings.side_effect = RuntimeError("DB down")

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
        collector.collect_with_warnings.return_value = CollectionResult(items=evidence)

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
        collector.collect_with_warnings.return_value = CollectionResult(items=evidence)

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
        """
        Verifies that injecting custom collector, claim generator, and risk aggregator causes their respective methods to be invoked when building the registry.
        
        This test constructs mocks for EvidenceCollector, ClaimGenerator, and RiskAggregator, injects them into EvidenceRegistryBuilder, calls build, and asserts that the collector's collect_with_warnings, the generator's generate, and the aggregator's aggregate methods are called.
        """
        collector = MagicMock(spec=EvidenceCollector)
        collector.collect_with_warnings.return_value = CollectionResult(items=[])

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

        collector.collect_with_warnings.assert_called_once_with(fetcher, 42)
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


# =========================================================================
# Evidence table DDLs for in-memory DuckDB
# =========================================================================

_EVIDENCE_DDLS = """
CREATE TABLE lz_evidence (
    collection_run_id VARCHAR NOT NULL,
    evidence_id VARCHAR NOT NULL,
    evidence_type VARCHAR NOT NULL,
    category VARCHAR NOT NULL,
    location VARCHAR NOT NULL,
    excerpt TEXT,
    observation TEXT,
    why_it_matters TEXT,
    tool_source VARCHAR NOT NULL,
    run_pk BIGINT NOT NULL,
    confidence VARCHAR NOT NULL DEFAULT 'high',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (collection_run_id, evidence_id)
);

CREATE TABLE lz_claims (
    collection_run_id VARCHAR NOT NULL,
    claim_id VARCHAR NOT NULL,
    category VARCHAR NOT NULL,
    statement TEXT NOT NULL,
    evidence_ids VARCHAR NOT NULL,
    implication TEXT,
    confidence VARCHAR NOT NULL,
    triggered_by VARCHAR NOT NULL,
    severity VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (collection_run_id, claim_id)
);

CREATE TABLE lz_risks (
    collection_run_id VARCHAR NOT NULL,
    risk_id VARCHAR NOT NULL,
    description TEXT NOT NULL,
    technical_cause TEXT,
    claim_ids VARCHAR NOT NULL,
    manifests_in VARCHAR,
    triggered_by VARCHAR NOT NULL,
    severity VARCHAR NOT NULL,
    owner VARCHAR,
    action TEXT,
    sla_date VARCHAR,
    status VARCHAR DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (collection_run_id, risk_id)
);

CREATE TABLE lz_warnings (
    collection_run_id VARCHAR NOT NULL,
    category VARCHAR NOT NULL,
    source VARCHAR NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


class TestEvidenceRegistryBuilderPersist:
    """Tests for EvidenceRegistryBuilder.persist() writing rows to DuckDB."""

    def _make_conn(self) -> duckdb.DuckDBPyConnection:
        """
        Create an in-memory DuckDB connection with the test schema initialized.
        
        Returns:
            duckdb.DuckDBPyConnection: A DuckDB connection pointing to an in-memory database where the required test tables and DDL from _EVIDENCE_DDLS have been executed.
        """
        conn = duckdb.connect(":memory:")
        conn.execute(_EVIDENCE_DDLS)
        return conn

    def test_persist_writes_correct_row_counts(self):
        """persist() writes evidence, claims, and risks to their tables."""
        conn = self._make_conn()
        registry = EvidenceRegistry(
            evidence=[
                _evidence("E-CCN-001", "complexity"),
                _evidence("E-SEC-001", "security", location="src/sec.py"),
            ],
            claims=[_claim("CLM-COUP-001", "coupling")],
            risks=[_risk("RISK-001")],
        )

        EvidenceRegistryBuilder.persist(registry, conn, "run-001")

        ev_count = conn.execute("SELECT COUNT(*) FROM lz_evidence").fetchone()[0]
        cl_count = conn.execute("SELECT COUNT(*) FROM lz_claims").fetchone()[0]
        ri_count = conn.execute("SELECT COUNT(*) FROM lz_risks").fetchone()[0]
        assert ev_count == 2
        assert cl_count == 1
        assert ri_count == 1

        conn.close()

    def test_persist_is_idempotent(self):
        """
        Verifies that persisting the same EvidenceRegistry twice results in identical row counts in the database.
        
        Persists a registry containing two evidence items, one claim, and one risk twice for the same run id and asserts that the lz_evidence, lz_claims, and lz_risks tables contain 2, 1, and 1 rows respectively.
        """
        conn = self._make_conn()
        registry = EvidenceRegistry(
            evidence=[
                _evidence("E-CCN-001", "complexity"),
                _evidence("E-SEC-001", "security", location="src/sec.py"),
            ],
            claims=[_claim("CLM-COUP-001", "coupling")],
            risks=[_risk("RISK-001")],
        )

        EvidenceRegistryBuilder.persist(registry, conn, "run-001")
        EvidenceRegistryBuilder.persist(registry, conn, "run-001")

        ev_count = conn.execute("SELECT COUNT(*) FROM lz_evidence").fetchone()[0]
        cl_count = conn.execute("SELECT COUNT(*) FROM lz_claims").fetchone()[0]
        ri_count = conn.execute("SELECT COUNT(*) FROM lz_risks").fetchone()[0]
        assert ev_count == 2
        assert cl_count == 1
        assert ri_count == 1

        conn.close()

    def test_persist_empty_registry(self):
        """Persisting empty registry clears previous data without inserting."""
        conn = self._make_conn()
        # First persist with data
        registry_full = EvidenceRegistry(
            evidence=[_evidence("E-CCN-001", "complexity")],
        )
        EvidenceRegistryBuilder.persist(registry_full, conn, "run-001")
        assert conn.execute("SELECT COUNT(*) FROM lz_evidence").fetchone()[0] == 1

        # Then persist empty registry for same run
        EvidenceRegistryBuilder.persist(EvidenceRegistry(), conn, "run-001")
        assert conn.execute("SELECT COUNT(*) FROM lz_evidence").fetchone()[0] == 0

        conn.close()

    def test_persist_writes_correct_field_values(self):
        """Spot-check that persisted fields match the entity values."""
        conn = self._make_conn()
        e = _evidence("E-CCN-001", "complexity")
        registry = EvidenceRegistry(evidence=[e])

        EvidenceRegistryBuilder.persist(registry, conn, "run-001")

        row = conn.execute(
            "SELECT collection_run_id, evidence_id, category, location, tool_source, run_pk "
            "FROM lz_evidence"
        ).fetchone()
        assert row == ("run-001", "E-CCN-001", "complexity", "src/file.py", "test-tool", 1)

        conn.close()


class TestBuildWarningBudgetIntegration:
    """Tests that builder.build() emits warnings when budget is exceeded."""

    def test_build_emits_warning_on_budget_exceeded(self):
        """If collector returns regressions, build() emits UserWarning."""
        evidence = [_evidence("E-CCN-001", "complexity")]
        # Create a CollectionResult with regression warnings that exceed the budget (limit=0)
        result = CollectionResult(
            items=evidence,
            warnings=[
                CollectorWarning(category="regression", source="_collect_quality", message="DB table missing"),
                CollectorWarning(category="regression", source="_collect_security", message="query failed"),
            ],
        )

        collector = MagicMock(spec=EvidenceCollector)
        collector.collect_with_warnings.return_value = result

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

        with pytest.warns(UserWarning, match="Warning budget exceeded"):
            builder.build(fetcher, run_pk=1)

    def test_build_no_warning_within_budget(self):
        """No budget warning when all warnings are within limits."""
        evidence = [_evidence("E-CCN-001", "complexity")]
        # expected_missing has a budget of 10, so 2 is fine
        result = CollectionResult(
            items=evidence,
            warnings=[
                CollectorWarning(category="expected_missing", source="_collect_coupling", message="table missing"),
                CollectorWarning(category="expected_missing", source="_collect_coverage", message="table missing"),
            ],
        )

        collector = MagicMock(spec=EvidenceCollector)
        collector.collect_with_warnings.return_value = result

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

        # Should not emit any UserWarning about budget
        import warnings as _warnings
        with _warnings.catch_warnings():
            _warnings.simplefilter("error", UserWarning)
            # This should NOT raise — all within budget
            registry = builder.build(fetcher, run_pk=1)

        assert len(registry.evidence) == 1
