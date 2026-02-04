"""Core evaluation types for license analysis PoC."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CheckResult:
    """Result of a single evaluation check."""

    check_id: str
    category: str
    passed: bool
    message: str
    expected: Any = None
    actual: Any = None


@dataclass
class EvaluationReport:
    """Complete evaluation report for a repository."""

    repository: str
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    pass_rate: float = 0.0
    results: list[CheckResult] = field(default_factory=list)

    def add_result(self, result: CheckResult) -> None:
        """Add a check result and update statistics."""
        self.results.append(result)
        self.total_checks += 1
        if result.passed:
            self.passed_checks += 1
        else:
            self.failed_checks += 1
        self.pass_rate = (
            self.passed_checks / self.total_checks if self.total_checks > 0 else 0.0
        )


def check_equal(
    check_id: str,
    category: str,
    name: str,
    expected: Any,
    actual: Any,
    tolerance: float = 0,
) -> CheckResult:
    """Create a check result comparing expected vs actual values."""
    if tolerance > 0 and isinstance(expected, int | float) and isinstance(actual, int | float):
        passed = abs(expected - actual) <= tolerance
    else:
        passed = expected == actual

    return CheckResult(
        check_id=check_id,
        category=category,
        passed=passed,
        message=f"{name}: expected={expected}, actual={actual}",
        expected=expected,
        actual=actual,
    )


def check_in_range(
    check_id: str,
    category: str,
    name: str,
    value: float,
    min_val: float,
    max_val: float,
) -> CheckResult:
    """Create a check result for value in range."""
    passed = min_val <= value <= max_val
    return CheckResult(
        check_id=check_id,
        category=category,
        passed=passed,
        message=f"{name}: value={value}, range=[{min_val}, {max_val}]",
        expected=f"[{min_val}, {max_val}]",
        actual=value,
    )


def check_contains(
    check_id: str,
    category: str,
    name: str,
    expected_items: list,
    actual_items: list,
) -> CheckResult:
    """Check that actual contains all expected items."""
    missing = set(expected_items) - set(actual_items)
    passed = len(missing) == 0
    return CheckResult(
        check_id=check_id,
        category=category,
        passed=passed,
        message=f"{name}: missing={list(missing) if missing else 'none'}",
        expected=expected_items,
        actual=actual_items,
    )


def check_boolean(
    check_id: str,
    category: str,
    name: str,
    expected: bool,
    actual: bool,
) -> CheckResult:
    """Check boolean equality."""
    passed = expected == actual
    return CheckResult(
        check_id=check_id,
        category=category,
        passed=passed,
        message=f"{name}: expected={expected}, actual={actual}",
        expected=expected,
        actual=actual,
    )
