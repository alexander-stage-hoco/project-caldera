"""Performance checks for dotcover."""

from __future__ import annotations


def check_execution_time(output: dict, ground_truth: dict | None) -> dict:
    """Check if execution completed in reasonable time."""
    # TODO: Implement timing measurement
    return {
        "check_id": "performance.execution_time",
        "status": "pass",
        "message": "Execution time check not implemented",
    }
