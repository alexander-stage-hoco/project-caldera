from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest

from persistence.adapters import SonarqubeAdapter
from persistence.repositories import LayoutRepository, SonarqubeRepository, ToolRunRepository

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def test_sonarqube_adapter_inserts_issues(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify SonarQube issues are inserted into landing zone."""
    fixture_path = FIXTURE_DIR / "sonarqube_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000001", "d-000000000002", "src/app.py"),
            ("f-000000000002", "d-000000000003", "src/utils/helpers.py"),
        ],
    )

    adapter = SonarqubeAdapter(tool_run_repo, layout_repo, SonarqubeRepository(duckdb_conn))
    run_pk = adapter.persist(payload)

    rows = duckdb_conn.execute(
        """
        SELECT file_id, relative_path, issue_key, rule_id, severity, issue_type, message
        FROM lz_sonarqube_issues
        WHERE run_pk = ?
        ORDER BY issue_key
        """,
        [run_pk],
    ).fetchall()

    assert len(rows) == 3
    assert rows[0] == (
        "f-000000000001",
        "src/app.py",
        "issue-001",
        "python:S1234",
        "MAJOR",
        "BUG",
        "Fix this bug in the calculation logic",
    )
    assert rows[1] == (
        "f-000000000002",
        "src/utils/helpers.py",
        "issue-002",
        "python:S5678",
        "CRITICAL",
        "VULNERABILITY",
        "SQL injection vulnerability detected",
    )
    assert rows[2] == (
        "f-000000000001",
        "src/app.py",
        "issue-003",
        "python:S9999",
        "MINOR",
        "CODE_SMELL",
        "Remove this unused variable",
    )


def test_sonarqube_adapter_inserts_metrics(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify SonarQube metrics are inserted into landing zone."""
    fixture_path = FIXTURE_DIR / "sonarqube_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000001", "d-000000000002", "src/app.py"),
            ("f-000000000002", "d-000000000003", "src/utils/helpers.py"),
        ],
    )

    adapter = SonarqubeAdapter(tool_run_repo, layout_repo, SonarqubeRepository(duckdb_conn))
    run_pk = adapter.persist(payload)

    rows = duckdb_conn.execute(
        """
        SELECT file_id, relative_path, ncloc, complexity, cognitive_complexity,
               duplicated_lines, duplicated_lines_density, code_smells, bugs, vulnerabilities
        FROM lz_sonarqube_metrics
        WHERE run_pk = ?
        ORDER BY relative_path
        """,
        [run_pk],
    ).fetchall()

    assert len(rows) == 2
    # src/app.py metrics
    assert rows[0] == (
        "f-000000000001",
        "src/app.py",
        100,  # ncloc
        10,   # complexity
        5,    # cognitive_complexity
        0,    # duplicated_lines
        0.0,  # duplicated_lines_density
        1,    # code_smells
        1,    # bugs
        0,    # vulnerabilities
    )
    # src/utils/helpers.py metrics
    assert rows[1] == (
        "f-000000000002",
        "src/utils/helpers.py",
        50,   # ncloc
        3,    # complexity
        2,    # cognitive_complexity
        5,    # duplicated_lines
        10.0, # duplicated_lines_density
        0,    # code_smells
        0,    # bugs
        1,    # vulnerabilities
    )


def test_sonarqube_adapter_raises_on_missing_layout(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
) -> None:
    """Verify adapter raises when layout run is missing."""
    fixture_path = FIXTURE_DIR / "sonarqube_output.json"
    payload = json.loads(fixture_path.read_text())

    adapter = SonarqubeAdapter(tool_run_repo, layout_repo, SonarqubeRepository(duckdb_conn))

    try:
        adapter.persist(payload)
    except KeyError as exc:
        assert "layout" in str(exc).lower()
    else:
        raise AssertionError("Expected KeyError for missing layout run")


def test_sonarqube_adapter_skips_files_not_in_layout(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter skips issues/metrics for files not present in layout run."""
    fixture_path = FIXTURE_DIR / "sonarqube_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    # Seed layout with only src/app.py (not src/utils/helpers.py)
    seed_layout(
        repo_id,
        run_id,
        [("f-000000000001", "d-000000000002", "src/app.py")],
    )

    logs: list[str] = []
    adapter = SonarqubeAdapter(
        tool_run_repo,
        layout_repo,
        SonarqubeRepository(duckdb_conn),
        logger=logs.append,
    )
    run_pk = adapter.persist(payload)

    # Verify warning was logged for skipped file
    assert any("not in layout" in log and "WARN" in log for log in logs)

    # Verify only issues for src/app.py were inserted (2 issues)
    issue_rows = duckdb_conn.execute(
        "SELECT relative_path FROM lz_sonarqube_issues WHERE run_pk = ?",
        [run_pk],
    ).fetchall()
    assert all(r[0] == "src/app.py" for r in issue_rows)
    assert len(issue_rows) == 2  # issue-001 and issue-003 are for src/app.py

    # Verify only metrics for src/app.py were inserted
    metric_rows = duckdb_conn.execute(
        "SELECT relative_path FROM lz_sonarqube_metrics WHERE run_pk = ?",
        [run_pk],
    ).fetchall()
    assert all(r[0] == "src/app.py" for r in metric_rows)
    assert len(metric_rows) == 1


def test_sonarqube_adapter_normalizes_paths(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify repo_root prefix is stripped from paths."""
    fixture_path = FIXTURE_DIR / "sonarqube_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000001", "d-000000000002", "src/app.py"),
            ("f-000000000002", "d-000000000003", "src/utils/helpers.py"),
        ],
    )

    repo_root = Path("/tmp/test-repo")

    # Modify component paths to include repo_root prefix
    for component in payload["data"]["results"]["components"]["by_key"].values():
        if "path" in component:
            component["path"] = f"{repo_root.as_posix()}/{component['path']}"

    adapter = SonarqubeAdapter(
        tool_run_repo, layout_repo, SonarqubeRepository(duckdb_conn), repo_root
    )
    run_pk = adapter.persist(payload)

    rows = duckdb_conn.execute(
        """
        SELECT file_id, relative_path
        FROM lz_sonarqube_issues
        WHERE run_pk = ?
        ORDER BY relative_path, issue_key
        """,
        [run_pk],
    ).fetchall()

    # Paths should be normalized to repo-relative
    assert ("f-000000000001", "src/app.py") in rows
    assert ("f-000000000002", "src/utils/helpers.py") in rows


def test_sonarqube_adapter_handles_optional_fields(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify null handling for optional issue and metric fields."""
    repo_id = "88888888-8888-8888-8888-888888888888"
    run_id = "77777777-7777-7777-7777-777777777777"

    seed_layout(
        repo_id,
        run_id,
        [("f-000000000001", "d-000000000002", "src/app.py")],
    )

    # Minimal valid payload with missing optional fields
    payload = {
        "metadata": {
            "run_id": run_id,
            "repo_id": repo_id,
            "branch": "main",
            "commit": "a" * 40,
            "tool_name": "sonarqube",
            "tool_version": "10.4.0",
            "timestamp": "2026-01-27T12:00:00Z",
            "schema_version": "1.2.0",
        },
        "data": {
            "schema_version": "1.2.0",
            "generated_at": "2026-01-27T12:00:00Z",
            "repo_name": "test-repo",
            "repo_path": "/tmp/test-repo",
            "results": {
                "tool": "sonarqube",
                "tool_version": "10.4.0",
                "source": {
                    "sonarqube_url": "http://localhost:9000",
                    "project_key": "test-repo",
                },
                "components": {
                    "root_key": "test-repo",
                    "by_key": {
                        "test-repo:src/app.py": {
                            "key": "test-repo:src/app.py",
                            "name": "app.py",
                            "qualifier": "FIL",
                            "path": "src/app.py",
                        }
                    },
                },
                "measures": {
                    "by_component_key": {
                        "test-repo:src/app.py": {
                            "key": "test-repo:src/app.py",
                            "measures": [
                                {"metric": "ncloc", "value": "50"},
                                # Missing: complexity, cognitive_complexity, etc.
                            ],
                        }
                    }
                },
                "issues": {
                    "items": [
                        {
                            "key": "issue-minimal",
                            "rule": "python:S1000",
                            "severity": "MAJOR",
                            "type": "CODE_SMELL",
                            "status": "OPEN",
                            "message": "Minimal issue",
                            "component": "test-repo:src/app.py",
                            "project": "test-repo",
                            # Missing: line, text_range, effort, tags
                        }
                    ],
                    "rollups": {"total": 1},
                },
                "quality_gate": {"status": "OK"},
            },
        },
    }

    adapter = SonarqubeAdapter(tool_run_repo, layout_repo, SonarqubeRepository(duckdb_conn))
    run_pk = adapter.persist(payload)

    # Check issue was inserted with nulls for optional fields
    issue_rows = duckdb_conn.execute(
        """
        SELECT issue_key, line_start, line_end, effort, tags
        FROM lz_sonarqube_issues
        WHERE run_pk = ?
        """,
        [run_pk],
    ).fetchall()

    assert len(issue_rows) == 1
    assert issue_rows[0][0] == "issue-minimal"
    assert issue_rows[0][1] is None  # line_start - optional
    assert issue_rows[0][2] is None  # line_end - optional
    assert issue_rows[0][3] is None  # effort - optional
    assert issue_rows[0][4] is None  # tags - optional

    # Check metrics were inserted with nulls for missing values
    metric_rows = duckdb_conn.execute(
        """
        SELECT ncloc, complexity, cognitive_complexity, bugs, vulnerabilities
        FROM lz_sonarqube_metrics
        WHERE run_pk = ?
        """,
        [run_pk],
    ).fetchall()

    assert len(metric_rows) == 1
    assert metric_rows[0][0] == 50      # ncloc - provided
    assert metric_rows[0][1] is None    # complexity - not provided
    assert metric_rows[0][2] is None    # cognitive_complexity - not provided
    assert metric_rows[0][3] is None    # bugs - not provided
    assert metric_rows[0][4] is None    # vulnerabilities - not provided


def test_sonarqube_adapter_validates_issue_line_ranges(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify data quality validation catches invalid line ranges."""
    repo_id = "88888888-8888-8888-8888-888888888888"
    run_id = "77777777-7777-7777-7777-777777777777"

    seed_layout(
        repo_id,
        run_id,
        [("f-000000000001", "d-000000000002", "src/app.py")],
    )

    payload = {
        "metadata": {
            "run_id": run_id,
            "repo_id": repo_id,
            "branch": "main",
            "commit": "a" * 40,
            "tool_name": "sonarqube",
            "tool_version": "10.4.0",
            "timestamp": "2026-01-27T12:00:00Z",
            "schema_version": "1.2.0",
        },
        "data": {
            "schema_version": "1.2.0",
            "generated_at": "2026-01-27T12:00:00Z",
            "repo_name": "test-repo",
            "repo_path": "/tmp/test-repo",
            "results": {
                "tool": "sonarqube",
                "tool_version": "10.4.0",
                "source": {
                    "sonarqube_url": "http://localhost:9000",
                    "project_key": "test-repo",
                },
                "components": {
                    "root_key": "test-repo",
                    "by_key": {
                        "test-repo:src/app.py": {
                            "key": "test-repo:src/app.py",
                            "name": "app.py",
                            "qualifier": "FIL",
                            "path": "src/app.py",
                        }
                    },
                },
                "measures": {"by_component_key": {}},
                "issues": {
                    "items": [
                        {
                            "key": "issue-bad-range",
                            "rule": "python:S1000",
                            "severity": "MAJOR",
                            "type": "BUG",
                            "status": "OPEN",
                            "message": "Test issue",
                            "component": "test-repo:src/app.py",
                            "project": "test-repo",
                            "text_range": {
                                "start_line": 20,
                                "end_line": 10,  # Invalid: end_line < start_line
                            },
                        }
                    ],
                    "rollups": {"total": 1},
                },
                "quality_gate": {"status": "OK"},
            },
        },
    }

    adapter = SonarqubeAdapter(tool_run_repo, layout_repo, SonarqubeRepository(duckdb_conn))

    with pytest.raises(ValueError, match="data quality validation failed"):
        adapter.persist(payload)


def test_sonarqube_adapter_skips_project_level_issues(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify issues without file paths (project-level) are skipped."""
    fixture_path = FIXTURE_DIR / "sonarqube_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000001", "d-000000000002", "src/app.py"),
            ("f-000000000002", "d-000000000003", "src/utils/helpers.py"),
        ],
    )

    # Add a project-level issue (component is TRK, no path)
    payload["data"]["results"]["issues"]["items"].append({
        "key": "issue-project",
        "rule": "project:P001",
        "severity": "INFO",
        "type": "CODE_SMELL",
        "status": "OPEN",
        "message": "Project-level issue",
        "component": "test-repo",  # Points to TRK component (no path)
        "project": "test-repo",
    })

    adapter = SonarqubeAdapter(tool_run_repo, layout_repo, SonarqubeRepository(duckdb_conn))
    run_pk = adapter.persist(payload)

    # Project-level issue should be skipped
    rows = duckdb_conn.execute(
        "SELECT issue_key FROM lz_sonarqube_issues WHERE run_pk = ?",
        [run_pk],
    ).fetchall()

    issue_keys = [r[0] for r in rows]
    assert "issue-project" not in issue_keys
    assert len(rows) == 3  # Only the 3 file-level issues
