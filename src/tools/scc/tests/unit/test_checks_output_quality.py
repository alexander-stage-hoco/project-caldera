"""Tests for scripts/checks/output_quality.py - OQ-1 to OQ-8 checks."""
from __future__ import annotations

import json

import pytest
from scripts.checks.output_quality import (
    check_json_valid,
    check_array_structure,
    check_required_fields,
    check_numeric_types,
    check_non_empty_output,
    check_bytes_present,
    check_complexity_present,
    check_no_parse_errors,
    run_output_quality_checks,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_scc_json(tmp_path):
    """Create a valid scc JSON output file."""
    data = [
        {
            "Name": "Python",
            "Count": 5,
            "Lines": 200,
            "Code": 150,
            "Comment": 30,
            "Blank": 20,
            "Bytes": 5000,
            "Complexity": 12,
        },
        {
            "Name": "JavaScript",
            "Count": 3,
            "Lines": 100,
            "Code": 80,
            "Comment": 10,
            "Blank": 10,
            "Bytes": 2000,
            "Complexity": 5,
        },
    ]
    path = tmp_path / "raw_scc_output.json"
    path.write_text(json.dumps(data))
    return path


@pytest.fixture
def invalid_json_file(tmp_path):
    """Create a file with invalid JSON."""
    path = tmp_path / "bad.json"
    path.write_text("{not valid json")
    return path


@pytest.fixture
def dict_json_file(tmp_path):
    """Create a file with a JSON dict (not array)."""
    path = tmp_path / "dict.json"
    path.write_text(json.dumps({"key": "value"}))
    return path


@pytest.fixture
def empty_array_json(tmp_path):
    """Create a file with an empty JSON array."""
    path = tmp_path / "empty.json"
    path.write_text(json.dumps([]))
    return path


# ---------------------------------------------------------------------------
# Tests: OQ-1 JSON Valid
# ---------------------------------------------------------------------------

class TestOQ1JsonValid:
    def test_valid_json(self, valid_scc_json):
        result = check_json_valid(valid_scc_json)
        assert result.passed is True
        assert result.check_id == "OQ-1"

    def test_invalid_json(self, invalid_json_file):
        result = check_json_valid(invalid_json_file)
        assert result.passed is False

    def test_missing_file(self, tmp_path):
        result = check_json_valid(tmp_path / "nonexistent.json")
        assert result.passed is False
        assert "not found" in result.message.lower()


# ---------------------------------------------------------------------------
# Tests: OQ-2 Array Structure
# ---------------------------------------------------------------------------

class TestOQ2ArrayStructure:
    def test_is_array(self, valid_scc_json):
        result = check_array_structure(valid_scc_json)
        assert result.passed is True

    def test_is_dict(self, dict_json_file):
        result = check_array_structure(dict_json_file)
        assert result.passed is False
        assert result.actual == "dict"


# ---------------------------------------------------------------------------
# Tests: OQ-3 Required Fields
# ---------------------------------------------------------------------------

class TestOQ3RequiredFields:
    def test_all_fields_present(self, valid_scc_json):
        result = check_required_fields(valid_scc_json)
        assert result.passed is True

    def test_missing_field(self, tmp_path):
        data = [{"Name": "Python", "Count": 5}]  # Missing Lines, Code, etc.
        path = tmp_path / "incomplete.json"
        path.write_text(json.dumps(data))
        result = check_required_fields(path)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: OQ-4 Numeric Types
# ---------------------------------------------------------------------------

class TestOQ4NumericTypes:
    def test_all_valid(self, valid_scc_json):
        result = check_numeric_types(valid_scc_json)
        assert result.passed is True

    def test_negative_value(self, tmp_path):
        data = [{"Name": "Python", "Count": -1, "Lines": 10, "Code": 5,
                 "Comment": 2, "Blank": 3}]
        path = tmp_path / "negative.json"
        path.write_text(json.dumps(data))
        result = check_numeric_types(path)
        assert result.passed is False

    def test_string_value(self, tmp_path):
        data = [{"Name": "Python", "Count": "five", "Lines": 10, "Code": 5,
                 "Comment": 2, "Blank": 3}]
        path = tmp_path / "string.json"
        path.write_text(json.dumps(data))
        result = check_numeric_types(path)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: OQ-5 Non-Empty Output
# ---------------------------------------------------------------------------

class TestOQ5NonEmptyOutput:
    def test_non_empty(self, valid_scc_json):
        result = check_non_empty_output(valid_scc_json)
        assert result.passed is True

    def test_empty_array(self, empty_array_json):
        result = check_non_empty_output(empty_array_json)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: OQ-6 Bytes Present
# ---------------------------------------------------------------------------

class TestOQ6BytesPresent:
    def test_bytes_present(self, valid_scc_json):
        result = check_bytes_present(valid_scc_json)
        assert result.passed is True

    def test_bytes_missing(self, tmp_path):
        data = [{"Name": "Python", "Count": 5, "Lines": 10, "Code": 5,
                 "Comment": 2, "Blank": 3, "Complexity": 1}]
        path = tmp_path / "no_bytes.json"
        path.write_text(json.dumps(data))
        result = check_bytes_present(path)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: OQ-7 Complexity Present
# ---------------------------------------------------------------------------

class TestOQ7ComplexityPresent:
    def test_complexity_present(self, valid_scc_json):
        result = check_complexity_present(valid_scc_json)
        assert result.passed is True

    def test_complexity_missing(self, tmp_path):
        data = [{"Name": "Python", "Count": 5, "Lines": 10, "Code": 5,
                 "Comment": 2, "Blank": 3, "Bytes": 100}]
        path = tmp_path / "no_cx.json"
        path.write_text(json.dumps(data))
        result = check_complexity_present(path)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: OQ-8 No Parse Errors
# ---------------------------------------------------------------------------

class TestOQ8NoParseErrors:
    def test_clean_run(self):
        result = check_no_parse_errors(0, "")
        assert result.passed is True

    def test_nonzero_exit(self):
        result = check_no_parse_errors(1, "")
        assert result.passed is False

    def test_error_in_stderr(self):
        result = check_no_parse_errors(0, "panic: runtime error")
        assert result.passed is False

    def test_warning_is_ok(self):
        result = check_no_parse_errors(0, "warning: something")
        assert result.passed is True


# ---------------------------------------------------------------------------
# Tests: run_output_quality_checks (runner)
# ---------------------------------------------------------------------------

class TestRunOutputQualityChecks:
    def test_returns_8_checks(self, valid_scc_json):
        results = run_output_quality_checks(valid_scc_json, 0, "")
        assert len(results) == 8
        assert all(r.check_id.startswith("OQ-") for r in results)
