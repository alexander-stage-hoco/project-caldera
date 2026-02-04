"""Detection checks for license analysis (LD-1 to LD-6)."""

from . import CheckResult


def run_detection_checks(
    analysis: dict, ground_truth: dict
) -> list[CheckResult]:
    """Run all detection quality checks."""
    results = []
    expected = ground_truth.get("expected", {})
    findings = analysis.get("findings", [])

    # LD-1: SPDX header detection
    expected_spdx_count = expected.get("spdx_headers_found", 0)
    actual_spdx_count = sum(1 for f in findings if f.get("match_type") == "spdx")
    results.append(
        CheckResult(
            check_id="LD-1",
            category="Detection",
            passed=expected_spdx_count == actual_spdx_count,
            message=f"SPDX headers: expected={expected_spdx_count}, actual={actual_spdx_count}",
            expected=expected_spdx_count,
            actual=actual_spdx_count,
        )
    )

    # LD-2: License file detection
    expected_file_count = expected.get("license_file_detections", 0)
    actual_file_count = sum(1 for f in findings if f.get("match_type") == "file")
    results.append(
        CheckResult(
            check_id="LD-2",
            category="Detection",
            passed=expected_file_count == actual_file_count,
            message=f"License file detections: expected={expected_file_count}, actual={actual_file_count}",
            expected=expected_file_count,
            actual=actual_file_count,
        )
    )

    # LD-3: Confidence scores valid (all between 0 and 1)
    confidences = [f.get("confidence", 0) for f in findings]
    all_valid = all(0 <= c <= 1 for c in confidences)
    results.append(
        CheckResult(
            check_id="LD-3",
            category="Detection",
            passed=all_valid,
            message=f"Confidence scores valid: all in [0,1]={all_valid}",
            expected="all confidences in [0, 1]",
            actual=f"min={min(confidences) if confidences else 'N/A'}, max={max(confidences) if confidences else 'N/A'}",
        )
    )

    # LD-4: Category classification correct
    categories_valid = all(
        f.get("category") in ["permissive", "weak-copyleft", "copyleft", "unknown"]
        for f in findings
    )
    results.append(
        CheckResult(
            check_id="LD-4",
            category="Detection",
            passed=categories_valid,
            message=f"Category classification: all valid={categories_valid}",
            expected="categories in [permissive, weak-copyleft, copyleft, unknown]",
            actual=[f.get("category") for f in findings],
        )
    )

    # LD-5: Match type classification correct
    match_types_valid = all(
        f.get("match_type") in ["file", "header", "spdx"]
        for f in findings
    )
    results.append(
        CheckResult(
            check_id="LD-5",
            category="Detection",
            passed=match_types_valid,
            message=f"Match type classification: all valid={match_types_valid}",
            expected="match_types in [file, header, spdx]",
            actual=[f.get("match_type") for f in findings],
        )
    )

    # LD-6: Finding count matches expected
    expected_findings_count = expected.get("total_findings", len(findings))
    actual_findings_count = len(findings)
    results.append(
        CheckResult(
            check_id="LD-6",
            category="Detection",
            passed=expected_findings_count == actual_findings_count,
            message=f"Finding count matches: expected={expected_findings_count}, actual={actual_findings_count}",
            expected=expected_findings_count,
            actual=actual_findings_count,
        )
    )

    return results
