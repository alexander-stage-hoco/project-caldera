"""Evaluation check framework for gitleaks PoC."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
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
        """Add a check result to the report."""
        self.results.append(result)
        self.total_checks += 1
        if result.passed:
            self.passed_checks += 1
        else:
            self.failed_checks += 1
        self.pass_rate = self.passed_checks / self.total_checks if self.total_checks > 0 else 0.0


def check_equal(
    check_id: str,
    category: str,
    name: str,
    expected: Any,
    actual: Any,
    tolerance: int = 0,
) -> CheckResult:
    """Check if expected equals actual within tolerance."""
    if tolerance == 0:
        passed = expected == actual
    else:
        passed = abs(expected - actual) <= tolerance

    return CheckResult(
        check_id=check_id,
        category=category,
        passed=passed,
        message=f"{name}: expected {expected}, got {actual}",
        expected=expected,
        actual=actual,
    )


def check_at_least(
    check_id: str,
    category: str,
    name: str,
    minimum: Any,
    actual: Any,
) -> CheckResult:
    """Check if actual is at least minimum."""
    passed = actual >= minimum
    return CheckResult(
        check_id=check_id,
        category=category,
        passed=passed,
        message=f"{name}: expected >= {minimum}, got {actual}",
        expected=f">= {minimum}",
        actual=actual,
    )


def check_at_most(
    check_id: str,
    category: str,
    name: str,
    maximum: Any,
    actual: Any,
) -> CheckResult:
    """Check if actual is at most maximum."""
    passed = actual <= maximum
    return CheckResult(
        check_id=check_id,
        category=category,
        passed=passed,
        message=f"{name}: expected <= {maximum}, got {actual}",
        expected=f"<= {maximum}",
        actual=actual,
    )


def check_contains(
    check_id: str,
    category: str,
    name: str,
    expected_items: list[Any],
    actual_set: set[Any] | list[Any],
) -> CheckResult:
    """Check if actual set contains all expected items."""
    actual_set = set(actual_set)
    missing = [item for item in expected_items if item not in actual_set]
    passed = len(missing) == 0

    return CheckResult(
        check_id=check_id,
        category=category,
        passed=passed,
        message=f"{name}: missing {missing}" if not passed else f"{name}: all expected items found",
        expected=expected_items,
        actual=list(actual_set),
    )


def check_not_contains(
    check_id: str,
    category: str,
    name: str,
    forbidden_items: list[Any],
    actual_set: set[Any] | list[Any],
) -> CheckResult:
    """Check if actual set does not contain any forbidden items."""
    actual_set = set(actual_set)
    found = [item for item in forbidden_items if item in actual_set]
    passed = len(found) == 0

    return CheckResult(
        check_id=check_id,
        category=category,
        passed=passed,
        message=f"{name}: found forbidden {found}" if not passed else f"{name}: no forbidden items found",
        expected=f"none of {forbidden_items}",
        actual=list(actual_set),
    )


def check_boolean(
    check_id: str,
    category: str,
    name: str,
    expected: bool,
    actual: bool,
) -> CheckResult:
    """Check if boolean value matches expected."""
    passed = expected == actual
    return CheckResult(
        check_id=check_id,
        category=category,
        passed=passed,
        message=f"{name}: expected {expected}, got {actual}",
        expected=expected,
        actual=actual,
    )


def load_analysis(analysis_path: Path) -> dict:
    """Load analysis JSON with root wrapper preserved for schema checks."""
    import json as _json

    data = _json.loads(analysis_path.read_text())
    if isinstance(data, dict) and "results" in data:
        normalized = dict(data.get("results", {}))
        normalized["schema_version"] = data.get("schema_version")
        normalized["timestamp"] = data.get("generated_at")
        normalized["repository"] = data.get("repo_name")
        normalized["repo_path"] = data.get("repo_path")
        normalized["_root"] = data
        return normalized
    return data
