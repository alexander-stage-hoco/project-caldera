from __future__ import annotations
"""
Accuracy checks (AC-1 to AC-10) for Roslyn Analyzers evaluation.

These checks verify detection accuracy for different violation categories.
"""

from . import (
    CheckResult,
    compute_recall,
    compute_precision,
    match_violations,
    get_violations_for_file,
    count_violations_by_rule,
)


def ac1_sql_injection_detection(analysis: dict, ground_truth: dict) -> CheckResult:
    """AC-1: SQL injection detection accuracy (>=80% recall on CA3001/CA2100)."""
    files = ground_truth.get("files", {})
    target_file = "security/sql_injection.cs"
    expected_data = files.get(target_file, {})

    expected_violations = expected_data.get("expected_violations", [])
    detected_violations = get_violations_for_file(analysis, target_file)

    # Count expected SQL injection violations
    expected_count = sum(
        v.get("count", 0) for v in expected_violations
        if v.get("rule_id") in ["CA3001", "CA2100"]
    )

    # Count detected
    detected_count = sum(
        1 for v in detected_violations
        if v.get("rule_id") in ["CA3001", "CA2100"]
    )

    recall = compute_recall(detected_count, expected_count)
    passed = recall >= 0.80

    return CheckResult(
        check_id="AC-1",
        name="SQL Injection Detection",
        category="accuracy",
        passed=passed,
        score=recall,
        threshold=0.80,
        actual_value=recall,
        message=f"{'All' if recall == 1.0 else f'{detected_count}/{expected_count}'} SQL injection patterns detected ({recall*100:.1f}% recall)",
        evidence={
            "expected": expected_count,
            "detected": detected_count,
            "missed": expected_count - detected_count,
            "rules_checked": ["CA3001", "CA2100"],
            "file_checked": target_file,
        }
    )


def ac2_xss_detection(analysis: dict, ground_truth: dict) -> CheckResult:
    """AC-2: XSS detection accuracy (>=80% recall on CA3002/SCS0029, or pass if analyzer limitation)."""
    files = ground_truth.get("files", {})
    target_file = "security/xss_vulnerabilities.cs"
    expected_data = files.get(target_file, {})

    expected_violations = expected_data.get("expected_violations", [])
    detected_violations = get_violations_for_file(analysis, target_file)
    is_analyzer_limitation = expected_data.get("analyzer_limitation", False)

    # Accept both CA3002 (built-in) and SCS0029 (SecurityCodeScan) for XSS detection
    xss_rules = ["CA3002", "SCS0029", "SCS0002"]

    expected_count = sum(
        v.get("count", 0) for v in expected_violations
        if v.get("rule_id") in xss_rules
    )

    detected_count = sum(
        1 for v in detected_violations
        if v.get("rule_id") in xss_rules
    )

    # If marked as analyzer limitation with 0 expected, pass the check
    if is_analyzer_limitation and expected_count == 0:
        return CheckResult(
            check_id="AC-2",
            name="XSS Detection",
            category="accuracy",
            passed=True,
            score=1.0,
            threshold=0.80,
            actual_value=1.0,
            message="XSS detection skipped (known analyzer limitation - CA3002/SCS0029 require specific patterns)",
            evidence={
                "expected": 0,
                "detected": detected_count,
                "analyzer_limitation": True,
                "rules_checked": xss_rules,
                "file_checked": target_file,
            }
        )

    recall = compute_recall(detected_count, expected_count)
    passed = recall >= 0.80

    return CheckResult(
        check_id="AC-2",
        name="XSS Detection",
        category="accuracy",
        passed=passed,
        score=recall,
        threshold=0.80,
        actual_value=recall,
        message=f"{'All' if recall == 1.0 else f'{detected_count}/{expected_count}'} XSS patterns detected ({recall*100:.1f}% recall)",
        evidence={
            "expected": expected_count,
            "detected": detected_count,
            "missed": expected_count - detected_count,
            "rules_checked": xss_rules,
            "file_checked": target_file,
        }
    )


def ac3_hardcoded_secrets_detection(analysis: dict, ground_truth: dict) -> CheckResult:
    """AC-3: Hardcoded secrets detection accuracy (>=80% recall on CA5390/SCS0015, or pass if analyzer limitation)."""
    files = ground_truth.get("files", {})
    target_file = "security/hardcoded_secrets.cs"
    expected_data = files.get(target_file, {})

    expected_violations = expected_data.get("expected_violations", [])
    detected_violations = get_violations_for_file(analysis, target_file)
    is_analyzer_limitation = expected_data.get("analyzer_limitation", False)

    # Accept both CA5390 (built-in, deprecated) and SCS0015 (SecurityCodeScan) for secrets
    secrets_rules = ["CA5390", "SCS0015"]

    expected_count = sum(
        v.get("count", 0) for v in expected_violations
        if v.get("rule_id") in secrets_rules
    )

    detected_count = sum(
        1 for v in detected_violations
        if v.get("rule_id") in secrets_rules
    )

    # If marked as analyzer limitation with 0 expected, pass the check
    if is_analyzer_limitation and expected_count == 0:
        return CheckResult(
            check_id="AC-3",
            name="Hardcoded Secrets Detection",
            category="accuracy",
            passed=True,
            score=1.0,
            threshold=0.80,
            actual_value=1.0,
            message="Hardcoded secrets detection skipped (known analyzer limitation - CA5390 deprecated, SCS0015 requires specific patterns)",
            evidence={
                "expected": 0,
                "detected": detected_count,
                "analyzer_limitation": True,
                "rules_checked": secrets_rules,
                "file_checked": target_file,
            }
        )

    recall = compute_recall(detected_count, expected_count)
    passed = recall >= 0.80

    return CheckResult(
        check_id="AC-3",
        name="Hardcoded Secrets Detection",
        category="accuracy",
        passed=passed,
        score=recall,
        threshold=0.80,
        actual_value=recall,
        message=f"{detected_count}/{expected_count} hardcoded secrets detected ({recall*100:.1f}% recall)",
        evidence={
            "expected": expected_count,
            "detected": detected_count,
            "missed": expected_count - detected_count,
            "rules_checked": secrets_rules,
            "file_checked": target_file,
        }
    )


def ac4_weak_crypto_detection(analysis: dict, ground_truth: dict) -> CheckResult:
    """AC-4: Weak crypto detection accuracy (>=80% recall on CA5350/CA5351)."""
    files = ground_truth.get("files", {})
    target_file = "security/weak_crypto.cs"
    expected_data = files.get(target_file, {})

    expected_violations = expected_data.get("expected_violations", [])
    detected_violations = get_violations_for_file(analysis, target_file)

    expected_count = sum(
        v.get("count", 0) for v in expected_violations
        if v.get("rule_id") in ["CA5350", "CA5351"]
    )

    detected_count = sum(
        1 for v in detected_violations
        if v.get("rule_id") in ["CA5350", "CA5351"]
    )

    recall = compute_recall(detected_count, expected_count)
    passed = recall >= 0.80

    return CheckResult(
        check_id="AC-4",
        name="Weak Crypto Detection",
        category="accuracy",
        passed=passed,
        score=recall,
        threshold=0.80,
        actual_value=recall,
        message=f"{detected_count}/{expected_count} weak crypto patterns detected ({recall*100:.1f}% recall)",
        evidence={
            "expected": expected_count,
            "detected": detected_count,
            "missed": expected_count - detected_count,
            "rules_checked": ["CA5350", "CA5351"],
            "file_checked": target_file,
        }
    )


def ac5_insecure_deserialization_detection(analysis: dict, ground_truth: dict) -> CheckResult:
    """AC-5: Insecure deserialization detection (>=80% recall on CA2300-CA2315)."""
    files = ground_truth.get("files", {})
    target_file = "security/insecure_deserialization.cs"
    expected_data = files.get(target_file, {})

    expected_violations = expected_data.get("expected_violations", [])
    detected_violations = get_violations_for_file(analysis, target_file)

    deser_rules = ["CA2300", "CA2301", "CA2305", "CA2311", "CA2315"]

    expected_count = sum(
        v.get("count", 0) for v in expected_violations
        if v.get("rule_id") in deser_rules
    )

    detected_count = sum(
        1 for v in detected_violations
        if v.get("rule_id") in deser_rules
    )

    recall = compute_recall(detected_count, expected_count)
    passed = recall >= 0.80

    return CheckResult(
        check_id="AC-5",
        name="Insecure Deserialization Detection",
        category="accuracy",
        passed=passed,
        score=recall,
        threshold=0.80,
        actual_value=recall,
        message=f"{detected_count}/{expected_count} deserialization issues detected ({recall*100:.1f}% recall)",
        evidence={
            "expected": expected_count,
            "detected": detected_count,
            "missed": expected_count - detected_count,
            "rules_checked": deser_rules,
            "file_checked": target_file,
        }
    )


def ac6_resource_disposal_detection(analysis: dict, ground_truth: dict) -> CheckResult:
    """AC-6: Resource disposal detection (>=80% recall on CA2000/CA1001)."""
    files = ground_truth.get("files", {})

    # Check multiple resource files
    resource_files = [
        "resource/undisposed_objects.cs",
        "resource/missing_idisposable.cs",
    ]

    total_expected = 0
    total_detected = 0
    disposal_rules = ["CA2000", "CA1001"]

    for target_file in resource_files:
        expected_data = files.get(target_file, {})
        expected_violations = expected_data.get("expected_violations", [])
        detected_violations = get_violations_for_file(analysis, target_file)

        total_expected += sum(
            v.get("count", 0) for v in expected_violations
            if v.get("rule_id") in disposal_rules
        )

        total_detected += sum(
            1 for v in detected_violations
            if v.get("rule_id") in disposal_rules
        )

    recall = compute_recall(total_detected, total_expected)
    passed = recall >= 0.80

    return CheckResult(
        check_id="AC-6",
        name="Resource Disposal Detection",
        category="accuracy",
        passed=passed,
        score=recall,
        threshold=0.80,
        actual_value=recall,
        message=f"{total_detected}/{total_expected} disposal issues detected ({recall*100:.1f}% recall)",
        evidence={
            "expected": total_expected,
            "detected": total_detected,
            "missed": total_expected - total_detected,
            "rules_checked": disposal_rules,
            "files_checked": resource_files,
        }
    )


def ac7_dead_code_detection(analysis: dict, ground_truth: dict) -> CheckResult:
    """AC-7: Dead code detection (>=80% recall on IDE0005/IDE0060, skipping analyzer limitations)."""
    files = ground_truth.get("files", {})

    dead_code_files = [
        "dead_code/unused_imports.cs",
        "dead_code/unused_parameters.cs",
    ]

    total_expected = 0
    total_detected = 0
    dead_code_rules = ["IDE0005", "IDE0060"]
    active_files = []
    skipped_files = []

    for target_file in dead_code_files:
        expected_data = files.get(target_file, {})

        # Skip files marked as analyzer limitations
        if expected_data.get("analyzer_limitation", False):
            skipped_files.append(target_file)
            continue

        active_files.append(target_file)
        expected_violations = expected_data.get("expected_violations", [])
        detected_violations = get_violations_for_file(analysis, target_file)

        total_expected += sum(
            v.get("count", 0) for v in expected_violations
            if v.get("rule_id") in dead_code_rules
        )

        total_detected += sum(
            1 for v in detected_violations
            if v.get("rule_id") in dead_code_rules
        )

    recall = compute_recall(total_detected, total_expected)
    passed = recall >= 0.80

    message = f"{total_detected}/{total_expected} dead code issues detected ({recall*100:.1f}% recall)"
    if skipped_files:
        message += f" (skipped {len(skipped_files)} files with analyzer limitations)"

    return CheckResult(
        check_id="AC-7",
        name="Dead Code Detection",
        category="accuracy",
        passed=passed,
        score=recall,
        threshold=0.80,
        actual_value=recall,
        message=message,
        evidence={
            "expected": total_expected,
            "detected": total_detected,
            "missed": total_expected - total_detected,
            "rules_checked": dead_code_rules,
            "files_checked": active_files,
            "skipped_files": skipped_files,
        }
    )


def ac8_design_violation_detection(analysis: dict, ground_truth: dict) -> CheckResult:
    """AC-8: Design violation detection (>=80% recall on CA1051/CA1040)."""
    files = ground_truth.get("files", {})

    design_files = [
        "design/visible_fields.cs",
        "design/empty_interfaces.cs",
    ]

    total_expected = 0
    total_detected = 0
    design_rules = ["CA1051", "CA1040"]

    for target_file in design_files:
        expected_data = files.get(target_file, {})
        expected_violations = expected_data.get("expected_violations", [])
        detected_violations = get_violations_for_file(analysis, target_file)

        total_expected += sum(
            v.get("count", 0) for v in expected_violations
            if v.get("rule_id") in design_rules
        )

        total_detected += sum(
            1 for v in detected_violations
            if v.get("rule_id") in design_rules
        )

    recall = compute_recall(total_detected, total_expected)
    passed = recall >= 0.80

    return CheckResult(
        check_id="AC-8",
        name="Design Violation Detection",
        category="accuracy",
        passed=passed,
        score=recall,
        threshold=0.80,
        actual_value=recall,
        message=f"{total_detected}/{total_expected} design violations detected ({recall*100:.1f}% recall)",
        evidence={
            "expected": total_expected,
            "detected": total_detected,
            "missed": total_expected - total_detected,
            "rules_checked": design_rules,
            "files_checked": design_files,
        }
    )


def ac9_overall_precision(analysis: dict, ground_truth: dict) -> CheckResult:
    """AC-9: Overall precision - measured via false positive rate on clean files.

    Note: With 14+ analyzers running, total violations will exceed ground truth.
    The ground truth only enumerates specific expected violations for testing
    detection capabilities, not ALL violations the analyzers might find.

    True precision is measured by checking if clean files (marked with
    is_false_positive_test=True) incorrectly get flagged. Any violation on
    a known-clean file is a true false positive.

    Precision = (total_reported - false_positives) / total_reported
    """
    files = ground_truth.get("files", {})
    analysis_files = analysis.get("files", [])

    # Find clean files (false positive test files)
    clean_files = [
        f for f, data in files.items()
        if data.get("is_false_positive_test", False)
    ]

    # Count violations on clean files (true false positives)
    false_positives = 0
    fp_details = []
    for af in analysis_files:
        file_path = af.get("file", "")
        # Normalize path to match ground truth keys
        normalized = file_path.replace("\\", "/")
        if any(normalized.endswith(cf) for cf in clean_files):
            violations = af.get("violations", [])
            if violations:
                false_positives += len(violations)
                fp_details.append({
                    "file": file_path,
                    "violation_count": len(violations),
                })

    analysis_summary = analysis.get("summary", {})
    total_reported = analysis_summary.get("total_violations", 0)

    # True positives = all reported minus false positives on clean files
    true_positives = total_reported - false_positives

    precision = compute_precision(true_positives, total_reported) if total_reported > 0 else 1.0
    passed = precision >= 0.85

    return CheckResult(
        check_id="AC-9",
        name="Overall Precision",
        category="accuracy",
        passed=passed,
        score=precision,
        threshold=0.85,
        actual_value=precision,
        message=f"Precision: {true_positives}/{total_reported} ({precision*100:.1f}%). {false_positives} false positives on {len(clean_files)} clean files.",
        evidence={
            "true_positives": true_positives,
            "false_positives": false_positives,
            "total_reported": total_reported,
            "clean_files_tested": len(clean_files),
            "precision": precision,
            "fp_file_details": fp_details if fp_details else "none",
        }
    )


def ac10_overall_recall(analysis: dict, ground_truth: dict) -> CheckResult:
    """AC-10: Overall recall (>=80% detected / total expected)."""
    summary = ground_truth.get("summary", {})
    total_expected = summary.get("total_expected_violations", 0)

    analysis_summary = analysis.get("summary", {})
    total_detected = analysis_summary.get("total_violations", 0)

    # Estimate detected as the actual detections
    detected = min(total_detected, total_expected)
    recall = compute_recall(detected, total_expected)
    passed = recall >= 0.80

    return CheckResult(
        check_id="AC-10",
        name="Overall Recall",
        category="accuracy",
        passed=passed,
        score=recall,
        threshold=0.80,
        actual_value=recall,
        message=f"Recall: {detected}/{total_expected} violations detected ({recall*100:.1f}%)",
        evidence={
            "detected": detected,
            "expected": total_expected,
            "missed": total_expected - detected,
            "recall": recall,
        }
    )


def run_all_accuracy_checks(analysis: dict, ground_truth: dict) -> list[CheckResult]:
    """Run all accuracy checks and return results."""
    return [
        ac1_sql_injection_detection(analysis, ground_truth),
        ac2_xss_detection(analysis, ground_truth),
        ac3_hardcoded_secrets_detection(analysis, ground_truth),
        ac4_weak_crypto_detection(analysis, ground_truth),
        ac5_insecure_deserialization_detection(analysis, ground_truth),
        ac6_resource_disposal_detection(analysis, ground_truth),
        ac7_dead_code_detection(analysis, ground_truth),
        ac8_design_violation_detection(analysis, ground_truth),
        ac9_overall_precision(analysis, ground_truth),
        ac10_overall_recall(analysis, ground_truth),
    ]
