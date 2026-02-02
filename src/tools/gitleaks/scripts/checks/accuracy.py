"""Accuracy checks for secret detection (SA-1 to SA-10)."""

from __future__ import annotations

from . import CheckResult, check_equal, check_contains, check_at_least


def run_accuracy_checks(analysis: dict, ground_truth: dict) -> list[CheckResult]:
    """Run all accuracy checks."""
    check_results: list[CheckResult] = []
    expected = ground_truth.get("expected", {})
    # Handle both old format (flat) and new format (with results wrapper)
    results = analysis.get("results", analysis)

    # SA-1: Total secret count matches expected
    check_results.append(
        check_equal(
            "SA-1",
            "Accuracy",
            "Total secrets",
            expected.get("total_secrets", 0),
            results.get("total_secrets", 0),
        )
    )

    # SA-2: Unique secret count matches expected
    check_results.append(
        check_equal(
            "SA-2",
            "Accuracy",
            "Unique secrets",
            expected.get("unique_secrets", 0),
            results.get("unique_secrets", 0),
        )
    )

    # SA-3: Secrets in HEAD matches expected
    check_results.append(
        check_equal(
            "SA-3",
            "Accuracy",
            "Secrets in HEAD",
            expected.get("secrets_in_head", 0),
            results.get("secrets_in_head", 0),
        )
    )

    # SA-4: Secrets in history matches expected
    check_results.append(
        check_equal(
            "SA-4",
            "Accuracy",
            "Secrets in history",
            expected.get("secrets_in_history", 0),
            results.get("secrets_in_history", 0),
        )
    )

    # SA-5: Files with secrets count matches expected
    check_results.append(
        check_equal(
            "SA-5",
            "Accuracy",
            "Files with secrets",
            expected.get("files_with_secrets", 0),
            results.get("files_with_secrets", 0),
        )
    )

    # SA-6: Commits with secrets count matches expected
    check_results.append(
        check_equal(
            "SA-6",
            "Accuracy",
            "Commits with secrets",
            expected.get("commits_with_secrets", 0),
            results.get("commits_with_secrets", 0),
        )
    )

    # SA-7: Expected rule IDs detected
    expected_rules = expected.get("rule_ids", [])
    actual_rules = list(results.get("secrets_by_rule", {}).keys())
    check_results.append(
        check_contains(
            "SA-7",
            "Accuracy",
            "Expected rule IDs",
            expected_rules,
            actual_rules,
        )
    )

    # SA-8: Expected files with secrets detected
    expected_files = expected.get("files_with_secrets_list", [])
    actual_files = list(results.get("files", {}).keys())
    if expected_files:
        check_results.append(
            check_contains(
                "SA-8",
                "Accuracy",
                "Expected files with secrets",
                expected_files,
                actual_files,
            )
        )
    else:
        # Skip if no files expected
        check_results.append(
            CheckResult(
                check_id="SA-8",
                category="Accuracy",
                passed=True,
                message="No specific files expected",
                expected=[],
                actual=actual_files,
            )
        )

    # SA-9: Rule counts match expected
    expected_by_rule = expected.get("secrets_by_rule", {})
    actual_by_rule = results.get("secrets_by_rule", {})
    rule_counts_match = True
    rule_count_details = []

    for rule_id, exp_count in expected_by_rule.items():
        act_count = actual_by_rule.get(rule_id, 0)
        if exp_count != act_count:
            rule_counts_match = False
            rule_count_details.append(f"{rule_id}: expected {exp_count}, got {act_count}")

    check_results.append(
        CheckResult(
            check_id="SA-9",
            category="Accuracy",
            passed=rule_counts_match,
            message="Rule counts match" if rule_counts_match else f"Rule count mismatch: {rule_count_details}",
            expected=expected_by_rule,
            actual=actual_by_rule,
        )
    )

    # SA-10: Expected line numbers for findings
    expected_findings = expected.get("findings", [])
    if expected_findings:
        actual_findings = results.get("findings", [])
        fingerprints_expected = set()
        for ef in expected_findings:
            # Build expected fingerprint pattern (file:rule:line)
            key = f"{ef.get('file_path')}:{ef.get('rule_id')}:{ef.get('line_number')}"
            fingerprints_expected.add(key)

        fingerprints_actual = set()
        for af in actual_findings:
            key = f"{af.get('file_path')}:{af.get('rule_id')}:{af.get('line_number')}"
            fingerprints_actual.add(key)

        missing = fingerprints_expected - fingerprints_actual
        check_results.append(
            CheckResult(
                check_id="SA-10",
                category="Accuracy",
                passed=len(missing) == 0,
                message="All expected findings found" if len(missing) == 0 else f"Missing findings: {missing}",
                expected=list(fingerprints_expected),
                actual=list(fingerprints_actual),
            )
        )
    else:
        check_results.append(
            CheckResult(
                check_id="SA-10",
                category="Accuracy",
                passed=True,
                message="No specific findings expected",
                expected=[],
                actual=[],
            )
        )

    # SA-11: Severity assignments match expected values
    if expected_findings:
        actual_findings = results.get("findings", [])

        # Build lookup for actual severities by file:rule:line
        actual_severity_map = {}
        for af in actual_findings:
            key = f"{af.get('file_path')}:{af.get('rule_id')}:{af.get('line_number')}"
            actual_severity_map[key] = af.get("severity", "UNKNOWN")

        severity_mismatches = []
        for ef in expected_findings:
            if "expected_severity" not in ef:
                continue  # Skip if no expected severity specified
            key = f"{ef.get('file_path')}:{ef.get('rule_id')}:{ef.get('line_number')}"
            expected_sev = ef.get("expected_severity")
            actual_sev = actual_severity_map.get(key, "NOT_FOUND")

            if expected_sev != actual_sev:
                severity_mismatches.append(f"{key}: expected {expected_sev}, got {actual_sev}")

        check_results.append(
            CheckResult(
                check_id="SA-11",
                category="Accuracy",
                passed=len(severity_mismatches) == 0,
                message="All severity assignments match" if len(severity_mismatches) == 0 else f"Severity mismatches: {severity_mismatches}",
                expected=[ef.get("expected_severity") for ef in expected_findings if "expected_severity" in ef],
                actual=[actual_severity_map.get(f"{ef.get('file_path')}:{ef.get('rule_id')}:{ef.get('line_number')}", "NOT_FOUND") for ef in expected_findings if "expected_severity" in ef],
            )
        )
    else:
        check_results.append(
            CheckResult(
                check_id="SA-11",
                category="Accuracy",
                passed=True,
                message="No severity expectations specified",
                expected=[],
                actual=[],
            )
        )

    return check_results
