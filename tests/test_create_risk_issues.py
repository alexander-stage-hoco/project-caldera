"""Tests for scripts/create_risk_issues.py — GitHub issue creation from risk register."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import duckdb
import pytest

# Add scripts/ to import path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from create_risk_issues import (
    _build_issue_body,
    _build_issue_title,
    _existing_issue_titles,
    _fetch_risks,
    main,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_db(tmp_path: Path) -> Path:
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
        CREATE TABLE lz_risks (
            collection_run_id VARCHAR NOT NULL,
            risk_id VARCHAR NOT NULL,
            description TEXT,
            technical_cause TEXT,
            manifests_in TEXT,
            triggered_by TEXT,
            severity VARCHAR NOT NULL,
            action TEXT,
            sla_date VARCHAR,
            status VARCHAR
        )
    """)
    conn.close()
    return db_path


def _insert_risk(
    db_path: Path,
    collection_run_id: str = "run-1",
    risk_id: str = "RISK-001",
    description: str = "High complexity in core module",
    severity: str = "high",
    technical_cause: str = "Deep nesting and long methods",
    manifests_in: str = "src/core.py,src/utils.py",
    triggered_by: str = "lizard",
    action: str = "Refactor methods over 50 LOC",
    sla_date: str | None = "2026-04-01",
    status: str = "open",
) -> None:
    conn = duckdb.connect(str(db_path))
    conn.execute(
        "INSERT OR IGNORE INTO lz_collection_runs (collection_run_id, repo_id, commit) VALUES (?, 'test', 'abc')",
        [collection_run_id],
    )
    conn.execute(
        "INSERT INTO lz_risks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [collection_run_id, risk_id, description, technical_cause, manifests_in, triggered_by, severity, action, sla_date, status],
    )
    conn.close()


SAMPLE_RISK: dict[str, str | None] = {
    "risk_id": "RISK-001",
    "description": "High complexity in core module",
    "technical_cause": "Deep nesting and long methods",
    "manifests_in": "src/core.py,src/utils.py",
    "triggered_by": "lizard",
    "severity": "high",
    "action": "Refactor methods over 50 LOC",
    "sla_date": "2026-04-01",
    "status": "open",
}


# ---------------------------------------------------------------------------
# _fetch_risks tests
# ---------------------------------------------------------------------------

class TestFetchRisks:
    def test_fetch_risks_filters_by_severity(self, tmp_path: Path) -> None:
        db_path = _create_db(tmp_path)
        _insert_risk(db_path, risk_id="RISK-001", severity="high")
        _insert_risk(db_path, risk_id="RISK-002", severity="medium")
        _insert_risk(db_path, risk_id="RISK-003", severity="low")

        conn = duckdb.connect(str(db_path), read_only=True)
        risks = _fetch_risks(conn, "run-1", "high")
        conn.close()

        assert len(risks) == 1
        assert risks[0]["risk_id"] == "RISK-001"

    def test_fetch_risks_latest_run_when_no_id(self, tmp_path: Path) -> None:
        """When collection_run_id is None, fetch from latest completed run."""
        db_path = _create_db(tmp_path)
        # Insert two completed runs and one failed run
        conn = duckdb.connect(str(db_path))
        conn.execute(
            "INSERT INTO lz_collection_runs (collection_run_id, repo_id, commit, status, started_at) VALUES "
            "('old-run', 'test', 'aaa', 'completed', '2026-01-01 00:00:00'), "
            "('new-run', 'test', 'bbb', 'completed', '2026-02-01 00:00:00'), "
            "('failed-run', 'test', 'ccc', 'failed', '2026-03-01 00:00:00')"
        )
        conn.execute(
            "INSERT INTO lz_risks (collection_run_id, risk_id, severity, description) VALUES "
            "('old-run', 'RISK-OLD', 'high', 'old risk'), "
            "('new-run', 'RISK-NEW', 'high', 'new risk'), "
            "('failed-run', 'RISK-FAIL', 'high', 'failed risk')"
        )
        conn.close()

        conn = duckdb.connect(str(db_path), read_only=True)
        risks = _fetch_risks(conn, None, "high")
        conn.close()

        assert len(risks) == 1
        assert risks[0]["risk_id"] == "RISK-NEW"

    def test_fetch_risks_empty_table(self, tmp_path: Path) -> None:
        db_path = _create_db(tmp_path)
        conn = duckdb.connect(str(db_path), read_only=True)
        risks = _fetch_risks(conn, "run-1", "high")
        conn.close()

        assert risks == []


# ---------------------------------------------------------------------------
# _build_issue_title / _build_issue_body tests
# ---------------------------------------------------------------------------

class TestBuildIssue:
    def test_build_issue_title_format(self) -> None:
        title = _build_issue_title(SAMPLE_RISK)
        assert title == "[RISK-001] High complexity in core module"

    def test_build_issue_body_includes_sections(self) -> None:
        body = _build_issue_body(SAMPLE_RISK)
        assert "**Severity:** high" in body
        assert "### Technical Cause" in body
        assert "Deep nesting" in body
        assert "### Suggested Action" in body
        assert "**SLA Date:** 2026-04-01" in body

    def test_build_issue_body_truncates_locations(self) -> None:
        risk = dict(SAMPLE_RISK)
        locations = [f"src/file_{i}.py" for i in range(15)]
        risk["manifests_in"] = ",".join(locations)

        body = _build_issue_body(risk)
        assert "and 5 more" in body
        assert "`src/file_0.py`" in body
        assert "`src/file_9.py`" in body


# ---------------------------------------------------------------------------
# _existing_issue_titles / main tests
# ---------------------------------------------------------------------------

class TestApplyFlow:
    def test_dry_run_prints_without_creating(self, tmp_path: Path) -> None:
        db_path = _create_db(tmp_path)
        _insert_risk(db_path)

        with patch("sys.argv", [
            "create_risk_issues.py",
            "--db", str(db_path),
            "--collection-run-id", "run-1",
        ]):
            with patch("create_risk_issues.subprocess.run") as mock_run:
                result = main()

        assert result == 0
        mock_run.assert_not_called()

    def test_apply_deduplicates_existing(self, tmp_path: Path) -> None:
        db_path = _create_db(tmp_path)
        _insert_risk(db_path)

        existing_titles = json.dumps([{"title": "[RISK-001] High complexity in core module"}])

        with patch("sys.argv", [
            "create_risk_issues.py",
            "--db", str(db_path),
            "--collection-run-id", "run-1",
            "--apply",
        ]):
            with patch("create_risk_issues.subprocess.run") as mock_run:
                # Mock gh issue list returning existing title
                mock_run.return_value = type("Result", (), {
                    "returncode": 0,
                    "stdout": existing_titles,
                    "stderr": "",
                })()
                result = main()

        assert result == 0
        # Only the list call should have happened, not create
        assert mock_run.call_count == 1
        assert "issue" in mock_run.call_args[0][0]
        assert "list" in mock_run.call_args[0][0]

    def test_apply_creates_new_issue(self, tmp_path: Path) -> None:
        db_path = _create_db(tmp_path)
        _insert_risk(db_path)

        call_count = 0

        def mock_subprocess_run(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            result = type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()
            if "list" in cmd:
                result.stdout = "[]"  # no existing issues
            elif "create" in cmd:
                result.stdout = "https://github.com/test/repo/issues/1"
            return result

        with patch("sys.argv", [
            "create_risk_issues.py",
            "--db", str(db_path),
            "--collection-run-id", "run-1",
            "--apply",
        ]):
            with patch("create_risk_issues.subprocess.run", side_effect=mock_subprocess_run):
                result = main()

        assert result == 0
        assert call_count == 2  # list + create
