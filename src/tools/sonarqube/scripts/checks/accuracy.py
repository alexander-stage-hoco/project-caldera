"""Accuracy checks (SQ-AC-*) for SonarQube evaluation."""

from . import (
    CheckCategory,
    CheckResult,
    get_nested,
    in_range,
)


def check_issue_count(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-AC-1: Check that total issue count is within expected range."""
    if not ground_truth:
        return CheckResult(
            check_id="SQ-AC-1",
            name="Issue count accuracy",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=0.5,
            message="No ground truth provided, skipping",
            evidence={"skipped": True},
        )

    expected = ground_truth.get("expected_issues", {})
    min_val = expected.get("min", 0)
    max_val = expected.get("max", float("inf"))

    results = data.get("results", data)
    actual = get_nested(results, "issues.rollups.total", 0)

    passed = in_range(actual, min_val, max_val)
    return CheckResult(
        check_id="SQ-AC-1",
        name="Issue count accuracy",
        category=CheckCategory.ACCURACY,
        passed=passed,
        score=1.0 if passed else 0.0,
        message=f"Issue count {actual} {'within' if passed else 'outside'} expected range [{min_val}, {max_val}]",
        evidence={"expected": {"min": min_val, "max": max_val}, "actual": actual},
    )


def check_bug_count(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-AC-2: Check that bug count is within expected range."""
    if not ground_truth:
        return CheckResult(
            check_id="SQ-AC-2",
            name="Bug count accuracy",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=0.5,
            message="No ground truth provided, skipping",
            evidence={"skipped": True},
        )

    expected = ground_truth.get("expected_bugs", {})
    min_val = expected.get("min", 0)
    max_val = expected.get("max", float("inf"))

    results = data.get("results", data)
    actual = get_nested(results, "issues.rollups.by_type.BUG", 0)

    passed = in_range(actual, min_val, max_val)
    return CheckResult(
        check_id="SQ-AC-2",
        name="Bug count accuracy",
        category=CheckCategory.ACCURACY,
        passed=passed,
        score=1.0 if passed else 0.0,
        message=f"Bug count {actual} {'within' if passed else 'outside'} expected range [{min_val}, {max_val}]",
        evidence={"expected": {"min": min_val, "max": max_val}, "actual": actual},
    )


def check_vulnerability_count(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-AC-3: Check that vulnerability count is within expected range."""
    if not ground_truth:
        return CheckResult(
            check_id="SQ-AC-3",
            name="Vulnerability count accuracy",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=0.5,
            message="No ground truth provided, skipping",
            evidence={"skipped": True},
        )

    expected = ground_truth.get("expected_vulnerabilities", {})
    min_val = expected.get("min", 0)
    max_val = expected.get("max", float("inf"))

    results = data.get("results", data)
    actual = get_nested(results, "issues.rollups.by_type.VULNERABILITY", 0)

    passed = in_range(actual, min_val, max_val)
    return CheckResult(
        check_id="SQ-AC-3",
        name="Vulnerability count accuracy",
        category=CheckCategory.ACCURACY,
        passed=passed,
        score=1.0 if passed else 0.0,
        message=f"Vulnerability count {actual} {'within' if passed else 'outside'} expected range [{min_val}, {max_val}]",
        evidence={"expected": {"min": min_val, "max": max_val}, "actual": actual},
    )


def check_smell_count(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-AC-4: Check that code smell count is within expected range."""
    if not ground_truth:
        return CheckResult(
            check_id="SQ-AC-4",
            name="Code smell count accuracy",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=0.5,
            message="No ground truth provided, skipping",
            evidence={"skipped": True},
        )

    expected = ground_truth.get("expected_smells", {})
    min_val = expected.get("min", 0)
    max_val = expected.get("max", float("inf"))

    results = data.get("results", data)
    actual = get_nested(results, "issues.rollups.by_type.CODE_SMELL", 0)

    passed = in_range(actual, min_val, max_val)
    return CheckResult(
        check_id="SQ-AC-4",
        name="Code smell count accuracy",
        category=CheckCategory.ACCURACY,
        passed=passed,
        score=1.0 if passed else 0.0,
        message=f"Code smell count {actual} {'within' if passed else 'outside'} expected range [{min_val}, {max_val}]",
        evidence={"expected": {"min": min_val, "max": max_val}, "actual": actual},
    )


def check_quality_gate_status(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-AC-5: Check that quality gate status matches expected."""
    if not ground_truth:
        return CheckResult(
            check_id="SQ-AC-5",
            name="Quality gate match",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=0.5,
            message="No ground truth provided, skipping",
            evidence={"skipped": True},
        )

    expected = ground_truth.get("quality_gate_expected")
    if not expected:
        return CheckResult(
            check_id="SQ-AC-5",
            name="Quality gate match",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=0.5,
            message="No expected quality gate status in ground truth",
            evidence={"skipped": True},
        )

    results = data.get("results", data)
    actual = get_nested(results, "quality_gate.status")

    passed = actual == expected
    return CheckResult(
        check_id="SQ-AC-5",
        name="Quality gate match",
        category=CheckCategory.ACCURACY,
        passed=passed,
        score=1.0 if passed else 0.0,
        message=f"Quality gate status '{actual}' {'matches' if passed else 'does not match'} expected '{expected}'",
        evidence={"expected": expected, "actual": actual},
    )


def run_accuracy_checks(data: dict, ground_truth: dict | None) -> list[CheckResult]:
    """Run all accuracy checks and return results."""
    return [
        check_issue_count(data, ground_truth),
        check_bug_count(data, ground_truth),
        check_vulnerability_count(data, ground_truth),
        check_smell_count(data, ground_truth),
        check_quality_gate_status(data, ground_truth),
    ]
