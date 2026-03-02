"""Tests for scripts/write_run_manifest.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import duckdb
import pytest

SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from write_run_manifest import main  # noqa: E402


def _setup_db(db_path: Path, *, with_quality: bool = True) -> None:
    """Create a minimal DuckDB with lz_collection_runs, lz_tool_runs, and optionally lz_run_quality_summary."""
    conn = duckdb.connect(str(db_path))
    conn.execute("""
        CREATE TABLE lz_collection_runs (
            collection_run_id VARCHAR PRIMARY KEY,
            repo_id VARCHAR,
            run_id VARCHAR,
            branch VARCHAR,
            commit VARCHAR,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            status VARCHAR
        )
    """)
    conn.execute("""
        INSERT INTO lz_collection_runs VALUES
        ('cr-1', 'my-repo', 'run-1', 'main', 'abc123', '2026-01-01 00:00:00', '2026-01-01 00:05:00', 'completed')
    """)
    conn.execute("""
        CREATE TABLE lz_tool_runs (
            run_pk BIGINT,
            collection_run_id VARCHAR,
            tool_name VARCHAR,
            tool_version VARCHAR,
            schema_version VARCHAR,
            timestamp TIMESTAMP,
            repo_id VARCHAR,
            run_id VARCHAR
        )
    """)
    conn.execute("""
        INSERT INTO lz_tool_runs VALUES
        (1, 'cr-1', 'scc', '3.1.0', '1.0.0', '2026-01-01 00:01:00', 'my-repo', 'run-1'),
        (2, 'cr-1', 'lizard', '1.17.0', '1.0.0', '2026-01-01 00:02:00', 'my-repo', 'run-1')
    """)
    if with_quality:
        conn.execute("""
            CREATE TABLE lz_run_quality_summary (
                collection_run_id VARCHAR PRIMARY KEY,
                tools_expected INTEGER,
                tools_completed INTEGER,
                tools_skipped INTEGER,
                tools_failed INTEGER,
                tools_empty INTEGER,
                ingestion_errors INTEGER DEFAULT 0,
                warning_count INTEGER DEFAULT 0,
                warnings_expected_missing INTEGER DEFAULT 0,
                warnings_regression INTEGER DEFAULT 0,
                warnings_degraded INTEGER DEFAULT 0,
                budget_passed BOOLEAN DEFAULT TRUE,
                trust_score INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            INSERT INTO lz_run_quality_summary
            (collection_run_id, tools_expected, tools_completed, tools_skipped, tools_failed, tools_empty,
             ingestion_errors, warning_count, trust_score)
            VALUES ('cr-1', 18, 16, 1, 1, 0, 2, 5, 82)
        """)
    conn.close()


def _run_main(args: list[str]) -> int:
    with patch("sys.argv", ["write_run_manifest.py"] + args):
        return main()


class TestBasicManifest:
    def test_basic_manifest_output(self, tmp_path: Path) -> None:
        db = tmp_path / "test.duckdb"
        out = tmp_path / "manifest.json"
        _setup_db(db)
        rc = _run_main(["--db", str(db), "--collection-run-id", "cr-1", "--out", str(out)])
        assert rc == 0
        manifest = json.loads(out.read_text())
        assert manifest["schema_version"] == 2
        assert "generated_at" in manifest
        assert manifest["collection_run"]["collection_run_id"] == "cr-1"
        assert manifest["collection_run"]["repo_id"] == "my-repo"
        assert manifest["collection_run"]["status"] == "completed"
        assert isinstance(manifest["tools"], list)

    def test_manifest_includes_trust(self, tmp_path: Path) -> None:
        db = tmp_path / "test.duckdb"
        out = tmp_path / "manifest.json"
        _setup_db(db, with_quality=True)
        _run_main(["--db", str(db), "--collection-run-id", "cr-1", "--out", str(out)])
        manifest = json.loads(out.read_text())
        trust = manifest["trust"]
        assert trust is not None
        assert trust["trust_score"] == 82
        assert trust["tools_expected"] == 18
        assert trust["warning_count"] == 5
        assert trust["ingestion_errors"] == 2

    def test_manifest_without_quality_summary(self, tmp_path: Path) -> None:
        db = tmp_path / "test.duckdb"
        out = tmp_path / "manifest.json"
        _setup_db(db, with_quality=False)
        _run_main(["--db", str(db), "--collection-run-id", "cr-1", "--out", str(out)])
        manifest = json.loads(out.read_text())
        assert manifest["trust"] is None

    def test_manifest_includes_all_tools(self, tmp_path: Path) -> None:
        db = tmp_path / "test.duckdb"
        out = tmp_path / "manifest.json"
        _setup_db(db)
        _run_main(["--db", str(db), "--collection-run-id", "cr-1", "--out", str(out)])
        manifest = json.loads(out.read_text())
        tool_names = [t["tool_name"] for t in manifest["tools"]]
        assert "scc" in tool_names
        assert "lizard" in tool_names
        assert len(manifest["tools"]) == 2


class TestWarningsEnrichment:
    def test_manifest_enriches_from_warnings_json(self, tmp_path: Path) -> None:
        db = tmp_path / "test.duckdb"
        out = tmp_path / "manifest.json"
        _setup_db(db)
        warnings_file = tmp_path / "warnings.json"
        warnings_file.write_text(json.dumps({
            "counts": {"expected_missing": 2, "regression": 1},
            "budgets": {"expected_missing": 5, "regression": 3},
            "budget_passed": False,
        }))
        _run_main([
            "--db", str(db),
            "--collection-run-id", "cr-1",
            "--out", str(out),
            "--warnings-json", str(warnings_file),
        ])
        manifest = json.loads(out.read_text())
        trust = manifest["trust"]
        assert trust["warning_counts"] == {"expected_missing": 2, "regression": 1}
        assert trust["budget_passed"] is False


class TestEdgeCases:
    def test_manifest_missing_collection_run_exits(self, tmp_path: Path) -> None:
        db = tmp_path / "test.duckdb"
        out = tmp_path / "manifest.json"
        _setup_db(db)
        with pytest.raises(SystemExit, match="not found"):
            _run_main(["--db", str(db), "--collection-run-id", "nonexistent", "--out", str(out)])

    def test_manifest_flags(self, tmp_path: Path) -> None:
        db = tmp_path / "test.duckdb"
        out = tmp_path / "manifest.json"
        _setup_db(db)
        _run_main([
            "--db", str(db),
            "--collection-run-id", "cr-1",
            "--out", str(out),
            "--tool-outputs-included",
            "--evidence-included",
        ])
        manifest = json.loads(out.read_text())
        assert manifest["tool_outputs_included"] is True
        assert manifest["evidence_included"] is True
        assert manifest["dbt_artifacts_included"] is False
