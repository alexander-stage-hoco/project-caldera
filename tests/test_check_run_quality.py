"""Tests for scripts/check_run_quality.py — CI quality gate checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import duckdb
import pytest

# Add scripts/ to import path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from check_run_quality import _check_warnings, main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_db(tmp_path: Path) -> Path:
    """Create an in-memory-like DuckDB with required tables and return its path."""
    db_path = tmp_path / "test.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute("""
        CREATE TABLE lz_collection_runs (
            collection_run_id VARCHAR PRIMARY KEY,
            repo_id VARCHAR NOT NULL,
            commit VARCHAR NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'completed',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE lz_run_quality_summary (
            collection_run_id VARCHAR NOT NULL PRIMARY KEY,
            tools_expected INTEGER NOT NULL DEFAULT 0,
            tools_completed INTEGER NOT NULL DEFAULT 0,
            tools_skipped INTEGER NOT NULL DEFAULT 0,
            tools_failed INTEGER NOT NULL DEFAULT 0,
            tools_empty INTEGER NOT NULL DEFAULT 0,
            ingestion_errors INTEGER NOT NULL DEFAULT 0,
            warning_count INTEGER NOT NULL DEFAULT 0,
            budget_passed BOOLEAN NOT NULL DEFAULT TRUE,
            trust_score INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.close()
    return db_path


def _insert_quality_summary(
    db_path: Path,
    collection_run_id: str = "run-1",
    trust_score: int = 80,
    tools_completed: int = 10,
    tools_expected: int = 10,
    tools_failed: int = 0,
    warning_count: int = 0,
) -> None:
    conn = duckdb.connect(str(db_path))
    conn.execute(
        "INSERT INTO lz_collection_runs (collection_run_id, repo_id, commit, status) VALUES (?, 'test', 'abc', 'completed')",
        [collection_run_id],
    )
    conn.execute(
        "INSERT INTO lz_run_quality_summary (collection_run_id, trust_score, tools_completed, tools_expected, tools_failed, warning_count) VALUES (?, ?, ?, ?, ?, ?)",
        [collection_run_id, trust_score, tools_completed, tools_expected, tools_failed, warning_count],
    )
    conn.close()


def _write_warnings_json(path: Path, counts: dict, budgets: dict, budget_passed: bool = True) -> None:
    total = sum(counts.values())
    data = {
        "counts": counts,
        "budgets": budgets,
        "budget_passed": budget_passed,
        "total": total,
    }
    path.write_text(json.dumps(data), encoding="utf-8")


# ---------------------------------------------------------------------------
# _check_warnings tests
# ---------------------------------------------------------------------------

class TestCheckWarnings:
    def test_warnings_within_budget_passes(self, tmp_path: Path) -> None:
        path = tmp_path / "warnings.json"
        _write_warnings_json(
            path,
            counts={"expected_missing": 2, "regression": 0, "degraded": 1},
            budgets={"expected_missing": 5, "regression": 0, "degraded": 3},
        )
        assert _check_warnings(path) is True

    def test_warnings_regression_over_budget_fails(self, tmp_path: Path) -> None:
        path = tmp_path / "warnings.json"
        _write_warnings_json(
            path,
            counts={"expected_missing": 0, "regression": 1, "degraded": 0},
            budgets={"expected_missing": 5, "regression": 0, "degraded": 3},
        )
        assert _check_warnings(path) is False

    def test_warnings_missing_file_passes(self, tmp_path: Path) -> None:
        # Missing file prints a warning but returns True (skip)
        path = tmp_path / "nonexistent.json"
        assert _check_warnings(path) is True

    def test_warnings_malformed_json_fails_gracefully(self, tmp_path: Path) -> None:
        path = tmp_path / "warnings.json"
        path.write_text("{invalid json", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            _check_warnings(path)


# ---------------------------------------------------------------------------
# main() tests
# ---------------------------------------------------------------------------

class TestMain:
    def test_main_trust_above_threshold_passes(self, tmp_path: Path) -> None:
        db_path = _create_db(tmp_path)
        _insert_quality_summary(db_path, trust_score=80)
        with patch("sys.argv", ["check_run_quality.py", "--db", str(db_path), "--min-trust", "50"]):
            assert main() == 0

    def test_main_trust_below_threshold_fails(self, tmp_path: Path) -> None:
        db_path = _create_db(tmp_path)
        _insert_quality_summary(db_path, trust_score=30)
        with patch("sys.argv", ["check_run_quality.py", "--db", str(db_path), "--min-trust", "50"]):
            assert main() == 1

    def test_main_no_quality_summary_warns(self, tmp_path: Path) -> None:
        db_path = _create_db(tmp_path)
        # No rows inserted — should warn but return 0
        with patch("sys.argv", ["check_run_quality.py", "--db", str(db_path)]):
            assert main() == 0

    def test_main_with_warning_budget_failure(self, tmp_path: Path) -> None:
        db_path = _create_db(tmp_path)
        _insert_quality_summary(db_path, trust_score=80)

        warnings_path = tmp_path / "warnings.json"
        _write_warnings_json(
            warnings_path,
            counts={"expected_missing": 0, "regression": 3, "degraded": 0},
            budgets={"expected_missing": 5, "regression": 0, "degraded": 3},
        )

        with patch("sys.argv", [
            "check_run_quality.py",
            "--db", str(db_path),
            "--min-trust", "50",
            "--check-warnings", str(warnings_path),
        ]):
            assert main() == 1
