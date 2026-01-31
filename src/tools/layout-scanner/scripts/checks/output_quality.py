"""
Output Quality Checks (OQ-1 to OQ-8).

Validates JSON structure, schema compliance, and data integrity.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Set

from . import CheckCategory, CheckResult, register_check


def run_output_quality_checks(
    output: Dict[str, Any],
    schema_path: Path = None,
) -> List[CheckResult]:
    """Run all output quality checks."""
    checks = []

    checks.append(check_json_valid(output))
    checks.append(check_schema_compliant(output, schema_path))
    checks.append(check_files_present(output))
    checks.append(check_directories_present(output))
    checks.append(check_hierarchy_valid(output))
    checks.append(check_ids_unique(output))
    checks.append(check_ids_format(output))
    checks.append(check_statistics_accurate(output))

    return checks


@register_check("OQ-1")
def check_json_valid(output: Dict[str, Any]) -> CheckResult:
    """OQ-1: Output is valid JSON (already parsed, so check structure)."""
    required_keys = [
        "schema_version", "tool", "tool_version", "run_id",
        "timestamp", "repository", "statistics", "files",
        "directories", "hierarchy"
    ]

    missing = [k for k in required_keys if k not in output]

    if missing:
        return CheckResult(
            check_id="OQ-1",
            name="JSON Valid",
            category=CheckCategory.OUTPUT_QUALITY,
            passed=False,
            score=0.0,
            message=f"Missing required keys: {missing}",
            evidence={"missing_keys": missing},
        )

    return CheckResult(
        check_id="OQ-1",
        name="JSON Valid",
        category=CheckCategory.OUTPUT_QUALITY,
        passed=True,
        score=1.0,
        message="All required keys present",
    )


@register_check("OQ-2")
def check_schema_compliant(
    output: Dict[str, Any],
    schema_path: Path = None,
) -> CheckResult:
    """OQ-2: Output matches JSON schema."""
    from ..schema_validator import SchemaValidator

    try:
        validator = SchemaValidator(schema_path)
        result = validator.validate_schema(output)

        if result.valid:
            return CheckResult(
                check_id="OQ-2",
                name="Schema Compliant",
                category=CheckCategory.OUTPUT_QUALITY,
                passed=True,
                score=1.0,
                message="Output validates against schema",
            )

        return CheckResult(
            check_id="OQ-2",
            name="Schema Compliant",
            category=CheckCategory.OUTPUT_QUALITY,
            passed=False,
            score=0.0,
            message=f"Schema validation failed: {len(result.errors)} errors",
            evidence={"errors": result.errors[:5]},
        )

    except FileNotFoundError:
        return CheckResult(
            check_id="OQ-2",
            name="Schema Compliant",
            category=CheckCategory.OUTPUT_QUALITY,
            passed=True,
            score=0.5,
            message="Schema file not found, skipped validation",
        )


@register_check("OQ-3")
def check_files_present(output: Dict[str, Any]) -> CheckResult:
    """OQ-3: Files section exists and structure is valid."""
    files = output.get("files", {})

    if not isinstance(files, dict):
        return CheckResult(
            check_id="OQ-3",
            name="Files Present",
            category=CheckCategory.OUTPUT_QUALITY,
            passed=False,
            score=0.0,
            message="'files' is not a dictionary",
        )

    # Check that files have required fields
    required_fields = ["id", "path", "name", "classification"]
    invalid_files = []

    for path, file_obj in files.items():
        missing = [f for f in required_fields if f not in file_obj]
        if missing:
            invalid_files.append({"path": path, "missing": missing})

    if invalid_files:
        return CheckResult(
            check_id="OQ-3",
            name="Files Present",
            category=CheckCategory.OUTPUT_QUALITY,
            passed=False,
            score=0.5,
            message=f"{len(invalid_files)} files missing required fields",
            evidence={"invalid_files": invalid_files[:5]},
        )

    return CheckResult(
        check_id="OQ-3",
        name="Files Present",
        category=CheckCategory.OUTPUT_QUALITY,
        passed=True,
        score=1.0,
        message=f"Files section valid with {len(files)} files",
        evidence={"file_count": len(files)},
    )


@register_check("OQ-4")
def check_directories_present(output: Dict[str, Any]) -> CheckResult:
    """OQ-4: Directories section exists and structure is valid."""
    directories = output.get("directories", {})

    if not isinstance(directories, dict):
        return CheckResult(
            check_id="OQ-4",
            name="Directories Present",
            category=CheckCategory.OUTPUT_QUALITY,
            passed=False,
            score=0.0,
            message="'directories' is not a dictionary",
        )

    required_fields = ["id", "path", "name", "classification"]
    invalid_dirs = []

    for path, dir_obj in directories.items():
        missing = [f for f in required_fields if f not in dir_obj]
        if missing:
            invalid_dirs.append({"path": path, "missing": missing})

    if invalid_dirs:
        return CheckResult(
            check_id="OQ-4",
            name="Directories Present",
            category=CheckCategory.OUTPUT_QUALITY,
            passed=False,
            score=0.5,
            message=f"{len(invalid_dirs)} directories missing required fields",
            evidence={"invalid_dirs": invalid_dirs[:5]},
        )

    return CheckResult(
        check_id="OQ-4",
        name="Directories Present",
        category=CheckCategory.OUTPUT_QUALITY,
        passed=True,
        score=1.0,
        message=f"Directories section valid with {len(directories)} directories",
        evidence={"directory_count": len(directories)},
    )


@register_check("OQ-5")
def check_hierarchy_valid(output: Dict[str, Any]) -> CheckResult:
    """OQ-5: Parent-child relationships are consistent."""
    hierarchy = output.get("hierarchy", {})
    files = output.get("files", {})
    directories = output.get("directories", {})

    if not hierarchy:
        return CheckResult(
            check_id="OQ-5",
            name="Hierarchy Valid",
            category=CheckCategory.OUTPUT_QUALITY,
            passed=False,
            score=0.0,
            message="Hierarchy section missing",
        )

    # Check that all referenced IDs exist
    all_ids: Set[str] = set()

    for file_obj in files.values():
        all_ids.add(file_obj.get("id", ""))

    for dir_obj in directories.values():
        all_ids.add(dir_obj.get("id", ""))

    # Check parents map
    parents = hierarchy.get("parents", {})
    orphan_ids = []

    for child_id, parent_id in parents.items():
        if parent_id not in all_ids:
            orphan_ids.append({"child": child_id, "parent": parent_id})

    if orphan_ids:
        return CheckResult(
            check_id="OQ-5",
            name="Hierarchy Valid",
            category=CheckCategory.OUTPUT_QUALITY,
            passed=False,
            score=0.5,
            message=f"{len(orphan_ids)} orphan references found",
            evidence={"orphans": orphan_ids[:5]},
        )

    return CheckResult(
        check_id="OQ-5",
        name="Hierarchy Valid",
        category=CheckCategory.OUTPUT_QUALITY,
        passed=True,
        score=1.0,
        message="All parent-child relationships valid",
    )


@register_check("OQ-6")
def check_ids_unique(output: Dict[str, Any]) -> CheckResult:
    """OQ-6: No duplicate file or directory IDs."""
    files = output.get("files", {})
    directories = output.get("directories", {})

    all_ids: List[str] = []

    for file_obj in files.values():
        all_ids.append(file_obj.get("id", ""))

    for dir_obj in directories.values():
        all_ids.append(dir_obj.get("id", ""))

    unique_ids = set(all_ids)
    duplicates = len(all_ids) - len(unique_ids)

    if duplicates > 0:
        # Find which IDs are duplicated
        seen = set()
        dup_ids = []
        for id_ in all_ids:
            if id_ in seen:
                dup_ids.append(id_)
            seen.add(id_)

        return CheckResult(
            check_id="OQ-6",
            name="IDs Unique",
            category=CheckCategory.OUTPUT_QUALITY,
            passed=False,
            score=0.0,
            message=f"{duplicates} duplicate IDs found",
            evidence={"duplicate_ids": dup_ids[:10]},
        )

    return CheckResult(
        check_id="OQ-6",
        name="IDs Unique",
        category=CheckCategory.OUTPUT_QUALITY,
        passed=True,
        score=1.0,
        message=f"All {len(all_ids)} IDs are unique",
    )


@register_check("OQ-7")
def check_ids_format(output: Dict[str, Any]) -> CheckResult:
    """OQ-7: IDs follow expected format (f-xxx for files, d-xxx for directories)."""
    files = output.get("files", {})
    directories = output.get("directories", {})

    invalid_file_ids = []
    invalid_dir_ids = []

    for path, file_obj in files.items():
        file_id = file_obj.get("id", "")
        if not file_id.startswith("f-") or len(file_id) != 14:
            invalid_file_ids.append({"path": path, "id": file_id})

    for path, dir_obj in directories.items():
        dir_id = dir_obj.get("id", "")
        if not dir_id.startswith("d-") or len(dir_id) != 14:
            invalid_dir_ids.append({"path": path, "id": dir_id})

    total_invalid = len(invalid_file_ids) + len(invalid_dir_ids)

    if total_invalid > 0:
        return CheckResult(
            check_id="OQ-7",
            name="IDs Format",
            category=CheckCategory.OUTPUT_QUALITY,
            passed=False,
            score=0.5,
            message=f"{total_invalid} IDs have invalid format",
            evidence={
                "invalid_file_ids": invalid_file_ids[:5],
                "invalid_dir_ids": invalid_dir_ids[:5],
            },
        )

    return CheckResult(
        check_id="OQ-7",
        name="IDs Format",
        category=CheckCategory.OUTPUT_QUALITY,
        passed=True,
        score=1.0,
        message="All IDs follow expected format",
    )


@register_check("OQ-8")
def check_statistics_accurate(output: Dict[str, Any]) -> CheckResult:
    """OQ-8: Statistics match actual object counts."""
    stats = output.get("statistics", {})
    files = output.get("files", {})
    directories = output.get("directories", {})

    errors = []

    # Check file count
    expected_files = len(files)
    actual_files = stats.get("total_files", 0)
    if expected_files != actual_files:
        errors.append(f"File count mismatch: stats={actual_files}, actual={expected_files}")

    # Check directory count
    expected_dirs = len(directories)
    actual_dirs = stats.get("total_directories", 0)
    if expected_dirs != actual_dirs:
        errors.append(f"Directory count mismatch: stats={actual_dirs}, actual={expected_dirs}")

    # Check classification counts sum to total files
    by_classification = stats.get("by_classification", {})
    classification_sum = sum(by_classification.values())
    if classification_sum != expected_files:
        errors.append(f"Classification sum mismatch: sum={classification_sum}, files={expected_files}")

    if errors:
        return CheckResult(
            check_id="OQ-8",
            name="Statistics Accurate",
            category=CheckCategory.OUTPUT_QUALITY,
            passed=False,
            score=0.0,
            message="; ".join(errors),
            evidence={"errors": errors},
        )

    return CheckResult(
        check_id="OQ-8",
        name="Statistics Accurate",
        category=CheckCategory.OUTPUT_QUALITY,
        passed=True,
        score=1.0,
        message="All statistics match actual counts",
    )
