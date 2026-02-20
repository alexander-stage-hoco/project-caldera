from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from persistence.adapters import LayoutAdapter, SonarqubeAdapter
from persistence.repositories import LayoutRepository, SonarqubeRepository, ToolRunRepository


def _load_schema(conn: duckdb.DuckDBPyConnection) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "persistence" / "schema.sql"
    conn.execute(schema_path.read_text())


def _create_layout_run(conn: duckdb.DuckDBPyConnection, run_id: str, repo_id: str) -> int:
    layout_fixture = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "layout_output.json"
    layout_payload = json.loads(layout_fixture.read_text())
    layout_payload["metadata"]["repo_id"] = repo_id
    layout_payload["metadata"]["run_id"] = run_id

    run_repo = ToolRunRepository(conn)
    layout_repo = LayoutRepository(conn)
    LayoutAdapter(run_repo, layout_repo, Path("/tmp/test-repo"), None).persist(layout_payload)
    return run_repo.get_run_pk(run_id, "layout-scanner")


def _load_sonarqube_fixture() -> dict:
    fixture_path = Path(__file__).resolve().parents[1] / "persistence" / "fixtures" / "sonarqube_output.json"
    return json.loads(fixture_path.read_text())


class TestSonarqubeAdapter:
    """Comprehensive tests for the SonarQube adapter (2 tables)."""

    def test_persist_issues_and_metrics(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_sonarqube_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        sonarqube_repo = SonarqubeRepository(conn)

        adapter = SonarqubeAdapter(run_repo, layout_repo, sonarqube_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        assert run_pk > 0

        issue_count = conn.execute(
            "SELECT COUNT(*) FROM lz_sonarqube_issues WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert issue_count == 3

        metric_count = conn.execute(
            "SELECT COUNT(*) FROM lz_sonarqube_metrics WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert metric_count == 2

        conn.close()

    def test_issue_field_correctness(self, tmp_path: Path) -> None:
        """Test issue fields including component path resolution."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_sonarqube_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        sonarqube_repo = SonarqubeRepository(conn)

        adapter = SonarqubeAdapter(run_repo, layout_repo, sonarqube_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT relative_path, issue_key, rule_id, issue_type, severity, message,
                      line_start, line_end, effort, status, tags
               FROM lz_sonarqube_issues WHERE run_pk = ? AND issue_key = 'issue-001'""",
            [run_pk],
        ).fetchone()

        assert row is not None
        assert row[0] == "src/app.py"
        assert row[1] == "issue-001"
        assert row[2] == "python:S1234"
        assert row[3] == "BUG"
        assert row[4] == "MAJOR"
        assert "bug" in row[5].lower() or "calculation" in row[5].lower()
        assert row[6] == 10
        assert row[7] == 12
        assert row[8] == "15min"
        assert row[9] == "OPEN"
        assert "bug" in row[10]

        conn.close()

    def test_metric_string_to_int_parsing(self, tmp_path: Path) -> None:
        """Test that SonarQube string values are correctly parsed to int/float."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_sonarqube_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        sonarqube_repo = SonarqubeRepository(conn)

        adapter = SonarqubeAdapter(run_repo, layout_repo, sonarqube_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            """SELECT ncloc, complexity, cognitive_complexity, duplicated_lines,
                      duplicated_lines_density, code_smells, bugs, vulnerabilities
               FROM lz_sonarqube_metrics WHERE run_pk = ? AND relative_path = 'src/app.py'""",
            [run_pk],
        ).fetchone()

        assert row[0] == 100  # ncloc parsed from "100"
        assert row[1] == 10
        assert row[2] == 5
        assert row[3] == 0
        assert abs(row[4] - 0.0) < 0.01
        assert row[5] == 1
        assert row[6] == 1
        assert row[7] == 0

        conn.close()

    def test_raises_on_missing_layout(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        payload = _load_sonarqube_fixture()
        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        sonarqube_repo = SonarqubeRepository(conn)

        adapter = SonarqubeAdapter(run_repo, layout_repo, sonarqube_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(KeyError, match="layout run not found"):
            adapter.persist(payload)

        conn.close()

    def test_skips_project_level_issues(self, tmp_path: Path) -> None:
        """Test that issues without a file path (project-level) are skipped."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_sonarqube_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        # Add a project-level issue (component is the project root with no path)
        payload["data"]["results"]["issues"]["items"].append({
            "key": "issue-proj",
            "rule": "python:S0000",
            "severity": "INFO",
            "type": "CODE_SMELL",
            "status": "OPEN",
            "message": "Project-level issue",
            "component": "test-repo",  # TRK component has no path
            "project": "test-repo",
        })

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        sonarqube_repo = SonarqubeRepository(conn)

        adapter = SonarqubeAdapter(run_repo, layout_repo, sonarqube_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        issue_count = conn.execute(
            "SELECT COUNT(*) FROM lz_sonarqube_issues WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert issue_count == 3  # Project-level issue skipped

        conn.close()

    def test_only_processes_fil_qualifier_for_metrics(self, tmp_path: Path) -> None:
        """Test that only FIL components get metrics rows."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_sonarqube_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        sonarqube_repo = SonarqubeRepository(conn)

        adapter = SonarqubeAdapter(run_repo, layout_repo, sonarqube_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        # Both components in measures are FIL, so should get 2 metrics rows
        metric_count = conn.execute(
            "SELECT COUNT(*) FROM lz_sonarqube_metrics WHERE run_pk = ?", [run_pk]
        ).fetchone()[0]
        assert metric_count == 2

        conn.close()

    def test_rejects_missing_issue_key(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_sonarqube_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        del payload["data"]["results"]["issues"]["items"][0]["key"]

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        sonarqube_repo = SonarqubeRepository(conn)

        adapter = SonarqubeAdapter(run_repo, layout_repo, sonarqube_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_rejects_invalid_line(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_sonarqube_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id
        payload["data"]["results"]["issues"]["items"][0]["line"] = 0

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        sonarqube_repo = SonarqubeRepository(conn)

        adapter = SonarqubeAdapter(run_repo, layout_repo, sonarqube_repo, Path("/tmp/test-repo"), None)
        with pytest.raises(ValueError, match="validation failed"):
            adapter.persist(payload)

        conn.close()

    def test_handles_issue_without_text_range(self, tmp_path: Path) -> None:
        """Test that issues without text_range use the line field."""
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_sonarqube_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        sonarqube_repo = SonarqubeRepository(conn)

        adapter = SonarqubeAdapter(run_repo, layout_repo, sonarqube_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        # issue-003 has no text_range, so line_start should come from "line" field
        row = conn.execute(
            "SELECT line_start FROM lz_sonarqube_issues WHERE run_pk = ? AND issue_key = 'issue-003'",
            [run_pk],
        ).fetchone()
        assert row[0] == 45

        conn.close()

    def test_tags_serialized_as_csv(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_sonarqube_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        sonarqube_repo = SonarqubeRepository(conn)

        adapter = SonarqubeAdapter(run_repo, layout_repo, sonarqube_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        row = conn.execute(
            "SELECT tags FROM lz_sonarqube_issues WHERE run_pk = ? AND issue_key = 'issue-002'",
            [run_pk],
        ).fetchone()
        assert "security" in row[0]
        assert "sql" in row[0]
        assert "cwe-89" in row[0]

        conn.close()

    def test_joins_with_layout_files(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.duckdb"
        conn = duckdb.connect(str(db_path))
        _load_schema(conn)

        repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        _create_layout_run(conn, run_id, repo_id)

        payload = _load_sonarqube_fixture()
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

        run_repo = ToolRunRepository(conn)
        layout_repo = LayoutRepository(conn)
        sonarqube_repo = SonarqubeRepository(conn)

        adapter = SonarqubeAdapter(run_repo, layout_repo, sonarqube_repo, Path("/tmp/test-repo"), None)
        run_pk = adapter.persist(payload)

        joined = conn.execute(
            """
            SELECT sq.relative_path, lf.relative_path
            FROM lz_sonarqube_issues sq
            JOIN lz_tool_runs tr ON tr.run_pk = sq.run_pk
            JOIN lz_tool_runs tr_layout
              ON tr_layout.collection_run_id = tr.collection_run_id
             AND tr_layout.tool_name IN ('layout', 'layout-scanner')
            JOIN lz_layout_files lf
              ON lf.run_pk = tr_layout.run_pk AND lf.file_id = sq.file_id
            WHERE sq.run_pk = ?
            """,
            [run_pk],
        ).fetchall()

        assert len(joined) == 3

        conn.close()
