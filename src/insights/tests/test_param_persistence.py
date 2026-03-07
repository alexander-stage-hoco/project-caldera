"""Unit tests for structured parameter persistence (conversion layer + DB ops)."""

from __future__ import annotations

import duckdb
import pytest

from insights.config.loader import ConfigLoader
from insights.evidence.entities import (
    ClaimParamRecord,
    ParameterSet,
    QueryParamRecord,
    RiskParamRecord,
)
from insights.evidence.param_persistence import (
    load_parameter_set_from_db,
    parameter_set_to_records,
    persist_params,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_tables(conn: duckdb.DuckDBPyConnection) -> None:
    """Create the minimal schema for parameter persistence tests."""
    conn.execute("""
        CREATE TABLE lz_evidence_sets (
            evidence_set_id VARCHAR NOT NULL PRIMARY KEY,
            collection_run_id VARCHAR NOT NULL,
            parameter_set_name VARCHAR NOT NULL,
            parameter_set_json TEXT NOT NULL DEFAULT '{}',
            status VARCHAR NOT NULL DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP,
            total_items INTEGER DEFAULT 0,
            reviewed_items INTEGER DEFAULT 0,
            accepted_items INTEGER DEFAULT 0,
            rejected_items INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE lz_evidence_query_params (
            evidence_set_id VARCHAR NOT NULL,
            query_name VARCHAR NOT NULL,
            threshold INTEGER,
            limit_rows INTEGER,
            coverage_threshold INTEGER,
            ccn_threshold INTEGER,
            density_threshold INTEGER,
            loc_threshold INTEGER,
            min_files INTEGER,
            min_depth INTEGER,
            gini_threshold DOUBLE,
            pct_threshold INTEGER,
            PRIMARY KEY (evidence_set_id, query_name)
        )
    """)
    conn.execute("""
        CREATE TABLE lz_evidence_claim_params (
            evidence_set_id VARCHAR NOT NULL,
            rule_name VARCHAR NOT NULL,
            fan_out_multiplier INTEGER,
            min_fan_out INTEGER,
            max_authors INTEGER,
            min_lines INTEGER,
            max_coverage INTEGER,
            min_ccn INTEGER,
            min_categories INTEGER,
            PRIMARY KEY (evidence_set_id, rule_name)
        )
    """)
    conn.execute("""
        CREATE TABLE lz_evidence_risk_params (
            evidence_set_id VARCHAR NOT NULL,
            pattern_name VARCHAR NOT NULL,
            min_claims INTEGER,
            default_severity VARCHAR,
            PRIMARY KEY (evidence_set_id, pattern_name)
        )
    """)


def _insert_evidence_set(conn: duckdb.DuckDBPyConnection, es_id: str, ps_name: str) -> None:
    conn.execute(
        "INSERT INTO lz_evidence_sets (evidence_set_id, collection_run_id, parameter_set_name) VALUES (?, 'crid-1', ?)",
        [es_id, ps_name],
    )


@pytest.fixture()
def conn():
    c = duckdb.connect(":memory:")
    _create_tables(c)
    yield c
    c.close()


# ---------------------------------------------------------------------------
# Conversion tests
# ---------------------------------------------------------------------------


class TestParameterSetToRecords:
    """parameter_set_to_records produces correct typed records."""

    def test_default_profile(self):
        ps = ConfigLoader.load_parameter_set("default")
        qr, cr, rr = parameter_set_to_records(ps, "es-1")

        assert len(qr) == len(ps.query_params)
        assert len(cr) == len(ps.claim_params)
        assert len(rr) == len(ps.risk_params)

        # Spot-check a query record
        complexity = next(r for r in qr if r.query_name == "evidence_complexity")
        assert complexity.threshold == 15
        assert complexity.limit_rows == 100

        # Spot-check a claim record
        coupling = next(r for r in cr if r.rule_name == "HighCouplingRule")
        assert coupling.fan_out_multiplier == 3
        assert coupling.min_fan_out == 5

        # Spot-check a risk record
        security = next(r for r in rr if r.pattern_name == "Security exposure")
        assert security.min_claims == 1
        assert security.default_severity == "high"

    def test_conservative_profile(self):
        ps = ConfigLoader.load_parameter_set("conservative")
        qr, cr, rr = parameter_set_to_records(ps, "es-2")

        complexity = next(r for r in qr if r.query_name == "evidence_complexity")
        assert complexity.threshold == 25
        assert complexity.limit_rows == 50

    def test_pe_due_diligence_profile(self):
        ps = ConfigLoader.load_parameter_set("pe_due_diligence")
        qr, cr, rr = parameter_set_to_records(ps, "es-3")

        complexity = next(r for r in qr if r.query_name == "evidence_complexity")
        assert complexity.threshold == 10

        security = next(r for r in rr if r.pattern_name == "Security exposure")
        assert security.default_severity == "critical"


class TestRecordValidation:
    """Entity __post_init__ validation."""

    def test_query_param_record_empty_set_id(self):
        with pytest.raises(ValueError, match="evidence_set_id must not be empty"):
            QueryParamRecord(evidence_set_id="", query_name="test")

    def test_query_param_record_empty_query_name(self):
        with pytest.raises(ValueError, match="query_name must not be empty"):
            QueryParamRecord(evidence_set_id="es-1", query_name="")

    def test_claim_param_record_empty_set_id(self):
        with pytest.raises(ValueError, match="evidence_set_id must not be empty"):
            ClaimParamRecord(evidence_set_id="", rule_name="test")

    def test_risk_param_record_invalid_severity(self):
        with pytest.raises(ValueError, match="Invalid default_severity"):
            RiskParamRecord(
                evidence_set_id="es-1",
                pattern_name="test",
                default_severity="invalid",
            )

    def test_risk_param_record_valid_severity(self):
        r = RiskParamRecord(
            evidence_set_id="es-1",
            pattern_name="test",
            default_severity="critical",
        )
        assert r.default_severity == "critical"

    def test_risk_param_record_none_severity_ok(self):
        r = RiskParamRecord(evidence_set_id="es-1", pattern_name="test")
        assert r.default_severity is None


# ---------------------------------------------------------------------------
# DB persistence tests
# ---------------------------------------------------------------------------


class TestPersistParams:
    """persist_params writes correct rows."""

    def test_persist_and_read_back(self, conn):
        ps = ConfigLoader.load_parameter_set("default")
        qr, cr, rr = parameter_set_to_records(ps, "es-persist")
        _insert_evidence_set(conn, "es-persist", "default")
        persist_params(conn, "es-persist", qr, cr, rr)

        q_count = conn.execute(
            "SELECT COUNT(*) FROM lz_evidence_query_params WHERE evidence_set_id = 'es-persist'"
        ).fetchone()[0]
        assert q_count == len(ps.query_params)

        c_count = conn.execute(
            "SELECT COUNT(*) FROM lz_evidence_claim_params WHERE evidence_set_id = 'es-persist'"
        ).fetchone()[0]
        assert c_count == len(ps.claim_params)

        r_count = conn.execute(
            "SELECT COUNT(*) FROM lz_evidence_risk_params WHERE evidence_set_id = 'es-persist'"
        ).fetchone()[0]
        assert r_count == len(ps.risk_params)

    def test_persist_idempotent(self, conn):
        ps = ConfigLoader.load_parameter_set("default")
        qr, cr, rr = parameter_set_to_records(ps, "es-idem")
        _insert_evidence_set(conn, "es-idem", "default")

        persist_params(conn, "es-idem", qr, cr, rr)
        persist_params(conn, "es-idem", qr, cr, rr)

        q_count = conn.execute(
            "SELECT COUNT(*) FROM lz_evidence_query_params WHERE evidence_set_id = 'es-idem'"
        ).fetchone()[0]
        assert q_count == len(ps.query_params)

    def test_typed_values(self, conn):
        ps = ConfigLoader.load_parameter_set("default")
        qr, cr, rr = parameter_set_to_records(ps, "es-typed")
        _insert_evidence_set(conn, "es-typed", "default")
        persist_params(conn, "es-typed", qr, cr, rr)

        row = conn.execute(
            "SELECT threshold, limit_rows FROM lz_evidence_query_params "
            "WHERE evidence_set_id = 'es-typed' AND query_name = 'evidence_complexity'"
        ).fetchone()
        assert row == (15, 100)


# ---------------------------------------------------------------------------
# Roundtrip tests
# ---------------------------------------------------------------------------


class TestLoadFromDb:
    """load_parameter_set_from_db reconstructs ParameterSet."""

    def test_load_returns_none_for_missing(self, conn):
        result = load_parameter_set_from_db(conn, "nonexistent")
        assert result is None

    def test_load_skips_nulls(self, conn):
        _insert_evidence_set(conn, "es-nulls", "default")
        conn.execute(
            "INSERT INTO lz_evidence_query_params (evidence_set_id, query_name, threshold) "
            "VALUES ('es-nulls', 'evidence_complexity', 15)"
        )
        ps = load_parameter_set_from_db(conn, "es-nulls")
        assert ps is not None
        params = ps.query_params["evidence_complexity"]
        assert params["threshold"] == 15
        assert "limit" not in params  # NULL columns excluded

    def test_roundtrip_default(self, conn):
        ps = ConfigLoader.load_parameter_set("default")
        qr, cr, rr = parameter_set_to_records(ps, "es-rt-default")
        _insert_evidence_set(conn, "es-rt-default", "default")
        persist_params(conn, "es-rt-default", qr, cr, rr)

        loaded = load_parameter_set_from_db(conn, "es-rt-default")
        assert loaded is not None
        assert loaded.name == "default"
        assert loaded.query_params == ps.query_params
        assert loaded.claim_params == ps.claim_params
        assert loaded.risk_params == ps.risk_params

    def test_roundtrip_conservative(self, conn):
        ps = ConfigLoader.load_parameter_set("conservative")
        qr, cr, rr = parameter_set_to_records(ps, "es-rt-conserv")
        _insert_evidence_set(conn, "es-rt-conserv", "conservative")
        persist_params(conn, "es-rt-conserv", qr, cr, rr)

        loaded = load_parameter_set_from_db(conn, "es-rt-conserv")
        assert loaded is not None
        assert loaded.query_params == ps.query_params
        assert loaded.claim_params == ps.claim_params

    def test_roundtrip_pe_due_diligence(self, conn):
        ps = ConfigLoader.load_parameter_set("pe_due_diligence")
        qr, cr, rr = parameter_set_to_records(ps, "es-rt-pe")
        _insert_evidence_set(conn, "es-rt-pe", "pe_due_diligence")
        persist_params(conn, "es-rt-pe", qr, cr, rr)

        loaded = load_parameter_set_from_db(conn, "es-rt-pe")
        assert loaded is not None
        assert loaded.query_params == ps.query_params
        assert loaded.risk_params == ps.risk_params
