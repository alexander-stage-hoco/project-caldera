from __future__ import annotations

import json
from pathlib import Path

from persistence.adapters import SccAdapter
from persistence.repositories import LayoutRepository, SccRepository, ToolRunRepository


def test_scc_adapter_inserts_file_metrics(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "scc_output.json"
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

    adapter = SccAdapter(tool_run_repo, layout_repo, SccRepository(duckdb_conn))
    run_pk = adapter.persist(payload)

    rows = duckdb_conn.execute(
        """
        SELECT file_id, relative_path, lines_total, code_lines, comment_lines, blank_lines
        FROM lz_scc_file_metrics
        WHERE run_pk = ?
        ORDER BY relative_path
        """,
        [run_pk],
    ).fetchall()

    assert rows == [
        ("f-000000000001", "src/app.py", 120, 90, 20, 10),
        ("f-000000000002", "src/utils/helpers.py", 80, 60, 10, 10),
    ]


def test_scc_adapter_raises_on_missing_layout(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
) -> None:
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "scc_output.json"
    payload = json.loads(fixture_path.read_text())

    adapter = SccAdapter(tool_run_repo, layout_repo, SccRepository(duckdb_conn))

    try:
        adapter.persist(payload)
    except KeyError as exc:
        assert "layout" in str(exc).lower()
    else:
        raise AssertionError("Expected KeyError for missing layout run")


def test_scc_adapter_uses_layout_directory_id(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "scc_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000010", "d-000000000010", "src/app.py"),
            ("f-000000000011", "d-000000000011", "src/utils/helpers.py"),
        ],
    )

    adapter = SccAdapter(tool_run_repo, layout_repo, SccRepository(duckdb_conn))
    run_pk = adapter.persist(payload)

    rows = duckdb_conn.execute(
        """
        SELECT relative_path, directory_id
        FROM lz_scc_file_metrics
        WHERE run_pk = ?
        ORDER BY relative_path
        """,
        [run_pk],
    ).fetchall()

    assert rows == [
        ("src/app.py", "d-000000000010"),
        ("src/utils/helpers.py", "d-000000000011"),
    ]


def test_scc_adapter_normalizes_repo_root_prefix(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "scc_output.json"
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

    adapter = SccAdapter(tool_run_repo, layout_repo, SccRepository(duckdb_conn), repo_root)
    run_pk = adapter.persist(payload)

    rows = duckdb_conn.execute(
        """
        SELECT file_id, relative_path
        FROM lz_scc_file_metrics
        WHERE run_pk = ?
        ORDER BY relative_path
        """,
        [run_pk],
    ).fetchall()

    assert rows == [
        ("f-000000000001", "src/app.py"),
        ("f-000000000002", "src/utils/helpers.py"),
    ]


def test_scc_adapter_rejects_duplicate_file_rows(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "scc_output.json"
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

    payload["data"]["files"].append(payload["data"]["files"][0])

    adapter = SccAdapter(tool_run_repo, layout_repo, SccRepository(duckdb_conn))

    try:
        adapter.persist(payload)
    except Exception as exc:
        assert "duplicate" in str(exc).lower() or "constraint" in str(exc).lower()
    else:
        raise AssertionError("Expected failure for duplicate file rows")
