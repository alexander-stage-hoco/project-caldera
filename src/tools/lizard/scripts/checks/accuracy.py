"""Accuracy checks for Lizard function analysis (AC-1 to AC-8).

These checks validate that Lizard correctly calculates CCN, NLOC, parameter
counts, and line ranges compared to ground truth.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from . import (
    CheckCategory,
    CheckResult,
    CheckSeverity,
    create_check_result,
    create_partial_check_result,
)


def load_ground_truth(ground_truth_path: Path) -> Dict[str, Any]:
    """Load ground truth JSON file."""
    with open(ground_truth_path) as f:
        return json.load(f)


def load_analysis(analysis_path: Path) -> Dict[str, Any]:
    """Load analysis JSON file."""
    with open(analysis_path) as f:
        return json.load(f)


def _get_functions_by_ccn_range(
    ground_truth: Dict[str, Any], min_ccn: int, max_ccn: int
) -> List[Tuple[str, str, Dict[str, Any]]]:
    """Get functions within a CCN range from ground truth.

    Returns list of (filename, function_name, function_data) tuples.
    """
    results = []
    for filename, file_data in ground_truth.get("files", {}).items():
        for func_name, func_data in file_data.get("functions", {}).items():
            ccn = func_data.get("ccn", 0)
            if min_ccn <= ccn <= max_ccn:
                results.append((filename, func_name, func_data))
    return results


def _find_function_in_analysis(
    analysis: Dict[str, Any], filename: str, func_name: str, expected_ccn: int | None = None
) -> Dict[str, Any] | None:
    """Find a function in analysis results by filename and function name.

    If expected_ccn is provided and there are multiple matches, returns
    the one closest to the expected CCN (handles duplicate function names).
    """
    candidates = []
    for file_data in analysis.get("files", []):
        # Check if filename matches (may be partial path)
        file_path = file_data.get("path", "")
        if filename in file_path or file_path.endswith(filename):
            for func in file_data.get("functions", []):
                # Match by function name (handle qualified names)
                analysis_name = func.get("name", "")
                if analysis_name == func_name or analysis_name.endswith(f".{func_name}"):
                    candidates.append(func)

    if not candidates:
        return None

    # If only one match or no expected CCN, return first
    if len(candidates) == 1 or expected_ccn is None:
        return candidates[0]

    # Multiple matches with expected CCN - return closest match
    return min(candidates, key=lambda f: abs(f.get("ccn", 0) - expected_ccn))


def check_ac1_simple_functions(
    analysis: Dict[str, Any], ground_truth: Dict[str, Any]
) -> CheckResult:
    """AC-1: Simple functions should have CCN=1.

    Validates that functions with expected CCN=1 in ground truth
    are correctly identified by Lizard.
    """
    simple_functions = _get_functions_by_ccn_range(ground_truth, 1, 1)

    if not simple_functions:
        return create_check_result(
            check_id="AC-1",
            name="Simple functions CCN=1",
            category=CheckCategory.ACCURACY,
            severity=CheckSeverity.CRITICAL,
            passed=True,
            message="No simple functions (CCN=1) in ground truth to validate",
            evidence={"simple_function_count": 0},
        )

    correct = 0
    incorrect = []

    for filename, func_name, gt_data in simple_functions:
        analysis_func = _find_function_in_analysis(analysis, filename, func_name, expected_ccn=1)
        if analysis_func:
            if analysis_func.get("ccn") == 1:
                correct += 1
            else:
                incorrect.append({
                    "file": filename,
                    "function": func_name,
                    "expected_ccn": 1,
                    "actual_ccn": analysis_func.get("ccn"),
                })
        else:
            incorrect.append({
                "file": filename,
                "function": func_name,
                "expected_ccn": 1,
                "actual_ccn": "NOT FOUND",
            })

    total = len(simple_functions)
    score = correct / total if total > 0 else 0.0

    return create_partial_check_result(
        check_id="AC-1",
        name="Simple functions CCN=1",
        category=CheckCategory.ACCURACY,
        severity=CheckSeverity.CRITICAL,
        score=score,
        message=f"{correct}/{total} simple functions correctly identified with CCN=1",
        evidence={
            "correct": correct,
            "total": total,
            "incorrect_functions": incorrect[:10],  # Limit to first 10
        },
    )


def check_ac2_complex_functions(
    analysis: Dict[str, Any], ground_truth: Dict[str, Any]
) -> CheckResult:
    """AC-2: Complex functions should have CCN 10-20.

    Validates that Lizard correctly calculates CCN for moderately
    complex functions.
    """
    complex_functions = _get_functions_by_ccn_range(ground_truth, 10, 20)

    if not complex_functions:
        return create_check_result(
            check_id="AC-2",
            name="Complex functions CCN 10-20",
            category=CheckCategory.ACCURACY,
            severity=CheckSeverity.HIGH,
            passed=True,
            message="No complex functions (CCN 10-20) in ground truth to validate",
            evidence={"complex_function_count": 0},
        )

    correct = 0
    close = 0  # Within tolerance
    incorrect = []
    tolerance = 2  # Allow CCN to be off by 2

    for filename, func_name, gt_data in complex_functions:
        expected_ccn = gt_data.get("ccn")
        analysis_func = _find_function_in_analysis(analysis, filename, func_name, expected_ccn=expected_ccn)

        if analysis_func:
            actual_ccn = analysis_func.get("ccn")
            if actual_ccn == expected_ccn:
                correct += 1
            elif abs(actual_ccn - expected_ccn) <= tolerance:
                close += 1
            else:
                incorrect.append({
                    "file": filename,
                    "function": func_name,
                    "expected_ccn": expected_ccn,
                    "actual_ccn": actual_ccn,
                    "diff": actual_ccn - expected_ccn,
                })
        else:
            incorrect.append({
                "file": filename,
                "function": func_name,
                "expected_ccn": expected_ccn,
                "actual_ccn": "NOT FOUND",
            })

    total = len(complex_functions)
    # Score: exact match = 1.0, within tolerance = 0.8, otherwise 0
    score = (correct + close * 0.8) / total if total > 0 else 0.0

    return create_partial_check_result(
        check_id="AC-2",
        name="Complex functions CCN 10-20",
        category=CheckCategory.ACCURACY,
        severity=CheckSeverity.HIGH,
        score=score,
        message=f"{correct} exact, {close} close (±{tolerance}), {len(incorrect)} incorrect out of {total} complex functions",
        evidence={
            "exact_matches": correct,
            "close_matches": close,
            "total": total,
            "tolerance": tolerance,
            "incorrect_functions": incorrect[:10],
        },
    )


def check_ac3_massive_functions(
    analysis: Dict[str, Any], ground_truth: Dict[str, Any]
) -> CheckResult:
    """AC-3: Massive functions should have CCN >= 20.

    Validates that Lizard correctly identifies high-complexity functions.
    """
    massive_functions = _get_functions_by_ccn_range(ground_truth, 20, 100)

    if not massive_functions:
        return create_check_result(
            check_id="AC-3",
            name="Massive functions CCN >= 20",
            category=CheckCategory.ACCURACY,
            severity=CheckSeverity.HIGH,
            passed=True,
            message="No massive functions (CCN >= 20) in ground truth to validate",
            evidence={"massive_function_count": 0},
        )

    correct = 0
    close = 0
    incorrect = []
    tolerance = 3  # Allow more tolerance for high CCN

    for filename, func_name, gt_data in massive_functions:
        expected_ccn = gt_data.get("ccn")
        analysis_func = _find_function_in_analysis(analysis, filename, func_name, expected_ccn=expected_ccn)

        if analysis_func:
            actual_ccn = analysis_func.get("ccn")
            if actual_ccn == expected_ccn:
                correct += 1
            elif abs(actual_ccn - expected_ccn) <= tolerance:
                close += 1
            else:
                incorrect.append({
                    "file": filename,
                    "function": func_name,
                    "expected_ccn": expected_ccn,
                    "actual_ccn": actual_ccn,
                    "diff": actual_ccn - expected_ccn,
                })
        else:
            incorrect.append({
                "file": filename,
                "function": func_name,
                "expected_ccn": expected_ccn,
                "actual_ccn": "NOT FOUND",
            })

    total = len(massive_functions)
    score = (correct + close * 0.8) / total if total > 0 else 0.0

    return create_partial_check_result(
        check_id="AC-3",
        name="Massive functions CCN >= 20",
        category=CheckCategory.ACCURACY,
        severity=CheckSeverity.HIGH,
        score=score,
        message=f"{correct} exact, {close} close (±{tolerance}), {len(incorrect)} incorrect out of {total} massive functions",
        evidence={
            "exact_matches": correct,
            "close_matches": close,
            "total": total,
            "tolerance": tolerance,
            "incorrect_functions": incorrect[:10],
        },
    )


def check_ac4_function_count(
    analysis: Dict[str, Any], ground_truth: Dict[str, Any]
) -> CheckResult:
    """AC-4: Function count should match expected per file.

    Validates that Lizard detects the expected number of functions in each file.
    """
    file_results = []
    total_expected = 0
    total_actual = 0

    for filename, gt_file_data in ground_truth.get("files", {}).items():
        expected_count = gt_file_data.get("expected_functions", 0)
        total_expected += expected_count

        # Find file in analysis
        actual_count = 0
        for analysis_file in analysis.get("files", []):
            file_path = analysis_file.get("path", "")
            if filename in file_path or file_path.endswith(filename):
                actual_count = analysis_file.get("function_count", len(analysis_file.get("functions", [])))
                break

        total_actual += actual_count

        if expected_count != actual_count:
            file_results.append({
                "file": filename,
                "expected": expected_count,
                "actual": actual_count,
                "diff": actual_count - expected_count,
            })

    # Calculate score based on how close total counts are
    if total_expected > 0:
        score = min(total_actual, total_expected) / max(total_actual, total_expected)
    else:
        score = 1.0 if total_actual == 0 else 0.0

    files_with_mismatch = len(file_results)
    total_files = len(ground_truth.get("files", {}))

    return create_partial_check_result(
        check_id="AC-4",
        name="Function count matches expected",
        category=CheckCategory.ACCURACY,
        severity=CheckSeverity.CRITICAL,
        score=score,
        message=f"{total_actual}/{total_expected} functions detected ({files_with_mismatch}/{total_files} files with count mismatch)",
        evidence={
            "total_expected": total_expected,
            "total_actual": total_actual,
            "files_with_mismatch": file_results[:10],
        },
    )


def check_ac5_nloc_accuracy(
    analysis: Dict[str, Any], ground_truth: Dict[str, Any]
) -> CheckResult:
    """AC-5: NLOC should be accurate within 10% tolerance.

    Validates that Lizard's NLOC calculation is reasonably accurate.
    """
    comparisons = []
    within_tolerance = 0
    tolerance_pct = 0.10  # 10%

    for filename, gt_file_data in ground_truth.get("files", {}).items():
        for func_name, gt_func in gt_file_data.get("functions", {}).items():
            expected_nloc = gt_func.get("nloc")
            if expected_nloc is None:
                continue

            analysis_func = _find_function_in_analysis(analysis, filename, func_name)
            if analysis_func:
                actual_nloc = analysis_func.get("nloc")
                if actual_nloc is not None:
                    tolerance = max(1, int(expected_nloc * tolerance_pct))
                    diff = abs(actual_nloc - expected_nloc)
                    is_within = diff <= tolerance

                    if is_within:
                        within_tolerance += 1
                    else:
                        comparisons.append({
                            "file": filename,
                            "function": func_name,
                            "expected_nloc": expected_nloc,
                            "actual_nloc": actual_nloc,
                            "diff": diff,
                        })

    total = within_tolerance + len(comparisons)
    score = within_tolerance / total if total > 0 else 1.0

    return create_partial_check_result(
        check_id="AC-5",
        name="NLOC accuracy within 10%",
        category=CheckCategory.ACCURACY,
        severity=CheckSeverity.MEDIUM,
        score=score,
        message=f"{within_tolerance}/{total} functions with NLOC within 10% tolerance",
        evidence={
            "within_tolerance": within_tolerance,
            "total": total,
            "tolerance_pct": tolerance_pct,
            "outliers": comparisons[:10],
        },
    )


def check_ac6_parameter_count(
    analysis: Dict[str, Any], ground_truth: Dict[str, Any]
) -> CheckResult:
    """AC-6: Parameter count should match exactly.

    Validates that Lizard correctly counts function parameters.
    """
    correct = 0
    incorrect = []

    for filename, gt_file_data in ground_truth.get("files", {}).items():
        for func_name, gt_func in gt_file_data.get("functions", {}).items():
            expected_params = gt_func.get("params")
            if expected_params is None:
                continue

            analysis_func = _find_function_in_analysis(analysis, filename, func_name)
            if analysis_func:
                actual_params = analysis_func.get("parameter_count")
                if actual_params is not None:
                    if actual_params == expected_params:
                        correct += 1
                    else:
                        incorrect.append({
                            "file": filename,
                            "function": func_name,
                            "expected_params": expected_params,
                            "actual_params": actual_params,
                        })

    total = correct + len(incorrect)
    score = correct / total if total > 0 else 1.0

    return create_partial_check_result(
        check_id="AC-6",
        name="Parameter count accuracy",
        category=CheckCategory.ACCURACY,
        severity=CheckSeverity.MEDIUM,
        score=score,
        message=f"{correct}/{total} functions with correct parameter count",
        evidence={
            "correct": correct,
            "total": total,
            "incorrect_functions": incorrect[:10],
        },
    )


def check_ac7_line_range(
    analysis: Dict[str, Any], ground_truth: Dict[str, Any]
) -> CheckResult:
    """AC-7: Start/end line ranges should be accurate.

    Validates that Lizard correctly identifies function boundaries.
    """
    correct_start = 0
    correct_end = 0
    incorrect = []
    total = 0

    for filename, gt_file_data in ground_truth.get("files", {}).items():
        for func_name, gt_func in gt_file_data.get("functions", {}).items():
            expected_start = gt_func.get("start_line")
            expected_end = gt_func.get("end_line")
            if expected_start is None or expected_end is None:
                continue

            total += 1
            analysis_func = _find_function_in_analysis(analysis, filename, func_name)

            if analysis_func:
                actual_start = analysis_func.get("start_line")
                actual_end = analysis_func.get("end_line")

                start_match = actual_start == expected_start
                end_match = actual_end == expected_end

                if start_match:
                    correct_start += 1
                if end_match:
                    correct_end += 1

                if not (start_match and end_match):
                    incorrect.append({
                        "file": filename,
                        "function": func_name,
                        "expected_start": expected_start,
                        "actual_start": actual_start,
                        "expected_end": expected_end,
                        "actual_end": actual_end,
                    })

    # Score based on both start and end accuracy
    if total > 0:
        score = (correct_start + correct_end) / (2 * total)
    else:
        score = 1.0

    return create_partial_check_result(
        check_id="AC-7",
        name="Line range accuracy",
        category=CheckCategory.ACCURACY,
        severity=CheckSeverity.LOW,
        score=score,
        message=f"Start: {correct_start}/{total}, End: {correct_end}/{total} correct line ranges",
        evidence={
            "correct_start": correct_start,
            "correct_end": correct_end,
            "total": total,
            "incorrect_ranges": incorrect[:10],
        },
    )


def check_ac8_nested_functions(
    analysis: Dict[str, Any], ground_truth: Dict[str, Any]
) -> CheckResult:
    """AC-8: Nested/inner functions should be detected.

    Validates that Lizard detects nested functions, closures, and inner functions.
    This is language-dependent behavior.
    """
    # Look for functions that might be nested based on naming patterns
    # Common patterns: outer.inner, Class.method, module.function
    nested_detected = []

    for file_data in analysis.get("files", []):
        for func in file_data.get("functions", []):
            name = func.get("name", "")
            long_name = func.get("long_name", "")

            # Detect qualified names (likely nested or methods)
            if "." in name or "::" in name:
                nested_detected.append({
                    "file": file_data.get("path", ""),
                    "name": name,
                    "long_name": long_name,
                    "ccn": func.get("ccn"),
                })

    # Also check for anonymous functions
    anonymous_count = 0
    for file_data in analysis.get("files", []):
        for func in file_data.get("functions", []):
            name = func.get("name", "")
            if "(anonymous)" in name or "lambda" in name.lower():
                anonymous_count += 1

    # This check passes if we detect any nested/qualified functions
    # (indicates Lizard is parsing complex structures)
    has_nested = len(nested_detected) > 0 or anonymous_count > 0

    return create_check_result(
        check_id="AC-8",
        name="Nested function detection",
        category=CheckCategory.ACCURACY,
        severity=CheckSeverity.MEDIUM,
        passed=has_nested,
        message=f"Detected {len(nested_detected)} qualified functions, {anonymous_count} anonymous functions",
        evidence={
            "qualified_functions_count": len(nested_detected),
            "anonymous_function_count": anonymous_count,
            "qualified_functions": nested_detected[:10],
        },
    )


def run_accuracy_checks(
    analysis: Dict[str, Any], ground_truth: Dict[str, Any]
) -> List[CheckResult]:
    """Run all accuracy checks.

    Args:
        analysis: Parsed analysis JSON
        ground_truth: Parsed ground truth JSON

    Returns:
        List of CheckResult objects
    """
    return [
        check_ac1_simple_functions(analysis, ground_truth),
        check_ac2_complex_functions(analysis, ground_truth),
        check_ac3_massive_functions(analysis, ground_truth),
        check_ac4_function_count(analysis, ground_truth),
        check_ac5_nloc_accuracy(analysis, ground_truth),
        check_ac6_parameter_count(analysis, ground_truth),
        check_ac7_line_range(analysis, ground_truth),
        check_ac8_nested_functions(analysis, ground_truth),
    ]
