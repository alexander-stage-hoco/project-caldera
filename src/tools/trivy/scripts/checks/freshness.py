"""Freshness quality checks for evaluation.

These checks validate the quality and accuracy of package freshness data
when --check-freshness is used during analysis.
"""
from typing import Generator

from . import CheckResult

CATEGORY = "Freshness Quality"


def run_freshness_checks(
    analysis: dict, ground_truth: dict
) -> Generator[CheckResult, None, None]:
    """Run all freshness-related checks.

    Args:
        analysis: Analysis output dictionary
        ground_truth: Ground truth expectations dictionary

    Yields:
        CheckResult for each freshness check
    """
    yield check_freshness_presence(analysis, ground_truth)
    yield check_outdated_count(analysis, ground_truth)
    yield check_version_delta_accuracy(analysis, ground_truth)
    yield check_registry_coverage(analysis, ground_truth)


def check_freshness_presence(analysis: dict, ground_truth: dict) -> CheckResult:
    """Check that freshness data is present when expected.

    FQ01: Validates that freshness checking was performed when ground truth
    expects it, and that the data structure is valid.
    """
    freshness = analysis.get("freshness", {})
    expected = ground_truth.get("freshness_expected", False)

    # Case 1: Freshness expected but not checked
    if expected and not freshness.get("checked", False):
        return CheckResult(
            check_id="FQ01_freshness_presence",
            category=CATEGORY,
            passed=False,
            message="Freshness checking expected but not performed",
            details={"expected": True, "actual_checked": False},
        )

    # Case 2: Freshness was checked
    if freshness.get("checked", False):
        pkg_count = freshness.get("total_packages", 0)
        outdated = freshness.get("outdated_count", 0)
        return CheckResult(
            check_id="FQ01_freshness_presence",
            category=CATEGORY,
            passed=True,
            message=f"Freshness data present for {pkg_count} packages ({outdated} outdated)",
            details={"package_count": pkg_count, "outdated_count": outdated},
        )

    # Case 3: Freshness not expected and not checked - OK
    return CheckResult(
        check_id="FQ01_freshness_presence",
        category=CATEGORY,
        passed=True,
        message="Freshness checking not required for this scenario",
    )


def check_outdated_count(analysis: dict, ground_truth: dict) -> CheckResult:
    """Check outdated count is within expected range.

    FQ02: Validates that the number of outdated packages falls within
    the expected range specified in ground truth.
    """
    freshness = analysis.get("freshness", {})

    # Skip if freshness not checked
    if not freshness.get("checked", False):
        return CheckResult(
            check_id="FQ02_outdated_count",
            category=CATEGORY,
            passed=True,
            message="Skipped - freshness not checked",
        )

    outdated = freshness.get("outdated_count", 0)
    expected = ground_truth.get("expected_outdated_count", {})

    # If no expectations set, just validate it's a reasonable number
    if not expected:
        return CheckResult(
            check_id="FQ02_outdated_count",
            category=CATEGORY,
            passed=True,
            message=f"Outdated count: {outdated} (no specific expectation)",
            details={"actual": outdated},
        )

    min_val = expected.get("min", 0)
    max_val = expected.get("max", float("inf"))

    passed = min_val <= outdated <= max_val
    return CheckResult(
        check_id="FQ02_outdated_count",
        category=CATEGORY,
        passed=passed,
        message=f"Outdated count {outdated} {'within' if passed else 'outside'} expected range [{min_val}, {max_val}]",
        details={"actual": outdated, "expected_min": min_val, "expected_max": max_val},
    )


def check_version_delta_accuracy(analysis: dict, ground_truth: dict) -> CheckResult:
    """Check version delta calculations are reasonable.

    FQ03: Validates internal consistency of version delta calculations.
    For example, if major_versions_behind > 0, is_outdated should be True.
    """
    freshness = analysis.get("freshness", {})

    # Skip if freshness not checked
    if not freshness.get("checked", False):
        return CheckResult(
            check_id="FQ03_version_delta",
            category=CATEGORY,
            passed=True,
            message="Skipped - freshness not checked",
        )

    packages = freshness.get("packages", [])
    issues = []

    for pkg in packages:
        pkg_name = pkg.get("package", "unknown")
        major = pkg.get("major_versions_behind", 0)
        minor = pkg.get("minor_versions_behind", 0)
        patch = pkg.get("patch_versions_behind", 0)
        is_outdated = pkg.get("is_outdated", False)

        # Sanity check 1: if any version delta > 0, should be outdated
        if (major > 0 or minor > 0 or patch > 0) and not is_outdated:
            issues.append(f"{pkg_name}: has version delta but is_outdated=False")

        # Sanity check 2: if major > 0, minor should be 0 (we only count one level)
        if major > 0 and minor > 0:
            issues.append(f"{pkg_name}: major={major} and minor={minor} (should be 0)")

        # Sanity check 3: version deltas should be non-negative
        if major < 0 or minor < 0 or patch < 0:
            issues.append(f"{pkg_name}: negative version delta detected")

    passed = len(issues) == 0
    return CheckResult(
        check_id="FQ03_version_delta",
        category=CATEGORY,
        passed=passed,
        message=f"Version delta calculations {'are consistent' if passed else 'have inconsistencies'}",
        details={"issues": issues, "packages_checked": len(packages)} if issues else {"packages_checked": len(packages)},
    )


def check_registry_coverage(analysis: dict, ground_truth: dict) -> CheckResult:
    """Check that supported package types have freshness data.

    FQ04: Validates that packages from supported registries (pip, npm, gomod)
    have freshness data when they exist in the analysis.
    """
    freshness = analysis.get("freshness", {})

    # Skip if freshness not checked
    if not freshness.get("checked", False):
        return CheckResult(
            check_id="FQ04_registry_coverage",
            category=CATEGORY,
            passed=True,
            message="Skipped - freshness not checked",
        )

    packages = freshness.get("packages", [])
    pkg_types = set(p.get("package_type", "") for p in packages)

    # Supported registries
    supported = {"pip", "npm", "gomod", "poetry", "yarn", "nodejs"}
    covered = pkg_types & supported

    # Also check SBOM to see what package types exist in the repo
    sbom = analysis.get("sbom", {})
    targets = analysis.get("targets", [])
    repo_pkg_types = set(t.get("type", "") for t in targets)

    # Find supported types in repo that should have freshness data
    expected_coverage = repo_pkg_types & supported
    missing_coverage = expected_coverage - covered

    if missing_coverage:
        return CheckResult(
            check_id="FQ04_registry_coverage",
            category=CATEGORY,
            passed=False,
            message=f"Missing freshness data for package types: {', '.join(missing_coverage)}",
            details={
                "covered_types": list(covered),
                "missing_types": list(missing_coverage),
            },
        )

    return CheckResult(
        check_id="FQ04_registry_coverage",
        category=CATEGORY,
        passed=True,
        message=f"Registry coverage: {', '.join(covered) if covered else 'none (no supported types in repo)'}",
        details={"covered_types": list(covered)},
    )
