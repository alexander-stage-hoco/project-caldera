"""Evaluation checks for Lizard function analysis.

This module provides programmatic checks to validate Lizard outputs against
ground truth and expected behaviors.

Check Categories:
- Accuracy (AC-*): CCN and function detection correctness
- Coverage (CV-*): Language coverage verification
- Edge Cases (EC-*): Handling of edge cases
- Performance (PF-*): Speed and resource usage
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class CheckCategory(Enum):
    """Categories of evaluation checks."""
    ACCURACY = "accuracy"
    COVERAGE = "coverage"
    EDGE_CASES = "edge_cases"
    PERFORMANCE = "performance"


class CheckSeverity(Enum):
    """Severity levels for check failures."""
    CRITICAL = "critical"  # Must pass
    HIGH = "high"          # Should pass
    MEDIUM = "medium"      # Nice to have
    LOW = "low"            # Informational


@dataclass
class CheckResult:
    """Result of a single evaluation check."""
    check_id: str                    # e.g., "AC-1"
    name: str                        # e.g., "Simple functions CCN=1"
    category: CheckCategory
    severity: CheckSeverity
    passed: bool
    score: float                     # 0.0 to 1.0
    message: str                     # Human-readable result
    evidence: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate score range."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be between 0.0 and 1.0, got {self.score}")


@dataclass
class EvaluationReport:
    """Complete evaluation report with all check results."""
    timestamp: str
    analysis_path: str
    ground_truth_path: str
    checks: List[CheckResult] = field(default_factory=list)

    @property
    def total_checks(self) -> int:
        return len(self.checks)

    @property
    def passed_checks(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def failed_checks(self) -> int:
        return sum(1 for c in self.checks if not c.passed)

    @property
    def overall_score(self) -> float:
        if not self.checks:
            return 0.0
        return sum(c.score for c in self.checks) / len(self.checks)

    @property
    def critical_failures(self) -> List[CheckResult]:
        return [c for c in self.checks
                if not c.passed and c.severity == CheckSeverity.CRITICAL]

    def by_category(self, category: CheckCategory) -> List[CheckResult]:
        return [c for c in self.checks if c.category == category]

    def to_dict(self) -> Dict[str, Any]:
        score = round(self.overall_score, 3)
        normalized = 1 + (self.overall_score * 4)  # 0-1 → 1-5
        if normalized >= 4.0:
            decision = "STRONG_PASS"
        elif normalized >= 3.5:
            decision = "PASS"
        elif normalized >= 3.0:
            decision = "WEAK_PASS"
        else:
            decision = "FAIL"

        return {
            "decision": decision,
            "score": score,
            "timestamp": self.timestamp,
            "analysis_path": self.analysis_path,
            "ground_truth_path": self.ground_truth_path,
            "summary": {
                "total_checks": self.total_checks,
                "passed": self.passed_checks,
                "failed": self.failed_checks,
                "score": round(self.overall_score, 3),
            },
            "checks": [
                {
                    "check_id": c.check_id,
                    "name": c.name,
                    "category": c.category.value,
                    "severity": c.severity.value,
                    "passed": c.passed,
                    "score": round(c.score, 3),
                    "message": c.message,
                    "evidence": c.evidence,
                }
                for c in self.checks
            ],
        }


def create_check_result(
    check_id: str,
    name: str,
    category: CheckCategory,
    severity: CheckSeverity,
    passed: bool,
    message: str,
    evidence: Optional[Dict[str, Any]] = None,
) -> CheckResult:
    """Helper to create a CheckResult with automatic score calculation."""
    return CheckResult(
        check_id=check_id,
        name=name,
        category=category,
        severity=severity,
        passed=passed,
        score=1.0 if passed else 0.0,
        message=message,
        evidence=evidence or {},
    )


def create_partial_check_result(
    check_id: str,
    name: str,
    category: CheckCategory,
    severity: CheckSeverity,
    score: float,
    message: str,
    evidence: Optional[Dict[str, Any]] = None,
) -> CheckResult:
    """Helper to create a CheckResult with partial score."""
    return CheckResult(
        check_id=check_id,
        name=name,
        category=category,
        severity=severity,
        passed=score >= 0.8,  # Consider 80%+ as passing
        score=score,
        message=message,
        evidence=evidence or {},
    )
