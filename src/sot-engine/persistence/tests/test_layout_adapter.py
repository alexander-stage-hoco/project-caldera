from __future__ import annotations

import copy
import json
from datetime import datetime
from pathlib import Path

import pytest

from persistence.adapters import LayoutAdapter
from persistence.repositories import (
    LayoutRepository,
    ToolRunRepository,
)


def test_layout_adapter_inserts_files(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
) -> None:
    """Verify adapter correctly creates LayoutFile entities from JSON."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "layout_output.json"
    payload = json.loads(fixture_path.read_text())

    adapter = LayoutAdapter(
        tool_run_repo,
        layout_repo,
    )
    run_pk = adapter.persist(payload)

    # Verify files were inserted
    result = duckdb_conn.execute(
        """SELECT relative_path, filename, extension, language, size_bytes
           FROM lz_layout_files WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    # Fixture has 14 files (src/app.py, src/utils/helpers.py, etc.)
    assert len(result) >= 2  # At least the core files

    paths = {row[0] for row in result}
    assert "src/app.py" in paths
    assert "src/utils/helpers.py" in paths


def test_layout_adapter_inserts_directories(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
) -> None:
    """Verify adapter correctly creates LayoutDirectory entities."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "layout_output.json"
    payload = json.loads(fixture_path.read_text())

    adapter = LayoutAdapter(
        tool_run_repo,
        layout_repo,
    )
    run_pk = adapter.persist(payload)

    # Verify directories were inserted
    result = duckdb_conn.execute(
        """SELECT relative_path, depth, parent_id, directory_id
           FROM lz_layout_directories WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    # Fixture has 4 directories: "", "src", "src/utils", "config"
    assert len(result) == 4

    paths = {row[0] for row in result}
    assert "." in paths  # root directory normalized to "."
    assert "src" in paths
    assert "src/utils" in paths
    assert "config" in paths


def test_layout_adapter_creates_directory_tree(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
) -> None:
    """Verify adapter correctly sets parent_id relationships."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "layout_output.json"
    payload = json.loads(fixture_path.read_text())

    adapter = LayoutAdapter(
        tool_run_repo,
        layout_repo,
    )
    run_pk = adapter.persist(payload)

    # Query directories with their parent relationships
    result = duckdb_conn.execute(
        """SELECT directory_id, relative_path, parent_id
           FROM lz_layout_directories WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    dirs_by_id = {row[0]: {"path": row[1], "parent_id": row[2]} for row in result}
    dirs_by_path = {row[1]: {"id": row[0], "parent_id": row[2]} for row in result}

    # Root directory should have no parent
    assert dirs_by_path["."]["parent_id"] is None

    # src directory should have root as parent
    src_parent_id = dirs_by_path["src"]["parent_id"]
    assert src_parent_id == dirs_by_path["."]["id"]

    # src/utils should have src as parent
    utils_parent_id = dirs_by_path["src/utils"]["parent_id"]
    assert utils_parent_id == dirs_by_path["src"]["id"]


def test_layout_adapter_normalizes_paths(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
) -> None:
    """Verify paths are normalized to repo-relative format."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "layout_output.json"
    payload = json.loads(fixture_path.read_text())

    adapter = LayoutAdapter(
        tool_run_repo,
        layout_repo,
    )
    run_pk = adapter.persist(payload)

    # Verify all file paths are repo-relative (no leading slash, no backslashes)
    result = duckdb_conn.execute(
        """SELECT relative_path FROM lz_layout_files WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    for row in result:
        path = row[0]
        assert not path.startswith("/"), f"Path should not start with /: {path}"
        assert "\\" not in path, f"Path should not contain backslashes: {path}"
        assert not path.startswith("./"), f"Path should not start with ./: {path}"


def test_layout_adapter_calculates_depth(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
) -> None:
    """Verify directory depth is correctly calculated."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "layout_output.json"
    payload = json.loads(fixture_path.read_text())

    adapter = LayoutAdapter(
        tool_run_repo,
        layout_repo,
    )
    run_pk = adapter.persist(payload)

    # Query directories with their depths
    result = duckdb_conn.execute(
        """SELECT relative_path, depth FROM lz_layout_directories WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    depths_by_path = {row[0]: row[1] for row in result}

    # Verify expected depths
    assert depths_by_path["."] == 0  # root
    assert depths_by_path["src"] == 1  # one level deep
    assert depths_by_path["src/utils"] == 2  # two levels deep
    assert depths_by_path["config"] == 1  # one level deep
