"""Tests for git-blame-scanner adapter.

Tests validate:
1. Schema path exists
2. Data quality validation rejects invalid data
3. Persistence correctly inserts file summaries and author stats
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pytest

from persistence.adapters.git_blame_scanner_adapter import GitBlameScannerAdapter, SCHEMA_PATH
from persistence.entities import GitBlameFileSummary, GitBlameAuthorStats
from persistence.repositories import (
    LayoutRepository,
    GitBlameRepository,
    ToolRunRepository,
)


@pytest.fixture
def in_memory_db():
    """Create in-memory DuckDB with schema."""
    conn = duckdb.connect(":memory:")
    schema_path = Path(__file__).resolve().parents[1] / "schema.sql"
    conn.execute(schema_path.read_text())
    return conn


@pytest.fixture
def sample_payload() -> dict:
    """Create a minimal valid payload for testing."""
    return {
        "metadata": {
            "tool_name": "git-blame-scanner",
            "tool_version": "1.0.0",
            "run_id": "550e8400-e29b-41d4-a716-446655440000",
            "repo_id": "550e8400-e29b-41d4-a716-446655440001",
            "branch": "main",
            "commit": "a" * 40,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "git-blame-scanner",
            "files": [
                {
                    "path": "src/main.py",
                    "total_lines": 100,
                    "unique_authors": 2,
                    "top_author": "alice@example.com",
                    "top_author_lines": 75,
                    "top_author_pct": 75.0,
                    "last_modified": "2026-01-15",
                    "churn_30d": 5,
                    "churn_90d": 15,
                },
                {
                    "path": "src/utils/helpers.py",
                    "total_lines": 50,
                    "unique_authors": 1,
                    "top_author": "bob@example.com",
                    "top_author_lines": 50,
                    "top_author_pct": 100.0,
                    "last_modified": "2026-01-10",
                    "churn_30d": 2,
                    "churn_90d": 8,
                },
            ],
            "authors": [
                {
                    "author_email": "alice@example.com",
                    "total_files": 5,
                    "total_lines": 300,
                    "exclusive_files": 2,
                    "avg_ownership_pct": 65.0,
                },
                {
                    "author_email": "bob@example.com",
                    "total_files": 3,
                    "total_lines": 150,
                    "exclusive_files": 1,
                    "avg_ownership_pct": 80.0,
                },
            ],
            "summary": {
                "total_files_analyzed": 2,
                "total_authors": 2,
                "single_author_files": 1,
                "single_author_pct": 50.0,
                "high_concentration_files": 1,
                "high_concentration_pct": 50.0,
                "stale_files_90d": 0,
                "knowledge_silo_count": 1,
                "avg_authors_per_file": 1.5,
            },
        },
    }


def test_adapter_schema_path_exists():
    """Verify the schema path is correctly configured."""
    assert SCHEMA_PATH.exists(), f"Schema not found at {SCHEMA_PATH}"


def test_adapter_validate_quality_rejects_empty_path(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    sample_payload,
):
    """Test that quality validation rejects empty paths."""
    sample_payload["data"]["files"][0]["path"] = ""

    git_blame_repo = GitBlameRepository(duckdb_conn)
    adapter = GitBlameScannerAdapter(
        run_repo=tool_run_repo,
        layout_repo=layout_repo,
        git_blame_repo=git_blame_repo,
    )

    with pytest.raises(ValueError) as exc_info:
        adapter.validate_quality(sample_payload["data"])

    assert "quality validation failed" in str(exc_info.value).lower()


def test_adapter_validate_quality_rejects_negative_churn(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    sample_payload,
):
    """Test that quality validation rejects negative churn values."""
    sample_payload["data"]["files"][0]["churn_30d"] = -1

    git_blame_repo = GitBlameRepository(duckdb_conn)
    adapter = GitBlameScannerAdapter(
        run_repo=tool_run_repo,
        layout_repo=layout_repo,
        git_blame_repo=git_blame_repo,
    )

    with pytest.raises(ValueError) as exc_info:
        adapter.validate_quality(sample_payload["data"])

    assert "quality validation failed" in str(exc_info.value).lower()


def test_adapter_validate_quality_rejects_invalid_churn_invariant(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    sample_payload,
):
    """Test that quality validation rejects churn_30d > churn_90d."""
    sample_payload["data"]["files"][0]["churn_30d"] = 20
    sample_payload["data"]["files"][0]["churn_90d"] = 10

    git_blame_repo = GitBlameRepository(duckdb_conn)
    adapter = GitBlameScannerAdapter(
        run_repo=tool_run_repo,
        layout_repo=layout_repo,
        git_blame_repo=git_blame_repo,
    )

    with pytest.raises(ValueError) as exc_info:
        adapter.validate_quality(sample_payload["data"])

    assert "quality validation failed" in str(exc_info.value).lower()


def test_adapter_validate_quality_rejects_invalid_ownership_pct(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    sample_payload,
):
    """Test that quality validation rejects ownership percentage > 100."""
    sample_payload["data"]["files"][0]["top_author_pct"] = 150.0

    git_blame_repo = GitBlameRepository(duckdb_conn)
    adapter = GitBlameScannerAdapter(
        run_repo=tool_run_repo,
        layout_repo=layout_repo,
        git_blame_repo=git_blame_repo,
    )

    with pytest.raises(ValueError) as exc_info:
        adapter.validate_quality(sample_payload["data"])

    assert "quality validation failed" in str(exc_info.value).lower()


def test_adapter_validate_quality_rejects_zero_unique_authors(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    sample_payload,
):
    """Test that quality validation rejects unique_authors < 1."""
    sample_payload["data"]["files"][0]["unique_authors"] = 0

    git_blame_repo = GitBlameRepository(duckdb_conn)
    adapter = GitBlameScannerAdapter(
        run_repo=tool_run_repo,
        layout_repo=layout_repo,
        git_blame_repo=git_blame_repo,
    )

    with pytest.raises(ValueError) as exc_info:
        adapter.validate_quality(sample_payload["data"])

    assert "quality validation failed" in str(exc_info.value).lower()


def test_adapter_validate_quality_accepts_valid_data(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    sample_payload,
):
    """Test that quality validation accepts valid data."""
    git_blame_repo = GitBlameRepository(duckdb_conn)
    adapter = GitBlameScannerAdapter(
        run_repo=tool_run_repo,
        layout_repo=layout_repo,
        git_blame_repo=git_blame_repo,
    )

    # Should not raise
    adapter.validate_quality(sample_payload["data"])


def test_adapter_persist(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    seed_layout,
    sample_payload,
):
    """Test persisting data through the adapter."""
    repo_id = sample_payload["metadata"]["repo_id"]
    run_id = sample_payload["metadata"]["run_id"]

    # Seed layout with files referenced in the payload
    seed_layout(
        repo_id,
        run_id,
        [
            ("f-000000000001", "d-000000000002", "src/main.py"),
            ("f-000000000002", "d-000000000003", "src/utils/helpers.py"),
        ],
    )

    git_blame_repo = GitBlameRepository(duckdb_conn)
    adapter = GitBlameScannerAdapter(
        run_repo=tool_run_repo,
        layout_repo=layout_repo,
        git_blame_repo=git_blame_repo,
    )

    run_pk = adapter.persist(sample_payload)

    # Verify file summaries were inserted
    file_rows = duckdb_conn.execute(
        """
        SELECT file_id, relative_path, total_lines, unique_authors, top_author,
               top_author_pct, churn_30d, churn_90d
        FROM lz_git_blame_summary
        WHERE run_pk = ?
        ORDER BY relative_path
        """,
        [run_pk],
    ).fetchall()

    assert len(file_rows) == 2
    assert file_rows[0] == (
        "f-000000000001", "src/main.py", 100, 2, "alice@example.com", 75.0, 5, 15
    )
    assert file_rows[1] == (
        "f-000000000002", "src/utils/helpers.py", 50, 1, "bob@example.com", 100.0, 2, 8
    )

    # Verify author stats were inserted
    author_rows = duckdb_conn.execute(
        """
        SELECT author_email, total_files, total_lines, exclusive_files, avg_ownership_pct
        FROM lz_git_blame_author_stats
        WHERE run_pk = ?
        ORDER BY author_email
        """,
        [run_pk],
    ).fetchall()

    assert len(author_rows) == 2
    assert author_rows[0] == ("alice@example.com", 5, 300, 2, 65.0)
    assert author_rows[1] == ("bob@example.com", 3, 150, 1, 80.0)


def test_adapter_raises_on_missing_layout(
    duckdb_conn,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    sample_payload,
):
    """Test that adapter raises KeyError when layout run is missing."""
    git_blame_repo = GitBlameRepository(duckdb_conn)
    adapter = GitBlameScannerAdapter(
        run_repo=tool_run_repo,
        layout_repo=layout_repo,
        git_blame_repo=git_blame_repo,
    )

    with pytest.raises(KeyError) as exc_info:
        adapter.persist(sample_payload)

    assert "layout" in str(exc_info.value).lower()
