"""Coverage checks for dotcover."""

from __future__ import annotations


def check_all_files_analyzed(output: dict, ground_truth: dict | None) -> dict:
    """Check that types were analyzed (Coverlet reports by type, not file)."""
    data = output.get("data", {})
    types = data.get("types", [])

    if not types:
        return {
            "check_id": "coverage.files_analyzed",
            "status": "warn",
            "message": "No types in output",
        }

    return {
        "check_id": "coverage.files_analyzed",
        "status": "pass",
        "message": f"{len(types)} types analyzed",
    }
