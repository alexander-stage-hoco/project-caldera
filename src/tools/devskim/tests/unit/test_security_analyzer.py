"""Unit tests for security_analyzer module."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import tempfile
import os

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from security_analyzer import (
    SecurityFinding,
    FileStats,
    DirectoryStats,
    DirectoryEntry,
    Distribution,
    AnalysisResult,
    map_rule_to_category,
    detect_language,
    count_lines,
    compute_distribution,
    parse_sarif_results,
    build_directory_entries,
    result_to_dict,
    distribution_to_dict,
    directory_stats_to_dict,
    get_devskim_version,
    compute_skewness,
    compute_kurtosis,
    compute_gini,
    compute_theil,
    compute_hoover,
    compute_palma,
    compute_top_share,
    compute_bottom_share,
    RULE_TO_CATEGORY_MAP,
    SEVERITY_MAP,
    SECURITY_CATEGORIES,
)


class TestTerminalHelpers:
    """Tests for terminal and formatting helper functions."""

    def test_get_terminal_width_returns_minimum(self) -> None:
        """get_terminal_width should return at least minimum."""
        from security_analyzer import get_terminal_width
        width = get_terminal_width(default=120, minimum=80)
        assert width >= 80

    def test_get_terminal_width_exception_returns_default(self) -> None:
        """get_terminal_width should return default on exception."""
        from security_analyzer import get_terminal_width
        from unittest.mock import patch

        with patch("shutil.get_terminal_size", side_effect=Exception("no terminal")):
            width = get_terminal_width(default=120, minimum=80)
            assert width == 120

    def test_c_with_color_enabled(self) -> None:
        """c() should apply color codes when enabled."""
        from security_analyzer import c, set_color_enabled, Colors
        set_color_enabled(True)
        result = c("test", Colors.RED)
        assert Colors.RED in result
        assert "test" in result
        set_color_enabled(True)  # Reset

    def test_c_without_color(self) -> None:
        """c() should return plain text when disabled."""
        from security_analyzer import c, set_color_enabled, Colors
        set_color_enabled(False)
        result = c("test", Colors.RED)
        assert result == "test"
        set_color_enabled(True)  # Reset

    def test_strip_ansi_removes_codes(self) -> None:
        """strip_ansi should remove ANSI escape codes."""
        from security_analyzer import strip_ansi
        text_with_ansi = "\033[31mred text\033[0m"
        result = strip_ansi(text_with_ansi)
        assert result == "red text"
        assert "\033" not in result

    def test_strip_ansi_preserves_plain_text(self) -> None:
        """strip_ansi should preserve plain text."""
        from security_analyzer import strip_ansi
        plain = "plain text"
        assert strip_ansi(plain) == plain

    def test_truncate_path_middle_short_path(self) -> None:
        """Short paths should not be truncated."""
        from security_analyzer import truncate_path_middle
        path = "short/path"
        result = truncate_path_middle(path, 20)
        assert result == path

    def test_truncate_path_middle_long_path(self) -> None:
        """Long paths should be truncated with ellipsis."""
        from security_analyzer import truncate_path_middle
        path = "very/long/path/to/some/file/in/deep/directory"
        result = truncate_path_middle(path, 20)
        assert len(result) == 20
        assert "..." in result

    def test_format_number_no_decimals(self) -> None:
        """format_number without decimals should return integer."""
        from security_analyzer import format_number
        assert format_number(1234567) == "1,234,567"
        assert format_number(0) == "0"

    def test_format_number_with_decimals(self) -> None:
        """format_number with decimals should format correctly."""
        from security_analyzer import format_number
        assert format_number(1234.5678, 2) == "1,234.57"

    def test_format_percent(self) -> None:
        """format_percent should format percentage."""
        from security_analyzer import format_percent
        assert format_percent(75.5) == "75.5%"
        assert format_percent(100.0) == "100.0%"


class TestPrintHelpers:
    """Tests for print helper functions."""

    def test_print_header(self, capsys) -> None:
        """print_header should output header box."""
        from security_analyzer import print_header, set_color_enabled
        set_color_enabled(False)
        print_header("Test Header", width=40)
        captured = capsys.readouterr()
        assert "Test Header" in captured.out
        assert "─" in captured.out or "-" in captured.out

    def test_print_section(self, capsys) -> None:
        """print_section should output section header."""
        from security_analyzer import print_section, set_color_enabled
        set_color_enabled(False)
        print_section("Test Section", width=40)
        captured = capsys.readouterr()
        assert "Test Section" in captured.out

    def test_print_section_end(self, capsys) -> None:
        """print_section_end should output border."""
        from security_analyzer import print_section_end, set_color_enabled
        set_color_enabled(False)
        print_section_end(width=40)
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_print_row_single_column(self, capsys) -> None:
        """print_row with single column should output correctly."""
        from security_analyzer import print_row, set_color_enabled
        set_color_enabled(False)
        print_row("Label:", "Value", width=40)
        captured = capsys.readouterr()
        assert "Label:" in captured.out
        assert "Value" in captured.out

    def test_print_row_two_columns(self, capsys) -> None:
        """print_row with two columns should output both."""
        from security_analyzer import print_row, set_color_enabled
        set_color_enabled(False)
        print_row("Left:", "Val1", "Right:", "Val2", width=60)
        captured = capsys.readouterr()
        assert "Left:" in captured.out
        assert "Right:" in captured.out

    def test_print_empty_row(self, capsys) -> None:
        """print_empty_row should output empty line."""
        from security_analyzer import print_empty_row, set_color_enabled
        set_color_enabled(False)
        print_empty_row(width=40)
        captured = capsys.readouterr()
        assert len(captured.out) > 0


class TestMapRuleToCategory:
    """Tests for map_rule_to_category function."""

    def test_direct_rule_mapping_sql_injection(self) -> None:
        """SQL injection rules should map correctly."""
        assert map_rule_to_category("DS104456") == "sql_injection"
        assert map_rule_to_category("DS127888") == "sql_injection"

    def test_direct_rule_mapping_hardcoded_secret(self) -> None:
        """Hardcoded secret rules should map correctly."""
        assert map_rule_to_category("DS134411") == "hardcoded_secret"
        assert map_rule_to_category("DS114352") == "hardcoded_secret"
        assert map_rule_to_category("DS173237") == "hardcoded_secret"

    def test_direct_rule_mapping_insecure_crypto(self) -> None:
        """Insecure crypto rules should map correctly."""
        assert map_rule_to_category("DS161085") == "insecure_crypto"
        assert map_rule_to_category("DS126858") == "insecure_crypto"
        assert map_rule_to_category("DS106863") == "insecure_crypto"

    def test_direct_rule_mapping_deserialization(self) -> None:
        """Deserialization rules should map correctly."""
        assert map_rule_to_category("DS181731") == "deserialization"
        assert map_rule_to_category("DS113853") == "deserialization"
        assert map_rule_to_category("DS425040") == "deserialization"

    def test_message_based_mapping_crypto(self) -> None:
        """Message-based mapping for crypto keywords."""
        assert map_rule_to_category("DS999999", "Use of MD5 hash algorithm") == "insecure_crypto"
        assert map_rule_to_category("DS999999", "SHA1 is weak") == "insecure_crypto"
        assert map_rule_to_category("DS999999", "DES cipher detected") == "insecure_crypto"

    def test_message_based_mapping_sql(self) -> None:
        """Message-based mapping for SQL keywords."""
        assert map_rule_to_category("DS999999", "SQL query construction") == "sql_injection"

    def test_message_based_mapping_secrets(self) -> None:
        """Message-based mapping for secret keywords."""
        assert map_rule_to_category("DS999999", "Hardcoded password detected") == "hardcoded_secret"
        assert map_rule_to_category("DS999999", "API key found") == "hardcoded_secret"

    def test_message_based_mapping_path(self) -> None:
        """Message-based mapping for path traversal."""
        assert map_rule_to_category("DS999999", "Path traversal vulnerability") == "path_traversal"

    def test_message_based_mapping_xss(self) -> None:
        """Message-based mapping for XSS."""
        assert map_rule_to_category("DS999999", "Cross-site scripting vulnerability") == "xss"

    def test_message_based_mapping_deserialization(self) -> None:
        """Message-based mapping for deserialization."""
        assert map_rule_to_category("DS999999", "BinaryFormatter usage detected") == "deserialization"
        assert map_rule_to_category("DS999999", "Deserialization of untrusted data") == "deserialization"

    def test_unknown_rule_returns_unknown(self) -> None:
        """Unknown rules should return 'unknown'."""
        assert map_rule_to_category("UNKNOWN_RULE") == "unknown"
        assert map_rule_to_category("CUSTOM123") == "unknown"

    def test_empty_rule_id(self) -> None:
        """Empty rule ID should return unknown."""
        assert map_rule_to_category("") == "unknown"


class TestDetectLanguage:
    """Tests for detect_language function."""

    def test_python_detection(self) -> None:
        """Python files should be detected."""
        assert detect_language("main.py") == "python"
        assert detect_language("src/utils/helper.py") == "python"

    def test_csharp_detection(self) -> None:
        """C# files should be detected."""
        assert detect_language("Program.cs") == "csharp"
        assert detect_language("src/Models/User.cs") == "csharp"

    def test_javascript_detection(self) -> None:
        """JavaScript files should be detected."""
        assert detect_language("app.js") == "javascript"
        assert detect_language("src/index.js") == "javascript"

    def test_typescript_detection(self) -> None:
        """TypeScript files should be detected."""
        assert detect_language("app.ts") == "typescript"
        assert detect_language("components/Button.tsx") == "typescript"

    def test_java_detection(self) -> None:
        """Java files should be detected."""
        assert detect_language("Main.java") == "java"

    def test_go_detection(self) -> None:
        """Go files should be detected."""
        assert detect_language("main.go") == "go"

    def test_rust_detection(self) -> None:
        """Rust files should be detected."""
        assert detect_language("main.rs") == "rust"

    def test_c_cpp_detection(self) -> None:
        """C/C++ files should be detected."""
        assert detect_language("main.c") == "c"
        assert detect_language("app.cpp") == "cpp"
        assert detect_language("header.h") == "c"
        assert detect_language("header.hpp") == "cpp"

    def test_unknown_extension(self) -> None:
        """Unknown extensions should return 'unknown'."""
        assert detect_language("file.xyz") == "unknown"
        assert detect_language("README.md") == "unknown"

    def test_case_insensitive(self) -> None:
        """Extension detection should be case insensitive."""
        assert detect_language("Main.PY") == "python"
        assert detect_language("App.CS") == "csharp"


class TestSecurityFindingDataclass:
    """Tests for SecurityFinding dataclass."""

    def test_create_minimal_finding(self) -> None:
        """Create a finding with required fields."""
        finding = SecurityFinding(
            rule_id="DS126858",
            dd_category="insecure_crypto",
            cwe_ids=["CWE-328"],
            file_path="InsecureCrypto.cs",
            line_start=10,
            line_end=10,
            column_start=1,
            column_end=20,
            severity="HIGH",
            message="Weak hash algorithm",
        )
        assert finding.rule_id == "DS126858"
        assert finding.dd_category == "insecure_crypto"
        assert finding.cwe_ids == ["CWE-328"]
        assert finding.file_path == "InsecureCrypto.cs"
        assert finding.severity == "HIGH"
        assert finding.code_snippet == ""  # default

    def test_finding_with_snippet(self) -> None:
        """Create finding with code snippet."""
        finding = SecurityFinding(
            rule_id="DS104456",
            dd_category="sql_injection",
            cwe_ids=["CWE-89"],
            file_path="SqlQuery.cs",
            line_start=25,
            line_end=25,
            column_start=5,
            column_end=50,
            severity="CRITICAL",
            message="SQL injection vulnerability",
            code_snippet="cmd.CommandText = query;",
        )
        assert finding.code_snippet == "cmd.CommandText = query;"
        assert finding.cwe_ids == ["CWE-89"]

    def test_finding_to_dict(self) -> None:
        """Convert finding to dict."""
        finding = SecurityFinding(
            rule_id="DS181731",
            dd_category="deserialization",
            cwe_ids=["CWE-502"],
            file_path="Deserialize.cs",
            line_start=15,
            line_end=15,
            column_start=1,
            column_end=30,
            severity="HIGH",
            message="Insecure deserialization",
        )
        d = asdict(finding)
        assert d["rule_id"] == "DS181731"
        assert d["dd_category"] == "deserialization"
        assert d["cwe_ids"] == ["CWE-502"]


class TestFileStatsDataclass:
    """Tests for FileStats dataclass."""

    def test_create_file_stats(self) -> None:
        """Create file stats with basic info."""
        stats = FileStats(
            path="src/Program.cs",
            language="csharp",
            lines=150,
            issue_count=3,
            issue_density=2.0,
        )
        assert stats.path == "src/Program.cs"
        assert stats.language == "csharp"
        assert stats.lines == 150
        assert stats.issue_count == 3

    def test_file_stats_with_breakdowns(self) -> None:
        """File stats with category and severity breakdowns."""
        stats = FileStats(
            path="Crypto.cs",
            language="csharp",
            lines=100,
            issue_count=5,
            issue_density=5.0,
            by_category={"insecure_crypto": 4, "hardcoded_secret": 1},
            by_severity={"HIGH": 3, "MEDIUM": 2},
        )
        assert stats.by_category["insecure_crypto"] == 4
        assert stats.by_severity["HIGH"] == 3

    def test_clean_file_stats(self) -> None:
        """File stats for clean file."""
        stats = FileStats(
            path="SafeCode.cs",
            language="csharp",
            lines=50,
            issue_count=0,
            issue_density=0.0,
        )
        assert stats.issue_count == 0
        assert stats.issue_density == 0.0


class TestDistribution:
    """Tests for Distribution dataclass and statistics."""

    def test_distribution_from_empty_values(self) -> None:
        """Empty values should return zero distribution."""
        dist = Distribution.from_values([])
        assert dist.count == 0
        assert dist.mean == 0.0
        assert dist.stddev == 0.0

    def test_distribution_from_single_value(self) -> None:
        """Single value distribution."""
        dist = Distribution.from_values([5.0])
        assert dist.count == 1
        assert dist.min == 5.0
        assert dist.max == 5.0
        assert dist.mean == 5.0
        assert dist.stddev == 0.0

    def test_distribution_from_values(self) -> None:
        """Distribution from multiple values."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        dist = Distribution.from_values(values)
        assert dist.count == 10
        assert dist.min == 1.0
        assert dist.max == 10.0
        assert dist.mean == 5.5
        assert dist.p50 == 5.5  # median

    def test_distribution_inequality_metrics(self) -> None:
        """Test inequality metrics (gini, theil, hoover)."""
        # Highly unequal distribution
        unequal = [0.0, 0.0, 0.0, 0.0, 100.0]
        dist = Distribution.from_values(unequal)
        assert dist.gini > 0.5  # High inequality

    def test_distribution_to_dict(self) -> None:
        """Convert distribution to dict."""
        dist = Distribution.from_values([1.0, 2.0, 3.0])
        d = distribution_to_dict(dist)
        assert "count" in d
        assert "mean" in d
        assert "gini" in d
        assert d["count"] == 3


class TestStatisticsHelpers:
    """Tests for statistical helper functions."""

    def test_compute_skewness_normal(self) -> None:
        """Skewness of symmetric distribution should be near zero."""
        symmetric = [1.0, 2.0, 3.0, 4.0, 5.0]
        mean = sum(symmetric) / len(symmetric)
        skew = compute_skewness(symmetric, mean)
        assert abs(skew) < 0.5  # Near zero

    def test_compute_skewness_short_list(self) -> None:
        """Skewness of short list should return 0."""
        assert compute_skewness([1.0], 1.0) == 0
        assert compute_skewness([1.0, 2.0], 1.5) == 0

    def test_compute_gini_equal(self) -> None:
        """Gini of equal values should be near zero."""
        equal = [10.0, 10.0, 10.0, 10.0]
        gini = compute_gini(equal)
        assert gini == 0.0

    def test_compute_gini_unequal(self) -> None:
        """Gini of unequal values should be positive."""
        unequal = [0.0, 0.0, 0.0, 100.0]
        gini = compute_gini(unequal)
        assert gini > 0.5

    def test_compute_hoover_equal(self) -> None:
        """Hoover of equal values should be zero."""
        equal = [25.0, 25.0, 25.0, 25.0]
        hoover = compute_hoover(equal)
        assert hoover == 0.0

    def test_compute_top_share(self) -> None:
        """Top share calculation."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        # Total = 150, top 20% (1 element) = 50
        share = compute_top_share(values, 0.20)
        assert share > 0.3  # Top element is 33% of total

    def test_compute_bottom_share(self) -> None:
        """Bottom share calculation."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        share = compute_bottom_share(values, 0.20)
        assert share < 0.1  # Bottom element is ~7% of total


class TestParseSarifResults:
    """Tests for parse_sarif_results function."""

    def test_parse_empty_sarif(self) -> None:
        """Empty SARIF should return empty findings."""
        sarif = {"runs": [{"results": []}]}
        findings = parse_sarif_results(sarif, "/tmp/repo")
        assert findings == []

    def test_parse_sarif_with_finding(self) -> None:
        """Parse SARIF with a single finding."""
        sarif = {
            "runs": [{
                "results": [{
                    "ruleId": "DS126858",
                    "message": {"text": "Weak hash algorithm"},
                    "level": "warning",
                    "locations": [{
                        "physicalLocation": {
                            "artifactLocation": {"uri": "InsecureCrypto.cs"},
                            "region": {
                                "startLine": 10,
                                "endLine": 10,
                                "startColumn": 5,
                                "endColumn": 20,
                            },
                        },
                    }],
                }],
            }],
        }
        findings = parse_sarif_results(sarif, "/tmp/repo")
        assert len(findings) == 1
        assert findings[0].rule_id == "DS126858"
        assert findings[0].dd_category == "insecure_crypto"
        assert findings[0].file_path == "InsecureCrypto.cs"

    def test_parse_sarif_with_file_uri(self) -> None:
        """Parse SARIF with file:// URI."""
        sarif = {
            "runs": [{
                "results": [{
                    "ruleId": "DS104456",
                    "message": {"text": "SQL injection"},
                    "level": "error",
                    "locations": [{
                        "physicalLocation": {
                            "artifactLocation": {"uri": "file:///tmp/repo/SqlQuery.cs"},
                            "region": {"startLine": 15},
                        },
                    }],
                }],
            }],
        }
        findings = parse_sarif_results(sarif, "/tmp/repo")
        assert len(findings) == 1
        assert findings[0].file_path == "SqlQuery.cs"

    def test_parse_sarif_severity_mapping(self) -> None:
        """Test SARIF level to severity mapping."""
        sarif_error = {
            "runs": [{"results": [{
                "ruleId": "TEST",
                "message": {"text": "test"},
                "level": "error",
                "locations": [{"physicalLocation": {
                    "artifactLocation": {"uri": "test.cs"},
                    "region": {"startLine": 1},
                }}],
            }]}],
        }
        sarif_warning = {
            "runs": [{"results": [{
                "ruleId": "TEST",
                "message": {"text": "test"},
                "level": "warning",
                "locations": [{"physicalLocation": {
                    "artifactLocation": {"uri": "test.cs"},
                    "region": {"startLine": 1},
                }}],
            }]}],
        }
        sarif_note = {
            "runs": [{"results": [{
                "ruleId": "TEST",
                "message": {"text": "test"},
                "level": "note",
                "locations": [{"physicalLocation": {
                    "artifactLocation": {"uri": "test.cs"},
                    "region": {"startLine": 1},
                }}],
            }]}],
        }

        assert parse_sarif_results(sarif_error, "/tmp")[0].severity == "CRITICAL"
        assert parse_sarif_results(sarif_warning, "/tmp")[0].severity == "HIGH"
        assert parse_sarif_results(sarif_note, "/tmp")[0].severity == "MEDIUM"


class TestBuildDirectoryEntries:
    """Tests for build_directory_entries function."""

    def test_empty_files_returns_empty(self) -> None:
        """Empty file list returns empty directory list."""
        dirs = build_directory_entries([], "/tmp")
        assert dirs == []

    def test_single_file_root_directory(self) -> None:
        """Single file in root creates one directory entry."""
        files = [FileStats(
            path="test.cs",
            language="csharp",
            lines=100,
            issue_count=1,
            issue_density=1.0,
        )]
        dirs = build_directory_entries(files, "/tmp")
        assert len(dirs) == 1
        assert dirs[0].path == "."
        assert dirs[0].recursive.file_count == 1

    def test_nested_files_creates_hierarchy(self) -> None:
        """Nested files create directory hierarchy."""
        files = [
            FileStats(path="src/app.cs", language="csharp", lines=100, issue_count=2, issue_density=2.0),
            FileStats(path="src/utils/helper.cs", language="csharp", lines=50, issue_count=1, issue_density=2.0),
        ]
        dirs = build_directory_entries(files, "/tmp")

        # Should have: src, src/utils (root "." only if files are directly in root)
        dir_paths = [d.path for d in dirs]
        assert "src" in dir_paths
        assert "src/utils" in dir_paths

    def test_root_directory_created_for_root_files(self) -> None:
        """Root directory created when files exist directly in root."""
        files = [
            FileStats(path="root.cs", language="csharp", lines=100, issue_count=1, issue_density=1.0),
            FileStats(path="src/app.cs", language="csharp", lines=50, issue_count=1, issue_density=2.0),
        ]
        dirs = build_directory_entries(files, "/tmp")

        dir_paths = [d.path for d in dirs]
        assert "." in dir_paths
        assert "src" in dir_paths

    def test_directory_stats_rollup(self) -> None:
        """Directory stats should roll up from files."""
        files = [
            FileStats(
                path="src/Crypto.cs",
                language="csharp",
                lines=100,
                issue_count=3,
                issue_density=3.0,
                by_category={"insecure_crypto": 3},
                by_severity={"HIGH": 3},
            ),
        ]
        dirs = build_directory_entries(files, "/tmp")
        src_dir = next((d for d in dirs if d.path == "src"), None)
        assert src_dir is not None
        assert src_dir.direct.issue_count == 3
        assert src_dir.recursive.issue_count == 3


class TestResultToDict:
    """Tests for result_to_dict function."""

    def test_empty_result_to_dict(self) -> None:
        """Convert empty result to dict."""
        result = AnalysisResult(
            generated_at="2026-01-22T00:00:00Z",
            repo_name="test",
            repo_path="/tmp/test",
        )
        output = result_to_dict(result)

        assert output["schema_version"] == "2.0.0"
        assert output["repo_name"] == "test"
        assert "results" in output
        assert output["results"]["tool"] == "devskim"

    def test_result_with_findings_to_dict(self) -> None:
        """Convert result with findings to dict."""
        finding = SecurityFinding(
            rule_id="DS126858",
            dd_category="insecure_crypto",
            cwe_ids=["CWE-328"],
            file_path="Crypto.cs",
            line_start=10,
            line_end=10,
            column_start=1,
            column_end=20,
            severity="HIGH",
            message="Weak hash",
        )
        file_stat = FileStats(
            path="Crypto.cs",
            language="csharp",
            lines=100,
            issue_count=1,
            issue_density=1.0,
            issues=[finding],
        )
        result = AnalysisResult(
            generated_at="2026-01-22T00:00:00Z",
            repo_name="test",
            repo_path="/tmp/test",
            findings=[finding],
            files=[file_stat],
            by_category={"insecure_crypto": 1},
            by_severity={"HIGH": 1},
        )
        output = result_to_dict(result)

        results = output["results"]
        assert results["summary"]["total_issues"] == 1
        assert len(results["files"]) == 1
        assert results["files"][0]["path"] == "Crypto.cs"
        assert len(results["files"][0]["issues"]) == 1


class TestGetDevskimVersion:
    """Tests for get_devskim_version function."""

    def test_get_version_success(self) -> None:
        """Get devskim version with mocked subprocess."""
        mock_result = MagicMock()
        mock_result.stdout = "1.0.28\n"

        with patch("security_analyzer.subprocess.run", return_value=mock_result):
            version = get_devskim_version()

        assert version == "1.0.28"

    def test_get_version_strips_whitespace(self) -> None:
        """Version string should be stripped."""
        mock_result = MagicMock()
        mock_result.stdout = "  1.0.28  \n"

        with patch("security_analyzer.subprocess.run", return_value=mock_result):
            version = get_devskim_version()

        assert version == "1.0.28"

    def test_get_version_failure_returns_unknown(self) -> None:
        """Failed version check returns 'unknown'."""
        with patch("security_analyzer.subprocess.run", side_effect=Exception("not found")):
            version = get_devskim_version()

        assert version == "unknown"


class TestCountLines:
    """Tests for count_lines function."""

    def test_count_lines_simple_file(self) -> None:
        """Count lines in a simple file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cs', delete=False) as f:
            f.write("line1\nline2\nline3\n")
            temp_path = f.name

        try:
            count = count_lines(temp_path)
            assert count == 3
        finally:
            os.unlink(temp_path)

    def test_count_lines_empty_file(self) -> None:
        """Count lines in an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cs', delete=False) as f:
            temp_path = f.name

        try:
            count = count_lines(temp_path)
            assert count == 0
        finally:
            os.unlink(temp_path)

    def test_count_lines_nonexistent_file(self) -> None:
        """Count lines for nonexistent file returns 0."""
        count = count_lines("/nonexistent/path/file.cs")
        assert count == 0


class TestConstants:
    """Tests for module constants."""

    def test_security_categories_defined(self) -> None:
        """All expected security categories are defined."""
        expected = [
            "sql_injection",
            "hardcoded_secret",
            "insecure_crypto",
            "path_traversal",
            "xss",
            "deserialization",
        ]
        for cat in expected:
            assert cat in SECURITY_CATEGORIES

    def test_severity_map_defined(self) -> None:
        """Severity mapping is defined."""
        assert "Critical" in SEVERITY_MAP
        assert "Important" in SEVERITY_MAP
        assert SEVERITY_MAP["Critical"] == "CRITICAL"
        assert SEVERITY_MAP["Important"] == "HIGH"

    def test_rule_to_category_map_has_entries(self) -> None:
        """Rule to category map has entries."""
        assert len(RULE_TO_CATEGORY_MAP) > 0
        assert "DS126858" in RULE_TO_CATEGORY_MAP
        assert RULE_TO_CATEGORY_MAP["DS126858"] == "insecure_crypto"


class TestDirectoryStatsToDict:
    """Tests for directory_stats_to_dict function."""

    def test_empty_stats_to_dict(self) -> None:
        """Convert empty stats to dict."""
        stats = DirectoryStats()
        d = directory_stats_to_dict(stats)
        assert d["file_count"] == 0
        assert d["issue_count"] == 0

    def test_stats_with_values_to_dict(self) -> None:
        """Convert populated stats to dict."""
        stats = DirectoryStats(
            file_count=5,
            lines_code=500,
            issue_count=10,
            by_category={"insecure_crypto": 8, "sql_injection": 2},
            by_severity={"HIGH": 6, "MEDIUM": 4},
            issue_density=2.0,
        )
        d = directory_stats_to_dict(stats)
        assert d["file_count"] == 5
        assert d["issue_count"] == 10
        assert d["by_category"]["insecure_crypto"] == 8
