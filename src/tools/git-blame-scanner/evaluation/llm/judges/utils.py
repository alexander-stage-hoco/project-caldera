"""Utility functions for git-blame-scanner LLM evaluation judges."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_analysis_bundle(output_dir: Path) -> dict[str, Any]:
    """Load all analysis results from the output directory.

    Args:
        output_dir: Directory containing analysis output JSON files

    Returns:
        Dictionary with:
        - repos: dict mapping repo name to analysis data
        - total_files: total file count across all repos
        - total_lines: total lines of code across all repos
        - aggregate_summary: aggregated metrics
    """
    repos: dict[str, Any] = {}
    total_files = 0
    total_lines = 0
    knowledge_silo_count = 0

    if not output_dir.exists():
        return {
            "repos": {},
            "total_files": 0,
            "total_lines": 0,
            "knowledge_silo_count": 0,
            "aggregate_summary": {},
            "error": f"Output directory not found: {output_dir}",
        }

    # Find all JSON files
    json_files = list(output_dir.glob("*.json"))
    if not json_files:
        json_files = list(output_dir.rglob("output.json"))

    for json_file in sorted(json_files):
        if json_file.name.startswith("."):
            continue
        try:
            data = json.loads(json_file.read_text())
            repo_name = data.get("id", json_file.stem)

            # Extract results from envelope format
            results = data.get("data", data)
            files = results.get("files", [])
            authors = results.get("authors", [])
            summary = results.get("summary", {})

            repos[repo_name] = {
                "data": data,
                "files": files,
                "authors": authors,
                "summary": summary,
            }

            # Aggregate metrics
            total_files += len(files)
            total_lines += summary.get("total_lines_analyzed", 0)
            knowledge_silo_count += summary.get("knowledge_silo_count", 0)

        except json.JSONDecodeError:
            continue

    # Build aggregate summary
    aggregate_summary = {
        "repo_count": len(repos),
        "total_files": total_files,
        "total_lines": total_lines,
        "knowledge_silo_count": knowledge_silo_count,
    }

    return {
        "repos": repos,
        "total_files": total_files,
        "total_lines": total_lines,
        "knowledge_silo_count": knowledge_silo_count,
        "aggregate_summary": aggregate_summary,
    }


def validate_ownership_percentages(files: list[dict]) -> dict[str, Any]:
    """Validate that file ownership percentages are valid.

    Args:
        files: List of file dictionaries

    Returns:
        Validation result with any issues found
    """
    issues = []

    for file_info in files:
        path = file_info.get("path", "unknown")
        top_author_pct = file_info.get("top_author_pct", 0)

        if top_author_pct < 0:
            issues.append(f"Negative ownership for {path}: {top_author_pct}%")
        if top_author_pct > 100:
            issues.append(f"Ownership exceeds 100% for {path}: {top_author_pct}%")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
    }


def validate_churn_metrics(files: list[dict]) -> dict[str, Any]:
    """Validate that churn metrics are consistent.

    Churn_30d should be <= churn_90d since 90-day window includes 30-day.

    Args:
        files: List of file dictionaries

    Returns:
        Validation result with any issues found
    """
    issues = []

    for file_info in files:
        path = file_info.get("path", "unknown")
        churn_30d = file_info.get("churn_30d", 0)
        churn_90d = file_info.get("churn_90d", 0)

        if churn_30d < 0:
            issues.append(f"Negative churn_30d for {path}: {churn_30d}")
        if churn_90d < 0:
            issues.append(f"Negative churn_90d for {path}: {churn_90d}")
        if churn_30d > churn_90d:
            issues.append(
                f"Churn_30d > churn_90d for {path}: {churn_30d} > {churn_90d}"
            )

    return {
        "valid": len(issues) == 0,
        "issues": issues,
    }


def compare_files(
    actual: list[dict],
    expected: list[dict],
    tolerance: float = 0.05,
) -> dict[str, Any]:
    """Compare actual file metrics against expected ground truth.

    Args:
        actual: List of file dictionaries from analysis
        expected: List of expected file dictionaries from ground truth
        tolerance: Acceptable variance for numeric comparisons (default 5%)

    Returns:
        Comparison result with matches, mismatches, and accuracy metrics
    """
    actual_by_path = {f.get("path", ""): f for f in actual}
    expected_by_path = {f.get("path", ""): f for f in expected}

    matches = []
    mismatches = []
    missing = []
    extra = []

    # Check expected files
    for path, exp in expected_by_path.items():
        if path in actual_by_path:
            act = actual_by_path[path]
            issues = []

            # Compare unique_authors
            exp_authors = exp.get("unique_authors", 0)
            act_authors = act.get("unique_authors", 0)
            if exp_authors != act_authors:
                issues.append(
                    f"unique_authors: expected {exp_authors}, got {act_authors}"
                )

            # Compare top_author_pct with tolerance
            exp_pct = exp.get("top_author_pct", 0)
            act_pct = act.get("top_author_pct", 0)
            if exp_pct > 0:
                diff_ratio = abs(exp_pct - act_pct) / exp_pct
                if diff_ratio > tolerance:
                    issues.append(
                        f"top_author_pct: expected {exp_pct}, got {act_pct}"
                    )

            if not issues:
                matches.append({"path": path})
            else:
                mismatches.append({"path": path, "issues": issues})
        else:
            missing.append({"path": path})

    # Check for extra files not in expected
    for path in actual_by_path:
        if path not in expected_by_path:
            extra.append({"path": path})

    total_expected = len(expected_by_path)
    accuracy = len(matches) / total_expected if total_expected > 0 else 1.0

    return {
        "matches": matches,
        "mismatches": mismatches,
        "missing": missing,
        "extra": extra,
        "accuracy": round(accuracy, 4),
        "total_expected": total_expected,
        "total_actual": len(actual_by_path),
    }


def calculate_knowledge_risk_metrics(files: list[dict]) -> dict[str, Any]:
    """Calculate knowledge risk metrics from file data.

    Args:
        files: List of file dictionaries

    Returns:
        Dictionary with risk metrics
    """
    if not files:
        return {
            "single_author_count": 0,
            "high_concentration_count": 0,
            "knowledge_silo_count": 0,
            "stale_file_count": 0,
            "avg_unique_authors": 0.0,
            "avg_top_author_pct": 0.0,
        }

    single_author_count = 0
    high_concentration_count = 0
    knowledge_silo_count = 0
    stale_file_count = 0
    total_unique_authors = 0
    total_top_author_pct = 0.0

    for file_info in files:
        unique_authors = file_info.get("unique_authors", 0)
        top_author_pct = file_info.get("top_author_pct", 0)
        total_lines = file_info.get("total_lines", 0)
        churn_90d = file_info.get("churn_90d", 0)

        total_unique_authors += unique_authors
        total_top_author_pct += top_author_pct

        if unique_authors == 1:
            single_author_count += 1
            if total_lines > 100:
                knowledge_silo_count += 1

        if top_author_pct >= 80:
            high_concentration_count += 1

        if churn_90d == 0:
            stale_file_count += 1

    n = len(files)
    return {
        "single_author_count": single_author_count,
        "high_concentration_count": high_concentration_count,
        "knowledge_silo_count": knowledge_silo_count,
        "stale_file_count": stale_file_count,
        "avg_unique_authors": round(total_unique_authors / n, 2),
        "avg_top_author_pct": round(total_top_author_pct / n, 2),
    }
