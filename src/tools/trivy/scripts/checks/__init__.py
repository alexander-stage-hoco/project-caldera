"""Trivy evaluation checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CheckResult:
    """Result of a single evaluation check."""

    check_id: str
    category: str
    passed: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationReport:
    """Summary report of all evaluation checks.

    Attributes:
        checks: List of individual check results
        passed_count: Number of checks that passed
        failed_count: Number of checks that failed
        pass_rate: Percentage of checks that passed (0-100)
        by_category: Results grouped by category
    """

    checks: list[CheckResult] = field(default_factory=list)
    passed_count: int = 0
    failed_count: int = 0
    pass_rate: float = 0.0
    by_category: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def from_checks(cls, checks: list[CheckResult]) -> "EvaluationReport":
        """Create an EvaluationReport from a list of CheckResults."""
        passed_count = sum(1 for c in checks if c.passed)
        failed_count = len(checks) - passed_count
        pass_rate = (passed_count / len(checks) * 100) if checks else 0.0

        by_category: dict[str, dict[str, Any]] = {}
        for check in checks:
            if check.category not in by_category:
                by_category[check.category] = {"passed": 0, "failed": 0, "checks": []}
            if check.passed:
                by_category[check.category]["passed"] += 1
            else:
                by_category[check.category]["failed"] += 1
            by_category[check.category]["checks"].append(check.check_id)

        return cls(
            checks=checks,
            passed_count=passed_count,
            failed_count=failed_count,
            pass_rate=pass_rate,
            by_category=by_category,
        )
