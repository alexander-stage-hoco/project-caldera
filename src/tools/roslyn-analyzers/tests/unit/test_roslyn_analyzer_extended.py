"""
Extended tests for roslyn_analyzer.py - covering uncovered functions.

Tests cover:
- get_documentation_url: URL generation for each rule prefix
- find_csproj_files: .csproj file discovery
- run_dotnet_build: subprocess invocation and timeout handling
- compute_directory_rollup: directory-level aggregation
- print_simple_summary: text output rendering
- group_violations_by_file: documentation URL fallback
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from roslyn_analyzer import (
    get_documentation_url,
    find_csproj_files,
    run_dotnet_build,
    compute_directory_rollup,
    print_simple_summary,
    group_violations_by_file,
    count_lines,
    AnalysisResult,
    FileResult,
    Violation,
)


class TestGetDocumentationUrl:
    """Test documentation URL generation for different rule prefixes."""

    def test_ca_rule(self):
        url = get_documentation_url("CA3001")
        assert "learn.microsoft.com" in url
        assert "ca3001" in url

    def test_cs_rule(self):
        url = get_documentation_url("CS0618")
        assert "learn.microsoft.com" in url
        assert "cs0618" in url

    def test_ide_rule(self):
        url = get_documentation_url("IDE0005")
        assert "learn.microsoft.com" in url
        assert "ide0005" in url

    def test_scs_rule(self):
        url = get_documentation_url("SCS0001")
        assert "security-code-scan.github.io" in url
        assert "SCS0001" in url

    def test_idisp_rule(self):
        url = get_documentation_url("IDISP001")
        assert "IDisposableAnalyzers" in url
        assert "IDISP001" in url

    def test_sa_rule(self):
        url = get_documentation_url("SA1001")
        assert "StyleCopAnalyzers" in url
        assert "SA1001" in url

    def test_sx_rule(self):
        url = get_documentation_url("SX0001")
        assert "StyleCopAnalyzers" in url

    def test_rcs_rule(self):
        url = get_documentation_url("RCS1001")
        assert "roslynator" in url.lower()
        assert "RCS1001" in url

    def test_vsthrd_rule(self):
        url = get_documentation_url("VSTHRD001")
        assert "vs-threading" in url
        assert "VSTHRD001" in url

    def test_ma_rule(self):
        url = get_documentation_url("MA0001")
        assert "Meziantou" in url
        assert "MA0001" in url

    def test_async_rule(self):
        url = get_documentation_url("ASYNC001")
        assert "AsyncFixer" in url

    def test_unknown_prefix_returns_empty(self):
        url = get_documentation_url("UNKNOWN001")
        assert url == ""


class TestFindCsprojFiles:
    """Test .csproj file discovery."""

    def test_finds_csproj_files(self, tmp_path):
        (tmp_path / "proj1.csproj").write_text("<Project />")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "proj2.csproj").write_text("<Project />")
        (tmp_path / "other.txt").write_text("not a csproj")

        files = find_csproj_files(tmp_path)
        assert len(files) == 2
        names = {f.name for f in files}
        assert "proj1.csproj" in names
        assert "proj2.csproj" in names

    def test_no_csproj_files(self, tmp_path):
        (tmp_path / "readme.md").write_text("# Readme")
        files = find_csproj_files(tmp_path)
        assert files == []


class TestRunDotnetBuild:
    """Test dotnet build invocation with mocked subprocess."""

    @patch("roslyn_analyzer.subprocess.run")
    def test_successful_build(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(
            returncode=0,
            stderr="Build succeeded.",
            stdout="",
        )
        sarif_path = tmp_path / "test.sarif"

        success, output = run_dotnet_build(tmp_path / "proj.csproj", sarif_path)

        assert success is True
        assert "Build succeeded" in output
        mock_run.assert_called_once()

    @patch("roslyn_analyzer.subprocess.run")
    def test_build_timeout(self, mock_run, tmp_path):
        mock_run.side_effect = subprocess.TimeoutExpired("dotnet", 30)
        sarif_path = tmp_path / "test.sarif"

        success, output = run_dotnet_build(tmp_path / "proj.csproj", sarif_path, timeout=30)

        assert success is False
        assert "timed out" in output.lower()

    @patch("roslyn_analyzer.subprocess.run")
    def test_build_exception(self, mock_run, tmp_path):
        mock_run.side_effect = OSError("dotnet not found")
        sarif_path = tmp_path / "test.sarif"

        success, output = run_dotnet_build(tmp_path / "proj.csproj", sarif_path)

        assert success is False
        assert "not found" in output

    @patch("roslyn_analyzer.subprocess.run")
    def test_sarif_cleanup_trailing_content(self, mock_run, tmp_path):
        """SARIF file with trailing non-JSON content is cleaned up."""
        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")
        sarif_path = tmp_path / "test.sarif"
        # Write SARIF with trailing garbage
        sarif_path.write_text('{"version": "2.1.0"}\n\ngarbage')

        success, _ = run_dotnet_build(tmp_path / "proj.csproj", sarif_path)

        assert success is True
        content = sarif_path.read_text()
        assert content == '{"version": "2.1.0"}'


class TestComputeDirectoryRollup:
    """Test directory-level aggregation."""

    def test_single_directory(self):
        files = {
            "src/file1.cs": FileResult(
                path="src/file1.cs", relative_path="src/file1.cs",
                violations=[
                    {"dd_category": "security", "dd_severity": "high", "rule_id": "CA3001"},
                    {"dd_category": "security", "dd_severity": "critical", "rule_id": "CA3001"},
                ]
            ),
            "src/file2.cs": FileResult(
                path="src/file2.cs", relative_path="src/file2.cs",
                violations=[
                    {"dd_category": "design", "dd_severity": "medium", "rule_id": "CA1040"},
                ]
            ),
        }

        rollup = compute_directory_rollup(files)

        assert len(rollup) == 1
        src_dir = rollup[0]
        assert src_dir["directory"] == "src"
        assert src_dir["files_analyzed"] == 2
        assert src_dir["total_violations"] == 3
        assert src_dir["by_category"]["security"] == 2
        assert src_dir["by_category"]["design"] == 1
        assert src_dir["by_severity"]["high"] == 1
        assert src_dir["by_severity"]["critical"] == 1

    def test_multiple_directories(self):
        files = {
            "src/file1.cs": FileResult(
                path="src/file1.cs", relative_path="src/file1.cs",
                violations=[
                    {"dd_category": "security", "dd_severity": "high", "rule_id": "CA3001"},
                ]
            ),
            "tests/test1.cs": FileResult(
                path="tests/test1.cs", relative_path="tests/test1.cs",
                violations=[
                    {"dd_category": "design", "dd_severity": "medium", "rule_id": "CA1040"},
                ]
            ),
        }

        rollup = compute_directory_rollup(files)

        assert len(rollup) == 2
        dirs = {r["directory"] for r in rollup}
        assert "src" in dirs
        assert "tests" in dirs

    def test_root_directory_files(self):
        """Files in root directory get directory='root'."""
        files = {
            "file.cs": FileResult(
                path="file.cs", relative_path="file.cs",
                violations=[
                    {"dd_category": "design", "dd_severity": "low", "rule_id": "CA1040"},
                ]
            ),
        }

        rollup = compute_directory_rollup(files)

        assert len(rollup) == 1
        assert rollup[0]["directory"] == "root"

    def test_top_rules_sorted_and_limited(self):
        """top_rules should be sorted by count and limited to 5."""
        violations = []
        for i in range(10):
            violations.append({
                "dd_category": "design",
                "dd_severity": "medium",
                "rule_id": f"CA{1000 + i}",
            })
        # Add extra violations for certain rules to ensure sorting
        for _ in range(5):
            violations.append({
                "dd_category": "design",
                "dd_severity": "medium",
                "rule_id": "CA1000",
            })
        files = {
            "src/file.cs": FileResult(
                path="src/file.cs", relative_path="src/file.cs",
                violations=violations,
            ),
        }

        rollup = compute_directory_rollup(files)

        top_rules = rollup[0]["top_rules"]
        assert len(top_rules) <= 5
        # Most common rule should be first
        assert top_rules[0] == "CA1000"

    def test_empty_files(self):
        rollup = compute_directory_rollup({})
        assert rollup == []


class TestPrintSimpleSummary:
    """Test text-only summary rendering."""

    def test_prints_summary(self, capsys):
        result = AnalysisResult(
            metadata={
                "version": "1.0.0",
                "tool": "roslyn-analyzers",
                "timestamp": "2026-01-01T00:00:00Z",
                "target_path": "/tmp/test",
                "analysis_duration_ms": 1234,
            },
            files=[],
            summary={
                "total_files_analyzed": 5,
                "total_violations": 10,
                "files_with_violations": 3,
                "violations_by_category": {"security": 4, "design": 6},
                "violations_by_severity": {"high": 7, "medium": 3},
                "violations_by_rule": {},
                "top_violated_rules": [],
            },
            statistics={},
            directory_rollup=[],
        )

        print_simple_summary(result)

        captured = capsys.readouterr()
        assert "ROSLYN ANALYZERS" in captured.out
        assert "Files Analyzed: 5" in captured.out
        assert "Total Violations: 10" in captured.out
        assert "security: 4" in captured.out
        assert "design: 6" in captured.out
        assert "high: 7" in captured.out


class TestDocumentationUrlFallback:
    """Test that group_violations_by_file uses documentation URL fallback."""

    def test_empty_doc_url_gets_fallback(self, tmp_path):
        test_file = tmp_path / "test.cs"
        test_file.write_text("content\n")

        violation = Violation(
            rule_id="CA3001",
            dd_category="security",
            dd_severity="high",
            roslyn_level="warning",
            file_path=str(test_file),
            line_start=1, line_end=1, column_start=1, column_end=10,
            message="test",
            documentation_url="",  # Empty URL should trigger fallback
        )

        files = group_violations_by_file([violation], tmp_path)
        v = list(files.values())[0].violations[0]
        # Should have the generated CA docs URL
        assert "learn.microsoft.com" in v["documentation_url"]
        assert "ca3001" in v["documentation_url"]

    def test_existing_doc_url_preserved(self, tmp_path):
        test_file = tmp_path / "test.cs"
        test_file.write_text("content\n")

        violation = Violation(
            rule_id="CA3001",
            dd_category="security",
            dd_severity="high",
            roslyn_level="warning",
            file_path=str(test_file),
            line_start=1, line_end=1, column_start=1, column_end=10,
            message="test",
            documentation_url="https://example.com/custom",
        )

        files = group_violations_by_file([violation], tmp_path)
        v = list(files.values())[0].violations[0]
        assert v["documentation_url"] == "https://example.com/custom"

    def test_empty_severity_gets_default(self, tmp_path):
        """Violations with empty severity get 'medium' default."""
        test_file = tmp_path / "test.cs"
        test_file.write_text("content\n")

        violation = Violation(
            rule_id="TEST001",
            dd_category="other",
            dd_severity="",
            roslyn_level="warning",
            file_path=str(test_file),
            line_start=1, line_end=1, column_start=1, column_end=10,
            message="test",
        )

        files = group_violations_by_file([violation], tmp_path)
        v = list(files.values())[0].violations[0]
        assert v["dd_severity"] == "medium"
        assert v["severity"] == "medium"
