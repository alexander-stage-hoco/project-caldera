"""Output Quality checks (OQ-1 to OQ-8)."""

import json
from pathlib import Path
from typing import List

from . import CheckResult


def check_json_valid(raw_output_path: Path) -> CheckResult:
    """OQ-1: Verify raw scc output is valid JSON."""
    try:
        with open(raw_output_path) as f:
            content = f.read()
        data = json.loads(content)
        return CheckResult(
            check_id="OQ-1",
            name="JSON Valid",
            passed=True,
            message=f"Valid JSON with {len(data)} entries",
            evidence={"entry_count": len(data)}
        )
    except json.JSONDecodeError as e:
        return CheckResult(
            check_id="OQ-1",
            name="JSON Valid",
            passed=False,
            message=f"JSON parse error: {e}",
            evidence={"error": str(e)}
        )
    except FileNotFoundError:
        return CheckResult(
            check_id="OQ-1",
            name="JSON Valid",
            passed=False,
            message=f"File not found: {raw_output_path}",
            evidence={"error": "file_not_found"}
        )


def check_array_structure(raw_output_path: Path) -> CheckResult:
    """OQ-2: Verify root is JSON array."""
    try:
        with open(raw_output_path) as f:
            data = json.load(f)

        is_array = isinstance(data, list)
        return CheckResult(
            check_id="OQ-2",
            name="Array Structure",
            passed=is_array,
            message="Root is array" if is_array else f"Root is {type(data).__name__}",
            expected="list",
            actual=type(data).__name__,
            evidence={"type": type(data).__name__}
        )
    except Exception as e:
        return CheckResult(
            check_id="OQ-2",
            name="Array Structure",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_required_fields(raw_output_path: Path) -> CheckResult:
    """OQ-3: Verify all required fields present."""
    required = ["Name", "Count", "Lines", "Code", "Comment", "Blank"]

    try:
        with open(raw_output_path) as f:
            data = json.load(f)

        missing = []
        for entry in data:
            for field in required:
                if field not in entry:
                    missing.append(f"{entry.get('Name', 'unknown')}.{field}")

        return CheckResult(
            check_id="OQ-3",
            name="Required Fields",
            passed=len(missing) == 0,
            message="All required fields present" if not missing else f"Missing: {missing[:5]}",
            expected=required,
            actual=missing[:10] if missing else "all present",
            evidence={"missing_fields": missing}
        )
    except Exception as e:
        return CheckResult(
            check_id="OQ-3",
            name="Required Fields",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_numeric_types(raw_output_path: Path) -> CheckResult:
    """OQ-4: Verify numeric fields are integers >= 0."""
    numeric_fields = ["Count", "Lines", "Code", "Comment", "Blank"]

    try:
        with open(raw_output_path) as f:
            data = json.load(f)

        invalid = []
        for entry in data:
            for field in numeric_fields:
                if field in entry:
                    val = entry[field]
                    if not isinstance(val, int) or val < 0:
                        invalid.append(f"{entry.get('Name', 'unknown')}.{field}={val}")

        return CheckResult(
            check_id="OQ-4",
            name="Numeric Types",
            passed=len(invalid) == 0,
            message="All numeric fields valid" if not invalid else f"Invalid: {invalid[:5]}",
            evidence={"invalid_fields": invalid}
        )
    except Exception as e:
        return CheckResult(
            check_id="OQ-4",
            name="Numeric Types",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_non_empty_output(raw_output_path: Path) -> CheckResult:
    """OQ-5: Verify array has >= 1 entry."""
    try:
        with open(raw_output_path) as f:
            data = json.load(f)

        count = len(data) if isinstance(data, list) else 0
        return CheckResult(
            check_id="OQ-5",
            name="Non-Empty Output",
            passed=count >= 1,
            message=f"Output has {count} entries",
            expected=">= 1",
            actual=count,
            evidence={"entry_count": count}
        )
    except Exception as e:
        return CheckResult(
            check_id="OQ-5",
            name="Non-Empty Output",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_bytes_present(raw_output_path: Path) -> CheckResult:
    """OQ-6: Verify all entries have Bytes field."""
    try:
        with open(raw_output_path) as f:
            data = json.load(f)

        missing = [entry.get("Name", "unknown") for entry in data if "Bytes" not in entry]

        return CheckResult(
            check_id="OQ-6",
            name="Bytes Present",
            passed=len(missing) == 0,
            message="All entries have Bytes" if not missing else f"Missing Bytes: {missing}",
            evidence={"missing_bytes": missing}
        )
    except Exception as e:
        return CheckResult(
            check_id="OQ-6",
            name="Bytes Present",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_complexity_present(raw_output_path: Path) -> CheckResult:
    """OQ-7: Verify all entries have Complexity field."""
    try:
        with open(raw_output_path) as f:
            data = json.load(f)

        missing = [entry.get("Name", "unknown") for entry in data if "Complexity" not in entry]

        return CheckResult(
            check_id="OQ-7",
            name="Complexity Present",
            passed=len(missing) == 0,
            message="All entries have Complexity" if not missing else f"Missing: {missing}",
            evidence={"missing_complexity": missing}
        )
    except Exception as e:
        return CheckResult(
            check_id="OQ-7",
            name="Complexity Present",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_no_parse_errors(exit_code: int, stderr: str) -> CheckResult:
    """OQ-8: Verify no parse errors in stderr."""
    has_errors = "error" in stderr.lower() or "panic" in stderr.lower()

    return CheckResult(
        check_id="OQ-8",
        name="No Parse Errors",
        passed=exit_code == 0 and not has_errors,
        message="No errors" if not has_errors else f"Errors detected: {stderr[:100]}",
        expected="exit_code=0, no errors",
        actual=f"exit_code={exit_code}, stderr={stderr[:50] if stderr else 'empty'}",
        evidence={"exit_code": exit_code, "stderr_sample": stderr[:200] if stderr else ""}
    )


def run_output_quality_checks(
    raw_output_path: Path,
    exit_code: int = 0,
    stderr: str = ""
) -> List[CheckResult]:
    """Run all output quality checks."""
    return [
        check_json_valid(raw_output_path),
        check_array_structure(raw_output_path),
        check_required_fields(raw_output_path),
        check_numeric_types(raw_output_path),
        check_non_empty_output(raw_output_path),
        check_bytes_present(raw_output_path),
        check_complexity_present(raw_output_path),
        check_no_parse_errors(exit_code, stderr),
    ]
