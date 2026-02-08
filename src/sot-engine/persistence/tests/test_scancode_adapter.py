from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from persistence.adapters import ScancodeAdapter
from persistence.repositories import (
    LayoutRepository,
    ScancodeRepository,
    ToolRunRepository,
)


def test_scancode_adapter_inserts_file_licenses(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter correctly persists file license findings."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "scancode_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    # Seed layout with files referenced by scancode
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000001", "d-000000000001", "LICENSE"),
            ("f-000000000002", "d-000000000002", "src/main.py"),
        ],
    )

    scancode_repo = ScancodeRepository(duckdb_conn)
    adapter = ScancodeAdapter(
        tool_run_repo,
        layout_repo,
        scancode_repo,
    )
    run_pk = adapter.persist(payload)

    # Verify file licenses were inserted
    result = duckdb_conn.execute(
        """SELECT relative_path, spdx_id, category, confidence
           FROM lz_scancode_file_licenses WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    assert len(result) == 2  # 2 findings in fixture
    licenses_by_path = {row[0]: row for row in result}

    assert licenses_by_path["LICENSE"][1] == "MIT"
    assert licenses_by_path["LICENSE"][2] == "permissive"
    assert licenses_by_path["LICENSE"][3] == 0.95

    assert licenses_by_path["src/main.py"][1] == "Apache-2.0"


def test_scancode_adapter_inserts_summary(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter correctly persists summary record."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "scancode_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000001", "d-000000000001", "LICENSE"),
            ("f-000000000002", "d-000000000002", "src/main.py"),
        ],
    )

    scancode_repo = ScancodeRepository(duckdb_conn)
    adapter = ScancodeAdapter(
        tool_run_repo,
        layout_repo,
        scancode_repo,
    )
    run_pk = adapter.persist(payload)

    # Verify summary was inserted
    result = duckdb_conn.execute(
        """SELECT total_files_scanned, files_with_licenses, overall_risk,
                  has_permissive, has_copyleft
           FROM lz_scancode_summary WHERE run_pk = ?""",
        [run_pk],
    ).fetchone()

    assert result is not None
    assert result[0] == 3  # total_files_scanned
    assert result[1] == 2  # files_with_licenses
    assert result[2] == "low"  # overall_risk
    assert result[3] is True  # has_permissive
    assert result[4] is False  # has_copyleft


def test_scancode_adapter_validates_confidence(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter validates confidence is in valid range 0-1."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "scancode_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    # Set invalid confidence value
    payload = copy.deepcopy(payload)
    payload["data"]["findings"][0]["confidence"] = 1.5  # Invalid: > 1

    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000001", "d-000000000001", "LICENSE"),
            ("f-000000000002", "d-000000000002", "src/main.py"),
        ],
    )

    scancode_repo = ScancodeRepository(duckdb_conn)
    adapter = ScancodeAdapter(
        tool_run_repo,
        layout_repo,
        scancode_repo,
    )

    with pytest.raises(ValueError):
        adapter.persist(payload)


def test_scancode_adapter_raises_on_missing_layout(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
) -> None:
    """Verify adapter raises KeyError when no layout run exists."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "scancode_output.json"
    payload = json.loads(fixture_path.read_text())

    scancode_repo = ScancodeRepository(duckdb_conn)
    adapter = ScancodeAdapter(
        tool_run_repo,
        layout_repo,
        scancode_repo,
    )

    with pytest.raises(KeyError):
        adapter.persist(payload)
