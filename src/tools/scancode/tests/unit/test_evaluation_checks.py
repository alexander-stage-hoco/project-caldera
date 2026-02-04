"""Unit tests for all 28 evaluation checks (LA, LC, LD, LP)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts"))

from checks import (
    CheckResult,
    EvaluationReport,
    check_equal,
    check_in_range,
    check_contains,
    check_boolean,
)
from checks.accuracy import run_accuracy_checks
from checks.coverage import run_coverage_checks
from checks.detection import run_detection_checks
from checks.performance import run_performance_checks


# ============================================================================
# Tests for check helper functions
# ============================================================================


class TestCheckEqual:
    """Tests for check_equal helper function."""

    def test_equal_values_pass(self):
        """Equal values should pass."""
        result = check_equal("TEST-1", "Test", "test value", 10, 10)
        assert result.passed is True
        assert result.check_id == "TEST-1"
        assert result.category == "Test"

    def test_unequal_values_fail(self):
        """Unequal values should fail."""
        result = check_equal("TEST-1", "Test", "test value", 10, 20)
        assert result.passed is False
        assert result.expected == 10
        assert result.actual == 20

    def test_tolerance_allows_difference(self):
        """Tolerance should allow small differences."""
        result = check_equal("TEST-1", "Test", "test value", 10, 12, tolerance=5)
        assert result.passed is True

    def test_tolerance_exceeded_fails(self):
        """Exceeding tolerance should fail."""
        result = check_equal("TEST-1", "Test", "test value", 10, 20, tolerance=5)
        assert result.passed is False

    def test_string_equality(self):
        """String comparison should work."""
        result = check_equal("TEST-1", "Test", "risk level", "low", "low")
        assert result.passed is True

    def test_string_inequality(self):
        """Different strings should fail."""
        result = check_equal("TEST-1", "Test", "risk level", "low", "high")
        assert result.passed is False

    def test_list_equality(self):
        """List comparison should work."""
        result = check_equal("TEST-1", "Test", "licenses", ["MIT"], ["MIT"])
        assert result.passed is True


class TestCheckInRange:
    """Tests for check_in_range helper function."""

    def test_value_in_range_passes(self):
        """Value within range should pass."""
        result = check_in_range("TEST-1", "Test", "scan time", 50, 0, 100)
        assert result.passed is True

    def test_value_at_min_passes(self):
        """Value at minimum boundary should pass."""
        result = check_in_range("TEST-1", "Test", "scan time", 0, 0, 100)
        assert result.passed is True

    def test_value_at_max_passes(self):
        """Value at maximum boundary should pass."""
        result = check_in_range("TEST-1", "Test", "scan time", 100, 0, 100)
        assert result.passed is True

    def test_value_below_min_fails(self):
        """Value below minimum should fail."""
        result = check_in_range("TEST-1", "Test", "scan time", -1, 0, 100)
        assert result.passed is False

    def test_value_above_max_fails(self):
        """Value above maximum should fail."""
        result = check_in_range("TEST-1", "Test", "scan time", 101, 0, 100)
        assert result.passed is False

    def test_message_includes_range(self):
        """Message should include the range."""
        result = check_in_range("TEST-1", "Test", "scan time", 50, 0, 100)
        assert "range=[0, 100]" in result.message


class TestCheckContains:
    """Tests for check_contains helper function."""

    def test_all_items_present_passes(self):
        """All expected items present should pass."""
        result = check_contains("TEST-1", "Test", "licenses", ["MIT"], ["MIT", "Apache-2.0"])
        assert result.passed is True

    def test_missing_items_fails(self):
        """Missing expected items should fail."""
        result = check_contains("TEST-1", "Test", "licenses", ["MIT", "BSD"], ["MIT"])
        assert result.passed is False

    def test_empty_expected_passes(self):
        """Empty expected list should pass."""
        result = check_contains("TEST-1", "Test", "licenses", [], ["MIT"])
        assert result.passed is True

    def test_both_empty_passes(self):
        """Both empty lists should pass."""
        result = check_contains("TEST-1", "Test", "licenses", [], [])
        assert result.passed is True

    def test_message_shows_missing(self):
        """Message should show missing items."""
        result = check_contains("TEST-1", "Test", "licenses", ["MIT", "BSD"], ["MIT"])
        assert "missing=" in result.message


class TestCheckBoolean:
    """Tests for check_boolean helper function."""

    def test_matching_true_passes(self):
        """Matching True values should pass."""
        result = check_boolean("TEST-1", "Test", "has copyleft", True, True)
        assert result.passed is True

    def test_matching_false_passes(self):
        """Matching False values should pass."""
        result = check_boolean("TEST-1", "Test", "has copyleft", False, False)
        assert result.passed is True  # Both False means they match

    def test_mismatched_values_fails(self):
        """Mismatched boolean values should fail."""
        result = check_boolean("TEST-1", "Test", "has copyleft", True, False)
        assert result.passed is False


class TestEvaluationReport:
    """Tests for EvaluationReport dataclass."""

    def test_initial_values(self):
        """EvaluationReport should have zero initial values."""
        report = EvaluationReport(repository="test")
        assert report.total_checks == 0
        assert report.passed_checks == 0
        assert report.failed_checks == 0
        assert report.pass_rate == 0.0
        assert report.results == []

    def test_add_passed_result(self):
        """Adding passed result should update statistics."""
        report = EvaluationReport(repository="test")
        report.add_result(CheckResult("TEST-1", "Test", passed=True, message="ok"))

        assert report.total_checks == 1
        assert report.passed_checks == 1
        assert report.failed_checks == 0
        assert report.pass_rate == 1.0

    def test_add_failed_result(self):
        """Adding failed result should update statistics."""
        report = EvaluationReport(repository="test")
        report.add_result(CheckResult("TEST-1", "Test", passed=False, message="failed"))

        assert report.total_checks == 1
        assert report.passed_checks == 0
        assert report.failed_checks == 1
        assert report.pass_rate == 0.0

    def test_mixed_results_pass_rate(self):
        """Mixed results should compute correct pass rate."""
        report = EvaluationReport(repository="test")
        report.add_result(CheckResult("TEST-1", "Test", passed=True, message="ok"))
        report.add_result(CheckResult("TEST-2", "Test", passed=False, message="failed"))
        report.add_result(CheckResult("TEST-3", "Test", passed=True, message="ok"))
        report.add_result(CheckResult("TEST-4", "Test", passed=True, message="ok"))

        assert report.total_checks == 4
        assert report.passed_checks == 3
        assert report.failed_checks == 1
        assert report.pass_rate == 0.75


# ============================================================================
# Tests for Accuracy Checks (LA-1 to LA-10)
# ============================================================================


class TestAccuracyChecks:
    """Tests for run_accuracy_checks function."""

    def _create_analysis(self, **overrides):
        """Create a base analysis dict with optional overrides."""
        base = {
            "licenses_found": ["MIT"],
            "license_counts": {"MIT": 2},
            "license_files_found": 1,
            "files_with_licenses": 2,
            "overall_risk": "low",
            "has_permissive": True,
            "has_copyleft": False,
            "has_weak_copyleft": False,
            "has_unknown": False,
        }
        base.update(overrides)
        return base

    def _create_ground_truth(self, **expected_overrides):
        """Create a base ground truth dict with optional overrides."""
        expected = {
            "total_licenses": 1,
            "licenses": ["MIT"],
            "license_files_found": 1,
            "files_with_licenses": 2,
            "overall_risk": "low",
            "has_permissive": True,
            "has_copyleft": False,
            "has_weak_copyleft": False,
            "has_unknown": False,
            "license_counts": {"MIT": 2},
        }
        expected.update(expected_overrides)
        return {"expected": expected, "thresholds": {"count_tolerance": 0}}

    def test_all_checks_pass_for_matching_data(self):
        """All accuracy checks should pass when data matches ground truth."""
        analysis = self._create_analysis()
        ground_truth = self._create_ground_truth()
        results = run_accuracy_checks(analysis, ground_truth)

        # LA-1 through LA-12 (12 checks), LA-13 and LA-14 only run with expected_findings
        assert len(results) == 12
        assert all(r.passed for r in results), f"Failed checks: {[r.check_id for r in results if not r.passed]}"

    def test_la1_total_licenses_count(self):
        """LA-1: Total licenses count should be validated."""
        analysis = self._create_analysis(licenses_found=["MIT", "Apache-2.0"])
        ground_truth = self._create_ground_truth(total_licenses=1)
        results = run_accuracy_checks(analysis, ground_truth)

        la1 = next(r for r in results if r.check_id == "LA-1")
        assert la1.passed is False
        assert la1.expected == 1
        assert la1.actual == 2

    def test_la1_with_tolerance(self):
        """LA-1: Should pass within tolerance."""
        analysis = self._create_analysis(licenses_found=["MIT", "Apache-2.0"])
        ground_truth = self._create_ground_truth(total_licenses=1)
        ground_truth["thresholds"]["count_tolerance"] = 1
        results = run_accuracy_checks(analysis, ground_truth)

        la1 = next(r for r in results if r.check_id == "LA-1")
        assert la1.passed is True

    def test_la2_expected_licenses_detected(self):
        """LA-2: Expected licenses should be detected."""
        analysis = self._create_analysis(licenses_found=["MIT"])
        ground_truth = self._create_ground_truth(licenses=["MIT", "Apache-2.0"])
        results = run_accuracy_checks(analysis, ground_truth)

        la2 = next(r for r in results if r.check_id == "LA-2")
        assert la2.passed is False  # Apache-2.0 missing

    def test_la3_license_files_count(self):
        """LA-3: License file count should be validated."""
        analysis = self._create_analysis(license_files_found=3)
        ground_truth = self._create_ground_truth(license_files_found=1)
        results = run_accuracy_checks(analysis, ground_truth)

        la3 = next(r for r in results if r.check_id == "LA-3")
        assert la3.passed is False

    def test_la4_files_with_licenses(self):
        """LA-4: Files with licenses count should be validated."""
        analysis = self._create_analysis(files_with_licenses=5)
        ground_truth = self._create_ground_truth(files_with_licenses=2)
        results = run_accuracy_checks(analysis, ground_truth)

        la4 = next(r for r in results if r.check_id == "LA-4")
        assert la4.passed is False

    def test_la5_overall_risk(self):
        """LA-5: Overall risk level should be validated."""
        analysis = self._create_analysis(overall_risk="high")
        ground_truth = self._create_ground_truth(overall_risk="low")
        results = run_accuracy_checks(analysis, ground_truth)

        la5 = next(r for r in results if r.check_id == "LA-5")
        assert la5.passed is False

    def test_la6_has_permissive(self):
        """LA-6: Has permissive flag should be validated."""
        analysis = self._create_analysis(has_permissive=False)
        ground_truth = self._create_ground_truth(has_permissive=True)
        results = run_accuracy_checks(analysis, ground_truth)

        la6 = next(r for r in results if r.check_id == "LA-6")
        assert la6.passed is False

    def test_la7_has_copyleft(self):
        """LA-7: Has copyleft flag should be validated."""
        analysis = self._create_analysis(has_copyleft=True)
        ground_truth = self._create_ground_truth(has_copyleft=False)
        results = run_accuracy_checks(analysis, ground_truth)

        la7 = next(r for r in results if r.check_id == "LA-7")
        assert la7.passed is False

    def test_la8_has_weak_copyleft(self):
        """LA-8: Has weak-copyleft flag should be validated."""
        analysis = self._create_analysis(has_weak_copyleft=True)
        ground_truth = self._create_ground_truth(has_weak_copyleft=False)
        results = run_accuracy_checks(analysis, ground_truth)

        la8 = next(r for r in results if r.check_id == "LA-8")
        assert la8.passed is False

    def test_la9_has_unknown(self):
        """LA-9: Has unknown flag should be validated."""
        analysis = self._create_analysis(has_unknown=True)
        ground_truth = self._create_ground_truth(has_unknown=False)
        results = run_accuracy_checks(analysis, ground_truth)

        la9 = next(r for r in results if r.check_id == "LA-9")
        assert la9.passed is False

    def test_la10_license_counts_match(self):
        """LA-10: License counts should match."""
        analysis = self._create_analysis(license_counts={"MIT": 3})
        ground_truth = self._create_ground_truth(license_counts={"MIT": 2})
        results = run_accuracy_checks(analysis, ground_truth)

        la10 = next(r for r in results if r.check_id == "LA-10")
        assert la10.passed is False

    def test_la11_no_unexpected_licenses(self):
        """LA-11: Should detect unexpected licenses (false positives)."""
        # Actual contains GPL which is not expected
        analysis = self._create_analysis(licenses_found=["MIT", "GPL-3.0-only"])
        ground_truth = self._create_ground_truth(licenses=["MIT"])
        results = run_accuracy_checks(analysis, ground_truth)

        la11 = next(r for r in results if r.check_id == "LA-11")
        assert la11.passed is False  # GPL-3.0-only is unexpected

    def test_la11_no_false_positives_passes(self):
        """LA-11: Should pass when no unexpected licenses are present."""
        analysis = self._create_analysis(licenses_found=["MIT"])
        ground_truth = self._create_ground_truth(licenses=["MIT"])
        results = run_accuracy_checks(analysis, ground_truth)

        la11 = next(r for r in results if r.check_id == "LA-11")
        assert la11.passed is True

    def test_la12_finding_paths_present(self):
        """LA-12: All findings should have file_path."""
        analysis = self._create_analysis()
        analysis["findings"] = [
            {"file_path": "LICENSE", "spdx_id": "MIT"},
            {"file_path": "src/main.py", "spdx_id": "MIT"},
        ]
        ground_truth = self._create_ground_truth()
        results = run_accuracy_checks(analysis, ground_truth)

        la12 = next(r for r in results if r.check_id == "LA-12")
        assert la12.passed is True

    def test_la12_missing_file_path_fails(self):
        """LA-12: Findings with missing file_path should fail."""
        analysis = self._create_analysis()
        analysis["findings"] = [
            {"file_path": "LICENSE", "spdx_id": "MIT"},
            {"spdx_id": "MIT"},  # Missing file_path
        ]
        ground_truth = self._create_ground_truth()
        results = run_accuracy_checks(analysis, ground_truth)

        la12 = next(r for r in results if r.check_id == "LA-12")
        assert la12.passed is False

    def test_la12_empty_file_path_fails(self):
        """LA-12: Findings with empty file_path should fail."""
        analysis = self._create_analysis()
        analysis["findings"] = [
            {"file_path": "", "spdx_id": "MIT"},  # Empty file_path
        ]
        ground_truth = self._create_ground_truth()
        results = run_accuracy_checks(analysis, ground_truth)

        la12 = next(r for r in results if r.check_id == "LA-12")
        assert la12.passed is False

    def test_la13_expected_paths_detected(self):
        """LA-13: All expected paths should be detected."""
        analysis = self._create_analysis()
        analysis["findings"] = [
            {"file_path": "LICENSE", "spdx_id": "MIT"},
            {"file_path": "src/main.py", "spdx_id": "MIT"},
        ]
        ground_truth = self._create_ground_truth()
        ground_truth["expected"]["expected_findings"] = [
            {"file_path": "LICENSE", "spdx_id": "MIT", "match_type": "file"},
            {"file_path": "src/main.py", "spdx_id": "MIT", "match_type": "spdx"},
        ]
        results = run_accuracy_checks(analysis, ground_truth)

        la13 = next(r for r in results if r.check_id == "LA-13")
        assert la13.passed is True

    def test_la13_missing_path_fails(self):
        """LA-13: Missing expected paths should fail."""
        analysis = self._create_analysis()
        analysis["findings"] = [
            {"file_path": "LICENSE", "spdx_id": "MIT"},
        ]
        ground_truth = self._create_ground_truth()
        ground_truth["expected"]["expected_findings"] = [
            {"file_path": "LICENSE", "spdx_id": "MIT", "match_type": "file"},
            {"file_path": "src/main.py", "spdx_id": "MIT", "match_type": "spdx"},
        ]
        results = run_accuracy_checks(analysis, ground_truth)

        la13 = next(r for r in results if r.check_id == "LA-13")
        assert la13.passed is False

    def test_la14_no_unexpected_paths(self):
        """LA-14: No unexpected paths should be present."""
        analysis = self._create_analysis()
        analysis["findings"] = [
            {"file_path": "LICENSE", "spdx_id": "MIT"},
            {"file_path": "src/main.py", "spdx_id": "MIT"},
        ]
        ground_truth = self._create_ground_truth()
        ground_truth["expected"]["expected_findings"] = [
            {"file_path": "LICENSE", "spdx_id": "MIT", "match_type": "file"},
            {"file_path": "src/main.py", "spdx_id": "MIT", "match_type": "spdx"},
        ]
        results = run_accuracy_checks(analysis, ground_truth)

        la14 = next(r for r in results if r.check_id == "LA-14")
        assert la14.passed is True

    def test_la14_unexpected_path_fails(self):
        """LA-14: Unexpected paths should fail."""
        analysis = self._create_analysis()
        analysis["findings"] = [
            {"file_path": "LICENSE", "spdx_id": "MIT"},
            {"file_path": "src/main.py", "spdx_id": "MIT"},
            {"file_path": "extra/unexpected.py", "spdx_id": "MIT"},  # Unexpected
        ]
        ground_truth = self._create_ground_truth()
        ground_truth["expected"]["expected_findings"] = [
            {"file_path": "LICENSE", "spdx_id": "MIT", "match_type": "file"},
            {"file_path": "src/main.py", "spdx_id": "MIT", "match_type": "spdx"},
        ]
        results = run_accuracy_checks(analysis, ground_truth)

        la14 = next(r for r in results if r.check_id == "LA-14")
        assert la14.passed is False

    def test_la13_la14_skipped_without_expected_findings(self):
        """LA-13 and LA-14 should be skipped when expected_findings is not defined."""
        analysis = self._create_analysis()
        analysis["findings"] = [
            {"file_path": "LICENSE", "spdx_id": "MIT"},
        ]
        ground_truth = self._create_ground_truth()
        # No expected_findings defined
        results = run_accuracy_checks(analysis, ground_truth)

        check_ids = [r.check_id for r in results]
        assert "LA-12" in check_ids  # LA-12 should always run
        assert "LA-13" not in check_ids  # LA-13 should be skipped
        assert "LA-14" not in check_ids  # LA-14 should be skipped


# ============================================================================
# Tests for Coverage Checks (LC-1 to LC-8)
# ============================================================================


class TestCoverageChecks:
    """Tests for run_coverage_checks function."""

    def _create_full_analysis(self):
        """Create analysis with all required fields."""
        return {
            "schema_version": "1.0.0",
            "repository": "test",
            "timestamp": "2025-01-01T00:00:00Z",
            "tool": "license-analyzer",
            "tool_version": "1.0.0",
            "total_files_scanned": 10,
            "files_with_licenses": 2,
            "license_files_found": 1,
            "licenses_found": ["MIT"],
            "license_counts": {"MIT": 2},
            "has_permissive": True,
            "has_weak_copyleft": False,
            "has_copyleft": False,
            "has_unknown": False,
            "overall_risk": "low",
            "risk_reasons": ["Only permissive licenses found"],
            "findings": [
                {
                    "file_path": "LICENSE",
                    "spdx_id": "MIT",
                    "category": "permissive",
                    "confidence": 0.90,
                    "match_type": "file",
                }
            ],
            "files": {
                "LICENSE": {
                    "file_path": "LICENSE",
                    "licenses": ["MIT"],
                    "category": "permissive",
                    "has_spdx_header": False,
                }
            },
            "scan_time_ms": 123.4,
        }

    def test_all_coverage_checks_pass(self):
        """All coverage checks should pass when all fields present."""
        analysis = self._create_full_analysis()
        ground_truth = {"expected": {}}
        results = run_coverage_checks(analysis, ground_truth)

        assert len(results) == 8  # LC-1 through LC-8
        assert all(r.passed for r in results), f"Failed: {[r.check_id for r in results if not r.passed]}"

    def test_lc1_summary_fields_missing(self):
        """LC-1: Missing summary fields should fail."""
        analysis = self._create_full_analysis()
        del analysis["total_files_scanned"]
        results = run_coverage_checks(analysis, {"expected": {}})

        lc1 = next(r for r in results if r.check_id == "LC-1")
        assert lc1.passed is False

    def test_lc2_license_inventory_missing(self):
        """LC-2: Missing license inventory should fail."""
        analysis = self._create_full_analysis()
        del analysis["licenses_found"]
        results = run_coverage_checks(analysis, {"expected": {}})

        lc2 = next(r for r in results if r.check_id == "LC-2")
        assert lc2.passed is False

    def test_lc3_category_flags_missing(self):
        """LC-3: Missing category flags should fail."""
        analysis = self._create_full_analysis()
        del analysis["has_permissive"]
        results = run_coverage_checks(analysis, {"expected": {}})

        lc3 = next(r for r in results if r.check_id == "LC-3")
        assert lc3.passed is False

    def test_lc4_risk_assessment_missing(self):
        """LC-4: Missing risk assessment should fail."""
        analysis = self._create_full_analysis()
        del analysis["overall_risk"]
        results = run_coverage_checks(analysis, {"expected": {}})

        lc4 = next(r for r in results if r.check_id == "LC-4")
        assert lc4.passed is False

    def test_lc5_findings_incomplete(self):
        """LC-5: Incomplete findings should fail."""
        analysis = self._create_full_analysis()
        analysis["findings"] = [{"file_path": "LICENSE"}]  # Missing required fields
        results = run_coverage_checks(analysis, {"expected": {}})

        lc5 = next(r for r in results if r.check_id == "LC-5")
        assert lc5.passed is False

    def test_lc5_empty_findings_passes(self):
        """LC-5: Empty findings array should pass (no incomplete findings)."""
        analysis = self._create_full_analysis()
        analysis["findings"] = []
        results = run_coverage_checks(analysis, {"expected": {}})

        lc5 = next(r for r in results if r.check_id == "LC-5")
        assert lc5.passed is True

    def test_lc6_file_summaries_incomplete(self):
        """LC-6: Incomplete file summaries should fail."""
        analysis = self._create_full_analysis()
        analysis["files"] = {"LICENSE": {"file_path": "LICENSE"}}  # Missing fields
        results = run_coverage_checks(analysis, {"expected": {}})

        lc6 = next(r for r in results if r.check_id == "LC-6")
        assert lc6.passed is False

    def test_lc7_metadata_missing(self):
        """LC-7: Missing metadata should fail."""
        analysis = self._create_full_analysis()
        del analysis["schema_version"]
        results = run_coverage_checks(analysis, {"expected": {}})

        lc7 = next(r for r in results if r.check_id == "LC-7")
        assert lc7.passed is False

    def test_lc8_timing_missing(self):
        """LC-8: Missing scan_time_ms should fail."""
        analysis = self._create_full_analysis()
        del analysis["scan_time_ms"]
        results = run_coverage_checks(analysis, {"expected": {}})

        lc8 = next(r for r in results if r.check_id == "LC-8")
        assert lc8.passed is False


# ============================================================================
# Tests for Detection Checks (LD-1 to LD-6)
# ============================================================================


class TestDetectionChecks:
    """Tests for run_detection_checks function."""

    def _create_analysis_with_findings(self, findings):
        """Create analysis with specified findings."""
        return {"findings": findings}

    def _create_ground_truth(self, **expected):
        """Create ground truth with expected values."""
        return {"expected": expected}

    def test_ld1_spdx_header_count(self):
        """LD-1: SPDX header count should match."""
        analysis = self._create_analysis_with_findings([
            {"file_path": "main.py", "spdx_id": "MIT", "category": "permissive", "confidence": 0.95, "match_type": "spdx"},
            {"file_path": "LICENSE", "spdx_id": "MIT", "category": "permissive", "confidence": 0.90, "match_type": "file"},
        ])
        ground_truth = self._create_ground_truth(spdx_headers_found=1)
        results = run_detection_checks(analysis, ground_truth)

        ld1 = next(r for r in results if r.check_id == "LD-1")
        assert ld1.passed is True

    def test_ld1_spdx_count_mismatch(self):
        """LD-1: Wrong SPDX count should fail."""
        analysis = self._create_analysis_with_findings([
            {"file_path": "main.py", "spdx_id": "MIT", "category": "permissive", "confidence": 0.95, "match_type": "spdx"},
        ])
        ground_truth = self._create_ground_truth(spdx_headers_found=2)
        results = run_detection_checks(analysis, ground_truth)

        ld1 = next(r for r in results if r.check_id == "LD-1")
        assert ld1.passed is False

    def test_ld2_license_file_count(self):
        """LD-2: License file detection count should match."""
        analysis = self._create_analysis_with_findings([
            {"file_path": "LICENSE", "spdx_id": "MIT", "category": "permissive", "confidence": 0.90, "match_type": "file"},
        ])
        ground_truth = self._create_ground_truth(license_file_detections=1)
        results = run_detection_checks(analysis, ground_truth)

        ld2 = next(r for r in results if r.check_id == "LD-2")
        assert ld2.passed is True

    def test_ld3_confidence_scores_valid(self):
        """LD-3: All confidence scores should be in [0, 1]."""
        analysis = self._create_analysis_with_findings([
            {"file_path": "a.py", "spdx_id": "MIT", "category": "permissive", "confidence": 0.95, "match_type": "spdx"},
            {"file_path": "b.py", "spdx_id": "MIT", "category": "permissive", "confidence": 0.80, "match_type": "header"},
        ])
        results = run_detection_checks(analysis, {"expected": {}})

        ld3 = next(r for r in results if r.check_id == "LD-3")
        assert ld3.passed is True

    def test_ld3_invalid_confidence_fails(self):
        """LD-3: Confidence outside [0, 1] should fail."""
        analysis = self._create_analysis_with_findings([
            {"file_path": "a.py", "spdx_id": "MIT", "category": "permissive", "confidence": 1.5, "match_type": "spdx"},
        ])
        results = run_detection_checks(analysis, {"expected": {}})

        ld3 = next(r for r in results if r.check_id == "LD-3")
        assert ld3.passed is False

    def test_ld4_valid_categories(self):
        """LD-4: All categories should be valid."""
        analysis = self._create_analysis_with_findings([
            {"file_path": "a.py", "spdx_id": "MIT", "category": "permissive", "confidence": 0.95, "match_type": "spdx"},
            {"file_path": "b.py", "spdx_id": "GPL-3.0", "category": "copyleft", "confidence": 0.90, "match_type": "file"},
        ])
        results = run_detection_checks(analysis, {"expected": {}})

        ld4 = next(r for r in results if r.check_id == "LD-4")
        assert ld4.passed is True

    def test_ld4_invalid_category_fails(self):
        """LD-4: Invalid category should fail."""
        analysis = self._create_analysis_with_findings([
            {"file_path": "a.py", "spdx_id": "MIT", "category": "invalid_category", "confidence": 0.95, "match_type": "spdx"},
        ])
        results = run_detection_checks(analysis, {"expected": {}})

        ld4 = next(r for r in results if r.check_id == "LD-4")
        assert ld4.passed is False

    def test_ld5_valid_match_types(self):
        """LD-5: All match types should be valid."""
        analysis = self._create_analysis_with_findings([
            {"file_path": "a.py", "spdx_id": "MIT", "category": "permissive", "confidence": 0.95, "match_type": "spdx"},
            {"file_path": "LICENSE", "spdx_id": "MIT", "category": "permissive", "confidence": 0.90, "match_type": "file"},
            {"file_path": "README", "spdx_id": "MIT", "category": "permissive", "confidence": 0.80, "match_type": "header"},
        ])
        results = run_detection_checks(analysis, {"expected": {}})

        ld5 = next(r for r in results if r.check_id == "LD-5")
        assert ld5.passed is True

    def test_ld5_invalid_match_type_fails(self):
        """LD-5: Invalid match type should fail."""
        analysis = self._create_analysis_with_findings([
            {"file_path": "a.py", "spdx_id": "MIT", "category": "permissive", "confidence": 0.95, "match_type": "invalid"},
        ])
        results = run_detection_checks(analysis, {"expected": {}})

        ld5 = next(r for r in results if r.check_id == "LD-5")
        assert ld5.passed is False

    def test_ld6_findings_count_match(self):
        """LD-6: Findings count should match expected."""
        analysis = self._create_analysis_with_findings([
            {"file_path": "a.py", "spdx_id": "MIT", "category": "permissive", "confidence": 0.95, "match_type": "spdx"},
            {"file_path": "LICENSE", "spdx_id": "MIT", "category": "permissive", "confidence": 0.90, "match_type": "file"},
        ])
        ground_truth = self._create_ground_truth(total_findings=2)
        results = run_detection_checks(analysis, ground_truth)

        ld6 = next(r for r in results if r.check_id == "LD-6")
        assert ld6.passed is True

    def test_ld6_findings_count_mismatch(self):
        """LD-6: Wrong findings count should fail."""
        analysis = self._create_analysis_with_findings([
            {"file_path": "a.py", "spdx_id": "MIT", "category": "permissive", "confidence": 0.95, "match_type": "spdx"},
        ])
        ground_truth = self._create_ground_truth(total_findings=3)
        results = run_detection_checks(analysis, ground_truth)

        ld6 = next(r for r in results if r.check_id == "LD-6")
        assert ld6.passed is False

    def test_empty_findings_passes_ld3_ld4_ld5(self):
        """Empty findings should pass confidence, category, and match_type checks."""
        analysis = self._create_analysis_with_findings([])
        results = run_detection_checks(analysis, {"expected": {}})

        ld3 = next(r for r in results if r.check_id == "LD-3")
        ld4 = next(r for r in results if r.check_id == "LD-4")
        ld5 = next(r for r in results if r.check_id == "LD-5")

        assert ld3.passed is True
        assert ld4.passed is True
        assert ld5.passed is True


# ============================================================================
# Tests for Performance Checks (LP-1 to LP-4)
# ============================================================================


class TestPerformanceChecks:
    """Tests for run_performance_checks function."""

    def test_lp1_scan_time_within_limit(self):
        """LP-1: Scan time within limit should pass."""
        analysis = {"scan_time_ms": 1000, "total_files_scanned": 10}
        ground_truth = {"thresholds": {"max_scan_time_ms": 5000}}
        results = run_performance_checks(analysis, ground_truth)

        lp1 = next(r for r in results if r.check_id == "LP-1")
        assert lp1.passed is True

    def test_lp1_scan_time_exceeds_limit(self):
        """LP-1: Scan time exceeding limit should fail."""
        analysis = {"scan_time_ms": 10000, "total_files_scanned": 10}
        ground_truth = {"thresholds": {"max_scan_time_ms": 5000}}
        results = run_performance_checks(analysis, ground_truth)

        lp1 = next(r for r in results if r.check_id == "LP-1")
        assert lp1.passed is False

    def test_lp2_scan_time_positive(self):
        """LP-2: Positive scan time should pass."""
        analysis = {"scan_time_ms": 100, "total_files_scanned": 10}
        results = run_performance_checks(analysis, {"thresholds": {}})

        lp2 = next(r for r in results if r.check_id == "LP-2")
        assert lp2.passed is True

    def test_lp2_zero_scan_time_fails(self):
        """LP-2: Zero scan time should fail."""
        analysis = {"scan_time_ms": 0, "total_files_scanned": 10}
        results = run_performance_checks(analysis, {"thresholds": {}})

        lp2 = next(r for r in results if r.check_id == "LP-2")
        assert lp2.passed is False

    def test_lp3_processing_rate_acceptable(self):
        """LP-3: Acceptable processing rate should pass."""
        analysis = {"scan_time_ms": 1000, "total_files_scanned": 100}  # 100 files/sec
        ground_truth = {"thresholds": {"min_files_per_second": 1}}
        results = run_performance_checks(analysis, ground_truth)

        lp3 = next(r for r in results if r.check_id == "LP-3")
        assert lp3.passed is True

    def test_lp3_processing_rate_too_slow(self):
        """LP-3: Processing rate too slow should fail."""
        analysis = {"scan_time_ms": 10000, "total_files_scanned": 1}  # 0.1 files/sec
        ground_truth = {"thresholds": {"min_files_per_second": 1}}
        results = run_performance_checks(analysis, ground_truth)

        lp3 = next(r for r in results if r.check_id == "LP-3")
        assert lp3.passed is False

    def test_lp3_zero_files_passes(self):
        """LP-3: Zero files scanned should pass (N/A case)."""
        analysis = {"scan_time_ms": 100, "total_files_scanned": 0}
        results = run_performance_checks(analysis, {"thresholds": {}})

        lp3 = next(r for r in results if r.check_id == "LP-3")
        assert lp3.passed is True

    def test_lp3_zero_time_passes(self):
        """LP-3: Zero scan time should pass (N/A case)."""
        analysis = {"scan_time_ms": 0, "total_files_scanned": 10}
        results = run_performance_checks(analysis, {"thresholds": {}})

        lp3 = next(r for r in results if r.check_id == "LP-3")
        assert lp3.passed is True

    def test_lp4_always_passes(self):
        """LP-4: Should always pass (completion check)."""
        analysis = {"scan_time_ms": 100, "total_files_scanned": 10}
        results = run_performance_checks(analysis, {"thresholds": {}})

        lp4 = next(r for r in results if r.check_id == "LP-4")
        assert lp4.passed is True

    def test_all_performance_checks_count(self):
        """Should return exactly 4 performance checks."""
        analysis = {"scan_time_ms": 100, "total_files_scanned": 10}
        results = run_performance_checks(analysis, {"thresholds": {}})

        assert len(results) == 4
        check_ids = {r.check_id for r in results}
        assert check_ids == {"LP-1", "LP-2", "LP-3", "LP-4"}


# ============================================================================
# Integration Tests
# ============================================================================


class TestCheckIntegration:
    """Integration tests combining multiple check categories."""

    def test_total_checks_count_is_32_with_expected_findings(self):
        """Total number of checks should be 32 (14 + 8 + 6 + 4) when expected_findings defined."""
        analysis = {
            "schema_version": "1.0.0",
            "repository": "test",
            "timestamp": "2025-01-01T00:00:00Z",
            "tool": "license-analyzer",
            "tool_version": "1.0.0",
            "total_files_scanned": 10,
            "files_with_licenses": 2,
            "license_files_found": 1,
            "licenses_found": ["MIT"],
            "license_counts": {"MIT": 2},
            "has_permissive": True,
            "has_weak_copyleft": False,
            "has_copyleft": False,
            "has_unknown": False,
            "overall_risk": "low",
            "risk_reasons": ["Only permissive licenses found"],
            "findings": [
                {"file_path": "LICENSE", "spdx_id": "MIT"},
                {"file_path": "src/main.py", "spdx_id": "MIT"},
            ],
            "files": {},
            "scan_time_ms": 123.4,
        }
        ground_truth = {
            "expected": {
                "total_licenses": 1,
                "licenses": ["MIT"],
                "license_files_found": 1,
                "files_with_licenses": 2,
                "overall_risk": "low",
                "has_permissive": True,
                "has_copyleft": False,
                "has_weak_copyleft": False,
                "has_unknown": False,
                "license_counts": {"MIT": 2},
                "spdx_headers_found": 1,
                "license_file_detections": 1,
                "total_findings": 2,
                "expected_findings": [
                    {"file_path": "LICENSE", "spdx_id": "MIT", "match_type": "file"},
                    {"file_path": "src/main.py", "spdx_id": "MIT", "match_type": "spdx"},
                ],
            },
            "thresholds": {
                "count_tolerance": 0,
                "max_scan_time_ms": 5000,
                "min_files_per_second": 1,
            },
        }

        accuracy = run_accuracy_checks(analysis, ground_truth)
        coverage = run_coverage_checks(analysis, ground_truth)
        detection = run_detection_checks(analysis, ground_truth)
        performance = run_performance_checks(analysis, ground_truth)

        # LA-12, LA-13, LA-14 are new checks (14 accuracy checks total)
        # LA-13 and LA-14 only run when expected_findings is defined
        total = len(accuracy) + len(coverage) + len(detection) + len(performance)
        assert total == 32

    def test_total_checks_count_is_30_without_expected_findings(self):
        """Total number of checks should be 30 (12 + 8 + 6 + 4) when expected_findings not defined."""
        analysis = {
            "schema_version": "1.0.0",
            "repository": "test",
            "timestamp": "2025-01-01T00:00:00Z",
            "tool": "license-analyzer",
            "tool_version": "1.0.0",
            "total_files_scanned": 10,
            "files_with_licenses": 2,
            "license_files_found": 1,
            "licenses_found": ["MIT"],
            "license_counts": {"MIT": 2},
            "has_permissive": True,
            "has_weak_copyleft": False,
            "has_copyleft": False,
            "has_unknown": False,
            "overall_risk": "low",
            "risk_reasons": ["Only permissive licenses found"],
            "findings": [],
            "files": {},
            "scan_time_ms": 123.4,
        }
        ground_truth = {
            "expected": {
                "total_licenses": 1,
                "licenses": ["MIT"],
                "license_files_found": 1,
                "files_with_licenses": 2,
                "overall_risk": "low",
                "has_permissive": True,
                "has_copyleft": False,
                "has_weak_copyleft": False,
                "has_unknown": False,
                "license_counts": {"MIT": 2},
                "spdx_headers_found": 0,
                "license_file_detections": 0,
                "total_findings": 0,
            },
            "thresholds": {
                "count_tolerance": 0,
                "max_scan_time_ms": 5000,
                "min_files_per_second": 1,
            },
        }

        accuracy = run_accuracy_checks(analysis, ground_truth)
        coverage = run_coverage_checks(analysis, ground_truth)
        detection = run_detection_checks(analysis, ground_truth)
        performance = run_performance_checks(analysis, ground_truth)

        # LA-12 always runs, LA-13/LA-14 skipped without expected_findings
        total = len(accuracy) + len(coverage) + len(detection) + len(performance)
        assert total == 30

    def test_check_categories_unique_ids(self):
        """Check IDs should be unique across all categories."""
        analysis = {"scan_time_ms": 100, "total_files_scanned": 10, "findings": []}
        ground_truth = {"expected": {}, "thresholds": {}}

        accuracy = run_accuracy_checks(analysis, ground_truth)
        coverage = run_coverage_checks(analysis, ground_truth)
        detection = run_detection_checks(analysis, ground_truth)
        performance = run_performance_checks(analysis, ground_truth)

        all_ids = [r.check_id for r in accuracy + coverage + detection + performance]
        assert len(all_ids) == len(set(all_ids)), "Duplicate check IDs found"

    def test_check_categories_prefixes(self):
        """Check IDs should have correct prefixes."""
        analysis = {"scan_time_ms": 100, "total_files_scanned": 10, "findings": []}
        ground_truth = {"expected": {}, "thresholds": {}}

        accuracy = run_accuracy_checks(analysis, ground_truth)
        coverage = run_coverage_checks(analysis, ground_truth)
        detection = run_detection_checks(analysis, ground_truth)
        performance = run_performance_checks(analysis, ground_truth)

        assert all(r.check_id.startswith("LA-") for r in accuracy)
        assert all(r.check_id.startswith("LC-") for r in coverage)
        assert all(r.check_id.startswith("LD-") for r in detection)
        assert all(r.check_id.startswith("LP-") for r in performance)
