from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest

from persistence.adapters import SemgrepAdapter
from persistence.repositories import LayoutRepository, SemgrepRepository, ToolRunRepository


def test_semgrep_adapter_inserts_smells(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "semgrep_output.json"
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

    adapter = SemgrepAdapter(tool_run_repo, layout_repo, SemgrepRepository(duckdb_conn))
    run_pk = adapter.persist(payload)

    rows = duckdb_conn.execute(
        """
        SELECT file_id, relative_path, rule_id, dd_smell_id
        FROM lz_semgrep_smells
        WHERE run_pk = ?
        ORDER BY relative_path
        """,
        [run_pk],
    ).fetchall()

    assert rows == [
        ("f-000000000001", "src/app.py", "DD-E2-ASYNC-VOID-python", "E2_ASYNC_VOID"),
        ("f-000000000002", "src/utils/helpers.py", "DD-D1-EMPTY-CATCH-python", "D1_EMPTY_CATCH"),
    ]


def test_semgrep_adapter_raises_on_missing_layout(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
) -> None:
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "semgrep_output.json"
    payload = json.loads(fixture_path.read_text())

    adapter = SemgrepAdapter(tool_run_repo, layout_repo, SemgrepRepository(duckdb_conn))

    try:
        adapter.persist(payload)
    except KeyError as exc:
        assert "layout" in str(exc).lower()
    else:
        raise AssertionError("Expected KeyError for missing layout run")


def test_semgrep_adapter_skips_files_not_in_layout(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter skips files not present in layout run."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "semgrep_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    # Seed layout with only src/app.py (not src/utils/helpers.py)
    seed_layout(
        repo_id,
        run_id,
        [("f-000000000001", "d-000000000002", "src/app.py")],  # Only one file
    )

    logs: list[str] = []
    adapter = SemgrepAdapter(
        tool_run_repo,
        layout_repo,
        SemgrepRepository(duckdb_conn),
        logger=logs.append,
    )
    # Adapter should succeed but skip the file not in layout
    adapter.persist(payload)
    assert any("skipping file not in layout" in log for log in logs)


def test_semgrep_adapter_normalizes_repo_root_prefix(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify repo_root prefix is stripped from paths."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "semgrep_output.json"
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

    repo_root = Path("/tmp/demo")
    for entry in payload["data"]["files"]:
        entry["path"] = f"{repo_root.as_posix().lstrip('/')}/{entry['path']}"

    adapter = SemgrepAdapter(
        tool_run_repo, layout_repo, SemgrepRepository(duckdb_conn), repo_root
    )
    run_pk = adapter.persist(payload)

    rows = duckdb_conn.execute(
        """
        SELECT file_id, relative_path
        FROM lz_semgrep_smells
        WHERE run_pk = ?
        ORDER BY relative_path
        """,
        [run_pk],
    ).fetchall()

    assert rows == [
        ("f-000000000001", "src/app.py"),
        ("f-000000000002", "src/utils/helpers.py"),
    ]


def test_semgrep_adapter_deduplicates_smell_rows(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter de-duplicates smells with same (file_id, rule_id, line_start)."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "semgrep_output.json"
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

    # Add duplicate smell (same rule_id, line_start)
    duplicate = payload["data"]["files"][0]["smells"][0].copy()
    payload["data"]["files"][0]["smells"].append(duplicate)

    logs: list[str] = []
    adapter = SemgrepAdapter(
        tool_run_repo, layout_repo, SemgrepRepository(duckdb_conn), logger=logs.append
    )

    # Adapter should de-duplicate and persist successfully
    run_pk = adapter.persist(payload)

    # Verify only unique smells were inserted (2 files, 1 smell each)
    rows = duckdb_conn.execute(
        "SELECT COUNT(*) FROM lz_semgrep_smells WHERE run_pk = ?", [run_pk]
    ).fetchone()
    assert rows[0] == 2, f"Expected 2 unique smells, got {rows[0]}"

    # Verify duplicate was logged
    assert any("duplicate smell" in log.lower() for log in logs)


def test_semgrep_adapter_validates_rule_id_required(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify missing rule_id raises schema validation error."""
    repo_id = "88888888-8888-8888-8888-888888888888"
    run_id = "77777777-7777-7777-7777-777777777777"

    seed_layout(
        repo_id,
        run_id,
        [("f-000000000001", "d-000000000002", "src/app.py")],
    )

    payload = {
        "metadata": {
            "tool_name": "semgrep",
            "tool_version": "1.0.0",
            "repo_id": repo_id,
            "run_id": run_id,
            "branch": "main",
            "commit": "a" * 40,
            "timestamp": "2026-01-26T12:00:00Z",
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "semgrep",
            "tool_version": "1.0.0",
            "summary": {"total_files": 1, "files_with_smells": 1, "total_smells": 1},
            "files": [
                {
                    "path": "src/app.py",
                    "language": "python",
                    "lines": 100,
                    "smell_count": 1,
                    "smells": [
                        {
                            # Missing rule_id (schema-required)
                            "line_start": 10,
                            "severity": "HIGH",
                            "message": "Test message",
                        }
                    ],
                }
            ],
            "directories": [],
            "by_language": {},
            "analysis_duration_ms": 1000,
            "rules_used": [],
        },
    }

    adapter = SemgrepAdapter(tool_run_repo, layout_repo, SemgrepRepository(duckdb_conn))

    with pytest.raises(ValueError, match="schema validation failed"):
        adapter.persist(payload)


def test_semgrep_adapter_validates_line_ranges(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify line_end < line_start is rejected by data quality validation."""
    repo_id = "88888888-8888-8888-8888-888888888888"
    run_id = "77777777-7777-7777-7777-777777777777"

    seed_layout(
        repo_id,
        run_id,
        [("f-000000000001", "d-000000000002", "src/app.py")],
    )

    payload = {
        "metadata": {
            "tool_name": "semgrep",
            "tool_version": "1.0.0",
            "repo_id": repo_id,
            "run_id": run_id,
            "branch": "main",
            "commit": "a" * 40,
            "timestamp": "2026-01-26T12:00:00Z",
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "semgrep",
            "tool_version": "1.0.0",
            "summary": {"total_files": 1, "files_with_smells": 1, "total_smells": 1},
            "files": [
                {
                    "path": "src/app.py",
                    "language": "python",
                    "lines": 100,
                    "smell_count": 1,
                    "smells": [
                        {
                            "rule_id": "test-rule",
                            "line_start": 20,
                            "line_end": 10,  # Invalid: line_end < line_start
                            "severity": "HIGH",
                            "message": "Test message",
                        }
                    ],
                }
            ],
            "directories": [],
            "by_language": {},
            "analysis_duration_ms": 1000,
            "rules_used": [],
        },
    }

    adapter = SemgrepAdapter(tool_run_repo, layout_repo, SemgrepRepository(duckdb_conn))

    with pytest.raises(ValueError, match="data quality validation failed"):
        adapter.persist(payload)


def test_semgrep_adapter_maps_optional_fields(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify null handling for dd_smell_id, dd_category, code_snippet (database-optional fields)."""
    repo_id = "88888888-8888-8888-8888-888888888888"
    run_id = "77777777-7777-7777-7777-777777777777"

    seed_layout(
        repo_id,
        run_id,
        [("f-000000000001", "d-000000000002", "src/app.py")],
    )

    payload = {
        "metadata": {
            "tool_name": "semgrep",
            "tool_version": "1.0.0",
            "repo_id": repo_id,
            "run_id": run_id,
            "branch": "main",
            "commit": "a" * 40,
            "timestamp": "2026-01-26T12:00:00Z",
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "semgrep",
            "tool_version": "1.0.0",
            "summary": {"total_files": 1, "files_with_smells": 1, "total_smells": 1},
            "files": [
                {
                    "path": "src/app.py",
                    "language": "python",
                    "lines": 100,
                    "smell_count": 1,
                    "smells": [
                        {
                            "rule_id": "test-rule",
                            "line_start": 10,
                            "severity": "HIGH",  # Schema-required
                            "message": "Test smell message",  # Schema-required
                            # No optional database fields: dd_smell_id, dd_category, code_snippet
                        }
                    ],
                }
            ],
            "directories": [],
            "by_language": {},
            "analysis_duration_ms": 1000,
            "rules_used": [],
        },
    }

    adapter = SemgrepAdapter(tool_run_repo, layout_repo, SemgrepRepository(duckdb_conn))
    run_pk = adapter.persist(payload)

    rows = duckdb_conn.execute(
        """
        SELECT rule_id, dd_smell_id, dd_category, code_snippet, severity, message
        FROM lz_semgrep_smells
        WHERE run_pk = ?
        """,
        [run_pk],
    ).fetchall()

    assert len(rows) == 1
    assert rows[0][0] == "test-rule"
    assert rows[0][1] is None  # dd_smell_id - optional
    assert rows[0][2] is None  # dd_category - optional
    assert rows[0][3] is None  # code_snippet - optional
    assert rows[0][4] == "HIGH"  # severity - required in schema
    assert rows[0][5] == "Test smell message"  # message - required in schema
