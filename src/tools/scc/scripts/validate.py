#!/usr/bin/env python3
"""Validate scc output against JSON schema."""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

try:
    from jsonschema import Draft7Validator
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


def load_json(path: Path) -> dict:
    """Load JSON file."""
    with open(path) as f:
        return json.load(f)


def validate_structure(output: dict) -> list:
    """Validate basic structure without jsonschema."""
    errors = []

    required_fields = ["metadata", "data"]
    for field in required_fields:
        if field not in output:
            errors.append(f"Missing required field: {field}")

    metadata = output.get("metadata", {})
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
        if not metadata.get(field):
            errors.append(f"metadata: Missing required field '{field}'")

    data = output.get("data", {})
    required_data = ["tool", "tool_version", "summary", "languages"]
    for field in required_data:
        if field not in data:
            errors.append(f"data: Missing required field '{field}'")

    if "summary" in data:
        summary_errors = validate_summary(data["summary"])
        errors.extend(summary_errors)

    return errors


def validate_summary(summary: dict) -> list:
    """Validate summary section."""
    errors = []

    required_fields = ["total_files", "total_loc"]
    for field in required_fields:
        if field not in summary:
            errors.append(f"summary: Missing required field '{field}'")

    numeric_fields = [
        "total_files",
        "total_loc",
        "total_code",
        "total_comment",
        "total_blank",
        "total_complexity",
        "languages_detected",
    ]
    for field in numeric_fields:
        if field in summary and not isinstance(summary[field], (int, float)):
            errors.append(f"summary.{field}: Expected number, got {type(summary[field]).__name__}")

    return errors


def validate_with_schema(output: dict, schema: dict) -> list:
    """Validate using JSON Schema if available."""
    if not JSONSCHEMA_AVAILABLE:
        return ["jsonschema not installed, skipping schema validation"]

    errors = []
    validator = Draft7Validator(schema)
    for error in validator.iter_errors(output):
        path = ".".join(str(p) for p in error.absolute_path) or "(root)"
        errors.append(f"Schema validation error at {path}: {error.message}")

    return errors


def generate_report(output: dict, errors: list, output_path: Path) -> None:
    """Generate validation report."""
    timestamp = datetime.now().isoformat()
    metadata = output.get("metadata", {})
    data = output.get("data", {})

    report = [
        "# Validation Report",
        "",
        f"**Generated:** {timestamp}",
        f"**Run ID:** {metadata.get('run_id', 'N/A')}",
        "",
        "## Summary",
        "",
    ]

    if not errors:
        report.extend([
            "**Status: PASSED**",
            "",
            "All validation checks passed successfully.",
            "",
        ])
    else:
        report.extend([
            f"**Status: FAILED** ({len(errors)} error(s))",
            "",
            "### Errors",
            "",
        ])
        for error in errors:
            report.append(f"- {error}")
        report.append("")

    if "summary" in data:
        summary = data["summary"]
        report.extend([
            "## Evidence Summary",
            "",
            f"- **Total Files:** {summary.get('total_files', 'N/A')}",
            f"- **Total LOC:** {summary.get('total_loc', 'N/A')}",
            f"- **Total Complexity:** {summary.get('total_complexity', 'N/A')}",
            "",
        ])

    if "languages" in data:
        report.extend([
            "## Language Summary",
            "",
            "| Language | Files | LOC | Comments | Complexity |",
            "|----------|------:|----:|---------:|-----------:|",
        ])
        for item in data["languages"]:
            report.append(
                f"| {item.get('name', 'N/A')} | "
                f"{item.get('files', 0)} | "
                f"{item.get('code', 0)} | "
                f"{item.get('comment', 0)} | "
                f"{item.get('complexity', 0)} |"
            )
        report.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(report))


def main():
    """Main entry point."""
    evaluation_dir = Path("evaluation") / "results"
    outputs_root = Path("outputs")
    output_dir = None

    if (evaluation_dir / "output.json").exists():
        output_dir = evaluation_dir
    elif outputs_root.exists():
        candidates = [
            p for p in outputs_root.iterdir()
            if p.is_dir() and (p / "output.json").exists()
        ]
        if candidates:
            output_dir = max(candidates, key=lambda p: p.stat().st_mtime)

    if output_dir is None:
        output_dir = Path("output")

    output_path = output_dir / "output.json"
    schema_path = Path("schemas/output.schema.json")
    report_path = output_dir / "validation_report.md"

    print(f"Loading output from {output_path}...")
    output = load_json(output_path)

    print("Validating structure...")
    errors = validate_structure(output)

    if schema_path.exists():
        print(f"Loading schema from {schema_path}...")
        schema = load_json(schema_path)
        print("Validating against JSON schema...")
        schema_errors = validate_with_schema(output, schema)
        errors.extend(schema_errors)
    else:
        print(f"Schema file not found at {schema_path}, skipping schema validation")

    print(f"Generating report at {report_path}...")
    generate_report(output, errors, report_path)

    if errors:
        print(f"\nValidation FAILED with {len(errors)} error(s):")
        for error in errors[:10]:
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
        return 1

    print("\nValidation PASSED!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
