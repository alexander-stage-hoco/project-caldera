"""
Schema Validator for Layout Scanner Output.

Provides three-level validation:
1. Schema: JSON Schema validation using jsonschema library
2. Referential: All parent_directory_id references exist
3. Consistency: Statistics match actual file/directory counts
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema


@dataclass
class ValidationResult:
    """Result of a validation check."""

    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    level: str = "unknown"

    def __bool__(self) -> bool:
        """Return True if validation passed."""
        return self.valid


@dataclass
class FullValidationResult:
    """Combined result of all validation levels."""

    valid: bool
    schema_result: ValidationResult
    referential_result: ValidationResult
    consistency_result: ValidationResult

    @property
    def all_errors(self) -> List[str]:
        """Get all errors from all levels."""
        return (
            self.schema_result.errors
            + self.referential_result.errors
            + self.consistency_result.errors
        )

    @property
    def all_warnings(self) -> List[str]:
        """Get all warnings from all levels."""
        return (
            self.schema_result.warnings
            + self.referential_result.warnings
            + self.consistency_result.warnings
        )


class SchemaValidator:
    """
    Three-level output validation for Layout Scanner.

    Levels:
    1. Schema: JSON structure, types, patterns, required fields
    2. Referential: parent_directory_id references valid directories
    3. Consistency: statistics.total_files == len(files), etc.
    """

    DEFAULT_SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "layout.json"

    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize validator.

        Args:
            schema_path: Path to JSON schema file. Uses default if not provided.
        """
        self.schema_path = schema_path or self.DEFAULT_SCHEMA_PATH
        self._schema: Optional[Dict[str, Any]] = None

    @property
    def schema(self) -> Dict[str, Any]:
        """Load and cache the JSON schema."""
        if self._schema is None:
            self._schema = self._load_schema()
        return self._schema

    def _load_schema(self) -> Dict[str, Any]:
        """Load JSON schema from file."""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")

        with open(self.schema_path) as f:
            return json.load(f)

    def validate(self, output: Dict[str, Any]) -> FullValidationResult:
        """
        Run all validation levels.

        Args:
            output: Scanner output dictionary to validate

        Returns:
            FullValidationResult with results from all levels
        """
        schema_result = self.validate_schema(output)
        referential_result = self.validate_referential(output)
        consistency_result = self.validate_consistency(output)

        # Overall valid only if all levels pass
        valid = (
            schema_result.valid
            and referential_result.valid
            and consistency_result.valid
        )

        return FullValidationResult(
            valid=valid,
            schema_result=schema_result,
            referential_result=referential_result,
            consistency_result=consistency_result,
        )

    def validate_schema(self, output: Dict[str, Any]) -> ValidationResult:
        """
        Level 1: JSON Schema validation using jsonschema library.

        Validates:
        - All required fields present
        - Field types match schema
        - Values match patterns (IDs, timestamps)
        - Enums have valid values
        """
        errors: List[str] = []
        warnings: List[str] = []

        try:
            jsonschema.validate(output, self.schema)
        except jsonschema.ValidationError as e:
            # Collect the error and any context
            path = ".".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
            errors.append(f"Schema error at '{path}': {e.message}")

            # Try to get additional errors using a validator
            validator = jsonschema.Draft202012Validator(self.schema)
            for error in validator.iter_errors(output):
                if error.message != e.message:  # Skip the first error we already have
                    err_path = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
                    errors.append(f"Schema error at '{err_path}': {error.message}")
                    if len(errors) >= 10:  # Limit errors
                        warnings.append("More than 10 schema errors found, truncating")
                        break

        except jsonschema.SchemaError as e:
            errors.append(f"Invalid schema: {e.message}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            level="schema",
        )

    def validate_referential(self, output: Dict[str, Any]) -> ValidationResult:
        """
        Level 2: Referential integrity validation.

        Validates:
        - All parent_directory_id references point to existing directories
        - All child_directory_ids reference existing directories
        - All child_file_ids reference existing files
        - hierarchy.parents map references valid IDs
        - hierarchy.children map references valid IDs
        """
        errors: List[str] = []
        warnings: List[str] = []

        files = output.get("files", {})
        directories = output.get("directories", {})
        hierarchy = output.get("hierarchy", {})

        # Build ID sets
        file_ids = {f.get("id") for f in files.values() if f.get("id")}
        dir_ids = {d.get("id") for d in directories.values() if d.get("id")}
        all_ids = file_ids | dir_ids

        # Check file parent_directory_id references
        for path, file_obj in files.items():
            parent_id = file_obj.get("parent_directory_id")
            if parent_id and parent_id not in dir_ids:
                errors.append(
                    f"File '{path}' references non-existent parent_directory_id: {parent_id}"
                )
                if len(errors) >= 20:
                    warnings.append("More than 20 referential errors found, truncating")
                    break

        # Check directory parent_directory_id references
        if len(errors) < 20:
            for path, dir_obj in directories.items():
                parent_id = dir_obj.get("parent_directory_id")
                # Root directory has null parent_id, that's valid
                if parent_id is not None and parent_id not in dir_ids:
                    errors.append(
                        f"Directory '{path}' references non-existent parent_directory_id: {parent_id}"
                    )
                    if len(errors) >= 20:
                        warnings.append("More than 20 referential errors found, truncating")
                        break

        # Check directory child_directory_ids
        if len(errors) < 20:
            for path, dir_obj in directories.items():
                for child_id in dir_obj.get("child_directory_ids", []):
                    if child_id not in dir_ids:
                        errors.append(
                            f"Directory '{path}' references non-existent child_directory_id: {child_id}"
                        )
                        if len(errors) >= 20:
                            warnings.append("More than 20 referential errors found, truncating")
                            break

        # Check directory child_file_ids
        if len(errors) < 20:
            for path, dir_obj in directories.items():
                for child_id in dir_obj.get("child_file_ids", []):
                    if child_id not in file_ids:
                        errors.append(
                            f"Directory '{path}' references non-existent child_file_id: {child_id}"
                        )
                        if len(errors) >= 20:
                            warnings.append("More than 20 referential errors found, truncating")
                            break

        # Check hierarchy.parents map
        if len(errors) < 20:
            parents = hierarchy.get("parents", {})
            for child_id, parent_id in parents.items():
                if child_id not in all_ids:
                    errors.append(
                        f"hierarchy.parents references non-existent child: {child_id}"
                    )
                if parent_id not in all_ids:
                    errors.append(
                        f"hierarchy.parents references non-existent parent: {parent_id}"
                    )
                if len(errors) >= 20:
                    warnings.append("More than 20 referential errors found, truncating")
                    break

        # Check hierarchy.children map
        if len(errors) < 20:
            children = hierarchy.get("children", {})
            for parent_id, child_ids in children.items():
                if parent_id not in all_ids:
                    errors.append(
                        f"hierarchy.children references non-existent parent: {parent_id}"
                    )
                for child_id in child_ids:
                    if child_id not in all_ids:
                        errors.append(
                            f"hierarchy.children references non-existent child: {child_id}"
                        )
                if len(errors) >= 20:
                    warnings.append("More than 20 referential errors found, truncating")
                    break

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            level="referential",
        )

    def validate_consistency(self, output: Dict[str, Any]) -> ValidationResult:
        """
        Level 3: Consistency validation.

        Validates:
        - statistics.total_files == len(files)
        - statistics.total_directories == len(directories)
        - statistics.by_classification sums to total_files
        - statistics.by_language sums to total_files
        - hierarchy.total_files == len(files)
        - hierarchy.total_directories == len(directories)
        """
        errors: List[str] = []
        warnings: List[str] = []

        files = output.get("files", {})
        directories = output.get("directories", {})
        stats = output.get("statistics", {})
        hierarchy = output.get("hierarchy", {})

        actual_file_count = len(files)
        actual_dir_count = len(directories)

        # Check statistics.total_files
        stats_total_files = stats.get("total_files")
        if stats_total_files is not None and stats_total_files != actual_file_count:
            errors.append(
                f"statistics.total_files ({stats_total_files}) != actual file count ({actual_file_count})"
            )

        # Check statistics.total_directories
        stats_total_dirs = stats.get("total_directories")
        if stats_total_dirs is not None and stats_total_dirs != actual_dir_count:
            errors.append(
                f"statistics.total_directories ({stats_total_dirs}) != actual directory count ({actual_dir_count})"
            )

        # Check statistics.by_classification sums to total
        by_classification = stats.get("by_classification", {})
        classification_sum = sum(by_classification.values())
        if by_classification and classification_sum != actual_file_count:
            errors.append(
                f"statistics.by_classification sum ({classification_sum}) != actual file count ({actual_file_count})"
            )

        # Check statistics.by_language sums to total
        by_language = stats.get("by_language", {})
        language_sum = sum(by_language.values())
        if by_language and language_sum != actual_file_count:
            errors.append(
                f"statistics.by_language sum ({language_sum}) != actual file count ({actual_file_count})"
            )

        # Check hierarchy totals
        hierarchy_total_files = hierarchy.get("total_files")
        if hierarchy_total_files is not None and hierarchy_total_files != actual_file_count:
            errors.append(
                f"hierarchy.total_files ({hierarchy_total_files}) != actual file count ({actual_file_count})"
            )

        hierarchy_total_dirs = hierarchy.get("total_directories")
        if hierarchy_total_dirs is not None and hierarchy_total_dirs != actual_dir_count:
            errors.append(
                f"hierarchy.total_directories ({hierarchy_total_dirs}) != actual directory count ({actual_dir_count})"
            )

        # Check that hierarchy.root_id exists in directories
        root_id = hierarchy.get("root_id")
        if root_id:
            dir_ids = {d.get("id") for d in directories.values()}
            if root_id not in dir_ids:
                errors.append(
                    f"hierarchy.root_id ({root_id}) does not exist in directories"
                )

        # Check total_size_bytes consistency
        stats_size = stats.get("total_size_bytes")
        if stats_size is not None:
            actual_size = sum(f.get("size_bytes", 0) for f in files.values())
            if stats_size != actual_size:
                warnings.append(
                    f"statistics.total_size_bytes ({stats_size}) != sum of file sizes ({actual_size})"
                )

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            level="consistency",
        )


def validate_file(
    file_path: Path,
    schema_path: Optional[Path] = None,
    verbose: bool = False,
) -> FullValidationResult:
    """
    Validate a scanner output file.

    Args:
        file_path: Path to JSON output file
        schema_path: Optional path to schema file
        verbose: Print detailed output

    Returns:
        FullValidationResult with all validation results
    """
    with open(file_path) as f:
        output = json.load(f)

    validator = SchemaValidator(schema_path)
    result = validator.validate(output)

    if verbose:
        print(f"Validating: {file_path}")
        print(f"  Schema:      {'PASS' if result.schema_result.valid else 'FAIL'}")
        print(f"  Referential: {'PASS' if result.referential_result.valid else 'FAIL'}")
        print(f"  Consistency: {'PASS' if result.consistency_result.valid else 'FAIL'}")

        if result.all_errors:
            print("\nErrors:")
            for error in result.all_errors:
                print(f"  - {error}")

        if result.all_warnings:
            print("\nWarnings:")
            for warning in result.all_warnings:
                print(f"  - {warning}")

    return result


def main(args: Optional[List[str]] = None) -> int:
    """CLI entry point for standalone validation."""
    parser = argparse.ArgumentParser(
        description="Validate Layout Scanner output files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "file",
        type=Path,
        help="JSON output file to validate",
    )

    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Path to JSON schema (default: schemas/layout.json)",
    )

    parser.add_argument(
        "--level",
        choices=["schema", "referential", "consistency", "all"],
        default="all",
        help="Validation level to run (default: all)",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )

    parsed = parser.parse_args(args)

    if not parsed.file.exists():
        print(f"Error: File not found: {parsed.file}", file=sys.stderr)
        return 1

    try:
        with open(parsed.file) as f:
            output = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        return 1

    validator = SchemaValidator(parsed.schema)

    # Run requested validation levels
    if parsed.level == "all":
        result = validator.validate(output)
        errors = result.all_errors
        warnings = result.all_warnings
        valid = result.valid
    elif parsed.level == "schema":
        level_result = validator.validate_schema(output)
        errors = level_result.errors
        warnings = level_result.warnings
        valid = level_result.valid
    elif parsed.level == "referential":
        level_result = validator.validate_referential(output)
        errors = level_result.errors
        warnings = level_result.warnings
        valid = level_result.valid
    else:  # consistency
        level_result = validator.validate_consistency(output)
        errors = level_result.errors
        warnings = level_result.warnings
        valid = level_result.valid

    # Output results
    if parsed.json:
        json_output = {
            "file": str(parsed.file),
            "valid": valid,
            "level": parsed.level,
            "errors": errors,
            "warnings": warnings,
        }
        print(json.dumps(json_output, indent=2))
    else:
        if parsed.verbose:
            print(f"Validating: {parsed.file}")
            print(f"Level: {parsed.level}")
            print()

        if valid:
            print("Validation PASSED")
        else:
            print("Validation FAILED")
            print()
            print("Errors:")
            for error in errors:
                print(f"  - {error}")

        if warnings:
            print()
            print("Warnings:")
            for warning in warnings:
                print(f"  - {warning}")

    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
