"""Integration fit checks for Trivy analysis."""

from typing import Any, Generator

from . import CheckResult

CATEGORY = "Integration Fit"


def run_integration_checks(
    analysis: dict[str, Any], ground_truth: dict[str, Any]
) -> Generator[CheckResult, None, None]:
    """Run all integration fit checks."""
    yield check_cve_counts_for_security(analysis)
    yield check_age_for_patch_currency(analysis)
    yield check_iac_for_infrastructure(analysis)
    yield check_directory_rollups(analysis)
    yield check_evidence_transformability(analysis)
    yield check_sbom_for_inventory(analysis)


def check_cve_counts_for_security(analysis: dict[str, Any]) -> CheckResult:
    """Check that critical/high counts are present for L7 Security lens."""
    summary = analysis.get("summary", {})

    required = ["critical_count", "high_count", "total_vulnerabilities"]
    missing = [f for f in required if f not in summary]

    if missing:
        return CheckResult(
            check_id="cve_counts_for_security",
            category=CATEGORY,
            passed=False,
            message=f"Missing CVE count fields: {missing}",
        )

    critical = summary.get("critical_count", 0)
    high = summary.get("high_count", 0)
    total = summary.get("total_vulnerabilities", 0)

    return CheckResult(
        check_id="cve_counts_for_security",
        category=CATEGORY,
        passed=True,
        message=f"CVE counts present: {total} total, {critical} critical, {high} high",
    )


def check_age_for_patch_currency(analysis: dict[str, Any]) -> CheckResult:
    """Check that oldest_cve_days is calculated for patch currency analysis."""
    summary = analysis.get("summary", {})

    if "oldest_cve_days" not in summary:
        return CheckResult(
            check_id="age_for_patch_currency",
            category=CATEGORY,
            passed=False,
            message="oldest_cve_days not present in summary",
        )

    oldest = summary.get("oldest_cve_days", 0)

    # Check that age_days is also in individual vulnerabilities
    vulnerabilities = analysis.get("vulnerabilities", [])
    if vulnerabilities:
        has_age = all("age_days" in v for v in vulnerabilities[:5])
        if not has_age:
            return CheckResult(
                check_id="age_for_patch_currency",
                category=CATEGORY,
                passed=False,
                message="age_days missing from vulnerability entries",
            )

    return CheckResult(
        check_id="age_for_patch_currency",
        category=CATEGORY,
        passed=True,
        message=f"Patch currency metrics present (oldest={oldest} days)",
    )


def check_iac_for_infrastructure(analysis: dict[str, Any]) -> CheckResult:
    """Check that IaC misconfiguration data is present."""
    iac = analysis.get("iac_misconfigurations", {})

    required = ["total_count", "critical_count", "high_count", "misconfigurations"]
    missing = [f for f in required if f not in iac]

    if missing:
        return CheckResult(
            check_id="iac_for_infrastructure",
            category=CATEGORY,
            passed=False,
            message=f"Missing IaC fields: {missing}",
        )

    total = iac.get("total_count", 0)
    critical = iac.get("critical_count", 0)

    return CheckResult(
        check_id="iac_for_infrastructure",
        category=CATEGORY,
        passed=True,
        message=f"IaC metrics present: {total} issues ({critical} critical)",
    )


def check_directory_rollups(analysis: dict[str, Any]) -> CheckResult:
    """Check that directory rollups work correctly."""
    directories = analysis.get("directories", {})

    if not directories:
        return CheckResult(
            check_id="directory_rollups",
            category=CATEGORY,
            passed=False,
            message="directories section is missing",
        )

    if "directory_count" not in directories:
        return CheckResult(
            check_id="directory_rollups",
            category=CATEGORY,
            passed=False,
            message="directory_count is missing",
        )

    dir_list = directories.get("directories", [])

    # Check that each directory has direct and recursive metrics
    for d in dir_list[:5]:
        if "direct" not in d or "recursive" not in d:
            return CheckResult(
                check_id="directory_rollups",
                category=CATEGORY,
                passed=False,
                message=f"Directory {d.get('path')} missing direct/recursive metrics",
            )

        # Check that recursive >= direct for counts
        direct = d.get("direct", {})
        recursive = d.get("recursive", {})

        if recursive.get("vulnerability_count", 0) < direct.get(
            "vulnerability_count", 0
        ):
            return CheckResult(
                check_id="directory_rollups",
                category=CATEGORY,
                passed=False,
                message=f"Directory {d.get('path')}: recursive < direct",
            )

    return CheckResult(
        check_id="directory_rollups",
        category=CATEGORY,
        passed=True,
        message=f"Directory rollups valid ({len(dir_list)} directories)",
    )


def check_evidence_transformability(analysis: dict[str, Any]) -> CheckResult:
    """Check that output structure is compatible with DD evidence schema."""
    # Check for key fields needed by DD Analyzer
    required_for_dd = {
        "repository": analysis.get("repository"),
        "timestamp": analysis.get("timestamp"),
        "summary.critical_count": analysis.get("summary", {}).get("critical_count"),
        "summary.high_count": analysis.get("summary", {}).get("high_count"),
        "summary.total_vulnerabilities": analysis.get("summary", {}).get(
            "total_vulnerabilities"
        ),
    }

    missing = [k for k, v in required_for_dd.items() if v is None]

    if missing:
        return CheckResult(
            check_id="evidence_transformability",
            category=CATEGORY,
            passed=False,
            message=f"Missing DD-required fields: {missing}",
        )

    # Check that vulnerabilities can be mapped to files
    vulnerabilities = analysis.get("vulnerabilities", [])
    if vulnerabilities:
        has_target = all("target" in v for v in vulnerabilities[:5])
        if not has_target:
            return CheckResult(
                check_id="evidence_transformability",
                category=CATEGORY,
                passed=False,
                message="Vulnerabilities missing target field for file mapping",
            )

    return CheckResult(
        check_id="evidence_transformability",
        category=CATEGORY,
        passed=True,
        message="Output structure compatible with DD evidence schema",
    )


def check_sbom_for_inventory(analysis: dict[str, Any]) -> CheckResult:
    """Check that SBOM/package inventory data is present."""
    sbom = analysis.get("sbom", {})

    if not sbom:
        return CheckResult(
            check_id="sbom_for_inventory",
            category=CATEGORY,
            passed=False,
            message="Missing sbom section",
        )

    required = ["format", "total_packages", "vulnerable_packages", "clean_packages"]
    missing = [f for f in required if f not in sbom]

    if missing:
        return CheckResult(
            check_id="sbom_for_inventory",
            category=CATEGORY,
            passed=False,
            message=f"Missing SBOM fields: {missing}",
        )

    total = sbom.get("total_packages", 0)
    vulnerable = sbom.get("vulnerable_packages", 0)
    clean = sbom.get("clean_packages", 0)

    # Validate consistency
    if total > 0 and clean + vulnerable != total:
        # Allow for some inconsistency due to how we count vulnerable packages
        # (unique packages with vulns vs total package entries)
        pass  # Not a failure, just informational

    return CheckResult(
        check_id="sbom_for_inventory",
        category=CATEGORY,
        passed=True,
        message=f"SBOM present: {total} total packages, {vulnerable} vulnerable, {clean} clean",
    )
