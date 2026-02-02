"""Output quality checks for gitleaks analysis.

Validates that the analysis output follows the Caldera envelope format
with proper metadata and data structure.
"""

from __future__ import annotations

from . import CheckResult


def _validate_caldera_envelope(root_payload: dict) -> list[str]:
    """Validate the Caldera envelope format.

    The expected format is:
    {
        "metadata": {
            "tool_name": "gitleaks",
            "tool_version": "...",
            "run_id": "...",
            "repo_id": "...",
            "branch": "...",
            "commit": "...",
            "timestamp": "...",
            "schema_version": "..."
        },
        "data": {
            "tool": "gitleaks",
            "tool_version": "...",
            "total_secrets": ...,
            "findings": [...]
        }
    }
    """
    errors: list[str] = []

    # Check for Caldera envelope structure (metadata + data)
    if "metadata" in root_payload and "data" in root_payload:
        # New Caldera envelope format
        metadata = root_payload.get("metadata", {})
        data = root_payload.get("data", {})

        # Validate required metadata fields
        required_metadata = [
            "tool_name",
            "tool_version",
            "run_id",
            "repo_id",
            "branch",
            "commit",
            "timestamp",
            "schema_version",
        ]
        for field in required_metadata:
            if field not in metadata:
                errors.append(f"Missing metadata field: {field}")

        # Validate metadata.tool_name
        if metadata.get("tool_name") != "gitleaks":
            errors.append("metadata.tool_name must be 'gitleaks'")

        # Validate required data fields
        required_data = ["tool", "tool_version", "total_secrets", "findings"]
        for field in required_data:
            if field not in data:
                errors.append(f"Missing data field: {field}")

        # Validate data.tool
        if data.get("tool") != "gitleaks":
            errors.append("data.tool must be 'gitleaks'")

        # Validate total_secrets type
        if "total_secrets" in data and not isinstance(data.get("total_secrets"), int):
            errors.append("data.total_secrets must be an integer")

        # Validate findings type
        if "findings" in data and not isinstance(data.get("findings"), list):
            errors.append("data.findings must be a list")

    elif "results" in root_payload:
        # Legacy format with results wrapper (from analyze.py output)
        # This is still acceptable as an intermediate format
        results = root_payload.get("results", {})
        required_root = ["schema_version", "generated_at", "repo_name", "repo_path", "results"]
        for field in required_root:
            if field not in root_payload:
                errors.append(f"Missing root field: {field}")

        required_results = ["tool", "tool_version", "total_secrets", "findings"]
        for field in required_results:
            if field not in results:
                errors.append(f"Missing results field: {field}")

        if results.get("tool") != "gitleaks":
            errors.append("results.tool must be 'gitleaks'")

        if "total_secrets" in results and not isinstance(results.get("total_secrets"), int):
            errors.append("results.total_secrets must be an integer")
        if "findings" in results and not isinstance(results.get("findings"), list):
            errors.append("results.findings must be a list")

    else:
        # Unknown format
        errors.append("Missing required envelope structure (metadata+data or results)")

    return errors


def run_output_quality_checks(analysis: dict) -> list[CheckResult]:
    """Run output quality checks against the Caldera envelope schema.

    Args:
        analysis: The analysis output dictionary. May contain a '_root' key
            with the original root payload for schema validation.

    Returns:
        List of CheckResult objects for the output quality dimension.
    """
    results: list[CheckResult] = []

    # Get the root payload - either from _root key or the analysis itself
    root_payload = analysis.get("_root") if isinstance(analysis, dict) else None

    if not root_payload:
        # If no _root, check if analysis itself is the root envelope
        if isinstance(analysis, dict) and ("metadata" in analysis or "results" in analysis):
            root_payload = analysis
        else:
            results.append(
                CheckResult(
                    check_id="OQ-1",
                    category="Output Quality",
                    passed=False,
                    message="Missing root wrapper for schema validation",
                )
            )
            return results

    errors = _validate_caldera_envelope(root_payload)
    results.append(
        CheckResult(
            check_id="OQ-1",
            category="Output Quality",
            passed=len(errors) == 0,
            message="Schema validation passed" if not errors else "Schema validation failed",
            expected="valid Caldera envelope schema",
            actual=errors[:5] if errors else "valid",
        )
    )
    return results
