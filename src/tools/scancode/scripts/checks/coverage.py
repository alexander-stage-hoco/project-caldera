"""Coverage checks for license analysis (LC-1 to LC-8)."""

from . import CheckResult, check_boolean


def run_coverage_checks(
    analysis: dict, ground_truth: dict
) -> list[CheckResult]:
    """Run all coverage checks."""
    results = []
    expected = ground_truth.get("expected", {})

    # LC-1: Summary metrics present
    summary_fields = [
        "total_files_scanned",
        "files_with_licenses",
        "license_files_found",
    ]
    missing_summary = [f for f in summary_fields if f not in analysis]
    results.append(
        CheckResult(
            check_id="LC-1",
            category="Coverage",
            passed=len(missing_summary) == 0,
            message=f"Summary fields: missing={missing_summary or 'none'}",
            expected=summary_fields,
            actual=[f for f in summary_fields if f in analysis],
        )
    )

    # LC-2: Licenses inventory present
    has_licenses_found = "licenses_found" in analysis
    has_license_counts = "license_counts" in analysis
    results.append(
        CheckResult(
            check_id="LC-2",
            category="Coverage",
            passed=has_licenses_found and has_license_counts,
            message=f"License inventory: licenses_found={has_licenses_found}, license_counts={has_license_counts}",
            expected="licenses_found and license_counts present",
            actual=f"licenses_found={has_licenses_found}, license_counts={has_license_counts}",
        )
    )

    # LC-3: Category flags present
    category_fields = [
        "has_permissive",
        "has_weak_copyleft",
        "has_copyleft",
        "has_unknown",
    ]
    missing_categories = [f for f in category_fields if f not in analysis]
    results.append(
        CheckResult(
            check_id="LC-3",
            category="Coverage",
            passed=len(missing_categories) == 0,
            message=f"Category flags: missing={missing_categories or 'none'}",
            expected=category_fields,
            actual=[f for f in category_fields if f in analysis],
        )
    )

    # LC-4: Risk assessment present
    has_risk = "overall_risk" in analysis
    has_reasons = "risk_reasons" in analysis
    results.append(
        CheckResult(
            check_id="LC-4",
            category="Coverage",
            passed=has_risk and has_reasons,
            message=f"Risk assessment: overall_risk={has_risk}, risk_reasons={has_reasons}",
            expected="overall_risk and risk_reasons present",
            actual=f"overall_risk={has_risk}, risk_reasons={has_reasons}",
        )
    )

    # LC-5: Findings array present with required fields
    findings = analysis.get("findings", [])
    has_findings = "findings" in analysis
    finding_fields = ["file_path", "spdx_id", "category", "confidence", "match_type"]
    findings_complete = all(
        all(f in finding for f in finding_fields)
        for finding in findings
    ) if findings else True
    results.append(
        CheckResult(
            check_id="LC-5",
            category="Coverage",
            passed=has_findings and findings_complete,
            message=f"Findings array: present={has_findings}, complete={findings_complete}",
            expected="findings with file_path, spdx_id, category, confidence, match_type",
            actual=f"present={has_findings}, complete={findings_complete}",
        )
    )

    # LC-6: File summaries present
    files = analysis.get("files", {})
    has_files = "files" in analysis
    file_fields = ["file_path", "licenses", "category", "has_spdx_header"]
    files_complete = all(
        all(f in file_data for f in file_fields)
        for file_data in files.values()
    ) if files else True
    results.append(
        CheckResult(
            check_id="LC-6",
            category="Coverage",
            passed=has_files and files_complete,
            message=f"File summaries: present={has_files}, complete={files_complete}",
            expected="files with file_path, licenses, category, has_spdx_header",
            actual=f"present={has_files}, complete={files_complete}",
        )
    )

    # LC-7: Metadata present
    metadata_fields = ["schema_version", "repository", "timestamp", "tool", "tool_version"]
    missing_metadata = [f for f in metadata_fields if f not in analysis]
    results.append(
        CheckResult(
            check_id="LC-7",
            category="Coverage",
            passed=len(missing_metadata) == 0,
            message=f"Metadata: missing={missing_metadata or 'none'}",
            expected=metadata_fields,
            actual=[f for f in metadata_fields if f in analysis],
        )
    )

    # LC-8: Timing present
    has_timing = "scan_time_ms" in analysis
    results.append(
        check_boolean(
            "LC-8",
            "Coverage",
            "Timing present (scan_time_ms)",
            True,
            has_timing,
        )
    )

    return results
