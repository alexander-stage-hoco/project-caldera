"""Tests for scripts/checks/directory_analysis.py - DA-1 to DA-12 checks."""
from __future__ import annotations

import pytest
from scripts.checks.directory_analysis import (
    check_directory_stats_complete,
    check_distribution_stats_valid,
    check_structural_metrics_valid,
    check_file_count_matches,
    check_recursive_includes_direct,
    check_inequality_metrics_valid,
    check_file_classification_counts,
    check_per_language_consistency,
    check_cocomo_preset_ordering,
    check_p99_monotonicity,
    check_summary_structure,
    check_file_entry_fields,
    run_directory_analysis_checks,
    DISTRIBUTION_FIELDS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_loc_distribution(**overrides):
    """Build a valid 22-field distribution dict."""
    defaults = {
        "min": 1, "max": 500, "mean": 50.0, "median": 30.0, "stddev": 60.0,
        "p25": 10, "p75": 70, "p90": 120, "p95": 200, "p99": 400,
        "skewness": 1.5, "kurtosis": 3.0, "cv": 1.2, "iqr": 60,
        "gini": 0.45, "theil": 0.3, "hoover": 0.25, "palma": 2.5,
        "top_10_pct_share": 0.4, "top_20_pct_share": 0.6, "bottom_50_pct_share": 0.15,
    }
    defaults.update(overrides)
    return defaults


@pytest.fixture
def valid_analysis_data():
    """Complete valid analysis data for all DA checks."""
    return {
        "directories": [
            {
                "path": "src",
                "depth": 1,
                "is_leaf": False,
                "child_count": 2,
                "direct": {"file_count": 3, "lines_code": 200, "code": 200, "complexity_total": 10},
                "recursive": {
                    "file_count": 10,
                    "lines_code": 1500,
                    "code": 1500,
                    "complexity_total": 50,
                    "loc_distribution": _make_loc_distribution(),
                },
            },
            {
                "path": "src/utils",
                "depth": 2,
                "is_leaf": True,
                "child_count": 0,
                "direct": {"file_count": 5, "lines_code": 800, "code": 800, "complexity_total": 30},
                "recursive": {
                    "file_count": 5,
                    "lines_code": 800,
                    "code": 800,
                    "complexity_total": 30,
                    "loc_distribution": _make_loc_distribution(),
                },
            },
            {
                "path": "tests",
                "depth": 1,
                "is_leaf": True,
                "child_count": 0,
                "direct": {"file_count": 2, "lines_code": 100, "code": 100, "complexity_total": 5},
                "recursive": {
                    "file_count": 2,
                    "lines_code": 100,
                    "code": 100,
                    "complexity_total": 5,
                    "loc_distribution": _make_loc_distribution(),
                },
            },
        ],
        "files": [
            {
                "path": "src/main.py", "filename": "main.py", "directory": "src",
                "language": "Python", "extension": ".py",
                "lines_total": 100, "lines_code": 80, "lines_comment": 10, "lines_blank": 10,
                "bytes": 2500, "complexity": 8, "uloc": 70,
                "comment_ratio": 0.1, "blank_ratio": 0.1, "code_ratio": 0.8,
                "complexity_density": 0.1, "dryness": 0.875, "bytes_per_loc": 31.25,
                "is_minified": False, "is_generated": False, "is_binary": False,
                "classification": "source",
            },
        ] * 10,  # 10 identical file entries
        "summary": {
            "total_files": 10,
            "total_loc": 800,
            "total_directories": 3,
            "total_languages": 2,
            "structure": {
                "max_depth": 2,
                "avg_depth": 1.33,
                "total_directories": 3,
                "leaf_directory_count": 2,
                "avg_files_per_directory": 3.33,
            },
            "ratios": {
                "comment_ratio": 0.1,
                "complexity_density": 0.05,
                "dryness": 0.9,
                "avg_complexity": 5.0,
            },
            "file_classifications": {
                "source_file_count": 8,
                "test_file_count": 2,
                "config_file_count": 0,
                "docs_file_count": 0,
                "build_file_count": 0,
                "ci_file_count": 0,
            },
            "languages": {
                "dominant_language": "Python",
                "dominant_language_pct": 0.8,
                "polyglot_score": 0.5,
            },
            "distributions": {
                "loc": _make_loc_distribution(),
                "complexity": _make_loc_distribution(),
            },
            "by_language": {
                "Python": {"lines_code": 600, "code": 600, "file_count": 7},
                "JavaScript": {"lines_code": 200, "code": 200, "file_count": 3},
            },
            "cocomo": {
                "early_startup": {"effort_person_months": 5, "cost": 50000},
                "growth_startup": {"effort_person_months": 8, "cost": 80000},
                "scale_up": {"effort_person_months": 12, "cost": 120000},
                "sme": {"effort_person_months": 16, "cost": 160000},
                "mid_market": {"effort_person_months": 20, "cost": 200000},
                "large_enterprise": {"effort_person_months": 25, "cost": 250000},
                "regulated": {"effort_person_months": 35, "cost": 350000},
                "open_source": {"effort_person_months": 3, "cost": 0},
            },
        },
    }


# ---------------------------------------------------------------------------
# Tests: DA-1 Directory Stats Complete
# ---------------------------------------------------------------------------

class TestDA1DirectoryStatsComplete:
    def test_all_complete(self, valid_analysis_data):
        result = check_directory_stats_complete(valid_analysis_data)
        assert result.passed is True
        assert result.check_id == "DA-1"

    def test_missing_direct(self, valid_analysis_data):
        del valid_analysis_data["directories"][0]["direct"]
        result = check_directory_stats_complete(valid_analysis_data)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: DA-2 Distribution Stats Valid
# ---------------------------------------------------------------------------

class TestDA2DistributionStatsValid:
    def test_all_valid(self, valid_analysis_data):
        result = check_distribution_stats_valid(valid_analysis_data)
        assert result.passed is True

    def test_missing_field(self, valid_analysis_data):
        del valid_analysis_data["directories"][0]["recursive"]["loc_distribution"]["gini"]
        result = check_distribution_stats_valid(valid_analysis_data)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: DA-3 Structural Metrics Valid
# ---------------------------------------------------------------------------

class TestDA3StructuralMetricsValid:
    def test_all_valid(self, valid_analysis_data):
        result = check_structural_metrics_valid(valid_analysis_data)
        assert result.passed is True

    def test_leaf_with_children(self, valid_analysis_data):
        # Mark a non-leaf as a leaf (inconsistency)
        valid_analysis_data["directories"][0]["is_leaf"] = True
        # child_count is 2, but is_leaf is True -> violation
        result = check_structural_metrics_valid(valid_analysis_data)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: DA-4 File Count Matches
# ---------------------------------------------------------------------------

class TestDA4FileCountMatches:
    def test_counts_match(self, valid_analysis_data):
        result = check_file_count_matches(valid_analysis_data)
        assert result.passed is True

    def test_counts_mismatch(self, valid_analysis_data):
        valid_analysis_data["summary"]["total_files"] = 999
        result = check_file_count_matches(valid_analysis_data)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: DA-5 Recursive Includes Direct
# ---------------------------------------------------------------------------

class TestDA5RecursiveIncludesDirect:
    def test_all_valid(self, valid_analysis_data):
        result = check_recursive_includes_direct(valid_analysis_data)
        assert result.passed is True

    def test_violation(self, valid_analysis_data):
        # Make recursive < direct (invalid)
        valid_analysis_data["directories"][0]["recursive"]["file_count"] = 1
        valid_analysis_data["directories"][0]["direct"]["file_count"] = 5
        result = check_recursive_includes_direct(valid_analysis_data)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: DA-6 Inequality Metrics Valid
# ---------------------------------------------------------------------------

class TestDA6InequalityMetricsValid:
    def test_all_valid(self, valid_analysis_data):
        result = check_inequality_metrics_valid(valid_analysis_data)
        assert result.passed is True

    def test_gini_out_of_range(self, valid_analysis_data):
        valid_analysis_data["directories"][0]["recursive"]["loc_distribution"]["gini"] = 1.5
        result = check_inequality_metrics_valid(valid_analysis_data)
        assert result.passed is False

    def test_negative_theil(self, valid_analysis_data):
        valid_analysis_data["directories"][0]["recursive"]["loc_distribution"]["theil"] = -0.5
        result = check_inequality_metrics_valid(valid_analysis_data)
        assert result.passed is False

    def test_hoover_out_of_range(self, valid_analysis_data):
        valid_analysis_data["directories"][0]["recursive"]["loc_distribution"]["hoover"] = 2.0
        result = check_inequality_metrics_valid(valid_analysis_data)
        assert result.passed is False

    def test_share_out_of_range(self, valid_analysis_data):
        valid_analysis_data["directories"][0]["recursive"]["loc_distribution"]["top_10_pct_share"] = 1.5
        result = check_inequality_metrics_valid(valid_analysis_data)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: DA-7 File Classification Counts
# ---------------------------------------------------------------------------

class TestDA7FileClassificationCounts:
    def test_counts_match(self, valid_analysis_data):
        result = check_file_classification_counts(valid_analysis_data)
        assert result.passed is True

    def test_counts_mismatch(self, valid_analysis_data):
        valid_analysis_data["summary"]["file_classifications"]["source_file_count"] = 99
        result = check_file_classification_counts(valid_analysis_data)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: DA-8 Per-Language Consistency
# ---------------------------------------------------------------------------

class TestDA8PerLanguageConsistency:
    def test_consistent(self, valid_analysis_data):
        result = check_per_language_consistency(valid_analysis_data)
        assert result.passed is True

    def test_inconsistent(self, valid_analysis_data):
        valid_analysis_data["summary"]["total_loc"] = 9999
        result = check_per_language_consistency(valid_analysis_data)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: DA-9 COCOMO Preset Ordering
# ---------------------------------------------------------------------------

class TestDA9CocomoPresetOrdering:
    def test_valid_ordering(self, valid_analysis_data):
        result = check_cocomo_preset_ordering(valid_analysis_data)
        assert result.passed is True

    def test_ordering_violation(self, valid_analysis_data):
        # Make startup cost higher than enterprise
        valid_analysis_data["summary"]["cocomo"]["early_startup"]["effort_person_months"] = 999
        result = check_cocomo_preset_ordering(valid_analysis_data)
        assert result.passed is False

    def test_nonzero_open_source_cost(self, valid_analysis_data):
        valid_analysis_data["summary"]["cocomo"]["open_source"]["cost"] = 50000
        result = check_cocomo_preset_ordering(valid_analysis_data)
        assert result.passed is False

    def test_missing_preset(self, valid_analysis_data):
        del valid_analysis_data["summary"]["cocomo"]["regulated"]
        result = check_cocomo_preset_ordering(valid_analysis_data)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: DA-10 P99 Monotonicity
# ---------------------------------------------------------------------------

class TestDA10P99Monotonicity:
    def test_monotonic(self, valid_analysis_data):
        result = check_p99_monotonicity(valid_analysis_data)
        assert result.passed is True

    def test_non_monotonic(self, valid_analysis_data):
        valid_analysis_data["directories"][0]["recursive"]["loc_distribution"]["p99"] = 1
        result = check_p99_monotonicity(valid_analysis_data)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: DA-11 Summary Structure Complete
# ---------------------------------------------------------------------------

class TestDA11SummaryStructure:
    def test_all_sections_present(self, valid_analysis_data):
        result = check_summary_structure(valid_analysis_data)
        assert result.passed is True

    def test_missing_section(self, valid_analysis_data):
        del valid_analysis_data["summary"]["cocomo"]
        result = check_summary_structure(valid_analysis_data)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: DA-12 File Entry Fields
# ---------------------------------------------------------------------------

class TestDA12FileEntryFields:
    def test_all_fields_present(self, valid_analysis_data):
        result = check_file_entry_fields(valid_analysis_data)
        assert result.passed is True

    def test_missing_field(self, valid_analysis_data):
        del valid_analysis_data["files"][0]["classification"]
        result = check_file_entry_fields(valid_analysis_data)
        assert result.passed is False


# ---------------------------------------------------------------------------
# Tests: run_directory_analysis_checks (runner)
# ---------------------------------------------------------------------------

class TestRunDirectoryAnalysisChecks:
    def test_returns_12_checks(self, valid_analysis_data):
        results = run_directory_analysis_checks(valid_analysis_data)
        assert len(results) == 12
        assert all(r.check_id.startswith("DA-") for r in results)
