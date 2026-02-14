"""Unit tests for dotcover check modules (accuracy, coverage, invariants, performance).

Tests cover:
- accuracy.check_overall_coverage: range validation with/without ground truth
- accuracy.check_assembly_detected: expected assembly presence
- coverage.check_all_files_analyzed: type count validation
- invariants.check_covered_lte_total: all hierarchy levels
- invariants.check_percentage_bounds: 0-100 range
- invariants.check_non_negative_counts: negative value detection
- invariants.check_hierarchy_consistency: type/assembly/method refs
- performance.check_execution_time: timing thresholds
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Shared fixture: well-formed output
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_output() -> dict:
    """Output with valid coverage data at all levels."""
    return {
        "metadata": {"timing": {"total_seconds": 30}},
        "data": {
            "summary": {
                "covered_statements": 15,
                "total_statements": 20,
                "statement_coverage_pct": 75.0,
            },
            "assemblies": [
                {"name": "LibA", "covered_statements": 10, "total_statements": 12, "statement_coverage_pct": 83.3},
                {"name": "LibB", "covered_statements": 5, "total_statements": 8, "statement_coverage_pct": 62.5},
            ],
            "types": [
                {"assembly": "LibA", "namespace": "LibA.Core", "name": "Foo",
                 "covered_statements": 10, "total_statements": 12, "statement_coverage_pct": 83.3},
                {"assembly": "LibB", "namespace": None, "name": "Bar",
                 "covered_statements": 5, "total_statements": 8, "statement_coverage_pct": 62.5},
            ],
            "methods": [
                {"assembly": "LibA", "type_name": "Foo", "name": "DoStuff",
                 "covered_statements": 5, "total_statements": 6, "statement_coverage_pct": 83.3},
                {"assembly": "LibA", "type_name": "Foo", "name": "Init",
                 "covered_statements": 5, "total_statements": 6, "statement_coverage_pct": 83.3},
                {"assembly": "LibB", "type_name": "Bar", "name": "Run",
                 "covered_statements": 5, "total_statements": 8, "statement_coverage_pct": 62.5},
            ],
        },
    }


# ===========================================================================
# accuracy checks
# ===========================================================================

class TestAccuracyOverallCoverage:
    """Tests for accuracy.check_overall_coverage."""

    def test_no_ground_truth_returns_pass(self, valid_output):
        from scripts.checks.accuracy import check_overall_coverage
        result = check_overall_coverage(valid_output, None)
        assert result["status"] == "pass"
        assert "skipped" in result["message"].lower()

    def test_within_range_passes(self, valid_output):
        from scripts.checks.accuracy import check_overall_coverage
        gt = {"expected_coverage": {"overall_min": 50, "overall_max": 90}}
        result = check_overall_coverage(valid_output, gt)
        assert result["status"] == "pass"
        assert "75.0%" in result["message"]

    def test_below_range_fails(self, valid_output):
        from scripts.checks.accuracy import check_overall_coverage
        gt = {"expected_coverage": {"overall_min": 80, "overall_max": 100}}
        result = check_overall_coverage(valid_output, gt)
        assert result["status"] == "fail"

    def test_above_range_fails(self, valid_output):
        from scripts.checks.accuracy import check_overall_coverage
        gt = {"expected_coverage": {"overall_min": 0, "overall_max": 50}}
        result = check_overall_coverage(valid_output, gt)
        assert result["status"] == "fail"

    def test_exactly_at_boundary_passes(self, valid_output):
        from scripts.checks.accuracy import check_overall_coverage
        gt = {"expected_coverage": {"overall_min": 75, "overall_max": 75}}
        result = check_overall_coverage(valid_output, gt)
        assert result["status"] == "pass"


class TestAccuracyAssemblyDetected:
    """Tests for accuracy.check_assembly_detected."""

    def test_no_ground_truth_returns_pass(self, valid_output):
        from scripts.checks.accuracy import check_assembly_detected
        result = check_assembly_detected(valid_output, None)
        assert result["status"] == "pass"

    def test_all_expected_found(self, valid_output):
        from scripts.checks.accuracy import check_assembly_detected
        gt = {"expected_assemblies": [{"name": "LibA"}]}
        result = check_assembly_detected(valid_output, gt)
        assert result["status"] == "pass"

    def test_missing_assembly_fails(self, valid_output):
        from scripts.checks.accuracy import check_assembly_detected
        gt = {"expected_assemblies": [{"name": "LibA"}, {"name": "MissingLib"}]}
        result = check_assembly_detected(valid_output, gt)
        assert result["status"] == "fail"
        assert "MissingLib" in result["message"]

    def test_empty_expected_passes(self, valid_output):
        from scripts.checks.accuracy import check_assembly_detected
        gt = {"expected_assemblies": []}
        result = check_assembly_detected(valid_output, gt)
        assert result["status"] == "pass"


# ===========================================================================
# coverage checks
# ===========================================================================

class TestCoverageFilesAnalyzed:
    """Tests for coverage.check_all_files_analyzed."""

    def test_types_present_passes(self, valid_output):
        from scripts.checks.coverage import check_all_files_analyzed
        result = check_all_files_analyzed(valid_output, None)
        assert result["status"] == "pass"
        assert "2 types" in result["message"]

    def test_empty_types_warns(self):
        from scripts.checks.coverage import check_all_files_analyzed
        output = {"data": {"types": []}}
        result = check_all_files_analyzed(output, None)
        assert result["status"] == "warn"

    def test_missing_types_key_warns(self):
        from scripts.checks.coverage import check_all_files_analyzed
        output = {"data": {}}
        result = check_all_files_analyzed(output, None)
        assert result["status"] == "warn"


# ===========================================================================
# invariants checks
# ===========================================================================

class TestCoveredLteTotal:
    """Tests for invariants.check_covered_lte_total."""

    def test_valid_data_all_pass(self, valid_output):
        from scripts.checks.invariants import check_covered_lte_total
        results = check_covered_lte_total(valid_output, None)
        assert all(r["status"] == "pass" for r in results)
        # Should have 4 checks: summary, assemblies, types, methods
        assert len(results) == 4

    def test_summary_violation_detected(self):
        from scripts.checks.invariants import check_covered_lte_total
        output = {
            "data": {
                "summary": {"covered_statements": 25, "total_statements": 20},
                "assemblies": [],
                "types": [],
                "methods": [],
            },
        }
        results = check_covered_lte_total(output, None)
        summary_result = next(r for r in results if "summary" in r["check_id"])
        assert summary_result["status"] == "fail"

    def test_assembly_violation_detected(self):
        from scripts.checks.invariants import check_covered_lte_total
        output = {
            "data": {
                "summary": {"covered_statements": 5, "total_statements": 10},
                "assemblies": [{"name": "Bad", "covered_statements": 15, "total_statements": 10}],
                "types": [],
                "methods": [],
            },
        }
        results = check_covered_lte_total(output, None)
        asm_result = next(r for r in results if "assemblies" in r["check_id"])
        assert asm_result["status"] == "fail"

    def test_type_violation_detected(self):
        from scripts.checks.invariants import check_covered_lte_total
        output = {
            "data": {
                "summary": {"covered_statements": 5, "total_statements": 10},
                "assemblies": [],
                "types": [{"name": "Bad", "covered_statements": 11, "total_statements": 10}],
                "methods": [],
            },
        }
        results = check_covered_lte_total(output, None)
        type_result = next(r for r in results if "types" in r["check_id"])
        assert type_result["status"] == "fail"

    def test_method_violation_detected(self):
        from scripts.checks.invariants import check_covered_lte_total
        output = {
            "data": {
                "summary": {"covered_statements": 5, "total_statements": 10},
                "assemblies": [],
                "types": [],
                "methods": [{"name": "Bad", "covered_statements": 6, "total_statements": 5}],
            },
        }
        results = check_covered_lte_total(output, None)
        method_result = next(r for r in results if "methods" in r["check_id"])
        assert method_result["status"] == "fail"


class TestPercentageBounds:
    """Tests for invariants.check_percentage_bounds."""

    def test_valid_data_all_pass(self, valid_output):
        from scripts.checks.invariants import check_percentage_bounds
        results = check_percentage_bounds(valid_output, None)
        assert all(r["status"] == "pass" for r in results)

    def test_negative_summary_pct_fails(self):
        from scripts.checks.invariants import check_percentage_bounds
        output = {
            "data": {
                "summary": {"statement_coverage_pct": -5.0},
                "assemblies": [],
                "types": [],
                "methods": [],
            },
        }
        results = check_percentage_bounds(output, None)
        summary_result = next(r for r in results if "summary" in r["check_id"])
        assert summary_result["status"] == "fail"

    def test_over_100_pct_fails(self):
        from scripts.checks.invariants import check_percentage_bounds
        output = {
            "data": {
                "summary": {"statement_coverage_pct": 50.0},
                "assemblies": [{"name": "X", "statement_coverage_pct": 105.0}],
                "types": [],
                "methods": [],
            },
        }
        results = check_percentage_bounds(output, None)
        asm_result = next(r for r in results if "assemblies" in r["check_id"])
        assert asm_result["status"] == "fail"

    def test_type_out_of_bounds(self):
        from scripts.checks.invariants import check_percentage_bounds
        output = {
            "data": {
                "summary": {"statement_coverage_pct": 50.0},
                "assemblies": [],
                "types": [{"name": "T", "statement_coverage_pct": -1.0}],
                "methods": [],
            },
        }
        results = check_percentage_bounds(output, None)
        type_result = next(r for r in results if "types" in r["check_id"])
        assert type_result["status"] == "fail"

    def test_method_out_of_bounds(self):
        from scripts.checks.invariants import check_percentage_bounds
        output = {
            "data": {
                "summary": {"statement_coverage_pct": 50.0},
                "assemblies": [],
                "types": [],
                "methods": [{"name": "M", "statement_coverage_pct": 200.0}],
            },
        }
        results = check_percentage_bounds(output, None)
        method_result = next(r for r in results if "methods" in r["check_id"])
        assert method_result["status"] == "fail"


class TestNonNegativeCounts:
    """Tests for invariants.check_non_negative_counts."""

    def test_valid_data_all_pass(self, valid_output):
        from scripts.checks.invariants import check_non_negative_counts
        results = check_non_negative_counts(valid_output, None)
        assert all(r["status"] == "pass" for r in results)

    def test_negative_summary_covered(self):
        from scripts.checks.invariants import check_non_negative_counts
        output = {
            "data": {
                "summary": {"covered_statements": -1, "total_statements": 10},
                "assemblies": [],
                "types": [],
                "methods": [],
            },
        }
        results = check_non_negative_counts(output, None)
        summary_result = next(r for r in results if "summary" in r["check_id"])
        assert summary_result["status"] == "fail"

    def test_negative_assembly_total(self):
        from scripts.checks.invariants import check_non_negative_counts
        output = {
            "data": {
                "summary": {"covered_statements": 0, "total_statements": 0},
                "assemblies": [{"name": "X", "covered_statements": 0, "total_statements": -5}],
                "types": [],
                "methods": [],
            },
        }
        results = check_non_negative_counts(output, None)
        asm_result = next(r for r in results if "assemblies" in r["check_id"])
        assert asm_result["status"] == "fail"

    def test_negative_type_covered(self):
        from scripts.checks.invariants import check_non_negative_counts
        output = {
            "data": {
                "summary": {"covered_statements": 0, "total_statements": 0},
                "assemblies": [],
                "types": [{"name": "T", "covered_statements": -3, "total_statements": 10}],
                "methods": [],
            },
        }
        results = check_non_negative_counts(output, None)
        type_result = next(r for r in results if "types" in r["check_id"])
        assert type_result["status"] == "fail"

    def test_negative_method_total(self):
        from scripts.checks.invariants import check_non_negative_counts
        output = {
            "data": {
                "summary": {"covered_statements": 0, "total_statements": 0},
                "assemblies": [],
                "types": [],
                "methods": [{"name": "M", "covered_statements": 0, "total_statements": -2}],
            },
        }
        results = check_non_negative_counts(output, None)
        method_result = next(r for r in results if "methods" in r["check_id"])
        assert method_result["status"] == "fail"


class TestHierarchyConsistency:
    """Tests for invariants.check_hierarchy_consistency."""

    def test_valid_hierarchy_all_pass(self, valid_output):
        from scripts.checks.invariants import check_hierarchy_consistency
        results = check_hierarchy_consistency(valid_output, None)
        assert all(r["status"] == "pass" for r in results)
        # 3 checks: types->assemblies, methods->types, methods->assemblies
        assert len(results) == 3

    def test_type_references_invalid_assembly(self):
        from scripts.checks.invariants import check_hierarchy_consistency
        output = {
            "data": {
                "assemblies": [{"name": "LibA"}],
                "types": [{"assembly": "NonExistent", "name": "Foo", "namespace": None}],
                "methods": [],
            },
        }
        results = check_hierarchy_consistency(output, None)
        type_result = next(r for r in results if "types_to_assemblies" in r["check_id"])
        assert type_result["status"] == "fail"

    def test_method_references_invalid_type(self):
        from scripts.checks.invariants import check_hierarchy_consistency
        output = {
            "data": {
                "assemblies": [{"name": "LibA"}],
                "types": [{"assembly": "LibA", "name": "Foo", "namespace": None}],
                "methods": [{"assembly": "LibA", "type_name": "NonExistent", "name": "Run"}],
            },
        }
        results = check_hierarchy_consistency(output, None)
        method_type_result = next(r for r in results if "methods_to_types" in r["check_id"])
        assert method_type_result["status"] == "fail"

    def test_method_references_invalid_assembly(self):
        from scripts.checks.invariants import check_hierarchy_consistency
        output = {
            "data": {
                "assemblies": [{"name": "LibA"}],
                "types": [{"assembly": "LibA", "name": "Foo", "namespace": None}],
                "methods": [{"assembly": "BadAsm", "type_name": "Foo", "name": "Run"}],
            },
        }
        results = check_hierarchy_consistency(output, None)
        method_asm_result = next(r for r in results if "methods_to_assemblies" in r["check_id"])
        assert method_asm_result["status"] == "fail"

    def test_empty_data_all_pass(self):
        from scripts.checks.invariants import check_hierarchy_consistency
        output = {
            "data": {
                "assemblies": [],
                "types": [],
                "methods": [],
            },
        }
        results = check_hierarchy_consistency(output, None)
        assert all(r["status"] == "pass" for r in results)

    def test_namespace_qualified_type_match(self):
        """Methods can reference types by just name or namespace.name."""
        from scripts.checks.invariants import check_hierarchy_consistency
        output = {
            "data": {
                "assemblies": [{"name": "Lib"}],
                "types": [{"assembly": "Lib", "name": "Calc", "namespace": "Lib.Core"}],
                "methods": [{"assembly": "Lib", "type_name": "Calc", "name": "Add"}],
            },
        }
        results = check_hierarchy_consistency(output, None)
        assert all(r["status"] == "pass" for r in results)


# ===========================================================================
# performance checks
# ===========================================================================

class TestExecutionTime:
    """Tests for performance.check_execution_time."""

    def test_fast_execution_passes(self):
        from scripts.checks.performance import check_execution_time
        output = {"metadata": {"timing": {"total_seconds": 30}}}
        result = check_execution_time(output, None)
        assert result["status"] == "pass"
        assert "30.0s" in result["message"]

    def test_medium_execution_warns(self):
        from scripts.checks.performance import check_execution_time
        output = {"metadata": {"timing": {"total_seconds": 200}}}
        result = check_execution_time(output, None)
        assert result["status"] == "warn"

    def test_slow_execution_fails(self):
        from scripts.checks.performance import check_execution_time
        output = {"metadata": {"timing": {"total_seconds": 400}}}
        result = check_execution_time(output, None)
        assert result["status"] == "fail"

    def test_no_timing_data_passes(self):
        from scripts.checks.performance import check_execution_time
        output = {"metadata": {}}
        result = check_execution_time(output, None)
        assert result["status"] == "pass"
        assert "not recorded" in result["message"].lower() or "not available" in result["message"].lower()

    def test_no_metadata_passes(self):
        from scripts.checks.performance import check_execution_time
        output = {}
        result = check_execution_time(output, None)
        assert result["status"] == "pass"

    def test_invalid_timing_value_warns(self):
        from scripts.checks.performance import check_execution_time
        output = {"metadata": {"timing": {"total_seconds": "not_a_number"}}}
        result = check_execution_time(output, None)
        assert result["status"] == "warn"
        assert "invalid" in result["message"].lower()

    def test_exactly_at_pass_threshold(self):
        from scripts.checks.performance import check_execution_time, THRESHOLD_PASS_SECONDS
        output = {"metadata": {"timing": {"total_seconds": THRESHOLD_PASS_SECONDS}}}
        result = check_execution_time(output, None)
        # Exactly at threshold is NOT < threshold, so should warn
        assert result["status"] == "warn"

    def test_exactly_at_warn_threshold(self):
        from scripts.checks.performance import check_execution_time, THRESHOLD_WARN_SECONDS
        output = {"metadata": {"timing": {"total_seconds": THRESHOLD_WARN_SECONDS}}}
        result = check_execution_time(output, None)
        # Exactly at warn threshold is NOT < threshold, so should fail
        assert result["status"] == "fail"

    def test_zero_seconds_passes(self):
        from scripts.checks.performance import check_execution_time
        output = {"metadata": {"timing": {"total_seconds": 0}}}
        result = check_execution_time(output, None)
        assert result["status"] == "pass"

    def test_float_timing_value(self):
        from scripts.checks.performance import check_execution_time
        output = {"metadata": {"timing": {"total_seconds": 45.7}}}
        result = check_execution_time(output, None)
        assert result["status"] == "pass"
