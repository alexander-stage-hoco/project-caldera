"""Tests for uncovered helper functions in checks/__init__.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.checks import (
    EvaluationReport,
    CheckResult,
    CheckCategory,
    get_nested,
    in_range,
    get_issues_rollups,
    get_components,
    get_quality_gate,
    load_analysis,
    load_ground_truth,
)


class TestEvaluationReportToDict:
    """Tests for EvaluationReport serialization (uncovered to_dict)."""

    def test_to_dict_with_categories(self) -> None:
        checks = [
            CheckResult(
                check_id="SQ-AC-1", name="Test",
                category=CheckCategory.ACCURACY, passed=True,
                score=1.0, message="OK",
            ),
            CheckResult(
                check_id="SQ-CV-1", name="Test 2",
                category=CheckCategory.COVERAGE, passed=False,
                score=0.3, message="Fail",
            ),
        ]
        report = EvaluationReport(
            timestamp="2025-01-01T00:00:00Z",
            analysis_path="/tmp/test.json",
            ground_truth_dir="/tmp/gt",
            checks=checks,
        )
        d = report.to_dict()
        assert d["summary"]["passed"] == 1
        assert d["summary"]["failed"] == 1
        assert d["summary"]["total"] == 2
        assert "score_by_category" in d["summary"]
        assert "passed_by_category" in d["summary"]
        assert "accuracy" in d["summary"]["score_by_category"]
        assert "coverage" in d["summary"]["score_by_category"]

    def test_to_dict_empty(self) -> None:
        report = EvaluationReport(
            timestamp="t", analysis_path="a",
            ground_truth_dir="g", checks=[],
        )
        d = report.to_dict()
        assert d["summary"]["score"] == 0.0


class TestGetNested:
    """Tests for dot-notation nested access."""

    def test_simple_key(self) -> None:
        assert get_nested({"a": 1}, "a") == 1

    def test_nested_key(self) -> None:
        assert get_nested({"a": {"b": 2}}, "a.b") == 2

    def test_missing_returns_default(self) -> None:
        assert get_nested({"a": 1}, "b", "default") == "default"

    def test_results_wrapper_fallback(self) -> None:
        data = {"results": {"issues": {"total": 5}}}
        assert get_nested(data, "issues.total") == 5

    def test_non_dict_intermediate(self) -> None:
        assert get_nested({"a": "string"}, "a.b", None) is None


class TestInRange:
    """Tests for range checking."""

    def test_in_range(self) -> None:
        assert in_range(5, 1, 10) is True

    def test_at_min(self) -> None:
        assert in_range(1, 1, 10) is True

    def test_below_min(self) -> None:
        assert in_range(0, 1, 10) is False


class TestDataExtractors:
    """Tests for get_issues_rollups, get_components, get_quality_gate."""

    def test_get_issues_rollups_with_results(self) -> None:
        data = {"results": {"issues": {"rollups": {"by_type": {"BUG": 3}}}}}
        rollups = get_issues_rollups(data)
        assert rollups["by_type"]["BUG"] == 3

    def test_get_components_flat(self) -> None:
        data = {"components": {"count": 5}}
        assert get_components(data)["count"] == 5

    def test_get_quality_gate_flat(self) -> None:
        data = {"quality_gate": {"status": "OK"}}
        assert get_quality_gate(data)["status"] == "OK"


class TestLoadAnalysis:
    """Tests for analysis loading with format detection."""

    def test_caldera_envelope_format(self, tmp_path: Path) -> None:
        data = {
            "metadata": {"tool_name": "sonarqube"},
            "data": {"issues": {"total": 5}},
        }
        p = tmp_path / "analysis.json"
        p.write_text(json.dumps(data))
        result = load_analysis(p)
        assert result["issues"]["total"] == 5

    def test_plain_format(self, tmp_path: Path) -> None:
        data = {"issues": {"total": 3}}
        p = tmp_path / "analysis.json"
        p.write_text(json.dumps(data))
        result = load_analysis(p)
        assert result["issues"]["total"] == 3


class TestLoadGroundTruth:
    """Tests for ground truth loading."""

    def test_loads_matching_file(self, tmp_path: Path) -> None:
        gt = {"expected": True}
        (tmp_path / "my-repo.json").write_text(json.dumps(gt))
        result = load_ground_truth(tmp_path, "my-repo")
        assert result["expected"] is True

    def test_returns_none_for_missing(self, tmp_path: Path) -> None:
        assert load_ground_truth(tmp_path, "nonexistent") is None
