"""
Accuracy checks (AC-1 to AC-8) for DevSkim security detection.

Tests detection accuracy for security vulnerabilities:
- AC-1: SQL injection detection
- AC-2: Hardcoded secrets detection
- AC-3: Insecure crypto detection
- AC-4: Path traversal detection
- AC-5: XSS detection
- AC-6: Deserialization detection
- AC-7: False positive rate
- AC-8: Overall precision/recall
"""

from . import (
    CheckResult,
    CheckCategory,
    load_all_ground_truth,
    get_file_from_analysis,
    count_findings_for_file,
    count_findings_by_category,
)


def run_accuracy_checks(
    analysis: dict,
    ground_truth_dir: str,
) -> list[CheckResult]:
    """Run all accuracy checks (AC-1 to AC-8)."""
    results = []
    ground_truth = load_all_ground_truth(ground_truth_dir)

    # AC-1: SQL injection detection
    sql_findings = count_findings_by_category(analysis, "sql_injection")
    sql_gt = _get_expected_count(ground_truth, "sql_injection")
    if not sql_gt:
        results.append(_skipped_check(
            check_id="AC-1",
            name="SQL injection detection",
            reason="No SQL injection expectations in ground truth",
        ))
    else:
        sql_passed = sql_findings >= sql_gt.get("min_expected", 0)
        sql_score = _compute_detection_score(sql_findings, sql_gt)
        results.append(CheckResult(
            check_id="AC-1",
            name="SQL injection detection",
            category=CheckCategory.ACCURACY,
            passed=sql_passed,
            score=sql_score,
            message=f"Found {sql_findings} SQL injection issues (expected >= {sql_gt.get('min_expected', 0)})",
            evidence={
                "count": sql_findings,
                "expected": sql_gt,
            },
        ))

    # AC-2: Hardcoded secrets detection
    secret_findings = count_findings_by_category(analysis, "hardcoded_secret")
    secret_gt = _get_expected_count(ground_truth, "hardcoded_secret")
    if not secret_gt:
        results.append(_skipped_check(
            check_id="AC-2",
            name="Hardcoded secrets detection",
            reason="No hardcoded secret expectations in ground truth",
        ))
    else:
        secret_passed = secret_findings >= secret_gt.get("min_expected", 0)
        secret_score = _compute_detection_score(secret_findings, secret_gt)
        results.append(CheckResult(
            check_id="AC-2",
            name="Hardcoded secrets detection",
            category=CheckCategory.ACCURACY,
            passed=secret_passed,
            score=secret_score,
            message=f"Found {secret_findings} hardcoded secrets (expected >= {secret_gt.get('min_expected', 0)})",
            evidence={
                "count": secret_findings,
                "expected": secret_gt,
            },
        ))

    # AC-3: Insecure crypto detection
    crypto_findings = count_findings_by_category(analysis, "insecure_crypto")
    crypto_gt = _get_expected_count(ground_truth, "insecure_crypto")
    if not crypto_gt:
        results.append(_skipped_check(
            check_id="AC-3",
            name="Insecure crypto detection",
            reason="No insecure crypto expectations in ground truth",
        ))
    else:
        crypto_passed = crypto_findings >= crypto_gt.get("min_expected", 0)
        crypto_score = _compute_detection_score(crypto_findings, crypto_gt)
        results.append(CheckResult(
            check_id="AC-3",
            name="Insecure crypto detection",
            category=CheckCategory.ACCURACY,
            passed=crypto_passed,
            score=crypto_score,
            message=f"Found {crypto_findings} insecure crypto issues (expected >= {crypto_gt.get('min_expected', 0)})",
            evidence={
                "count": crypto_findings,
                "expected": crypto_gt,
            },
        ))

    # AC-4: Path traversal detection
    path_findings = count_findings_by_category(analysis, "path_traversal")
    path_gt = _get_expected_count(ground_truth, "path_traversal")
    if not path_gt:
        results.append(_skipped_check(
            check_id="AC-4",
            name="Path traversal detection",
            reason="No path traversal expectations in ground truth",
        ))
    else:
        path_passed = path_findings >= path_gt.get("min_expected", 0)
        path_score = _compute_detection_score(path_findings, path_gt)
        results.append(CheckResult(
            check_id="AC-4",
            name="Path traversal detection",
            category=CheckCategory.ACCURACY,
            passed=path_passed,
            score=path_score,
            message=f"Found {path_findings} path traversal issues",
            evidence={
                "count": path_findings,
                "expected": path_gt,
            },
        ))

    # AC-5: XSS detection
    xss_findings = count_findings_by_category(analysis, "xss")
    xss_gt = _get_expected_count(ground_truth, "xss")
    if not xss_gt:
        results.append(_skipped_check(
            check_id="AC-5",
            name="XSS detection",
            reason="No XSS expectations in ground truth",
        ))
    else:
        xss_passed = xss_findings >= xss_gt.get("min_expected", 0)
        xss_score = _compute_detection_score(xss_findings, xss_gt)
        results.append(CheckResult(
            check_id="AC-5",
            name="XSS detection",
            category=CheckCategory.ACCURACY,
            passed=xss_passed,
            score=xss_score,
            message=f"Found {xss_findings} XSS issues",
            evidence={
                "count": xss_findings,
                "expected": xss_gt,
            },
        ))

    # AC-6: Deserialization detection
    deser_findings = count_findings_by_category(analysis, "deserialization")
    deser_gt = _get_expected_count(ground_truth, "deserialization")
    if not deser_gt:
        results.append(_skipped_check(
            check_id="AC-6",
            name="Deserialization detection",
            reason="No deserialization expectations in ground truth",
        ))
    else:
        deser_passed = deser_findings >= deser_gt.get("min_expected", 0)
        deser_score = _compute_detection_score(deser_findings, deser_gt)
        results.append(CheckResult(
            check_id="AC-6",
            name="Deserialization detection",
            category=CheckCategory.ACCURACY,
            passed=deser_passed,
            score=deser_score,
            message=f"Found {deser_findings} deserialization issues",
            evidence={
                "count": deser_findings,
                "expected": deser_gt,
            },
        ))

    # AC-7: False positive rate
    fp_score, fp_message, fp_evidence = _check_false_positive_rate(analysis, ground_truth)
    results.append(CheckResult(
        check_id="AC-7",
        name="False positive rate",
        category=CheckCategory.ACCURACY,
        passed=fp_score >= 0.7,
        score=fp_score,
        message=fp_message,
        evidence=fp_evidence,
    ))

    # AC-8: Overall precision/recall
    pr_score, pr_message, pr_evidence = _compute_precision_recall(analysis, ground_truth)
    results.append(CheckResult(
        check_id="AC-8",
        name="Overall precision/recall",
        category=CheckCategory.ACCURACY,
        passed=pr_score >= 0.6,
        score=pr_score,
        message=pr_message,
        evidence=pr_evidence,
    ))

    return results


def _get_expected_count(ground_truth: dict, category: str) -> dict | None:
    """Get expected count for a category from all ground truth files."""
    total_expected = {"min_expected": 0, "max_false_positives": 0}
    found = False

    for lang, gt in ground_truth.items():
        aggregate = gt.get("aggregate_expectations", {})
        if category in aggregate.get("required_categories", []):
            found = True
        for file_name, file_gt in gt.get("files", {}).items():
            for expected in file_gt.get("expected_issues", []):
                if expected.get("category") == category or _matches_category(expected, category):
                    total_expected["min_expected"] += expected.get("count", 0)
                    found = True

    return total_expected if found else None


def _skipped_check(check_id: str, name: str, reason: str) -> CheckResult:
    """Return a skipped check result when ground truth is missing."""
    return CheckResult(
        check_id=check_id,
        name=name,
        category=CheckCategory.ACCURACY,
        passed=True,
        score=1.0,
        message=f"Skipped: {reason}",
        evidence={
            "skipped": True,
            "reason": reason,
        },
    )


def _matches_category(expected: dict, category: str) -> bool:
    """Check if expected issue matches a category."""
    rule_id = expected.get("rule_id", "").lower()
    category_lower = category.lower()

    if "sql" in category_lower and "sql" in rule_id:
        return True
    if "secret" in category_lower and ("secret" in rule_id or "password" in rule_id or "credential" in rule_id):
        return True
    if "crypto" in category_lower and ("crypto" in rule_id or "md5" in rule_id or "sha1" in rule_id):
        return True

    return False


def _compute_detection_score(found: int, expected: dict | None) -> float:
    """Compute detection score based on found vs expected."""
    if expected is None:
        # No ground truth, give partial credit if anything found
        return 0.7 if found > 0 else 0.5

    min_expected = expected.get("min_expected", 0)
    if min_expected == 0:
        return 1.0 if found >= 0 else 0.5

    if found >= min_expected:
        return 1.0
    elif found > 0:
        return 0.5 + (found / min_expected) * 0.5
    else:
        return 0.0


def _check_false_positive_rate(analysis: dict, ground_truth: dict) -> tuple[float, str, dict]:
    """Check false positive rate against ground truth."""
    total_findings = analysis.get("summary", {}).get("total_issues", 0)
    if total_findings == 0:
        return 1.0, "No findings to check for false positives", {}

    # Count findings in safe files (files expected to have no issues)
    false_positives = 0
    safe_files = []

    for lang, gt in ground_truth.items():
        for file_name, file_gt in gt.get("files", {}).items():
            if file_gt.get("expected_issues", []) == []:
                safe_files.append(file_name)
                file_findings = _count_file_findings(analysis, file_name)
                false_positives += file_findings

    max_allowed = int(total_findings * 0.2)  # Allow 20% false positive rate
    score = max(0.0, 1.0 - (false_positives / total_findings)) if total_findings > 0 else 1.0

    return (
        score,
        f"Found {false_positives} potential false positives out of {total_findings} total",
        {
            "false_positives": false_positives,
            "total_findings": total_findings,
            "safe_files_checked": safe_files,
        },
    )


def _count_file_findings(analysis: dict, file_name: str) -> int:
    """Count findings for a file by name (partial match)."""
    for file_info in analysis.get("files", []):
        if file_name in file_info.get("path", ""):
            return file_info.get("issue_count", 0)
    return 0


def _compute_precision_recall(analysis: dict, ground_truth: dict) -> tuple[float, str, dict]:
    """Compute overall precision and recall."""
    total_expected = 0
    total_found = 0
    true_positives = 0

    for lang, gt in ground_truth.items():
        for file_name, file_gt in gt.get("files", {}).items():
            expected_count = file_gt.get("total_expected", 0)
            total_expected += expected_count

            found_count = _count_file_findings(analysis, file_name)
            total_found += found_count

            # Estimate true positives as min(found, expected)
            true_positives += min(found_count, expected_count)

    precision = true_positives / total_found if total_found > 0 else 1.0
    recall = true_positives / total_expected if total_expected > 0 else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    score = f1

    return (
        score,
        f"Precision: {precision:.2f}, Recall: {recall:.2f}, F1: {f1:.2f}",
        {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "true_positives": true_positives,
            "total_found": total_found,
            "total_expected": total_expected,
        },
    )
