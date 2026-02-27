"""Shared fixtures for Caldera CLI tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture()
def project_root(tmp_path: Path) -> Path:
    """Create a minimal fake Caldera project root."""
    (tmp_path / "CLAUDE.md").write_text("# test")
    tools = tmp_path / "src" / "tools"
    tools.mkdir(parents=True)
    # Create a few fake tool dirs
    for t in ("scc", "lizard", "semgrep"):
        tool_dir = tools / t
        tool_dir.mkdir()
        (tool_dir / "Makefile").write_text("all:\n\t@true\n")
    (tmp_path / ".venv" / "bin").mkdir(parents=True)
    (tmp_path / ".venv" / "bin" / "python").write_text("#!/bin/sh\n")
    (tmp_path / ".venv" / "bin" / "dbt").write_text("#!/bin/sh\n")
    return tmp_path


@pytest.fixture()
def tmp_db(tmp_path: Path) -> Path:
    """Create a minimal DuckDB database with landing-zone tables."""
    import duckdb

    db_path = tmp_path / "test.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute("""
        CREATE TABLE lz_collection_runs (
            collection_run_id VARCHAR,
            repo_id VARCHAR,
            branch VARCHAR,
            status VARCHAR,
            started_at TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE lz_tool_runs (
            run_pk INTEGER,
            collection_run_id VARCHAR,
            repo_id VARCHAR,
            tool_name VARCHAR,
            branch VARCHAR,
            timestamp TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE VIEW stg_lz_tool_runs AS
        SELECT * FROM lz_tool_runs
    """)
    # Seed some data
    conn.execute("""
        INSERT INTO lz_collection_runs VALUES
        ('aaaa-bbbb-cccc-dddd', 'my-repo', 'main', 'completed', '2026-01-15 10:00:00'),
        ('eeee-ffff-0000-1111', 'my-repo', 'develop', 'failed', '2026-01-14 09:00:00')
    """)
    conn.execute("""
        INSERT INTO lz_tool_runs VALUES
        (1, 'aaaa-bbbb-cccc-dddd', 'my-repo', 'scc', 'main', '2026-01-15 10:01:00'),
        (2, 'aaaa-bbbb-cccc-dddd', 'my-repo', 'lizard', 'main', '2026-01-15 10:02:00')
    """)
    conn.close()
    return db_path


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear env vars that could affect test behaviour."""
    monkeypatch.delenv("CALDERA_DB_PATH", raising=False)
    monkeypatch.delenv("DB_PATH", raising=False)
