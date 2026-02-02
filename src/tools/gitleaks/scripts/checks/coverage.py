"""Coverage checks for secret detection (SC-1 to SC-8)."""

from __future__ import annotations

from . import CheckResult, check_at_least, check_boolean


def run_coverage_checks(analysis: dict, ground_truth: dict) -> list[CheckResult]:
    """Run all coverage checks."""
    check_results: list[CheckResult] = []
    expected = ground_truth.get("expected", {})
    # Thresholds can be at top level or inside expected (per ground truth schema)
    thresholds = expected.get("thresholds", {})
    if not thresholds:
        # Fallback to top-level thresholds for backwards compatibility
        thresholds = ground_truth.get("thresholds", {})
    # Handle both old format (flat) and new format (with results wrapper)
    results = analysis.get("results", analysis)

    # SC-1: Schema version present
    check_results.append(
        CheckResult(
            check_id="SC-1",
            category="Coverage",
            passed=results.get("schema_version") is not None,
            message="Schema version present" if results.get("schema_version") else "Schema version missing",
            expected="non-null",
            actual=results.get("schema_version"),
        )
    )

    # SC-2: Tool version present
    check_results.append(
        CheckResult(
            check_id="SC-2",
            category="Coverage",
            passed=results.get("tool_version") is not None and len(results.get("tool_version", "")) > 0,
            message="Tool version present" if results.get("tool_version") else "Tool version missing",
            expected="non-empty string",
            actual=results.get("tool_version"),
        )
    )

    # SC-3: Timestamp present
    check_results.append(
        CheckResult(
            check_id="SC-3",
            category="Coverage",
            passed=results.get("timestamp") is not None,
            message="Timestamp present" if results.get("timestamp") else "Timestamp missing",
            expected="non-null",
            actual=results.get("timestamp"),
        )
    )

    # SC-4: Summary metrics present
    summary_fields = ["total_secrets", "unique_secrets", "secrets_in_head", "secrets_in_history", "files_with_secrets", "commits_with_secrets"]
    missing_fields = [f for f in summary_fields if f not in results]
    check_results.append(
        CheckResult(
            check_id="SC-4",
            category="Coverage",
            passed=len(missing_fields) == 0,
            message="All summary metrics present" if len(missing_fields) == 0 else f"Missing fields: {missing_fields}",
            expected=summary_fields,
            actual=[f for f in summary_fields if f in results],
        )
    )

    # SC-5: Findings list present
    check_results.append(
        CheckResult(
            check_id="SC-5",
            category="Coverage",
            passed="findings" in results,
            message="Findings list present" if "findings" in results else "Findings list missing",
            expected="findings list",
            actual="present" if "findings" in results else "missing",
        )
    )

    # SC-6: Files summary present
    check_results.append(
        CheckResult(
            check_id="SC-6",
            category="Coverage",
            passed="files" in results,
            message="Files summary present" if "files" in results else "Files summary missing",
            expected="files dict",
            actual="present" if "files" in results else "missing",
        )
    )

    # SC-7: Directory metrics present
    check_results.append(
        CheckResult(
            check_id="SC-7",
            category="Coverage",
            passed="directories" in results,
            message="Directory metrics present" if "directories" in results else "Directory metrics missing",
            expected="directories dict",
            actual="present" if "directories" in results else "missing",
        )
    )

    # SC-8: All findings have required fields
    findings = results.get("findings", [])
    required_fields = ["file_path", "line_number", "rule_id", "secret_type", "commit_hash", "fingerprint"]
    all_valid = True
    invalid_findings = []

    for i, finding in enumerate(findings):
        missing = [f for f in required_fields if f not in finding or finding[f] is None]
        if missing:
            all_valid = False
            invalid_findings.append(f"Finding {i}: missing {missing}")

    check_results.append(
        CheckResult(
            check_id="SC-8",
            category="Coverage",
            passed=all_valid,
            message="All findings have required fields" if all_valid else f"Invalid findings: {invalid_findings[:3]}...",
            expected=required_fields,
            actual="all valid" if all_valid else invalid_findings,
        )
    )

    return check_results
