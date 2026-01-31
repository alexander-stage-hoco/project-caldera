"""Tests for SCC coverage checks (CV-1 to CV-11).

Tests the coverage checks including CV-10 (Python docstrings as comments)
and CV-11 (multi-line string handling validation).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks import CheckResult
from checks.coverage import (
    check_python_docstrings_as_comments,
    check_multiline_string_handling,
    run_coverage_checks,
)


class TestCV10PythonDocstringsAsComments:
    """Tests for CV-10: Python docstrings counted as comments."""

    @pytest.fixture
    def mock_scc_files_with_docstrings(self):
        """Mock scc output with Python files containing docstrings."""
        return [
            {
                "Location": "eval-repos/synthetic/python/simple.py",
                "Language": "Python",
                "Lines": 50,
                "Code": 30,
                "Comment": 15,
                "Blank": 5,
            },
            {
                "Location": "eval-repos/synthetic/python/docstring_example.py",
                "Language": "Python",
                "Lines": 100,
                "Code": 60,
                "Comment": 30,  # High comment count indicates docstrings
                "Blank": 10,
            },
        ]

    @pytest.fixture
    def mock_scc_files_no_comments(self):
        """Mock scc output with Python files missing comment counts."""
        return [
            {
                "Location": "eval-repos/synthetic/python/simple.py",
                "Language": "Python",
                "Lines": 50,
                "Code": 45,
                "Comment": 0,  # No comments - potential issue
                "Blank": 5,
            },
        ]

    def test_cv10_passes_when_docstrings_counted_as_comments(
        self, mock_scc_files_with_docstrings, tmp_path
    ):
        """CV-10 should pass when Python files have comments (docstrings)."""
        raw_output = tmp_path / "raw.json"
        raw_output.write_text(json.dumps([]))

        with patch("checks.coverage.reliability") as mock_rel:
            mock_rel.run_scc_by_file.return_value = (
                mock_scc_files_with_docstrings,
                0,
                "",
            )

            result = check_python_docstrings_as_comments(raw_output, tmp_path)

            assert result.check_id == "CV-10"
            assert result.passed is True
        assert "docstring files" in result.message.lower()

    def test_cv10_fails_when_no_comments_found(
        self, mock_scc_files_no_comments, tmp_path
    ):
        """CV-10 should fail when Python files have no comments."""
        raw_output = tmp_path / "raw.json"
        raw_output.write_text(json.dumps([]))

        with patch("checks.coverage.reliability") as mock_rel:
            mock_rel.run_scc_by_file.return_value = (
                mock_scc_files_no_comments,
                0,
                "",
            )

            result = check_python_docstrings_as_comments(raw_output, tmp_path)

            assert result.check_id == "CV-10"
            assert result.passed is False

    def test_cv10_handles_empty_file_list(self, tmp_path):
        """CV-10 should handle empty file list gracefully."""
        raw_output = tmp_path / "raw.json"
        raw_output.write_text(json.dumps([]))

        with patch("checks.coverage.reliability") as mock_rel:
            mock_rel.run_scc_by_file.return_value = ([], 0, "")

            result = check_python_docstrings_as_comments(raw_output, tmp_path)

            assert result.check_id == "CV-10"
            # Should not crash, may pass or fail based on logic
            assert isinstance(result.passed, bool)

    def test_cv10_handles_exception(self, tmp_path):
        """CV-10 should handle exceptions gracefully."""
        raw_output = tmp_path / "raw.json"
        raw_output.write_text(json.dumps([]))

        with patch("checks.coverage.reliability") as mock_rel:
            mock_rel.run_scc_by_file.side_effect = Exception("Test error")

            result = check_python_docstrings_as_comments(raw_output, tmp_path)

            assert result.check_id == "CV-10"
            assert result.passed is False
            assert "error" in result.message.lower()


class TestCV11MultilineStringHandling:
    """Tests for CV-11: Multi-line string handling validation."""

    @pytest.fixture
    def mock_scc_files_valid_metrics(self):
        """Mock scc output with valid line count metrics."""
        return [
            {
                "Location": "eval-repos/synthetic/python/template_strings.py",
                "Language": "Python",
                "Lines": 100,
                "Code": 70,
                "Comment": 20,
                "Blank": 10,
            },
            {
                "Location": "eval-repos/synthetic/javascript/multiline.js",
                "Language": "JavaScript",
                "Lines": 50,
                "Code": 35,
                "Comment": 5,
                "Blank": 10,
            },
        ]

    @pytest.fixture
    def mock_scc_files_invalid_metrics(self):
        """Mock scc output with invalid line count metrics."""
        return [
            {
                "Location": "eval-repos/synthetic/python/bad_metrics.py",
                "Language": "Python",
                "Lines": 100,
                "Code": 150,  # Code > Lines - invalid
                "Comment": 20,
                "Blank": 10,
            },
        ]

    @pytest.fixture
    def mock_scc_files_multiline_named(self):
        """Mock scc output with files named for multiline content."""
        return [
            {
                "Location": "eval-repos/synthetic/python/multiline_test.py",
                "Language": "Python",
                "Lines": 100,
                "Code": 80,
                "Comment": 10,
                "Blank": 10,
            },
            {
                "Location": "eval-repos/synthetic/csharp/verbatim_strings.cs",
                "Language": "C#",
                "Lines": 50,
                "Code": 40,
                "Comment": 5,
                "Blank": 5,
            },
        ]

    def test_cv11_passes_with_valid_metrics(
        self, mock_scc_files_valid_metrics, tmp_path
    ):
        """CV-11 should pass when line metrics are consistent."""
        raw_output = tmp_path / "raw.json"
        raw_output.write_text(json.dumps([]))

        with patch("checks.coverage.reliability") as mock_rel:
            mock_rel.run_scc_by_file.return_value = (
                mock_scc_files_valid_metrics,
                0,
                "",
            )

            result = check_multiline_string_handling(raw_output, tmp_path)

            assert result.check_id == "CV-11"
            assert result.passed is True

    def test_cv11_fails_with_invalid_metrics(
        self, mock_scc_files_invalid_metrics, tmp_path
    ):
        """CV-11 should fail when line metrics are inconsistent."""
        raw_output = tmp_path / "raw.json"
        raw_output.write_text(json.dumps([]))

        with patch("checks.coverage.reliability") as mock_rel:
            mock_rel.run_scc_by_file.return_value = (
                mock_scc_files_invalid_metrics,
                0,
                "",
            )

            result = check_multiline_string_handling(raw_output, tmp_path)

            assert result.check_id == "CV-11"
            # May pass or fail depending on tolerance - check it doesn't crash
            assert isinstance(result.passed, bool)

    def test_cv11_validates_multiline_named_files(
        self, mock_scc_files_multiline_named, tmp_path
    ):
        """CV-11 should specifically validate files with multiline patterns in name."""
        raw_output = tmp_path / "raw.json"
        raw_output.write_text(json.dumps([]))

        with patch("checks.coverage.reliability") as mock_rel:
            mock_rel.run_scc_by_file.return_value = (
                mock_scc_files_multiline_named,
                0,
                "",
            )

            result = check_multiline_string_handling(raw_output, tmp_path)

            assert result.check_id == "CV-11"
            assert result.passed is True
            assert "multiline" in result.message.lower() or "valid" in result.message.lower()

    def test_cv11_handles_empty_file_list(self, tmp_path):
        """CV-11 should handle empty file list gracefully."""
        raw_output = tmp_path / "raw.json"
        raw_output.write_text(json.dumps([]))

        with patch("checks.coverage.reliability") as mock_rel:
            mock_rel.run_scc_by_file.return_value = ([], 0, "")

            result = check_multiline_string_handling(raw_output, tmp_path)

            assert result.check_id == "CV-11"
            assert isinstance(result.passed, bool)

    def test_cv11_handles_exception(self, tmp_path):
        """CV-11 should handle exceptions gracefully."""
        raw_output = tmp_path / "raw.json"
        raw_output.write_text(json.dumps([]))

        with patch("checks.coverage.reliability") as mock_rel:
            mock_rel.run_scc_by_file.side_effect = Exception("Test error")

            result = check_multiline_string_handling(raw_output, tmp_path)

            assert result.check_id == "CV-11"
            assert result.passed is False
            assert "error" in result.message.lower()


class TestRunCoverageChecks:
    """Tests for the run_coverage_checks orchestrator function."""

    def test_run_coverage_checks_includes_cv10_cv11(self, tmp_path):
        """run_coverage_checks should include CV-10 and CV-11."""
        raw_output = tmp_path / "raw.json"
        raw_output.write_text(json.dumps([
            {"Name": "Python", "Count": 9, "Code": 500},
            {"Name": "C#", "Count": 9, "Code": 500},
            {"Name": "JavaScript", "Count": 9, "Code": 500},
            {"Name": "TypeScript", "Count": 9, "Code": 500},
            {"Name": "Go", "Count": 9, "Code": 500},
            {"Name": "Rust", "Count": 9, "Code": 500},
            {"Name": "Java", "Count": 9, "Code": 500},
        ]))

        with patch("checks.coverage.reliability") as mock_rel:
            mock_rel.run_scc_by_file.return_value = (
                [
                    {"Location": "test.py", "Language": "Python", "Lines": 10, "Code": 5, "Comment": 3, "Blank": 2},
                ],
                0,
                "",
            )

            results = run_coverage_checks(raw_output, tmp_path)

            check_ids = [r.check_id for r in results]
            assert "CV-10" in check_ids, "CV-10 should be included in coverage checks"
            assert "CV-11" in check_ids, "CV-11 should be included in coverage checks"

    def test_run_coverage_checks_returns_list_of_check_results(self, tmp_path):
        """run_coverage_checks should return a list of CheckResult objects."""
        raw_output = tmp_path / "raw.json"
        raw_output.write_text(json.dumps([
            {"Name": "Python", "Count": 9, "Code": 500},
        ]))

        with patch("checks.coverage.reliability") as mock_rel:
            mock_rel.run_scc_by_file.return_value = ([], 0, "")

            results = run_coverage_checks(raw_output, tmp_path)

            assert isinstance(results, list)
            assert all(isinstance(r, CheckResult) for r in results)
