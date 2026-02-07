"""Performance checks for dotcover.

This module validates performance requirements:
- Execution time < 2 minutes for typical repository (from EVAL_STRATEGY.md)

Timing data is expected in metadata.timing.total_seconds of the output envelope.
"""

from __future__ import annotations

# Performance threshold from EVAL_STRATEGY.md
THRESHOLD_PASS_SECONDS = 120  # < 2 minutes = pass
THRESHOLD_WARN_SECONDS = 300  # 2-5 minutes = warn


def check_execution_time(output: dict, ground_truth: dict | None) -> dict:
    """Check if execution completed in reasonable time.

    Thresholds (from EVAL_STRATEGY.md):
    - Pass: < 2 minutes
    - Warn: 2-5 minutes
    - Fail: > 5 minutes

    If timing data is not available in the output, returns pass with a note.
    """
    metadata = output.get("metadata", {})
    timing = metadata.get("timing", {})
    total_seconds = timing.get("total_seconds")

    # Handle missing timing data
    if total_seconds is None:
        return {
            "check_id": "performance.execution_time",
            "status": "pass",
            "message": "No timing data available in output (timing not recorded)",
        }

    # Validate timing value
    try:
        total_seconds = float(total_seconds)
    except (TypeError, ValueError):
        return {
            "check_id": "performance.execution_time",
            "status": "warn",
            "message": f"Invalid timing value: {total_seconds}",
        }

    # Check against thresholds
    if total_seconds < THRESHOLD_PASS_SECONDS:
        return {
            "check_id": "performance.execution_time",
            "status": "pass",
            "message": f"Execution time {total_seconds:.1f}s < {THRESHOLD_PASS_SECONDS}s threshold",
        }
    elif total_seconds < THRESHOLD_WARN_SECONDS:
        return {
            "check_id": "performance.execution_time",
            "status": "warn",
            "message": f"Execution time {total_seconds:.1f}s between {THRESHOLD_PASS_SECONDS}-{THRESHOLD_WARN_SECONDS}s",
        }
    else:
        return {
            "check_id": "performance.execution_time",
            "status": "fail",
            "message": f"Execution time {total_seconds:.1f}s > {THRESHOLD_WARN_SECONDS}s threshold",
        }
