from __future__ import annotations
"""
Programmatic evaluation checks for Roslyn Analyzers PoC.

This module provides utilities and base classes for implementing
the 28 programmatic checks (AC-1 to AC-10, CV-1 to CV-8,
EC-1 to EC-8, PF-1 to PF-4).
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CheckResult:
    """Result of a single programmatic check."""
    check_id: str
    name: str
    category: str
    passed: bool
    score: float
    threshold: float
    actual_value: float
    message: str
    evidence: dict = field(default_factory=dict)


@dataclass
class EvaluationReport:
    """Complete evaluation report with all checks."""
    evaluation_id: str
    timestamp: str
    analysis_file: str
    summary: dict
    category_scores: dict
    checks: list[CheckResult]
    decision: str
    decision_reason: str


def compute_recall(detected: int, expected: int) -> float:
    """Compute recall (detected / expected)."""
    if expected == 0:
        return 1.0
    return detected / expected


def compute_precision(true_positives: int, total_reported: int) -> float:
    """Compute precision (true positives / total reported)."""
    if total_reported == 0:
        return 1.0
    return true_positives / total_reported


def compute_f1(precision: float, recall: float) -> float:
    """Compute F1 score."""
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def match_violations(
    detected: list[dict],
    expected: list[dict],
    file_key: str,
    tolerance_lines: int = 5
) -> tuple[int, int, int]:
    """
    Match detected violations against expected violations.

    Returns:
        Tuple of (true_positives, false_positives, false_negatives)
    """
    # Group expected by rule
    expected_by_rule: dict[str, list] = {}
    for exp in expected:
        rule = exp.get("rule_id", "")
        if rule not in expected_by_rule:
            expected_by_rule[rule] = []
        expected_by_rule[rule].append(exp)

    # Group detected by rule
    detected_by_rule: dict[str, list] = {}
    for det in detected:
        rule = det.get("rule_id", "")
        if rule not in detected_by_rule:
            detected_by_rule[rule] = []
        detected_by_rule[rule].append(det)

    true_positives = 0
    matched_expected = set()
    matched_detected = set()

    # Match by rule and approximate line number
    for rule, expected_list in expected_by_rule.items():
        detected_list = detected_by_rule.get(rule, [])

        for i, exp in enumerate(expected_list):
            exp_lines = exp.get("lines", [])
            for j, det in enumerate(detected_list):
                det_line = det.get("line_start", 0)

                # Check if any expected line is within tolerance
                for exp_line in exp_lines:
                    if abs(det_line - exp_line) <= tolerance_lines:
                        if (rule, i) not in matched_expected and (rule, j) not in matched_detected:
                            true_positives += 1
                            matched_expected.add((rule, i))
                            matched_detected.add((rule, j))
                            break

    # Calculate false positives and negatives
    total_expected = sum(exp.get("count", len(exp.get("lines", []))) for exp in expected)
    total_detected = len(detected)

    false_positives = total_detected - true_positives
    false_negatives = total_expected - true_positives

    return true_positives, max(0, false_positives), max(0, false_negatives)


def load_analysis_results(analysis_path: str) -> dict:
    """Load analysis results from JSON file."""
    import json
    from pathlib import Path

    path = Path(analysis_path)
    if not path.exists():
        raise FileNotFoundError(f"Analysis file not found: {analysis_path}")

    with open(path) as f:
        data = json.load(f)

    if isinstance(data, dict) and isinstance(data.get("results"), dict):
        results = dict(data["results"])
        metadata = dict(results.get("metadata") or {})
        metadata.setdefault("tool", results.get("tool"))
        metadata.setdefault("tool_version", results.get("tool_version"))
        metadata.setdefault("analysis_duration_ms", results.get("analysis_duration_ms", 0))
        metadata.setdefault("timestamp", data.get("generated_at"))
        metadata.setdefault("repo_name", data.get("repo_name"))
        metadata.setdefault("repo_path", data.get("repo_path"))
        results["metadata"] = metadata
        results["_root"] = data
        return results

    if isinstance(data, dict) and isinstance(data.get("data"), dict):
        results = dict(data["data"])
        metadata = dict(data.get("metadata") or {})
        metadata.setdefault("tool", results.get("tool"))
        metadata.setdefault("tool_version", results.get("tool_version"))
        metadata.setdefault("analysis_duration_ms", results.get("analysis_duration_ms", 0))
        metadata.setdefault("timestamp", metadata.get("timestamp") or data.get("generated_at"))
        metadata.setdefault("repo_name", metadata.get("repo_id"))
        metadata.setdefault("repo_path", metadata.get("repo_path"))
        results["metadata"] = metadata
        results["_root"] = data
        return results

    return data


def load_ground_truth(ground_truth_path: str) -> dict:
    """Load ground truth from JSON file."""
    import json
    from pathlib import Path

    path = Path(ground_truth_path)
    if path.is_dir():
        # Look for csharp.json in directory
        path = path / "csharp.json"

    if not path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {path}")

    with open(path) as f:
        return json.load(f)


def get_violations_for_file(analysis: dict, file_path: str) -> list[dict]:
    """Get violations for a specific file from analysis results."""
    for file_data in analysis.get("files", []):
        if file_path in file_data.get("path", "") or file_path in file_data.get("relative_path", ""):
            return file_data.get("violations", [])
    return []


def count_violations_by_rule(analysis: dict, rule_id: str) -> int:
    """Count total violations for a specific rule."""
    count = 0
    for file_data in analysis.get("files", []):
        for v in file_data.get("violations", []):
            if v.get("rule_id") == rule_id:
                count += 1
    return count


def count_violations_by_category(analysis: dict, category: str) -> int:
    """Count total violations for a specific category."""
    return analysis.get("summary", {}).get("violations_by_category", {}).get(category, 0)
