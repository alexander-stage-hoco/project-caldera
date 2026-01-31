from __future__ import annotations

from datetime import datetime

from persistence.entities import ToolRun
from persistence.repositories import ToolRunRepository


def test_tool_run_repository_rejects_duplicate_tool_run(duckdb_conn) -> None:
    repo = ToolRunRepository(duckdb_conn)

    run = ToolRun(
        collection_run_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        repo_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        run_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        tool_name="scc",
        tool_version="1.0.0",
        schema_version="1.0.0",
        branch="main",
        commit="a" * 40,
        timestamp=datetime(2026, 1, 25, 12, 0, 0),
    )

    repo.insert(run)
    try:
        repo.insert(run)
    except Exception as exc:
        assert "unique" in str(exc).lower() or "constraint" in str(exc).lower()
    else:
        raise AssertionError("Expected duplicate tool run insert to fail")
