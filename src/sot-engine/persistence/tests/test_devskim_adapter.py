from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from persistence.adapters import DevskimAdapter
from persistence.repositories import (
    DevskimRepository,
    LayoutRepository,
    ToolRunRepository,
)


def test_devskim_adapter_inserts_findings(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter correctly maps issues to DevskimFinding entities."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "devskim_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    # Seed layout with files referenced by devskim findings
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000001", "d-000000000002", "src/crypto.cs"),
            ("f-000000000002", "d-000000000002", "src/serializer.cs"),
            ("f-000000000003", "d-000000000002", "src/safe.cs"),
        ],
    )

    devskim_repo = DevskimRepository(duckdb_conn)
    adapter = DevskimAdapter(
        tool_run_repo,
        layout_repo,
        devskim_repo,
    )
    run_pk = adapter.persist(payload)

    # Verify findings were inserted
    result = duckdb_conn.execute(
        """SELECT relative_path, rule_id, dd_category, severity, line_start
           FROM lz_devskim_findings WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    assert len(result) == 3  # 3 issues in fixture
    rule_ids = {row[1] for row in result}
    assert "DS126858" in rule_ids
    assert "DS425040" in rule_ids


def test_devskim_adapter_raises_on_missing_layout(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
) -> None:
    """Verify adapter raises KeyError when no layout run exists for collection."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "devskim_output.json"
    payload = json.loads(fixture_path.read_text())

    # Don't seed layout - should raise KeyError
    devskim_repo = DevskimRepository(duckdb_conn)
    adapter = DevskimAdapter(
        tool_run_repo,
        layout_repo,
        devskim_repo,
    )

    with pytest.raises(KeyError):
        adapter.persist(payload)


def test_devskim_adapter_uses_layout_ids(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify file_id and directory_id are correctly linked from layout."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "devskim_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    # Seed layout with specific file and directory IDs
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-crypto-001", "d-src-001", "src/crypto.cs"),
            ("f-serializer-002", "d-src-001", "src/serializer.cs"),
        ],
    )

    devskim_repo = DevskimRepository(duckdb_conn)
    adapter = DevskimAdapter(
        tool_run_repo,
        layout_repo,
        devskim_repo,
    )
    run_pk = adapter.persist(payload)

    # Verify findings have correct file_id and directory_id
    result = duckdb_conn.execute(
        """SELECT relative_path, file_id, directory_id FROM lz_devskim_findings WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    findings_by_path = {row[0]: (row[1], row[2]) for row in result}

    # src/crypto.cs findings should have correct IDs
    assert findings_by_path["src/crypto.cs"][0] == "f-crypto-001"
    assert findings_by_path["src/crypto.cs"][1] == "d-src-001"

    # src/serializer.cs findings should have correct IDs
    assert findings_by_path["src/serializer.cs"][0] == "f-serializer-002"
    assert findings_by_path["src/serializer.cs"][1] == "d-src-001"


def test_devskim_adapter_skips_files_not_in_layout(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter warns and skips files not found in layout."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "devskim_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    # Seed layout with only one of the files with issues
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000001", "d-000000000002", "src/crypto.cs"),
            # src/serializer.cs intentionally omitted
        ],
    )

    logs: list[str] = []
    devskim_repo = DevskimRepository(duckdb_conn)
    adapter = DevskimAdapter(
        tool_run_repo,
        layout_repo,
        devskim_repo,
        logger=logs.append,
    )
    run_pk = adapter.persist(payload)

    # Verify warning was logged for missing file
    assert any("skipping file not in layout" in log and "serializer.cs" in log for log in logs)

    # Verify only findings for files in layout were inserted
    result = duckdb_conn.execute(
        """SELECT relative_path FROM lz_devskim_findings WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    paths = {row[0] for row in result}
    assert "src/crypto.cs" in paths
    assert "src/serializer.cs" not in paths


def test_devskim_adapter_deduplicates_findings(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter handles duplicate finding entries correctly."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "devskim_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    # Add duplicate finding to fixture
    payload = copy.deepcopy(payload)
    duplicate_issue = payload["data"]["files"][0]["issues"][0].copy()
    payload["data"]["files"][0]["issues"].append(duplicate_issue)

    # Seed layout with files
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000001", "d-000000000002", "src/crypto.cs"),
            ("f-000000000002", "d-000000000002", "src/serializer.cs"),
        ],
    )

    logs: list[str] = []
    devskim_repo = DevskimRepository(duckdb_conn)
    adapter = DevskimAdapter(
        tool_run_repo,
        layout_repo,
        devskim_repo,
        logger=logs.append,
    )
    run_pk = adapter.persist(payload)

    # Verify warning was logged for duplicate
    assert any("skipping duplicate" in log for log in logs)

    # Verify only unique findings were inserted (3, not 4)
    result = duckdb_conn.execute(
        """SELECT COUNT(*) FROM lz_devskim_findings WHERE run_pk = ?""",
        [run_pk],
    ).fetchone()

    assert result[0] == 3  # Original 3 findings, duplicate was skipped
