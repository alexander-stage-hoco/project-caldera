"""Performance checks for git-blame-scanner.

This module contains programmatic evaluation checks for output
performance and efficiency metrics.
"""

from __future__ import annotations


def check_reasonable_file_count(output: dict, ground_truth: dict | None) -> list[dict]:
    """Check that file count is reasonable (not empty, not excessive)."""
    data = output.get("data", {})
    files = data.get("files", [])
    summary = data.get("summary", {})

    total_analyzed = summary.get("total_files_analyzed", len(files))

    if total_analyzed == 0:
        return [{
            "check_id": "performance.reasonable_file_count",
            "status": "fail",
            "message": "No files analyzed",
        }]
    elif total_analyzed > 100000:
        return [{
            "check_id": "performance.reasonable_file_count",
            "status": "warn",
            "message": f"Very large file count: {total_analyzed}",
        }]
    else:
        return [{
            "check_id": "performance.reasonable_file_count",
            "status": "pass",
            "message": f"Reasonable file count: {total_analyzed}",
        }]


def check_author_count_reasonable(output: dict, ground_truth: dict | None) -> list[dict]:
    """Check that author count is reasonable relative to file count."""
    data = output.get("data", {})
    files = data.get("files", [])
    authors = data.get("authors", [])

    if not files:
        return [{
            "check_id": "performance.author_count_reasonable",
            "status": "pass",
            "message": "No files to check (skipped)",
        }]

    # Author count should not exceed file count (each file has at least one author)
    # In practice, there are usually fewer authors than files
    ratio = len(authors) / len(files) if files else 0

    if len(authors) == 0:
        return [{
            "check_id": "performance.author_count_reasonable",
            "status": "fail",
            "message": "No authors found",
        }]
    elif ratio > 1:
        # More authors than files is possible but unusual
        return [{
            "check_id": "performance.author_count_reasonable",
            "status": "pass",
            "message": f"Author-to-file ratio: {ratio:.2f} (many contributors per file)",
        }]
    else:
        return [{
            "check_id": "performance.author_count_reasonable",
            "status": "pass",
            "message": f"Author-to-file ratio: {ratio:.2f}",
        }]


def check_metadata_complete(output: dict, ground_truth: dict | None) -> list[dict]:
    """Check that metadata section is complete."""
    metadata = output.get("metadata", {})

    required_fields = [
        "tool_name", "tool_version", "run_id", "repo_id",
        "branch", "commit", "timestamp", "schema_version",
    ]

    missing = [f for f in required_fields if f not in metadata]

    if not missing:
        return [{
            "check_id": "performance.metadata_complete",
            "status": "pass",
            "message": f"Metadata contains all {len(required_fields)} required fields",
        }]
    else:
        return [{
            "check_id": "performance.metadata_complete",
            "status": "fail",
            "message": f"Metadata missing fields: {missing}",
        }]


def check_commit_sha_valid(output: dict, ground_truth: dict | None) -> list[dict]:
    """Check that commit SHA is valid format."""
    metadata = output.get("metadata", {})
    commit = metadata.get("commit", "")

    if len(commit) == 40 and all(c in "0123456789abcdef" for c in commit.lower()):
        return [{
            "check_id": "performance.commit_sha_valid",
            "status": "pass",
            "message": f"Valid commit SHA: {commit[:12]}...",
        }]
    else:
        return [{
            "check_id": "performance.commit_sha_valid",
            "status": "warn",
            "message": f"Invalid commit SHA format: {commit[:20]}...",
        }]


def check_paths_normalized(output: dict, ground_truth: dict | None) -> list[dict]:
    """Check that all file paths are properly normalized."""
    data = output.get("data", {})
    files = data.get("files", [])

    violations = []
    for f in files:
        path = f.get("path", "")
        if path.startswith("/"):
            violations.append(f"Absolute path: {path}")
        elif path.startswith("./"):
            violations.append(f"./ prefix: {path}")
        elif ".." in path.split("/"):
            violations.append(f".. segment: {path}")
        elif "\\" in path:
            violations.append(f"Backslash: {path}")

    if not violations:
        return [{
            "check_id": "performance.paths_normalized",
            "status": "pass",
            "message": f"All {len(files)} file paths are properly normalized",
        }]
    else:
        return [{
            "check_id": "performance.paths_normalized",
            "status": "fail",
            "message": f"Found {len(violations)} path normalization issues: {violations[:3]}",
        }]
