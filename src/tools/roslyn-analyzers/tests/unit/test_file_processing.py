"""
Tests for file processing and statistics computation.

Tests cover:
- Path normalization (file:// URIs to relative paths)
- Line counting accuracy for .cs files
- Violations grouped correctly by file
- Statistics computation (mean, median, min, max violations)
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from roslyn_analyzer import (
    count_lines,
    group_violations_by_file,
    compute_statistics,
    Violation,
    FileResult,
)


class TestLineCountingAccuracy:
    """Test line counting for .cs files."""

    def test_count_lines_simple_file(self, tmp_path):
        """Count lines in a simple file."""
        cs_file = tmp_path / "test.cs"
        cs_file.write_text("line1\nline2\nline3\n")

        count = count_lines(cs_file)

        assert count == 3

    def test_count_lines_empty_file(self, tmp_path):
        """Count lines in an empty file."""
        cs_file = tmp_path / "empty.cs"
        cs_file.write_text("")

        count = count_lines(cs_file)

        assert count == 0

    def test_count_lines_single_line_no_newline(self, tmp_path):
        """Count lines when file has no trailing newline."""
        cs_file = tmp_path / "single.cs"
        cs_file.write_text("single line without newline")

        count = count_lines(cs_file)

        assert count == 1

    def test_count_lines_multiline_realistic(self, tmp_path):
        """Count lines in a realistic C# file."""
        cs_content = """using System;
using System.Collections.Generic;

namespace TestNamespace
{
    public class TestClass
    {
        private readonly string _name;

        public TestClass(string name)
        {
            _name = name;
        }

        public void DoSomething()
        {
            Console.WriteLine(_name);
        }
    }
}
"""
        cs_file = tmp_path / "realistic.cs"
        cs_file.write_text(cs_content)

        count = count_lines(cs_file)

        # 20 lines (the trailing newline doesn't add an extra line)
        assert count == 20

    def test_count_lines_nonexistent_file(self, tmp_path):
        """Return 0 for nonexistent file."""
        count = count_lines(tmp_path / "nonexistent.cs")

        assert count == 0

    def test_count_lines_with_unicode(self, tmp_path):
        """Handle files with unicode characters."""
        cs_content = "// Comment with emoji 🎉\nstring s = \"Unicode: é à ü\";\n"
        cs_file = tmp_path / "unicode.cs"
        cs_file.write_text(cs_content, encoding="utf-8")

        count = count_lines(cs_file)

        assert count == 2


class TestPathNormalization:
    """Test file:// URI to path normalization in group_violations_by_file."""

    def test_normalize_file_uri_unix(self, tmp_path):
        """Normalize Unix file:// URI to path."""
        # Create a test file
        test_file = tmp_path / "src" / "test.cs"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("// test")

        violation = Violation(
            rule_id="CA0001",
            dd_category="test",
            dd_severity="medium",
            roslyn_level="warning",
            file_path=f"file://{test_file}",  # Unix-style file URI
            line_start=1,
            line_end=1,
            column_start=1,
            column_end=10,
            message="Test violation"
        )

        files = group_violations_by_file([violation], tmp_path)

        # Should normalize to relative path
        assert len(files) == 1
        key = list(files.keys())[0]
        assert "file://" not in key

    def test_normalize_already_relative_path(self, tmp_path):
        """Handle already relative paths."""
        test_file = tmp_path / "src" / "test.cs"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("// test")

        violation = Violation(
            rule_id="CA0001",
            dd_category="test",
            dd_severity="medium",
            roslyn_level="warning",
            file_path=str(test_file),
            line_start=1,
            line_end=1,
            column_start=1,
            column_end=10,
            message="Test violation"
        )

        files = group_violations_by_file([violation], tmp_path)

        assert len(files) == 1
        key = list(files.keys())[0]
        assert key == "src/test.cs"


class TestViolationGrouping:
    """Test violations are grouped correctly by file."""

    def test_group_single_file_multiple_violations(self, tmp_path):
        """Group multiple violations for the same file."""
        test_file = tmp_path / "test.cs"
        test_file.write_text("line1\nline2\nline3\n")

        violations = [
            Violation(
                rule_id="CA0001",
                dd_category="test",
                dd_severity="medium",
                roslyn_level="warning",
                file_path=str(test_file),
                line_start=1, line_end=1, column_start=1, column_end=10,
                message="First"
            ),
            Violation(
                rule_id="CA0002",
                dd_category="test",
                dd_severity="high",
                roslyn_level="warning",
                file_path=str(test_file),
                line_start=2, line_end=2, column_start=1, column_end=10,
                message="Second"
            )
        ]

        files = group_violations_by_file(violations, tmp_path)

        assert len(files) == 1
        file_result = list(files.values())[0]
        assert file_result.violation_count == 2
        assert len(file_result.violations) == 2

    def test_group_multiple_files(self, tmp_path):
        """Group violations across multiple files."""
        file1 = tmp_path / "file1.cs"
        file2 = tmp_path / "subdir" / "file2.cs"
        file1.write_text("content1\n")
        file2.parent.mkdir()
        file2.write_text("content2\n")

        violations = [
            Violation(
                rule_id="CA0001", dd_category="test", dd_severity="medium",
                roslyn_level="warning", file_path=str(file1),
                line_start=1, line_end=1, column_start=1, column_end=10,
                message="In file1"
            ),
            Violation(
                rule_id="CA0002", dd_category="test", dd_severity="high",
                roslyn_level="warning", file_path=str(file2),
                line_start=1, line_end=1, column_start=1, column_end=10,
                message="In file2"
            )
        ]

        files = group_violations_by_file(violations, tmp_path)

        assert len(files) == 2
        assert any("file1.cs" in k for k in files.keys())
        assert any("file2.cs" in k for k in files.keys())

    def test_group_preserves_violation_details(self, tmp_path):
        """Verify violation details are preserved after grouping."""
        test_file = tmp_path / "test.cs"
        test_file.write_text("content\n")

        violation = Violation(
            rule_id="CA3001",
            dd_category="security",
            dd_severity="critical",
            roslyn_level="error",
            file_path=str(test_file),
            line_start=10,
            line_end=12,
            column_start=5,
            column_end=25,
            message="SQL injection vulnerability",
            documentation_url="https://example.com/ca3001"
        )

        files = group_violations_by_file([violation], tmp_path)

        file_result = list(files.values())[0]
        v = file_result.violations[0]

        assert v["rule_id"] == "CA3001"
        assert v["dd_category"] == "security"
        assert v["dd_severity"] == "critical"
        assert v["line_start"] == 10
        assert v["line_end"] == 12
        assert v["column_start"] == 5
        assert v["column_end"] == 25
        assert v["message"] == "SQL injection vulnerability"
        assert v["documentation_url"] == "https://example.com/ca3001"


class TestStatisticsComputation:
    """Test aggregate statistics computation."""

    def test_compute_statistics_basic(self, tmp_path):
        """Compute basic statistics from file results."""
        files = {
            "file1.cs": FileResult(
                path="file1.cs", relative_path="file1.cs",
                lines_of_code=100, violations=[{"dd_category": "security", "dd_severity": "high", "rule_id": "CA3001"}] * 3
            ),
            "file2.cs": FileResult(
                path="file2.cs", relative_path="file2.cs",
                lines_of_code=50, violations=[{"dd_category": "design", "dd_severity": "medium", "rule_id": "CA1040"}]
            ),
            "file3.cs": FileResult(
                path="file3.cs", relative_path="file3.cs",
                lines_of_code=200, violations=[]
            )
        }
        violations = [
            Violation("CA3001", "security", "high", "warning", "f", 1, 1, 1, 1, "m"),
            Violation("CA3001", "security", "high", "warning", "f", 2, 2, 1, 1, "m"),
            Violation("CA3001", "security", "high", "warning", "f", 3, 3, 1, 1, "m"),
            Violation("CA1040", "design", "medium", "warning", "f", 1, 1, 1, 1, "m"),
        ]

        stats = compute_statistics(files, violations)

        # Check violations per file stats
        vpf = stats["violations_per_file"]
        assert vpf["min"] == 0
        assert vpf["max"] == 3
        assert vpf["mean"] == pytest.approx(4 / 3)  # (3 + 1 + 0) / 3

    def test_compute_statistics_category_distribution(self, tmp_path):
        """Verify category distribution computation."""
        files = {
            "test.cs": FileResult(
                path="test.cs", relative_path="test.cs",
                lines_of_code=100, violations=[]
            )
        }
        violations = [
            Violation("CA3001", "security", "high", "warning", "f", 1, 1, 1, 1, "m"),
            Violation("CA3001", "security", "critical", "error", "f", 2, 2, 1, 1, "m"),
            Violation("CA1040", "design", "medium", "info", "f", 3, 3, 1, 1, "m"),
        ]

        stats = compute_statistics(files, violations)

        cat_dist = stats["category_distribution"]
        assert cat_dist["security"]["count"] == 2
        assert cat_dist["design"]["count"] == 1
        assert "critical" in cat_dist["security"]["severity_breakdown"]
        assert "high" in cat_dist["security"]["severity_breakdown"]

    def test_compute_statistics_violations_per_1000_loc(self, tmp_path):
        """Verify violations per 1000 LOC calculation."""
        files = {
            "test.cs": FileResult(
                path="test.cs", relative_path="test.cs",
                lines_of_code=500, violations=[]
            )
        }
        violations = [
            Violation("CA0001", "test", "high", "warning", "f", i, i, 1, 1, "m")
            for i in range(10)
        ]

        stats = compute_statistics(files, violations)

        # 10 violations / 500 lines * 1000 = 20
        assert stats["violations_per_1000_loc"] == pytest.approx(20.0)

    def test_compute_statistics_empty_files(self):
        """Handle case with no files."""
        stats = compute_statistics({}, [])

        assert stats["violations_per_file"]["mean"] == 0
        assert stats["violations_per_file"]["min"] == 0
        assert stats["violations_per_file"]["max"] == 0
        assert stats["violations_per_1000_loc"] == 0

    def test_compute_statistics_rule_coverage(self, tmp_path):
        """Verify rule coverage statistics."""
        files = {
            "test.cs": FileResult(
                path="test.cs", relative_path="test.cs",
                lines_of_code=100, violations=[]
            )
        }
        violations = [
            Violation("CA3001", "security", "high", "warning", "f", 1, 1, 1, 1, "m"),
            Violation("CA3001", "security", "high", "warning", "f", 2, 2, 1, 1, "m"),
            Violation("CA1040", "design", "medium", "info", "f", 3, 3, 1, 1, "m"),
            Violation("CA2000", "resource", "high", "warning", "f", 4, 4, 1, 1, "m"),
        ]

        stats = compute_statistics(files, violations)

        rc = stats["rule_coverage"]
        assert rc["rules_triggered"] == 3  # CA3001, CA1040, CA2000
        assert rc["rules_available"] > 0

    def test_compute_statistics_file_coverage(self, tmp_path):
        """Verify file coverage statistics."""
        files = {
            "with_violations.cs": FileResult(
                path="with_violations.cs", relative_path="with_violations.cs",
                lines_of_code=100
            ),
            "clean.cs": FileResult(
                path="clean.cs", relative_path="clean.cs",
                lines_of_code=50
            )
        }
        files["with_violations.cs"].violations = [{"rule_id": "CA0001"}]

        stats = compute_statistics(files, [])

        fc = stats["file_coverage"]
        assert fc["files_with_violations"] == 1
        assert fc["files_clean"] == 1
        assert fc["violation_rate"] == pytest.approx(50.0)


class TestFileResultProperties:
    """Test FileResult dataclass properties."""

    def test_violation_count_property(self):
        """Test violation_count property returns correct count."""
        fr = FileResult(path="test.cs", relative_path="test.cs")
        fr.violations = [{"rule_id": f"CA{i}"} for i in range(5)]

        assert fr.violation_count == 5

    def test_violation_count_empty(self):
        """Test violation_count for empty violations list."""
        fr = FileResult(path="test.cs", relative_path="test.cs")

        assert fr.violation_count == 0

    def test_file_result_default_values(self):
        """Test FileResult default values."""
        fr = FileResult(path="test.cs", relative_path="test.cs")

        assert fr.language == "csharp"
        assert fr.lines_of_code == 0
        assert fr.violations == []
