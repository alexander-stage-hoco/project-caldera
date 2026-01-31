"""Integration tests for SCC comparison.

Tests comparison between layout scanner output and SCC output
for language detection and file counts.
"""

import json
import pytest
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks.scc_comparison import (
    ComparisonResult,
    LanguageComparison,
    compare_with_scc,
    parse_scc_output,
    parse_layout_output,
    normalize_language,
    run_scc_comparison_checks,
    check_total_file_count,
    check_language_detection_coverage,
    check_language_count_accuracy,
    check_major_language_agreement,
    LANGUAGE_NORMALIZATION,
)
from checks import CheckCategory


# =============================================================================
# Language Normalization Tests
# =============================================================================


class TestLanguageNormalization:
    """Test language name normalization."""

    def test_normalize_csharp_variants(self):
        """C# variants should normalize to 'C#'."""
        assert normalize_language("C#") == "C#"
        assert normalize_language("csharp") == "C#"
        assert normalize_language("CSharp") == "C#"

    def test_normalize_javascript_variants(self):
        """JavaScript variants should normalize."""
        assert normalize_language("JavaScript") == "JavaScript"
        assert normalize_language("javascript") == "JavaScript"
        assert normalize_language("js") == "JavaScript"

    def test_normalize_typescript(self):
        """TypeScript variants should normalize."""
        assert normalize_language("TypeScript") == "TypeScript"
        assert normalize_language("typescript") == "TypeScript"
        assert normalize_language("ts") == "TypeScript"

    def test_normalize_shell_variants(self):
        """Shell variants should normalize to 'Shell'."""
        assert normalize_language("Shell") == "Shell"
        assert normalize_language("Bash") == "Shell"
        assert normalize_language("bash") == "Shell"
        assert normalize_language("sh") == "Shell"

    def test_unknown_languages_passthrough(self):
        """Unknown languages should pass through unchanged."""
        assert normalize_language("Haskell") == "Haskell"
        assert normalize_language("CustomLang") == "CustomLang"

    def test_normalize_powershell_variants(self):
        """PowerShell variants should normalize to 'PowerShell'."""
        assert normalize_language("PowerShell") == "PowerShell"
        assert normalize_language("Powershell") == "PowerShell"  # SCC uses this
        assert normalize_language("powershell") == "PowerShell"

    def test_normalize_scc_specific_formats(self):
        """SCC-specific build formats should normalize."""
        assert normalize_language("MSBuild") == "MSBuild"
        assert normalize_language("msbuild") == "MSBuild"
        assert normalize_language("nuspec") == "nuspec"
        assert normalize_language("NuSpec") == "nuspec"

    def test_normalize_scc_special_categories(self):
        """SCC special categories should normalize."""
        assert normalize_language("License") == "License"
        assert normalize_language("Plain Text") == "Plain Text"
        assert normalize_language("plaintext") == "Plain Text"
        assert normalize_language("TemplateToolkit") == "TemplateToolkit"


# =============================================================================
# SCC Output Parsing Tests
# =============================================================================


class TestParseSccOutput:
    """Test parsing SCC output format."""

    def test_parse_simple_scc_output(self):
        """Parse simple SCC output."""
        scc_output = [
            {"Name": "Python", "Count": 10},
            {"Name": "JavaScript", "Count": 5},
        ]

        result = parse_scc_output(scc_output)

        assert result["Python"] == 10
        assert result["JavaScript"] == 5

    def test_parse_full_scc_output(self):
        """Parse full SCC output with all fields."""
        scc_output = [
            {
                "Name": "Python",
                "Bytes": 26520,
                "CodeBytes": 0,
                "Lines": 892,
                "Code": 765,
                "Comment": 58,
                "Blank": 69,
                "Complexity": 56,
                "Count": 9,
            },
            {
                "Name": "Go",
                "Bytes": 22118,
                "Lines": 1127,
                "Code": 845,
                "Count": 9,
            },
        ]

        result = parse_scc_output(scc_output)

        assert result["Python"] == 9
        assert result["Go"] == 9

    def test_parse_scc_normalizes_languages(self):
        """SCC output parsing should normalize language names."""
        scc_output = [
            {"Name": "JavaScript", "Count": 5},
            {"Name": "TypeScript", "Count": 3},
        ]

        result = parse_scc_output(scc_output)

        assert result["JavaScript"] == 5
        assert result["TypeScript"] == 3

    def test_parse_scc_empty_output(self):
        """Parsing empty SCC output should return empty dict."""
        result = parse_scc_output([])
        assert result == {}

    def test_parse_scc_skips_zero_count(self):
        """Languages with zero count should be skipped."""
        scc_output = [
            {"Name": "Python", "Count": 10},
            {"Name": "Go", "Count": 0},
        ]

        result = parse_scc_output(scc_output)

        assert "Python" in result
        assert "Go" not in result


# =============================================================================
# Layout Output Parsing Tests
# =============================================================================


class TestParseLayoutOutput:
    """Test parsing layout scanner output format."""

    def test_parse_layout_output(self):
        """Parse layout scanner output from statistics."""
        layout_output = {
            "statistics": {
                "total_files": 15,
                "by_language": {
                    "Python": 10,
                    "JavaScript": 5,
                },
            },
        }

        result = parse_layout_output(layout_output)

        assert result["Python"] == 10
        assert result["JavaScript"] == 5

    def test_parse_layout_excludes_unknown(self):
        """'unknown' language should be excluded."""
        layout_output = {
            "statistics": {
                "by_language": {
                    "Python": 10,
                    "unknown": 5,
                },
            },
        }

        result = parse_layout_output(layout_output)

        assert "Python" in result
        assert "unknown" not in result

    def test_parse_layout_empty_statistics(self):
        """Empty statistics should return empty dict."""
        layout_output = {"statistics": {}}
        result = parse_layout_output(layout_output)
        assert result == {}

    def test_parse_layout_missing_statistics(self):
        """Missing statistics should return empty dict."""
        layout_output = {}
        result = parse_layout_output(layout_output)
        assert result == {}


# =============================================================================
# Compare With SCC Tests
# =============================================================================


class TestCompareWithScc:
    """Test the main comparison function."""

    def test_compare_exact_match(self):
        """Test comparison when outputs match exactly."""
        layout_output = {
            "statistics": {
                "total_files": 15,
                "by_language": {"Python": 10, "Go": 5},
            },
        }
        scc_output = [
            {"Name": "Python", "Count": 10},
            {"Name": "Go", "Count": 5},
        ]

        result = compare_with_scc(layout_output, scc_output)

        assert result.layout_total_files == 15
        assert result.scc_total_files == 15
        assert result.total_file_difference == 0
        assert result.language_agreement_rate == 1.0
        assert len(result.common_languages) == 2
        assert len(result.layout_only_languages) == 0
        assert len(result.scc_only_languages) == 0

    def test_compare_layout_has_more_files(self):
        """Test when layout scanner counts more files (common case)."""
        layout_output = {
            "statistics": {
                "total_files": 25,  # Includes non-code files
                "by_language": {"Python": 10, "Go": 5, "JSON": 5, "YAML": 5},
            },
        }
        scc_output = [
            {"Name": "Python", "Count": 10},
            {"Name": "Go", "Count": 5},
        ]

        result = compare_with_scc(layout_output, scc_output)

        assert result.layout_total_files == 25
        assert result.scc_total_files == 15
        assert result.total_file_difference == 10
        assert "JSON" in result.layout_only_languages
        assert "YAML" in result.layout_only_languages

    def test_compare_language_count_mismatch(self):
        """Test when file counts per language differ."""
        layout_output = {
            "statistics": {
                "total_files": 20,
                "by_language": {"Python": 12, "Go": 8},
            },
        }
        scc_output = [
            {"Name": "Python", "Count": 10},
            {"Name": "Go", "Count": 5},
        ]

        result = compare_with_scc(layout_output, scc_output)

        # Find Python comparison
        py_comp = next(lc for lc in result.language_comparisons if lc.language == "Python")
        assert py_comp.layout_count == 12
        assert py_comp.scc_count == 10
        assert py_comp.count_difference == 2

    def test_compare_scc_has_exclusive_language(self):
        """Test when SCC detects a language not found by layout scanner."""
        layout_output = {
            "statistics": {
                "total_files": 10,
                "by_language": {"Python": 10},
            },
        }
        scc_output = [
            {"Name": "Python", "Count": 10},
            {"Name": "Rust", "Count": 5},  # Not in layout output
        ]

        result = compare_with_scc(layout_output, scc_output)

        assert "Rust" in result.scc_only_languages
        assert result.language_agreement_rate < 1.0

    def test_compare_empty_outputs(self):
        """Test comparison with empty outputs."""
        layout_output = {"statistics": {"total_files": 0, "by_language": {}}}
        scc_output = []

        result = compare_with_scc(layout_output, scc_output)

        assert result.layout_total_files == 0
        assert result.scc_total_files == 0
        assert len(result.common_languages) == 0


# =============================================================================
# Check Functions Tests
# =============================================================================


class TestCheckTotalFileCount:
    """Tests for SCC-1: Total file count check."""

    def test_pass_when_layout_has_more(self):
        """Should pass when layout has more files (expected)."""
        comparison = ComparisonResult(
            layout_total_files=100,
            scc_total_files=80,
            total_file_difference=20,
        )

        result = check_total_file_count(comparison)

        assert result.passed
        assert result.check_id == "SCC-1"

    def test_fail_when_scc_has_more(self):
        """Should fail when SCC has more files (unexpected)."""
        comparison = ComparisonResult(
            layout_total_files=70,
            scc_total_files=100,
            total_file_difference=-30,
        )

        result = check_total_file_count(comparison)

        assert not result.passed
        assert result.check_id == "SCC-1"


class TestCheckLanguageDetectionCoverage:
    """Tests for SCC-2: Language detection coverage check."""

    def test_pass_all_languages_covered(self):
        """Should pass when all SCC languages are detected."""
        comparison = ComparisonResult(
            layout_total_files=100,
            scc_total_files=80,
            total_file_difference=20,
            layout_languages={"Python", "Go", "Rust"},
            scc_languages={"Python", "Go"},
            common_languages={"Python", "Go"},
            layout_only_languages={"Rust"},
            scc_only_languages=set(),
        )

        result = check_language_detection_coverage(comparison)

        assert result.passed
        assert result.check_id == "SCC-2"

    def test_fail_missing_scc_languages(self):
        """Should fail when SCC languages are missing from layout."""
        comparison = ComparisonResult(
            layout_total_files=100,
            scc_total_files=80,
            total_file_difference=20,
            layout_languages={"Python"},
            scc_languages={"Python", "Go", "Rust"},
            common_languages={"Python"},
            layout_only_languages=set(),
            scc_only_languages={"Go", "Rust"},
        )

        result = check_language_detection_coverage(comparison)

        assert not result.passed
        assert "Go" in result.evidence["missing_languages"]
        assert "Rust" in result.evidence["missing_languages"]


class TestCheckLanguageCountAccuracy:
    """Tests for SCC-3: Language count accuracy check."""

    def test_pass_exact_counts(self):
        """Should pass when counts match exactly."""
        comparison = ComparisonResult(
            layout_total_files=15,
            scc_total_files=15,
            total_file_difference=0,
            common_languages={"Python", "Go"},
            language_comparisons=[
                LanguageComparison("Python", 10, 10, 0, True, True),
                LanguageComparison("Go", 5, 5, 0, True, True),
            ],
        )

        result = check_language_count_accuracy(comparison)

        assert result.passed
        assert result.score == 1.0

    def test_pass_within_tolerance(self):
        """Should pass when counts are within tolerance."""
        comparison = ComparisonResult(
            layout_total_files=102,
            scc_total_files=100,
            total_file_difference=2,
            common_languages={"Python"},
            language_comparisons=[
                LanguageComparison("Python", 102, 100, 2, True, True),  # 2% diff
            ],
        )

        # 10% tolerance
        result = check_language_count_accuracy(comparison, tolerance_percent=0.1)

        assert result.passed

    def test_fail_beyond_tolerance(self):
        """Should fail when counts exceed tolerance."""
        comparison = ComparisonResult(
            layout_total_files=150,
            scc_total_files=100,
            total_file_difference=50,
            common_languages={"Python"},
            language_comparisons=[
                LanguageComparison("Python", 150, 100, 50, True, True),  # 50% diff
            ],
        )

        result = check_language_count_accuracy(comparison, tolerance_percent=0.1)

        assert not result.passed


class TestCheckMajorLanguageAgreement:
    """Tests for SCC-4: Major language agreement check."""

    def test_pass_major_languages_match(self):
        """Should pass when major languages have exact match."""
        comparison = ComparisonResult(
            layout_total_files=100,
            scc_total_files=100,
            total_file_difference=0,
            common_languages={"Python", "Go"},
            language_comparisons=[
                LanguageComparison("Python", 60, 60, 0, True, True),  # Major
                LanguageComparison("Go", 40, 40, 0, True, True),  # Major
            ],
        )

        result = check_major_language_agreement(comparison)

        assert result.passed

    def test_fail_major_languages_mismatch(self):
        """Should fail when major languages have count mismatch."""
        comparison = ComparisonResult(
            layout_total_files=100,
            scc_total_files=100,
            total_file_difference=0,
            common_languages={"Python", "Go"},
            language_comparisons=[
                LanguageComparison("Python", 70, 60, 10, True, True),  # Major, mismatch
                LanguageComparison("Go", 30, 40, -10, True, True),  # Major, mismatch
            ],
        )

        result = check_major_language_agreement(comparison)

        assert not result.passed


# =============================================================================
# Run All Checks Tests
# =============================================================================


class TestRunSccComparisonChecks:
    """Tests for running all SCC comparison checks."""

    def test_run_all_checks(self):
        """Should return all check results."""
        layout_output = {
            "statistics": {
                "total_files": 20,
                "by_language": {"Python": 10, "Go": 5, "Rust": 5},
            },
        }
        scc_output = [
            {"Name": "Python", "Count": 10},
            {"Name": "Go", "Count": 5},
            {"Name": "Rust", "Count": 5},
        ]

        results = run_scc_comparison_checks(layout_output, scc_output)

        assert len(results) == 4
        check_ids = {r.check_id for r in results}
        assert "SCC-1" in check_ids
        assert "SCC-2" in check_ids
        assert "SCC-3" in check_ids
        assert "SCC-4" in check_ids

    def test_all_checks_have_category(self):
        """All checks should have ACCURACY category."""
        layout_output = {"statistics": {"total_files": 10, "by_language": {"Python": 10}}}
        scc_output = [{"Name": "Python", "Count": 10}]

        results = run_scc_comparison_checks(layout_output, scc_output)

        for result in results:
            assert result.category == CheckCategory.ACCURACY


# =============================================================================
# Comparison Result Tests
# =============================================================================


class TestComparisonResult:
    """Tests for ComparisonResult dataclass."""

    def test_to_dict(self):
        """to_dict should produce JSON-serializable output."""
        result = ComparisonResult(
            layout_total_files=100,
            scc_total_files=80,
            total_file_difference=20,
            layout_languages={"Python", "Go"},
            scc_languages={"Python"},
            common_languages={"Python"},
            layout_only_languages={"Go"},
            scc_only_languages=set(),
            language_comparisons=[
                LanguageComparison("Python", 80, 80, 0, True, True),
            ],
            language_agreement_rate=0.5,
            count_agreement_rate=1.0,
        )

        d = result.to_dict()

        # Should be JSON-serializable
        json_str = json.dumps(d)
        assert isinstance(json_str, str)

        # Check key fields
        assert d["layout_total_files"] == 100
        assert d["scc_total_files"] == 80
        assert "Python" in d["common_languages"]


# =============================================================================
# Real-World Scenario Tests
# =============================================================================


class TestRealWorldScenarios:
    """Tests simulating real-world comparison scenarios."""

    def test_typical_polyglot_repo(self):
        """Test typical polyglot repository comparison."""
        layout_output = {
            "statistics": {
                "total_files": 150,
                "by_language": {
                    "Python": 45,
                    "TypeScript": 40,
                    "JavaScript": 20,
                    "JSON": 25,
                    "YAML": 10,
                    "Markdown": 10,
                },
            },
        }
        scc_output = [
            {"Name": "Python", "Count": 45},
            {"Name": "TypeScript", "Count": 40},
            {"Name": "JavaScript", "Count": 20},
            {"Name": "JSON", "Count": 25},
            {"Name": "YAML", "Count": 10},
            {"Name": "Markdown", "Count": 10},
        ]

        result = compare_with_scc(layout_output, scc_output)

        assert result.language_agreement_rate == 1.0
        assert result.count_agreement_rate == 1.0
        assert len(result.scc_only_languages) == 0

    def test_layout_detects_more_configs(self):
        """Layout scanner may detect more config/data files."""
        layout_output = {
            "statistics": {
                "total_files": 100,
                "by_language": {
                    "Python": 50,
                    "JavaScript": 20,
                    "JSON": 15,
                    "YAML": 10,
                    "TOML": 5,  # Layout detects this
                },
            },
        }
        scc_output = [
            {"Name": "Python", "Count": 50},
            {"Name": "JavaScript", "Count": 20},
            {"Name": "JSON", "Count": 15},
            {"Name": "YAML", "Count": 10},
            # SCC doesn't report TOML
        ]

        result = compare_with_scc(layout_output, scc_output)

        assert "TOML" in result.layout_only_languages
        assert result.layout_total_files > result.scc_total_files

    def test_scc_groups_header_files_differently(self):
        """SCC may group C/C++ header files differently."""
        layout_output = {
            "statistics": {
                "total_files": 50,
                "by_language": {
                    "C": 20,
                    "C++": 30,
                },
            },
        }
        scc_output = [
            {"Name": "C", "Count": 25},  # Includes some headers
            {"Name": "C++", "Count": 20},
            {"Name": "C Header", "Count": 5},  # SCC separates these
        ]

        result = compare_with_scc(layout_output, scc_output)

        # This is expected discrepancy due to header file handling
        assert result.scc_total_files == result.layout_total_files


class TestEdgeCases:
    """Test edge cases for SCC comparison."""

    def test_empty_layout_output(self):
        """Handle empty layout output gracefully."""
        layout_output = {}
        scc_output = [{"Name": "Python", "Count": 10}]

        result = compare_with_scc(layout_output, scc_output)

        assert result.layout_total_files == 0
        assert result.scc_total_files == 10
        assert "Python" in result.scc_only_languages

    def test_empty_scc_output(self):
        """Handle empty SCC output gracefully."""
        layout_output = {
            "statistics": {
                "total_files": 10,
                "by_language": {"Python": 10},
            },
        }
        scc_output = []

        result = compare_with_scc(layout_output, scc_output)

        assert result.layout_total_files == 10
        assert result.scc_total_files == 0
        assert "Python" in result.layout_only_languages

    def test_both_empty(self):
        """Handle both outputs empty."""
        layout_output = {}
        scc_output = []

        result = compare_with_scc(layout_output, scc_output)

        assert result.layout_total_files == 0
        assert result.scc_total_files == 0
        assert len(result.common_languages) == 0
