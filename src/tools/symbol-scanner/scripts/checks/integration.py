"""Integration checks for programmatic evaluation."""

from __future__ import annotations


def check_path_normalization(actual: dict) -> dict:
    """Check that all paths are repo-relative."""
    issues = []

    for symbol in actual.get("symbols", []):
        path = symbol.get("path", "")
        if path.startswith("/") or path.startswith("./") or "\\" in path:
            issues.append(f"symbol path: {path}")

    for call in actual.get("calls", []):
        path = call.get("caller_file", "")
        if path.startswith("/") or path.startswith("./") or "\\" in path:
            issues.append(f"call caller_file: {path}")

    for imp in actual.get("imports", []):
        path = imp.get("file", "")
        if path.startswith("/") or path.startswith("./") or "\\" in path:
            issues.append(f"import file: {path}")

    return {
        "name": "path_normalization",
        "passed": len(issues) == 0,
        "issues": issues,
    }


def check_envelope_structure(output: dict) -> dict:
    """Check that output has correct envelope structure."""
    issues = []

    if "metadata" not in output:
        issues.append("missing metadata")
    else:
        required_metadata = ["tool_name", "tool_version", "run_id", "repo_id", "branch", "commit", "timestamp", "schema_version"]
        for field in required_metadata:
            if field not in output["metadata"]:
                issues.append(f"missing metadata.{field}")

    if "data" not in output:
        issues.append("missing data")
    else:
        required_data = ["symbols", "calls", "imports", "summary"]
        for field in required_data:
            if field not in output["data"]:
                issues.append(f"missing data.{field}")

    return {
        "name": "envelope_structure",
        "passed": len(issues) == 0,
        "issues": issues,
    }


def check_summary_accuracy(actual: dict) -> dict:
    """Check that summary counts match actual data."""
    issues = []

    summary = actual.get("summary", {})
    symbols = actual.get("symbols", [])
    calls = actual.get("calls", [])
    imports = actual.get("imports", [])

    if summary.get("total_symbols") != len(symbols):
        issues.append(f"total_symbols mismatch: {summary.get('total_symbols')} != {len(symbols)}")

    if summary.get("total_calls") != len(calls):
        issues.append(f"total_calls mismatch: {summary.get('total_calls')} != {len(calls)}")

    if summary.get("total_imports") != len(imports):
        issues.append(f"total_imports mismatch: {summary.get('total_imports')} != {len(imports)}")

    return {
        "name": "summary_accuracy",
        "passed": len(issues) == 0,
        "issues": issues,
    }


def run_checks(output: dict, actual_data: dict, expected_data: dict = None) -> list[dict]:
    """Run all integration checks."""
    return [
        check_path_normalization(actual_data),
        check_envelope_structure(output),
        check_summary_accuracy(actual_data),
    ]
