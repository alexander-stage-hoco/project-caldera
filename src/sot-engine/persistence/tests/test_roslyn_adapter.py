from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path

import pytest

from persistence.adapters import RoslynAdapter
from persistence.entities import LayoutDirectory, LayoutFile, ToolRun
from persistence.repositories import (
    LayoutRepository,
    RoslynRepository,
    ToolRunRepository,
)


def test_roslyn_adapter_inserts_violations(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter correctly maps violations to RoslynViolation entities."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "roslyn_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    # Seed layout with files referenced by roslyn violations
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000001", "d-000000000002", "src/app.py"),
            ("f-000000000002", "d-000000000003", "src/utils/helpers.py"),
        ],
    )

    roslyn_repo = RoslynRepository(duckdb_conn)
    adapter = RoslynAdapter(
        tool_run_repo,
        layout_repo,
        roslyn_repo,
    )
    run_pk = adapter.persist(payload)

    # Verify violations were inserted
    result = duckdb_conn.execute(
        """SELECT relative_path, rule_id, dd_category, severity, line_start
           FROM lz_roslyn_violations WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    assert len(result) == 3  # 3 violations in fixture
    rule_ids = {row[1] for row in result}
    assert "CS0219" in rule_ids
    assert "SCS0016" in rule_ids
    assert "CA1063" in rule_ids


def test_roslyn_adapter_raises_on_missing_layout(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
) -> None:
    """Verify adapter raises KeyError when no layout run exists for collection."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "roslyn_output.json"
    payload = json.loads(fixture_path.read_text())

    # Don't seed layout - should raise KeyError
    roslyn_repo = RoslynRepository(duckdb_conn)
    adapter = RoslynAdapter(
        tool_run_repo,
        layout_repo,
        roslyn_repo,
    )

    with pytest.raises(KeyError):
        adapter.persist(payload)


def test_roslyn_adapter_uses_layout_directory_id(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify file_id and directory_id are correctly linked from layout."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "roslyn_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    # Seed layout with specific file and directory IDs
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-app-001", "d-src-001", "src/app.py"),
            ("f-helpers-002", "d-utils-002", "src/utils/helpers.py"),
        ],
    )

    roslyn_repo = RoslynRepository(duckdb_conn)
    adapter = RoslynAdapter(
        tool_run_repo,
        layout_repo,
        roslyn_repo,
    )
    run_pk = adapter.persist(payload)

    # Verify violations have correct file_id and directory_id
    result = duckdb_conn.execute(
        """SELECT relative_path, file_id, directory_id FROM lz_roslyn_violations WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    violations_by_path = {row[0]: (row[1], row[2]) for row in result}

    # src/app.py violations should have correct IDs
    assert violations_by_path["src/app.py"][0] == "f-app-001"
    assert violations_by_path["src/app.py"][1] == "d-src-001"

    # src/utils/helpers.py violations should have correct IDs
    assert violations_by_path["src/utils/helpers.py"][0] == "f-helpers-002"
    assert violations_by_path["src/utils/helpers.py"][1] == "d-utils-002"


def test_roslyn_adapter_skips_files_not_in_layout(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter warns and skips files not found in layout."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "roslyn_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    # Seed layout with only one of the files
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000001", "d-000000000002", "src/app.py"),
            # src/utils/helpers.py intentionally omitted
        ],
    )

    logs: list[str] = []
    roslyn_repo = RoslynRepository(duckdb_conn)
    adapter = RoslynAdapter(
        tool_run_repo,
        layout_repo,
        roslyn_repo,
        logger=logs.append,
    )
    run_pk = adapter.persist(payload)

    # Verify warning was logged for missing file
    assert any("skipping file not in layout" in log and "helpers.py" in log for log in logs)

    # Verify only violations for files in layout were inserted
    result = duckdb_conn.execute(
        """SELECT relative_path FROM lz_roslyn_violations WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    paths = {row[0] for row in result}
    assert "src/app.py" in paths
    assert "src/utils/helpers.py" not in paths


def test_roslyn_adapter_deduplicates_violations(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
) -> None:
    """Verify adapter handles duplicate violation entries correctly."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "roslyn_output.json"
    payload = json.loads(fixture_path.read_text())

    repo_id = payload["metadata"]["repo_id"]
    run_id = payload["metadata"]["run_id"]

    # Add duplicate violation to fixture
    payload = copy.deepcopy(payload)
    duplicate_violation = payload["data"]["files"][0]["violations"][0].copy()
    payload["data"]["files"][0]["violations"].append(duplicate_violation)

    # Seed layout with files
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000001", "d-000000000002", "src/app.py"),
            ("f-000000000002", "d-000000000003", "src/utils/helpers.py"),
        ],
    )

    logs: list[str] = []
    roslyn_repo = RoslynRepository(duckdb_conn)
    adapter = RoslynAdapter(
        tool_run_repo,
        layout_repo,
        roslyn_repo,
        logger=logs.append,
    )
    run_pk = adapter.persist(payload)

    # Verify warning was logged for duplicate
    assert any("skipping duplicate violation" in log for log in logs)

    # Verify only unique violations were inserted (3, not 4)
    result = duckdb_conn.execute(
        """SELECT COUNT(*) FROM lz_roslyn_violations WHERE run_pk = ?""",
        [run_pk],
    ).fetchone()

    assert result[0] == 3  # Original 3 violations, duplicate was skipped
