"""Rollup validation checks for gitleaks analysis (RV-1 to RV-4).

Validates directory rollup invariants:
- Recursive counts >= Direct counts
- Non-negative counts
- Root recursive equals total secrets
"""

from __future__ import annotations

from . import CheckResult


def run_rollup_checks(analysis: dict, ground_truth: dict) -> list[CheckResult]:
    """Run all rollup validation checks.

    Validates directory rollup invariants as specified in EVAL_STRATEGY.md:
    - RV-1: Recursive >= Direct for secret counts
    - RV-2: Recursive >= Direct for file counts
    - RV-3: All counts are non-negative
    - RV-4: Root recursive equals total secrets

    Args:
        analysis: The normalized analysis output dictionary.
        ground_truth: The ground truth data for the scenario (unused but kept for consistency).

    Returns:
        List of CheckResult objects for the rollup dimension.
    """
    check_results: list[CheckResult] = []
    # Handle both old format (flat) and new format (with results wrapper)
    results = analysis.get("results", analysis)

    directories = results.get("directories", {})
    total_secrets = results.get("total_secrets", 0)

    if not directories:
        # No directories to validate - pass with note
        check_results.append(
            CheckResult(
                check_id="RV-1",
                category="Rollup Validation",
                passed=True,
                message="N/A - no directory metrics present",
                expected="N/A",
                actual="N/A",
            )
        )
        check_results.append(
            CheckResult(
                check_id="RV-2",
                category="Rollup Validation",
                passed=True,
                message="N/A - no directory metrics present",
                expected="N/A",
                actual="N/A",
            )
        )
        check_results.append(
            CheckResult(
                check_id="RV-3",
                category="Rollup Validation",
                passed=True,
                message="N/A - no directory metrics present",
                expected="N/A",
                actual="N/A",
            )
        )
        check_results.append(
            CheckResult(
                check_id="RV-4",
                category="Rollup Validation",
                passed=True,
                message="N/A - no directory metrics present",
                expected="N/A",
                actual="N/A",
            )
        )
        return check_results

    # RV-1: Recursive >= Direct for secret counts
    rv1_failures = []
    for path, metrics in directories.items():
        direct = metrics.get("direct_secret_count", 0)
        recursive = metrics.get("recursive_secret_count", 0)
        if recursive < direct:
            rv1_failures.append(f"{path}: recursive ({recursive}) < direct ({direct})")

    check_results.append(
        CheckResult(
            check_id="RV-1",
            category="Rollup Validation",
            passed=len(rv1_failures) == 0,
            message="Recursive >= Direct for all directories" if not rv1_failures else f"Invariant violations: {rv1_failures[:3]}",
            expected="recursive_secret_count >= direct_secret_count",
            actual="all valid" if not rv1_failures else rv1_failures,
        )
    )

    # RV-2: Recursive >= Direct for file counts
    rv2_failures = []
    for path, metrics in directories.items():
        direct_files = metrics.get("direct_file_count", 0)
        recursive_files = metrics.get("recursive_file_count", 0)
        if recursive_files < direct_files:
            rv2_failures.append(f"{path}: recursive_files ({recursive_files}) < direct_files ({direct_files})")

    check_results.append(
        CheckResult(
            check_id="RV-2",
            category="Rollup Validation",
            passed=len(rv2_failures) == 0,
            message="Recursive >= Direct for file counts" if not rv2_failures else f"Invariant violations: {rv2_failures[:3]}",
            expected="recursive_file_count >= direct_file_count",
            actual="all valid" if not rv2_failures else rv2_failures,
        )
    )

    # RV-3: All counts are non-negative
    rv3_failures = []
    count_fields = ["direct_secret_count", "recursive_secret_count", "direct_file_count", "recursive_file_count"]
    for path, metrics in directories.items():
        for field in count_fields:
            value = metrics.get(field, 0)
            if value < 0:
                rv3_failures.append(f"{path}.{field} = {value}")

    check_results.append(
        CheckResult(
            check_id="RV-3",
            category="Rollup Validation",
            passed=len(rv3_failures) == 0,
            message="All counts are non-negative" if not rv3_failures else f"Negative counts: {rv3_failures[:3]}",
            expected="all counts >= 0",
            actual="all valid" if not rv3_failures else rv3_failures,
        )
    )

    # RV-4: Root recursive equals total secrets
    # Root directory is typically "." or the first path in the hierarchy
    root_metrics = directories.get(".", {})
    if not root_metrics:
        # Try to find root by shortest path
        paths = sorted(directories.keys(), key=len)
        if paths:
            root_metrics = directories.get(paths[0], {})

    root_recursive = root_metrics.get("recursive_secret_count", 0)
    rv4_passed = root_recursive == total_secrets

    check_results.append(
        CheckResult(
            check_id="RV-4",
            category="Rollup Validation",
            passed=rv4_passed,
            message=f"Root recursive ({root_recursive}) == total_secrets ({total_secrets})" if rv4_passed else f"Mismatch: root recursive ({root_recursive}) != total_secrets ({total_secrets})",
            expected=f"root.recursive_secret_count == {total_secrets}",
            actual=root_recursive,
        )
    )

    return check_results
