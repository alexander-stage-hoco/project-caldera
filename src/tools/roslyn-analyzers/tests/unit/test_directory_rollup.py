"""
Tests for directory aggregation and rollup statistics.

Tests cover:
- Directory-level aggregation of violations
- Top 5 rules per directory calculation
- Category/severity breakdown by directory
- Handling files in different directory levels
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from roslyn_analyzer import (
    compute_directory_rollup,
    FileResult,
)


class TestDirectoryRollupBasic:
    """Test basic directory rollup functionality."""

    def test_rollup_single_directory(self):
        """Rollup violations in a single directory."""
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
            )
        }

        rollup = compute_directory_rollup(files)

        assert len(rollup) == 1
        src_dir = rollup[0]
        assert src_dir["directory"] == "src"
        assert src_dir["total_violations"] == 3
        assert src_dir["files_analyzed"] == 2

    def test_rollup_multiple_directories(self):
        """Rollup violations across multiple directories."""
        files = {
            "src/security/vuln.cs": FileResult(
                path="src/security/vuln.cs", relative_path="src/security/vuln.cs",
                violations=[
                    {"dd_category": "security", "dd_severity": "high", "rule_id": "CA3001"},
                ]
            ),
            "src/design/empty.cs": FileResult(
                path="src/design/empty.cs", relative_path="src/design/empty.cs",
                violations=[
                    {"dd_category": "design", "dd_severity": "medium", "rule_id": "CA1040"},
                ]
            ),
            "tests/unit/test1.cs": FileResult(
                path="tests/unit/test1.cs", relative_path="tests/unit/test1.cs",
                violations=[]
            )
        }

        rollup = compute_directory_rollup(files)

        assert len(rollup) == 3
        dirs = {r["directory"] for r in rollup}
        assert "src/security" in dirs
        assert "src/design" in dirs
        assert "tests/unit" in dirs

    def test_rollup_root_directory(self):
        """Handle files in root directory (no parent)."""
        files = {
            "Program.cs": FileResult(
                path="Program.cs", relative_path="Program.cs",
                violations=[
                    {"dd_category": "security", "dd_severity": "high", "rule_id": "CA3001"},
                ]
            )
        }

        rollup = compute_directory_rollup(files)

        assert len(rollup) == 1
        assert rollup[0]["directory"] == "root"
        assert rollup[0]["total_violations"] == 1


class TestDirectoryRollupCategories:
    """Test category breakdown in directory rollup."""

    def test_rollup_category_breakdown(self):
        """Verify category counts per directory."""
        files = {
            "src/file.cs": FileResult(
                path="src/file.cs", relative_path="src/file.cs",
                violations=[
                    {"dd_category": "security", "dd_severity": "high", "rule_id": "CA3001"},
                    {"dd_category": "security", "dd_severity": "high", "rule_id": "CA3002"},
                    {"dd_category": "design", "dd_severity": "medium", "rule_id": "CA1040"},
                    {"dd_category": "resource", "dd_severity": "critical", "rule_id": "CA2000"},
                ]
            )
        }

        rollup = compute_directory_rollup(files)

        by_cat = rollup[0]["by_category"]
        assert by_cat["security"] == 2
        assert by_cat["design"] == 1
        assert by_cat["resource"] == 1

    def test_rollup_aggregates_across_files(self):
        """Verify categories are aggregated across files in same directory."""
        files = {
            "src/a.cs": FileResult(
                path="src/a.cs", relative_path="src/a.cs",
                violations=[
                    {"dd_category": "security", "dd_severity": "high", "rule_id": "CA3001"},
                ]
            ),
            "src/b.cs": FileResult(
                path="src/b.cs", relative_path="src/b.cs",
                violations=[
                    {"dd_category": "security", "dd_severity": "critical", "rule_id": "CA3002"},
                    {"dd_category": "design", "dd_severity": "medium", "rule_id": "CA1040"},
                ]
            )
        }

        rollup = compute_directory_rollup(files)

        assert len(rollup) == 1
        by_cat = rollup[0]["by_category"]
        assert by_cat["security"] == 2
        assert by_cat["design"] == 1


class TestDirectoryRollupSeverities:
    """Test severity breakdown in directory rollup."""

    def test_rollup_severity_breakdown(self):
        """Verify severity counts per directory."""
        files = {
            "src/file.cs": FileResult(
                path="src/file.cs", relative_path="src/file.cs",
                violations=[
                    {"dd_category": "security", "dd_severity": "critical", "rule_id": "CA3001"},
                    {"dd_category": "security", "dd_severity": "high", "rule_id": "CA3002"},
                    {"dd_category": "security", "dd_severity": "high", "rule_id": "CA3003"},
                    {"dd_category": "design", "dd_severity": "medium", "rule_id": "CA1040"},
                    {"dd_category": "dead_code", "dd_severity": "low", "rule_id": "IDE0060"},
                ]
            )
        }

        rollup = compute_directory_rollup(files)

        by_sev = rollup[0]["by_severity"]
        assert by_sev["critical"] == 1
        assert by_sev["high"] == 2
        assert by_sev["medium"] == 1
        assert by_sev["low"] == 1

    def test_rollup_missing_severities_handled(self):
        """Handle directories with only certain severity levels."""
        files = {
            "src/file.cs": FileResult(
                path="src/file.cs", relative_path="src/file.cs",
                violations=[
                    {"dd_category": "design", "dd_severity": "medium", "rule_id": "CA1040"},
                ]
            )
        }

        rollup = compute_directory_rollup(files)

        by_sev = rollup[0]["by_severity"]
        assert by_sev.get("medium") == 1
        assert by_sev.get("critical") is None
        assert by_sev.get("high") is None


class TestDirectoryRollupTopRules:
    """Test top rules calculation per directory."""

    def test_rollup_top_5_rules(self):
        """Verify top 5 rules are returned sorted by frequency."""
        files = {
            "src/file.cs": FileResult(
                path="src/file.cs", relative_path="src/file.cs",
                violations=[
                    {"dd_category": "security", "dd_severity": "high", "rule_id": "CA3001"},
                    {"dd_category": "security", "dd_severity": "high", "rule_id": "CA3001"},
                    {"dd_category": "security", "dd_severity": "high", "rule_id": "CA3001"},
                    {"dd_category": "security", "dd_severity": "high", "rule_id": "CA3002"},
                    {"dd_category": "security", "dd_severity": "high", "rule_id": "CA3002"},
                    {"dd_category": "design", "dd_severity": "medium", "rule_id": "CA1040"},
                    {"dd_category": "resource", "dd_severity": "critical", "rule_id": "CA2000"},
                    {"dd_category": "resource", "dd_severity": "critical", "rule_id": "CA1001"},
                    {"dd_category": "dead_code", "dd_severity": "low", "rule_id": "IDE0060"},
                    {"dd_category": "performance", "dd_severity": "low", "rule_id": "CA1822"},
                ]
            )
        }

        rollup = compute_directory_rollup(files)

        top_rules = rollup[0]["top_rules"]
        assert len(top_rules) <= 5
        # CA3001 (3) should be first, CA3002 (2) should be second
        assert top_rules[0] == "CA3001"
        assert top_rules[1] == "CA3002"

    def test_rollup_fewer_than_5_rules(self):
        """Handle directories with fewer than 5 distinct rules."""
        files = {
            "src/file.cs": FileResult(
                path="src/file.cs", relative_path="src/file.cs",
                violations=[
                    {"dd_category": "security", "dd_severity": "high", "rule_id": "CA3001"},
                    {"dd_category": "design", "dd_severity": "medium", "rule_id": "CA1040"},
                ]
            )
        }

        rollup = compute_directory_rollup(files)

        top_rules = rollup[0]["top_rules"]
        assert len(top_rules) == 2
        assert "CA3001" in top_rules
        assert "CA1040" in top_rules

    def test_rollup_no_violations_no_top_rules(self):
        """Handle directories with no violations."""
        files = {
            "src/clean.cs": FileResult(
                path="src/clean.cs", relative_path="src/clean.cs",
                violations=[]
            )
        }

        rollup = compute_directory_rollup(files)

        assert rollup[0]["top_rules"] == []


class TestDirectoryRollupFilesCounting:
    """Test files_analyzed counting in rollup."""

    def test_rollup_counts_files_correctly(self):
        """Verify files are counted per directory."""
        files = {
            "src/a.cs": FileResult(path="src/a.cs", relative_path="src/a.cs", violations=[]),
            "src/b.cs": FileResult(path="src/b.cs", relative_path="src/b.cs", violations=[]),
            "src/c.cs": FileResult(path="src/c.cs", relative_path="src/c.cs", violations=[]),
            "tests/test.cs": FileResult(path="tests/test.cs", relative_path="tests/test.cs", violations=[]),
        }

        rollup = compute_directory_rollup(files)

        rollup_by_dir = {r["directory"]: r for r in rollup}
        assert rollup_by_dir["src"]["files_analyzed"] == 3
        assert rollup_by_dir["tests"]["files_analyzed"] == 1

    def test_rollup_includes_files_without_violations(self):
        """Verify clean files are still counted."""
        files = {
            "src/vuln.cs": FileResult(
                path="src/vuln.cs", relative_path="src/vuln.cs",
                violations=[{"dd_category": "security", "dd_severity": "high", "rule_id": "CA3001"}]
            ),
            "src/clean1.cs": FileResult(path="src/clean1.cs", relative_path="src/clean1.cs", violations=[]),
            "src/clean2.cs": FileResult(path="src/clean2.cs", relative_path="src/clean2.cs", violations=[]),
        }

        rollup = compute_directory_rollup(files)

        assert rollup[0]["files_analyzed"] == 3
        assert rollup[0]["total_violations"] == 1


class TestDirectoryRollupEdgeCases:
    """Test edge cases in directory rollup."""

    def test_rollup_empty_files(self):
        """Handle empty file dictionary."""
        rollup = compute_directory_rollup({})

        assert rollup == []

    def test_rollup_deeply_nested_directories(self):
        """Handle deeply nested directory structures."""
        files = {
            "a/b/c/d/e/file.cs": FileResult(
                path="a/b/c/d/e/file.cs", relative_path="a/b/c/d/e/file.cs",
                violations=[{"dd_category": "security", "dd_severity": "high", "rule_id": "CA3001"}]
            )
        }

        rollup = compute_directory_rollup(files)

        assert len(rollup) == 1
        assert rollup[0]["directory"] == "a/b/c/d/e"
        assert rollup[0]["total_violations"] == 1

    def test_rollup_windows_style_paths(self):
        """Handle Windows-style path separators (converted to forward slashes)."""
        # Note: In practice, paths should be normalized before reaching this function
        files = {
            "src\\subdir\\file.cs": FileResult(
                path="src\\subdir\\file.cs", relative_path="src\\subdir\\file.cs",
                violations=[{"dd_category": "security", "dd_severity": "high", "rule_id": "CA3001"}]
            )
        }

        rollup = compute_directory_rollup(files)

        # Path is used as-is, parent is computed
        assert len(rollup) == 1
        # The actual directory depends on Path behavior on the current OS

    def test_rollup_special_characters_in_paths(self):
        """Handle paths with spaces and special characters."""
        files = {
            "My Project/Source Files/main.cs": FileResult(
                path="My Project/Source Files/main.cs",
                relative_path="My Project/Source Files/main.cs",
                violations=[{"dd_category": "design", "dd_severity": "medium", "rule_id": "CA1040"}]
            )
        }

        rollup = compute_directory_rollup(files)

        assert len(rollup) == 1
        assert "Source Files" in rollup[0]["directory"]


class TestDirectoryRollupDataStructure:
    """Test the structure of rollup output."""

    def test_rollup_contains_required_fields(self):
        """Verify all required fields are present in rollup entries."""
        files = {
            "src/file.cs": FileResult(
                path="src/file.cs", relative_path="src/file.cs",
                violations=[{"dd_category": "security", "dd_severity": "high", "rule_id": "CA3001"}]
            )
        }

        rollup = compute_directory_rollup(files)

        entry = rollup[0]
        assert "directory" in entry
        assert "total_violations" in entry
        assert "files_analyzed" in entry
        assert "by_category" in entry
        assert "by_severity" in entry
        assert "top_rules" in entry

    def test_rollup_returns_list(self):
        """Verify rollup returns a list."""
        files = {
            "src/file.cs": FileResult(path="src/file.cs", relative_path="src/file.cs", violations=[])
        }

        rollup = compute_directory_rollup(files)

        assert isinstance(rollup, list)

    def test_rollup_category_and_severity_are_dicts(self):
        """Verify category and severity breakdowns are dictionaries."""
        files = {
            "src/file.cs": FileResult(
                path="src/file.cs", relative_path="src/file.cs",
                violations=[{"dd_category": "security", "dd_severity": "high", "rule_id": "CA3001"}]
            )
        }

        rollup = compute_directory_rollup(files)

        assert isinstance(rollup[0]["by_category"], dict)
        assert isinstance(rollup[0]["by_severity"], dict)
        assert isinstance(rollup[0]["top_rules"], list)
