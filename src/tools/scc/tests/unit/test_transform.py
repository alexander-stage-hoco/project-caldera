"""Tests for scripts/transform.py - evidence schema transformation."""
from __future__ import annotations

import pytest
from scripts.transform import (
    transform_to_evidence,
    transform_per_file_output,
    transform_directory_evidence,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def single_language_output():
    """Minimal scc JSON output with one language."""
    return [
        {
            "Name": "Python",
            "Count": 5,
            "Lines": 200,
            "Code": 150,
            "Comment": 30,
            "Blank": 20,
            "Bytes": 5000,
            "Complexity": 12,
            "WeightedComplexity": 18,
        }
    ]


@pytest.fixture
def multi_language_output():
    """scc JSON output with multiple languages."""
    return [
        {
            "Name": "Python",
            "Count": 5,
            "Lines": 200,
            "Code": 150,
            "Comment": 30,
            "Blank": 20,
            "Bytes": 5000,
            "Complexity": 12,
            "WeightedComplexity": 18,
        },
        {
            "Name": "JavaScript",
            "Count": 3,
            "Lines": 100,
            "Code": 80,
            "Comment": 10,
            "Blank": 10,
            "Bytes": 2000,
            "Complexity": 5,
            "WeightedComplexity": 8,
        },
        {
            "Name": "Markdown",
            "Count": 0,
            "Lines": 0,
            "Code": 0,
            "Comment": 0,
            "Blank": 0,
            "Bytes": 0,
            "Complexity": 0,
            "WeightedComplexity": 0,
        },
    ]


@pytest.fixture
def per_file_output():
    """scc --by-file JSON output."""
    return [
        {
            "Name": "Python",
            "Files": [
                {
                    "Location": "src/main.py",
                    "Filename": "main.py",
                    "Lines": 100,
                    "Code": 80,
                    "Comment": 10,
                    "Blank": 10,
                    "Bytes": 2500,
                    "Complexity": 8,
                    "Uloc": 70,
                    "Minified": False,
                    "Generated": False,
                    "Binary": False,
                },
                {
                    "Location": "src/utils.py",
                    "Filename": "utils.py",
                    "Lines": 50,
                    "Code": 40,
                    "Comment": 5,
                    "Blank": 5,
                    "Bytes": 1200,
                    "Complexity": 3,
                    "Uloc": 35,
                    "Minified": False,
                    "Generated": False,
                    "Binary": False,
                },
            ],
        },
        {
            "Name": "JavaScript",
            "Files": [
                {
                    "Location": "lib/app.js",
                    "Filename": "app.js",
                    "Lines": 0,
                    "Code": 0,
                    "Comment": 0,
                    "Blank": 0,
                    "Bytes": 500,
                    "Complexity": 0,
                    "Uloc": 0,
                    "Minified": True,
                    "Generated": True,
                    "Binary": False,
                },
            ],
        },
    ]


# ---------------------------------------------------------------------------
# Tests: transform_to_evidence
# ---------------------------------------------------------------------------

class TestTransformToEvidence:
    """Tests for transform_to_evidence function."""

    def test_basic_structure(self, single_language_output):
        result = transform_to_evidence(single_language_output, run_id="test-run-001")

        assert result["schema_version"] == "1.0"
        assert result["run_id"] == "test-run-001"
        assert result["evidence_type"] == "size_metrics"
        assert result["source"] == "scc"
        assert "created_at" in result
        assert "items" in result
        assert "metrics" in result
        assert "summary" in result

    def test_auto_generated_run_id(self, single_language_output):
        result = transform_to_evidence(single_language_output)
        assert result["run_id"].startswith("poc-scc-")

    def test_skips_zero_count_entries(self, multi_language_output):
        result = transform_to_evidence(multi_language_output, run_id="test")
        # Markdown has Count=0, should be skipped
        assert len(result["items"]) == 2
        languages = [item["data"]["language"] for item in result["items"]]
        assert "Markdown" not in languages

    def test_summary_totals_are_correct(self, multi_language_output):
        result = transform_to_evidence(multi_language_output, run_id="test")
        summary = result["summary"]
        assert summary["total_files"] == 8  # 5 + 3 + 0
        assert summary["total_loc"] == 230  # 150 + 80
        assert summary["total_lines"] == 300  # 200 + 100
        assert summary["total_comments"] == 40  # 30 + 10
        assert summary["total_blanks"] == 30  # 20 + 10
        assert summary["total_bytes"] == 7000  # 5000 + 2000
        assert summary["total_complexity"] == 17  # 12 + 5
        assert summary["languages"] == 2  # Python and JavaScript (Markdown has 0 count)

    def test_comment_ratio_calculated(self, single_language_output):
        result = transform_to_evidence(single_language_output, run_id="test")
        expected_ratio = round(30 / 200, 4)
        assert result["summary"]["comment_ratio"] == expected_ratio

    def test_complexity_per_loc(self, single_language_output):
        result = transform_to_evidence(single_language_output, run_id="test")
        expected = round(12 / 150, 4)
        assert result["summary"]["complexity_per_loc"] == expected

    def test_zero_lines_yields_zero_ratios(self):
        empty_output = [{"Name": "Empty", "Count": 0, "Lines": 0, "Code": 0,
                         "Comment": 0, "Blank": 0, "Bytes": 0, "Complexity": 0}]
        result = transform_to_evidence(empty_output, run_id="test")
        assert result["summary"]["comment_ratio"] == 0
        assert result["summary"]["complexity_per_loc"] == 0

    def test_metrics_alias_matches_summary(self, single_language_output):
        result = transform_to_evidence(single_language_output, run_id="test")
        assert result["metrics"]["total_files"] == result["summary"]["total_files"]
        assert result["metrics"]["total_loc"] == result["summary"]["total_loc"]
        assert result["metrics"]["total_complexity"] == result["summary"]["total_complexity"]

    def test_evidence_item_structure(self, single_language_output):
        result = transform_to_evidence(single_language_output, run_id="test")
        item = result["items"][0]
        assert "evidence_id" in item
        assert item["type"] == "size_loc"
        assert item["source"] == "scc"
        assert "provenance" in item
        assert item["data"]["language"] == "Python"
        assert item["data"]["files"] == 5
        assert item["data"]["lines_total"] == 200
        assert item["data"]["lines_code"] == 150


# ---------------------------------------------------------------------------
# Tests: transform_per_file_output
# ---------------------------------------------------------------------------

class TestTransformPerFileOutput:
    """Tests for transform_per_file_output function."""

    def test_basic_structure(self, per_file_output):
        result = transform_per_file_output(per_file_output, run_id="pf-test")
        assert result["schema_version"] == "2.0"
        assert result["run_id"] == "pf-test"
        assert result["evidence_type"] == "size_metrics_full"
        assert "files" in result
        assert "languages" in result
        assert "summary" in result
        assert "provenance" in result

    def test_file_entries_count(self, per_file_output):
        result = transform_per_file_output(per_file_output, run_id="pf-test")
        # 2 Python + 1 JavaScript
        assert len(result["files"]) == 3

    def test_derived_metrics_comment_ratio(self, per_file_output):
        result = transform_per_file_output(per_file_output, run_id="pf-test")
        main_py = [f for f in result["files"] if f["path"] == "src/main.py"][0]
        assert main_py["comment_ratio"] == round(10 / 100, 4)

    def test_derived_metrics_complexity_density(self, per_file_output):
        result = transform_per_file_output(per_file_output, run_id="pf-test")
        main_py = [f for f in result["files"] if f["path"] == "src/main.py"][0]
        assert main_py["complexity_density"] == round(8 / 80, 4)

    def test_derived_metrics_dryness(self, per_file_output):
        result = transform_per_file_output(per_file_output, run_id="pf-test")
        main_py = [f for f in result["files"] if f["path"] == "src/main.py"][0]
        assert main_py["dryness"] == round(70 / 80, 4)

    def test_zero_code_file_has_zero_density(self, per_file_output):
        result = transform_per_file_output(per_file_output, run_id="pf-test")
        app_js = [f for f in result["files"] if f["path"] == "lib/app.js"][0]
        assert app_js["complexity_density"] == 0
        assert app_js["dryness"] == 0

    def test_minified_and_generated_flags(self, per_file_output):
        result = transform_per_file_output(per_file_output, run_id="pf-test")
        assert result["summary"]["minified_count"] == 1
        assert result["summary"]["generated_count"] == 1

    def test_language_summaries(self, per_file_output):
        result = transform_per_file_output(per_file_output, run_id="pf-test")
        py_summary = [l for l in result["languages"] if l["language"] == "Python"][0]
        assert py_summary["file_count"] == 2
        assert py_summary["lines_code"] == 120  # 80 + 40
        assert py_summary["complexity"] == 11  # 8 + 3

    def test_summary_totals(self, per_file_output):
        result = transform_per_file_output(per_file_output, run_id="pf-test")
        s = result["summary"]
        assert s["total_files"] == 3
        assert s["total_loc"] == 120  # 80 + 40 + 0
        assert s["total_lines"] == 150  # 100 + 50 + 0
        assert s["languages_count"] == 2

    def test_empty_files_list_skips_language(self):
        data = [{"Name": "Go", "Files": []}]
        result = transform_per_file_output(data, run_id="test")
        assert len(result["files"]) == 0
        assert len(result["languages"]) == 0

    def test_auto_generated_run_id(self, per_file_output):
        result = transform_per_file_output(per_file_output)
        assert result["run_id"].startswith("poc-scc-full-")


# ---------------------------------------------------------------------------
# Tests: transform_directory_evidence
# ---------------------------------------------------------------------------

class TestTransformDirectoryEvidence:
    """Tests for transform_directory_evidence function."""

    @pytest.fixture
    def dir_analysis(self):
        return {
            "directories": [
                {
                    "path": "src",
                    "depth": 1,
                    "is_hotspot": True,
                    "hotspot_score": 0.85,
                    "hotspot_rank": 1,
                    "direct": {"file_count": 3, "lines_code": 200},
                    "recursive": {
                        "file_count": 10,
                        "lines_code": 1500,
                        "complexity_total": 50,
                    },
                },
                {
                    "path": "tests",
                    "depth": 1,
                    "is_hotspot": False,
                    "hotspot_score": 0.2,
                    "hotspot_rank": 5,
                    "direct": {"file_count": 5, "lines_code": 300},
                    "recursive": {
                        "file_count": 5,
                        "lines_code": 300,
                        "complexity_total": 10,
                    },
                },
            ],
            "summary": {"total_files": 15, "hotspot_directories": 1},
            "cocomo_params": {"a": 3.0, "b": 1.12},
        }

    def test_basic_structure(self, dir_analysis):
        result = transform_directory_evidence(dir_analysis, run_id="dir-test")
        assert result["schema_version"] == "1.0"
        assert result["run_id"] == "dir-test"
        assert result["evidence_type"] == "directory_analysis"
        assert "items" in result
        assert "summary" in result
        assert "cocomo_params" in result

    def test_hotspot_evidence_items(self, dir_analysis):
        result = transform_directory_evidence(dir_analysis, run_id="dir-test")
        hotspot_items = [i for i in result["items"] if i["type"] == "directory_hotspot"]
        assert len(hotspot_items) == 1
        assert hotspot_items[0]["data"]["path"] == "src"

    def test_directory_stats_items(self, dir_analysis):
        result = transform_directory_evidence(dir_analysis, run_id="dir-test")
        stat_items = [i for i in result["items"] if i["type"] == "directory_stats"]
        assert len(stat_items) == 2

    def test_total_items_count(self, dir_analysis):
        result = transform_directory_evidence(dir_analysis, run_id="dir-test")
        # 1 hotspot + 2 directory_stats = 3
        assert len(result["items"]) == 3

    def test_auto_generated_run_id(self, dir_analysis):
        result = transform_directory_evidence(dir_analysis)
        assert result["run_id"].startswith("poc-scc-dirs-")
