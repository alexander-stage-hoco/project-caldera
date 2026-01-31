"""
Evaluation checks for SonarQube analysis.

This module provides programmatic checks to validate SonarQube output against ground truth.
Checks are organized into five categories:
- Accuracy (SQ-AC-1 to SQ-AC-5): Issue detection accuracy
- Coverage (SQ-CV-1 to SQ-CV-4): Metric and language coverage
- Completeness (SQ-CM-1 to SQ-CM-6): Data structure completeness
- Edge Cases (SQ-EC-*): Robustness testing
- Performance (SQ-PF-*): Speed and resource checks
"""

from dataclasses import dataclass, field
from typing import Any
from enum import Enum
from pathlib import Path
import json


class CheckCategory(Enum):
    """Categories of evaluation checks."""
    ACCURACY = "accuracy"
    COVERAGE = "coverage"
    COMPLETENESS = "completeness"
    EDGE_CASES = "edge_cases"
    PERFORMANCE = "performance"


@dataclass
class CheckResult:
    """Result of a single evaluation check."""
    check_id: str           # e.g., "SQ-AC-1"
    name: str               # e.g., "Issue count accuracy"
    category: CheckCategory
    passed: bool
    score: float            # 0.0 to 1.0
    message: str            # Human-readable result description
    evidence: dict[str, Any] = field(default_factory=dict)  # Supporting data

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "check_id": self.check_id,
            "name": self.name,
            "category": self.category.value,
            "passed": self.passed,
            "score": self.score,
            "message": self.message,
            "evidence": self.evidence,
        }


@dataclass
class EvaluationReport:
    """Complete evaluation report with all check results."""
    timestamp: str
    analysis_path: str
    ground_truth_dir: str
    checks: list[CheckResult]

    @property
    def passed(self) -> int:
        """Count of passed checks."""
        return sum(1 for c in self.checks if c.passed)

    @property
    def failed(self) -> int:
        """Count of failed checks."""
        return sum(1 for c in self.checks if not c.passed)

    @property
    def total(self) -> int:
        """Total number of checks."""
        return len(self.checks)

    @property
    def score(self) -> float:
        """Overall score (0.0 to 1.0)."""
        if not self.checks:
            return 0.0
        return sum(c.score for c in self.checks) / len(self.checks)

    @property
    def score_by_category(self) -> dict[str, float]:
        """Score breakdown by category."""
        categories: dict[str, list[float]] = {}
        for check in self.checks:
            cat = check.category.value
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(check.score)

        return {
            cat: sum(scores) / len(scores) if scores else 0.0
            for cat, scores in categories.items()
        }

    @property
    def passed_by_category(self) -> dict[str, tuple[int, int]]:
        """Passed/total breakdown by category."""
        categories: dict[str, list[bool]] = {}
        for check in self.checks:
            cat = check.category.value
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(check.passed)

        return {
            cat: (sum(results), len(results))
            for cat, results in categories.items()
        }

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "analysis_path": self.analysis_path,
            "ground_truth_dir": self.ground_truth_dir,
            "summary": {
                "passed": self.passed,
                "failed": self.failed,
                "total": self.total,
                "score": round(self.score, 4),
                "score_by_category": {
                    k: round(v, 4) for k, v in self.score_by_category.items()
                },
                "passed_by_category": self.passed_by_category,
            },
            "checks": [c.to_dict() for c in self.checks],
        }


def load_analysis(analysis_path: str | Path) -> dict:
    """Load analysis JSON file.

    Handles Caldera envelope format (with metadata/data) and legacy format.
    """
    with open(analysis_path) as f:
        data = json.load(f)

    # Handle Caldera envelope format
    if isinstance(data, dict) and "metadata" in data and "data" in data:
        return data["data"]

    return data


def load_ground_truth(ground_truth_dir: str | Path, name: str) -> dict | None:
    """Load ground truth for a specific repo."""
    gt_path = Path(ground_truth_dir) / f"{name}.json"
    if gt_path.exists():
        with open(gt_path) as f:
            return json.load(f)
    return None


def load_all_ground_truth(ground_truth_dir: str | Path) -> dict[str, dict]:
    """Load all ground truth files."""
    gt_dir = Path(ground_truth_dir)
    result = {}
    for gt_file in gt_dir.glob("*.json"):
        with open(gt_file) as f:
            data = json.load(f)
            result[gt_file.stem] = data
    return result


def get_nested(data: dict, path: str, default: Any = None) -> Any:
    """Get nested value from dict using dot notation.

    Handles both legacy format (flat) and new format (with results wrapper).
    """
    keys = path.split(".")
    current = data

    # Handle results wrapper
    if (
        isinstance(current, dict)
        and "results" in current
        and isinstance(current.get("results"), dict)
        and keys[0] not in current
        and keys[0] in current["results"]
    ):
        current = current["results"]

    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current


def in_range(value: float | int, min_val: float | int, max_val: float | int) -> bool:
    """Check if value is in range [min_val, max_val]."""
    return min_val <= value <= max_val


def get_issues_rollups(analysis: dict) -> dict:
    """Extract issues rollups from analysis data."""
    results = analysis.get("results", analysis)
    return results.get("issues", {}).get("rollups", {})


def get_components(analysis: dict) -> dict:
    """Extract components from analysis data."""
    results = analysis.get("results", analysis)
    return results.get("components", {})


def get_quality_gate(analysis: dict) -> dict:
    """Extract quality gate from analysis data."""
    results = analysis.get("results", analysis)
    return results.get("quality_gate", {})


# Expose check modules
from .accuracy import run_accuracy_checks
from .coverage import run_coverage_checks
from .completeness import run_completeness_checks
from .edge_cases import run_edge_case_checks
from .performance import run_performance_checks

__all__ = [
    "CheckResult",
    "CheckCategory",
    "EvaluationReport",
    "load_analysis",
    "load_ground_truth",
    "load_all_ground_truth",
    "get_nested",
    "in_range",
    "get_issues_rollups",
    "get_components",
    "get_quality_gate",
    "run_accuracy_checks",
    "run_coverage_checks",
    "run_completeness_checks",
    "run_edge_case_checks",
    "run_performance_checks",
]
