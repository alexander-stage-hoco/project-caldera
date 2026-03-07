from __future__ import annotations

import logging
from pathlib import Path

import duckdb

_log = logging.getLogger(__name__)


def ensure_schema(conn: duckdb.DuckDBPyConnection, schema_path: Path) -> None:
    exists = conn.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'lz_tool_runs'
        """
    ).fetchone()
    if not exists:
        conn.execute(schema_path.read_text())
        return

    collection_exists = conn.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'lz_collection_runs'
        """
    ).fetchone()
    if not collection_exists:
        raise RuntimeError(
            "lz_collection_runs missing. Apply schema.sql before running orchestrator."
        )

    _apply_migrations(conn)


# -- Schema migrations --------------------------------------------------------
# Each entry is an idempotent ALTER TABLE statement for columns added after the
# initial schema.sql release.  DuckDB supports ADD COLUMN IF NOT EXISTS.

_MIGRATIONS: tuple[str, ...] = (
    "ALTER TABLE lz_layout_files ADD COLUMN IF NOT EXISTS stable_fingerprint VARCHAR",
    # P1: Run quality summary table
    """CREATE TABLE IF NOT EXISTS lz_run_quality_summary (
        collection_run_id VARCHAR NOT NULL PRIMARY KEY,
        tools_expected INTEGER NOT NULL,
        tools_completed INTEGER NOT NULL,
        tools_skipped INTEGER NOT NULL,
        tools_failed INTEGER NOT NULL,
        tools_empty INTEGER NOT NULL,
        ingestion_errors INTEGER NOT NULL DEFAULT 0,
        warning_count INTEGER NOT NULL DEFAULT 0,
        trust_score INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    # P3: Evidence, claims, risks tables
    """CREATE TABLE IF NOT EXISTS lz_evidence (
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
    )""",
    """CREATE TABLE IF NOT EXISTS lz_claims (
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
    )""",
    """CREATE TABLE IF NOT EXISTS lz_risks (
        collection_run_id VARCHAR NOT NULL,
        risk_id VARCHAR NOT NULL,
        description TEXT NOT NULL,
        technical_cause TEXT,
        claim_ids VARCHAR NOT NULL,
        manifests_in VARCHAR,
        triggered_by VARCHAR NOT NULL,
        severity VARCHAR NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (collection_run_id, risk_id)
    )""",
)


def _apply_migrations(conn: duckdb.DuckDBPyConnection) -> None:
    """Run idempotent schema migrations on an existing database."""
    for stmt in _MIGRATIONS:
        try:
            conn.execute(stmt)
        except Exception as exc:
            _log.warning("Migration skipped (%s): %s", stmt.split()[:5], exc)
