from __future__ import annotations

import copy
import json
from pathlib import Path

from persistence.adapters import GitleaksAdapter
from persistence.repositories import GitleaksRepository, LayoutRepository, ToolRunRepository


def test_gitleaks_adapter_skips_secrets_in_current_head_not_in_layout(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter warns and skips when in_current_head=true but file not in layout."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "gitleaks_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    # Seed layout with only .env (not config/api.py)
    # Both findings in fixture have in_current_head=true
    seed_layout(
        repo_id,
        run_id,
        [("f-000000000001", "d-000000000001", ".env")],
    )

    logs: list[str] = []
    adapter = GitleaksAdapter(
        tool_run_repo,
        layout_repo,
        GitleaksRepository(duckdb_conn),
        logger=logs.append,
    )
    adapter.persist(payload)

    # Verify warning for current secret in file not in layout
    assert any("skipping secret in file not in layout" in log for log in logs)
    assert any("config/api.py" in log for log in logs)


def test_gitleaks_adapter_skips_historical_secrets_in_deleted_files(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter warns and skips when in_current_head=false (historical secret)."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "gitleaks_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    # Modify fixture: set in_current_head=false for config/api.py finding
    payload = copy.deepcopy(payload)
    for finding in payload["data"]["findings"]:
        if finding["file_path"] == "config/api.py":
            finding["in_current_head"] = False

    # Seed layout with only .env (not config/api.py)
    seed_layout(
        repo_id,
        run_id,
        [("f-000000000001", "d-000000000001", ".env")],
    )

    logs: list[str] = []
    adapter = GitleaksAdapter(
        tool_run_repo,
        layout_repo,
        GitleaksRepository(duckdb_conn),
        logger=logs.append,
    )
    adapter.persist(payload)

    # Verify warning for historical secret in deleted file
    assert any("skipping historical secret in deleted file" in log for log in logs)
    assert any("config/api.py" in log for log in logs)
