"""Tests for git-fame adapter.

git-fame provides author-level authorship metrics (not per-file), so this
adapter handles per-author records plus a summary record per run.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from persistence.adapters.git_fame_adapter import GitFameAdapter, SCHEMA_PATH
from persistence.repositories import GitFameRepository, ToolRunRepository


@pytest.fixture
def fixture_payload() -> dict:
    """Load the git-fame output fixture."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "git_fame_output.json"
    return json.loads(fixture_path.read_text())


@pytest.fixture
def mock_adapter() -> GitFameAdapter:
    """Create adapter with mocked dependencies for validation-only tests."""
    mock_run_repo = MagicMock(spec=ToolRunRepository)
    mock_git_fame_repo = MagicMock(spec=GitFameRepository)
    return GitFameAdapter(
        run_repo=mock_run_repo,
        git_fame_repo=mock_git_fame_repo,
    )


def test_adapter_schema_path_exists():
    """Verify the schema path is correctly configured."""
    assert SCHEMA_PATH.exists(), f"Schema not found at {SCHEMA_PATH}"


def test_adapter_validate_quality_passes_valid_data(mock_adapter, fixture_payload):
    """Test that valid data passes quality validation."""
    # Should not raise
    mock_adapter.validate_quality(fixture_payload["data"])


def test_adapter_rejects_invalid_hhi(mock_adapter, fixture_payload):
    """Test that HHI outside 0-1 range is rejected."""
    # HHI too high
    payload = copy.deepcopy(fixture_payload)
    payload["data"]["summary"]["hhi_index"] = 1.5
    with pytest.raises(ValueError, match="data quality validation failed"):
        mock_adapter.validate_quality(payload["data"])

    # HHI too low
    payload = copy.deepcopy(fixture_payload)
    payload["data"]["summary"]["hhi_index"] = -0.1
    with pytest.raises(ValueError, match="data quality validation failed"):
        mock_adapter.validate_quality(payload["data"])


def test_adapter_rejects_invalid_ownership(mock_adapter, fixture_payload):
    """Test that ownership percentages not summing to ~100% are rejected."""
    payload = copy.deepcopy(fixture_payload)
    # Set ownership that doesn't sum to 100%
    payload["data"]["authors"][0]["ownership_pct"] = 50.0
    payload["data"]["authors"][1]["ownership_pct"] = 30.0  # Total: 80%

    with pytest.raises(ValueError, match="data quality validation failed"):
        mock_adapter.validate_quality(payload["data"])


def test_adapter_rejects_invalid_bus_factor(mock_adapter, fixture_payload):
    """Test that bus_factor exceeding author_count is rejected."""
    payload = copy.deepcopy(fixture_payload)
    payload["data"]["summary"]["bus_factor"] = 5  # Exceeds author_count=2

    with pytest.raises(ValueError, match="data quality validation failed"):
        mock_adapter.validate_quality(payload["data"])


def test_adapter_rejects_author_without_name(mock_adapter, fixture_payload):
    """Test that authors without name are rejected."""
    payload = copy.deepcopy(fixture_payload)
    # Remove both "name" and "author" fields to trigger validation error
    if "author" in payload["data"]["authors"][0]:
        payload["data"]["authors"][0]["author"] = ""
    if "name" in payload["data"]["authors"][0]:
        payload["data"]["authors"][0]["name"] = ""

    with pytest.raises(ValueError, match="data quality validation failed"):
        mock_adapter.validate_quality(payload["data"])


def test_adapter_persist(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    fixture_payload,
) -> None:
    """Test persisting data through the adapter."""
    git_fame_repo = GitFameRepository(duckdb_conn)
    adapter = GitFameAdapter(tool_run_repo, git_fame_repo=git_fame_repo)

    run_pk = adapter.persist(fixture_payload)

    # Verify summary was inserted
    summary_rows = duckdb_conn.execute(
        """
        SELECT repo_id, author_count, total_loc, hhi_index, bus_factor,
               top_author_pct, top_two_pct
        FROM lz_git_fame_summary
        WHERE run_pk = ?
        """,
        [run_pk],
    ).fetchall()

    assert len(summary_rows) == 1
    assert summary_rows[0] == (
        "22222222-2222-2222-2222-222222222222",
        2,
        1000,
        0.52,
        2,
        60.0,
        100.0,
    )

    # Verify authors were inserted
    author_rows = duckdb_conn.execute(
        """
        SELECT author_name, author_email, surviving_loc, ownership_pct,
               insertions_total, deletions_total, commit_count, files_touched
        FROM lz_git_fame_authors
        WHERE run_pk = ?
        ORDER BY ownership_pct DESC
        """,
        [run_pk],
    ).fetchall()

    assert len(author_rows) == 2
    assert author_rows[0] == (
        "Alice Developer",
        "alice@example.com",
        600,
        60.0,
        800,
        200,
        45,
        25,
    )
    assert author_rows[1] == (
        "Bob Contributor",
        "bob@example.com",
        400,
        40.0,
        500,
        100,
        30,
        18,
    )


def test_adapter_persist_creates_tool_run(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    fixture_payload,
) -> None:
    """Test that persist creates a tool run record."""
    git_fame_repo = GitFameRepository(duckdb_conn)
    adapter = GitFameAdapter(tool_run_repo, git_fame_repo=git_fame_repo)

    run_pk = adapter.persist(fixture_payload)

    # Verify tool run was created
    tool_run = duckdb_conn.execute(
        """
        SELECT tool_name, tool_version, repo_id, run_id
        FROM lz_tool_runs
        WHERE run_pk = ?
        """,
        [run_pk],
    ).fetchone()

    assert tool_run is not None
    assert tool_run[0] == "git-fame"
    assert tool_run[1] == "2.0.0"
    assert tool_run[2] == "22222222-2222-2222-2222-222222222222"
    assert tool_run[3] == "11111111-1111-1111-1111-111111111111"
