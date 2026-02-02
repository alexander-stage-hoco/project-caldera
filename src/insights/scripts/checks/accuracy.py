"""
Accuracy checks (IN-AC-*) for Insights reports.

These checks verify that reported metrics match source data.
"""

from typing import Any

from . import register_check, CheckOutput, CheckResult


@register_check(
    check_id="IN-AC-1",
    name="Total Files Accuracy",
    description="Verify total files count matches database",
    dimension="accuracy",
    weight=1.0,
)
def check_total_files_accuracy(
    report_data: dict[str, Any],
    db_data: dict[str, Any],
    **kwargs: Any,
) -> CheckOutput:
    """Check that reported total files matches database."""
    report_files = report_data.get("repo_health", {}).get("total_files", 0)
    db_files = db_data.get("total_files", 0)

    if db_files == 0:
        return CheckOutput(
            check_id="IN-AC-1",
            name="Total Files Accuracy",
            result=CheckResult.SKIP,
            score=1.0,
            message="No file data in database to compare",
        )

    if report_files == db_files:
        return CheckOutput(
            check_id="IN-AC-1",
            name="Total Files Accuracy",
            result=CheckResult.PASS,
            score=1.0,
            message=f"Total files match: {report_files}",
        )

    # Calculate accuracy as 1 - (error / expected)
    error_pct = abs(report_files - db_files) / db_files
    score = max(0.0, 1.0 - error_pct)

    return CheckOutput(
        check_id="IN-AC-1",
        name="Total Files Accuracy",
        result=CheckResult.FAIL if error_pct > 0.01 else CheckResult.PASS,
        score=score,
        message=f"Report: {report_files}, Database: {db_files} (error: {error_pct:.1%})",
        details={"report_value": report_files, "db_value": db_files, "error_pct": error_pct},
    )


@register_check(
    check_id="IN-AC-2",
    name="Total LOC Accuracy",
    description="Verify total lines of code matches database",
    dimension="accuracy",
    weight=1.0,
)
def check_total_loc_accuracy(
    report_data: dict[str, Any],
    db_data: dict[str, Any],
    **kwargs: Any,
) -> CheckOutput:
    """Check that reported total LOC matches database."""
    report_loc = report_data.get("repo_health", {}).get("total_loc", 0)
    db_loc = db_data.get("total_loc", 0)

    if db_loc == 0:
        return CheckOutput(
            check_id="IN-AC-2",
            name="Total LOC Accuracy",
            result=CheckResult.SKIP,
            score=1.0,
            message="No LOC data in database to compare",
        )

    if report_loc == db_loc:
        return CheckOutput(
            check_id="IN-AC-2",
            name="Total LOC Accuracy",
            result=CheckResult.PASS,
            score=1.0,
            message=f"Total LOC match: {report_loc}",
        )

    error_pct = abs(report_loc - db_loc) / db_loc
    score = max(0.0, 1.0 - error_pct)

    return CheckOutput(
        check_id="IN-AC-2",
        name="Total LOC Accuracy",
        result=CheckResult.FAIL if error_pct > 0.01 else CheckResult.PASS,
        score=score,
        message=f"Report: {report_loc}, Database: {db_loc} (error: {error_pct:.1%})",
        details={"report_value": report_loc, "db_value": db_loc, "error_pct": error_pct},
    )


@register_check(
    check_id="IN-AC-3",
    name="Hotspot Count Accuracy",
    description="Verify hotspot counts match database queries",
    dimension="accuracy",
    weight=0.8,
)
def check_hotspot_count_accuracy(
    report_data: dict[str, Any],
    db_data: dict[str, Any],
    **kwargs: Any,
) -> CheckOutput:
    """Check that hotspot counts are accurate."""
    report_hotspots = len(report_data.get("file_hotspots", {}).get("complexity_hotspots", []))
    db_hotspots = db_data.get("complexity_hotspot_count", 0)

    if db_hotspots == 0:
        return CheckOutput(
            check_id="IN-AC-3",
            name="Hotspot Count Accuracy",
            result=CheckResult.SKIP,
            score=1.0,
            message="No hotspot data in database to compare",
        )

    # Hotspots may be limited, so check if report count <= db count
    if report_hotspots <= db_hotspots:
        return CheckOutput(
            check_id="IN-AC-3",
            name="Hotspot Count Accuracy",
            result=CheckResult.PASS,
            score=1.0,
            message=f"Report shows {report_hotspots} of {db_hotspots} hotspots",
        )

    return CheckOutput(
        check_id="IN-AC-3",
        name="Hotspot Count Accuracy",
        result=CheckResult.FAIL,
        score=0.5,
        message=f"Report shows {report_hotspots} but database has {db_hotspots}",
        details={"report_value": report_hotspots, "db_value": db_hotspots},
    )


@register_check(
    check_id="IN-AC-4",
    name="Vulnerability Count Accuracy",
    description="Verify vulnerability counts match database",
    dimension="accuracy",
    weight=1.0,
)
def check_vulnerability_count_accuracy(
    report_data: dict[str, Any],
    db_data: dict[str, Any],
    **kwargs: Any,
) -> CheckOutput:
    """Check that vulnerability counts are accurate."""
    report_vulns = report_data.get("vulnerabilities", {}).get("total_count", 0)
    db_vulns = db_data.get("total_vulnerabilities", 0)

    if db_vulns == 0 and report_vulns == 0:
        return CheckOutput(
            check_id="IN-AC-4",
            name="Vulnerability Count Accuracy",
            result=CheckResult.PASS,
            score=1.0,
            message="No vulnerabilities in either report or database",
        )

    if db_vulns == 0:
        return CheckOutput(
            check_id="IN-AC-4",
            name="Vulnerability Count Accuracy",
            result=CheckResult.SKIP,
            score=1.0,
            message="No vulnerability data in database to compare",
        )

    if report_vulns == db_vulns:
        return CheckOutput(
            check_id="IN-AC-4",
            name="Vulnerability Count Accuracy",
            result=CheckResult.PASS,
            score=1.0,
            message=f"Vulnerability count matches: {report_vulns}",
        )

    error_pct = abs(report_vulns - db_vulns) / db_vulns
    score = max(0.0, 1.0 - error_pct)

    return CheckOutput(
        check_id="IN-AC-4",
        name="Vulnerability Count Accuracy",
        result=CheckResult.FAIL if error_pct > 0.01 else CheckResult.PASS,
        score=score,
        message=f"Report: {report_vulns}, Database: {db_vulns}",
        details={"report_value": report_vulns, "db_value": db_vulns, "error_pct": error_pct},
    )


@register_check(
    check_id="IN-AC-5",
    name="Average Complexity Accuracy",
    description="Verify average complexity matches database",
    dimension="accuracy",
    weight=0.8,
)
def check_avg_complexity_accuracy(
    report_data: dict[str, Any],
    db_data: dict[str, Any],
    **kwargs: Any,
) -> CheckOutput:
    """Check that average complexity is accurate."""
    report_avg = report_data.get("repo_health", {}).get("avg_ccn")
    db_avg = db_data.get("avg_ccn")

    if db_avg is None or db_avg == 0:
        return CheckOutput(
            check_id="IN-AC-5",
            name="Average Complexity Accuracy",
            result=CheckResult.SKIP,
            score=1.0,
            message="No complexity data in database to compare",
        )

    if report_avg is None:
        return CheckOutput(
            check_id="IN-AC-5",
            name="Average Complexity Accuracy",
            result=CheckResult.FAIL,
            score=0.0,
            message="Report missing average complexity",
        )

    # Allow small floating point differences
    error_pct = abs(report_avg - db_avg) / db_avg if db_avg != 0 else 0
    score = max(0.0, 1.0 - error_pct)

    return CheckOutput(
        check_id="IN-AC-5",
        name="Average Complexity Accuracy",
        result=CheckResult.PASS if error_pct < 0.05 else CheckResult.FAIL,
        score=score,
        message=f"Report: {report_avg:.2f}, Database: {db_avg:.2f}",
        details={"report_value": report_avg, "db_value": db_avg, "error_pct": error_pct},
    )


@register_check(
    check_id="IN-AC-6",
    name="Severity Distribution Accuracy",
    description="Verify severity distribution matches database",
    dimension="accuracy",
    weight=0.8,
)
def check_severity_distribution_accuracy(
    report_data: dict[str, Any],
    db_data: dict[str, Any],
    **kwargs: Any,
) -> CheckOutput:
    """Check that severity distribution is accurate."""
    report_summary = report_data.get("vulnerabilities", {}).get("summary", [])
    db_summary = db_data.get("vulnerability_summary", [])

    if not db_summary:
        return CheckOutput(
            check_id="IN-AC-6",
            name="Severity Distribution Accuracy",
            result=CheckResult.SKIP,
            score=1.0,
            message="No severity distribution data in database",
        )

    # Build lookup dicts
    report_counts = {item.get("severity"): item.get("count", 0) for item in report_summary}
    db_counts = {item.get("severity"): item.get("count", 0) for item in db_summary}

    mismatches = []
    for severity in set(report_counts.keys()) | set(db_counts.keys()):
        report_count = report_counts.get(severity, 0)
        db_count = db_counts.get(severity, 0)
        if report_count != db_count:
            mismatches.append(f"{severity}: {report_count} vs {db_count}")

    if not mismatches:
        return CheckOutput(
            check_id="IN-AC-6",
            name="Severity Distribution Accuracy",
            result=CheckResult.PASS,
            score=1.0,
            message="Severity distribution matches",
        )

    score = 1.0 - (len(mismatches) / len(db_counts)) if db_counts else 0.0

    return CheckOutput(
        check_id="IN-AC-6",
        name="Severity Distribution Accuracy",
        result=CheckResult.FAIL,
        score=max(0.0, score),
        message=f"Mismatches: {', '.join(mismatches)}",
        details={"mismatches": mismatches},
    )


# Export list of checks for discovery
ACCURACY_CHECKS = [
    "IN-AC-1",
    "IN-AC-2",
    "IN-AC-3",
    "IN-AC-4",
    "IN-AC-5",
    "IN-AC-6",
]
