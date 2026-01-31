"""Integration Fit checks (IF-1 to IF-6)."""

import json
from pathlib import Path
from typing import List
import re

from . import CheckResult


def check_output_generated(output_path: Path) -> CheckResult:
    """IF-1: Verify output.json is generated."""
    if output_path.exists():
        return CheckResult(
            check_id="IF-1",
            name="Output Generated",
            passed=True,
            message="output.json present",
            evidence={"output_path": str(output_path)}
        )
    return CheckResult(
        check_id="IF-1",
        name="Output Generated",
        passed=False,
        message=f"Missing output: {output_path}",
        evidence={"output_path": str(output_path)}
    )


def check_schema_valid(output_path: Path, schema_path: Path) -> CheckResult:
    """IF-2: Verify output validates against JSON schema."""
    try:
        from jsonschema import validate, ValidationError

        with open(output_path) as f:
            output = json.load(f)
        with open(schema_path) as f:
            schema = json.load(f)

        validate(output, schema)
        return CheckResult(
            check_id="IF-2",
            name="Schema Valid",
            passed=True,
            message="Output validates against schema",
            evidence={"schema_path": str(schema_path)}
        )
    except ValidationError as e:
        return CheckResult(
            check_id="IF-2",
            name="Schema Valid",
            passed=False,
            message=f"Schema validation failed: {e.message[:100]}",
            evidence={"validation_error": e.message}
        )
    except ImportError:
        # jsonschema not installed, do basic validation
        try:
            with open(output_path) as f:
                output = json.load(f)
            required = ["metadata", "data"]
            missing = [f for f in required if f not in output]
            return CheckResult(
                check_id="IF-2",
                name="Schema Valid",
                passed=len(missing) == 0,
                message="Basic validation (jsonschema not installed)" if not missing else f"Missing: {missing}",
                evidence={"missing_fields": missing}
            )
        except Exception as e:
            return CheckResult(
                check_id="IF-2",
                name="Schema Valid",
                passed=False,
                message=f"Error: {e}",
                evidence={"error": str(e)}
            )
    except Exception as e:
        return CheckResult(
            check_id="IF-2",
            name="Schema Valid",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_all_fields_mapped(output_path: Path) -> CheckResult:
    """IF-3: Verify required fields exist in envelope data."""
    required_fields = ["summary", "languages"]

    try:
        with open(output_path) as f:
            output = json.load(f)
        data = output.get("data", {})
        missing = [field for field in required_fields if field not in data]

        return CheckResult(
            check_id="IF-3",
            name="Required Fields Present",
            passed=len(missing) == 0,
            message="All required fields present" if not missing else f"Missing: {missing}",
            expected=required_fields,
            actual=missing,
            evidence={"missing_fields": missing}
        )
    except Exception as e:
        return CheckResult(
            check_id="IF-3",
            name="Required Fields Present",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_no_data_loss(raw_output_path: Path, output_path: Path) -> CheckResult:
    """IF-4: Verify totals in envelope output match raw totals."""
    try:
        with open(raw_output_path) as f:
            raw = json.load(f)
        with open(output_path) as f:
            output = json.load(f)

        # Calculate raw totals
        raw_files = sum(entry.get("Count", 0) for entry in raw)
        raw_loc = sum(entry.get("Code", 0) for entry in raw)

        # Get envelope totals
        summary = output.get("data", {}).get("summary", {})
        envelope_files = summary.get("total_files", 0)
        envelope_loc = summary.get("total_loc", 0)

        files_match = raw_files == envelope_files
        loc_match = raw_loc == envelope_loc

        return CheckResult(
            check_id="IF-4",
            name="No Data Loss",
            passed=files_match and loc_match,
            message=f"Totals match" if files_match and loc_match else f"Mismatch: files {raw_files}!={envelope_files} or loc {raw_loc}!={envelope_loc}",
            expected={"files": raw_files, "loc": raw_loc},
            actual={"files": envelope_files, "loc": envelope_loc},
            evidence={
                "raw_files": raw_files,
                "raw_loc": raw_loc,
                "envelope_files": envelope_files,
                "envelope_loc": envelope_loc,
            }
        )
    except Exception as e:
        return CheckResult(
            check_id="IF-4",
            name="No Data Loss",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_metadata_complete(output_path: Path) -> CheckResult:
    """IF-5: Verify metadata fields are present and non-empty."""
    required = [
        "tool_name",
        "tool_version",
        "run_id",
        "repo_id",
        "branch",
        "commit",
        "timestamp",
        "schema_version",
    ]

    try:
        with open(output_path) as f:
            output = json.load(f)

        metadata = output.get("metadata", {})
        missing = [field for field in required if not metadata.get(field)]

        return CheckResult(
            check_id="IF-5",
            name="Metadata Complete",
            passed=len(missing) == 0,
            message="Metadata complete" if not missing else f"Missing: {missing}",
            evidence={"missing_fields": missing}
        )
    except Exception as e:
        return CheckResult(
            check_id="IF-5",
            name="Metadata Complete",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def _invalid_relative_path(path: str) -> bool:
    if not path:
        return True
    if path.startswith(("/", "\\")):
        return True
    if path.startswith("./") or path.endswith("/"):
        return True
    if "\\" in path:
        return True
    if re.match(r"^[A-Za-z]:", path):
        return True
    if ".." in path.split("/"):
        return True
    return False


def check_paths_relative(output_path: Path) -> CheckResult:
    """IF-6: Verify file and directory paths are repo-relative."""
    try:
        with open(output_path) as f:
            output = json.load(f)

        data = output.get("data", {})
        invalid = []

        for entry in data.get("files", []):
            path = entry.get("path")
            if _invalid_relative_path(path):
                invalid.append(path)

        for entry in data.get("directories", []):
            path = entry.get("path")
            if _invalid_relative_path(path):
                invalid.append(path)

        return CheckResult(
            check_id="IF-6",
            name="Relative Paths",
            passed=len(invalid) == 0,
            message="All paths are repo-relative" if not invalid else f"Invalid: {invalid[:5]}",
            evidence={"invalid_paths": invalid}
        )
    except Exception as e:
        return CheckResult(
            check_id="IF-6",
            name="Relative Paths",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def run_integration_fit_checks(
    raw_output_path: Path,
    output_path: Path,
    schema_path: Path
) -> List[CheckResult]:
    """Run all integration fit checks."""
    return [
        check_output_generated(output_path),
        check_schema_valid(output_path, schema_path),
        check_all_fields_mapped(output_path),
        check_no_data_loss(raw_output_path, output_path),
        check_metadata_complete(output_path),
        check_paths_relative(output_path),
    ]
