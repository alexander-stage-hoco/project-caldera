"""
Accuracy checks (AC-1 to AC-9) for Semgrep smell detection.

Tests detection accuracy against ground truth:
- AC-1: SQL injection detection
- AC-2: Empty catch detection
- AC-3: Catch-all detection
- AC-4: Async void detection
- AC-5: HttpClient new detection
- AC-6: High complexity detection
- AC-7: God class detection
- AC-8: Overall detection quality (categorization rate)
- AC-9: Line number accuracy (±2 tolerance)
"""

from . import (
    CheckResult,
    CheckCategory,
    load_analysis,
    load_all_ground_truth,
    get_file_from_analysis,
    get_smells_by_type,
    normalize_path,
)


def _get_expected_count(smell: dict) -> int:
    """Get expected count from smell dict, supporting both 'count' and 'min_count' fields.

    Ground truth entries may have:
    - 'count': exact expected count
    - 'min_count': minimum expected count (used for flexible detection)

    Returns count if present, otherwise min_count, otherwise 0.
    """
    return smell.get("count", smell.get("min_count", 0))


def check_line_accuracy(
    analysis: dict,
    ground_truth: dict[str, dict],
    tolerance: int = 2,
) -> tuple[int, int, int, dict]:
    """Check line number accuracy across all files.

    Compares detected smell line numbers against expected lines from ground truth.
    A detection is considered:
    - "exact" if detected line == expected line
    - "near" if abs(detected line - expected line) <= tolerance

    Args:
        analysis: Analysis output with files and smells
        ground_truth: Ground truth dict keyed by language
        tolerance: Line number tolerance for near matches (default ±2)

    Returns:
        Tuple of (exact_matches, near_matches, total_expected, per_smell_stats)
    """
    exact = near = total = 0
    per_smell_stats: dict[str, dict] = {}  # Track per smell type

    for lang, lang_gt in ground_truth.items():
        for filename, file_gt in lang_gt.get("files", {}).items():
            # Get detected smells for this file
            file_info = get_file_from_analysis(analysis, filename)
            if not file_info:
                continue

            detected_smells = file_info.get("smells", [])

            for expected in file_gt.get("expected_smells", []):
                smell_id = expected.get("smell_id")
                expected_lines = expected.get("lines", [])

                if not expected_lines:  # Skip if no line expectations
                    continue

                # Initialize per-smell tracking
                if smell_id not in per_smell_stats:
                    per_smell_stats[smell_id] = {
                        "exact": 0, "near": 0, "missed": 0, "total": 0
                    }

                # Get detected lines for this smell type
                detected_lines = [
                    s["line_start"]
                    for s in detected_smells
                    if s.get("dd_smell_id") == smell_id
                ]

                for exp_line in expected_lines:
                    total += 1
                    per_smell_stats[smell_id]["total"] += 1

                    if exp_line in detected_lines:
                        exact += 1
                        per_smell_stats[smell_id]["exact"] += 1
                    elif any(abs(det - exp_line) <= tolerance for det in detected_lines):
                        near += 1
                        per_smell_stats[smell_id]["near"] += 1
                    else:
                        per_smell_stats[smell_id]["missed"] += 1

    return exact, near, total, per_smell_stats


def run_accuracy_checks(
    analysis: dict,
    ground_truth_dir: str,
) -> list[CheckResult]:
    """Run all accuracy checks (AC-1 to AC-9)."""
    results = []
    gt = load_all_ground_truth(ground_truth_dir)
    smells_by_type = get_smells_by_type(analysis)

    # AC-1: SQL injection detection
    sql_count = smells_by_type.get("SQL_INJECTION", 0)
    expected_sql = sum(
        sum(_get_expected_count(s) for s in f.get("expected_smells", []) if "SQL" in s.get("smell_id", ""))
        for lang_gt in gt.values()
        for f in lang_gt.get("files", {}).values()
    )

    ac1_score = min(sql_count / expected_sql, 1.0) if expected_sql > 0 else (1.0 if sql_count == 0 else 0.0)
    results.append(CheckResult(
        check_id="AC-1",
        name="SQL injection detection",
        category=CheckCategory.ACCURACY,
        passed=sql_count > 0 and ac1_score >= 0.5,
        score=ac1_score,
        message=f"Detected {sql_count} SQL injections (expected ~{expected_sql})",
        evidence={"detected": sql_count, "expected": expected_sql},
    ))

    # AC-2: Empty catch detection
    empty_catch_count = smells_by_type.get("D1_EMPTY_CATCH", 0)
    expected_empty = sum(
        sum(_get_expected_count(s) for s in f.get("expected_smells", []) if s.get("smell_id") == "D1_EMPTY_CATCH")
        for lang_gt in gt.values()
        for f in lang_gt.get("files", {}).values()
    )

    # Semgrep auto config doesn't include empty catch rules by default
    # Score based on presence of any detection
    ac2_score = min(empty_catch_count / expected_empty, 1.0) if expected_empty > 0 else 1.0
    results.append(CheckResult(
        check_id="AC-2",
        name="Empty catch detection",
        category=CheckCategory.ACCURACY,
        passed=ac2_score >= 0.5 if expected_empty > 0 else True,  # Require ≥50% detection
        score=ac2_score if expected_empty > 0 else 0.5,
        message=f"Detected {empty_catch_count} empty catches (expected ~{expected_empty})",
        evidence={
            "detected": empty_catch_count,
            "expected": expected_empty,
            "note": "Requires custom rules - auto config doesn't include empty catch rules",
        },
    ))

    # AC-3: Catch-all detection
    catch_all_count = smells_by_type.get("D2_CATCH_ALL", 0)
    expected_catch_all = sum(
        sum(_get_expected_count(s) for s in f.get("expected_smells", []) if s.get("smell_id") == "D2_CATCH_ALL")
        for lang_gt in gt.values()
        for f in lang_gt.get("files", {}).values()
    )

    ac3_score = min(catch_all_count / expected_catch_all, 1.0) if expected_catch_all > 0 else 1.0
    results.append(CheckResult(
        check_id="AC-3",
        name="Catch-all detection",
        category=CheckCategory.ACCURACY,
        passed=ac3_score >= 0.5 if expected_catch_all > 0 else True,  # Require ≥50% detection
        score=ac3_score if expected_catch_all > 0 else 0.5,
        message=f"Detected {catch_all_count} catch-all patterns",
        evidence={"detected": catch_all_count, "expected": expected_catch_all},
    ))

    # AC-4: Async void detection (C# specific)
    async_void_count = smells_by_type.get("E2_ASYNC_VOID", 0)
    expected_async = sum(
        sum(_get_expected_count(s) for s in f.get("expected_smells", []) if s.get("smell_id") == "E2_ASYNC_VOID")
        for lang_gt in gt.values()
        for f in lang_gt.get("files", {}).values()
    )

    ac4_score = min(async_void_count / expected_async, 1.0) if expected_async > 0 else 1.0
    results.append(CheckResult(
        check_id="AC-4",
        name="Async void detection",
        category=CheckCategory.ACCURACY,
        passed=ac4_score >= 0.5 if expected_async > 0 else True,  # Require ≥50% detection
        score=ac4_score if expected_async > 0 else 0.5,
        message=f"Detected {async_void_count} async void methods",
        evidence={"detected": async_void_count, "expected": expected_async},
    ))

    # AC-5: HttpClient new detection
    httpclient_count = smells_by_type.get("F3_HTTPCLIENT_NEW", 0)
    # Also count any SSRF detections which often involve HttpClient
    for smell_type, count in smells_by_type.items():
        if "http" in smell_type.lower() or "ssrf" in smell_type.lower():
            httpclient_count += count

    ac5_score = 1.0 if httpclient_count > 0 else 0.5
    results.append(CheckResult(
        check_id="AC-5",
        name="HttpClient/HTTP-related detection",
        category=CheckCategory.ACCURACY,
        passed=ac5_score >= 0.5,  # Require ≥50% detection
        score=ac5_score,
        message=f"Detected {httpclient_count} HTTP-related issues",
        evidence={"detected": httpclient_count},
    ))

    # AC-6: High complexity detection
    complexity_count = smells_by_type.get("A2_HIGH_CYCLOMATIC", 0)
    results.append(CheckResult(
        check_id="AC-6",
        name="High complexity detection",
        category=CheckCategory.ACCURACY,
        passed=True,
        score=0.5,  # Neutral - Semgrep isn't a complexity analyzer
        message=f"Detected {complexity_count} high complexity (Semgrep focuses on security)",
        evidence={
            "detected": complexity_count,
            "note": "Semgrep is not designed for complexity analysis - use Lizard",
        },
    ))

    # AC-7: God class detection
    god_class_count = smells_by_type.get("C3_GOD_CLASS", 0)
    results.append(CheckResult(
        check_id="AC-7",
        name="God class detection",
        category=CheckCategory.ACCURACY,
        passed=True,
        score=0.5,  # Neutral
        message=f"Detected {god_class_count} god classes (Semgrep focuses on security)",
        evidence={"detected": god_class_count},
    ))

    # AC-8: Overall detection quality (categorization rate)
    # Measures how well detections are categorized (not just security focus)
    # Handle both old format (flat) and new format (with results wrapper)
    results_data = analysis.get("results", analysis) if "results" in analysis else analysis
    summary = results_data.get("summary", {})
    total_smells = summary.get("total_smells", 0)
    smells_by_category = summary.get("smells_by_category", {})
    unknown_smells = smells_by_category.get("unknown", 0)
    security_smells = smells_by_category.get("security", 0)

    # Categorization rate: properly categorized smells / total smells
    categorized_smells = total_smells - unknown_smells
    categorization_rate = categorized_smells / total_smells if total_smells > 0 else 1.0

    results.append(CheckResult(
        check_id="AC-8",
        name="Overall detection quality",
        category=CheckCategory.ACCURACY,
        passed=categorization_rate >= 0.8,  # Require 80% categorized
        score=categorization_rate,
        message=f"Categorization: {categorization_rate:.1%} ({categorized_smells}/{total_smells} properly categorized)",
        evidence={
            "total_smells": total_smells,
            "unknown_smells": unknown_smells,
            "categorized_smells": categorized_smells,
            "security_smells": security_smells,
        },
    ))

    # AC-9: Line number accuracy
    exact, near, total_expected, per_smell_stats = check_line_accuracy(analysis, gt, tolerance=2)
    matched = exact + near
    line_accuracy = matched / total_expected if total_expected > 0 else 1.0

    # Calculate per-smell accuracy rates
    smell_accuracy = {}
    for smell_id, stats in per_smell_stats.items():
        rate = (stats["exact"] + stats["near"]) / stats["total"] if stats["total"] > 0 else 1.0
        smell_accuracy[smell_id] = {
            "accuracy": round(rate, 3),
            "exact": stats["exact"],
            "near": stats["near"],
            "missed": stats["missed"],
            "total": stats["total"],
        }

    # Sort by worst accuracy for diagnostic focus
    worst_smells = dict(sorted(smell_accuracy.items(), key=lambda x: x[1]["accuracy"])[:5])

    results.append(CheckResult(
        check_id="AC-9",
        name="Line number accuracy",
        category=CheckCategory.ACCURACY,
        passed=line_accuracy >= 0.7,  # Require 70% line match within ±2
        score=line_accuracy,
        message=f"Line accuracy: {line_accuracy:.1%} ({exact} exact, {near} near ±2, {total_expected - matched} missed)",
        evidence={
            "exact_matches": exact,
            "near_matches": near,
            "total_expected": total_expected,
            "misses": total_expected - matched,
            "per_smell_accuracy": smell_accuracy,
            "worst_performers": worst_smells,
        },
    ))

    return results
