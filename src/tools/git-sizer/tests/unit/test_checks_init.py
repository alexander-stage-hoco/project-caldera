"""Unit tests for scripts.checks __init__ module (EvaluationReport, loaders, utilities)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Ensure src is on the path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from scripts.checks import (
    CheckCategory,
    CheckResult,
    EvaluationReport,
    get_repo_by_name,
    get_repo_from_results,
    load_all_ground_truth,
    load_all_results,
    load_analysis,
    load_ground_truth,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_check(check_id: str, category: CheckCategory, passed: bool, score: float) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        name=f"Test {check_id}",
        category=category,
        passed=passed,
        score=score,
        message="ok" if passed else "fail",
    )


# ---------------------------------------------------------------------------
# CheckResult
# ---------------------------------------------------------------------------

class TestCheckResult:
    def test_to_dict_includes_all_fields(self):
        cr = CheckResult(
            check_id="AC-1",
            name="Blob detection",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=0.95,
            message="Detected",
            evidence={"max_blob": 123},
        )
        d = cr.to_dict()
        assert d["check_id"] == "AC-1"
        assert d["category"] == "accuracy"
        assert d["passed"] is True
        assert d["score"] == 0.95
        assert d["evidence"] == {"max_blob": 123}

    def test_to_dict_default_evidence_is_empty(self):
        cr = CheckResult(
            check_id="X-1", name="X", category=CheckCategory.COVERAGE,
            passed=False, score=0.0, message="none",
        )
        assert cr.to_dict()["evidence"] == {}


# ---------------------------------------------------------------------------
# EvaluationReport properties
# ---------------------------------------------------------------------------

class TestEvaluationReport:
    def _make_report(self, checks: list[CheckResult]) -> EvaluationReport:
        return EvaluationReport(
            timestamp="2026-01-30T00:00:00",
            analysis_path="/tmp/a",
            ground_truth_dir="/tmp/gt",
            checks=checks,
        )

    def test_passed_failed_total(self):
        checks = [
            _make_check("AC-1", CheckCategory.ACCURACY, True, 1.0),
            _make_check("AC-2", CheckCategory.ACCURACY, False, 0.3),
            _make_check("CV-1", CheckCategory.COVERAGE, True, 0.9),
        ]
        report = self._make_report(checks)
        assert report.passed == 2
        assert report.failed == 1
        assert report.total == 3

    def test_score_empty_checks(self):
        report = self._make_report([])
        assert report.score == 0.0

    def test_score_average(self):
        checks = [
            _make_check("AC-1", CheckCategory.ACCURACY, True, 1.0),
            _make_check("AC-2", CheckCategory.ACCURACY, True, 0.5),
        ]
        report = self._make_report(checks)
        assert report.score == pytest.approx(0.75)

    def test_score_by_category(self):
        checks = [
            _make_check("AC-1", CheckCategory.ACCURACY, True, 1.0),
            _make_check("AC-2", CheckCategory.ACCURACY, True, 0.5),
            _make_check("CV-1", CheckCategory.COVERAGE, True, 0.8),
        ]
        report = self._make_report(checks)
        by_cat = report.score_by_category
        assert by_cat["accuracy"] == pytest.approx(0.75)
        assert by_cat["coverage"] == pytest.approx(0.8)

    def test_passed_by_category(self):
        checks = [
            _make_check("AC-1", CheckCategory.ACCURACY, True, 1.0),
            _make_check("AC-2", CheckCategory.ACCURACY, False, 0.0),
            _make_check("CV-1", CheckCategory.COVERAGE, True, 0.8),
        ]
        report = self._make_report(checks)
        by_cat = report.passed_by_category
        assert by_cat["accuracy"] == (1, 2)
        assert by_cat["coverage"] == (1, 1)

    # ---- to_dict / decision mapping ----

    def test_to_dict_decision_strong_pass(self):
        """Score >= 0.8 => normalized >= 4.0 => STRONG_PASS."""
        checks = [_make_check("AC-1", CheckCategory.ACCURACY, True, 0.85)]
        d = self._make_report(checks).to_dict()
        assert d["decision"] == "STRONG_PASS"

    def test_to_dict_decision_pass(self):
        """Score 0.7-0.79 => normalized 3.5-3.99 => PASS."""
        checks = [_make_check("AC-1", CheckCategory.ACCURACY, True, 0.75)]
        d = self._make_report(checks).to_dict()
        assert d["decision"] == "PASS"

    def test_to_dict_decision_weak_pass(self):
        """Score 0.6-0.69 => normalized 3.0-3.49 => WEAK_PASS."""
        checks = [_make_check("AC-1", CheckCategory.ACCURACY, True, 0.65)]
        d = self._make_report(checks).to_dict()
        assert d["decision"] == "WEAK_PASS"

    def test_to_dict_decision_fail(self):
        """Score < 0.6 => normalized < 3.0 => FAIL."""
        checks = [_make_check("AC-1", CheckCategory.ACCURACY, False, 0.4)]
        d = self._make_report(checks).to_dict()
        assert d["decision"] == "FAIL"

    def test_to_dict_has_all_keys(self):
        checks = [_make_check("AC-1", CheckCategory.ACCURACY, True, 0.9)]
        d = self._make_report(checks).to_dict()
        assert "timestamp" in d
        assert "analysis_path" in d
        assert "summary" in d
        assert "checks" in d
        assert d["summary"]["total"] == 1


# ---------------------------------------------------------------------------
# File-based loaders
# ---------------------------------------------------------------------------

class TestLoadAnalysis:
    def test_load_analysis(self, tmp_path: Path):
        data = {"repositories": []}
        path = tmp_path / "analysis.json"
        path.write_text(json.dumps(data))
        loaded = load_analysis(path)
        assert loaded == data


class TestLoadGroundTruth:
    def test_load_existing(self, tmp_path: Path):
        gt_data = {"expected": True}
        (tmp_path / "my-repo.json").write_text(json.dumps(gt_data))
        result = load_ground_truth(tmp_path, "my-repo")
        assert result == gt_data

    def test_load_missing_returns_none(self, tmp_path: Path):
        result = load_ground_truth(tmp_path, "nonexistent")
        assert result is None


class TestLoadAllGroundTruth:
    def test_loads_multiple(self, tmp_path: Path):
        for name in ("alpha", "beta"):
            (tmp_path / f"{name}.json").write_text(json.dumps({"repo": name}))
        result = load_all_ground_truth(tmp_path)
        assert "alpha" in result
        assert "beta" in result
        assert result["alpha"]["repo"] == "alpha"

    def test_empty_dir(self, tmp_path: Path):
        result = load_all_ground_truth(tmp_path)
        assert result == {}


class TestGetRepoFromResults:
    def test_caldera_envelope_format(self, tmp_path: Path):
        repo_dir = tmp_path / "my-repo"
        repo_dir.mkdir()
        envelope = {
            "metadata": {"tool_name": "git-sizer"},
            "data": {"metrics": {"commit_count": 42}},
        }
        (repo_dir / "output.json").write_text(json.dumps(envelope))
        result = get_repo_from_results(tmp_path, "my-repo")
        assert result is not None
        assert result["metrics"]["commit_count"] == 42
        assert result["repository"] == "my-repo"

    def test_missing_repo_returns_none(self, tmp_path: Path):
        result = get_repo_from_results(tmp_path, "nonexistent")
        assert result is None

    def test_non_envelope_format(self, tmp_path: Path):
        repo_dir = tmp_path / "plain"
        repo_dir.mkdir()
        data = {"commit_count": 10}
        (repo_dir / "output.json").write_text(json.dumps(data))
        result = get_repo_from_results(tmp_path, "plain")
        assert result == data


class TestLoadAllResults:
    def test_loads_root_and_subdirs(self, tmp_path: Path):
        # Root output.json
        root_envelope = {
            "metadata": {"repo_name": "root-repo"},
            "data": {"metrics": {}},
        }
        (tmp_path / "output.json").write_text(json.dumps(root_envelope))

        # Sub-directory
        sub = tmp_path / "sub-repo"
        sub.mkdir()
        sub_envelope = {
            "metadata": {},
            "data": {"metrics": {"commit_count": 5}},
        }
        (sub / "output.json").write_text(json.dumps(sub_envelope))

        result = load_all_results(tmp_path)
        assert result["summary"]["total_repositories"] == 2
        repos = result["repositories"]
        names = [r.get("repository") for r in repos]
        assert "root-repo" in names
        assert "sub-repo" in names

    def test_empty_dir_returns_empty(self, tmp_path: Path):
        result = load_all_results(tmp_path)
        assert result["repositories"] == []
        assert result["summary"]["total_repositories"] == 0


class TestGetRepoByName:
    def test_finds_by_repository_field(self):
        analysis = {"repositories": [{"repository": "alpha", "v": 1}, {"repository": "beta", "v": 2}]}
        assert get_repo_by_name(analysis, "beta")["v"] == 2

    def test_finds_by_repo_name_field(self):
        analysis = {"repositories": [{"repo_name": "gamma", "v": 3}]}
        assert get_repo_by_name(analysis, "gamma")["v"] == 3

    def test_returns_none_when_not_found(self):
        analysis = {"repositories": [{"repository": "alpha"}]}
        assert get_repo_by_name(analysis, "missing") is None

    def test_empty_repositories(self):
        assert get_repo_by_name({"repositories": []}, "x") is None
        assert get_repo_by_name({}, "x") is None
