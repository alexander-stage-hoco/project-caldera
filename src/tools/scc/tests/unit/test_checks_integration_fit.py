"""Tests for scripts/checks/integration_fit.py - IF-1 to IF-6 checks."""
from __future__ import annotations

import json

import pytest
from scripts.checks.integration_fit import (
    check_output_generated,
    check_all_fields_mapped,
    check_no_data_loss,
    check_metadata_complete,
    check_paths_relative,
    _invalid_relative_path,
    run_integration_fit_checks,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def envelope_output(tmp_path):
    """Create a valid envelope output.json."""
    data = {
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
            "summary": {"total_files": 8, "total_loc": 230},
            "languages": [{"name": "Python"}],
            "files": [
                {"path": "src/main.py"},
                {"path": "src/utils.py"},
            ],
            "directories": [
                {"path": "src"},
                {"path": "tests"},
            ],
        },
    }
    path = tmp_path / "output.json"
    path.write_text(json.dumps(data))
    return path


@pytest.fixture
def raw_output(tmp_path):
    """Create a valid raw scc output."""
    data = [
        {"Name": "Python", "Count": 5, "Code": 150},
        {"Name": "JavaScript", "Count": 3, "Code": 80},
    ]
    path = tmp_path / "raw_scc_output.json"
    path.write_text(json.dumps(data))
    return path


# ---------------------------------------------------------------------------
# Tests: IF-1 Output Generated
# ---------------------------------------------------------------------------

class TestIF1OutputGenerated:
    def test_file_exists(self, envelope_output):
        result = check_output_generated(envelope_output)
        assert result.passed is True
        assert result.check_id == "IF-1"

    def test_file_missing(self, tmp_path):
        result = check_output_generated(tmp_path / "missing.json")
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: IF-3 All Fields Mapped
# ---------------------------------------------------------------------------

class TestIF3AllFieldsMapped:
    def test_all_present(self, envelope_output):
        result = check_all_fields_mapped(envelope_output)
        assert result.passed is True

    def test_missing_summary(self, tmp_path):
        data = {"metadata": {}, "data": {"languages": []}}
        path = tmp_path / "output.json"
        path.write_text(json.dumps(data))
        result = check_all_fields_mapped(path)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: IF-4 No Data Loss
# ---------------------------------------------------------------------------

class TestIF4NoDataLoss:
    def test_totals_match(self, raw_output, envelope_output):
        result = check_no_data_loss(raw_output, envelope_output)
        assert result.passed is True

    def test_totals_mismatch(self, raw_output, tmp_path):
        envelope = {
            "data": {"summary": {"total_files": 999, "total_loc": 999}}
        }
        path = tmp_path / "bad_envelope.json"
        path.write_text(json.dumps(envelope))
        result = check_no_data_loss(raw_output, path)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: IF-5 Metadata Complete
# ---------------------------------------------------------------------------

class TestIF5MetadataComplete:
    def test_complete(self, envelope_output):
        result = check_metadata_complete(envelope_output)
        assert result.passed is True

    def test_missing_field(self, tmp_path):
        data = {"metadata": {"tool_name": "scc"}}
        path = tmp_path / "output.json"
        path.write_text(json.dumps(data))
        result = check_metadata_complete(path)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: IF-6 Paths Relative
# ---------------------------------------------------------------------------

class TestIF6PathsRelative:
    def test_valid_paths(self, envelope_output):
        result = check_paths_relative(envelope_output)
        assert result.passed is True

    def test_absolute_path(self, tmp_path):
        data = {
            "data": {
                "files": [{"path": "/absolute/path.py"}],
                "directories": [],
            }
        }
        path = tmp_path / "output.json"
        path.write_text(json.dumps(data))
        result = check_paths_relative(path)
        assert result.passed is False

    def test_dot_prefix(self, tmp_path):
        data = {
            "data": {
                "files": [{"path": "./relative/path.py"}],
                "directories": [],
            }
        }
        path = tmp_path / "output.json"
        path.write_text(json.dumps(data))
        result = check_paths_relative(path)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: _invalid_relative_path
# ---------------------------------------------------------------------------

class TestInvalidRelativePath:
    def test_valid_path(self):
        assert _invalid_relative_path("src/main.py") is False

    def test_empty_path(self):
        assert _invalid_relative_path("") is True

    def test_absolute_unix(self):
        assert _invalid_relative_path("/src/main.py") is True

    def test_absolute_windows(self):
        assert _invalid_relative_path("C:\\src\\main.py") is True

    def test_dot_prefix(self):
        assert _invalid_relative_path("./src/main.py") is True

    def test_trailing_slash(self):
        assert _invalid_relative_path("src/") is True

    def test_backslash(self):
        assert _invalid_relative_path("src\\main.py") is True

    def test_parent_traversal(self):
        assert _invalid_relative_path("../src/main.py") is True

    def test_windows_drive(self):
        assert _invalid_relative_path("D:src/main.py") is True


# ---------------------------------------------------------------------------
# Tests: run_integration_fit_checks
# ---------------------------------------------------------------------------

class TestRunIntegrationFitChecks:
    def test_returns_6_checks(self, raw_output, envelope_output, tmp_path):
        schema_path = tmp_path / "schema.json"
        schema_path.write_text(json.dumps({"type": "object"}))
        results = run_integration_fit_checks(raw_output, envelope_output, schema_path)
        assert len(results) == 6
        assert all(r.check_id.startswith("IF-") for r in results)
