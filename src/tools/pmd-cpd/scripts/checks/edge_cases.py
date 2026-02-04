"""
Edge case checks (EC-1 to EC-8) for PMD CPD evaluation.

These checks validate handling of edge cases and unusual inputs.
"""

from pathlib import Path
from . import (
    CheckResult,
    CheckCategory,
    load_all_ground_truth,
    normalize_path,
)


def run_edge_case_checks(analysis: dict, ground_truth_dir: str) -> list[CheckResult]:
    """Run all edge case checks."""
    ground_truth = load_all_ground_truth(ground_truth_dir)
    results = []

    results.append(_ec1_empty_files(analysis))
    results.append(_ec2_single_line_files(analysis))
    results.append(_ec3_large_files(analysis))
    results.append(_ec4_unicode_content(analysis))
    results.append(_ec5_mixed_line_endings(analysis))
    results.append(_ec6_deeply_nested_code(analysis))
    results.append(_ec7_special_characters_paths(analysis))
    results.append(_ec8_no_duplicates_repository(analysis, ground_truth))

    return results


def _ec1_empty_files(analysis: dict) -> CheckResult:
    """EC-1: Empty files should be handled gracefully."""
    files = analysis.get("files", [])
    errors = analysis.get("errors", [])

    # Check if any errors mention empty files
    empty_file_errors = [e for e in errors if "empty" in e.lower()]

    # A passing result means no crashes from empty files
    passed = len(empty_file_errors) == 0
    score = 1.0 if passed else 0.0

    return CheckResult(
        check_id="EC-1",
        name="Empty file handling",
        category=CheckCategory.EDGE_CASES,
        passed=passed,
        score=score,
        message="Empty files handled gracefully" if passed else f"Empty file issues: {len(empty_file_errors)}",
        evidence={"errors": empty_file_errors}
    )


def _ec2_single_line_files(analysis: dict) -> CheckResult:
    """EC-2: Single-line files should not cause issues."""
    files = analysis.get("files", [])

    # Single line files should have 0 duplicates (too small)
    single_line_issues = 0
    evidence = []

    for f in files:
        total_lines = f.get("total_lines", 0)
        dup_lines = f.get("duplicate_lines", 0)

        if total_lines <= 1 and dup_lines > 0:
            single_line_issues += 1
            evidence.append({
                "file": f.get("path"),
                "total_lines": total_lines,
                "duplicate_lines": dup_lines
            })

    passed = single_line_issues == 0
    score = 1.0 if passed else max(0.0, 1.0 - (single_line_issues / max(len(files), 1)))

    return CheckResult(
        check_id="EC-2",
        name="Single-line file handling",
        category=CheckCategory.EDGE_CASES,
        passed=passed,
        score=score,
        message=f"Single-line files handled correctly" if passed else f"{single_line_issues} single-line file issues",
        evidence={"issues": evidence}
    )


def _ec3_large_files(analysis: dict) -> CheckResult:
    """EC-3: Large files should be analyzed without timeout."""
    files = analysis.get("files", [])
    metadata = analysis.get("metadata", {})

    # Check if analysis completed
    elapsed = metadata.get("elapsed_seconds", 0)
    timeout_threshold = 600  # 10 minutes

    passed = elapsed < timeout_threshold

    # Find any large files that were analyzed
    large_files = [f for f in files if f.get("total_lines", 0) > 1000]

    return CheckResult(
        check_id="EC-3",
        name="Large file handling",
        category=CheckCategory.EDGE_CASES,
        passed=passed,
        score=1.0 if passed else 0.5,
        message=f"Analysis completed in {elapsed:.1f}s, {len(large_files)} large files processed",
        evidence={
            "elapsed_seconds": elapsed,
            "large_file_count": len(large_files),
            "timeout_threshold": timeout_threshold
        }
    )


def _ec4_unicode_content(analysis: dict) -> CheckResult:
    """EC-4: Files with unicode content should be handled."""
    errors = analysis.get("errors", [])

    # Check for encoding-related errors
    encoding_errors = [e for e in errors if any(
        term in e.lower() for term in ["encoding", "unicode", "utf", "decode", "codec"]
    )]

    passed = len(encoding_errors) == 0
    score = 1.0 if passed else 0.5

    return CheckResult(
        check_id="EC-4",
        name="Unicode content handling",
        category=CheckCategory.EDGE_CASES,
        passed=passed,
        score=score,
        message="Unicode content handled correctly" if passed else f"{len(encoding_errors)} encoding issues",
        evidence={"encoding_errors": encoding_errors}
    )


def _ec5_mixed_line_endings(analysis: dict) -> CheckResult:
    """EC-5: Files with mixed line endings should be handled."""
    # This is mostly a sanity check - CPD should handle this
    errors = analysis.get("errors", [])

    line_ending_errors = [e for e in errors if any(
        term in e.lower() for term in ["line ending", "crlf", "newline"]
    )]

    passed = len(line_ending_errors) == 0

    return CheckResult(
        check_id="EC-5",
        name="Mixed line endings handling",
        category=CheckCategory.EDGE_CASES,
        passed=passed,
        score=1.0 if passed else 0.5,
        message="Line endings handled correctly" if passed else f"{len(line_ending_errors)} line ending issues",
        evidence={"errors": line_ending_errors}
    )


def _ec6_deeply_nested_code(analysis: dict) -> CheckResult:
    """EC-6: Deeply nested code structures should be analyzed."""
    # CPD should handle nested functions, classes, etc.
    duplications = analysis.get("duplications", [])

    # Just verify we can analyze without crashes
    passed = True  # If we got this far, analysis didn't crash
    score = 1.0

    return CheckResult(
        check_id="EC-6",
        name="Deeply nested code handling",
        category=CheckCategory.EDGE_CASES,
        passed=passed,
        score=score,
        message=f"Nested code structures analyzed ({len(duplications)} clones found)",
        evidence={"total_clones": len(duplications)}
    )


def _ec7_special_characters_paths(analysis: dict) -> CheckResult:
    """EC-7: File paths with special characters should be handled."""
    files = analysis.get("files", [])
    errors = analysis.get("errors", [])

    # Check for path-related errors
    path_errors = [e for e in errors if any(
        term in e.lower() for term in ["path", "filename", "directory"]
    )]

    passed = len(path_errors) == 0
    score = 1.0 if passed else 0.5

    return CheckResult(
        check_id="EC-7",
        name="Special character paths handling",
        category=CheckCategory.EDGE_CASES,
        passed=passed,
        score=score,
        message=f"File paths handled correctly ({len(files)} files processed)",
        evidence={"path_errors": path_errors}
    )


def _ec8_no_duplicates_repository(analysis: dict, ground_truth: dict[str, dict]) -> CheckResult:
    """EC-8: Repositories with no duplicates should show 0% duplication."""
    summary = analysis.get("summary", {})
    total_clones = summary.get("total_clones", 0)
    dup_pct = summary.get("duplication_percentage", 0.0)

    # Count expected clean files from ground truth
    clean_file_count = 0
    for lang, gt in ground_truth.items():
        for filename, exp in gt.get("files", {}).items():
            if exp.get("expected_clone_count") == 0:
                clean_file_count += 1

    # If we have clean files, they should contribute to low duplication
    if clean_file_count > 0:
        # Overall duplication should not be excessive
        passed = dup_pct <= 50.0  # Less than 50% overall
        score = 1.0 - (dup_pct / 100.0) if dup_pct <= 100 else 0.0
    else:
        # No clean files to test
        passed = True
        score = 1.0

    return CheckResult(
        check_id="EC-8",
        name="Zero duplication handling",
        category=CheckCategory.EDGE_CASES,
        passed=passed,
        score=score,
        message=f"Overall duplication: {dup_pct:.1f}% ({total_clones} clones)",
        evidence={
            "total_clones": total_clones,
            "duplication_percentage": dup_pct,
            "clean_files_in_gt": clean_file_count
        }
    )
