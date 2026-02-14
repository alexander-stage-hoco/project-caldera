"""Tests for scripts/validate.py - output validation logic."""
from __future__ import annotations

import json

import pytest
from scripts.validate import (
    validate_structure,
    validate_summary,
    validate_with_schema,
    generate_report,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_output():
    """A fully valid scc envelope output."""
    return {
        "metadata": {
            "tool_name": "scc",
            "tool_version": "3.6.0",
            "run_id": "abc-123",
            "repo_id": "my-repo",
            "branch": "main",
            "commit": "a" * 40,
            "timestamp": "2026-01-01T00:00:00Z",
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "scc",
            "tool_version": "3.6.0",
            "summary": {
                "total_files": 10,
                "total_loc": 500,
                "total_code": 400,
                "total_comment": 50,
                "total_blank": 50,
                "total_complexity": 20,
                "languages_detected": 3,
            },
            "languages": [
                {"name": "Python", "files": 5, "code": 300, "comment": 30, "complexity": 15},
            ],
        },
    }


# ---------------------------------------------------------------------------
# Tests: validate_structure
# ---------------------------------------------------------------------------

class TestValidateStructure:
    """Tests for validate_structure function."""

    def test_valid_output_has_no_errors(self, valid_output):
        errors = validate_structure(valid_output)
        assert errors == []

    def test_missing_metadata_reports_error(self, valid_output):
        del valid_output["metadata"]
        errors = validate_structure(valid_output)
        assert any("metadata" in e for e in errors)

    def test_missing_data_reports_error(self, valid_output):
        del valid_output["data"]
        errors = validate_structure(valid_output)
        assert any("data" in e for e in errors)

    def test_missing_metadata_field(self, valid_output):
        del valid_output["metadata"]["run_id"]
        errors = validate_structure(valid_output)
        assert any("run_id" in e for e in errors)

    def test_empty_metadata_field(self, valid_output):
        valid_output["metadata"]["branch"] = ""
        errors = validate_structure(valid_output)
        assert any("branch" in e for e in errors)

    def test_missing_data_fields(self, valid_output):
        del valid_output["data"]["summary"]
        errors = validate_structure(valid_output)
        assert any("summary" in e for e in errors)

    def test_missing_all_required_metadata(self):
        output = {"metadata": {}, "data": {"tool": "scc", "tool_version": "3.6.0",
                                           "summary": {"total_files": 1, "total_loc": 1},
                                           "languages": []}}
        errors = validate_structure(output)
        # Should report errors for all 8 metadata fields
        assert len(errors) >= 8


# ---------------------------------------------------------------------------
# Tests: validate_summary
# ---------------------------------------------------------------------------

class TestValidateSummary:
    """Tests for validate_summary function."""

    def test_valid_summary(self):
        summary = {"total_files": 10, "total_loc": 500, "total_code": 400}
        errors = validate_summary(summary)
        assert errors == []

    def test_missing_required_field(self):
        summary = {"total_code": 400}
        errors = validate_summary(summary)
        assert any("total_files" in e for e in errors)
        assert any("total_loc" in e for e in errors)

    def test_non_numeric_field(self):
        summary = {"total_files": "ten", "total_loc": 500}
        errors = validate_summary(summary)
        assert any("total_files" in e and "number" in e for e in errors)

    def test_float_is_valid_numeric(self):
        summary = {"total_files": 10, "total_loc": 500.5}
        errors = validate_summary(summary)
        assert errors == []


# ---------------------------------------------------------------------------
# Tests: validate_with_schema
# ---------------------------------------------------------------------------

class TestValidateWithSchema:
    """Tests for validate_with_schema function."""

    def test_valid_against_simple_schema(self):
        output = {"name": "test", "value": 42}
        schema = {
            "type": "object",
            "required": ["name", "value"],
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "integer"},
            },
        }
        errors = validate_with_schema(output, schema)
        assert errors == []

    def test_invalid_against_schema(self):
        output = {"name": 123}
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
        errors = validate_with_schema(output, schema)
        # Either jsonschema is installed and reports error, or reports not installed
        assert len(errors) >= 1


# ---------------------------------------------------------------------------
# Tests: generate_report
# ---------------------------------------------------------------------------

class TestGenerateReport:
    """Tests for generate_report function."""

    def test_passing_report(self, valid_output, tmp_path):
        report_path = tmp_path / "report.md"
        generate_report(valid_output, [], report_path)

        content = report_path.read_text()
        assert "PASSED" in content
        assert "Validation Report" in content

    def test_failing_report(self, valid_output, tmp_path):
        report_path = tmp_path / "report.md"
        errors = ["Missing field: foo", "Invalid type: bar"]
        generate_report(valid_output, errors, report_path)

        content = report_path.read_text()
        assert "FAILED" in content
        assert "2 error" in content
        assert "Missing field: foo" in content

    def test_report_includes_evidence_summary(self, valid_output, tmp_path):
        report_path = tmp_path / "report.md"
        generate_report(valid_output, [], report_path)

        content = report_path.read_text()
        assert "Evidence Summary" in content
        assert "10" in content  # total_files
        assert "500" in content  # total_loc

    def test_report_includes_language_table(self, valid_output, tmp_path):
        report_path = tmp_path / "report.md"
        generate_report(valid_output, [], report_path)

        content = report_path.read_text()
        assert "Language Summary" in content
        assert "Python" in content

    def test_report_with_empty_data(self, tmp_path):
        output = {"metadata": {}, "data": {}}
        report_path = tmp_path / "report.md"
        generate_report(output, [], report_path)

        content = report_path.read_text()
        assert "Validation Report" in content
