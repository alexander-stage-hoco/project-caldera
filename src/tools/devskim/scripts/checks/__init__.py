"""
Evaluation checks for DevSkim security analysis.

This module provides programmatic checks to validate DevSkim output against ground truth.
Checks are organized into four categories:
- Accuracy (AC-1 to AC-8): Security detection accuracy
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


# DD Security Categories (DevSkim focuses on security)
SECURITY_CATEGORIES = [
    "sql_injection",
    "hardcoded_secret",
    "insecure_crypto",
    "path_traversal",
    "xss",
    "deserialization",
    "xxe",
    "command_injection",
    "ldap_injection",
    "open_redirect",
    "ssrf",
    "csrf",
    "information_disclosure",
    "broken_access_control",
    "security_misconfiguration",
]


@dataclass
class CheckResult:
    """Result of a single evaluation check."""
    check_id: str           # e.g., "AC-1"
    name: str               # e.g., "SQL injection detection"
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

    @property
    def decision(self) -> str:
        """Overall decision based on score."""
        if self.score >= 0.8:
            return "STRONG_PASS"
        elif self.score >= 0.6:
            return "PASS"
        elif self.score >= 0.5:
            return "WEAK_PASS"
        else:
            return "FAIL"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "analysis_path": self.analysis_path,
            "ground_truth_dir": self.ground_truth_dir,
            # Root-level decision and score for compliance scanner compatibility
            "decision": self.decision,
            "score": round(self.score, 4),
            "summary": {
                "passed": self.passed,
                "failed": self.failed,
                "total": self.total,
                "score": round(self.score, 4),
                "decision": self.decision,
                "score_by_category": {
                    k: round(v, 4) for k, v in self.score_by_category.items()
                },
                "passed_by_category": self.passed_by_category,
            },
            "checks": [c.to_dict() for c in self.checks],
        }


def load_analysis(analysis_path: str | Path) -> dict:
    """Load analysis JSON file.

    Handles both envelope formats:
    - {"results": {...}} - older format
    - {"data": {...}} - Caldera envelope format
    """
    with open(analysis_path) as f:
        data = json.load(f)

    # Handle Caldera envelope format ({"data": {...}})
    if isinstance(data, dict) and isinstance(data.get("data"), dict):
        results = dict(data["data"])
        results["_root"] = data
        return results

    # Handle older envelope format ({"results": {...}})
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
    normalized_target = normalize_path(file_path)
    for file_info in analysis.get("files", []):
        normalized = normalize_path(file_info.get("path", ""))
        if normalized == normalized_target or normalized.endswith(normalized_target):
            return file_info
    return None


def get_issues_by_category(analysis: dict) -> dict[str, int]:
    """Get issue counts by DD category."""
    counts: dict[str, int] = {cat: 0 for cat in SECURITY_CATEGORIES}
    counts["unknown"] = 0
    for file_info in analysis.get("files", []):
        for issue in file_info.get("issues", []):
            cat = issue.get("dd_category", "unknown")
            if cat in counts:
                counts[cat] += 1
            else:
                counts["unknown"] += 1
    return counts


def get_issues_by_severity(analysis: dict) -> dict[str, int]:
    """Get issue counts by severity."""
    counts: dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for file_info in analysis.get("files", []):
        for issue in file_info.get("issues", []):
            sev = issue.get("severity", "LOW")
            if sev in counts:
                counts[sev] += 1
    return counts


def get_language_stats(analysis: dict) -> dict[str, dict]:
    """Get per-language statistics."""
    stats: dict[str, dict] = {}
    for file_info in analysis.get("files", []):
        lang = file_info.get("language", "unknown")
        if lang not in stats:
            stats[lang] = {
                "files": 0,
                "issues": 0,
                "categories_covered": set(),
            }
        stats[lang]["files"] += 1
        stats[lang]["issues"] += len(file_info.get("issues", []))
        for issue in file_info.get("issues", []):
            cat = issue.get("dd_category", "")
            if cat:
                stats[lang]["categories_covered"].add(cat)

    # Convert sets to lists for JSON serialization
    for lang in stats:
        stats[lang]["categories_covered"] = list(stats[lang]["categories_covered"])

    return stats


def count_findings_for_file(analysis: dict, file_path: str, category: str | None = None) -> int:
    """Count findings for a specific file, optionally filtered by category."""
    file_info = get_file_from_analysis(analysis, file_path)
    if not file_info:
        return 0

    issues = file_info.get("issues", [])
    if category:
        return sum(1 for issue in issues if issue.get("dd_category") == category)
    return len(issues)


def count_findings_by_category(analysis: dict, category: str) -> int:
    """Count total findings for a specific category."""
    return get_issues_by_category(analysis).get(category, 0)


# Expose check modules
from .accuracy import run_accuracy_checks
from .coverage import run_coverage_checks
from .edge_cases import run_edge_case_checks
from .performance import run_performance_checks
from .output_quality import run_output_quality_checks
from .integration_fit import run_integration_fit_checks

__all__ = [
    "CheckResult",
    "CheckCategory",
    "EvaluationReport",
    "SECURITY_CATEGORIES",
    "load_analysis",
    "load_ground_truth",
    "load_all_ground_truth",
    "normalize_path",
    "get_file_from_analysis",
    "get_issues_by_category",
    "get_issues_by_severity",
    "get_language_stats",
    "count_findings_for_file",
    "count_findings_by_category",
    "run_accuracy_checks",
    "run_coverage_checks",
    "run_edge_case_checks",
    "run_performance_checks",
    "run_output_quality_checks",
    "run_integration_fit_checks",
]
