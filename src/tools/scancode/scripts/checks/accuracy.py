"""Accuracy checks for license analysis (LA-1 to LA-10)."""

from . import CheckResult, check_boolean, check_contains, check_equal


def run_accuracy_checks(
    analysis: dict, ground_truth: dict
) -> list[CheckResult]:
    """Run all accuracy checks against ground truth."""
    results = []
    expected = ground_truth.get("expected", {})
    tolerance = ground_truth.get("thresholds", {}).get("count_tolerance", 0)

    # LA-1: Total licenses found count
    expected_count = expected.get("total_licenses", 0)
    actual_count = len(analysis.get("licenses_found", []))
    results.append(
        check_equal(
            "LA-1",
            "Accuracy",
            "Total licenses found",
            expected_count,
            actual_count,
            tolerance,
        )
    )

    # LA-2: Specific licenses detected
    expected_licenses = expected.get("licenses", [])
    actual_licenses = analysis.get("licenses_found", [])
    results.append(
        check_contains(
            "LA-2",
            "Accuracy",
            "Expected licenses detected",
            expected_licenses,
            actual_licenses,
        )
    )

    # LA-3: License file count
    expected_files = expected.get("license_files_found", 0)
    actual_files = analysis.get("license_files_found", 0)
    results.append(
        check_equal(
            "LA-3",
            "Accuracy",
            "License files found",
            expected_files,
            actual_files,
            tolerance,
        )
    )

    # LA-4: Files with licenses count
    expected_with = expected.get("files_with_licenses", 0)
    actual_with = analysis.get("files_with_licenses", 0)
    results.append(
        check_equal(
            "LA-4",
            "Accuracy",
            "Files with licenses",
            expected_with,
            actual_with,
            tolerance,
        )
    )

    # LA-5: Overall risk level
    expected_risk = expected.get("overall_risk", "unknown")
    actual_risk = analysis.get("overall_risk", "unknown")
    results.append(
        check_equal(
            "LA-5",
            "Accuracy",
            "Overall risk level",
            expected_risk,
            actual_risk,
        )
    )

    # LA-6: Has permissive flag
    expected_permissive = expected.get("has_permissive", False)
    actual_permissive = analysis.get("has_permissive", False)
    results.append(
        check_boolean(
            "LA-6",
            "Accuracy",
            "Has permissive license",
            expected_permissive,
            actual_permissive,
        )
    )

    # LA-7: Has copyleft flag
    expected_copyleft = expected.get("has_copyleft", False)
    actual_copyleft = analysis.get("has_copyleft", False)
    results.append(
        check_boolean(
            "LA-7",
            "Accuracy",
            "Has copyleft license",
            expected_copyleft,
            actual_copyleft,
        )
    )

    # LA-8: Has weak-copyleft flag
    expected_weak = expected.get("has_weak_copyleft", False)
    actual_weak = analysis.get("has_weak_copyleft", False)
    results.append(
        check_boolean(
            "LA-8",
            "Accuracy",
            "Has weak-copyleft license",
            expected_weak,
            actual_weak,
        )
    )

    # LA-9: Has unknown flag
    expected_unknown = expected.get("has_unknown", False)
    actual_unknown = analysis.get("has_unknown", False)
    results.append(
        check_boolean(
            "LA-9",
            "Accuracy",
            "Has unknown license",
            expected_unknown,
            actual_unknown,
        )
    )

    # LA-10: License counts match
    expected_counts = expected.get("license_counts", {})
    actual_counts = analysis.get("license_counts", {})
    counts_match = True
    for license_id, count in expected_counts.items():
        actual = actual_counts.get(license_id, 0)
        if abs(count - actual) > tolerance:
            counts_match = False
            break
    results.append(
        CheckResult(
            check_id="LA-10",
            category="Accuracy",
            passed=counts_match,
            message=f"License counts: expected={expected_counts}, actual={actual_counts}",
            expected=expected_counts,
            actual=actual_counts,
        )
    )

    # LA-11: No unexpected licenses detected (false positive check)
    # LA-2 checks expected ⊆ actual, LA-11 checks actual ⊆ expected
    unexpected = set(actual_licenses) - set(expected_licenses)
    no_false_positives = len(unexpected) == 0
    results.append(
        CheckResult(
            check_id="LA-11",
            category="Accuracy",
            passed=no_false_positives,
            message=f"No unexpected licenses: unexpected={list(unexpected) if unexpected else 'none'}",
            expected=expected_licenses,
            actual=actual_licenses,
        )
    )

    # LA-12: Finding paths present and non-empty
    findings = analysis.get("findings", [])
    invalid_paths = [f for f in findings if not f.get("file_path")]
    results.append(
        CheckResult(
            check_id="LA-12",
            category="Accuracy",
            passed=len(invalid_paths) == 0,
            message=f"Finding paths present: {len(invalid_paths)} invalid",
            expected="all findings have file_path",
            actual=f"{len(invalid_paths)} findings missing file_path",
        )
    )

    # LA-13/LA-14: Path matching (only if expected_findings defined)
    expected_findings = expected.get("expected_findings")
    if expected_findings is not None:
        expected_paths = {f["file_path"] for f in expected_findings}
        actual_paths = {f.get("file_path") for f in findings if f.get("file_path")}

        # LA-13: Expected paths detected
        missing = expected_paths - actual_paths
        results.append(
            CheckResult(
                check_id="LA-13",
                category="Accuracy",
                passed=len(missing) == 0,
                message=f"Expected paths detected: missing={list(missing) if missing else 'none'}",
                expected=sorted(expected_paths),
                actual=sorted(actual_paths),
            )
        )

        # LA-14: No unexpected paths
        unexpected_paths = actual_paths - expected_paths
        results.append(
            CheckResult(
                check_id="LA-14",
                category="Accuracy",
                passed=len(unexpected_paths) == 0,
                message=f"No unexpected paths: extra={list(unexpected_paths) if unexpected_paths else 'none'}",
                expected=sorted(expected_paths),
                actual=sorted(actual_paths),
            )
        )

    return results
