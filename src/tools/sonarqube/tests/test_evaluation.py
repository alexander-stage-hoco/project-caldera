"""Tests for the evaluation framework."""

import json
from pathlib import Path

import pytest

from scripts.checks import (
    CheckCategory,
    CheckResult,
    EvaluationReport,
    get_nested,
    in_range,
    load_analysis,
)
from scripts.checks.accuracy import (
    check_issue_count,
    check_bug_count,
    check_vulnerability_count,
    check_smell_count,
    check_quality_gate_status,
    run_accuracy_checks,
)
from scripts.checks.coverage import (
    check_metric_presence,
    check_rule_coverage,
    check_file_coverage,
    check_language_coverage,
    run_coverage_checks,
)
from scripts.checks.completeness import (
    check_component_tree,
    check_issue_locations,
    check_rules_hydrated,
    check_duplications_present,
    check_quality_gate_conditions,
    check_derived_insights,
    run_completeness_checks,
)
from scripts.evaluate import run_all_checks


class TestCheckUtilities:
    """Tests for check utility functions."""

    def test_in_range_true(self):
        """Test in_range returns True for values in range."""
        assert in_range(5, 1, 10)
        assert in_range(1, 1, 10)  # Inclusive start
        assert in_range(10, 1, 10)  # Inclusive end

    def test_in_range_false(self):
        """Test in_range returns False for values out of range."""
        assert not in_range(0, 1, 10)
        assert not in_range(11, 1, 10)

    def test_get_nested_simple(self):
        """Test get_nested with simple path."""
        data = {"a": {"b": {"c": "value"}}}
        assert get_nested(data, "a.b.c") == "value"

    def test_get_nested_missing(self):
        """Test get_nested returns default for missing path."""
        data = {"a": {"b": {}}}
        assert get_nested(data, "a.b.c", "default") == "default"

    def test_get_nested_default_none(self):
        """Test get_nested default is None."""
        data = {}
        assert get_nested(data, "missing") is None


class TestCheckResult:
    """Tests for CheckResult dataclass."""

    def test_to_dict(self):
        """Test CheckResult.to_dict conversion."""
        result = CheckResult(
            check_id="TEST-1",
            name="Test Check",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=1.0,
            message="Test passed",
            evidence={"expected": 10, "actual": 10},
        )

        d = result.to_dict()

        assert d["check_id"] == "TEST-1"
        assert d["name"] == "Test Check"
        assert d["category"] == "accuracy"
        assert d["passed"] is True
        assert d["score"] == 1.0
        assert d["message"] == "Test passed"
        assert d["evidence"]["expected"] == 10
        assert d["evidence"]["actual"] == 10

    def test_to_dict_empty_evidence(self):
        """Test to_dict with empty evidence."""
        result = CheckResult(
            check_id="TEST-1",
            name="Test",
            category=CheckCategory.ACCURACY,
            passed=True,
            score=1.0,
            message="OK",
        )

        d = result.to_dict()

        assert d["evidence"] == {}


class TestEvaluationReport:
    """Tests for EvaluationReport aggregation."""

    def test_empty_report(self):
        """Test empty evaluation report."""
        report = EvaluationReport(
            timestamp="2024-01-01T00:00:00Z",
            analysis_path="test.json",
            ground_truth_dir="",
            checks=[],
        )

        assert report.total == 0
        assert report.passed == 0
        assert report.failed == 0
        assert report.score == 0.0

    def test_report_with_checks(self):
        """Test report with mixed results."""
        checks = [
            CheckResult(
                check_id="A-1", name="A", category=CheckCategory.ACCURACY,
                passed=True, score=1.0, message="OK"
            ),
            CheckResult(
                check_id="A-2", name="B", category=CheckCategory.ACCURACY,
                passed=True, score=1.0, message="OK"
            ),
            CheckResult(
                check_id="A-3", name="C", category=CheckCategory.ACCURACY,
                passed=False, score=0.0, message="Failed"
            ),
        ]
        report = EvaluationReport(
            timestamp="2024-01-01T00:00:00Z",
            analysis_path="test.json",
            ground_truth_dir="",
            checks=checks,
        )

        assert report.total == 3
        assert report.passed == 2
        assert report.failed == 1
        assert report.score == pytest.approx(2.0 / 3.0, rel=0.01)

    def test_score_by_category(self):
        """Test score breakdown by category."""
        checks = [
            CheckResult(
                check_id="A-1", name="A", category=CheckCategory.ACCURACY,
                passed=True, score=1.0, message="OK"
            ),
            CheckResult(
                check_id="C-1", name="C", category=CheckCategory.COVERAGE,
                passed=False, score=0.0, message="Failed"
            ),
        ]
        report = EvaluationReport(
            timestamp="2024-01-01T00:00:00Z",
            analysis_path="test.json",
            ground_truth_dir="",
            checks=checks,
        )

        scores = report.score_by_category
        assert scores["accuracy"] == 1.0
        assert scores["coverage"] == 0.0

    def test_passed_by_category(self):
        """Test passed/total breakdown by category."""
        checks = [
            CheckResult(
                check_id="A-1", name="A", category=CheckCategory.ACCURACY,
                passed=True, score=1.0, message="OK"
            ),
            CheckResult(
                check_id="A-2", name="B", category=CheckCategory.ACCURACY,
                passed=False, score=0.0, message="Failed"
            ),
        ]
        report = EvaluationReport(
            timestamp="2024-01-01T00:00:00Z",
            analysis_path="test.json",
            ground_truth_dir="",
            checks=checks,
        )

        by_cat = report.passed_by_category
        assert by_cat["accuracy"] == (1, 2)

    def test_to_dict(self):
        """Test to_dict conversion."""
        checks = [
            CheckResult(
                check_id="A-1", name="A", category=CheckCategory.ACCURACY,
                passed=True, score=1.0, message="OK"
            ),
        ]
        report = EvaluationReport(
            timestamp="2024-01-01T00:00:00Z",
            analysis_path="test.json",
            ground_truth_dir="gt",
            checks=checks,
        )

        d = report.to_dict()

        assert d["analysis_path"] == "test.json"
        assert d["ground_truth_dir"] == "gt"
        assert "accuracy" in d["summary"]["score_by_category"]
        assert isinstance(d["summary"]["score"], float)


class TestAccuracyChecks:
    """Tests for accuracy checks (SQ-AC-*)."""

    def test_check_issue_count_pass(self, sample_sonarqube_export, sample_ground_truth):
        """Test issue count check passes within range."""
        result = check_issue_count(sample_sonarqube_export, sample_ground_truth)

        assert result.check_id == "SQ-AC-1"
        assert result.passed is True

    def test_check_issue_count_fail(self, sample_sonarqube_export, sample_ground_truth):
        """Test issue count check fails outside range."""
        # Modify ground truth to have impossible range
        sample_ground_truth["expected_issues"] = {"min": 1000, "max": 2000}

        result = check_issue_count(sample_sonarqube_export, sample_ground_truth)

        assert result.passed is False

    def test_check_issue_count_skip_no_ground_truth(self, sample_sonarqube_export):
        """Test issue count check skips without ground truth."""
        result = check_issue_count(sample_sonarqube_export, None)

        # Without ground truth, returns passed=True with 0.5 score (skipped)
        assert result.passed is True
        assert result.score == 0.5
        assert result.evidence.get("skipped") is True

    def test_check_bug_count(self, sample_sonarqube_export, sample_ground_truth):
        """Test bug count check."""
        result = check_bug_count(sample_sonarqube_export, sample_ground_truth)

        assert result.check_id == "SQ-AC-2"
        assert result.category == CheckCategory.ACCURACY

    def test_check_vulnerability_count(self, sample_sonarqube_export, sample_ground_truth):
        """Test vulnerability count check."""
        result = check_vulnerability_count(sample_sonarqube_export, sample_ground_truth)

        assert result.check_id == "SQ-AC-3"
        assert result.category == CheckCategory.ACCURACY

    def test_check_smell_count(self, sample_sonarqube_export, sample_ground_truth):
        """Test code smell count check."""
        result = check_smell_count(sample_sonarqube_export, sample_ground_truth)

        assert result.check_id == "SQ-AC-4"
        assert result.category == CheckCategory.ACCURACY

    def test_check_quality_gate_status_pass(self, sample_sonarqube_export, sample_ground_truth):
        """Test quality gate check passes with matching status."""
        result = check_quality_gate_status(sample_sonarqube_export, sample_ground_truth)

        assert result.check_id == "SQ-AC-5"
        assert result.passed is True

    def test_check_quality_gate_status_fail(self, sample_sonarqube_export, sample_ground_truth):
        """Test quality gate check fails with mismatched status."""
        sample_ground_truth["quality_gate_expected"] = "ERROR"

        result = check_quality_gate_status(sample_sonarqube_export, sample_ground_truth)

        assert result.passed is False


class TestCoverageChecks:
    """Tests for coverage checks (SQ-CV-*)."""

    def test_check_metric_presence_pass(self, sample_sonarqube_export):
        """Test metric presence passes with required metrics."""
        # Add all required metrics
        sample_sonarqube_export["results"]["metric_catalog"] = [
            {"key": "ncloc", "name": "Lines of Code", "type": "INT"},
            {"key": "complexity", "name": "Complexity", "type": "INT"},
            {"key": "violations", "name": "Violations", "type": "INT"},
            {"key": "bugs", "name": "Bugs", "type": "INT"},
            {"key": "vulnerabilities", "name": "Vulnerabilities", "type": "INT"},
            {"key": "code_smells", "name": "Code Smells", "type": "INT"},
        ]

        result = check_metric_presence(sample_sonarqube_export, None)

        assert result.check_id == "SQ-CV-1"
        assert result.passed is True

    def test_check_metric_presence_fail(self, sample_sonarqube_export):
        """Test metric presence fails with missing metrics."""
        sample_sonarqube_export["results"]["metric_catalog"] = [
            {"key": "ncloc", "name": "Lines of Code", "type": "INT"},
        ]

        result = check_metric_presence(sample_sonarqube_export, None)

        assert result.passed is False
        assert result.evidence.get("missing")

    def test_check_rule_coverage_pass(self, sample_sonarqube_export):
        """Test rule coverage passes with all rules covered."""
        result = check_rule_coverage(sample_sonarqube_export, None)

        assert result.check_id == "SQ-CV-2"
        # Should pass since sample data has rules for all issues
        assert result.passed is True

    def test_check_file_coverage(self, sample_sonarqube_export):
        """Test file coverage check."""
        result = check_file_coverage(sample_sonarqube_export, None)

        assert result.check_id == "SQ-CV-3"
        assert result.category == CheckCategory.COVERAGE

    def test_check_language_coverage_pass(self, sample_sonarqube_export, sample_ground_truth):
        """Test language coverage passes with expected languages."""
        result = check_language_coverage(sample_sonarqube_export, sample_ground_truth)

        assert result.check_id == "SQ-CV-4"
        assert result.passed is True

    def test_check_language_coverage_skip_no_ground_truth(self, sample_sonarqube_export):
        """Test language coverage skips without ground truth."""
        result = check_language_coverage(sample_sonarqube_export, None)

        assert result.passed is True
        assert result.score == 0.5


class TestCompletenessChecks:
    """Tests for completeness checks (SQ-CM-*)."""

    def test_check_component_tree_pass(self, sample_sonarqube_export):
        """Test component tree check passes with all qualifiers."""
        # Add DIR qualifier
        sample_sonarqube_export["results"]["components"]["by_key"]["test-project:src"] = {
            "key": "test-project:src",
            "qualifier": "DIR",
        }

        result = check_component_tree(sample_sonarqube_export, None)

        assert result.check_id == "SQ-CM-1"
        assert result.passed is True

    def test_check_component_tree_fail(self):
        """Test component tree check fails with missing qualifiers."""
        data = {
            "results": {
                "components": {
                    "by_key": {
                        "proj": {"qualifier": "TRK"},
                    }
                }
            }
        }

        result = check_component_tree(data, None)

        assert result.passed is False
        assert result.evidence.get("missing")  # missing list

    def test_check_issue_locations_pass(self, sample_sonarqube_export):
        """Test issue locations check passes with location info."""
        result = check_issue_locations(sample_sonarqube_export, None)

        assert result.check_id == "SQ-CM-2"
        assert result.passed is True

    def test_check_issue_locations_skip_no_issues(self):
        """Test issue locations skips with no issues."""
        data = {"results": {"issues": {"items": []}}}

        result = check_issue_locations(data, None)

        assert result.passed is True
        assert result.evidence.get("skipped") is True

    def test_check_rules_hydrated_pass(self, sample_sonarqube_export):
        """Test rules hydrated check passes with complete rules."""
        result = check_rules_hydrated(sample_sonarqube_export, None)

        assert result.check_id == "SQ-CM-3"
        assert result.passed is True

    def test_check_rules_hydrated_skip_no_rules(self):
        """Test rules hydrated skips with no rules."""
        data = {"results": {"rules": {"by_key": {}}}}

        result = check_rules_hydrated(data, None)

        assert result.passed is True
        assert result.evidence.get("skipped") is True

    def test_check_duplications_present_pass_zero_dup(self):
        """Test duplications check passes with zero duplication."""
        data = {
            "results": {
                "duplications": {
                    "project_summary": {"duplicated_lines_density": 0},
                    "by_file_key": {},
                }
            }
        }

        result = check_duplications_present(data, None)

        assert result.check_id == "SQ-CM-4"
        assert result.passed is True

    def test_check_quality_gate_conditions_pass(self, sample_sonarqube_export):
        """Test quality gate conditions check passes."""
        result = check_quality_gate_conditions(sample_sonarqube_export, None)

        assert result.check_id == "SQ-CM-5"
        assert result.passed is True

    def test_check_quality_gate_conditions_fail_no_status(self):
        """Test quality gate conditions fails without status."""
        data = {"results": {"quality_gate": {}}}

        result = check_quality_gate_conditions(data, None)

        assert result.passed is False

    def test_check_derived_insights_pass(self, sample_sonarqube_export):
        """Test derived insights check passes."""
        result = check_derived_insights(sample_sonarqube_export, None)

        assert result.check_id == "SQ-CM-6"
        assert result.passed is True

    def test_check_derived_insights_fail(self):
        """Test derived insights fails without insights."""
        data = {"results": {"derived_insights": {"hotspots": [], "directory_rollups": {}}}}

        result = check_derived_insights(data, None)

        assert result.passed is False


class TestRunAllChecks:
    """Tests for run_all_checks function."""

    def test_runs_all_checks(self, sample_sonarqube_export, sample_ground_truth):
        """Test all checks are run."""
        checks = run_all_checks(
            sample_sonarqube_export,
            sample_ground_truth,
        )

        # Should have results from all dimensions
        categories = {c.category for c in checks}
        assert CheckCategory.ACCURACY in categories
        assert CheckCategory.COVERAGE in categories
        assert CheckCategory.COMPLETENESS in categories

        # Should have checks from each dimension
        total_checks = len(checks)
        assert total_checks >= 15  # At least AC + CV + CM checks

    def test_skip_performance_checks(self, sample_sonarqube_export, sample_ground_truth):
        """Test performance checks can be skipped."""
        checks_with_perf = run_all_checks(
            sample_sonarqube_export,
            sample_ground_truth,
            skip_performance=False,
        )
        checks_without_perf = run_all_checks(
            sample_sonarqube_export,
            sample_ground_truth,
            skip_performance=True,
        )

        # Should have fewer checks when skipping performance
        perf_check_count = len([c for c in checks_with_perf if c.category == CheckCategory.PERFORMANCE])
        if perf_check_count > 0:
            assert len(checks_without_perf) < len(checks_with_perf)


class TestLoadAnalysis:
    """Tests for load_analysis function."""

    def test_loads_envelope_format(self, tmp_path):
        """Test loading Caldera envelope format."""
        data = {
            "metadata": {"tool_name": "sonarqube", "tool_version": "1.0"},
            "data": {"results": {"issues": {"items": []}}}
        }
        path = tmp_path / "export.json"
        with open(path, "w") as f:
            json.dump(data, f)

        loaded = load_analysis(path)

        # Should unwrap to data contents
        assert "results" in loaded
        assert "metadata" not in loaded

    def test_loads_legacy_format(self, tmp_path):
        """Test loading legacy (non-envelope) format."""
        data = {"results": {"issues": {"items": []}}}
        path = tmp_path / "export.json"
        with open(path, "w") as f:
            json.dump(data, f)

        loaded = load_analysis(path)

        assert "results" in loaded


class TestCheckRegistration:
    """Tests for check registration."""

    def test_accuracy_checks_count(self, sample_sonarqube_export, sample_ground_truth):
        """Test accuracy checks count."""
        checks = run_accuracy_checks(sample_sonarqube_export, sample_ground_truth)
        assert len(checks) == 5  # SQ-AC-1 through SQ-AC-5

    def test_coverage_checks_count(self, sample_sonarqube_export, sample_ground_truth):
        """Test coverage checks count."""
        checks = run_coverage_checks(sample_sonarqube_export, sample_ground_truth)
        assert len(checks) == 4  # SQ-CV-1 through SQ-CV-4

    def test_completeness_checks_count(self, sample_sonarqube_export, sample_ground_truth):
        """Test completeness checks count."""
        checks = run_completeness_checks(sample_sonarqube_export, sample_ground_truth)
        assert len(checks) == 6  # SQ-CM-1 through SQ-CM-6

    def test_all_checks_have_unique_ids(self, sample_sonarqube_export, sample_ground_truth):
        """Test all check IDs are unique."""
        checks = run_all_checks(sample_sonarqube_export, sample_ground_truth)
        all_ids = [c.check_id for c in checks]

        assert len(all_ids) == len(set(all_ids)), "Found duplicate check IDs"


class TestCheckCategories:
    """Tests for check category assignment."""

    def test_accuracy_checks_have_accuracy_category(self, sample_sonarqube_export, sample_ground_truth):
        """Test accuracy checks are in accuracy category."""
        checks = run_accuracy_checks(sample_sonarqube_export, sample_ground_truth)
        for check in checks:
            assert check.category == CheckCategory.ACCURACY

    def test_coverage_checks_have_coverage_category(self, sample_sonarqube_export, sample_ground_truth):
        """Test coverage checks are in coverage category."""
        checks = run_coverage_checks(sample_sonarqube_export, sample_ground_truth)
        for check in checks:
            assert check.category == CheckCategory.COVERAGE

    def test_completeness_checks_have_completeness_category(self, sample_sonarqube_export, sample_ground_truth):
        """Test completeness checks are in completeness category."""
        checks = run_completeness_checks(sample_sonarqube_export, sample_ground_truth)
        for check in checks:
            assert check.category == CheckCategory.COMPLETENESS
