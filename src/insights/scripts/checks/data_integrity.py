"""
Data integrity checks (IN-DI-*) for Insights reports.

These checks verify internal consistency of report data.
"""

from typing import Any

from . import register_check, CheckOutput, CheckResult


@register_check(
    check_id="IN-DI-1",
    name="File Counts Consistent",
    description="Verify file counts are internally consistent",
    dimension="data_integrity",
    weight=1.0,
)
def check_file_counts_consistent(
    report_data: dict[str, Any],
    **kwargs: Any,
) -> CheckOutput:
    """Check that file counts are internally consistent."""
    repo_health = report_data.get("repo_health", {})
    language_coverage = report_data.get("language_coverage", {})

    total_files = repo_health.get("total_files", 0)

    if not language_coverage or not total_files:
        return CheckOutput(
            check_id="IN-DI-1",
            name="File Counts Consistent",
            result=CheckResult.SKIP,
            score=1.0,
            message="Insufficient data for consistency check",
        )

    lang_total = language_coverage.get("total_files", 0)

    if total_files == lang_total:
        return CheckOutput(
            check_id="IN-DI-1",
            name="File Counts Consistent",
            result=CheckResult.PASS,
            score=1.0,
            message=f"File counts match: {total_files}",
        )

    # Allow some variance (language detection might miss some files)
    variance = abs(total_files - lang_total) / total_files if total_files > 0 else 1.0

    if variance <= 0.1:
        return CheckOutput(
            check_id="IN-DI-1",
            name="File Counts Consistent",
            result=CheckResult.PASS,
            score=0.9,
            message=f"File counts within tolerance: {total_files} vs {lang_total}",
        )

    return CheckOutput(
        check_id="IN-DI-1",
        name="File Counts Consistent",
        result=CheckResult.FAIL,
        score=max(0.0, 1.0 - variance),
        message=f"Inconsistent: repo_health={total_files}, language_coverage={lang_total}",
        details={"repo_health_files": total_files, "language_files": lang_total},
    )


@register_check(
    check_id="IN-DI-2",
    name="LOC Sums Consistent",
    description="Verify LOC sums match component totals",
    dimension="data_integrity",
    weight=1.0,
)
def check_loc_sums_consistent(
    report_data: dict[str, Any],
    **kwargs: Any,
) -> CheckOutput:
    """Check that LOC sums are internally consistent."""
    repo_health = report_data.get("repo_health", {})

    total_loc = repo_health.get("total_loc", 0)
    total_code = repo_health.get("total_code", 0)
    total_comment = repo_health.get("total_comment", 0)

    if not total_loc:
        return CheckOutput(
            check_id="IN-DI-2",
            name="LOC Sums Consistent",
            result=CheckResult.SKIP,
            score=1.0,
            message="No LOC data to validate",
        )

    # LOC should include code, comments, and blanks
    # We can't verify blanks without that data, but code + comments should be <= total_loc
    if total_code + total_comment <= total_loc:
        return CheckOutput(
            check_id="IN-DI-2",
            name="LOC Sums Consistent",
            result=CheckResult.PASS,
            score=1.0,
            message=f"LOC consistent: {total_code} code + {total_comment} comments <= {total_loc} total",
        )

    return CheckOutput(
        check_id="IN-DI-2",
        name="LOC Sums Consistent",
        result=CheckResult.FAIL,
        score=0.5,
        message=f"Inconsistent: code ({total_code}) + comments ({total_comment}) > total ({total_loc})",
        details={
            "total_loc": total_loc,
            "total_code": total_code,
            "total_comment": total_comment,
        },
    )


@register_check(
    check_id="IN-DI-3",
    name="Severity Counts Sum Correctly",
    description="Verify severity counts sum to total",
    dimension="data_integrity",
    weight=1.0,
)
def check_severity_sums(
    report_data: dict[str, Any],
    **kwargs: Any,
) -> CheckOutput:
    """Check that severity counts sum to total vulnerabilities."""
    vulns = report_data.get("vulnerabilities", {})
    summary = vulns.get("summary", [])
    total_count = vulns.get("total_count", 0)

    if not summary:
        return CheckOutput(
            check_id="IN-DI-3",
            name="Severity Counts Sum Correctly",
            result=CheckResult.SKIP,
            score=1.0,
            message="No severity data to validate",
        )

    summary_sum = sum(item.get("count", 0) for item in summary)

    if summary_sum == total_count:
        return CheckOutput(
            check_id="IN-DI-3",
            name="Severity Counts Sum Correctly",
            result=CheckResult.PASS,
            score=1.0,
            message=f"Severity counts sum correctly: {summary_sum}",
        )

    return CheckOutput(
        check_id="IN-DI-3",
        name="Severity Counts Sum Correctly",
        result=CheckResult.FAIL,
        score=0.5,
        message=f"Sum mismatch: severity counts ({summary_sum}) vs total ({total_count})",
        details={"summary_sum": summary_sum, "total_count": total_count},
    )


@register_check(
    check_id="IN-DI-4",
    name="Hotspots Sorted by Severity",
    description="Verify hotspots are sorted by complexity descending",
    dimension="data_integrity",
    weight=0.6,
)
def check_hotspots_sorted(
    report_data: dict[str, Any],
    **kwargs: Any,
) -> CheckOutput:
    """Check that hotspots are sorted by complexity descending."""
    file_hotspots = report_data.get("file_hotspots", {})
    complexity_hotspots = file_hotspots.get("complexity_hotspots", [])

    if len(complexity_hotspots) < 2:
        return CheckOutput(
            check_id="IN-DI-4",
            name="Hotspots Sorted by Severity",
            result=CheckResult.SKIP,
            score=1.0,
            message="Insufficient hotspots to check sorting",
        )

    complexities = [h.get("complexity", 0) for h in complexity_hotspots]
    is_sorted = all(complexities[i] >= complexities[i + 1] for i in range(len(complexities) - 1))

    if is_sorted:
        return CheckOutput(
            check_id="IN-DI-4",
            name="Hotspots Sorted by Severity",
            result=CheckResult.PASS,
            score=1.0,
            message=f"Hotspots correctly sorted ({len(complexity_hotspots)} items)",
        )

    # Count inversions
    inversions = sum(
        1 for i in range(len(complexities) - 1)
        if complexities[i] < complexities[i + 1]
    )
    score = 1.0 - (inversions / (len(complexities) - 1))

    return CheckOutput(
        check_id="IN-DI-4",
        name="Hotspots Sorted by Severity",
        result=CheckResult.FAIL,
        score=max(0.0, score),
        message=f"Hotspots not sorted: {inversions} inversions found",
        details={"inversions": inversions, "total_pairs": len(complexities) - 1},
    )


@register_check(
    check_id="IN-DI-5",
    name="No Duplicate Entries",
    description="Verify no duplicate file entries in hotspots",
    dimension="data_integrity",
    weight=0.8,
)
def check_no_duplicates(
    report_data: dict[str, Any],
    **kwargs: Any,
) -> CheckOutput:
    """Check that there are no duplicate file entries."""
    file_hotspots = report_data.get("file_hotspots", {})
    complexity_hotspots = file_hotspots.get("complexity_hotspots", [])

    if not complexity_hotspots:
        return CheckOutput(
            check_id="IN-DI-5",
            name="No Duplicate Entries",
            result=CheckResult.SKIP,
            score=1.0,
            message="No hotspots to check for duplicates",
        )

    paths = [h.get("relative_path") for h in complexity_hotspots]
    unique_paths = set(paths)
    duplicates = len(paths) - len(unique_paths)

    if duplicates == 0:
        return CheckOutput(
            check_id="IN-DI-5",
            name="No Duplicate Entries",
            result=CheckResult.PASS,
            score=1.0,
            message=f"All {len(paths)} entries are unique",
        )

    score = len(unique_paths) / len(paths)

    # Find which paths are duplicated
    from collections import Counter
    path_counts = Counter(paths)
    duplicated_paths = [p for p, c in path_counts.items() if c > 1]

    return CheckOutput(
        check_id="IN-DI-5",
        name="No Duplicate Entries",
        result=CheckResult.FAIL,
        score=score,
        message=f"{duplicates} duplicate entries found",
        details={"duplicated_paths": duplicated_paths[:5]},
    )


# Export list of checks
DATA_INTEGRITY_CHECKS = [
    "IN-DI-1",
    "IN-DI-2",
    "IN-DI-3",
    "IN-DI-4",
    "IN-DI-5",
]
