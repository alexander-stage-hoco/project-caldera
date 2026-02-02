"""Edge case checks for gitleaks analysis (EC-1 to EC-4).

Validates handling of edge cases:
- Empty repositories
- Unicode file paths
- Large files
- Binary files
"""

from __future__ import annotations

from . import CheckResult


def run_edge_case_checks(analysis: dict, ground_truth: dict) -> list[CheckResult]:
    """Run all edge case checks.

    Args:
        analysis: The normalized analysis output dictionary.
        ground_truth: The ground truth data for the scenario.

    Returns:
        List of CheckResult objects for the edge case dimension.
    """
    check_results: list[CheckResult] = []
    expected = ground_truth.get("expected", {})
    # Handle both old format (flat) and new format (with results wrapper)
    results = analysis.get("results", analysis)

    # EC-1: Empty repo handling - should return valid output with zero secrets
    is_empty_repo = expected.get("is_empty_repo", False)
    if is_empty_repo:
        has_valid_output = (
            "total_secrets" in results
            and results.get("total_secrets") == 0
            and "findings" in results
            and isinstance(results.get("findings"), list)
        )
        check_results.append(
            CheckResult(
                check_id="EC-1",
                category="Edge Cases",
                passed=has_valid_output,
                message="Empty repo produces valid zero-secret output" if has_valid_output else "Empty repo handling failed",
                expected="valid output with 0 secrets",
                actual={
                    "total_secrets": results.get("total_secrets"),
                    "has_findings_list": "findings" in results,
                },
            )
        )
    else:
        check_results.append(
            CheckResult(
                check_id="EC-1",
                category="Edge Cases",
                passed=True,
                message="N/A - not an empty repo scenario",
                expected="N/A",
                actual="N/A",
            )
        )

    # EC-2: Unicode file path handling - all paths should be valid UTF-8
    findings = results.get("findings", [])
    unicode_issues = []
    for i, finding in enumerate(findings):
        file_path = finding.get("file_path", "")
        try:
            # Check if path is valid UTF-8 and properly encoded
            if isinstance(file_path, str):
                file_path.encode("utf-8").decode("utf-8")
            elif isinstance(file_path, bytes):
                unicode_issues.append(f"Finding {i}: path is bytes, not string")
        except (UnicodeDecodeError, UnicodeEncodeError):
            unicode_issues.append(f"Finding {i}: invalid UTF-8 in path")

    check_results.append(
        CheckResult(
            check_id="EC-2",
            category="Edge Cases",
            passed=len(unicode_issues) == 0,
            message="All file paths are valid UTF-8" if not unicode_issues else f"Unicode issues: {unicode_issues[:3]}",
            expected="valid UTF-8 paths",
            actual="all valid" if not unicode_issues else unicode_issues,
        )
    )

    # EC-3: Large file handling - scan should complete without timeout
    # Check if scan_time_ms is reasonable (not timing out)
    scan_time = results.get("scan_time_ms", 0)
    max_expected_time = expected.get("max_scan_time_ms", 60000)  # 60s default max
    has_large_files = expected.get("has_large_files", False)

    if has_large_files:
        scan_completed = scan_time > 0 and scan_time < max_expected_time
        check_results.append(
            CheckResult(
                check_id="EC-3",
                category="Edge Cases",
                passed=scan_completed,
                message=f"Large file scan completed in {scan_time}ms" if scan_completed else "Large file scan may have timed out",
                expected=f"< {max_expected_time}ms",
                actual=scan_time,
            )
        )
    else:
        check_results.append(
            CheckResult(
                check_id="EC-3",
                category="Edge Cases",
                passed=True,
                message="N/A - no large file scenario",
                expected="N/A",
                actual="N/A",
            )
        )

    # EC-4: Binary file handling - binary files should be skipped or handled gracefully
    has_binary_files = expected.get("has_binary_files", False)
    binary_extensions = {".exe", ".dll", ".so", ".dylib", ".bin", ".png", ".jpg", ".gif", ".pdf", ".zip", ".tar", ".gz"}

    if has_binary_files:
        # Check that no findings are from binary files
        binary_findings = []
        for finding in findings:
            file_path = finding.get("file_path", "")
            ext = "." + file_path.split(".")[-1].lower() if "." in file_path else ""
            if ext in binary_extensions:
                binary_findings.append(file_path)

        check_results.append(
            CheckResult(
                check_id="EC-4",
                category="Edge Cases",
                passed=len(binary_findings) == 0,
                message="Binary files handled correctly" if not binary_findings else f"Findings in binary files: {binary_findings[:3]}",
                expected="no findings in binary files",
                actual="none" if not binary_findings else binary_findings,
            )
        )
    else:
        check_results.append(
            CheckResult(
                check_id="EC-4",
                category="Edge Cases",
                passed=True,
                message="N/A - no binary file scenario",
                expected="N/A",
                actual="N/A",
            )
        )

    return check_results
