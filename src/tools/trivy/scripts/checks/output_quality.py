"""Output quality checks for Trivy analysis."""

from datetime import datetime
from typing import Any, Generator

from . import CheckResult

CATEGORY = "Output Quality"


def run_output_quality_checks(
    analysis: dict[str, Any], ground_truth: dict[str, Any]
) -> Generator[CheckResult, None, None]:
    """Run all output quality checks."""
    yield check_json_validity(analysis)
    yield check_schema_version(analysis)
    yield check_required_summary_fields(analysis)
    yield check_required_vuln_fields(analysis)
    yield check_provenance(analysis)
    yield check_timestamp_format(analysis)
    yield check_numeric_types(analysis)


def check_json_validity(analysis: dict[str, Any]) -> CheckResult:
    """Check that analysis output is valid JSON structure."""
    required_keys = ["schema_version", "repository", "timestamp", "summary"]
    missing = [k for k in required_keys if k not in analysis]

    if missing:
        return CheckResult(
            check_id="json_validity",
            category=CATEGORY,
            passed=False,
            message=f"Missing required keys: {missing}",
        )

    return CheckResult(
        check_id="json_validity",
        category=CATEGORY,
        passed=True,
        message="Valid JSON structure with all required keys",
    )


def check_schema_version(analysis: dict[str, Any]) -> CheckResult:
    """Check that schema_version is present and valid."""
    version = analysis.get("schema_version")

    if not version:
        return CheckResult(
            check_id="schema_version",
            category=CATEGORY,
            passed=False,
            message="schema_version is missing",
        )

    if not isinstance(version, str):
        return CheckResult(
            check_id="schema_version",
            category=CATEGORY,
            passed=False,
            message=f"schema_version must be string, got {type(version).__name__}",
        )

    if version not in ["1.0", "1.1", "1.0.0", "1.1.0"]:
        return CheckResult(
            check_id="schema_version",
            category=CATEGORY,
            passed=False,
            message=f"Unexpected schema_version: {version}",
        )

    return CheckResult(
        check_id="schema_version",
        category=CATEGORY,
        passed=True,
        message=f"Valid schema_version: {version}",
    )


def check_required_summary_fields(analysis: dict[str, Any]) -> CheckResult:
    """Check that all required summary fields are present."""
    summary = analysis.get("summary", {})

    required_fields = [
        "total_vulnerabilities",
        "critical_count",
        "high_count",
        "medium_count",
        "low_count",
        "fix_available_count",
        "fix_available_pct",
        "dependency_count",
        "oldest_cve_days",
        "targets_scanned",
    ]

    missing = [f for f in required_fields if f not in summary]

    if missing:
        return CheckResult(
            check_id="required_summary_fields",
            category=CATEGORY,
            passed=False,
            message=f"Missing summary fields: {missing}",
        )

    return CheckResult(
        check_id="required_summary_fields",
        category=CATEGORY,
        passed=True,
        message=f"All {len(required_fields)} required summary fields present",
    )


def check_required_vuln_fields(analysis: dict[str, Any]) -> CheckResult:
    """Check that vulnerability entries have required fields."""
    vulnerabilities = analysis.get("vulnerabilities", [])

    if not vulnerabilities:
        return CheckResult(
            check_id="required_vuln_fields",
            category=CATEGORY,
            passed=True,
            message="No vulnerabilities to check (empty list)",
        )

    required_fields = [
        "id",
        "severity",
        "package",
        "installed_version",
        "fix_available",
        "target",
    ]

    errors = []
    for i, vuln in enumerate(vulnerabilities[:10]):  # Check first 10
        missing = [f for f in required_fields if f not in vuln]
        if missing:
            errors.append(f"vuln[{i}] missing: {missing}")

    if errors:
        return CheckResult(
            check_id="required_vuln_fields",
            category=CATEGORY,
            passed=False,
            message=f"Missing vulnerability fields: {errors[:3]}",
        )

    return CheckResult(
        check_id="required_vuln_fields",
        category=CATEGORY,
        passed=True,
        message=f"All {len(required_fields)} required fields present in vulnerabilities",
    )


def check_provenance(analysis: dict[str, Any]) -> CheckResult:
    """Check that provenance fields are present."""
    required = ["tool", "tool_version", "timestamp", "repository"]
    missing = [f for f in required if not analysis.get(f)]

    if missing:
        return CheckResult(
            check_id="provenance",
            category=CATEGORY,
            passed=False,
            message=f"Missing provenance fields: {missing}",
        )

    return CheckResult(
        check_id="provenance",
        category=CATEGORY,
        passed=True,
        message=f"All provenance fields present (tool={analysis.get('tool')})",
    )


def check_timestamp_format(analysis: dict[str, Any]) -> CheckResult:
    """Check that timestamp is valid ISO8601."""
    timestamp = analysis.get("timestamp", "")

    if not timestamp:
        return CheckResult(
            check_id="timestamp_format",
            category=CATEGORY,
            passed=False,
            message="timestamp is missing",
        )

    try:
        # Try parsing ISO8601
        ts = timestamp.replace("Z", "+00:00")
        datetime.fromisoformat(ts)
        return CheckResult(
            check_id="timestamp_format",
            category=CATEGORY,
            passed=True,
            message="Valid ISO8601 timestamp",
        )
    except ValueError as e:
        return CheckResult(
            check_id="timestamp_format",
            category=CATEGORY,
            passed=False,
            message=f"Invalid timestamp format: {e}",
        )


def check_numeric_types(analysis: dict[str, Any]) -> CheckResult:
    """Check that numeric fields have correct types."""
    summary = analysis.get("summary", {})

    int_fields = [
        "total_vulnerabilities",
        "critical_count",
        "high_count",
        "medium_count",
        "low_count",
        "fix_available_count",
        "dependency_count",
        "oldest_cve_days",
        "targets_scanned",
    ]

    float_fields = ["fix_available_pct"]

    errors = []

    for field in int_fields:
        val = summary.get(field)
        if val is not None and not isinstance(val, int):
            errors.append(f"{field} should be int, got {type(val).__name__}")

    for field in float_fields:
        val = summary.get(field)
        if val is not None and not isinstance(val, (int, float)):
            errors.append(f"{field} should be numeric, got {type(val).__name__}")

    if errors:
        return CheckResult(
            check_id="numeric_types",
            category=CATEGORY,
            passed=False,
            message=f"Type errors: {errors[:3]}",
        )

    return CheckResult(
        check_id="numeric_types",
        category=CATEGORY,
        passed=True,
        message="All numeric fields have correct types",
    )
