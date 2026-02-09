"""Unit tests for git-blame-scanner analyze script.

Tests cover:
- Output structure validation
- Metadata field requirements
- Path normalization
- FileBlameStats and AuthorStats dataclasses
- compute_author_stats function
- Metric value ranges
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest

# Import from analyze script
from analyze import (
    FileBlameStats,
    AuthorStats,
    compute_author_stats,
    TOOL_NAME,
    TOOL_VERSION,
    SCHEMA_VERSION,
)


# Fixture: sample analysis output
@pytest.fixture
def sample_output() -> dict:
    """Create a sample output.json for testing."""
    return {
        "metadata": {
            "tool_name": "git-blame-scanner",
            "tool_version": "1.0.0",
            "run_id": "test-run-id",
            "repo_id": "test-repo-id",
            "branch": "main",
            "commit": "a" * 40,
            "timestamp": "2025-01-01T00:00:00Z",
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "git-blame-scanner",
            "tool_version": "1.0.0",
            "files": [
                {
                    "path": "src/main.py",
                    "total_lines": 100,
                    "unique_authors": 2,
                    "top_author": "alice@example.com",
                    "top_author_lines": 80,
                    "top_author_pct": 80.0,
                    "last_modified": "2025-01-01",
                    "churn_30d": 2,
                    "churn_90d": 5,
                },
                {
                    "path": "src/utils.py",
                    "total_lines": 50,
                    "unique_authors": 1,
                    "top_author": "bob@example.com",
                    "top_author_lines": 50,
                    "top_author_pct": 100.0,
                    "last_modified": "2024-12-01",
                    "churn_30d": 0,
                    "churn_90d": 0,
                },
            ],
            "authors": [
                {
                    "author_email": "alice@example.com",
                    "total_files": 1,
                    "total_lines": 80,
                    "exclusive_files": 0,
                    "avg_ownership_pct": 80.0,
                },
                {
                    "author_email": "bob@example.com",
                    "total_files": 2,
                    "total_lines": 70,
                    "exclusive_files": 1,
                    "avg_ownership_pct": 60.0,
                },
            ],
            "summary": {
                "total_files_analyzed": 2,
                "total_authors": 2,
                "single_author_files": 1,
                "single_author_pct": 50.0,
                "high_concentration_files": 2,
                "high_concentration_pct": 100.0,
                "stale_files_90d": 1,
                "knowledge_silo_count": 0,
                "avg_authors_per_file": 1.5,
            },
            "knowledge_silos": [],
        },
    }


def test_analyze_output_structure(sample_output: dict):
    """Test that analyze produces valid output structure."""
    # Verify top-level structure
    assert "metadata" in sample_output
    assert "data" in sample_output

    # Verify data structure
    data = sample_output["data"]
    assert "tool" in data
    assert "files" in data
    assert "authors" in data
    assert "summary" in data
    assert isinstance(data["files"], list)
    assert isinstance(data["authors"], list)


def test_analyze_metadata_fields(sample_output: dict):
    """Test that all required metadata fields are present."""
    required_fields = [
        "tool_name", "tool_version", "run_id", "repo_id",
        "branch", "commit", "timestamp", "schema_version"
    ]
    metadata = sample_output["metadata"]

    for field in required_fields:
        assert field in metadata, f"Missing required field: {field}"
        assert metadata[field], f"Field is empty: {field}"


def test_path_normalization(sample_output: dict):
    """Test that all paths are repo-relative.

    Paths MUST be repo-relative (no leading /, ./, or ..)
    See docs/TOOL_REQUIREMENTS.md for path requirements.
    """
    data = sample_output["data"]

    for file_entry in data.get("files", []):
        path = file_entry.get("path", "")
        # Must not be absolute
        assert not path.startswith("/"), f"Absolute path found: {path}"
        # Must not have ./ prefix
        assert not path.startswith("./"), f"Path has ./ prefix: {path}"
        # Must not contain .. segments
        assert ".." not in path.split("/"), f"Path has .. segment: {path}"
        # Must use forward slashes
        assert "\\" not in path, f"Path has backslash: {path}"


def test_file_required_fields(sample_output: dict):
    """Test that file entries have all required fields."""
    required_fields = [
        "path", "total_lines", "unique_authors", "top_author",
        "top_author_pct", "last_modified", "churn_30d", "churn_90d"
    ]
    data = sample_output["data"]

    for file_entry in data.get("files", []):
        for field in required_fields:
            assert field in file_entry, f"Missing required field: {field}"


def test_author_required_fields(sample_output: dict):
    """Test that author entries have all required fields."""
    required_fields = [
        "author_email", "total_files", "total_lines",
        "exclusive_files", "avg_ownership_pct"
    ]
    data = sample_output["data"]

    for author_entry in data.get("authors", []):
        for field in required_fields:
            assert field in author_entry, f"Missing required field: {field}"


def test_summary_required_fields(sample_output: dict):
    """Test that summary has all required fields."""
    required_fields = [
        "total_files_analyzed", "total_authors", "single_author_files",
        "single_author_pct", "high_concentration_files", "high_concentration_pct",
        "stale_files_90d", "knowledge_silo_count", "avg_authors_per_file"
    ]
    summary = sample_output["data"]["summary"]

    for field in required_fields:
        assert field in summary, f"Missing required field: {field}"


class TestFileBlameStats:
    """Tests for FileBlameStats dataclass."""

    def test_create_file_blame_stats(self):
        """Test creating a FileBlameStats instance."""
        stats = FileBlameStats(
            relative_path="src/main.py",
            total_lines=100,
            unique_authors=2,
            top_author="alice@example.com",
            top_author_lines=80,
            top_author_pct=80.0,
            last_modified="2025-01-01",
            churn_30d=2,
            churn_90d=5,
            authors={"alice@example.com": 80, "bob@example.com": 20},
        )

        assert stats.relative_path == "src/main.py"
        assert stats.total_lines == 100
        assert stats.unique_authors == 2
        assert stats.top_author_pct == 80.0

    def test_top_author_pct_range(self):
        """Test that top_author_pct is between 0 and 100."""
        stats = FileBlameStats(
            relative_path="test.py",
            total_lines=100,
            unique_authors=1,
            top_author="alice@example.com",
            top_author_lines=100,
            top_author_pct=100.0,
            last_modified="2025-01-01",
            churn_30d=0,
            churn_90d=0,
            authors={"alice@example.com": 100},
        )

        assert 0 <= stats.top_author_pct <= 100

    def test_churn_invariant(self):
        """Test that churn_30d <= churn_90d."""
        stats = FileBlameStats(
            relative_path="test.py",
            total_lines=50,
            unique_authors=1,
            top_author="alice@example.com",
            top_author_lines=50,
            top_author_pct=100.0,
            last_modified="2025-01-01",
            churn_30d=3,
            churn_90d=5,
            authors={"alice@example.com": 50},
        )

        assert stats.churn_30d <= stats.churn_90d


class TestAuthorStats:
    """Tests for AuthorStats dataclass."""

    def test_create_author_stats(self):
        """Test creating an AuthorStats instance."""
        stats = AuthorStats(
            author_email="alice@example.com",
            total_files=5,
            total_lines=500,
            exclusive_files=2,
            avg_ownership_pct=75.0,
        )

        assert stats.author_email == "alice@example.com"
        assert stats.total_files == 5
        assert stats.exclusive_files == 2

    def test_exclusive_files_le_total_files(self):
        """Test that exclusive_files <= total_files."""
        stats = AuthorStats(
            author_email="alice@example.com",
            total_files=10,
            total_lines=1000,
            exclusive_files=3,
            avg_ownership_pct=80.0,
        )

        assert stats.exclusive_files <= stats.total_files


class TestComputeAuthorStats:
    """Tests for compute_author_stats function."""

    def test_compute_author_stats_single_author(self):
        """Test compute_author_stats with single author files."""
        file_stats = [
            FileBlameStats(
                relative_path="file1.py",
                total_lines=100,
                unique_authors=1,
                top_author="alice@example.com",
                top_author_lines=100,
                top_author_pct=100.0,
                last_modified="2025-01-01",
                churn_30d=0,
                churn_90d=0,
                authors={"alice@example.com": 100},
            ),
            FileBlameStats(
                relative_path="file2.py",
                total_lines=50,
                unique_authors=1,
                top_author="alice@example.com",
                top_author_lines=50,
                top_author_pct=100.0,
                last_modified="2025-01-01",
                churn_30d=0,
                churn_90d=0,
                authors={"alice@example.com": 50},
            ),
        ]

        author_stats = compute_author_stats(file_stats)

        assert len(author_stats) == 1
        assert author_stats[0].author_email == "alice@example.com"
        assert author_stats[0].total_files == 2
        assert author_stats[0].total_lines == 150
        assert author_stats[0].exclusive_files == 2
        assert author_stats[0].avg_ownership_pct == 100.0

    def test_compute_author_stats_multiple_authors(self):
        """Test compute_author_stats with multiple authors."""
        file_stats = [
            FileBlameStats(
                relative_path="shared.py",
                total_lines=100,
                unique_authors=2,
                top_author="alice@example.com",
                top_author_lines=60,
                top_author_pct=60.0,
                last_modified="2025-01-01",
                churn_30d=0,
                churn_90d=0,
                authors={"alice@example.com": 60, "bob@example.com": 40},
            ),
        ]

        author_stats = compute_author_stats(file_stats)

        assert len(author_stats) == 2

        alice = next(a for a in author_stats if a.author_email == "alice@example.com")
        bob = next(a for a in author_stats if a.author_email == "bob@example.com")

        assert alice.total_lines == 60
        assert bob.total_lines == 40
        assert alice.exclusive_files == 0
        assert bob.exclusive_files == 0

    def test_compute_author_stats_empty(self):
        """Test compute_author_stats with empty input."""
        author_stats = compute_author_stats([])
        assert len(author_stats) == 0


class TestMetricRanges:
    """Tests for metric value ranges."""

    def test_unique_authors_positive(self, sample_output: dict):
        """Test that unique_authors is always >= 1."""
        data = sample_output["data"]
        for file_entry in data.get("files", []):
            assert file_entry["unique_authors"] >= 1

    def test_top_author_pct_range(self, sample_output: dict):
        """Test that top_author_pct is between 0 and 100."""
        data = sample_output["data"]
        for file_entry in data.get("files", []):
            pct = file_entry["top_author_pct"]
            assert 0 <= pct <= 100, f"Invalid top_author_pct: {pct}"

    def test_churn_non_negative(self, sample_output: dict):
        """Test that churn values are non-negative."""
        data = sample_output["data"]
        for file_entry in data.get("files", []):
            assert file_entry["churn_30d"] >= 0
            assert file_entry["churn_90d"] >= 0

    def test_churn_invariant(self, sample_output: dict):
        """Test that churn_30d <= churn_90d for all files."""
        data = sample_output["data"]
        for file_entry in data.get("files", []):
            assert file_entry["churn_30d"] <= file_entry["churn_90d"], (
                f"Churn invariant violated: churn_30d={file_entry['churn_30d']} > "
                f"churn_90d={file_entry['churn_90d']}"
            )


class TestToolConstants:
    """Tests for tool constants."""

    def test_tool_name(self):
        """Test TOOL_NAME constant."""
        assert TOOL_NAME == "git-blame-scanner"

    def test_tool_version(self):
        """Test TOOL_VERSION constant."""
        assert TOOL_VERSION == "1.0.0"

    def test_schema_version(self):
        """Test SCHEMA_VERSION constant."""
        assert SCHEMA_VERSION == "1.0.0"
