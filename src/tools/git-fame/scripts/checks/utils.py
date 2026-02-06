"""Utility functions for git-fame evaluation checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_analysis_bundle(output_dir: Path, repo_name: str = "synthetic") -> dict[str, Any]:
    """Load the analysis bundle for a repository.

    The bundle includes both the analysis output and any raw git-fame output.

    Args:
        output_dir: Path to the output directory
        repo_name: Name of the repository (default: synthetic)

    Returns:
        Dictionary containing analysis data, or empty dict if not found
    """
    # Try multiple locations for the analysis file
    possible_paths = [
        output_dir / "latest" / "analysis.json",
        output_dir / "runs" / "latest" / "analysis.json",
        output_dir / f"{repo_name}.json",
        output_dir / "analysis.json",
    ]

    for path in possible_paths:
        if path.exists():
            try:
                with open(path) as f:
                    return json.load(f)
            except json.JSONDecodeError:
                continue

    # Try to find most recent run directory
    runs_dir = output_dir / "runs"
    if runs_dir.exists():
        run_dirs = sorted(runs_dir.iterdir(), reverse=True)
        for run_dir in run_dirs:
            analysis_file = run_dir / "analysis.json"
            if analysis_file.exists():
                try:
                    with open(analysis_file) as f:
                        return json.load(f)
                except json.JSONDecodeError:
                    continue

    return {}


def load_ground_truth(ground_truth_file: Path) -> dict[str, Any]:
    """Load ground truth data from JSON file.

    Args:
        ground_truth_file: Path to the ground truth JSON file

    Returns:
        Dictionary mapping repo names to their expected values,
        or empty dict if not found
    """
    if not ground_truth_file.exists():
        return {}

    try:
        with open(ground_truth_file) as f:
            data = json.load(f)
            # Handle nested structure with "repos" key
            if "repos" in data:
                return data["repos"]
            return data
    except json.JSONDecodeError:
        return {}


def find_repo_analyses(output_dir: Path) -> dict[str, dict[str, Any]]:
    """Find all repository analyses in the output directory.

    Args:
        output_dir: Path to the output directory

    Returns:
        Dictionary mapping repo names to their analysis data
    """
    analyses = {}

    # Check for combined analysis
    combined_file = output_dir / "combined_analysis.json"
    if combined_file.exists():
        try:
            with open(combined_file) as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass

    # Check for individual analysis files
    for json_file in output_dir.glob("*.json"):
        if json_file.name in ("combined_analysis.json", "metadata.json"):
            continue
        try:
            with open(json_file) as f:
                data = json.load(f)
                repo_name = data.get("repo_name", json_file.stem)
                analyses[repo_name] = data
        except json.JSONDecodeError:
            continue

    # Check runs directory
    runs_dir = output_dir / "runs"
    if runs_dir.exists():
        for run_dir in runs_dir.iterdir():
            if not run_dir.is_dir():
                continue
            analysis_file = run_dir / "analysis.json"
            if analysis_file.exists():
                try:
                    with open(analysis_file) as f:
                        data = json.load(f)
                        repo_name = data.get("repo_name", run_dir.name)
                        if repo_name not in analyses:
                            analyses[repo_name] = data
                except json.JSONDecodeError:
                    continue

    return analyses


def check_result(
    check: str,
    passed: bool,
    message: str,
) -> dict[str, Any]:
    """Create a standardized check result dictionary.

    Args:
        check: The check identifier (e.g., "OQ-1")
        passed: Whether the check passed
        message: Description of the result

    Returns:
        Dictionary with check, passed, and message keys
    """
    return {
        "check": check,
        "passed": passed,
        "message": message,
    }
