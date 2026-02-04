"""
Evaluation checks for PMD CPD duplication analysis.

This module provides programmatic checks to validate CPD output against ground truth.
Checks are organized into four categories:
- Accuracy (AC-1 to AC-8): Clone detection accuracy
- Coverage (CV-1 to CV-8): Language and file coverage
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


# Target languages for CPD
SUPPORTED_LANGUAGES = [
    "python",
    "javascript",
    "typescript",
    "csharp",
    "java",
    "go",
    "rust",
]


@dataclass
class CheckResult:
    """Result of a single evaluation check."""
    check_id: str           # e.g., "AC-1"
    name: str               # e.g., "Heavy duplication detection"
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

    Supports both full output (with top-level results wrapper) and
    direct results payloads.
    """
    with open(analysis_path) as f:
        data = json.load(f)

    if isinstance(data, dict) and "results" in data and isinstance(data["results"], dict):
        return data["results"]
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
    """Normalize path for comparison."""
    path = path.strip()
    path = path.replace("\\", "/")
    if path.startswith("./"):
        path = path[2:]
    if path.startswith("/"):
        path = path[1:]
    return path


def get_file_from_analysis(analysis: dict, file_path: str) -> dict | None:
    """Find a file in the analysis by its path."""
    normalized_target = normalize_path(file_path)
    for file_info in analysis.get("files", []):
        normalized = normalize_path(file_info.get("path", ""))
        if normalized == normalized_target or normalized.endswith(normalized_target):
            return file_info
    return None


def get_language_from_path(file_path: str) -> str:
    """Detect language from file path."""
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".cs": "csharp",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
    }
    ext = Path(file_path).suffix.lower()
    return ext_map.get(ext, "unknown")


def get_clones_for_file(analysis: dict, file_path: str) -> list[dict]:
    """Get all clones that involve a specific file."""
    normalized_target = normalize_path(file_path)
    clones = []
    for dup in analysis.get("duplications", []):
        for occ in dup.get("occurrences", []):
            normalized = normalize_path(occ.get("file", ""))
            if normalized == normalized_target or normalized.endswith(normalized_target):
                clones.append(dup)
                break
    return clones


def get_cross_file_clones(analysis: dict) -> list[dict]:
    """Get all cross-file clones."""
    cross_file = []
    for dup in analysis.get("duplications", []):
        files = set()
        for occ in dup.get("occurrences", []):
            files.add(normalize_path(occ.get("file", "")))
        if len(files) > 1:
            cross_file.append(dup)
    return cross_file


def get_language_stats(analysis: dict) -> dict[str, dict]:
    """Get per-language statistics."""
    stats: dict[str, dict] = {}
    for file_info in analysis.get("files", []):
        lang = file_info.get("language", "unknown")
        if lang not in stats:
            stats[lang] = {
                "files": 0,
                "clones": 0,
                "duplicate_lines": 0,
            }
        stats[lang]["files"] += 1
        stats[lang]["duplicate_lines"] += file_info.get("duplicate_lines", 0)
        stats[lang]["clones"] += file_info.get("duplicate_blocks", 0)
    return stats


# Expose check modules
from .accuracy import run_accuracy_checks
from .coverage import run_coverage_checks
from .edge_cases import run_edge_case_checks
from .performance import run_performance_checks

__all__ = [
    "CheckResult",
    "CheckCategory",
    "EvaluationReport",
    "SUPPORTED_LANGUAGES",
    "load_analysis",
    "load_ground_truth",
    "load_all_ground_truth",
    "normalize_path",
    "get_file_from_analysis",
    "get_language_from_path",
    "get_clones_for_file",
    "get_cross_file_clones",
    "get_language_stats",
    "run_accuracy_checks",
    "run_coverage_checks",
    "run_edge_case_checks",
    "run_performance_checks",
]
