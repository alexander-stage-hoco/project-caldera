"""Unit tests for checks module helper functions."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from checks import (
    load_analysis,
    load_ground_truth,
    load_all_ground_truth,
    normalize_path,
    get_file_from_analysis,
    get_issues_by_category,
    get_issues_by_severity,
    get_language_stats,
    count_findings_for_file,
    count_findings_by_category,
)


class TestLoadAnalysis:
    """Tests for load_analysis function."""

    def test_load_caldera_envelope_format(self, tmp_path: Path) -> None:
        """load_analysis should handle Caldera envelope format."""
        analysis_data = {
            "data": {
                "tool": "devskim",
                "files": [{"path": "test.cs"}],
            },
            "metadata": {"run_id": "123"},
        }
        analysis_file = tmp_path / "analysis.json"
        analysis_file.write_text(json.dumps(analysis_data))

        result = load_analysis(str(analysis_file))

        assert result["tool"] == "devskim"
        assert result["files"] == [{"path": "test.cs"}]
        assert "_root" in result
        assert result["_root"]["metadata"]["run_id"] == "123"

    def test_load_older_envelope_format(self, tmp_path: Path) -> None:
        """load_analysis should handle older results format."""
        analysis_data = {
            "results": {
                "tool": "devskim",
                "files": [{"path": "test.cs"}],
            },
        }
        analysis_file = tmp_path / "analysis.json"
        analysis_file.write_text(json.dumps(analysis_data))

        result = load_analysis(str(analysis_file))

        assert result["tool"] == "devskim"
        assert result["files"] == [{"path": "test.cs"}]
        assert "_root" in result

    def test_load_raw_format(self, tmp_path: Path) -> None:
        """load_analysis should handle raw JSON format."""
        analysis_data = {
            "tool": "devskim",
            "files": [{"path": "test.cs"}],
        }
        analysis_file = tmp_path / "analysis.json"
        analysis_file.write_text(json.dumps(analysis_data))

        result = load_analysis(str(analysis_file))

        assert result["tool"] == "devskim"
        assert "_root" not in result


class TestLoadGroundTruth:
    """Tests for load_ground_truth function."""

    def test_load_existing_ground_truth(self, tmp_path: Path) -> None:
        """load_ground_truth should load existing file."""
        gt_data = {"language": "csharp", "files": []}
        gt_file = tmp_path / "csharp.json"
        gt_file.write_text(json.dumps(gt_data))

        result = load_ground_truth(str(tmp_path), "csharp")

        assert result is not None
        assert result["language"] == "csharp"

    def test_load_missing_ground_truth(self, tmp_path: Path) -> None:
        """load_ground_truth should return None for missing file."""
        result = load_ground_truth(str(tmp_path), "nonexistent")
        assert result is None


class TestLoadAllGroundTruth:
    """Tests for load_all_ground_truth function."""

    def test_load_all_ground_truth(self, tmp_path: Path) -> None:
        """load_all_ground_truth should load all JSON files."""
        (tmp_path / "csharp.json").write_text('{"language": "csharp"}')
        (tmp_path / "python.json").write_text('{"language": "python"}')

        result = load_all_ground_truth(str(tmp_path))

        assert len(result) == 2
        assert "csharp" in result
        assert "python" in result


class TestNormalizePath:
    """Tests for normalize_path function."""

    def test_normalize_leading_dot_slash(self) -> None:
        """normalize_path should remove leading ./"""
        assert normalize_path("./src/file.cs") == "src/file.cs"

    def test_normalize_leading_slash(self) -> None:
        """normalize_path should remove leading /"""
        assert normalize_path("/src/file.cs") == "src/file.cs"

    def test_normalize_clean_path(self) -> None:
        """normalize_path should preserve clean paths."""
        assert normalize_path("src/file.cs") == "src/file.cs"

    def test_normalize_strips_whitespace(self) -> None:
        """normalize_path should strip whitespace."""
        assert normalize_path("  src/file.cs  ") == "src/file.cs"


class TestGetFileFromAnalysis:
    """Tests for get_file_from_analysis function."""

    def test_find_exact_match(self) -> None:
        """get_file_from_analysis should find exact path match."""
        analysis = {
            "files": [
                {"path": "src/file1.cs", "issues": []},
                {"path": "src/file2.cs", "issues": []},
            ]
        }

        result = get_file_from_analysis(analysis, "src/file1.cs")

        assert result is not None
        assert result["path"] == "src/file1.cs"

    def test_find_with_leading_slash(self) -> None:
        """get_file_from_analysis should normalize paths."""
        analysis = {
            "files": [{"path": "src/file.cs", "issues": []}]
        }

        result = get_file_from_analysis(analysis, "/src/file.cs")

        assert result is not None

    def test_not_found(self) -> None:
        """get_file_from_analysis should return None for missing file."""
        analysis = {"files": [{"path": "src/file.cs", "issues": []}]}

        result = get_file_from_analysis(analysis, "other/file.cs")

        assert result is None


class TestGetIssuesByCategory:
    """Tests for get_issues_by_category function."""

    def test_count_issues_by_category(self) -> None:
        """get_issues_by_category should count correctly."""
        analysis = {
            "files": [
                {
                    "path": "test.cs",
                    "issues": [
                        {"dd_category": "sql_injection"},
                        {"dd_category": "sql_injection"},
                        {"dd_category": "insecure_crypto"},
                    ],
                }
            ]
        }

        result = get_issues_by_category(analysis)

        assert result["sql_injection"] == 2
        assert result["insecure_crypto"] == 1
        assert result["xss"] == 0

    def test_unknown_category(self) -> None:
        """get_issues_by_category should count unknown categories."""
        analysis = {
            "files": [
                {
                    "path": "test.cs",
                    "issues": [{"dd_category": "some_new_category"}],
                }
            ]
        }

        result = get_issues_by_category(analysis)

        assert result["unknown"] == 1


class TestGetIssuesBySeverity:
    """Tests for get_issues_by_severity function."""

    def test_count_issues_by_severity(self) -> None:
        """get_issues_by_severity should count correctly."""
        analysis = {
            "files": [
                {
                    "path": "test.cs",
                    "issues": [
                        {"severity": "CRITICAL"},
                        {"severity": "HIGH"},
                        {"severity": "HIGH"},
                    ],
                }
            ]
        }

        result = get_issues_by_severity(analysis)

        assert result["CRITICAL"] == 1
        assert result["HIGH"] == 2
        assert result["MEDIUM"] == 0


class TestGetLanguageStats:
    """Tests for get_language_stats function."""

    def test_get_language_stats(self) -> None:
        """get_language_stats should aggregate by language."""
        analysis = {
            "files": [
                {
                    "path": "test.cs",
                    "language": "csharp",
                    "issues": [{"dd_category": "sql_injection"}],
                },
                {
                    "path": "test.py",
                    "language": "python",
                    "issues": [],
                },
            ]
        }

        result = get_language_stats(analysis)

        assert "csharp" in result
        assert "python" in result
        assert result["csharp"]["files"] == 1
        assert result["csharp"]["issues"] == 1


class TestCountFindings:
    """Tests for count findings functions."""

    def test_count_findings_for_file(self) -> None:
        """count_findings_for_file should count correctly."""
        analysis = {
            "files": [
                {
                    "path": "test.cs",
                    "issues": [
                        {"dd_category": "sql_injection"},
                        {"dd_category": "insecure_crypto"},
                    ],
                }
            ]
        }

        assert count_findings_for_file(analysis, "test.cs") == 2
        assert count_findings_for_file(analysis, "test.cs", category="sql_injection") == 1
        assert count_findings_for_file(analysis, "missing.cs") == 0

    def test_count_findings_by_category(self) -> None:
        """count_findings_by_category should count correctly."""
        analysis = {
            "files": [
                {
                    "path": "test.cs",
                    "issues": [
                        {"dd_category": "sql_injection"},
                        {"dd_category": "sql_injection"},
                    ],
                }
            ]
        }

        assert count_findings_by_category(analysis, "sql_injection") == 2
        assert count_findings_by_category(analysis, "xss") == 0
