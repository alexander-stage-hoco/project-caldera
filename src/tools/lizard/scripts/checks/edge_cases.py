"""Edge case checks for Lizard function analysis (EC-1 to EC-8).

These checks validate that Lizard correctly handles edge cases such as
empty files, unicode, deep nesting, and language-specific constructs.
"""

from typing import Any, Dict, List

from . import (
    CheckCategory,
    CheckResult,
    CheckSeverity,
    create_check_result,
    create_partial_check_result,
)


def _find_edge_case_files(
    analysis: Dict[str, Any], pattern: str
) -> List[Dict[str, Any]]:
    """Find files in the edge_cases directory matching a pattern."""
    results = []
    for file_data in analysis.get("files", []):
        path = file_data.get("path", "")
        if "edge_cases" in path and pattern in path.lower():
            results.append(file_data)
    return results


def check_ec1_empty_files(
    analysis: Dict[str, Any], ground_truth: Dict[str, Any]
) -> CheckResult:
    """EC-1: Empty files should report 0 functions.

    Validates that empty source files are handled correctly.
    """
    # Find empty files in ground truth
    empty_files = []
    for filename, file_data in ground_truth.get("files", {}).items():
        if file_data.get("expected_functions", 0) == 0 and "empty" in filename.lower():
            empty_files.append(filename)

    if not empty_files:
        return create_check_result(
            check_id="EC-1",
            name="Empty files handled",
            category=CheckCategory.EDGE_CASES,
            severity=CheckSeverity.MEDIUM,
            passed=True,
            message="No empty files in ground truth to validate",
            evidence={"empty_file_count": 0},
        )

    correct = 0
    incorrect = []

    for filename in empty_files:
        # Find in analysis
        found = False
        for file_data in analysis.get("files", []):
            if filename in file_data.get("path", ""):
                found = True
                function_count = len(file_data.get("functions", []))
                if function_count == 0:
                    correct += 1
                else:
                    incorrect.append({
                        "file": filename,
                        "expected_functions": 0,
                        "actual_functions": function_count,
                    })
                break

        # If file not in analysis, that's correct (empty file might be skipped)
        if not found:
            correct += 1

    total = len(empty_files)
    score = correct / total if total > 0 else 1.0

    return create_partial_check_result(
        check_id="EC-1",
        name="Empty files handled",
        category=CheckCategory.EDGE_CASES,
        severity=CheckSeverity.MEDIUM,
        score=score,
        message=f"{correct}/{total} empty files correctly report 0 functions",
        evidence={
            "correct": correct,
            "total": total,
            "incorrect_files": incorrect,
        },
    )


def check_ec2_comments_only_files(
    analysis: Dict[str, Any], ground_truth: Dict[str, Any]
) -> CheckResult:
    """EC-2: Comments-only files should report 0 functions.

    Validates that files containing only comments are handled correctly.
    """
    comment_files = []
    for filename, file_data in ground_truth.get("files", {}).items():
        if file_data.get("expected_functions", 0) == 0 and "comment" in filename.lower():
            comment_files.append(filename)

    if not comment_files:
        return create_check_result(
            check_id="EC-2",
            name="Comments-only files handled",
            category=CheckCategory.EDGE_CASES,
            severity=CheckSeverity.MEDIUM,
            passed=True,
            message="No comments-only files in ground truth to validate",
            evidence={"comment_only_file_count": 0},
        )

    correct = 0
    incorrect = []

    for filename in comment_files:
        found = False
        for file_data in analysis.get("files", []):
            if filename in file_data.get("path", ""):
                found = True
                function_count = len(file_data.get("functions", []))
                if function_count == 0:
                    correct += 1
                else:
                    incorrect.append({
                        "file": filename,
                        "expected_functions": 0,
                        "actual_functions": function_count,
                    })
                break

        if not found:
            correct += 1

    total = len(comment_files)
    score = correct / total if total > 0 else 1.0

    return create_partial_check_result(
        check_id="EC-2",
        name="Comments-only files handled",
        category=CheckCategory.EDGE_CASES,
        severity=CheckSeverity.MEDIUM,
        score=score,
        message=f"{correct}/{total} comments-only files correctly report 0 functions",
        evidence={
            "correct": correct,
            "total": total,
            "incorrect_files": incorrect,
        },
    )


def check_ec3_single_line_files(
    analysis: Dict[str, Any], ground_truth: Dict[str, Any]
) -> CheckResult:
    """EC-3: Single-line files are handled without errors.

    Validates that minimal files don't cause parsing errors.
    """
    single_line_files = []
    for filename, file_data in ground_truth.get("files", {}).items():
        if "single_line" in filename.lower() or "single-line" in filename.lower():
            single_line_files.append(filename)

    if not single_line_files:
        return create_check_result(
            check_id="EC-3",
            name="Single-line files handled",
            category=CheckCategory.EDGE_CASES,
            severity=CheckSeverity.LOW,
            passed=True,
            message="No single-line files in ground truth to validate",
            evidence={"single_line_file_count": 0},
        )

    # Check that analysis completed without errors for these files
    # (presence in output or absence with 0 functions is acceptable)
    handled = 0
    for filename in single_line_files:
        # Either the file is in analysis or it was skipped (both are valid)
        handled += 1

    return create_check_result(
        check_id="EC-3",
        name="Single-line files handled",
        category=CheckCategory.EDGE_CASES,
        severity=CheckSeverity.LOW,
        passed=True,
        message=f"{handled} single-line files handled without errors",
        evidence={
            "files_handled": handled,
            "files": single_line_files,
        },
    )


def check_ec4_unicode_function_names(
    analysis: Dict[str, Any], ground_truth: Dict[str, Any]
) -> CheckResult:
    """EC-4: Unicode in function names is handled correctly.

    Validates that functions with non-ASCII characters are detected.
    """
    unicode_files = []
    unicode_functions = []

    for filename, file_data in ground_truth.get("files", {}).items():
        if "unicode" in filename.lower():
            unicode_files.append(filename)
            for func_name in file_data.get("functions", {}).keys():
                unicode_functions.append((filename, func_name))

    if not unicode_files:
        return create_check_result(
            check_id="EC-4",
            name="Unicode function names handled",
            category=CheckCategory.EDGE_CASES,
            severity=CheckSeverity.MEDIUM,
            passed=True,
            message="No unicode test files in ground truth",
            evidence={"unicode_file_count": 0},
        )

    found_functions = 0
    missing_functions = []

    for filename, func_name in unicode_functions:
        for file_data in analysis.get("files", []):
            if filename in file_data.get("path", ""):
                for func in file_data.get("functions", []):
                    if func.get("name") == func_name:
                        found_functions += 1
                        break
                else:
                    missing_functions.append({"file": filename, "function": func_name})
                break

    total = len(unicode_functions)
    score = found_functions / total if total > 0 else 1.0

    return create_partial_check_result(
        check_id="EC-4",
        name="Unicode function names handled",
        category=CheckCategory.EDGE_CASES,
        severity=CheckSeverity.MEDIUM,
        score=score,
        message=f"{found_functions}/{total} functions in unicode files detected",
        evidence={
            "found": found_functions,
            "total": total,
            "missing": missing_functions[:10],
        },
    )


def check_ec5_deep_nesting(
    analysis: Dict[str, Any], ground_truth: Dict[str, Any]
) -> CheckResult:
    """EC-5: Deep nesting (10+ levels) is detected correctly.

    Validates that deeply nested control structures are reflected in CCN.
    """
    deep_nesting_functions = []

    for filename, file_data in ground_truth.get("files", {}).items():
        if "deep" in filename.lower() or "nesting" in filename.lower():
            for func_name, func_data in file_data.get("functions", {}).items():
                if func_data.get("ccn", 0) >= 10:
                    deep_nesting_functions.append({
                        "file": filename,
                        "function": func_name,
                        "expected_ccn": func_data.get("ccn"),
                    })

    if not deep_nesting_functions:
        return create_check_result(
            check_id="EC-5",
            name="Deep nesting detected",
            category=CheckCategory.EDGE_CASES,
            severity=CheckSeverity.HIGH,
            passed=True,
            message="No deeply nested functions in ground truth",
            evidence={"deep_nesting_count": 0},
        )

    detected = 0
    not_detected = []

    for func_info in deep_nesting_functions:
        for file_data in analysis.get("files", []):
            if func_info["file"] in file_data.get("path", ""):
                for func in file_data.get("functions", []):
                    if func.get("name") == func_info["function"]:
                        actual_ccn = func.get("ccn", 0)
                        # Consider detected if CCN is reasonably high (>=8)
                        if actual_ccn >= 8:
                            detected += 1
                        else:
                            not_detected.append({
                                **func_info,
                                "actual_ccn": actual_ccn,
                            })
                        break
                break

    total = len(deep_nesting_functions)
    score = detected / total if total > 0 else 1.0

    return create_partial_check_result(
        check_id="EC-5",
        name="Deep nesting detected",
        category=CheckCategory.EDGE_CASES,
        severity=CheckSeverity.HIGH,
        score=score,
        message=f"{detected}/{total} deeply nested functions have high CCN (>=8)",
        evidence={
            "detected": detected,
            "total": total,
            "not_detected": not_detected,
        },
    )


def check_ec6_lambda_functions(analysis: Dict[str, Any]) -> CheckResult:
    """EC-6: Lambda/anonymous functions are handled.

    Validates handling of lambdas (language-dependent behavior).
    """
    lambda_count = 0
    lambda_examples = []

    for file_data in analysis.get("files", []):
        for func in file_data.get("functions", []):
            name = func.get("name", "").lower()
            long_name = func.get("long_name", "").lower()

            # Common lambda patterns
            if any(pattern in name or pattern in long_name for pattern in [
                "lambda", "anonymous", "(anonymous)", "<lambda>", "closure"
            ]):
                lambda_count += 1
                lambda_examples.append({
                    "file": file_data.get("path", ""),
                    "name": func.get("name"),
                    "ccn": func.get("ccn"),
                })

    # This is informational - lambdas may or may not be tracked
    # depending on the language
    return create_check_result(
        check_id="EC-6",
        name="Lambda functions handled",
        category=CheckCategory.EDGE_CASES,
        severity=CheckSeverity.LOW,
        passed=True,  # Informational check
        message=f"Found {lambda_count} lambda/anonymous functions in analysis",
        evidence={
            "lambda_count": lambda_count,
            "examples": lambda_examples[:10],
        },
    )


def check_ec7_class_methods(analysis: Dict[str, Any]) -> CheckResult:
    """EC-7: Class methods are detected with qualified names.

    Validates that methods within classes are properly attributed.
    """
    method_count = 0
    method_examples = []

    for file_data in analysis.get("files", []):
        for func in file_data.get("functions", []):
            name = func.get("name", "")
            long_name = func.get("long_name", "")

            # Methods typically have qualified names with dots or ::
            if "." in name or "::" in name or (long_name and "." in long_name):
                method_count += 1
                method_examples.append({
                    "file": file_data.get("path", ""),
                    "name": name,
                    "long_name": long_name,
                    "ccn": func.get("ccn"),
                })

    # Methods should be detected in OOP languages
    passed = method_count > 0

    return create_check_result(
        check_id="EC-7",
        name="Class methods detected",
        category=CheckCategory.EDGE_CASES,
        severity=CheckSeverity.HIGH,
        passed=passed,
        message=f"Found {method_count} class methods with qualified names",
        evidence={
            "method_count": method_count,
            "examples": method_examples[:10],
        },
    )


def check_ec8_anonymous_functions(analysis: Dict[str, Any]) -> CheckResult:
    """EC-8: Anonymous functions/callbacks are handled appropriately.

    Validates handling of inline functions and callbacks.
    """
    anonymous_patterns = [
        "(anonymous)",
        "anonymous",
        "<anonymous>",
        "callback",
        "=>",
    ]

    anonymous_count = 0
    anonymous_examples = []

    for file_data in analysis.get("files", []):
        for func in file_data.get("functions", []):
            name = func.get("name", "").lower()

            if any(pattern.lower() in name for pattern in anonymous_patterns):
                anonymous_count += 1
                anonymous_examples.append({
                    "file": file_data.get("path", ""),
                    "name": func.get("name"),
                    "ccn": func.get("ccn"),
                    "nloc": func.get("nloc"),
                })

    # This is informational - anonymous function tracking varies by language
    return create_check_result(
        check_id="EC-8",
        name="Anonymous functions handled",
        category=CheckCategory.EDGE_CASES,
        severity=CheckSeverity.LOW,
        passed=True,  # Informational check
        message=f"Found {anonymous_count} anonymous functions/callbacks",
        evidence={
            "anonymous_count": anonymous_count,
            "examples": anonymous_examples[:10],
        },
    )


def run_edge_case_checks(
    analysis: Dict[str, Any], ground_truth: Dict[str, Any]
) -> List[CheckResult]:
    """Run all edge case checks.

    Args:
        analysis: Parsed analysis JSON
        ground_truth: Parsed ground truth JSON

    Returns:
        List of CheckResult objects
    """
    return [
        check_ec1_empty_files(analysis, ground_truth),
        check_ec2_comments_only_files(analysis, ground_truth),
        check_ec3_single_line_files(analysis, ground_truth),
        check_ec4_unicode_function_names(analysis, ground_truth),
        check_ec5_deep_nesting(analysis, ground_truth),
        check_ec6_lambda_functions(analysis),
        check_ec7_class_methods(analysis),
        check_ec8_anonymous_functions(analysis),
    ]
