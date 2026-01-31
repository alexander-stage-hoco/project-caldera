"""
Output quality checks for Semgrep smell analysis.

Validates core sections and required fields for schema compliance.
"""

from pathlib import Path

import json
from jsonschema import Draft202012Validator

from . import CheckResult, CheckCategory


def run_output_quality_checks(analysis: dict) -> list[CheckResult]:
    """Run output quality checks."""
    results = []

    required_sections = [
        "tool",
        "tool_version",
        "metadata",
        "summary",
        "directories",
        "files",
        "by_language",
        "statistics",
    ]
    missing_sections = [section for section in required_sections if section not in analysis]
    section_score = 1.0 if not missing_sections else 0.0

    results.append(CheckResult(
        check_id="OQ-1",
        name="Required sections present",
        category=CheckCategory.OUTPUT_QUALITY,
        passed=not missing_sections,
        score=section_score,
        message="All required sections present" if not missing_sections else f"Missing sections: {missing_sections}",
        evidence={"missing_sections": missing_sections},
    ))

    files = analysis.get("files", [])
    missing_fields = 0
    total_files = len(files)
    for file_info in files:
        for field in ("path", "language", "lines", "smell_count", "smells"):
            if field not in file_info:
                missing_fields += 1
                break

    file_score = 1.0 if total_files == 0 else max(0.0, 1.0 - (missing_fields / total_files))
    results.append(CheckResult(
        check_id="OQ-2",
        name="File entries include required fields",
        category=CheckCategory.OUTPUT_QUALITY,
        passed=missing_fields == 0,
        score=file_score,
        message=f"{total_files - missing_fields}/{total_files} files include required fields",
        evidence={
            "total_files": total_files,
            "files_missing_fields": missing_fields,
        },
    ))

    root_payload = analysis.get("_root") if isinstance(analysis, dict) else None
    schema_errors = []
    if root_payload:
        schema_path = Path(__file__).parent.parent.parent / "schemas" / "output.schema.json"
        if schema_path.exists():
            schema = schema_path.read_text()
            validator = Draft202012Validator(schema=json.loads(schema))
            schema_errors = [e.message for e in validator.iter_errors(root_payload)]
        else:
            schema_errors = [f"Schema not found: {schema_path}"]
    else:
        schema_errors = ["Missing root wrapper for schema validation"]

    results.append(CheckResult(
        check_id="OQ-3",
        name="Schema validation",
        category=CheckCategory.OUTPUT_QUALITY,
        passed=len(schema_errors) == 0,
        score=1.0 if not schema_errors else 0.0,
        message="Schema validation passed" if not schema_errors else "Schema validation failed",
        evidence={"errors": schema_errors[:5]},
    ))

    return results
