"""Tests for directory_analyzer.py display/print functions.

Covers the 18+ print_* dashboard functions that render terminal output.
Uses capsys to capture stdout, with color disabled for predictable assertions.
"""
from __future__ import annotations

import pytest
from scripts.directory_analyzer import (
    set_color_enabled,
    print_header,
    print_section,
    print_section_end,
    print_row,
    print_directory_entry,
    print_all_directories,
    print_top_by_metric,
    print_file_classifications,
    print_inequality_metrics,
    print_language_breakdown,
    print_cocomo_comparison,
    print_distribution_stats,
    print_directory_structure,
    print_top_directories_enhanced,
    print_top_direct_directories,
    print_header_metadata,
    print_validation_evidence,
    print_executive_summary,
    print_quality_indicators,
    print_language_analysis,
    print_per_language_distributions,
    print_inequality_analysis,
    print_distribution_statistics_enhanced,
    print_top_files_by_loc,
    print_top_files_by_complexity,
    print_top_files_by_density,
    print_directory_tree_enhanced,
    print_analysis_summary,
    print_footer,
    strip_ansi,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def disable_colors():
    """Disable color for all tests to get clean output."""
    set_color_enabled(False)
    yield
    set_color_enabled(True)


def _make_dist(count=10, min_v=5, max_v=200, mean_v=80, median_v=60):
    """Create a complete distribution dict."""
    return {
        "count": count,
        "min": min_v,
        "max": max_v,
        "mean": mean_v,
        "median": median_v,
        "stddev": 45.0,
        "p25": 20,
        "p75": 120,
        "p90": 160,
        "p95": 180,
        "p99": 195,
        "skewness": 1.2,
        "kurtosis": 2.5,
        "cv": 0.56,
        "iqr": 100,
        "gini": 0.42,
        "theil": 0.35,
        "hoover": 0.28,
        "palma": 3.5,
        "top_10_pct_share": 0.45,
        "top_20_pct_share": 0.60,
        "bottom_50_pct_share": 0.15,
    }


def _make_directory(path="src", depth=1, is_leaf=False, child_count=2,
                    rec_files=10, rec_code=500, rec_cx=25, rec_avg=2.5,
                    dir_files=3, dir_code=150, dir_cx=8, dir_avg=2.67):
    """Create a directory entry dict."""
    return {
        "path": path,
        "name": path.split("/")[-1],
        "depth": depth,
        "is_leaf": is_leaf,
        "child_count": child_count,
        "recursive": {
            "file_count": rec_files,
            "code": rec_code,
            "complexity_total": rec_cx,
            "avg_complexity": rec_avg,
            "loc_distribution": _make_dist() if rec_files >= 3 else None,
        },
        "direct": {
            "file_count": dir_files,
            "code": dir_code,
            "complexity_total": dir_cx,
            "avg_complexity": dir_avg,
            "loc_distribution": _make_dist() if dir_files >= 3 else None,
        },
    }


def _make_file(path="src/main.py", language="Python", code=100, complexity=8, density=0.08):
    """Create a file entry dict."""
    return {
        "path": path,
        "filename": path.split("/")[-1],
        "language": language,
        "code": code,
        "lines": int(code * 1.2),
        "complexity": complexity,
        "complexity_density": density,
        "comment_ratio": 0.12,
        "blank_ratio": 0.10,
    }


@pytest.fixture
def sample_directories():
    """Sample directories for display testing."""
    return [
        _make_directory("src", depth=0, child_count=3, rec_files=20, rec_code=1500),
        _make_directory("src/core", depth=1, child_count=1, rec_files=12, rec_code=900),
        _make_directory("src/core/utils", depth=2, is_leaf=True, child_count=0,
                        rec_files=5, rec_code=300, dir_files=5, dir_code=300),
        _make_directory("src/api", depth=1, is_leaf=True, child_count=0,
                        rec_files=4, rec_code=350, dir_files=4, dir_code=350),
        _make_directory("tests", depth=0, is_leaf=True, child_count=0,
                        rec_files=3, rec_code=200, dir_files=3, dir_code=200),
    ]


@pytest.fixture
def sample_files():
    """Sample files for display testing."""
    return [
        _make_file("src/core/app.py", "Python", 400, 55, 0.138),
        _make_file("src/core/utils/helpers.py", "Python", 200, 12, 0.060),
        _make_file("src/core/models.py", "Python", 150, 8, 0.053),
        _make_file("src/api/routes.py", "Python", 180, 20, 0.111),
        _make_file("src/api/middleware.py", "Python", 80, 5, 0.063),
        _make_file("lib/utils.js", "JavaScript", 120, 10, 0.083),
        _make_file("lib/main.js", "JavaScript", 90, 7, 0.078),
        _make_file("tests/test_app.py", "Python", 100, 3, 0.030),
    ]


@pytest.fixture
def sample_summary():
    """Sample summary dict with all sub-sections."""
    return {
        "total_files": 8,
        "total_loc": 1320,
        "total_lines": 1650,
        "total_bytes": 35000,
        "total_complexity": 120,
        "total_directories": 5,
        "total_languages": 2,
        "ratios": {
            "avg_complexity": 15.0,
            "complexity_density": 0.091,
            "dryness": 0.85,
            "comment_ratio": 0.12,
            "blank_ratio": 0.10,
            "generated_ratio": 0.0,
            "minified_ratio": 0.0,
        },
        "structure": {
            "max_depth": 2,
            "avg_depth": 1.2,
            "total_directories": 5,
            "leaf_directory_count": 3,
            "avg_files_per_directory": 1.6,
        },
        "languages": {
            "dominant_language": "Python",
            "dominant_language_pct": 0.84,
            "polyglot_score": 0.32,
        },
        "by_language": {
            "Python": {
                "file_count": 6,
                "code": 1110,
                "complexity_total": 103,
                "avg_complexity": 17.2,
                "complexity_density": 0.093,
                "dryness": 0.86,
                "loc_distribution": _make_dist(),
                "complexity_distribution": _make_dist(min_v=3, max_v=55, mean_v=17),
            },
            "JavaScript": {
                "file_count": 2,
                "code": 210,
                "complexity_total": 17,
                "avg_complexity": 8.5,
                "complexity_density": 0.081,
                "dryness": 0.82,
                "loc_distribution": None,
                "complexity_distribution": None,
            },
        },
        "distributions": {
            "loc": _make_dist(),
            "complexity": _make_dist(min_v=3, max_v=55, mean_v=17, median_v=9),
            "comment_ratio": _make_dist(min_v=0, max_v=0.35, mean_v=0.12, median_v=0.10),
            "bytes": _make_dist(min_v=500, max_v=12000, mean_v=4375, median_v=3500),
        },
        "file_classifications": {
            "source_file_count": 5,
            "source_loc": 1010,
            "test_file_count": 1,
            "test_loc": 100,
            "config_file_count": 0,
            "config_loc": 0,
            "docs_file_count": 0,
            "docs_loc": 0,
            "build_file_count": 0,
            "build_loc": 0,
            "ci_file_count": 0,
            "ci_loc": 0,
        },
        "cocomo": {
            "early_startup": {"cost": 50000, "effort_person_months": 3.2, "schedule_months": 4.5, "people": 0.7},
            "growth_startup": {"cost": 65000, "effort_person_months": 4.0, "schedule_months": 5.0, "people": 0.8},
            "scale_up": {"cost": 80000, "effort_person_months": 5.0, "schedule_months": 5.5, "people": 0.9},
            "sme": {"cost": 95000, "effort_person_months": 6.0, "schedule_months": 6.0, "people": 1.0},
            "mid_market": {"cost": 110000, "effort_person_months": 7.0, "schedule_months": 6.5, "people": 1.1},
            "large_enterprise": {"cost": 130000, "effort_person_months": 8.5, "schedule_months": 7.0, "people": 1.2},
            "regulated": {"cost": 160000, "effort_person_months": 10.0, "schedule_months": 7.5, "people": 1.3},
            "open_source": {"cost": 0, "effort_person_months": 2.0, "schedule_months": 3.0, "people": 0.7},
        },
    }


@pytest.fixture
def full_result(sample_directories, sample_files, sample_summary):
    """A full analysis result dict combining dirs, files, summary."""
    return {
        "schema_version": "2.1",
        "run_id": "test-run-display",
        "timestamp": "2026-01-15T10:30:00Z",
        "directories": sample_directories,
        "files": sample_files,
        "summary": sample_summary,
    }


# ---------------------------------------------------------------------------
# Tests: Basic display helpers
# ---------------------------------------------------------------------------

class TestPrintDirectoryEntry:
    def test_basic_output(self, capsys):
        d = _make_directory("src/core")
        print_directory_entry(d)
        out = capsys.readouterr().out
        assert "src/core" in out
        assert "Recursive:" in out

    def test_direct_shown_when_nonzero(self, capsys):
        d = _make_directory("src/core", dir_files=5)
        print_directory_entry(d)
        out = capsys.readouterr().out
        assert "Direct:" in out

    def test_direct_hidden_when_zero(self, capsys):
        d = _make_directory("src/core", dir_files=0, dir_code=0)
        print_directory_entry(d)
        out = capsys.readouterr().out
        assert "Direct:" not in out


class TestPrintAllDirectories:
    def test_prints_all(self, capsys, sample_directories):
        print_all_directories(sample_directories)
        out = capsys.readouterr().out
        assert "5 total" in out
        for d in sample_directories:
            assert d["path"] in out


class TestPrintTopByMetric:
    def test_by_avg_complexity(self, capsys, sample_directories):
        print_top_by_metric(sample_directories, "recursive.avg_complexity",
                            "Top by Complexity", limit=3)
        out = capsys.readouterr().out
        assert "Top by Complexity" in out
        assert "#1" in out

    def test_ascending_sort(self, capsys, sample_directories):
        print_top_by_metric(sample_directories, "recursive.code",
                            "Smallest", limit=2, descending=False)
        out = capsys.readouterr().out
        assert "Smallest" in out


# ---------------------------------------------------------------------------
# Tests: v2.0 Dashboard display functions (summary-based)
# ---------------------------------------------------------------------------

class TestPrintFileClassifications:
    def test_with_classifications(self, capsys, sample_summary):
        print_file_classifications(sample_summary)
        out = capsys.readouterr().out
        assert "File Classifications" in out
        assert "Source" in out
        assert "Test" in out

    def test_empty_classifications(self, capsys):
        print_file_classifications({})
        out = capsys.readouterr().out
        assert out == ""  # Early return for empty


class TestPrintInequalityMetrics:
    def test_with_distributions(self, capsys, sample_summary):
        print_inequality_metrics(sample_summary)
        out = capsys.readouterr().out
        assert "Gini" in out
        assert "Top 10%" in out

    def test_empty_distributions(self, capsys):
        print_inequality_metrics({})
        out = capsys.readouterr().out
        assert out == ""


class TestPrintLanguageBreakdown:
    def test_with_languages(self, capsys, sample_summary):
        print_language_breakdown(sample_summary)
        out = capsys.readouterr().out
        assert "Python" in out
        assert "JavaScript" in out

    def test_empty_languages(self, capsys):
        print_language_breakdown({})
        out = capsys.readouterr().out
        assert out == ""


class TestPrintCocomoComparison:
    def test_all_presets(self, capsys, sample_summary):
        print_cocomo_comparison(sample_summary)
        out = capsys.readouterr().out
        assert "COCOMO" in out
        assert "Early Startup" in out
        assert "Open Source" in out
        assert "$0" in out  # open_source cost

    def test_empty(self, capsys):
        print_cocomo_comparison({})
        out = capsys.readouterr().out
        assert out == ""


class TestPrintDistributionStats:
    def test_with_distributions(self, capsys, sample_summary):
        print_distribution_stats(sample_summary)
        out = capsys.readouterr().out
        assert "LOC" in out
        assert "Complexity" in out
        assert "median" in out

    def test_empty(self, capsys):
        print_distribution_stats({})
        out = capsys.readouterr().out
        assert out == ""


class TestPrintDirectoryStructure:
    def test_with_structure(self, capsys, sample_summary):
        print_directory_structure(sample_summary)
        out = capsys.readouterr().out
        assert "Max Depth" in out
        assert "Leaf Directories" in out

    def test_empty(self, capsys):
        print_directory_structure({})
        out = capsys.readouterr().out
        assert out == ""


class TestPrintTopDirectoriesEnhanced:
    def test_basic(self, capsys, sample_directories):
        print_top_directories_enhanced(sample_directories)
        out = capsys.readouterr().out
        assert "Top 5" in out
        assert "#1" in out
        assert "Recursive:" in out


class TestPrintTopDirectDirectories:
    def test_basic(self, capsys, sample_directories):
        print_top_direct_directories(sample_directories, limit=3)
        out = capsys.readouterr().out
        assert "Top 3" in out
        assert "Direct:" in out


# ---------------------------------------------------------------------------
# Tests: v2.0 Dashboard sections (result-based)
# ---------------------------------------------------------------------------

class TestPrintHeaderMetadata:
    def test_output(self, capsys, full_result):
        print_header_metadata(full_result, "/tmp/repo")
        out = capsys.readouterr().out
        assert "scc Directory Analysis v2.0" in out
        assert "test-run-display" in out
        assert "/tmp/repo" in out


class TestPrintValidationEvidence:
    def test_output(self, capsys, full_result):
        print_validation_evidence(full_result)
        out = capsys.readouterr().out
        assert "VALIDATION EVIDENCE" in out
        assert "sum(direct.file_count)" in out
        assert "recursive >= direct" in out
        assert "gini" in out


class TestPrintExecutiveSummary:
    def test_output(self, capsys, full_result):
        print_executive_summary(full_result)
        out = capsys.readouterr().out
        assert "EXECUTIVE SUMMARY" in out
        assert "Codebase Size" in out
        assert "Code Quality" in out
        assert "Python" in out


class TestPrintQualityIndicators:
    def test_output(self, capsys, full_result):
        print_quality_indicators(full_result)
        out = capsys.readouterr().out
        assert "QUALITY INDICATORS" in out
        assert "Source" in out
        assert "Test" in out
        assert "Assessment" in out


class TestPrintLanguageAnalysis:
    def test_output(self, capsys, full_result):
        print_language_analysis(full_result)
        out = capsys.readouterr().out
        assert "LANGUAGE ANALYSIS" in out
        assert "Python" in out
        assert "TOTAL" in out

    def test_empty_languages(self, capsys):
        print_language_analysis({"summary": {}})
        out = capsys.readouterr().out
        assert out == ""


class TestPrintPerLanguageDistributions:
    def test_output(self, capsys, full_result):
        print_per_language_distributions(full_result)
        out = capsys.readouterr().out
        assert "PER-LANGUAGE DISTRIBUTION" in out
        # Python has distributions; JavaScript does not
        assert "Python" in out

    def test_empty(self, capsys):
        print_per_language_distributions({"summary": {}})
        out = capsys.readouterr().out
        assert out == ""


class TestPrintInequalityAnalysis:
    def test_output(self, capsys, full_result):
        print_inequality_analysis(full_result)
        out = capsys.readouterr().out
        assert "INEQUALITY ANALYSIS" in out
        assert "Gini" in out
        assert "Theil" in out
        assert "Hoover" in out
        assert "Top 10%" in out

    def test_empty(self, capsys):
        print_inequality_analysis({"summary": {}})
        out = capsys.readouterr().out
        assert out == ""


class TestPrintDistributionStatisticsEnhanced:
    def test_output(self, capsys, full_result):
        print_distribution_statistics_enhanced(full_result)
        out = capsys.readouterr().out
        assert "DISTRIBUTION STATISTICS" in out
        assert "Minimum" in out
        assert "Maximum" in out
        assert "Median" in out
        assert "P90" in out

    def test_empty(self, capsys):
        print_distribution_statistics_enhanced({"summary": {}})
        out = capsys.readouterr().out
        assert out == ""


class TestPrintTopFilesByLoc:
    def test_output(self, capsys, full_result):
        print_top_files_by_loc(full_result, limit=5)
        out = capsys.readouterr().out
        assert "TOP 5 FILES BY LINES OF CODE" in out
        assert "app.py" in out  # highest LOC file

    def test_empty_files(self, capsys):
        print_top_files_by_loc({"files": [], "summary": {}})
        out = capsys.readouterr().out
        assert out == ""


class TestPrintTopFilesByComplexity:
    def test_output(self, capsys, full_result):
        print_top_files_by_complexity(full_result, limit=5)
        out = capsys.readouterr().out
        assert "TOP 5 FILES BY COMPLEXITY" in out

    def test_high_complexity_warning(self, capsys):
        result = {
            "files": [
                _make_file("big.py", "Python", 500, 80, 0.16),
            ],
            "summary": {},
        }
        print_top_files_by_complexity(result, limit=5)
        out = capsys.readouterr().out
        assert "Complexity > 50" in out

    def test_empty_files(self, capsys):
        print_top_files_by_complexity({"files": [], "summary": {}})
        out = capsys.readouterr().out
        assert out == ""


class TestPrintTopFilesByDensity:
    def test_output(self, capsys, full_result):
        print_top_files_by_density(full_result, limit=5)
        out = capsys.readouterr().out
        assert "COMPLEXITY DENSITY" in out

    def test_empty(self, capsys):
        print_top_files_by_density({"files": [], "summary": {}})
        out = capsys.readouterr().out
        assert out == ""


class TestPrintDirectoryTreeEnhanced:
    def test_output(self, capsys, full_result):
        print_directory_tree_enhanced(full_result)
        out = capsys.readouterr().out
        assert "DIRECTORY TREE" in out
        assert "Recursive" in out
        assert "Direct" in out

    def test_empty(self, capsys):
        print_directory_tree_enhanced({"directories": []})
        out = capsys.readouterr().out
        assert out == ""


class TestPrintAnalysisSummary:
    def test_output(self, capsys, full_result):
        print_analysis_summary(full_result)
        out = capsys.readouterr().out
        assert "ANALYSIS SUMMARY" in out
        assert "Key Findings" in out
        assert "Code Concentration" in out
        assert "Language Mix" in out
        assert "Recommendations" in out

    def test_no_concerns(self, capsys):
        """When there are no high-complexity files, no test warnings etc."""
        result = {
            "summary": {
                "total_files": 5,
                "total_loc": 500,
                "total_complexity": 20,
                "total_languages": 1,
                "distributions": {
                    "loc": {
                        "gini": 0.2,
                        "top_10_pct_share": 0.3,
                        "skewness": 0.1,
                    },
                },
                "file_classifications": {
                    "test_file_count": 2,
                    "test_loc": 200,
                    "source_loc": 300,
                    "source_file_count": 3,
                },
                "languages": {
                    "dominant_language": "Python",
                    "dominant_language_pct": 1.0,
                },
                "structure": {
                    "max_depth": 2,
                },
            },
            "directories": [
                _make_directory("src", rec_files=5, rec_code=500),
            ],
            "files": [
                _make_file("a.py", complexity=10),
            ],
        }
        print_analysis_summary(result)
        out = capsys.readouterr().out
        assert "No major concerns" in out


class TestPrintFooter:
    def test_output(self, capsys):
        print_footer("/tmp/output.json", run_time=1.23)
        out = capsys.readouterr().out
        assert "Analysis complete" in out
        assert "/tmp/output.json" in out
        assert "1.23s" in out


# ---------------------------------------------------------------------------
# Tests: strip_ansi
# ---------------------------------------------------------------------------

class TestStripAnsi:
    def test_strips_color_codes(self):
        colored = "\033[1;32mGreen Bold\033[0m"
        assert strip_ansi(colored) == "Green Bold"

    def test_plain_text_unchanged(self):
        assert strip_ansi("hello world") == "hello world"

    def test_empty_string(self):
        assert strip_ansi("") == ""
