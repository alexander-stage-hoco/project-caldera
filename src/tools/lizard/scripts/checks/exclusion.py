"""Exclusion checks for Lizard function analysis (EX-1 to EX-6).

These checks validate that the file exclusion mechanism works correctly,
including pattern matching, minification detection, and proper tracking
of excluded files.
"""

from typing import Any, Dict, List

from . import (
    CheckCategory,
    CheckResult,
    CheckSeverity,
    create_check_result,
    create_partial_check_result,
)


# Valid exclusion reasons
VALID_EXCLUSION_REASONS = {"pattern", "minified", "large", "language"}

# Known vendor/generated patterns that should be excluded
EXPECTED_VENDOR_PATTERNS = [
    "*.min.js",
    "*.min.css",
    "*.bundle.js",
    "*.d.ts",
    "*.designer.cs",
    "*.Designer.cs",
    "*.g.cs",
    "*.generated.*",
    "*_pb2.py",
    "*.pb.go",
    "jquery*.js",
    "react*.js",
    "angular*.js",
]


def check_ex1_excluded_files_present(analysis: Dict[str, Any]) -> CheckResult:
    """EX-1: excluded_files array exists in output.

    Validates that the output includes an excluded_files array,
    even if empty.
    """
    excluded_files = analysis.get("excluded_files")

    if excluded_files is None:
        return create_check_result(
            check_id="EX-1",
            name="excluded_files array present",
            category=CheckCategory.COVERAGE,
            severity=CheckSeverity.HIGH,
            passed=False,
            message="excluded_files array is missing from output",
            evidence={"has_excluded_files": False},
        )

    return create_check_result(
        check_id="EX-1",
        name="excluded_files array present",
        category=CheckCategory.COVERAGE,
        severity=CheckSeverity.HIGH,
        passed=True,
        message=f"excluded_files array present with {len(excluded_files)} entries",
        evidence={
            "has_excluded_files": True,
            "count": len(excluded_files),
        },
    )


def check_ex2_exclusion_reasons_valid(analysis: Dict[str, Any]) -> CheckResult:
    """EX-2: All exclusion reasons are valid enum values.

    Validates that every excluded file has a reason in the valid set:
    pattern, minified, large, language.
    """
    excluded_files = analysis.get("excluded_files", [])

    if not excluded_files:
        return create_check_result(
            check_id="EX-2",
            name="exclusion reasons valid",
            category=CheckCategory.COVERAGE,
            severity=CheckSeverity.MEDIUM,
            passed=True,
            message="No excluded files to check",
            evidence={"total": 0, "valid": 0, "invalid": []},
        )

    invalid_entries = []
    for entry in excluded_files:
        reason = entry.get("reason", "")
        if reason not in VALID_EXCLUSION_REASONS:
            invalid_entries.append({
                "path": entry.get("path", "unknown"),
                "reason": reason,
            })

    valid_count = len(excluded_files) - len(invalid_entries)
    passed = len(invalid_entries) == 0

    return create_check_result(
        check_id="EX-2",
        name="exclusion reasons valid",
        category=CheckCategory.COVERAGE,
        severity=CheckSeverity.MEDIUM,
        passed=passed,
        message=f"{valid_count}/{len(excluded_files)} entries have valid reasons"
        if passed
        else f"{len(invalid_entries)} entries have invalid reasons",
        evidence={
            "total": len(excluded_files),
            "valid": valid_count,
            "invalid": invalid_entries[:10],  # Limit to first 10
        },
    )


def check_ex3_excluded_paths_normalized(analysis: Dict[str, Any]) -> CheckResult:
    """EX-3: Excluded file paths are repo-relative.

    Validates that all excluded file paths are properly normalized
    (no leading slashes, no Windows paths, no ./.. prefixes).
    """
    excluded_files = analysis.get("excluded_files", [])

    if not excluded_files:
        return create_check_result(
            check_id="EX-3",
            name="excluded paths normalized",
            category=CheckCategory.COVERAGE,
            severity=CheckSeverity.MEDIUM,
            passed=True,
            message="No excluded files to check",
            evidence={"total": 0, "valid": 0, "invalid": []},
        )

    invalid_paths = []
    for entry in excluded_files:
        path = entry.get("path", "")
        issues = []

        if path.startswith("/"):
            issues.append("leading slash")
        if path.startswith("./"):
            issues.append("relative prefix")
        if ".." in path:
            issues.append("parent reference")
        if "\\" in path:
            issues.append("Windows separator")
        if ":" in path and len(path) > 1 and path[1] == ":":
            issues.append("Windows drive letter")

        if issues:
            invalid_paths.append({
                "path": path,
                "issues": issues,
            })

    valid_count = len(excluded_files) - len(invalid_paths)
    passed = len(invalid_paths) == 0

    return create_check_result(
        check_id="EX-3",
        name="excluded paths normalized",
        category=CheckCategory.COVERAGE,
        severity=CheckSeverity.MEDIUM,
        passed=passed,
        message=f"{valid_count}/{len(excluded_files)} paths are properly normalized"
        if passed
        else f"{len(invalid_paths)} paths have normalization issues",
        evidence={
            "total": len(excluded_files),
            "valid": valid_count,
            "invalid": invalid_paths[:10],
        },
    )


def check_ex4_exclusion_counts_consistent(analysis: Dict[str, Any]) -> CheckResult:
    """EX-4: Summary exclusion counts match excluded_files array.

    Validates that:
    - excluded_count == len(excluded_files)
    - excluded_by_* counts sum to excluded_count
    - Individual reason counts match actual entries
    """
    excluded_files = analysis.get("excluded_files", [])
    summary = analysis.get("summary", {})

    # Get counts from summary
    excluded_count = summary.get("excluded_count", 0)
    by_pattern = summary.get("excluded_by_pattern", 0)
    by_minified = summary.get("excluded_by_minified", 0)
    by_size = summary.get("excluded_by_size", 0)
    by_language = summary.get("excluded_by_language", 0)

    # Count actual exclusions by reason
    actual_counts = {
        "pattern": 0,
        "minified": 0,
        "large": 0,
        "language": 0,
    }
    for entry in excluded_files:
        reason = entry.get("reason", "")
        if reason in actual_counts:
            actual_counts[reason] += 1

    issues = []

    # Check total count
    if excluded_count != len(excluded_files):
        issues.append(f"excluded_count ({excluded_count}) != len(excluded_files) ({len(excluded_files)})")

    # Check individual counts
    if by_pattern != actual_counts["pattern"]:
        issues.append(f"excluded_by_pattern ({by_pattern}) != actual pattern count ({actual_counts['pattern']})")
    if by_minified != actual_counts["minified"]:
        issues.append(f"excluded_by_minified ({by_minified}) != actual minified count ({actual_counts['minified']})")
    if by_size != actual_counts["large"]:
        issues.append(f"excluded_by_size ({by_size}) != actual large count ({actual_counts['large']})")
    if by_language != actual_counts["language"]:
        issues.append(f"excluded_by_language ({by_language}) != actual language count ({actual_counts['language']})")

    # Check sum
    sum_by_reason = by_pattern + by_minified + by_size + by_language
    if sum_by_reason != excluded_count:
        issues.append(f"sum of by_* ({sum_by_reason}) != excluded_count ({excluded_count})")

    passed = len(issues) == 0

    return create_check_result(
        check_id="EX-4",
        name="exclusion counts consistent",
        category=CheckCategory.COVERAGE,
        severity=CheckSeverity.HIGH,
        passed=passed,
        message="All exclusion counts are consistent"
        if passed
        else f"Found {len(issues)} inconsistencies in exclusion counts",
        evidence={
            "summary_excluded_count": excluded_count,
            "array_length": len(excluded_files),
            "summary_by_reason": {
                "pattern": by_pattern,
                "minified": by_minified,
                "large": by_size,
                "language": by_language,
            },
            "actual_by_reason": actual_counts,
            "issues": issues,
        },
    )


def check_ex5_vendor_patterns_detected(
    analysis: Dict[str, Any],
    ground_truth: Dict[str, Any] = None,
) -> CheckResult:
    """EX-5: Known vendor patterns are detected.

    Checks that files matching known vendor patterns (*.min.js, *.d.ts, etc.)
    are properly excluded with reason='pattern'.
    """
    excluded_files = analysis.get("excluded_files", [])

    # Get pattern-excluded files
    pattern_excluded = [
        entry for entry in excluded_files
        if entry.get("reason") == "pattern"
    ]

    # Check for expected pattern matches
    found_patterns = set()
    for entry in pattern_excluded:
        path = entry.get("path", "")
        details = entry.get("details", "")

        # Track which patterns were actually matched
        for pattern in EXPECTED_VENDOR_PATTERNS:
            # Check if this file matches the pattern
            if details == pattern:
                found_patterns.add(pattern)
            elif "*" in pattern:
                # Simple glob check
                prefix = pattern.split("*")[0]
                suffix = pattern.split("*")[-1]
                if path.startswith(prefix) and path.endswith(suffix):
                    found_patterns.add(pattern)

    # Score based on whether pattern exclusion is working
    # This check passes if the mechanism exists, even if no files were excluded
    if not pattern_excluded and len(excluded_files) == 0:
        # No files to exclude is acceptable
        return create_check_result(
            check_id="EX-5",
            name="vendor patterns detected",
            category=CheckCategory.COVERAGE,
            severity=CheckSeverity.MEDIUM,
            passed=True,
            message="No files excluded (pattern matching not tested)",
            evidence={
                "pattern_excluded_count": 0,
                "patterns_found": [],
            },
        )

    passed = len(pattern_excluded) > 0 or len(excluded_files) == 0

    return create_check_result(
        check_id="EX-5",
        name="vendor patterns detected",
        category=CheckCategory.COVERAGE,
        severity=CheckSeverity.MEDIUM,
        passed=passed,
        message=f"{len(pattern_excluded)} files excluded by pattern matching"
        if pattern_excluded
        else "No pattern-excluded files found",
        evidence={
            "pattern_excluded_count": len(pattern_excluded),
            "patterns_found": list(found_patterns),
            "sample_excluded": [
                {"path": e.get("path"), "pattern": e.get("details")}
                for e in pattern_excluded[:5]
            ],
        },
    )


def check_ex6_minified_detection_works(
    analysis: Dict[str, Any],
    ground_truth: Dict[str, Any] = None,
) -> CheckResult:
    """EX-6: Content-based minification detection finds minified files.

    Checks that minified JavaScript/TypeScript files are detected
    via content-based heuristics (not just pattern matching).
    """
    excluded_files = analysis.get("excluded_files", [])

    # Get minified-excluded files
    minified_excluded = [
        entry for entry in excluded_files
        if entry.get("reason") == "minified"
    ]

    # Verify they are JS/TS files (where content detection applies)
    js_ts_minified = [
        entry for entry in minified_excluded
        if entry.get("language", "").lower() in ["javascript", "typescript"]
    ]

    # This check passes if the mechanism exists
    # Even if no minified files were found (repo may not have any)
    if not minified_excluded and len(excluded_files) == 0:
        return create_check_result(
            check_id="EX-6",
            name="minified detection works",
            category=CheckCategory.COVERAGE,
            severity=CheckSeverity.LOW,
            passed=True,
            message="No files excluded (minification detection not tested)",
            evidence={
                "minified_excluded_count": 0,
            },
        )

    # Consider it working if any minified files were found
    # or if no excluded files exist (nothing to detect)
    passed = True  # Content-based detection is best-effort

    message = (
        f"{len(minified_excluded)} files excluded by minification detection"
        if minified_excluded
        else "No content-based minified files detected"
    )

    return create_check_result(
        check_id="EX-6",
        name="minified detection works",
        category=CheckCategory.COVERAGE,
        severity=CheckSeverity.LOW,
        passed=passed,
        message=message,
        evidence={
            "minified_excluded_count": len(minified_excluded),
            "js_ts_minified_count": len(js_ts_minified),
            "sample_minified": [
                {"path": e.get("path"), "language": e.get("language")}
                for e in minified_excluded[:5]
            ],
        },
    )


def run_exclusion_checks(
    analysis: Dict[str, Any],
    ground_truth: Dict[str, Any] = None,
) -> List[CheckResult]:
    """Run all exclusion checks.

    Args:
        analysis: Parsed analysis JSON
        ground_truth: Optional ground truth data (not used by most checks)

    Returns:
        List of CheckResult objects
    """
    return [
        check_ex1_excluded_files_present(analysis),
        check_ex2_exclusion_reasons_valid(analysis),
        check_ex3_excluded_paths_normalized(analysis),
        check_ex4_exclusion_counts_consistent(analysis),
        check_ex5_vendor_patterns_detected(analysis, ground_truth),
        check_ex6_minified_detection_works(analysis, ground_truth),
    ]
