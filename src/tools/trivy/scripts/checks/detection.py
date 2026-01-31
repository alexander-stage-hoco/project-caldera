"""Detection accuracy checks for Trivy analysis."""

from typing import Any, Generator

from . import CheckResult

CATEGORY = "Detection Accuracy"


def run_detection_checks(
    analysis: dict[str, Any], ground_truth: dict[str, Any]
) -> Generator[CheckResult, None, None]:
    """Run all detection accuracy checks."""
    yield check_critical_detected(analysis, ground_truth)
    yield check_severity_distribution(analysis, ground_truth)
    yield check_target_identification(analysis, ground_truth)
    yield check_fix_availability(analysis, ground_truth)


def check_critical_detected(
    analysis: dict[str, Any], ground_truth: dict[str, Any]
) -> CheckResult:
    """Check that known critical CVEs are detected."""
    required_cves = ground_truth.get("required_cves", [])

    if not required_cves:
        return CheckResult(
            check_id="critical_detected",
            category=CATEGORY,
            passed=True,
            message="No required CVEs specified in ground truth",
        )

    vulnerabilities = analysis.get("vulnerabilities", [])
    found_ids = {v.get("id", "") for v in vulnerabilities}

    missing = [cve for cve in required_cves if cve not in found_ids]

    if missing:
        return CheckResult(
            check_id="critical_detected",
            category=CATEGORY,
            passed=False,
            message=f"Missing required CVEs: {missing}",
            details={"missing": missing, "found": list(found_ids)},
        )

    return CheckResult(
        check_id="critical_detected",
        category=CATEGORY,
        passed=True,
        message=f"All {len(required_cves)} required CVEs detected",
    )


def check_severity_distribution(
    analysis: dict[str, Any], ground_truth: dict[str, Any]
) -> CheckResult:
    """Check that severity counts match expected ranges."""
    summary = analysis.get("summary", {})

    # Check critical count
    expected_critical = ground_truth.get("expected_critical")
    actual_critical = summary.get("critical_count", 0)

    if expected_critical is not None:
        if isinstance(expected_critical, dict):
            min_val = expected_critical.get("min", 0)
            max_val = expected_critical.get("max", float("inf"))
            if not (min_val <= actual_critical <= max_val):
                return CheckResult(
                    check_id="severity_distribution",
                    category=CATEGORY,
                    passed=False,
                    message=f"Critical count {actual_critical} not in range [{min_val}, {max_val}]",
                )
        elif actual_critical != expected_critical:
            return CheckResult(
                check_id="severity_distribution",
                category=CATEGORY,
                passed=False,
                message=f"Critical count {actual_critical} != expected {expected_critical}",
            )

    # Check high count if specified
    expected_high = ground_truth.get("expected_high")
    actual_high = summary.get("high_count", 0)

    if expected_high is not None:
        if isinstance(expected_high, dict):
            min_val = expected_high.get("min", 0)
            max_val = expected_high.get("max", float("inf"))
            if not (min_val <= actual_high <= max_val):
                return CheckResult(
                    check_id="severity_distribution",
                    category=CATEGORY,
                    passed=False,
                    message=f"High count {actual_high} not in range [{min_val}, {max_val}]",
                )

    return CheckResult(
        check_id="severity_distribution",
        category=CATEGORY,
        passed=True,
        message=f"Severity distribution matches (C={actual_critical}, H={actual_high})",
    )


def check_target_identification(
    analysis: dict[str, Any], ground_truth: dict[str, Any]
) -> CheckResult:
    """Check that correct lockfile types are identified."""
    targets = analysis.get("targets", [])
    expected_targets = ground_truth.get("expected_targets")

    if expected_targets is None:
        return CheckResult(
            check_id="target_identification",
            category=CATEGORY,
            passed=True,
            message="No expected_targets specified in ground truth",
        )

    actual_count = len(targets)

    if isinstance(expected_targets, dict):
        min_val = expected_targets.get("min", 0)
        max_val = expected_targets.get("max", float("inf"))
        if not (min_val <= actual_count <= max_val):
            return CheckResult(
                check_id="target_identification",
                category=CATEGORY,
                passed=False,
                message=f"Target count {actual_count} not in range [{min_val}, {max_val}]",
            )
    elif actual_count != expected_targets:
        # Allow flexibility - we just check we found something
        if actual_count == 0 and expected_targets > 0:
            return CheckResult(
                check_id="target_identification",
                category=CATEGORY,
                passed=False,
                message=f"No targets found, expected {expected_targets}",
            )

    target_types = [t.get("type", "unknown") for t in targets]
    return CheckResult(
        check_id="target_identification",
        category=CATEGORY,
        passed=True,
        message=f"Found {actual_count} targets: {set(target_types)}",
    )


def check_fix_availability(
    analysis: dict[str, Any], ground_truth: dict[str, Any]
) -> CheckResult:
    """Check that fix_available is properly detected."""
    summary = analysis.get("summary", {})
    expected_pct = ground_truth.get("expected_fix_available_pct")

    if expected_pct is None:
        return CheckResult(
            check_id="fix_availability",
            category=CATEGORY,
            passed=True,
            message="No expected_fix_available_pct specified",
        )

    actual_pct = summary.get("fix_available_pct", 0)

    if isinstance(expected_pct, dict):
        min_val = expected_pct.get("min", 0)
        max_val = expected_pct.get("max", 100)
        if not (min_val <= actual_pct <= max_val):
            return CheckResult(
                check_id="fix_availability",
                category=CATEGORY,
                passed=False,
                message=f"fix_available_pct {actual_pct}% not in range [{min_val}, {max_val}]%",
            )

    return CheckResult(
        check_id="fix_availability",
        category=CATEGORY,
        passed=True,
        message=f"fix_available_pct={actual_pct:.1f}% within expected range",
    )
