"""Shared pytest fixtures for git-sizer tests."""

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_git_sizer_raw_output() -> dict[str, Any]:
    """Sample raw output from git-sizer binary."""
    return {
        "repositorySize": {
            "commits": {
                "count": 100,
                "totalSize": 50000,
                "maxSize": 2048,
            },
            "trees": {
                "count": 250,
                "totalSize": 75000,
                "totalEntries": 1500,
                "maxEntries": 50,
            },
            "blobs": {
                "count": 180,
                "totalSize": 5242880,
                "maxSize": 1048576,
            },
            "tags": {
                "count": 5,
                "maxDepth": 1,
            },
            "references": {
                "count": 10,
            },
            "branches": {
                "count": 3,
            },
        },
        "pathInfo": {
            "maxDepth": 8,
            "maxLength": 120,
        },
        "problems": [
            {
                "metric": "max_blob_size",
                "level": 2,
                "value": "1.0 MiB",
            },
        ],
    }


@pytest.fixture
def sample_caldera_envelope() -> dict[str, Any]:
    """Sample Caldera envelope format output."""
    return {
        "metadata": {
            "tool_name": "git-sizer",
            "tool_version": "1.5.0",
            "run_id": "550e8400-e29b-41d4-a716-446655440000",
            "repo_id": "660e8400-e29b-41d4-a716-446655440001",
            "branch": "main",
            "commit": "a" * 40,
            "timestamp": "2026-01-30T12:00:00Z",
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "git-sizer",
            "tool_version": "1.5.0",
            "health_grade": "B",
            "duration_ms": 150,
            "metrics": {
                "commit_count": 100,
                "commit_total_size": 50000,
                "max_commit_size": 2048,
                "max_history_depth": 100,
                "max_parent_count": 2,
                "tree_count": 250,
                "tree_total_size": 75000,
                "tree_total_entries": 1500,
                "max_tree_entries": 50,
                "blob_count": 180,
                "blob_total_size": 5242880,
                "max_blob_size": 1048576,
                "tag_count": 5,
                "max_tag_depth": 1,
                "reference_count": 10,
                "branch_count": 3,
                "max_path_depth": 8,
                "max_path_length": 120,
                "expanded_tree_count": 0,
                "expanded_blob_count": 0,
                "expanded_blob_size": 0,
            },
            "violations": [
                {
                    "metric": "max_blob_size",
                    "value": "1.0 MiB",
                    "raw_value": 1048576,
                    "level": 2,
                    "object_ref": None,
                },
            ],
            "lfs_candidates": [],
            "raw_output": {},
        },
    }


@pytest.fixture
def healthy_repo_path(temp_dir: Path) -> Path:
    """Create a minimal healthy test repo."""
    repo_path = temp_dir / "healthy-repo"
    repo_path.mkdir()

    # Initialize git repo
    import subprocess
    subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo_path,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=repo_path,
        capture_output=True,
    )

    # Create a simple file and commit
    (repo_path / "README.md").write_text("# Test Repo\n")
    subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        capture_output=True,
    )

    return repo_path
