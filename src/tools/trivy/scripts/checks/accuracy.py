"""Count accuracy checks for Trivy analysis."""

from typing import Any, Generator

from . import CheckResult

CATEGORY = "Count Accuracy"


def run_accuracy_checks(
    analysis: dict[str, Any], ground_truth: dict[str, Any]
) -> Generator[CheckResult, None, None]:
    """Run all count accuracy checks."""
    yield check_count_accuracy(analysis, ground_truth)
    yield check_severity_accuracy(analysis, ground_truth)
    yield check_false_positive_rate(analysis, ground_truth)
    yield check_package_accuracy(analysis, ground_truth)


def check_count_accuracy(
    analysis: dict[str, Any], ground_truth: dict[str, Any]
) -> CheckResult:
    """Check that total vulnerability count is within expected range."""
    summary = analysis.get("summary", {})
    expected = ground_truth.get("expected_vulnerabilities")

    if expected is None:
        return CheckResult(
            check_id="count_accuracy",
            category=CATEGORY,
            passed=True,
            message="No expected_vulnerabilities specified",
        )

    actual = summary.get("total_vulnerabilities", 0)

    if isinstance(expected, dict):
        min_val = expected.get("min", 0)
        max_val = expected.get("max", float("inf"))
        if not (min_val <= actual <= max_val):
            return CheckResult(
                check_id="count_accuracy",
                category=CATEGORY,
                passed=False,
                message=f"Count {actual} not in expected range [{min_val}, {max_val}]",
            )
    elif actual != expected:
        return CheckResult(
            check_id="count_accuracy",
            category=CATEGORY,
            passed=False,
            message=f"Count {actual} != expected {expected}",
        )

    return CheckResult(
        check_id="count_accuracy",
        category=CATEGORY,
        passed=True,
        message=f"Vulnerability count {actual} within expected range",
    )


def check_severity_accuracy(
    analysis: dict[str, Any], ground_truth: dict[str, Any]
) -> CheckResult:
    """Check that per-severity counts match ground truth."""
    summary = analysis.get("summary", {})

    severity_checks = [
        ("expected_critical", "critical_count"),
        ("expected_high", "high_count"),
        ("expected_medium", "medium_count"),
        ("expected_low", "low_count"),
    ]

    errors = []
    checked = 0

    for gt_key, summary_key in severity_checks:
        expected = ground_truth.get(gt_key)
        if expected is None:
            continue

        checked += 1
        actual = summary.get(summary_key, 0)

        if isinstance(expected, dict):
            min_val = expected.get("min", 0)
            max_val = expected.get("max", float("inf"))
            if not (min_val <= actual <= max_val):
                errors.append(f"{summary_key}={actual} not in [{min_val}, {max_val}]")
        elif actual != expected:
            errors.append(f"{summary_key}={actual} != expected {expected}")

    if errors:
        return CheckResult(
            check_id="severity_accuracy",
            category=CATEGORY,
            passed=False,
            message=f"Severity mismatches: {errors}",
        )

    if checked == 0:
        return CheckResult(
            check_id="severity_accuracy",
            category=CATEGORY,
            passed=True,
            message="No severity expectations specified in ground truth",
        )

    return CheckResult(
        check_id="severity_accuracy",
        category=CATEGORY,
        passed=True,
        message=f"All {checked} severity counts within expected ranges",
    )


def check_false_positive_rate(
    analysis: dict[str, Any], ground_truth: dict[str, Any]
) -> CheckResult:
    """Check that we're not detecting non-existent vulnerabilities."""
    expected_vulns = ground_truth.get("expected_vulnerabilities")
    summary = analysis.get("summary", {})
    actual = summary.get("total_vulnerabilities", 0)

    # If expected is 0, we should find 0
    if isinstance(expected_vulns, dict):
        if expected_vulns.get("max") == 0 and actual > 0:
            return CheckResult(
                check_id="false_positive_rate",
                category=CATEGORY,
                passed=False,
                message=f"Expected 0 vulnerabilities but found {actual}",
            )
    elif expected_vulns == 0 and actual > 0:
        return CheckResult(
            check_id="false_positive_rate",
            category=CATEGORY,
            passed=False,
            message=f"Expected 0 vulnerabilities but found {actual}",
        )

    # Check for obviously wrong packages
    forbidden_packages = ground_truth.get("forbidden_packages", [])
    if forbidden_packages:
        vulnerabilities = analysis.get("vulnerabilities", [])
        found_forbidden = [
            v.get("package")
            for v in vulnerabilities
            if v.get("package") in forbidden_packages
        ]
        if found_forbidden:
            return CheckResult(
                check_id="false_positive_rate",
                category=CATEGORY,
                passed=False,
                message=f"Found forbidden packages: {found_forbidden}",
            )

    return CheckResult(
        check_id="false_positive_rate",
        category=CATEGORY,
        passed=True,
        message="No false positives detected",
    )


def check_package_accuracy(
    analysis: dict[str, Any], ground_truth: dict[str, Any]
) -> CheckResult:
    """Check that correct packages are identified as vulnerable."""
    required_packages = ground_truth.get("required_packages", [])

    if not required_packages:
        return CheckResult(
            check_id="package_accuracy",
            category=CATEGORY,
            passed=True,
            message="No required_packages specified in ground truth",
        )

    vulnerabilities = analysis.get("vulnerabilities", [])
    found_packages = {v.get("package", "") for v in vulnerabilities}

    missing = [pkg for pkg in required_packages if pkg not in found_packages]

    if missing:
        return CheckResult(
            check_id="package_accuracy",
            category=CATEGORY,
            passed=False,
            message=f"Missing required packages: {missing}",
        )

    return CheckResult(
        check_id="package_accuracy",
        category=CATEGORY,
        passed=True,
        message=f"All {len(required_packages)} required packages detected",
    )
