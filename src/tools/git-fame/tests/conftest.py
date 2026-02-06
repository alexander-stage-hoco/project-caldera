"""Pytest configuration and fixtures for git-fame tests."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))


# =============================================================================
# Sample Output Data Fixtures
# =============================================================================


@pytest.fixture
def valid_output_data() -> dict[str, Any]:
    """Valid git-fame analysis output with multiple authors.

    This represents a typical output from analyze.py with realistic
    author distributions and metrics.
    """
    return {
        "schema_version": "1.0.0",
        "generated_at": "2026-02-06T12:00:00Z",
        "repo_name": "test-repo",
        "repo_path": "/path/to/test-repo",
        "results": {
            "tool": "git-fame",
            "tool_version": "3.1.1",
            "run_id": "fame-20260206-120000-test-repo",
            "provenance": {
                "tool": "git-fame",
                "command": "git-fame --format json --branch HEAD",
            },
            "summary": {
                "author_count": 3,
                "total_loc": 1000,
                "hhi_index": 0.38,
                "bus_factor": 1,
                "top_author_pct": 50.0,
                "top_two_pct": 80.0,
            },
            "authors": [
                {
                    "name": "Alice Developer",
                    "surviving_loc": 500,
                    "insertions_total": 600,
                    "deletions_total": 100,
                    "commit_count": 20,
                    "files_touched": 10,
                    "ownership_pct": 50.0,
                },
                {
                    "name": "Bob Engineer",
                    "surviving_loc": 300,
                    "insertions_total": 350,
                    "deletions_total": 50,
                    "commit_count": 15,
                    "files_touched": 8,
                    "ownership_pct": 30.0,
                },
                {
                    "name": "Carol Coder",
                    "surviving_loc": 200,
                    "insertions_total": 220,
                    "deletions_total": 20,
                    "commit_count": 10,
                    "files_touched": 5,
                    "ownership_pct": 20.0,
                },
            ],
        },
    }


@pytest.fixture
def single_author_data() -> dict[str, Any]:
    """Output data for single-author repository.

    Represents maximum concentration with HHI=1.0 and bus_factor=1.
    """
    return {
        "schema_version": "1.0.0",
        "generated_at": "2026-02-06T12:00:00Z",
        "repo_name": "single-author",
        "repo_path": "/path/to/single-author",
        "results": {
            "tool": "git-fame",
            "tool_version": "3.1.1",
            "run_id": "fame-20260206-120000-single-author",
            "provenance": {
                "tool": "git-fame",
                "command": "git-fame --format json --branch HEAD",
            },
            "summary": {
                "author_count": 1,
                "total_loc": 350,
                "hhi_index": 1.0,
                "bus_factor": 1,
                "top_author_pct": 100.0,
                "top_two_pct": 100.0,
            },
            "authors": [
                {
                    "name": "Alice Developer",
                    "surviving_loc": 350,
                    "insertions_total": 400,
                    "deletions_total": 50,
                    "commit_count": 4,
                    "files_touched": 4,
                    "ownership_pct": 100.0,
                },
            ],
        },
    }


@pytest.fixture
def multi_author_data() -> dict[str, Any]:
    """Output data for multi-author repository with 50/30/20 split.

    Represents moderate concentration typical of small teams.
    """
    return {
        "schema_version": "1.0.0",
        "generated_at": "2026-02-06T12:00:00Z",
        "repo_name": "multi-author",
        "repo_path": "/path/to/multi-author",
        "results": {
            "tool": "git-fame",
            "tool_version": "3.1.1",
            "run_id": "fame-20260206-120000-multi-author",
            "provenance": {
                "tool": "git-fame",
                "command": "git-fame --format json --branch HEAD",
            },
            "summary": {
                "author_count": 3,
                "total_loc": 350,
                "hhi_index": 0.38,
                "bus_factor": 1,
                "top_author_pct": 50.0,
                "top_two_pct": 80.0,
            },
            "authors": [
                {
                    "name": "Alice Developer",
                    "surviving_loc": 175,
                    "insertions_total": 200,
                    "deletions_total": 25,
                    "commit_count": 2,
                    "files_touched": 2,
                    "ownership_pct": 50.0,
                },
                {
                    "name": "Bob Engineer",
                    "surviving_loc": 105,
                    "insertions_total": 120,
                    "deletions_total": 15,
                    "commit_count": 2,
                    "files_touched": 2,
                    "ownership_pct": 30.0,
                },
                {
                    "name": "Carol Coder",
                    "surviving_loc": 70,
                    "insertions_total": 80,
                    "deletions_total": 10,
                    "commit_count": 2,
                    "files_touched": 2,
                    "ownership_pct": 20.0,
                },
            ],
        },
    }


@pytest.fixture
def balanced_data() -> dict[str, Any]:
    """Output data for balanced repository with ~25% each.

    Represents low concentration with well-distributed ownership.
    """
    return {
        "schema_version": "1.0.0",
        "generated_at": "2026-02-06T12:00:00Z",
        "repo_name": "balanced",
        "repo_path": "/path/to/balanced",
        "results": {
            "tool": "git-fame",
            "tool_version": "3.1.1",
            "run_id": "fame-20260206-120000-balanced",
            "provenance": {
                "tool": "git-fame",
                "command": "git-fame --format json --branch HEAD",
            },
            "summary": {
                "author_count": 4,
                "total_loc": 350,
                "hhi_index": 0.25,
                "bus_factor": 2,
                "top_author_pct": 25.0,
                "top_two_pct": 50.0,
            },
            "authors": [
                {
                    "name": "Alice Developer",
                    "surviving_loc": 88,
                    "insertions_total": 95,
                    "deletions_total": 7,
                    "commit_count": 2,
                    "files_touched": 2,
                    "ownership_pct": 25.14,
                },
                {
                    "name": "Bob Engineer",
                    "surviving_loc": 88,
                    "insertions_total": 95,
                    "deletions_total": 7,
                    "commit_count": 2,
                    "files_touched": 2,
                    "ownership_pct": 25.14,
                },
                {
                    "name": "Carol Coder",
                    "surviving_loc": 88,
                    "insertions_total": 95,
                    "deletions_total": 7,
                    "commit_count": 2,
                    "files_touched": 2,
                    "ownership_pct": 25.14,
                },
                {
                    "name": "Dave Designer",
                    "surviving_loc": 86,
                    "insertions_total": 93,
                    "deletions_total": 7,
                    "commit_count": 2,
                    "files_touched": 2,
                    "ownership_pct": 24.57,
                },
            ],
        },
    }


@pytest.fixture
def bus_factor_1_data() -> dict[str, Any]:
    """Output data for repository with dominant author (90%).

    Represents high-risk bus factor scenario.
    """
    return {
        "schema_version": "1.0.0",
        "generated_at": "2026-02-06T12:00:00Z",
        "repo_name": "bus-factor-1",
        "repo_path": "/path/to/bus-factor-1",
        "results": {
            "tool": "git-fame",
            "tool_version": "3.1.1",
            "run_id": "fame-20260206-120000-bus-factor-1",
            "provenance": {
                "tool": "git-fame",
                "command": "git-fame --format json --branch HEAD",
            },
            "summary": {
                "author_count": 3,
                "total_loc": 350,
                "hhi_index": 0.815,
                "bus_factor": 1,
                "top_author_pct": 90.0,
                "top_two_pct": 95.0,
            },
            "authors": [
                {
                    "name": "Alice Developer",
                    "surviving_loc": 315,
                    "insertions_total": 350,
                    "deletions_total": 35,
                    "commit_count": 4,
                    "files_touched": 4,
                    "ownership_pct": 90.0,
                },
                {
                    "name": "Bob Engineer",
                    "surviving_loc": 18,
                    "insertions_total": 20,
                    "deletions_total": 2,
                    "commit_count": 1,
                    "files_touched": 1,
                    "ownership_pct": 5.14,
                },
                {
                    "name": "Carol Coder",
                    "surviving_loc": 17,
                    "insertions_total": 19,
                    "deletions_total": 2,
                    "commit_count": 1,
                    "files_touched": 1,
                    "ownership_pct": 4.86,
                },
            ],
        },
    }


# =============================================================================
# Directory and File Fixtures
# =============================================================================


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def output_dir_with_data(temp_dir: Path, valid_output_data: dict[str, Any]) -> Path:
    """Create output directory with valid analysis data.

    Returns:
        Path to the output directory containing analysis.json
    """
    output_dir = temp_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create run directory structure
    runs_dir = output_dir / "runs"
    runs_dir.mkdir()

    run_id = valid_output_data["results"]["run_id"]
    run_dir = runs_dir / run_id
    run_dir.mkdir()

    # Write analysis file
    analysis_file = run_dir / "analysis.json"
    analysis_file.write_text(json.dumps(valid_output_data, indent=2))

    # Create latest symlink
    latest_link = output_dir / "latest"
    latest_link.symlink_to(f"runs/{run_id}")

    return output_dir


@pytest.fixture
def output_dir_with_multiple_repos(
    temp_dir: Path,
    single_author_data: dict[str, Any],
    multi_author_data: dict[str, Any],
    balanced_data: dict[str, Any],
    bus_factor_1_data: dict[str, Any],
) -> Path:
    """Create output directory with multiple repository analyses.

    Returns:
        Path to the output directory containing combined_analysis.json
    """
    output_dir = temp_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create combined analysis file
    combined = {
        "single-author": single_author_data,
        "multi-author": multi_author_data,
        "balanced": balanced_data,
        "bus-factor-1": bus_factor_1_data,
    }
    combined_file = output_dir / "combined_analysis.json"
    combined_file.write_text(json.dumps(combined, indent=2))

    # Also create individual files
    for repo_name, data in combined.items():
        repo_file = output_dir / f"{repo_name}.json"
        repo_file.write_text(json.dumps(data, indent=2))

    return output_dir


@pytest.fixture
def ground_truth_file(temp_dir: Path) -> Path:
    """Create a ground truth JSON file for testing.

    Returns:
        Path to the ground truth file
    """
    ground_truth = {
        "schema_version": "1.0",
        "scenario": "synthetic",
        "description": "Ground truth for synthetic test repository",
        "repo_path": "eval-repos/synthetic",
        "expected": {
            "summary": {
                "author_count": 3,
                "file_count": {"min": 6, "max": 6},
                "total_loc": {"min": 300, "max": 400},
            },
            "concentration_metrics": {
                "bus_factor": 1,
                "hhi_index": {"min": 0.35, "max": 0.42},
                "top_author_pct": {"min": 48.0, "max": 53.0},
            },
            "authors": [
                {
                    "name": "Alice Developer",
                    "loc_pct": {"min": 48.0, "max": 53.0},
                    "file_count": 2,
                    "commit_count": {"min": 2, "max": 2},
                },
                {
                    "name": "Bob Engineer",
                    "loc_pct": {"min": 28.0, "max": 33.0},
                    "file_count": 2,
                    "commit_count": {"min": 2, "max": 2},
                },
                {
                    "name": "Carol Coder",
                    "loc_pct": {"min": 18.0, "max": 23.0},
                    "file_count": 2,
                    "commit_count": {"min": 2, "max": 2},
                },
            ],
        },
        "thresholds": {
            "max_analysis_time_ms": 5000,
        },
    }

    ground_truth_dir = temp_dir / "evaluation" / "ground-truth"
    ground_truth_dir.mkdir(parents=True, exist_ok=True)

    gt_file = ground_truth_dir / "synthetic.json"
    gt_file.write_text(json.dumps(ground_truth, indent=2))

    return gt_file


@pytest.fixture
def eval_repos_dir(temp_dir: Path) -> Path:
    """Create eval-repos directory structure.

    Returns:
        Path to the eval-repos directory
    """
    eval_repos = temp_dir / "eval-repos"
    eval_repos.mkdir(parents=True, exist_ok=True)

    # Create synthetic repo directory structure
    synthetic_dir = eval_repos / "synthetic"
    synthetic_dir.mkdir()

    # Create subdirectories for scenarios
    for scenario in ["single-author", "multi-author", "balanced", "bus-factor-1"]:
        scenario_dir = synthetic_dir / scenario
        scenario_dir.mkdir()

    # Create real repo directory
    real_dir = eval_repos / "real"
    real_dir.mkdir()

    return eval_repos


@pytest.fixture
def tool_root() -> Path:
    """Return the git-fame tool root directory."""
    return Path(__file__).parent.parent


# =============================================================================
# Helper Functions
# =============================================================================


def create_git_repo(repo_path: Path, authors: list[dict[str, Any]] | None = None) -> Path:
    """Create a minimal git repository with optional authors.

    Args:
        repo_path: Path where the repository should be created
        authors: List of author dicts with 'name', 'email', and optional 'files'

    Returns:
        Path to the created repository
    """
    import subprocess

    repo_path.mkdir(parents=True, exist_ok=True)

    # Initialize git repo
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

    if authors:
        for author in authors:
            # Set author for commits
            env = {
                "GIT_AUTHOR_NAME": author["name"],
                "GIT_AUTHOR_EMAIL": author["email"],
                "GIT_COMMITTER_NAME": author["name"],
                "GIT_COMMITTER_EMAIL": author["email"],
            }

            for file_info in author.get("files", []):
                file_path = repo_path / file_info["path"]
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(file_info.get("content", "# placeholder\n"))

                subprocess.run(
                    ["git", "add", str(file_info["path"])],
                    cwd=repo_path,
                    capture_output=True,
                    env={**subprocess.os.environ, **env},
                )
                subprocess.run(
                    ["git", "commit", "-m", f"Add {file_info['path']}"],
                    cwd=repo_path,
                    capture_output=True,
                    env={**subprocess.os.environ, **env},
                )
    else:
        # Create a simple default commit
        (repo_path / "README.md").write_text("# Test Repo\n")
        subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            capture_output=True,
        )

    return repo_path
