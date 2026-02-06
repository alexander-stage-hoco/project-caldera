"""Unit tests for analyze.py module.

This module tests the analyze.py CLI functions by importing from the scripts package.
"""

from __future__ import annotations

import json
import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Import from scripts package (conftest.py sets up the path)
from scripts.analyze import (
    result_to_data_dict,
    _directory_stats_to_dict,
    to_envelope_format,
    main,
    TOOL_VERSION,
    SCHEMA_VERSION,
)
from security_analyzer import (
    AnalysisResult,
    FileStats,
    SecurityFinding,
    DirectoryEntry,
    DirectoryStats,
    LanguageStats,
)


class TestResultToDataDict:
    """Tests for result_to_data_dict function."""

    def test_empty_result(self, empty_analysis_result: AnalysisResult) -> None:
        """Empty result should produce valid data dict."""
        data = result_to_data_dict(empty_analysis_result)

        assert data["tool"] == "devskim"
        assert data["summary"]["total_files"] == 0
        assert data["summary"]["total_issues"] == 0
        assert data["files"] == []
        assert data["directories"] == []

    def test_result_with_files(self, mock_analysis_result: AnalysisResult) -> None:
        """Result with files should serialize correctly."""
        data = result_to_data_dict(mock_analysis_result)

        assert data["tool"] == "devskim"
        assert data["summary"]["total_files"] == 1
        assert data["summary"]["files_with_issues"] == 1
        assert data["summary"]["total_issues"] == 1
        assert len(data["files"]) == 1

        file_data = data["files"][0]
        assert file_data["path"] == "src/Crypto.cs"
        assert file_data["language"] == "csharp"
        assert file_data["lines"] == 150
        assert file_data["issue_count"] == 1

    def test_result_with_directories(self, mock_analysis_result: AnalysisResult) -> None:
        """Result with directories should serialize correctly."""
        data = result_to_data_dict(mock_analysis_result)

        assert len(data["directories"]) == 1
        dir_data = data["directories"][0]
        assert dir_data["path"] == "src"
        assert dir_data["name"] == "src"
        assert dir_data["depth"] == 1
        assert dir_data["is_leaf"] is True

    def test_result_with_languages(self, mock_analysis_result: AnalysisResult) -> None:
        """Result with language stats should serialize correctly."""
        data = result_to_data_dict(mock_analysis_result)

        assert "csharp" in data["by_language"]
        lang_data = data["by_language"]["csharp"]
        assert lang_data["files"] == 1
        assert lang_data["lines"] == 150
        assert lang_data["issue_count"] == 1
        assert "insecure_crypto" in lang_data["categories_covered"]

    def test_issue_density_rounding(self) -> None:
        """Issue density should be rounded to 4 decimal places."""
        file_stats = FileStats(
            path="test.cs",
            language="csharp",
            lines=100,
            issue_count=3,
            issue_density=0.123456789,
        )
        result = AnalysisResult(
            generated_at="2026-01-22T00:00:00Z",
            repo_name="test",
            repo_path="/tmp/test",
            files=[file_stats],
        )

        data = result_to_data_dict(result)
        assert data["files"][0]["issue_density"] == 0.1235

    def test_issues_serialization(self, mock_analysis_result: AnalysisResult) -> None:
        """Issues should be fully serialized with all fields."""
        data = result_to_data_dict(mock_analysis_result)

        issue = data["files"][0]["issues"][0]
        assert issue["rule_id"] == "DS126858"
        assert issue["cwe_ids"] == ["CWE-328"]
        assert issue["dd_category"] == "insecure_crypto"
        assert issue["line_start"] == 10
        assert issue["line_end"] == 10
        assert issue["column_start"] == 5
        assert issue["column_end"] == 30
        assert issue["severity"] == "HIGH"
        assert issue["message"] == "Weak hash algorithm MD5"
        assert issue["code_snippet"] == "var hash = MD5.Create();"


class TestDirectoryStatsToDict:
    """Tests for _directory_stats_to_dict function."""

    def test_empty_stats(self) -> None:
        """Empty stats should produce valid dict."""
        stats = DirectoryStats()
        d = _directory_stats_to_dict(stats)

        assert d["file_count"] == 0
        assert d["lines_code"] == 0
        assert d["issue_count"] == 0
        assert d["by_category"] == {}
        assert d["by_severity"] == {}
        assert d["issue_density"] == 0

    def test_stats_with_values(self) -> None:
        """Stats with values should serialize correctly."""
        stats = DirectoryStats(
            file_count=5,
            lines_code=500,
            issue_count=10,
            by_category={"insecure_crypto": 8, "sql_injection": 2},
            by_severity={"HIGH": 6, "MEDIUM": 4},
            issue_density=2.0,
        )
        d = _directory_stats_to_dict(stats)

        assert d["file_count"] == 5
        assert d["lines_code"] == 500
        assert d["issue_count"] == 10
        assert d["by_category"]["insecure_crypto"] == 8
        assert d["by_severity"]["HIGH"] == 6
        assert d["issue_density"] == 2.0

    def test_zero_density_handling(self) -> None:
        """Zero density should return 0, not None."""
        stats = DirectoryStats(
            file_count=5,
            lines_code=500,
            issue_count=0,
            issue_density=None,
        )
        d = _directory_stats_to_dict(stats)
        assert d["issue_density"] == 0


class TestToEnvelopeFormat:
    """Tests for to_envelope_format function."""

    def test_envelope_structure(self) -> None:
        """Envelope should have correct structure."""
        data = {"tool": "devskim", "files": []}

        with patch("scripts.analyze.create_envelope") as mock_create:
            mock_create.return_value = {
                "data": data,
                "metadata": {"tool": "devskim"},
            }

            result = to_envelope_format(
                data,
                run_id="run-123",
                repo_id="repo-456",
                branch="main",
                commit="abc123",
                timestamp="2026-01-22T00:00:00Z",
                devskim_version="1.0.28",
            )

            mock_create.assert_called_once_with(
                data,
                tool_name="devskim",
                tool_version="1.0.28",
                run_id="run-123",
                repo_id="repo-456",
                branch="main",
                commit="abc123",
                timestamp="2026-01-22T00:00:00Z",
                schema_version=SCHEMA_VERSION,
            )

    def test_envelope_passes_params(self) -> None:
        """Envelope should pass all params to create_envelope."""
        data = {"tool": "devskim"}

        with patch("scripts.analyze.create_envelope") as mock_create:
            mock_create.return_value = {"data": data}

            to_envelope_format(
                data,
                run_id="custom-run",
                repo_id="custom-repo",
                branch="feature/test",
                commit="def456",
                timestamp="2026-02-01T12:00:00Z",
                devskim_version="2.0.0",
            )

            call_args = mock_create.call_args
            assert call_args[1]["run_id"] == "custom-run"
            assert call_args[1]["repo_id"] == "custom-repo"
            assert call_args[1]["branch"] == "feature/test"
            assert call_args[1]["commit"] == "def456"

    def test_schema_version_constant(self) -> None:
        """Schema version constant should be defined."""
        assert SCHEMA_VERSION == "1.0.0"

    def test_tool_version_constant(self) -> None:
        """Tool version constant should be defined."""
        assert TOOL_VERSION == "1.0.0"


class TestAnalyzeIntegration:
    """Integration tests for analyze.py CLI.

    These tests verify the CLI behavior by running the analyze module as a script.
    """

    def test_result_to_data_dict_end_to_end(self, mock_analysis_result: AnalysisResult) -> None:
        """End-to-end test of result_to_data_dict conversion."""
        data = result_to_data_dict(mock_analysis_result)

        # Verify complete structure
        assert data["tool"] == "devskim"
        assert data["tool_version"] == "1.0.28"

        # Verify summary
        summary = data["summary"]
        assert summary["total_files"] == 1
        assert summary["total_directories"] == 1
        assert summary["files_with_issues"] == 1
        assert summary["total_issues"] == 1
        assert summary["total_lines"] == 150

        # Verify files serialization
        assert len(data["files"]) == 1
        file_data = data["files"][0]
        assert file_data["path"] == "src/Crypto.cs"
        assert len(file_data["issues"]) == 1

        # Verify directories serialization
        assert len(data["directories"]) == 1
        dir_data = data["directories"][0]
        assert dir_data["path"] == "src"

        # Verify language stats
        assert "csharp" in data["by_language"]

        # Verify metadata
        assert data["analysis_duration_ms"] == 500
        assert data["rules_used"] == ["DS126858"]

    def test_data_dict_json_serializable(self, mock_analysis_result: AnalysisResult) -> None:
        """Data dict should be fully JSON serializable."""
        data = result_to_data_dict(mock_analysis_result)

        # This should not raise
        json_str = json.dumps(data, indent=2)
        assert len(json_str) > 0

        # Round-trip should work
        parsed = json.loads(json_str)
        assert parsed["tool"] == "devskim"

    def test_multiple_files_handling(self) -> None:
        """Multiple files should be handled correctly."""
        finding1 = SecurityFinding(
            rule_id="DS126858",
            dd_category="insecure_crypto",
            cwe_ids=["CWE-328"],
            file_path="src/Crypto.cs",
            line_start=10,
            line_end=10,
            column_start=5,
            column_end=30,
            severity="HIGH",
            message="Weak hash",
        )
        finding2 = SecurityFinding(
            rule_id="DS104456",
            dd_category="sql_injection",
            cwe_ids=["CWE-89"],
            file_path="src/Database.cs",
            line_start=25,
            line_end=25,
            column_start=1,
            column_end=50,
            severity="CRITICAL",
            message="SQL injection",
        )

        file1 = FileStats(
            path="src/Crypto.cs",
            language="csharp",
            lines=100,
            issue_count=1,
            issue_density=1.0,
            issues=[finding1],
        )
        file2 = FileStats(
            path="src/Database.cs",
            language="csharp",
            lines=200,
            issue_count=1,
            issue_density=0.5,
            issues=[finding2],
        )

        result = AnalysisResult(
            generated_at="2026-01-22T00:00:00Z",
            repo_name="test",
            repo_path="/tmp/test",
            files=[file1, file2],
            findings=[finding1, finding2],
        )

        data = result_to_data_dict(result)

        assert data["summary"]["total_files"] == 2
        assert data["summary"]["total_issues"] == 2
        assert data["summary"]["total_lines"] == 300
        assert len(data["files"]) == 2

    def test_empty_issues_file(self) -> None:
        """Files with no issues should be handled correctly."""
        file_stats = FileStats(
            path="src/Clean.cs",
            language="csharp",
            lines=50,
            issue_count=0,
            issue_density=0.0,
            issues=[],
        )

        result = AnalysisResult(
            generated_at="2026-01-22T00:00:00Z",
            repo_name="test",
            repo_path="/tmp/test",
            files=[file_stats],
        )

        data = result_to_data_dict(result)

        assert data["summary"]["files_with_issues"] == 0
        assert data["files"][0]["issues"] == []


class TestMain:
    """Tests for main() function."""

    @patch("scripts.analyze.display_dashboard")
    @patch("scripts.analyze.get_devskim_version", return_value="1.0.28")
    @patch("scripts.analyze.analyze_with_devskim")
    @patch("scripts.analyze.validate_common_args")
    def test_main_basic(
        self,
        mock_validate,
        mock_analyze,
        mock_version,
        mock_dashboard,
        mock_analysis_result,
        tmp_path,
    ) -> None:
        """Basic main execution should work."""
        output_file = tmp_path / "output.json"

        # Setup mock common args
        mock_common = MagicMock()
        mock_common.repo_path = tmp_path
        mock_common.repo_name = "test-repo"
        mock_common.repo_id = "repo-123"
        mock_common.run_id = "run-456"
        mock_common.branch = "main"
        mock_common.commit = "abc123"
        mock_common.output_path = output_file
        mock_validate.return_value = mock_common

        mock_analyze.return_value = mock_analysis_result

        test_args = [
            "analyze",
            "--repo-path", str(tmp_path),
            "--output", str(output_file),
        ]

        with patch("sys.argv", test_args):
            main()

        # Verify analysis was called
        mock_analyze.assert_called_once()

        # Verify dashboard was called
        mock_dashboard.assert_called_once_with(mock_analysis_result)

        # Verify output file was created
        assert output_file.exists()
        output_data = json.loads(output_file.read_text())
        assert "data" in output_data

    @patch("scripts.analyze.display_dashboard")
    @patch("scripts.analyze.get_devskim_version", return_value="1.0.28")
    @patch("scripts.analyze.analyze_with_devskim")
    @patch("scripts.analyze.validate_common_args")
    @patch("scripts.analyze.set_color_enabled")
    def test_main_no_color(
        self,
        mock_set_color,
        mock_validate,
        mock_analyze,
        mock_version,
        mock_dashboard,
        mock_analysis_result,
        tmp_path,
    ) -> None:
        """--no-color flag should disable colors."""
        output_file = tmp_path / "output.json"

        mock_common = MagicMock()
        mock_common.repo_path = tmp_path
        mock_common.repo_name = "test-repo"
        mock_common.repo_id = "repo-123"
        mock_common.run_id = "run-456"
        mock_common.branch = "main"
        mock_common.commit = "abc123"
        mock_common.output_path = output_file
        mock_validate.return_value = mock_common

        mock_analyze.return_value = mock_analysis_result

        test_args = [
            "analyze",
            "--repo-path", str(tmp_path),
            "--output", str(output_file),
            "--no-color",
        ]

        with patch("sys.argv", test_args):
            main()

        mock_set_color.assert_called_with(False)

    @patch("scripts.analyze.display_dashboard")
    @patch("scripts.analyze.get_devskim_version", return_value="1.0.28")
    @patch("scripts.analyze.analyze_with_devskim")
    @patch("scripts.analyze.validate_common_args")
    def test_main_json_only(
        self,
        mock_validate,
        mock_analyze,
        mock_version,
        mock_dashboard,
        mock_analysis_result,
        tmp_path,
    ) -> None:
        """--json-only flag should skip dashboard."""
        output_file = tmp_path / "output.json"

        mock_common = MagicMock()
        mock_common.repo_path = tmp_path
        mock_common.repo_name = "test-repo"
        mock_common.repo_id = "repo-123"
        mock_common.run_id = "run-456"
        mock_common.branch = "main"
        mock_common.commit = "abc123"
        mock_common.output_path = output_file
        mock_validate.return_value = mock_common

        mock_analyze.return_value = mock_analysis_result

        test_args = [
            "analyze",
            "--repo-path", str(tmp_path),
            "--output", str(output_file),
            "--json-only",
        ]

        with patch("sys.argv", test_args):
            main()

        # Dashboard should NOT be called
        mock_dashboard.assert_not_called()

    @patch("scripts.analyze.display_dashboard")
    @patch("scripts.analyze.get_devskim_version", return_value="1.0.28")
    @patch("scripts.analyze.analyze_with_devskim")
    @patch("scripts.analyze.validate_common_args")
    def test_main_custom_rules(
        self,
        mock_validate,
        mock_analyze,
        mock_version,
        mock_dashboard,
        mock_analysis_result,
        tmp_path,
    ) -> None:
        """--custom-rules should pass rules path to analyzer."""
        output_file = tmp_path / "output.json"
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()

        mock_common = MagicMock()
        mock_common.repo_path = tmp_path
        mock_common.repo_name = "test-repo"
        mock_common.repo_id = "repo-123"
        mock_common.run_id = "run-456"
        mock_common.branch = "main"
        mock_common.commit = "abc123"
        mock_common.output_path = output_file
        mock_validate.return_value = mock_common

        mock_analyze.return_value = mock_analysis_result

        test_args = [
            "analyze",
            "--repo-path", str(tmp_path),
            "--output", str(output_file),
            "--json-only",
            "--custom-rules", str(rules_dir),
        ]

        with patch("sys.argv", test_args):
            main()

        # Verify analyze was called with custom rules path
        mock_analyze.assert_called_once()
        call_args = mock_analyze.call_args
        # custom_rules_path is the 4th positional arg
        assert call_args[0][3] == str(rules_dir)

    @patch("scripts.analyze.display_dashboard")
    @patch("scripts.analyze.get_devskim_version", return_value="1.0.28")
    @patch("scripts.analyze.analyze_with_devskim")
    @patch("scripts.analyze.validate_common_args")
    def test_main_sets_repo_name_env(
        self,
        mock_validate,
        mock_analyze,
        mock_version,
        mock_dashboard,
        mock_analysis_result,
        tmp_path,
    ) -> None:
        """REPO_NAME env var should be set for security_analyzer."""
        output_file = tmp_path / "output.json"

        mock_common = MagicMock()
        mock_common.repo_path = tmp_path
        mock_common.repo_name = "my-test-repo"
        mock_common.repo_id = "repo-123"
        mock_common.run_id = "run-456"
        mock_common.branch = "main"
        mock_common.commit = "abc123"
        mock_common.output_path = output_file
        mock_validate.return_value = mock_common

        mock_analyze.return_value = mock_analysis_result

        test_args = [
            "analyze",
            "--repo-path", str(tmp_path),
            "--output", str(output_file),
            "--json-only",
        ]

        with patch("sys.argv", test_args):
            main()

        assert os.environ.get("REPO_NAME") == "my-test-repo"

    @patch("scripts.analyze.display_dashboard")
    @patch("scripts.analyze.get_devskim_version", return_value="1.0.28")
    @patch("scripts.analyze.analyze_with_devskim")
    @patch("scripts.analyze.validate_common_args")
    def test_main_output_content(
        self,
        mock_validate,
        mock_analyze,
        mock_version,
        mock_dashboard,
        mock_analysis_result,
        tmp_path,
    ) -> None:
        """Output file should contain valid JSON with envelope structure."""
        output_file = tmp_path / "output.json"

        mock_common = MagicMock()
        mock_common.repo_path = tmp_path
        mock_common.repo_name = "test-repo"
        mock_common.repo_id = "repo-123"
        mock_common.run_id = "run-456"
        mock_common.branch = "main"
        mock_common.commit = "abc123"
        mock_common.output_path = output_file
        mock_validate.return_value = mock_common

        mock_analyze.return_value = mock_analysis_result

        test_args = [
            "analyze",
            "--repo-path", str(tmp_path),
            "--output", str(output_file),
            "--json-only",
        ]

        with patch("sys.argv", test_args):
            main()

        output_data = json.loads(output_file.read_text())
        assert "data" in output_data
        assert output_data["data"]["tool"] == "devskim"
        assert "summary" in output_data["data"]
        assert "files" in output_data["data"]

    @patch("scripts.analyze.display_dashboard")
    @patch("scripts.analyze.get_devskim_version", return_value="1.0.28")
    @patch("scripts.analyze.analyze_with_devskim")
    @patch("scripts.analyze.validate_common_args")
    def test_main_relative_custom_rules(
        self,
        mock_validate,
        mock_analyze,
        mock_version,
        mock_dashboard,
        mock_analysis_result,
        tmp_path,
    ) -> None:
        """Relative custom rules path should be resolved from tool dir."""
        output_file = tmp_path / "output.json"

        mock_common = MagicMock()
        mock_common.repo_path = tmp_path
        mock_common.repo_name = "test-repo"
        mock_common.repo_id = "repo-123"
        mock_common.run_id = "run-456"
        mock_common.branch = "main"
        mock_common.commit = "abc123"
        mock_common.output_path = output_file
        mock_validate.return_value = mock_common

        mock_analyze.return_value = mock_analysis_result

        # Use relative path - it won't exist, so custom_rules_path will be None
        test_args = [
            "analyze",
            "--repo-path", str(tmp_path),
            "--output", str(output_file),
            "--json-only",
            "--custom-rules", "relative/rules",  # Relative path
        ]

        with patch("sys.argv", test_args):
            main()

        # Verify analyze was called (with None for custom_rules since path doesn't exist)
        mock_analyze.assert_called_once()
        call_args = mock_analyze.call_args
        # custom_rules_path is the 4th positional arg - should be None since relative path doesn't exist
        assert call_args[0][3] is None
