"""Accuracy checks for git-blame-scanner.

This module contains programmatic evaluation checks for ownership
and authorship accuracy.
"""

from __future__ import annotations

from typing import Any


def check_ownership_bounds(output: dict, ground_truth: dict | None) -> list[dict]:
    """Check that all ownership percentages are within valid bounds (0-100%)."""
    data = output.get("data", {})
    files = data.get("files", [])

    results = []
    violations = []

    for f in files:
        pct = f.get("top_author_pct", 0)
        if pct < 0 or pct > 100:
            violations.append(f"{f.get('path')}: {pct}%")

    if not violations:
        results.append({
            "check_id": "accuracy.ownership_bounds",
            "status": "pass",
            "message": f"All {len(files)} files have valid ownership percentages (0-100%)",
        })
    else:
        results.append({
            "check_id": "accuracy.ownership_bounds",
            "status": "fail",
            "message": f"Found {len(violations)} files with invalid ownership: {violations[:5]}",
        })

    return results


def check_unique_authors_positive(output: dict, ground_truth: dict | None) -> list[dict]:
    """Check that unique_authors >= 1 for all files."""
    data = output.get("data", {})
    files = data.get("files", [])

    violations = []
    for f in files:
        authors = f.get("unique_authors", 0)
        if authors < 1:
            violations.append(f"{f.get('path')}: {authors}")

    if not violations:
        return [{
            "check_id": "accuracy.unique_authors_positive",
            "status": "pass",
            "message": f"All {len(files)} files have unique_authors >= 1",
        }]
    else:
        return [{
            "check_id": "accuracy.unique_authors_positive",
            "status": "fail",
            "message": f"Found {len(violations)} files with invalid unique_authors: {violations[:5]}",
        }]


def check_churn_monotonicity(output: dict, ground_truth: dict | None) -> list[dict]:
    """Check that churn_30d <= churn_90d for all files."""
    data = output.get("data", {})
    files = data.get("files", [])

    violations = []
    for f in files:
        churn_30d = f.get("churn_30d", 0)
        churn_90d = f.get("churn_90d", 0)
        if churn_30d > churn_90d:
            violations.append(f"{f.get('path')}: 30d={churn_30d} > 90d={churn_90d}")

    if not violations:
        return [{
            "check_id": "accuracy.churn_monotonicity",
            "status": "pass",
            "message": f"All {len(files)} files satisfy churn_30d <= churn_90d",
        }]
    else:
        return [{
            "check_id": "accuracy.churn_monotonicity",
            "status": "fail",
            "message": f"Found {len(violations)} files violating churn invariant: {violations[:5]}",
        }]


def check_exclusive_files_bound(output: dict, ground_truth: dict | None) -> list[dict]:
    """Check that exclusive_files <= total_files for all authors."""
    data = output.get("data", {})
    authors = data.get("authors", [])

    violations = []
    for a in authors:
        exclusive = a.get("exclusive_files", 0)
        total = a.get("total_files", 0)
        if exclusive > total:
            violations.append(f"{a.get('author_email')}: exclusive={exclusive} > total={total}")

    if not violations:
        return [{
            "check_id": "accuracy.exclusive_files_bound",
            "status": "pass",
            "message": f"All {len(authors)} authors satisfy exclusive_files <= total_files",
        }]
    else:
        return [{
            "check_id": "accuracy.exclusive_files_bound",
            "status": "fail",
            "message": f"Found {len(violations)} authors violating bound: {violations[:5]}",
        }]


def check_single_author_consistency(output: dict, ground_truth: dict | None) -> list[dict]:
    """Check that single-author files match between files and summary."""
    data = output.get("data", {})
    files = data.get("files", [])
    summary = data.get("summary", {})

    # Count single-author files from file data
    actual_single = sum(1 for f in files if f.get("unique_authors", 0) == 1)
    reported_single = summary.get("single_author_files", 0)

    if actual_single == reported_single:
        return [{
            "check_id": "accuracy.single_author_consistency",
            "status": "pass",
            "message": f"Single-author file count matches: {actual_single}",
        }]
    else:
        return [{
            "check_id": "accuracy.single_author_consistency",
            "status": "fail",
            "message": f"Single-author mismatch: counted {actual_single}, reported {reported_single}",
        }]


def check_high_concentration_consistency(output: dict, ground_truth: dict | None) -> list[dict]:
    """Check that high-concentration files match between files and summary."""
    data = output.get("data", {})
    files = data.get("files", [])
    summary = data.get("summary", {})

    # Count high-concentration files from file data (>= 80%)
    actual_high = sum(1 for f in files if f.get("top_author_pct", 0) >= 80)
    reported_high = summary.get("high_concentration_files", 0)

    if actual_high == reported_high:
        return [{
            "check_id": "accuracy.high_concentration_consistency",
            "status": "pass",
            "message": f"High-concentration file count matches: {actual_high}",
        }]
    else:
        return [{
            "check_id": "accuracy.high_concentration_consistency",
            "status": "fail",
            "message": f"High-concentration mismatch: counted {actual_high}, reported {reported_high}",
        }]
