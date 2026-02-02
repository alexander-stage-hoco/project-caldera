"""Integration tests validating ground truth files and evaluation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks import CheckResult, EvaluationReport
from checks.accuracy import run_accuracy_checks
from checks.coverage import run_coverage_checks
from checks.detection import run_detection_checks
from checks.performance import run_performance_checks

# Paths
TOOL_ROOT = Path(__file__).parents[2]
GROUND_TRUTH_DIR = TOOL_ROOT / "evaluation" / "ground-truth"


class TestGroundTruthFileStructure:
    """Tests validating ground truth file structure."""

    @pytest.fixture
    def ground_truth_files(self) -> list[Path]:
        """Get all ground truth files."""
        return list(GROUND_TRUTH_DIR.glob("*.json"))

    def test_ground_truth_files_exist(self, ground_truth_files: list[Path]) -> None:
        """At least one ground truth file should exist."""
        assert len(ground_truth_files) > 0, "No ground truth files found"

    def test_ground_truth_files_are_valid_json(
        self, ground_truth_files: list[Path]
    ) -> None:
        """All ground truth files should be valid JSON."""
        for gt_file in ground_truth_files:
            try:
                json.loads(gt_file.read_text())
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {gt_file.name}: {e}")

    def test_ground_truth_has_required_fields(
        self, ground_truth_files: list[Path]
    ) -> None:
        """Ground truth files should have required fields."""
        required_root = {"schema_version", "scenario", "expected"}
        required_expected = {
            "total_secrets",
            "unique_secrets",
            "secrets_in_head",
            "secrets_in_history",
        }

        for gt_file in ground_truth_files:
            data = json.loads(gt_file.read_text())

            missing_root = required_root - set(data.keys())
            assert not missing_root, f"{gt_file.name} missing: {missing_root}"

            expected = data.get("expected", {})
            missing_expected = required_expected - set(expected.keys())
            assert (
                not missing_expected
            ), f"{gt_file.name} expected missing: {missing_expected}"

    def test_ground_truth_has_thresholds(
        self, ground_truth_files: list[Path]
    ) -> None:
        """Ground truth files should have performance thresholds."""
        for gt_file in ground_truth_files:
            data = json.loads(gt_file.read_text())
            expected = data.get("expected", {})

            # Thresholds can be at root or in expected
            thresholds = expected.get("thresholds", data.get("thresholds", {}))
            assert "max_scan_time_ms" in thresholds, f"{gt_file.name} missing max_scan_time_ms"

    def test_ground_truth_scenario_matches_filename(
        self, ground_truth_files: list[Path]
    ) -> None:
        """Scenario field should match filename."""
        for gt_file in ground_truth_files:
            data = json.loads(gt_file.read_text())
            scenario = data.get("scenario", "")
            expected_name = gt_file.stem

            assert scenario == expected_name, (
                f"{gt_file.name}: scenario '{scenario}' doesn't match filename"
            )


class TestGroundTruthConsistency:
    """Tests validating ground truth data consistency."""

    @pytest.fixture
    def all_ground_truth(self) -> dict[str, dict]:
        """Load all ground truth files."""
        truths = {}
        for gt_file in GROUND_TRUTH_DIR.glob("*.json"):
            truths[gt_file.stem] = json.loads(gt_file.read_text())
        return truths

    def test_total_equals_head_plus_history(
        self, all_ground_truth: dict[str, dict]
    ) -> None:
        """total_secrets should equal secrets_in_head + secrets_in_history."""
        for name, gt in all_ground_truth.items():
            expected = gt.get("expected", {})
            total = expected.get("total_secrets", 0)
            in_head = expected.get("secrets_in_head", 0)
            in_history = expected.get("secrets_in_history", 0)

            assert total == in_head + in_history, (
                f"{name}: total({total}) != head({in_head}) + history({in_history})"
            )

    def test_files_count_consistency(self, all_ground_truth: dict[str, dict]) -> None:
        """files_with_secrets should match files_with_secrets_list length."""
        for name, gt in all_ground_truth.items():
            expected = gt.get("expected", {})
            count = expected.get("files_with_secrets", 0)
            file_list = expected.get("files_with_secrets_list", [])

            assert count == len(file_list), (
                f"{name}: files_with_secrets({count}) != list length({len(file_list)})"
            )

    def test_rule_ids_consistency(self, all_ground_truth: dict[str, dict]) -> None:
        """rule_ids should match secrets_by_rule keys."""
        for name, gt in all_ground_truth.items():
            expected = gt.get("expected", {})
            rule_ids = set(expected.get("rule_ids", []))
            by_rule_keys = set(expected.get("secrets_by_rule", {}).keys())

            assert rule_ids == by_rule_keys, (
                f"{name}: rule_ids {rule_ids} != secrets_by_rule keys {by_rule_keys}"
            )

    def test_secrets_by_rule_sums_to_total(
        self, all_ground_truth: dict[str, dict]
    ) -> None:
        """Sum of secrets_by_rule should equal total_secrets."""
        for name, gt in all_ground_truth.items():
            expected = gt.get("expected", {})
            total = expected.get("total_secrets", 0)
            by_rule = expected.get("secrets_by_rule", {})
            rule_sum = sum(by_rule.values())

            assert total == rule_sum, (
                f"{name}: total({total}) != sum of rules({rule_sum})"
            )

    def test_findings_count_consistency(
        self, all_ground_truth: dict[str, dict]
    ) -> None:
        """Findings list length should match total_secrets."""
        for name, gt in all_ground_truth.items():
            expected = gt.get("expected", {})
            total = expected.get("total_secrets", 0)
            findings = expected.get("findings", [])

            assert total == len(findings), (
                f"{name}: total({total}) != findings count({len(findings)})"
            )


class TestEvaluationWithMockData:
    """Tests running evaluation checks with mock analysis data."""

    @pytest.fixture
    def clean_analysis(self) -> dict:
        """Mock analysis for clean repo."""
        return {
            "results": {
                "schema_version": "2.0.0",
                "tool_version": "8.18.4",
                "timestamp": "2026-01-21T00:00:00Z",
                "total_secrets": 0,
                "unique_secrets": 0,
                "secrets_in_head": 0,
                "secrets_in_history": 0,
                "files_with_secrets": 0,
                "commits_with_secrets": 0,
                "secrets_by_rule": {},
                "findings": [],
                "files": {},
                "directories": {},
                "scan_time_ms": 500,
            }
        }

    @pytest.fixture
    def clean_ground_truth(self) -> dict:
        """Load no-secrets ground truth."""
        gt_path = GROUND_TRUTH_DIR / "no-secrets.json"
        if not gt_path.exists():
            pytest.skip("no-secrets ground truth not found")
        return json.loads(gt_path.read_text())

    def test_accuracy_checks_pass_for_clean_repo(
        self, clean_analysis: dict, clean_ground_truth: dict
    ) -> None:
        """Accuracy checks should pass for matching clean repo."""
        results = run_accuracy_checks(clean_analysis, clean_ground_truth)

        failed = [r for r in results if not r.passed]
        assert len(failed) == 0, f"Failed checks: {[r.check_id for r in failed]}"

    def test_coverage_checks_pass_with_complete_data(
        self, clean_analysis: dict, clean_ground_truth: dict
    ) -> None:
        """Coverage checks should pass with complete data."""
        results = run_coverage_checks(clean_analysis, clean_ground_truth)

        failed = [r for r in results if not r.passed]
        assert len(failed) == 0, f"Failed checks: {[r.check_id for r in failed]}"

    def test_detection_checks_pass_for_clean_repo(
        self, clean_analysis: dict, clean_ground_truth: dict
    ) -> None:
        """Detection checks should pass for clean repo."""
        results = run_detection_checks(clean_analysis, clean_ground_truth)

        failed = [r for r in results if not r.passed]
        assert len(failed) == 0, f"Failed checks: {[r.check_id for r in failed]}"

    def test_performance_checks_pass_within_thresholds(
        self, clean_analysis: dict, clean_ground_truth: dict
    ) -> None:
        """Performance checks should pass within thresholds."""
        results = run_performance_checks(clean_analysis, clean_ground_truth)

        failed = [r for r in results if not r.passed]
        assert len(failed) == 0, f"Failed checks: {[r.check_id for r in failed]}"


class TestEvaluationReportAggregation:
    """Tests for evaluation report aggregation."""

    def test_evaluation_report_aggregates_results(self) -> None:
        """EvaluationReport should correctly aggregate check results."""
        report = EvaluationReport(repository="test-repo")

        report.add_result(CheckResult("T-1", "Test", True, "Pass"))
        report.add_result(CheckResult("T-2", "Test", False, "Fail"))
        report.add_result(CheckResult("T-3", "Test", True, "Pass"))

        assert report.total_checks == 3
        assert report.passed_checks == 2
        assert report.failed_checks == 1
        assert report.pass_rate == pytest.approx(2 / 3)

    def test_evaluation_report_empty(self) -> None:
        """Empty report should have zero counts."""
        report = EvaluationReport(repository="test-repo")

        assert report.total_checks == 0
        assert report.pass_rate == 0.0

    def test_evaluation_report_all_pass(self) -> None:
        """Report with all passing checks."""
        report = EvaluationReport(repository="test-repo")

        for i in range(5):
            report.add_result(CheckResult(f"T-{i}", "Test", True, "Pass"))

        assert report.pass_rate == 1.0


class TestCheckUtilityFunctions:
    """Tests for check utility functions."""

    def test_check_equal_exact_match(self) -> None:
        """check_equal with exact match."""
        from checks import check_equal

        result = check_equal("T-1", "Test", "Value", 5, 5)
        assert result.passed is True

    def test_check_equal_with_tolerance(self) -> None:
        """check_equal with tolerance."""
        from checks import check_equal

        result = check_equal("T-1", "Test", "Value", 5, 7, tolerance=3)
        assert result.passed is True

        result = check_equal("T-1", "Test", "Value", 5, 10, tolerance=3)
        assert result.passed is False

    def test_check_at_least(self) -> None:
        """check_at_least function."""
        from checks import check_at_least

        result = check_at_least("T-1", "Test", "Value", 5, 10)
        assert result.passed is True

        result = check_at_least("T-1", "Test", "Value", 5, 3)
        assert result.passed is False

    def test_check_at_most(self) -> None:
        """check_at_most function."""
        from checks import check_at_most

        result = check_at_most("T-1", "Test", "Value", 10, 5)
        assert result.passed is True

        result = check_at_most("T-1", "Test", "Value", 10, 15)
        assert result.passed is False

    def test_check_contains(self) -> None:
        """check_contains function."""
        from checks import check_contains

        result = check_contains("T-1", "Test", "Items", ["a", "b"], {"a", "b", "c"})
        assert result.passed is True

        result = check_contains("T-1", "Test", "Items", ["a", "d"], {"a", "b", "c"})
        assert result.passed is False

    def test_check_not_contains(self) -> None:
        """check_not_contains function."""
        from checks import check_not_contains

        result = check_not_contains("T-1", "Test", "Items", ["x", "y"], {"a", "b", "c"})
        assert result.passed is True

        result = check_not_contains("T-1", "Test", "Items", ["a", "x"], {"a", "b", "c"})
        assert result.passed is False

    def test_check_boolean(self) -> None:
        """check_boolean function."""
        from checks import check_boolean

        result = check_boolean("T-1", "Test", "Flag", True, True)
        assert result.passed is True

        result = check_boolean("T-1", "Test", "Flag", True, False)
        assert result.passed is False
