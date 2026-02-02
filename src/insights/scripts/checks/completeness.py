"""
Completeness checks (IN-CM-*) for Insights reports.

These checks verify that all required sections and fields are present.
"""

from typing import Any

from . import register_check, CheckOutput, CheckResult


REQUIRED_SECTIONS = [
    "repo_health",
    "file_hotspots",
    "vulnerabilities",
]

OPTIONAL_SECTIONS = [
    "directory_analysis",
    "cross_tool",
    "language_coverage",
]


@register_check(
    check_id="IN-CM-1",
    name="Required Sections Present",
    description="Verify all required sections are included",
    dimension="completeness",
    weight=1.0,
)
def check_required_sections(
    report_content: str,
    report_data: dict[str, Any],
    format: str = "html",
    **kwargs: Any,
) -> CheckOutput:
    """Check that all required sections are present."""
    # Check both report_data keys and HTML/MD content for section IDs
    present_sections = set(report_data.keys())

    # Also check content for section IDs
    if format == "html":
        for section in REQUIRED_SECTIONS:
            if f'id="{section}"' in report_content:
                present_sections.add(section)
    elif format == "md":
        for section in REQUIRED_SECTIONS:
            # Markdown sections typically use ## Section Title
            section_title = section.replace("_", " ").title()
            if f"## {section_title}" in report_content or f"# {section_title}" in report_content:
                present_sections.add(section)

    missing = set(REQUIRED_SECTIONS) - present_sections

    if not missing:
        return CheckOutput(
            check_id="IN-CM-1",
            name="Required Sections Present",
            result=CheckResult.PASS,
            score=1.0,
            message=f"All {len(REQUIRED_SECTIONS)} required sections present",
        )

    score = (len(REQUIRED_SECTIONS) - len(missing)) / len(REQUIRED_SECTIONS)

    return CheckOutput(
        check_id="IN-CM-1",
        name="Required Sections Present",
        result=CheckResult.FAIL,
        score=score,
        message=f"Missing sections: {', '.join(missing)}",
        details={"missing": list(missing), "present": list(present_sections)},
    )


@register_check(
    check_id="IN-CM-2",
    name="Repo Health Metrics Complete",
    description="Verify repo health section has all key metrics",
    dimension="completeness",
    weight=1.0,
)
def check_repo_health_complete(
    report_data: dict[str, Any],
    **kwargs: Any,
) -> CheckOutput:
    """Check that repo health section has required metrics."""
    required_fields = ["total_files", "total_loc", "total_code", "avg_ccn"]
    repo_health = report_data.get("repo_health", {})

    if not repo_health:
        return CheckOutput(
            check_id="IN-CM-2",
            name="Repo Health Metrics Complete",
            result=CheckResult.FAIL,
            score=0.0,
            message="Repo health section is empty",
        )

    present = [f for f in required_fields if repo_health.get(f) is not None]
    missing = [f for f in required_fields if repo_health.get(f) is None]

    if not missing:
        return CheckOutput(
            check_id="IN-CM-2",
            name="Repo Health Metrics Complete",
            result=CheckResult.PASS,
            score=1.0,
            message="All repo health metrics present",
        )

    score = len(present) / len(required_fields)

    return CheckOutput(
        check_id="IN-CM-2",
        name="Repo Health Metrics Complete",
        result=CheckResult.FAIL,
        score=score,
        message=f"Missing fields: {', '.join(missing)}",
        details={"missing": missing, "present": present},
    )


@register_check(
    check_id="IN-CM-3",
    name="Hotspot Details Complete",
    description="Verify hotspots have required detail fields",
    dimension="completeness",
    weight=0.8,
)
def check_hotspot_details_complete(
    report_data: dict[str, Any],
    **kwargs: Any,
) -> CheckOutput:
    """Check that hotspots have complete details."""
    required_fields = ["relative_path", "complexity"]
    file_hotspots = report_data.get("file_hotspots", {})
    hotspots = file_hotspots.get("complexity_hotspots", [])

    if not hotspots:
        return CheckOutput(
            check_id="IN-CM-3",
            name="Hotspot Details Complete",
            result=CheckResult.SKIP,
            score=1.0,
            message="No hotspots to validate",
        )

    incomplete = []
    for i, hotspot in enumerate(hotspots):
        missing = [f for f in required_fields if hotspot.get(f) is None]
        if missing:
            incomplete.append(f"Hotspot {i}: missing {', '.join(missing)}")

    if not incomplete:
        return CheckOutput(
            check_id="IN-CM-3",
            name="Hotspot Details Complete",
            result=CheckResult.PASS,
            score=1.0,
            message=f"All {len(hotspots)} hotspots have complete details",
        )

    score = (len(hotspots) - len(incomplete)) / len(hotspots)

    return CheckOutput(
        check_id="IN-CM-3",
        name="Hotspot Details Complete",
        result=CheckResult.FAIL,
        score=score,
        message=f"{len(incomplete)} hotspots with missing fields",
        details={"incomplete": incomplete[:5]},  # Limit details
    )


@register_check(
    check_id="IN-CM-4",
    name="Vulnerability Details Complete",
    description="Verify vulnerabilities have required detail fields",
    dimension="completeness",
    weight=0.8,
)
def check_vulnerability_details_complete(
    report_data: dict[str, Any],
    **kwargs: Any,
) -> CheckOutput:
    """Check that vulnerabilities have complete details."""
    required_fields = ["cve_id", "severity", "package_name"]
    vulns = report_data.get("vulnerabilities", {})
    top_cves = vulns.get("top_cves", [])

    if not top_cves:
        return CheckOutput(
            check_id="IN-CM-4",
            name="Vulnerability Details Complete",
            result=CheckResult.SKIP,
            score=1.0,
            message="No vulnerabilities to validate",
        )

    incomplete = []
    for i, cve in enumerate(top_cves):
        missing = [f for f in required_fields if cve.get(f) is None]
        if missing:
            incomplete.append(f"CVE {i}: missing {', '.join(missing)}")

    if not incomplete:
        return CheckOutput(
            check_id="IN-CM-4",
            name="Vulnerability Details Complete",
            result=CheckResult.PASS,
            score=1.0,
            message=f"All {len(top_cves)} CVEs have complete details",
        )

    score = (len(top_cves) - len(incomplete)) / len(top_cves)

    return CheckOutput(
        check_id="IN-CM-4",
        name="Vulnerability Details Complete",
        result=CheckResult.FAIL,
        score=score,
        message=f"{len(incomplete)} CVEs with missing fields",
        details={"incomplete": incomplete[:5]},
    )


@register_check(
    check_id="IN-CM-5",
    name="Directory Rollups Present",
    description="Verify directory analysis includes rollup data",
    dimension="completeness",
    weight=0.6,
)
def check_directory_rollups_present(
    report_data: dict[str, Any],
    **kwargs: Any,
) -> CheckOutput:
    """Check that directory rollups are present."""
    dir_analysis = report_data.get("directory_analysis", {})

    if not dir_analysis:
        return CheckOutput(
            check_id="IN-CM-5",
            name="Directory Rollups Present",
            result=CheckResult.SKIP,
            score=1.0,
            message="Directory analysis section not included",
        )

    rollup_keys = ["hotspots", "largest"]
    present = [k for k in rollup_keys if dir_analysis.get(k)]
    missing = [k for k in rollup_keys if not dir_analysis.get(k)]

    if not missing:
        return CheckOutput(
            check_id="IN-CM-5",
            name="Directory Rollups Present",
            result=CheckResult.PASS,
            score=1.0,
            message="Directory rollups present",
        )

    score = len(present) / len(rollup_keys)

    return CheckOutput(
        check_id="IN-CM-5",
        name="Directory Rollups Present",
        result=CheckResult.FAIL,
        score=score,
        message=f"Missing rollups: {', '.join(missing)}",
        details={"missing": missing, "present": present},
    )


# Export list of checks
COMPLETENESS_CHECKS = [
    "IN-CM-1",
    "IN-CM-2",
    "IN-CM-3",
    "IN-CM-4",
    "IN-CM-5",
]
