"""
Evaluation checks for git-sizer repository health analysis.

This module provides programmatic checks to validate git-sizer output against ground truth.
Checks are organized into four categories:
- Accuracy (AC-1 to AC-8): Size detection accuracy
- Coverage (CV-1 to CV-8): Metric coverage
- Edge Cases (EC-1 to EC-8): Edge case handling
- Performance (PF-1 to PF-4): Speed and efficiency
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
    EDGE_CASES = "edge_cases"
    PERFORMANCE = "performance"


@dataclass
class CheckResult:
    """Result of a single evaluation check."""
    check_id: str           # e.g., "AC-1"
    name: str               # e.g., "Large blob detection"
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
    """Load analysis JSON file."""
    with open(analysis_path) as f:
        return json.load(f)


def load_ground_truth(ground_truth_dir: str | Path, repo_name: str) -> dict | None:
    """Load ground truth for a specific repository."""
    gt_path = Path(ground_truth_dir) / f"{repo_name}.json"
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


def get_repo_from_results(results_dir: str | Path, repo_name: str) -> dict | None:
    """Load analysis results for a specific repository from the results directory.

    In Caldera, results are stored as evaluation/results/<repo-name>/output.json
    """
    output_path = Path(results_dir) / repo_name / "output.json"
    if output_path.exists():
        with open(output_path) as f:
            data = json.load(f)
            # Caldera envelope format - extract data section and add repo info
            if "data" in data:
                result = data["data"].copy()
                result["repository"] = repo_name
                result["metadata"] = data.get("metadata", {})
                return result
            return data
    return None


def load_all_results(results_dir: str | Path) -> dict:
    """Load all analysis results from the results directory.

    Returns a dict with 'repositories' list for compatibility with Vulcan format.
    """
    results_path = Path(results_dir)
    repositories = []

    root_output = results_path / "output.json"
    if root_output.exists():
        with open(root_output) as f:
            data = json.load(f)
            if "data" in data:
                repo_data = data["data"].copy()
                repo_name = data.get("metadata", {}).get("repo_name") or repo_data.get("repo_name") or "primary"
                repo_data["repository"] = repo_name
                repo_data["metadata"] = data.get("metadata", {})
                repositories.append(repo_data)

    for repo_dir in results_path.iterdir():
        if repo_dir.is_dir():
            output_path = repo_dir / "output.json"
            if output_path.exists():
                with open(output_path) as f:
                    data = json.load(f)
                    # Caldera envelope format
                    if "data" in data:
                        repo_data = data["data"].copy()
                        repo_data["repository"] = repo_dir.name
                        repo_data["metadata"] = data.get("metadata", {})
                        repositories.append(repo_data)

    return {
        "repositories": repositories,
        "summary": {
            "total_repositories": len(repositories),
        }
    }


def get_repo_by_name(analysis: dict, repo_name: str) -> dict | None:
    """Find a repository in the analysis by its name.

    Returns the flattened repo data with metrics at top level.
    Handles both Caldera format (repositories list) and direct format.
    """
    for repo in analysis.get("repositories", []):
        # Check various name fields
        if repo.get("repository") == repo_name:
            return repo
        if repo.get("repo_name") == repo_name:
            return repo
    return None


# Expose check modules
from .accuracy import run_accuracy_checks
from .coverage import run_coverage_checks
from .edge_cases import run_edge_case_checks
from .performance import run_performance_checks

__all__ = [
    "CheckResult",
    "CheckCategory",
    "EvaluationReport",
    "load_analysis",
    "load_ground_truth",
    "load_all_ground_truth",
    "load_all_results",
    "get_repo_from_results",
    "get_repo_by_name",
    "run_accuracy_checks",
    "run_coverage_checks",
    "run_edge_case_checks",
    "run_performance_checks",
]
