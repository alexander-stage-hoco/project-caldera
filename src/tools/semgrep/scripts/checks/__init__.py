"""
Evaluation checks for Semgrep smell analysis.

This module provides programmatic checks to validate Semgrep output against ground truth.
Checks are organized into four categories:
- Accuracy (AC-1 to AC-9): Smell detection accuracy
- Coverage (CV-1 to CV-8): Language and category coverage
- Edge Cases (EC-1 to EC-8): Edge case handling
- Performance (PF-1 to PF-4): Speed and resource checks
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
    OUTPUT_QUALITY = "output_quality"
    INTEGRATION_FIT = "integration_fit"


# DD Smell Categories
SMELL_CATEGORIES = [
    "size_complexity",
    "refactoring",
    "dependency",
    "error_handling",
    "async_concurrency",
    "resource_management",
    "nullability",
    "api_design",
    "dead_code",
    "security",  # SQL injection, SSRF, etc.
    # Code Quality (Phase 3)
    "correctness",      # Logic errors, null dereferences, boundary issues
    "best_practice",    # Anti-patterns, deprecated APIs, maintainability issues
    "performance",      # Inefficient patterns, complexity issues
]


@dataclass
class CheckResult:
    """Result of a single evaluation check."""
    check_id: str           # e.g., "AC-1"
    name: str               # e.g., "Empty catch detection"
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
        data = json.load(f)
    if isinstance(data, dict) and isinstance(data.get("results"), dict):
        results = dict(data["results"])
        results["_root"] = data
        return results
    return data


def load_ground_truth(ground_truth_dir: str | Path, language: str) -> dict | None:
    """Load ground truth for a specific language."""
    gt_path = Path(ground_truth_dir) / f"{language}.json"
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
            result[data.get("language", gt_file.stem)] = data
    return result


def normalize_path(path: str) -> str:
    """Normalize path for comparison (handle leading ./, remove leading /)."""
    path = path.strip()
    if path.startswith("./"):
        path = path[2:]
    if path.startswith("/"):
        path = path[1:]
    return path


def get_file_from_analysis(analysis: dict, file_path: str) -> dict | None:
    """Find a file in the analysis by its path."""
    # Handle both old format (flat) and new format (with results wrapper)
    results = analysis.get("results", analysis) if "results" in analysis else analysis
    normalized_target = normalize_path(file_path)
    for file_info in results.get("files", []):
        normalized = normalize_path(file_info.get("path", ""))
        if normalized == normalized_target or normalized.endswith(normalized_target):
            return file_info
    return None


def get_smells_by_category(analysis: dict) -> dict[str, int]:
    """Get smell counts by DD category."""
    # Handle both old format (flat) and new format (with results wrapper)
    results = analysis.get("results", analysis) if "results" in analysis else analysis
    counts: dict[str, int] = {cat: 0 for cat in SMELL_CATEGORIES}
    for file_info in results.get("files", []):
        for smell in file_info.get("smells", []):
            cat = smell.get("dd_category", "")
            if cat in counts:
                counts[cat] += 1
    return counts


def get_smells_by_type(analysis: dict) -> dict[str, int]:
    """Get smell counts by DD smell type (e.g., D1_EMPTY_CATCH)."""
    # Handle both old format (flat) and new format (with results wrapper)
    results = analysis.get("results", analysis) if "results" in analysis else analysis
    counts: dict[str, int] = {}
    for file_info in results.get("files", []):
        for smell in file_info.get("smells", []):
            smell_type = smell.get("dd_smell_id", smell.get("rule_id", "unknown"))
            counts[smell_type] = counts.get(smell_type, 0) + 1
    return counts


def get_language_stats(analysis: dict) -> dict[str, dict]:
    """Get per-language statistics."""
    # Handle both old format (flat) and new format (with results wrapper)
    results = analysis.get("results", analysis) if "results" in analysis else analysis
    stats: dict[str, dict] = {}
    for file_info in results.get("files", []):
        lang = file_info.get("language", "unknown")
        if lang not in stats:
            stats[lang] = {
                "files": 0,
                "smells": 0,
                "categories_covered": set(),
            }
        stats[lang]["files"] += 1
        stats[lang]["smells"] += len(file_info.get("smells", []))
        for smell in file_info.get("smells", []):
            cat = smell.get("dd_category", "")
            if cat:
                stats[lang]["categories_covered"].add(cat)

    # Convert sets to lists for JSON serialization
    for lang in stats:
        stats[lang]["categories_covered"] = list(stats[lang]["categories_covered"])

    return stats


# Expose check modules
from .accuracy import run_accuracy_checks
from .coverage import run_coverage_checks
from .edge_cases import run_edge_case_checks
from .output_quality import run_output_quality_checks
from .performance import run_performance_checks
from .integration_fit import run_integration_fit_checks
from .security import run_security_checks

__all__ = [
    "CheckResult",
    "CheckCategory",
    "EvaluationReport",
    "SMELL_CATEGORIES",
    "load_analysis",
    "load_ground_truth",
    "load_all_ground_truth",
    "normalize_path",
    "get_file_from_analysis",
    "get_smells_by_category",
    "get_smells_by_type",
    "get_language_stats",
    "run_accuracy_checks",
    "run_coverage_checks",
    "run_edge_case_checks",
    "run_output_quality_checks",
    "run_performance_checks",
    "run_integration_fit_checks",
    "run_security_checks",
]
