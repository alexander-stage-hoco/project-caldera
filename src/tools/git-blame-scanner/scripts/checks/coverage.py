"""Coverage checks for git-blame-scanner.

This module contains programmatic evaluation checks for output coverage
and completeness.
"""

from __future__ import annotations


def check_has_files(output: dict, ground_truth: dict | None) -> list[dict]:
    """Check that output contains at least one file."""
    data = output.get("data", {})
    files = data.get("files", [])

    if files:
        return [{
            "check_id": "coverage.has_files",
            "status": "pass",
            "message": f"Output contains {len(files)} files",
        }]
    else:
        return [{
            "check_id": "coverage.has_files",
            "status": "fail",
            "message": "Output contains no files",
        }]


def check_has_authors(output: dict, ground_truth: dict | None) -> list[dict]:
    """Check that output contains at least one author."""
    data = output.get("data", {})
    authors = data.get("authors", [])

    if authors:
        return [{
            "check_id": "coverage.has_authors",
            "status": "pass",
            "message": f"Output contains {len(authors)} authors",
        }]
    else:
        return [{
            "check_id": "coverage.has_authors",
            "status": "fail",
            "message": "Output contains no authors",
        }]


def check_has_summary(output: dict, ground_truth: dict | None) -> list[dict]:
    """Check that output contains a summary section."""
    data = output.get("data", {})
    summary = data.get("summary", {})

    required_fields = [
        "total_files_analyzed", "total_authors", "single_author_files",
        "single_author_pct", "high_concentration_files", "high_concentration_pct",
    ]

    missing = [f for f in required_fields if f not in summary]

    if not missing:
        return [{
            "check_id": "coverage.has_summary",
            "status": "pass",
            "message": f"Summary contains all {len(required_fields)} required fields",
        }]
    else:
        return [{
            "check_id": "coverage.has_summary",
            "status": "fail",
            "message": f"Summary missing fields: {missing}",
        }]


def check_file_fields_complete(output: dict, ground_truth: dict | None) -> list[dict]:
    """Check that all files have required fields."""
    data = output.get("data", {})
    files = data.get("files", [])

    required_fields = [
        "path", "total_lines", "unique_authors", "top_author",
        "top_author_pct", "last_modified", "churn_30d", "churn_90d",
    ]

    incomplete = []
    for f in files:
        missing = [field for field in required_fields if field not in f]
        if missing:
            incomplete.append(f"{f.get('path', 'unknown')}: missing {missing}")

    if not incomplete:
        return [{
            "check_id": "coverage.file_fields_complete",
            "status": "pass",
            "message": f"All {len(files)} files have complete fields",
        }]
    else:
        return [{
            "check_id": "coverage.file_fields_complete",
            "status": "fail",
            "message": f"Found {len(incomplete)} files with missing fields: {incomplete[:3]}",
        }]


def check_author_fields_complete(output: dict, ground_truth: dict | None) -> list[dict]:
    """Check that all authors have required fields."""
    data = output.get("data", {})
    authors = data.get("authors", [])

    required_fields = [
        "author_email", "total_files", "total_lines",
        "exclusive_files", "avg_ownership_pct",
    ]

    incomplete = []
    for a in authors:
        missing = [field for field in required_fields if field not in a]
        if missing:
            incomplete.append(f"{a.get('author_email', 'unknown')}: missing {missing}")

    if not incomplete:
        return [{
            "check_id": "coverage.author_fields_complete",
            "status": "pass",
            "message": f"All {len(authors)} authors have complete fields",
        }]
    else:
        return [{
            "check_id": "coverage.author_fields_complete",
            "status": "fail",
            "message": f"Found {len(incomplete)} authors with missing fields: {incomplete[:3]}",
        }]


def check_knowledge_silos_identified(output: dict, ground_truth: dict | None) -> list[dict]:
    """Check that knowledge silos are identified when present."""
    data = output.get("data", {})
    files = data.get("files", [])
    silos = data.get("knowledge_silos", [])
    summary = data.get("summary", {})

    # Count files that should be knowledge silos (single author, > 100 lines)
    expected_silos = [
        f.get("path") for f in files
        if f.get("unique_authors", 0) == 1 and f.get("total_lines", 0) > 100
    ]

    if not expected_silos:
        return [{
            "check_id": "coverage.knowledge_silos_identified",
            "status": "pass",
            "message": "No knowledge silos expected (no single-author files > 100 lines)",
        }]

    # Check that silos are properly reported
    silo_count = summary.get("knowledge_silo_count", 0)
    if silo_count == len(expected_silos):
        return [{
            "check_id": "coverage.knowledge_silos_identified",
            "status": "pass",
            "message": f"Identified {silo_count} knowledge silos correctly",
        }]
    else:
        return [{
            "check_id": "coverage.knowledge_silos_identified",
            "status": "warn",
            "message": f"Knowledge silo count: expected {len(expected_silos)}, got {silo_count}",
        }]
