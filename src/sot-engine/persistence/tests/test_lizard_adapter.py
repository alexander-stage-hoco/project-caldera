from __future__ import annotations

import json
from pathlib import Path

from persistence.adapters import LizardAdapter
from persistence.repositories import LayoutRepository, LizardRepository, ToolRunRepository


def test_lizard_adapter_inserts_file_and_function_metrics(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "lizard_output.json"
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

    adapter = LizardAdapter(tool_run_repo, layout_repo, LizardRepository(duckdb_conn))
    run_pk = adapter.persist(payload)

    file_rows = duckdb_conn.execute(
        """
        SELECT file_id, relative_path, function_count, total_ccn, max_ccn
        FROM lz_lizard_file_metrics
        WHERE run_pk = ?
        ORDER BY relative_path
        """,
        [run_pk],
    ).fetchall()

    assert file_rows == [
        ("f-000000000001", "src/app.py", 2, 10, 7),
        ("f-000000000002", "src/utils/helpers.py", 2, 8, 6),
    ]

    function_rows = duckdb_conn.execute(
        """
        SELECT file_id, function_name, ccn, line_start, line_end
        FROM lz_lizard_function_metrics
        WHERE run_pk = ?
        ORDER BY file_id, line_start
        """,
        [run_pk],
    ).fetchall()

    assert function_rows == [
        ("f-000000000001", "main", 7, 10, 90),
        ("f-000000000001", "helper", 3, 95, 130),
        ("f-000000000002", "calc", 6, 5, 60),
        ("f-000000000002", "format", 2, 70, 95),
    ]


def test_lizard_adapter_raises_on_missing_layout(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
) -> None:
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "lizard_output.json"
    payload = json.loads(fixture_path.read_text())

    adapter = LizardAdapter(tool_run_repo, layout_repo, LizardRepository(duckdb_conn))

    try:
        adapter.persist(payload)
    except KeyError as exc:
        assert "layout" in str(exc).lower()
    else:
        raise AssertionError("Expected KeyError for missing layout run")


def test_lizard_adapter_deduplicates_function_rows(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Test that duplicate functions are silently skipped during persistence."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "lizard_output.json"
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

    # Get original function count
    original_func_count = sum(
        len(f.get("functions", []) or [])
        for f in payload["data"]["files"]
    )

    # Add duplicate function
    duplicate = payload["data"]["files"][0]["functions"][0]
    payload["data"]["files"][0]["functions"].append(duplicate)

    logs: list[str] = []
    adapter = LizardAdapter(
        tool_run_repo,
        layout_repo,
        LizardRepository(duckdb_conn),
        logger=logs.append,
    )

    # Should succeed without error
    run_pk = adapter.persist(payload)

    # Verify duplicate was skipped and logged
    assert any("duplicate" in log.lower() for log in logs)

    # Verify only original count of unique functions were inserted
    rows = duckdb_conn.execute(
        "SELECT function_name FROM lz_lizard_function_metrics WHERE run_pk = ?",
        [run_pk],
    ).fetchall()
    assert len(rows) == original_func_count


def test_lizard_adapter_normalizes_repo_root_prefix(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "lizard_output.json"
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

    adapter = LizardAdapter(tool_run_repo, layout_repo, LizardRepository(duckdb_conn), repo_root)
    run_pk = adapter.persist(payload)

    rows = duckdb_conn.execute(
        """
        SELECT file_id, relative_path
        FROM lz_lizard_file_metrics
        WHERE run_pk = ?
        ORDER BY relative_path
        """,
        [run_pk],
    ).fetchall()

    assert rows == [
        ("f-000000000001", "src/app.py"),
        ("f-000000000002", "src/utils/helpers.py"),
    ]


def test_lizard_adapter_maps_start_line_fields(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "lizard_output.json"
    payload = json.loads(fixture_path.read_text())

    for entry in payload["data"]["files"]:
        for func in entry.get("functions", []):
            func["start_line"] = func.pop("line_start")
            func["end_line"] = func.pop("line_end")
            func["parameter_count"] = func.pop("params")

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

    adapter = LizardAdapter(tool_run_repo, layout_repo, LizardRepository(duckdb_conn))
    run_pk = adapter.persist(payload)

    rows = duckdb_conn.execute(
        """
        SELECT line_start, line_end, params
        FROM lz_lizard_function_metrics
        WHERE run_pk = ?
        ORDER BY line_start
        LIMIT 1
        """,
        [run_pk],
    ).fetchall()

    assert rows[0][0] is not None


def test_lizard_adapter_inserts_excluded_files(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Test that excluded files are persisted to the landing zone."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "lizard_output.json"
    payload = json.loads(fixture_path.read_text())

    # Add excluded_files to payload
    payload["data"]["excluded_files"] = [
        {
            "path": "src/vendor/lib.min.js",
            "reason": "minified",
            "language": "JavaScript",
            "details": "Minified file detected: < 50 chars avg line length",
        },
        {
            "path": "src/generated/parser.py",
            "reason": "pattern",
            "language": "Python",
            "details": "Matched exclusion pattern: **/generated/**",
        },
        {
            "path": "assets/data.bin",
            "reason": "language",
            "language": "unknown",
            "details": "Unsupported language",
        },
    ]

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

    from persistence.repositories import LizardRepository

    adapter = LizardAdapter(tool_run_repo, layout_repo, LizardRepository(duckdb_conn))
    run_pk = adapter.persist(payload)

    excluded_rows = duckdb_conn.execute(
        """
        SELECT file_path, reason, language, details
        FROM lz_lizard_excluded_files
        WHERE run_pk = ?
        ORDER BY file_path
        """,
        [run_pk],
    ).fetchall()

    assert len(excluded_rows) == 3
    assert excluded_rows[0] == (
        "assets/data.bin",
        "language",
        "unknown",
        "Unsupported language",
    )
    assert excluded_rows[1] == (
        "src/generated/parser.py",
        "pattern",
        "Python",
        "Matched exclusion pattern: **/generated/**",
    )
    assert excluded_rows[2] == (
        "src/vendor/lib.min.js",
        "minified",
        "JavaScript",
        "Minified file detected: < 50 chars avg line length",
    )


def test_lizard_adapter_handles_empty_excluded_files(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Test that adapter handles missing or empty excluded_files gracefully."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "lizard_output.json"
    payload = json.loads(fixture_path.read_text())

    # Ensure no excluded_files key
    assert "excluded_files" not in payload["data"]

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

    from persistence.repositories import LizardRepository

    adapter = LizardAdapter(tool_run_repo, layout_repo, LizardRepository(duckdb_conn))
    run_pk = adapter.persist(payload)

    excluded_rows = duckdb_conn.execute(
        "SELECT COUNT(*) FROM lz_lizard_excluded_files WHERE run_pk = ?",
        [run_pk],
    ).fetchone()

    assert excluded_rows[0] == 0
