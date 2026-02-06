"""Utility functions for git-fame LLM evaluation judges."""

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
        - total_authors: total unique author count across all repos
        - total_loc: total lines of code across all repos
        - aggregate_summary: aggregated metrics
    """
    repos: dict[str, Any] = {}
    all_authors: set[str] = set()
    total_loc = 0
    total_commits = 0

    if not output_dir.exists():
        return {
            "repos": {},
            "total_authors": 0,
            "total_loc": 0,
            "total_commits": 0,
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
            results = data.get("results", data)
            authors = results.get("authors", [])
            summary = results.get("summary", {})

            repos[repo_name] = {
                "data": data,
                "authors": authors,
                "summary": summary,
            }

            # Aggregate metrics
            for author in authors:
                all_authors.add(author.get("name", ""))
                total_commits += author.get("commit_count", 0)

            total_loc += summary.get("total_loc", 0)

        except json.JSONDecodeError:
            continue

    # Build aggregate summary
    aggregate_summary = {
        "repo_count": len(repos),
        "unique_authors": len(all_authors),
        "total_loc": total_loc,
        "total_commits": total_commits,
    }

    return {
        "repos": repos,
        "total_authors": len(all_authors),
        "total_loc": total_loc,
        "total_commits": total_commits,
        "aggregate_summary": aggregate_summary,
    }


def load_ground_truth(ground_truth_dir: Path) -> dict[str, Any]:
    """Load ground truth files for comparison.

    Args:
        ground_truth_dir: Directory containing ground truth JSON files

    Returns:
        Dictionary mapping repo name to ground truth data
    """
    ground_truth: dict[str, Any] = {}

    if not ground_truth_dir.exists():
        return ground_truth

    for gt_file in sorted(ground_truth_dir.glob("*.json")):
        if gt_file.name.startswith("."):
            continue
        try:
            data = json.loads(gt_file.read_text())
            repo_name = data.get("id", gt_file.stem)
            ground_truth[repo_name] = data
        except json.JSONDecodeError:
            continue

    return ground_truth


def compare_authors(
    actual: list[dict],
    expected: list[dict],
    tolerance: float = 0.05,
) -> dict[str, Any]:
    """Compare actual author metrics against expected ground truth.

    Args:
        actual: List of author dictionaries from analysis
        expected: List of expected author dictionaries from ground truth
        tolerance: Acceptable variance for numeric comparisons (default 5%)

    Returns:
        Comparison result with matches, mismatches, and accuracy metrics
    """
    actual_by_name = {a.get("name", ""): a for a in actual}
    expected_by_name = {e.get("name", ""): e for e in expected}

    matches = []
    mismatches = []
    missing = []
    extra = []

    # Check expected authors
    for name, exp in expected_by_name.items():
        if name in actual_by_name:
            act = actual_by_name[name]
            exp_pct = exp.get("ownership_pct", 0)
            act_pct = act.get("ownership_pct", 0)

            # Check if within tolerance
            if exp_pct > 0:
                diff_ratio = abs(exp_pct - act_pct) / exp_pct
                is_match = diff_ratio <= tolerance
            else:
                is_match = act_pct == 0

            if is_match:
                matches.append({
                    "name": name,
                    "expected_pct": exp_pct,
                    "actual_pct": act_pct,
                })
            else:
                mismatches.append({
                    "name": name,
                    "expected_pct": exp_pct,
                    "actual_pct": act_pct,
                    "difference": act_pct - exp_pct,
                })
        else:
            missing.append({
                "name": name,
                "expected_pct": exp.get("ownership_pct", 0),
            })

    # Check for extra authors not in expected
    for name in actual_by_name:
        if name not in expected_by_name:
            extra.append({
                "name": name,
                "actual_pct": actual_by_name[name].get("ownership_pct", 0),
            })

    total_expected = len(expected_by_name)
    accuracy = len(matches) / total_expected if total_expected > 0 else 1.0

    return {
        "matches": matches,
        "mismatches": mismatches,
        "missing": missing,
        "extra": extra,
        "accuracy": round(accuracy, 4),
        "total_expected": total_expected,
        "total_actual": len(actual_by_name),
    }


def validate_ownership_percentages(authors: list[dict]) -> dict[str, Any]:
    """Validate that ownership percentages sum to 100% and are non-negative.

    Args:
        authors: List of author dictionaries

    Returns:
        Validation result with any issues found
    """
    issues = []
    total_pct = 0.0

    for author in authors:
        pct = author.get("ownership_pct", 0)
        name = author.get("name", "unknown")

        if pct < 0:
            issues.append(f"Negative ownership for {name}: {pct}%")
        if pct > 100:
            issues.append(f"Ownership exceeds 100% for {name}: {pct}%")

        total_pct += pct

    # Check total sums to approximately 100%
    if abs(total_pct - 100.0) > 1.0:  # Allow 1% tolerance
        issues.append(f"Total ownership does not sum to 100%: {total_pct:.2f}%")

    return {
        "valid": len(issues) == 0,
        "total_pct": round(total_pct, 2),
        "issues": issues,
    }


def calculate_concentration_metrics(authors: list[dict]) -> dict[str, Any]:
    """Calculate various concentration metrics from author ownership.

    Args:
        authors: List of author dictionaries with ownership_pct

    Returns:
        Dictionary with HHI, Gini, bus factor, and top-N metrics
    """
    if not authors:
        return {
            "hhi": 0.0,
            "gini": 0.0,
            "bus_factor": 0,
            "top_1_pct": 0.0,
            "top_3_pct": 0.0,
            "top_5_pct": 0.0,
        }

    # Sort by ownership descending
    sorted_authors = sorted(
        authors,
        key=lambda a: a.get("ownership_pct", 0),
        reverse=True
    )

    ownership_pcts = [a.get("ownership_pct", 0) for a in sorted_authors]
    n = len(ownership_pcts)

    # HHI (Herfindahl-Hirschman Index)
    total = sum(ownership_pcts)
    if total > 0:
        hhi = sum((p / total) ** 2 for p in ownership_pcts)
    else:
        hhi = 0.0

    # Gini coefficient
    if n > 1 and total > 0:
        sorted_pcts = sorted(ownership_pcts)
        cumsum = 0.0
        weighted_sum = 0.0
        for i, p in enumerate(sorted_pcts, 1):
            cumsum += p
            weighted_sum += (2 * i - n - 1) * p
        gini = weighted_sum / (n * total)
    else:
        gini = 0.0

    # Bus factor
    cumulative = 0.0
    bus_factor = 0
    for i, pct in enumerate(ownership_pcts, 1):
        cumulative += pct
        if cumulative >= 50:
            bus_factor = i
            break
    if bus_factor == 0 and n > 0:
        bus_factor = n

    # Top-N percentages
    top_1 = ownership_pcts[0] if n >= 1 else 0.0
    top_3 = sum(ownership_pcts[:3]) if n >= 1 else 0.0
    top_5 = sum(ownership_pcts[:5]) if n >= 1 else 0.0

    return {
        "hhi": round(hhi, 4),
        "gini": round(gini, 4),
        "bus_factor": bus_factor,
        "top_1_pct": round(top_1, 2),
        "top_3_pct": round(top_3, 2),
        "top_5_pct": round(top_5, 2),
    }
