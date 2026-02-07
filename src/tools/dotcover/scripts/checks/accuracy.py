"""Accuracy checks for dotcover.

This module contains programmatic evaluation checks for accuracy.
Each check_* function receives the tool output and ground truth,
and returns a dict with check_id, status, and message.
"""

from __future__ import annotations


def check_overall_coverage(output: dict, ground_truth: dict | None) -> dict:
    """Check overall coverage is within expected range."""
    if ground_truth is None:
        return {
            "check_id": "accuracy.overall_coverage",
            "status": "pass",
            "message": "No ground truth (skipped)",
        }

    data = output.get("data", {})
    summary = data.get("summary", {})
    actual_pct = summary.get("statement_coverage_pct", 0)

    expected = ground_truth.get("expected_coverage", {})
    min_pct = expected.get("overall_min", 0)
    max_pct = expected.get("overall_max", 100)

    if min_pct <= actual_pct <= max_pct:
        return {
            "check_id": "accuracy.overall_coverage",
            "status": "pass",
            "message": f"Coverage {actual_pct:.1f}% within range [{min_pct}-{max_pct}]",
        }
    else:
        return {
            "check_id": "accuracy.overall_coverage",
            "status": "fail",
            "message": f"Coverage {actual_pct:.1f}% outside range [{min_pct}-{max_pct}]",
        }


def check_assembly_detected(output: dict, ground_truth: dict | None) -> dict:
    """Check expected assemblies are present."""
    if ground_truth is None:
        return {
            "check_id": "accuracy.assembly_detected",
            "status": "pass",
            "message": "No ground truth (skipped)",
        }

    data = output.get("data", {})
    assemblies = {a["name"] for a in data.get("assemblies", [])}
    expected = {a["name"] for a in ground_truth.get("expected_assemblies", [])}

    if expected <= assemblies:
        return {
            "check_id": "accuracy.assembly_detected",
            "status": "pass",
            "message": f"All expected assemblies found: {expected}",
        }
    else:
        missing = expected - assemblies
        return {
            "check_id": "accuracy.assembly_detected",
            "status": "fail",
            "message": f"Missing assemblies: {missing}",
        }
