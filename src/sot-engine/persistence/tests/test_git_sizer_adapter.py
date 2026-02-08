from __future__ import annotations

import json
from pathlib import Path

import pytest

from persistence.adapters import GitSizerAdapter
from persistence.repositories import (
    GitSizerRepository,
    ToolRunRepository,
)


def test_git_sizer_adapter_inserts_metrics(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
) -> None:
    """Verify adapter correctly persists repository-level metrics."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "git_sizer_output.json"
    payload = json.loads(fixture_path.read_text())

    git_sizer_repo = GitSizerRepository(duckdb_conn)
    adapter = GitSizerAdapter(
        tool_run_repo,
        git_sizer_repo=git_sizer_repo,
    )
    run_pk = adapter.persist(payload)

    # Verify metrics were inserted
    result = duckdb_conn.execute(
        """SELECT health_grade, commit_count, blob_count, max_blob_size
           FROM lz_git_sizer_metrics WHERE run_pk = ?""",
        [run_pk],
    ).fetchone()

    assert result is not None
    assert result[0] == "B"  # health_grade
    assert result[1] == 120  # commit_count
    assert result[2] == 300  # blob_count
    assert result[3] == 262144  # max_blob_size


def test_git_sizer_adapter_inserts_violations(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
) -> None:
    """Verify adapter correctly persists threshold violations."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "git_sizer_output.json"
    payload = json.loads(fixture_path.read_text())

    git_sizer_repo = GitSizerRepository(duckdb_conn)
    adapter = GitSizerAdapter(
        tool_run_repo,
        git_sizer_repo=git_sizer_repo,
    )
    run_pk = adapter.persist(payload)

    # Verify violations were inserted
    result = duckdb_conn.execute(
        """SELECT metric, raw_value, level, object_ref
           FROM lz_git_sizer_violations WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    assert len(result) == 1  # 1 violation in fixture
    assert result[0][0] == "max_blob_size"
    assert result[0][1] == 262144
    assert result[0][2] == 2  # level
    assert result[0][3] == "large.bin"  # object_ref


def test_git_sizer_adapter_inserts_lfs_candidates(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
) -> None:
    """Verify adapter correctly persists LFS migration candidates."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "git_sizer_output.json"
    payload = json.loads(fixture_path.read_text())

    git_sizer_repo = GitSizerRepository(duckdb_conn)
    adapter = GitSizerAdapter(
        tool_run_repo,
        git_sizer_repo=git_sizer_repo,
    )
    run_pk = adapter.persist(payload)

    # Verify LFS candidates were inserted
    result = duckdb_conn.execute(
        """SELECT file_path FROM lz_git_sizer_lfs_candidates WHERE run_pk = ?""",
        [run_pk],
    ).fetchall()

    assert len(result) == 1  # 1 LFS candidate in fixture
    assert result[0][0] == "large.bin"


def test_git_sizer_adapter_validates_health_grade(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
) -> None:
    """Verify adapter validates health_grade is a valid value."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "git_sizer_output.json"
    payload = json.loads(fixture_path.read_text())

    # Set invalid health grade
    payload["data"]["health_grade"] = "Z"  # Invalid grade

    git_sizer_repo = GitSizerRepository(duckdb_conn)
    adapter = GitSizerAdapter(
        tool_run_repo,
        git_sizer_repo=git_sizer_repo,
    )

    with pytest.raises(ValueError):
        adapter.persist(payload)
