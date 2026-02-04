"""Output quality checks for DevSkim analysis."""

from . import CheckResult, CheckCategory


def _validate_root_payload(root_payload: dict) -> list[str]:
    errors: list[str] = []
    required_root = ["schema_version", "generated_at", "repo_name", "repo_path", "results"]
    for field in required_root:
        if field not in root_payload:
            errors.append(f"Missing root field: {field}")

    results = root_payload.get("results", {})
    required_results = ["tool", "tool_version", "metadata", "summary"]
    for field in required_results:
        if field not in results:
            errors.append(f"Missing results field: {field}")

    if results.get("tool") != "devskim":
        errors.append("results.tool must be 'devskim'")

    return errors


def run_output_quality_checks(analysis: dict) -> list[CheckResult]:
    """Run output quality checks against the root output schema."""
    results: list[CheckResult] = []
    root_payload = analysis.get("_root") if isinstance(analysis, dict) else None

    if not root_payload:
        results.append(CheckResult(
            check_id="OQ-1",
            name="Schema validation",
            category=CheckCategory.OUTPUT_QUALITY,
            passed=False,
            score=0.0,
            message="Missing root wrapper for schema validation",
        ))
        return results

    errors = _validate_root_payload(root_payload)
    results.append(CheckResult(
        check_id="OQ-1",
        name="Schema validation",
        category=CheckCategory.OUTPUT_QUALITY,
        passed=len(errors) == 0,
        score=1.0 if not errors else 0.0,
        message="Schema validation passed" if not errors else "Schema validation failed",
        evidence={"errors": errors[:5]},
    ))
    return results
