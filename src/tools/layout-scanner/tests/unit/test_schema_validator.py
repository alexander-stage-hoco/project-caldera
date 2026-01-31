"""
Unit tests for schema_validator.py
"""

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from scripts.schema_validator import (
    FullValidationResult,
    SchemaValidator,
    ValidationResult,
    validate_file,
)


def _create_minimal_valid_output() -> Dict[str, Any]:
    """Create a minimal valid scanner output for testing."""
    return {
        "schema_version": "1.0.0",
        "tool": "layout-scanner",
        "tool_version": "1.0.0",
        "run_id": "layout-20260110-120000-test",
        "timestamp": "2026-01-10T12:00:00Z",
        "repository": "test-repo",
        "repository_path": "/tmp/test-repo",
        "passes_completed": ["filesystem"],
        "statistics": {
            "total_files": 1,
            "total_directories": 1,
            "total_size_bytes": 100,
            "max_depth": 0,
            "scan_duration_ms": 50,
            "files_per_second": 20.0,
            "by_classification": {"source": 1},
            "by_language": {"Python": 1},
        },
        "files": {
            "test.py": {
                "id": "f-000000000001",
                "path": "test.py",
                "name": "test.py",
                "extension": ".py",
                "size_bytes": 100,
                "modified_time": "2026-01-10T12:00:00Z",
                "is_symlink": False,
                "language": "Python",
                "classification": "source",
                "classification_reason": "code file",
                "classification_confidence": 1.0,
                "parent_directory_id": "d-000000000001",
                "depth": 0,
                "first_commit_date": None,
                "last_commit_date": None,
                "commit_count": None,
                "author_count": None,
                "content_hash": None,
                "is_binary": None,
                "line_count": None,
            }
        },
        "directories": {
            ".": {
                "id": "d-000000000001",
                "path": ".",
                "name": "test-repo",
                "modified_time": "2026-01-10T12:00:00Z",
                "is_symlink": False,
                "classification": "source",
                "classification_reason": "majority source",
                "parent_directory_id": None,
                "depth": 0,
                "child_directory_ids": [],
                "child_file_ids": ["f-000000000001"],
                "direct_file_count": 1,
                "direct_directory_count": 0,
                "recursive_file_count": 1,
                "recursive_directory_count": 0,
                "direct_size_bytes": 100,
                "recursive_size_bytes": 100,
                "classification_distribution": {"source": 1},
                "language_distribution": {"Python": 1},
            }
        },
        "hierarchy": {
            "root_id": "d-000000000001",
            "max_depth": 0,
            "total_files": 1,
            "total_directories": 1,
            "total_size_bytes": 100,
            "children": {
                "d-000000000001": ["f-000000000001"],
            },
            "parents": {
                "f-000000000001": "d-000000000001",
            },
            "depth_distribution": {"0": 2},
        },
    }


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_valid_result(self):
        """Valid result should be truthy."""
        result = ValidationResult(valid=True, level="test")
        assert result.valid is True
        assert bool(result) is True

    def test_invalid_result(self):
        """Invalid result should be falsy."""
        result = ValidationResult(valid=False, errors=["error"], level="test")
        assert result.valid is False
        assert bool(result) is False

    def test_default_values(self):
        """Default values should be empty lists."""
        result = ValidationResult(valid=True, level="test")
        assert result.errors == []
        assert result.warnings == []


class TestFullValidationResult:
    """Tests for FullValidationResult dataclass."""

    def test_all_pass(self):
        """All pass should be valid."""
        result = FullValidationResult(
            valid=True,
            schema_result=ValidationResult(valid=True, level="schema"),
            referential_result=ValidationResult(valid=True, level="referential"),
            consistency_result=ValidationResult(valid=True, level="consistency"),
        )
        assert result.valid is True
        assert result.all_errors == []
        assert result.all_warnings == []

    def test_any_fail(self):
        """Any fail should be invalid."""
        result = FullValidationResult(
            valid=False,
            schema_result=ValidationResult(valid=False, errors=["schema error"], level="schema"),
            referential_result=ValidationResult(valid=True, level="referential"),
            consistency_result=ValidationResult(valid=True, level="consistency"),
        )
        assert result.valid is False
        assert "schema error" in result.all_errors

    def test_collects_all_errors(self):
        """Should collect errors from all levels."""
        result = FullValidationResult(
            valid=False,
            schema_result=ValidationResult(valid=False, errors=["e1"], level="schema"),
            referential_result=ValidationResult(valid=False, errors=["e2"], level="referential"),
            consistency_result=ValidationResult(valid=False, errors=["e3"], level="consistency"),
        )
        assert len(result.all_errors) == 3
        assert "e1" in result.all_errors
        assert "e2" in result.all_errors
        assert "e3" in result.all_errors

    def test_collects_all_warnings(self):
        """Should collect warnings from all levels."""
        result = FullValidationResult(
            valid=True,
            schema_result=ValidationResult(valid=True, warnings=["w1"], level="schema"),
            referential_result=ValidationResult(valid=True, warnings=["w2"], level="referential"),
            consistency_result=ValidationResult(valid=True, warnings=["w3"], level="consistency"),
        )
        assert len(result.all_warnings) == 3


class TestSchemaValidatorInit:
    """Tests for SchemaValidator initialization."""

    def test_default_schema_path(self):
        """Should use default schema path."""
        validator = SchemaValidator()
        assert validator.schema_path.name == "layout.json"

    def test_custom_schema_path(self):
        """Should use custom schema path."""
        path = Path("/tmp/custom.json")
        validator = SchemaValidator(schema_path=path)
        assert validator.schema_path == path

    def test_schema_loading(self):
        """Should load schema on first access."""
        validator = SchemaValidator()
        schema = validator.schema
        assert "$schema" in schema
        assert schema["title"] == "Layout Scanner Output"

    def test_schema_caching(self):
        """Schema should be cached."""
        validator = SchemaValidator()
        schema1 = validator.schema
        schema2 = validator.schema
        assert schema1 is schema2


class TestSchemaValidation:
    """Tests for schema validation level."""

    def test_valid_output_passes(self):
        """Valid output should pass schema validation."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        result = validator.validate_schema(output)
        assert result.valid is True
        assert result.errors == []

    def test_missing_required_field(self):
        """Missing required field should fail."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        del output["schema_version"]
        result = validator.validate_schema(output)
        assert result.valid is False
        assert any("schema_version" in e for e in result.errors)

    def test_invalid_type(self):
        """Invalid type should fail."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        output["statistics"]["total_files"] = "not a number"
        result = validator.validate_schema(output)
        assert result.valid is False

    def test_invalid_enum_value(self):
        """Invalid enum value should fail."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        output["files"]["test.py"]["classification"] = "invalid_class"
        result = validator.validate_schema(output)
        assert result.valid is False

    def test_invalid_pattern(self):
        """Invalid pattern should fail."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        output["files"]["test.py"]["id"] = "invalid-id"
        result = validator.validate_schema(output)
        assert result.valid is False

    def test_additional_properties_forbidden(self):
        """Unknown properties should fail with strict schema."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        output["unknown_field"] = "value"
        result = validator.validate_schema(output)
        assert result.valid is False

    def test_truncates_errors(self):
        """Should truncate at 10 errors."""
        validator = SchemaValidator()
        # Create output with many errors
        output = {"invalid": "data"}
        result = validator.validate_schema(output)
        assert len(result.errors) <= 11  # 10 + possible truncation warning


class TestReferentialValidation:
    """Tests for referential integrity validation."""

    def test_valid_references_pass(self):
        """Valid references should pass."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        result = validator.validate_referential(output)
        assert result.valid is True
        assert result.errors == []

    def test_invalid_file_parent_id(self):
        """Invalid file parent_directory_id should fail."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        output["files"]["test.py"]["parent_directory_id"] = "d-nonexistent00"
        result = validator.validate_referential(output)
        assert result.valid is False
        assert any("non-existent parent_directory_id" in e for e in result.errors)

    def test_invalid_directory_parent_id(self):
        """Invalid directory parent_directory_id should fail."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        # Add a subdirectory with invalid parent
        output["directories"]["subdir"] = {
            "id": "d-000000000002",
            "path": "subdir",
            "name": "subdir",
            "modified_time": "2026-01-10T12:00:00Z",
            "is_symlink": False,
            "classification": "source",
            "classification_reason": "test",
            "parent_directory_id": "d-nonexistent00",  # Invalid
            "depth": 1,
            "child_directory_ids": [],
            "child_file_ids": [],
            "direct_file_count": 0,
            "direct_directory_count": 0,
            "recursive_file_count": 0,
            "recursive_directory_count": 0,
            "direct_size_bytes": 0,
            "recursive_size_bytes": 0,
            "classification_distribution": {},
            "language_distribution": {},
        }
        result = validator.validate_referential(output)
        assert result.valid is False

    def test_invalid_child_directory_id(self):
        """Invalid child_directory_id should fail."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        output["directories"]["."]["child_directory_ids"] = ["d-nonexistent00"]
        result = validator.validate_referential(output)
        assert result.valid is False

    def test_invalid_child_file_id(self):
        """Invalid child_file_id should fail."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        output["directories"]["."]["child_file_ids"] = ["f-nonexistent00"]
        result = validator.validate_referential(output)
        assert result.valid is False

    def test_invalid_hierarchy_parent(self):
        """Invalid hierarchy.parents entry should fail."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        output["hierarchy"]["parents"]["f-nonexistent00"] = "d-000000000001"
        result = validator.validate_referential(output)
        assert result.valid is False

    def test_invalid_hierarchy_child(self):
        """Invalid hierarchy.children entry should fail."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        output["hierarchy"]["children"]["d-000000000001"].append("f-nonexistent00")
        result = validator.validate_referential(output)
        assert result.valid is False

    def test_null_parent_id_allowed_for_root(self):
        """Root directory with null parent_id should pass."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        # Root already has null parent_id
        result = validator.validate_referential(output)
        assert result.valid is True


class TestConsistencyValidation:
    """Tests for consistency validation."""

    def test_consistent_data_passes(self):
        """Consistent data should pass."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        result = validator.validate_consistency(output)
        assert result.valid is True
        assert result.errors == []

    def test_file_count_mismatch(self):
        """Mismatched file count should fail."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        output["statistics"]["total_files"] = 999
        result = validator.validate_consistency(output)
        assert result.valid is False
        assert any("total_files" in e for e in result.errors)

    def test_directory_count_mismatch(self):
        """Mismatched directory count should fail."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        output["statistics"]["total_directories"] = 999
        result = validator.validate_consistency(output)
        assert result.valid is False
        assert any("total_directories" in e for e in result.errors)

    def test_classification_sum_mismatch(self):
        """Mismatched classification sum should fail."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        output["statistics"]["by_classification"] = {"source": 5}  # Wrong sum
        result = validator.validate_consistency(output)
        assert result.valid is False
        assert any("by_classification" in e for e in result.errors)

    def test_language_sum_mismatch(self):
        """Mismatched language sum should fail."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        output["statistics"]["by_language"] = {"Python": 5}  # Wrong sum
        result = validator.validate_consistency(output)
        assert result.valid is False
        assert any("by_language" in e for e in result.errors)

    def test_hierarchy_file_count_mismatch(self):
        """Mismatched hierarchy.total_files should fail."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        output["hierarchy"]["total_files"] = 999
        result = validator.validate_consistency(output)
        assert result.valid is False

    def test_hierarchy_directory_count_mismatch(self):
        """Mismatched hierarchy.total_directories should fail."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        output["hierarchy"]["total_directories"] = 999
        result = validator.validate_consistency(output)
        assert result.valid is False

    def test_invalid_root_id(self):
        """Invalid hierarchy.root_id should fail."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        output["hierarchy"]["root_id"] = "d-nonexistent00"
        result = validator.validate_consistency(output)
        assert result.valid is False

    def test_size_mismatch_is_warning(self):
        """Size mismatch should be a warning, not error."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        output["statistics"]["total_size_bytes"] = 999
        result = validator.validate_consistency(output)
        # This is a warning, not an error
        assert any("total_size_bytes" in w for w in result.warnings)


class TestFullValidation:
    """Tests for full validation."""

    def test_all_levels_pass(self):
        """Valid output should pass all levels."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        result = validator.validate(output)
        assert result.valid is True
        assert result.schema_result.valid is True
        assert result.referential_result.valid is True
        assert result.consistency_result.valid is True

    def test_schema_fail_makes_invalid(self):
        """Schema failure should make result invalid."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        del output["schema_version"]
        result = validator.validate(output)
        assert result.valid is False
        assert result.schema_result.valid is False

    def test_referential_fail_makes_invalid(self):
        """Referential failure should make result invalid."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        output["files"]["test.py"]["parent_directory_id"] = "d-nonexistent00"
        result = validator.validate(output)
        assert result.valid is False
        assert result.referential_result.valid is False

    def test_consistency_fail_makes_invalid(self):
        """Consistency failure should make result invalid."""
        validator = SchemaValidator()
        output = _create_minimal_valid_output()
        output["statistics"]["total_files"] = 999
        result = validator.validate(output)
        assert result.valid is False
        assert result.consistency_result.valid is False


class TestValidateFile:
    """Tests for validate_file function."""

    def test_validates_json_file(self, tmp_path):
        """Should validate a JSON file."""
        output_file = tmp_path / "output.json"
        output = _create_minimal_valid_output()
        output_file.write_text(json.dumps(output))

        result = validate_file(output_file)
        assert result.valid is True

    def test_invalid_json_raises(self, tmp_path):
        """Should raise on invalid JSON."""
        output_file = tmp_path / "output.json"
        output_file.write_text("not valid json")

        with pytest.raises(json.JSONDecodeError):
            validate_file(output_file)


class TestCLI:
    """Tests for CLI functionality."""

    def test_main_valid_file(self, tmp_path):
        """CLI should return 0 for valid file."""
        from scripts.schema_validator import main

        output_file = tmp_path / "output.json"
        output = _create_minimal_valid_output()
        output_file.write_text(json.dumps(output))

        result = main([str(output_file)])
        assert result == 0

    def test_main_invalid_file(self, tmp_path):
        """CLI should return 1 for invalid file."""
        from scripts.schema_validator import main

        output_file = tmp_path / "output.json"
        output_file.write_text('{"invalid": true}')

        result = main([str(output_file)])
        assert result == 1

    def test_main_missing_file(self, tmp_path):
        """CLI should return 1 for missing file."""
        from scripts.schema_validator import main

        result = main([str(tmp_path / "nonexistent.json")])
        assert result == 1

    def test_main_json_output(self, tmp_path, capsys):
        """CLI should output JSON when requested."""
        from scripts.schema_validator import main

        output_file = tmp_path / "output.json"
        output = _create_minimal_valid_output()
        output_file.write_text(json.dumps(output))

        main([str(output_file), "--json"])
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["valid"] is True

    def test_main_specific_level(self, tmp_path):
        """CLI should support specific validation level."""
        from scripts.schema_validator import main

        output_file = tmp_path / "output.json"
        output = _create_minimal_valid_output()
        output_file.write_text(json.dumps(output))

        result = main([str(output_file), "--level", "schema"])
        assert result == 0
