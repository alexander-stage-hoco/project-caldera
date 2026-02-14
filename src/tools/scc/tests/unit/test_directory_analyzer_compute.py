"""Tests for directory_analyzer.py computation functions.

Covers compute_language_stats, compute_directory_stats, format_file_entry,
analyze_directories - the core data processing pipeline.
"""
from __future__ import annotations

import pytest
from scripts.directory_analyzer import (
    compute_language_stats,
    compute_directory_stats,
    format_file_entry,
    analyze_directories,
    get_terminal_width,
    print_header,
    print_section,
    print_section_end,
    print_row,
    set_color_enabled,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_file(
    location: str = "src/main.py",
    language: str = "Python",
    lines: int = 100,
    code: int = 80,
    comment: int = 10,
    blank: int = 10,
    bytes: int = 2500,
    complexity: int = 8,
    uloc: int = 70,
    minified: bool = False,
    generated: bool = False,
    binary: bool = False,
) -> dict:
    """Create a normalized file entry (lowercase keys as from run_scc_by_file)."""
    return {
        "location": location,
        "language": language,
        "lines": lines,
        "code": code,
        "comment": comment,
        "blank": blank,
        "bytes": bytes,
        "complexity": complexity,
        "uloc": uloc,
        "minified": minified,
        "generated": generated,
        "binary": binary,
    }


@pytest.fixture
def sample_files():
    """Sample file entries for testing."""
    return [
        make_file("src/main.py", "Python", 100, 80, 10, 10, 2500, 8, 70),
        make_file("src/utils.py", "Python", 50, 40, 5, 5, 1200, 3, 35),
        make_file("src/app.py", "Python", 200, 160, 20, 20, 5000, 15, 140),
        make_file("tests/test_main.py", "Python", 80, 60, 5, 15, 1800, 2, 55),
        make_file("lib/app.js", "JavaScript", 150, 120, 15, 15, 3000, 10, 100),
        make_file("lib/utils.js", "JavaScript", 75, 60, 8, 7, 1500, 5, 50),
        make_file("lib/helper.js", "JavaScript", 30, 20, 5, 5, 600, 1, 18),
    ]


# ---------------------------------------------------------------------------
# Tests: compute_language_stats
# ---------------------------------------------------------------------------

class TestComputeLanguageStats:
    def test_groups_by_language(self, sample_files):
        result = compute_language_stats(sample_files)
        assert "Python" in result
        assert "JavaScript" in result
        assert len(result) == 2

    def test_file_count_per_language(self, sample_files):
        result = compute_language_stats(sample_files)
        assert result["Python"]["file_count"] == 4
        assert result["JavaScript"]["file_count"] == 3

    def test_code_totals(self, sample_files):
        result = compute_language_stats(sample_files)
        # Python: 80 + 40 + 160 + 60 = 340
        assert result["Python"]["code"] == 340
        # JavaScript: 120 + 60 + 20 = 200
        assert result["JavaScript"]["code"] == 200

    def test_computed_ratios(self, sample_files):
        result = compute_language_stats(sample_files)
        py = result["Python"]
        assert py["avg_file_loc"] > 0
        assert py["avg_complexity"] > 0
        assert py["comment_ratio"] > 0
        assert py["dryness"] > 0

    def test_distributions_present_when_3_plus_files(self, sample_files):
        result = compute_language_stats(sample_files)
        # Python has 4 files, JavaScript has 3 - both should have distributions
        assert result["Python"]["loc_distribution"] is not None
        assert result["JavaScript"]["loc_distribution"] is not None

    def test_distributions_none_for_fewer_than_3_files(self):
        files = [
            make_file("a.py", "Python", 100, 80),
            make_file("b.py", "Python", 50, 40),
        ]
        result = compute_language_stats(files)
        assert result["Python"]["loc_distribution"] is None

    def test_empty_files(self):
        result = compute_language_stats([])
        assert result == {}


# ---------------------------------------------------------------------------
# Tests: compute_directory_stats
# ---------------------------------------------------------------------------

class TestComputeDirectoryStats:
    def test_empty_files_returns_zeros(self):
        result = compute_directory_stats([])
        assert result["file_count"] == 0
        assert result["code"] == 0
        assert result["loc_distribution"] is None

    def test_basic_aggregation(self, sample_files):
        result = compute_directory_stats(sample_files)
        assert result["file_count"] == 7
        assert result["code"] == 540  # 80+40+160+60+120+60+20
        assert result["complexity_total"] == 44  # 8+3+15+2+10+5+1

    def test_computed_ratios(self, sample_files):
        result = compute_directory_stats(sample_files)
        assert result["avg_file_loc"] > 0
        assert result["avg_complexity"] > 0
        assert result["comment_ratio"] > 0
        assert result["dryness"] > 0
        assert result["blank_ratio"] > 0

    def test_file_classifications(self, sample_files):
        result = compute_directory_stats(sample_files)
        assert result["test_file_count"] == 1  # tests/test_main.py
        assert result["test_loc"] == 60

    def test_distributions_present(self, sample_files):
        result = compute_directory_stats(sample_files)
        assert result["loc_distribution"] is not None
        assert result["complexity_distribution"] is not None
        assert result["comment_ratio_distribution"] is not None
        assert result["bytes_distribution"] is not None

    def test_by_language_present(self, sample_files):
        result = compute_directory_stats(sample_files)
        assert "Python" in result["by_language"]
        assert "JavaScript" in result["by_language"]

    def test_minified_generated_counts(self):
        files = [
            make_file("a.py", minified=True),
            make_file("b.py", generated=True),
            make_file("c.py"),
        ]
        result = compute_directory_stats(files)
        assert result["minified_count"] == 1
        assert result["generated_count"] == 1
        assert result["minified_ratio"] > 0
        assert result["generated_ratio"] > 0


# ---------------------------------------------------------------------------
# Tests: format_file_entry
# ---------------------------------------------------------------------------

class TestFormatFileEntry:
    def test_basic_formatting(self):
        f = make_file("src/main.py", "Python", 100, 80, 10, 10, 2500, 8, 70)
        result = format_file_entry(f)

        assert result["path"] == "src/main.py"
        assert result["filename"] == "main.py"
        assert result["directory"] == "src"
        assert result["language"] == "Python"
        assert result["extension"] == ".py"
        assert result["lines"] == 100
        assert result["code"] == 80
        assert result["complexity"] == 8

    def test_computed_ratios(self):
        f = make_file("src/main.py", "Python", 100, 80, 10, 10, 2500, 8, 70)
        result = format_file_entry(f)

        assert result["comment_ratio"] == round(10 / 100, 4)
        assert result["blank_ratio"] == round(10 / 100, 4)
        assert result["code_ratio"] == round(80 / 100, 4)
        assert result["complexity_density"] == round(8 / 80, 4)
        assert result["dryness"] == round(70 / 80, 4)
        assert result["bytes_per_loc"] == round(2500 / 80, 2)

    def test_zero_lines_ratios(self):
        f = make_file("empty.py", lines=0, code=0, comment=0, blank=0, uloc=0)
        result = format_file_entry(f)
        assert result["comment_ratio"] == 0
        assert result["complexity_density"] == 0
        assert result["dryness"] == 0
        assert result["bytes_per_loc"] == 0

    def test_classification_test_file(self):
        f = make_file("tests/test_main.py", "Python")
        result = format_file_entry(f)
        assert result["classification"] == "test"

    def test_classification_source_file(self):
        f = make_file("src/main.py", "Python")
        result = format_file_entry(f)
        assert result["classification"] is None  # Source files return None

    def test_flags(self):
        f = make_file(minified=True, generated=True, binary=True)
        result = format_file_entry(f)
        assert result["is_minified"] is True
        assert result["is_generated"] is True
        assert result["is_binary"] is True


# ---------------------------------------------------------------------------
# Tests: analyze_directories
# ---------------------------------------------------------------------------

class TestAnalyzeDirectories:
    def test_empty_files(self):
        result = analyze_directories([])
        assert result["schema_version"] == "2.1"
        assert len(result["directories"]) == 0
        assert len(result["files"]) == 0
        assert result["summary"]["total_files"] == 0

    def test_basic_analysis(self, sample_files):
        result = analyze_directories(sample_files, cocomo_preset="sme")
        assert result["schema_version"] == "2.1"
        assert "directories" in result
        assert "files" in result
        assert "summary" in result
        assert len(result["files"]) == 7
        assert len(result["directories"]) > 0

    def test_directory_direct_recursive_invariant(self, sample_files):
        result = analyze_directories(sample_files, cocomo_preset="sme")
        for d in result["directories"]:
            assert d["recursive"]["file_count"] >= d["direct"]["file_count"], (
                f"Directory {d['path']}: recursive ({d['recursive']['file_count']}) "
                f"< direct ({d['direct']['file_count']})"
            )

    def test_summary_totals(self, sample_files):
        result = analyze_directories(sample_files, cocomo_preset="sme")
        summary = result["summary"]
        assert summary["total_files"] == 7
        assert summary["total_loc"] > 0
        assert summary["total_directories"] > 0

    def test_cocomo_estimates_present(self, sample_files):
        result = analyze_directories(sample_files, cocomo_preset="sme")
        cocomo = result["summary"].get("cocomo", {})
        assert len(cocomo) == 8  # 8 presets
        assert "sme" in cocomo
        assert "open_source" in cocomo
        assert cocomo["open_source"]["cost"] == 0

    def test_leaf_directories_correct(self, sample_files):
        result = analyze_directories(sample_files, cocomo_preset="sme")
        for d in result["directories"]:
            if d["is_leaf"]:
                assert d["child_count"] == 0
            else:
                assert d["child_count"] > 0

    def test_distributions_in_summary(self, sample_files):
        result = analyze_directories(sample_files, cocomo_preset="sme")
        dists = result["summary"].get("distributions", {})
        assert "loc" in dists
        assert "complexity" in dists

    def test_by_language_in_summary(self, sample_files):
        result = analyze_directories(sample_files, cocomo_preset="sme")
        by_lang = result["summary"].get("by_language", {})
        assert "Python" in by_lang
        assert "JavaScript" in by_lang

    def test_file_classifications_in_summary(self, sample_files):
        result = analyze_directories(sample_files, cocomo_preset="sme")
        fc = result["summary"].get("file_classifications", {})
        assert "source_file_count" in fc
        assert "test_file_count" in fc
        assert fc["test_file_count"] >= 1

    def test_sum_direct_equals_total(self, sample_files):
        result = analyze_directories(sample_files, cocomo_preset="sme")
        total_direct = sum(
            d["direct"]["file_count"] for d in result["directories"]
        )
        assert total_direct == result["summary"]["total_files"]


# ---------------------------------------------------------------------------
# Tests: Display helpers (just ensure no crash, don't check output)
# ---------------------------------------------------------------------------

class TestDisplayHelpers:
    def test_get_terminal_width(self):
        width = get_terminal_width()
        assert width >= 80

    def test_print_header_no_crash(self, capsys):
        set_color_enabled(False)
        print_header("Test Header")
        captured = capsys.readouterr()
        assert "Test Header" in captured.out
        set_color_enabled(True)

    def test_print_section_no_crash(self, capsys):
        set_color_enabled(False)
        print_section("Test Section")
        captured = capsys.readouterr()
        assert "Test Section" in captured.out
        set_color_enabled(True)

    def test_print_section_end_no_crash(self, capsys):
        set_color_enabled(False)
        print_section_end()
        capsys.readouterr()  # Just check no crash
        set_color_enabled(True)

    def test_print_row_single_column(self, capsys):
        set_color_enabled(False)
        print_row("Label", "Value")
        captured = capsys.readouterr()
        assert "Label" in captured.out
        assert "Value" in captured.out
        set_color_enabled(True)

    def test_print_row_two_columns(self, capsys):
        set_color_enabled(False)
        print_row("Label1", "Value1", "Label2", "Value2")
        captured = capsys.readouterr()
        assert "Label1" in captured.out
        assert "Label2" in captured.out
        set_color_enabled(True)
