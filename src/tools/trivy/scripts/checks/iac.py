"""IaC misconfiguration detection checks for Trivy analysis."""

from typing import Any, Generator

from . import CheckResult

CATEGORY = "IaC Detection"


def run_iac_checks(
    analysis: dict[str, Any], ground_truth: dict[str, Any]
) -> Generator[CheckResult, None, None]:
    """Run all IaC misconfiguration checks."""
    # Only run checks if IaC is expected in ground truth
    if not ground_truth.get("iac_expected", False):
        return

    yield check_iac_total_count(analysis, ground_truth)
    yield check_iac_severity_distribution(analysis, ground_truth)
    yield check_iac_type_coverage(analysis, ground_truth)
    yield check_required_iac_ids(analysis, ground_truth)
    yield check_actionability_rate(analysis, ground_truth)


def check_iac_total_count(
    analysis: dict[str, Any], ground_truth: dict[str, Any]
) -> CheckResult:
    """Check that total IaC misconfigurations are within expected range."""
    iac_data = analysis.get("iac_misconfigurations", {})
    actual_count = iac_data.get("total_count", 0)

    expected_iac = ground_truth.get("expected_iac", {})
    expected_total = expected_iac.get("total", {})

    if not expected_total:
        return CheckResult(
            check_id="iac_total_count",
            category=CATEGORY,
            passed=True,
            message="No expected_iac.total specified in ground truth",
        )

    min_val = expected_total.get("min", 0)
    max_val = expected_total.get("max", float("inf"))

    if not (min_val <= actual_count <= max_val):
        return CheckResult(
            check_id="iac_total_count",
            category=CATEGORY,
            passed=False,
            message=f"IaC count {actual_count} not in range [{min_val}, {max_val}]",
            details={"actual": actual_count, "expected_range": [min_val, max_val]},
        )

    return CheckResult(
        check_id="iac_total_count",
        category=CATEGORY,
        passed=True,
        message=f"IaC count {actual_count} within expected range [{min_val}, {max_val}]",
    )


def check_iac_severity_distribution(
    analysis: dict[str, Any], ground_truth: dict[str, Any]
) -> CheckResult:
    """Check that IaC severity counts match expected ranges."""
    iac_data = analysis.get("iac_misconfigurations", {})
    expected_iac = ground_truth.get("expected_iac", {})

    # Check critical count
    expected_critical = expected_iac.get("critical")
    actual_critical = iac_data.get("critical_count", 0)

    if expected_critical is not None:
        if isinstance(expected_critical, dict):
            min_val = expected_critical.get("min", 0)
            max_val = expected_critical.get("max", float("inf"))
            if not (min_val <= actual_critical <= max_val):
                return CheckResult(
                    check_id="iac_severity_distribution",
                    category=CATEGORY,
                    passed=False,
                    message=f"IaC critical count {actual_critical} not in range [{min_val}, {max_val}]",
                )

    # Check high count
    expected_high = expected_iac.get("high")
    actual_high = iac_data.get("high_count", 0)

    if expected_high is not None:
        if isinstance(expected_high, dict):
            min_val = expected_high.get("min", 0)
            max_val = expected_high.get("max", float("inf"))
            if not (min_val <= actual_high <= max_val):
                return CheckResult(
                    check_id="iac_severity_distribution",
                    category=CATEGORY,
                    passed=False,
                    message=f"IaC high count {actual_high} not in range [{min_val}, {max_val}]",
                )

    return CheckResult(
        check_id="iac_severity_distribution",
        category=CATEGORY,
        passed=True,
        message=f"IaC severity distribution matches (C={actual_critical}, H={actual_high})",
    )


def check_iac_type_coverage(
    analysis: dict[str, Any], ground_truth: dict[str, Any]
) -> CheckResult:
    """Check that required IaC types (dockerfile, terraform, etc.) are detected."""
    required_types = ground_truth.get("required_iac_types", [])

    if not required_types:
        return CheckResult(
            check_id="iac_type_coverage",
            category=CATEGORY,
            passed=True,
            message="No required_iac_types specified in ground truth",
        )

    iac_data = analysis.get("iac_misconfigurations", {})
    misconfigs = iac_data.get("misconfigurations", [])

    # Extract unique target types from misconfigurations
    found_types = set()
    for m in misconfigs:
        target = m.get("target", "")
        target_lower = target.lower()

        # Determine type from target filename
        if "dockerfile" in target_lower or target_lower == "dockerfile":
            found_types.add("dockerfile")
        elif target_lower.endswith(".tf"):
            found_types.add("terraform")
        elif target_lower.endswith((".yaml", ".yml")):
            # Could be kubernetes, cloudformation, or other
            found_types.add("yaml")
            found_types.add("kubernetes")  # Also mark as kubernetes for yaml files
        elif target_lower.endswith(".json"):
            found_types.add("json")
            found_types.add("cloudformation")  # JSON could be CloudFormation

    # Check for required types
    missing_types = []
    for req_type in required_types:
        req_lower = req_type.lower()
        if req_lower not in found_types:
            missing_types.append(req_type)

    if missing_types:
        return CheckResult(
            check_id="iac_type_coverage",
            category=CATEGORY,
            passed=False,
            message=f"Missing IaC types: {missing_types}",
            details={"required": required_types, "found": list(found_types)},
        )

    return CheckResult(
        check_id="iac_type_coverage",
        category=CATEGORY,
        passed=True,
        message=f"All required IaC types detected: {required_types}",
    )


def check_required_iac_ids(
    analysis: dict[str, Any], ground_truth: dict[str, Any]
) -> CheckResult:
    """Check that required IaC issue IDs are detected."""
    required_ids = ground_truth.get("required_iac_ids", [])

    if not required_ids:
        return CheckResult(
            check_id="required_iac_ids",
            category=CATEGORY,
            passed=True,
            message="No required_iac_ids specified in ground truth",
        )

    iac_data = analysis.get("iac_misconfigurations", {})
    misconfigs = iac_data.get("misconfigurations", [])

    # Extract found IDs
    found_ids = {m.get("id", "") for m in misconfigs}

    # Check for required IDs
    missing_ids = [rid for rid in required_ids if rid not in found_ids]

    if missing_ids:
        return CheckResult(
            check_id="required_iac_ids",
            category=CATEGORY,
            passed=False,
            message=f"Missing required IaC issues: {missing_ids}",
            details={"required": required_ids, "found": list(found_ids)},
        )

    return CheckResult(
        check_id="required_iac_ids",
        category=CATEGORY,
        passed=True,
        message=f"All {len(required_ids)} required IaC issues detected",
    )


def check_actionability_rate(
    analysis: dict[str, Any], ground_truth: dict[str, Any]
) -> CheckResult:
    """Check that IaC findings have actionable resolution text."""
    iac_data = analysis.get("iac_misconfigurations", {})
    misconfigs = iac_data.get("misconfigurations", [])

    if not misconfigs:
        return CheckResult(
            check_id="iac_actionability",
            category=CATEGORY,
            passed=True,
            message="No IaC misconfigurations to check for actionability",
        )

    # Count misconfigs with meaningful resolution text
    actionable_count = 0
    for m in misconfigs:
        resolution = m.get("resolution", "")
        # Consider actionable if resolution is non-empty and has at least 10 chars
        if resolution and len(resolution.strip()) >= 10:
            actionable_count += 1

    actionability_rate = (actionable_count / len(misconfigs)) * 100

    # Require at least 80% actionability
    if actionability_rate < 80:
        return CheckResult(
            check_id="iac_actionability",
            category=CATEGORY,
            passed=False,
            message=f"IaC actionability rate {actionability_rate:.1f}% below 80% threshold",
            details={
                "total": len(misconfigs),
                "actionable": actionable_count,
                "rate": actionability_rate,
            },
        )

    return CheckResult(
        check_id="iac_actionability",
        category=CATEGORY,
        passed=True,
        message=f"IaC actionability rate {actionability_rate:.1f}% ({actionable_count}/{len(misconfigs)})",
    )
