"""Analysis output and ground truth loading utilities.

This module provides utilities for loading tool analysis results and
ground truth files from directories, with automatic envelope unwrapping.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .envelope import unwrap_envelope


def load_analysis_results(
    output_dir: Path,
    filename: str = "output.json",
    unwrap: bool = True,
) -> dict[str, Any]:
    """Load and optionally unwrap analysis results from output directory.

    Args:
        output_dir: Directory containing the output file
        filename: Name of the output file (default: "output.json")
        unwrap: Whether to unwrap envelope format (default: True)

    Returns:
        The loaded (and optionally unwrapped) analysis results.
        Returns empty dict if file doesn't exist.

    Example:
        >>> results = load_analysis_results(Path("outputs/run-123"))
        >>> files = results.get("files", [])
    """
    output_path = output_dir / filename
    if not output_path.exists():
        return {}

    try:
        payload = json.loads(output_path.read_text())
    except json.JSONDecodeError:
        return {}

    if unwrap:
        return unwrap_envelope(payload)
    return payload


def load_ground_truth(
    ground_truth_dir: Path,
    pattern: str = "*.json",
) -> dict[str, dict[str, Any]]:
    """Load all ground truth files from directory.

    Args:
        ground_truth_dir: Directory containing ground truth JSON files
        pattern: Glob pattern for finding files (default: "*.json")

    Returns:
        Dictionary mapping filename stem (without .json) to file contents.
        Files that fail to parse are skipped.

    Example:
        >>> gt_files = load_ground_truth(Path("evaluation/ground-truth"))
        >>> for repo_name, gt_data in gt_files.items():
        ...     expected_count = gt_data.get("expected_count", 0)
    """
    results: dict[str, dict[str, Any]] = {}

    if not ground_truth_dir.exists():
        return results

    for gt_file in sorted(ground_truth_dir.glob(pattern)):
        if gt_file.name.startswith("."):
            continue
        try:
            data = json.loads(gt_file.read_text())
            results[gt_file.stem] = data
        except json.JSONDecodeError:
            # Skip files that fail to parse
            continue

    return results


def load_all_outputs(
    output_dir: Path,
    unwrap: bool = True,
) -> dict[str, dict[str, Any]]:
    """Load all JSON output files from a directory.

    Useful for loading multi-repo analysis results where each repo
    has its own output file or subdirectory.

    Args:
        output_dir: Directory containing output files
        unwrap: Whether to unwrap envelope format (default: True)

    Returns:
        Dictionary mapping repo name to output data.
        - For files: uses 'id' field from envelope if present, else filename stem
        - For subdirs with output.json: uses subdirectory name

    Example:
        >>> outputs = load_all_outputs(Path("outputs"))
        >>> for repo_name, data in outputs.items():
        ...     print(f"{repo_name}: {len(data.get('files', []))} files")
    """
    results: dict[str, dict[str, Any]] = {}

    if not output_dir.exists() or not output_dir.is_dir():
        return results

    # Check for JSON files in directory
    json_files = list(output_dir.glob("*.json"))
    for json_file in sorted(json_files):
        if json_file.name.startswith("."):
            continue
        try:
            payload = json.loads(json_file.read_text())
            # Use 'id' field from envelope for ground truth matching
            repo_name = payload.get("id", json_file.stem)
            data = unwrap_envelope(payload) if unwrap else payload
            results[repo_name] = data
        except json.JSONDecodeError:
            continue

    # Check for subdirectories with output.json
    for subdir in sorted(output_dir.iterdir()):
        if not subdir.is_dir():
            continue
        output_file = subdir / "output.json"
        if output_file.exists():
            try:
                payload = json.loads(output_file.read_text())
                data = unwrap_envelope(payload) if unwrap else payload
                results[subdir.name] = data
            except json.JSONDecodeError:
                continue

    return results
