"""Tests for scripts/checks/coverage.py - language detection and coverage checks."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from scripts.checks import CheckResult
from scripts.checks.coverage import (
    check_python_detected,
    check_csharp_detected,
    check_javascript_detected,
    check_typescript_detected,
    check_go_detected,
    check_rust_detected,
    check_java_detected,
    check_file_counts_match,
    check_loc_within_range,
    run_coverage_checks,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def raw_output_path(tmp_path):
    """Create a raw scc output JSON file."""
    data = [
        {"Name": "Python", "Code": 1000, "Count": 9},
        {"Name": "C#", "Code": 800, "Count": 9},
        {"Name": "JavaScript", "Code": 700, "Count": 9},
        {"Name": "TypeScript", "Code": 600, "Count": 9},
        {"Name": "Go", "Code": 500, "Count": 9},
        {"Name": "Rust", "Code": 400, "Count": 9},
        {"Name": "Java", "Code": 300, "Count": 9},
    ]
    path = tmp_path / "raw_scc_output.json"
    path.write_text(json.dumps(data))
    return path


# ---------------------------------------------------------------------------
# Tests: Language detection checks (CV-1 to CV-7)
# ---------------------------------------------------------------------------

class TestLanguageDetection:
    def test_python_detected(self, raw_output_path):
        result = check_python_detected(raw_output_path)
        assert result.passed is True
        assert result.check_id == "CV-1"

    def test_python_not_detected(self, tmp_path):
        data = [{"Name": "Go", "Code": 100}]
        path = tmp_path / "raw.json"
        path.write_text(json.dumps(data))
        result = check_python_detected(path)
        assert result.passed is False

    def test_csharp_detected(self, raw_output_path):
        result = check_csharp_detected(raw_output_path)
        assert result.passed is True
        assert result.check_id == "CV-2"

    def test_javascript_detected(self, raw_output_path):
        result = check_javascript_detected(raw_output_path)
        assert result.passed is True
        assert result.check_id == "CV-3"

    def test_typescript_detected(self, raw_output_path):
        result = check_typescript_detected(raw_output_path)
        assert result.passed is True
        assert result.check_id == "CV-4"

    def test_go_detected(self, raw_output_path):
        result = check_go_detected(raw_output_path)
        assert result.passed is True
        assert result.check_id == "CV-5"

    def test_rust_detected(self, raw_output_path):
        result = check_rust_detected(raw_output_path)
        assert result.passed is True
        assert result.check_id == "CV-6"

    def test_java_detected(self, raw_output_path):
        result = check_java_detected(raw_output_path)
        assert result.passed is True
        assert result.check_id == "CV-7"

    def test_bad_file_returns_error(self, tmp_path):
        path = tmp_path / "nonexistent.json"
        result = check_python_detected(path)
        assert result.passed is False
        assert "Error" in result.message


# ---------------------------------------------------------------------------
# Tests: CV-8 file counts match
# ---------------------------------------------------------------------------

class TestFileCountsMatch:
    def test_all_match(self, raw_output_path):
        result = check_file_counts_match(raw_output_path, expected_per_lang=9)
        assert result.passed is True
        assert result.check_id == "CV-8"

    def test_mismatch(self, tmp_path):
        data = [
            {"Name": "Python", "Code": 1000, "Count": 5},  # wrong count
            {"Name": "C#", "Code": 800, "Count": 9},
            {"Name": "JavaScript", "Code": 700, "Count": 9},
            {"Name": "TypeScript", "Code": 600, "Count": 9},
            {"Name": "Go", "Code": 500, "Count": 9},
            {"Name": "Rust", "Code": 400, "Count": 9},
            {"Name": "Java", "Code": 300, "Count": 9},
        ]
        path = tmp_path / "raw.json"
        path.write_text(json.dumps(data))
        result = check_file_counts_match(path, expected_per_lang=9)
        assert result.passed is False

    def test_missing_language(self, tmp_path):
        data = [{"Name": "Python", "Code": 1000, "Count": 9}]  # Missing 6 languages
        path = tmp_path / "raw.json"
        path.write_text(json.dumps(data))
        result = check_file_counts_match(path, expected_per_lang=9)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: CV-9 LOC within range
# ---------------------------------------------------------------------------

class TestLocWithinRange:
    def test_within_range(self, raw_output_path):
        # Total: 1000+800+700+600+500+400+300 = 4300
        result = check_loc_within_range(raw_output_path, min_loc=4000, max_loc=5000)
        assert result.passed is True
        assert result.check_id == "CV-9"

    def test_below_range(self, raw_output_path):
        result = check_loc_within_range(raw_output_path, min_loc=10000, max_loc=20000)
        assert result.passed is False

    def test_above_range(self, raw_output_path):
        result = check_loc_within_range(raw_output_path, min_loc=100, max_loc=200)
        assert result.passed is False

    def test_bad_file(self, tmp_path):
        result = check_loc_within_range(tmp_path / "no.json")
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: run_coverage_checks
# ---------------------------------------------------------------------------

class TestRunCoverageChecks:
    def test_returns_11_checks(self, raw_output_path):
        results = run_coverage_checks(raw_output_path)
        assert len(results) == 11
        assert all(isinstance(r, CheckResult) for r in results)
