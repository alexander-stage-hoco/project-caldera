"""Accuracy checks for dotcover.

This module contains programmatic evaluation checks for accuracy.
Each check_* function receives the tool output and ground truth,
and returns a dict with check_id, status, and message.

For implementation examples, see:
- src/tools/scc/scripts/checks/per_file.py - Per-file metric validation
- src/tools/lizard/scripts/checks/accuracy.py - Function detection accuracy
- src/tools/semgrep/scripts/checks/accuracy.py - Smell detection precision/recall

Documentation:
- docs/TOOL_REQUIREMENTS.md - Check format requirements
- Your EVAL_STRATEGY.md - Defines which checks to implement
"""

from __future__ import annotations


def check_file_count_accuracy(output: dict, ground_truth: dict | None) -> dict:
    """Check if file count matches ground truth.

    This is a basic example check. You should implement checks specific
    to your tool's metrics and accuracy requirements.
    """
    if ground_truth is None:
        return {
            "check_id": "accuracy.file_count",
            "status": "pass",
            "message": "No ground truth available (skipped)",
        }

    data = output.get("data", {})
    actual_count = len(data.get("files", []))
    expected_count = ground_truth.get("expected_file_count", 0)

    if actual_count == expected_count:
        return {
            "check_id": "accuracy.file_count",
            "status": "pass",
            "message": f"File count matches: {actual_count}",
        }
    else:
        return {
            "check_id": "accuracy.file_count",
            "status": "fail",
            "message": f"File count mismatch: expected {expected_count}, got {actual_count}",
        }


# TODO: Add your tool-specific accuracy checks below.
#
# Example check patterns:
#
# def check_metric_precision(output: dict, ground_truth: dict | None) -> dict:
#     """Check precision of detected metrics against ground truth."""
#     # Precision = true_positives / (true_positives + false_positives)
#     ...
#
# def check_metric_recall(output: dict, ground_truth: dict | None) -> dict:
#     """Check recall of detected metrics against ground truth."""
#     # Recall = true_positives / (true_positives + false_negatives)
#     ...
#
# def check_threshold_compliance(output: dict, ground_truth: dict | None) -> dict:
#     """Check that metrics meet minimum thresholds defined in ground truth."""
#     ...
