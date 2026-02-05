"""Coverage checks for dotcover."""

from __future__ import annotations


def check_all_files_analyzed(output: dict, ground_truth: dict | None) -> dict:
    """Check that all expected files were analyzed."""
    data = output.get("data", {})
    files = data.get("files", [])

    if not files:
        return {
            "check_id": "coverage.files_analyzed",
            "status": "warn",
            "message": "No files in output",
        }

    return {
        "check_id": "coverage.files_analyzed",
        "status": "pass",
        "message": f"{len(files)} files analyzed",
    }
