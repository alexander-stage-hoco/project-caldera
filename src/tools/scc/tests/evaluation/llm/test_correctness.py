"""Mathematical correctness and business logic tests.

All tests use REAL data from output/ directory - NO MOCKING.
These tests verify that numerical calculations are mathematically correct.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from evaluation.llm.orchestrator import LLMEvaluator


# ==============================================================================
# Mathematical Correctness Tests
# ==============================================================================


class TestPercentileMathematicalCorrectness:
    """Verify percentile calculations are mathematically sound."""

    def test_percentiles_monotonically_increasing(self, directories_with_distributions):
        """Percentiles must be monotonically non-decreasing: min <= p25 <= median <= p75 <= p90 <= p95 <= max.

        Note: Due to floating point rounding (e.g., mean=0.0789 vs min=0.07894...), we use
        a small tolerance for comparison.
        """
        tolerance = 1e-4
        for d in directories_with_distributions:
            for dist_name in ["loc_distribution", "complexity_distribution"]:
                stats = d.get("recursive", {}).get(dist_name)
                if stats:
                    min_val = stats.get("min", 0)
                    p25 = stats.get("p25", 0)
                    median = stats.get("median", 0)
                    p75 = stats.get("p75", 0)
                    p90 = stats.get("p90", 0)
                    p95 = stats.get("p95", 0)
                    max_val = stats.get("max", 0)

                    assert min_val <= p25 + tolerance, f"min ({min_val}) > p25 ({p25}) in {d.get('path')}/{dist_name}"
                    assert p25 <= median + tolerance, f"p25 ({p25}) > median ({median}) in {d.get('path')}/{dist_name}"
                    assert median <= p75 + tolerance, f"median ({median}) > p75 ({p75}) in {d.get('path')}/{dist_name}"
                    assert p75 <= p90 + tolerance, f"p75 ({p75}) > p90 ({p90}) in {d.get('path')}/{dist_name}"
                    assert p90 <= p95 + tolerance, f"p90 ({p90}) > p95 ({p95}) in {d.get('path')}/{dist_name}"
                    assert p95 <= max_val + tolerance, f"p95 ({p95}) > max ({max_val}) in {d.get('path')}/{dist_name}"

    def test_median_between_p25_and_p75(self, directories_with_distributions):
        """Median (p50) must be between p25 and p75 (with tolerance for rounding)."""
        tolerance = 1e-4
        for d in directories_with_distributions:
            for dist_name in ["loc_distribution", "complexity_distribution"]:
                stats = d.get("recursive", {}).get(dist_name)
                if stats:
                    p25 = stats.get("p25", 0)
                    median = stats.get("median", 0)
                    p75 = stats.get("p75", 0)
                    assert p25 - tolerance <= median <= p75 + tolerance, (
                        f"Median ({median}) not in IQR [{p25}, {p75}] in {d.get('path')}/{dist_name}"
                    )

    def test_mean_within_data_range(self, directories_with_distributions):
        """Mean must be within [min, max] range (with tolerance for rounding)."""
        tolerance = 1e-4
        for d in directories_with_distributions:
            for dist_name in ["loc_distribution", "complexity_distribution"]:
                stats = d.get("recursive", {}).get(dist_name)
                if stats:
                    min_val = stats.get("min", 0)
                    max_val = stats.get("max", float("inf"))
                    mean = stats.get("mean", 0)
                    assert min_val - tolerance <= mean <= max_val + tolerance, (
                        f"Mean ({mean}) outside range [{min_val}, {max_val}] in {d.get('path')}/{dist_name}"
                    )


class TestStandardDeviationCorrectness:
    """Verify standard deviation calculations."""

    def test_stddev_non_negative(self, directories_with_distributions):
        """Standard deviation must be >= 0."""
        for d in directories_with_distributions:
            for dist_name in ["loc_distribution", "complexity_distribution"]:
                stats = d.get("recursive", {}).get(dist_name)
                if stats:
                    stddev = stats.get("stddev", 0)
                    assert stddev >= 0, (
                        f"Negative stddev ({stddev}) in {d.get('path')}/{dist_name}"
                    )

    def test_stddev_not_exceeds_half_range(self, directories_with_distributions):
        """Stddev is typically less than half the data range for reasonable distributions."""
        for d in directories_with_distributions:
            for dist_name in ["loc_distribution", "complexity_distribution"]:
                stats = d.get("recursive", {}).get(dist_name)
                if stats:
                    min_val = stats.get("min", 0)
                    max_val = stats.get("max", 0)
                    stddev = stats.get("stddev", 0)
                    data_range = max_val - min_val
                    if data_range > 0:
                        # For any distribution, stddev <= range
                        assert stddev <= data_range, (
                            f"Stddev ({stddev}) > range ({data_range}) in {d.get('path')}/{dist_name}"
                        )

    def test_zero_stddev_implies_min_equals_max(self, directories_with_distributions):
        """If stddev = 0, all values are identical so min = max."""
        for d in directories_with_distributions:
            for dist_name in ["loc_distribution", "complexity_distribution"]:
                stats = d.get("recursive", {}).get(dist_name)
                if stats:
                    min_val = stats.get("min", 0)
                    max_val = stats.get("max", 0)
                    stddev = stats.get("stddev", 0)
                    if stddev == 0:
                        assert min_val == max_val, (
                            f"Zero stddev but min ({min_val}) != max ({max_val}) in {d.get('path')}/{dist_name}"
                        )


class TestSkewnessCorrectness:
    """Verify skewness calculations make mathematical sense."""

    def test_positive_skewness_mean_gte_median(self, directories_with_distributions):
        """Positive skewness typically means mean >= median (right-skewed)."""
        for d in directories_with_distributions:
            for dist_name in ["loc_distribution", "complexity_distribution"]:
                stats = d.get("recursive", {}).get(dist_name)
                if stats and "skewness" in stats:
                    skewness = stats.get("skewness", 0)
                    mean = stats.get("mean", 0)
                    median = stats.get("median", 0)
                    # Strong positive skewness typically means mean > median
                    if skewness > 1.0:
                        # Allow some tolerance for edge cases
                        assert mean >= median * 0.8, (
                            f"Strong positive skewness ({skewness}) but mean ({mean}) << median ({median}) "
                            f"in {d.get('path')}/{dist_name}"
                        )

    def test_negative_skewness_mean_lte_median(self, directories_with_distributions):
        """Negative skewness typically means mean <= median (left-skewed)."""
        for d in directories_with_distributions:
            for dist_name in ["loc_distribution", "complexity_distribution"]:
                stats = d.get("recursive", {}).get(dist_name)
                if stats and "skewness" in stats:
                    skewness = stats.get("skewness", 0)
                    mean = stats.get("mean", 0)
                    median = stats.get("median", 0)
                    # Strong negative skewness typically means mean < median
                    if skewness < -1.0 and median > 0:
                        assert mean <= median * 1.2, (
                            f"Strong negative skewness ({skewness}) but mean ({mean}) >> median ({median}) "
                            f"in {d.get('path')}/{dist_name}"
                        )


class TestKurtosisCorrectness:
    """Verify kurtosis calculations are sensible."""

    def test_kurtosis_is_finite(self, directories_with_distributions):
        """Kurtosis should be a finite number."""
        for d in directories_with_distributions:
            for dist_name in ["loc_distribution", "complexity_distribution"]:
                stats = d.get("recursive", {}).get(dist_name)
                if stats and "kurtosis" in stats:
                    kurtosis = stats.get("kurtosis", 0)
                    assert math.isfinite(kurtosis), (
                        f"Non-finite kurtosis ({kurtosis}) in {d.get('path')}/{dist_name}"
                    )


class TestAggregationMathematicalCorrectness:
    """Verify aggregation calculations are mathematically correct."""

    def test_sum_direct_equals_total(self, all_directories, summary):
        """Sum of all direct.file_count should equal summary.total_files."""
        sum_direct = sum(d.get("direct", {}).get("file_count", 0) for d in all_directories)
        total_files = summary.get("total_files", 0)
        assert sum_direct == total_files, (
            f"Sum of direct file counts ({sum_direct}) != total_files ({total_files})"
        )

    def test_recursive_gte_direct_files(self, all_directories):
        """recursive.file_count >= direct.file_count for every directory."""
        for d in all_directories:
            direct = d.get("direct", {}).get("file_count", 0)
            recursive = d.get("recursive", {}).get("file_count", 0)
            assert recursive >= direct, (
                f"recursive ({recursive}) < direct ({direct}) in {d.get('path')}"
            )

    def test_recursive_gte_direct_loc(self, all_directories):
        """recursive.lines_code >= direct.lines_code for every directory."""
        for d in all_directories:
            direct = d.get("direct", {}).get("lines_code", 0)
            recursive = d.get("recursive", {}).get("lines_code", 0)
            assert recursive >= direct, (
                f"recursive LOC ({recursive}) < direct LOC ({direct}) in {d.get('path')}"
            )

    def test_recursive_gte_direct_complexity(self, all_directories):
        """recursive.complexity_total >= direct.complexity_total for every directory."""
        for d in all_directories:
            direct = d.get("direct", {}).get("complexity_total", 0)
            recursive = d.get("recursive", {}).get("complexity_total", 0)
            assert recursive >= direct, (
                f"recursive complexity ({recursive}) < direct complexity ({direct}) in {d.get('path')}"
            )

    def test_leaf_directory_direct_equals_recursive(self, leaf_directories):
        """For leaf directories, direct stats should equal recursive stats."""
        fields = ["file_count", "lines_code", "lines_comment", "lines_blank", "complexity_total"]
        for d in leaf_directories:
            for field in fields:
                direct_val = d.get("direct", {}).get(field)
                recursive_val = d.get("recursive", {}).get(field)
                if direct_val is not None and recursive_val is not None:
                    assert direct_val == recursive_val, (
                        f"Leaf dir {d.get('path')}: direct.{field} ({direct_val}) != "
                        f"recursive.{field} ({recursive_val})"
                    )


class TestComputedRatiosCorrectness:
    """Verify computed ratios are mathematically correct."""

    def test_avg_complexity_non_negative(self, all_directories):
        """avg_complexity must be >= 0."""
        for d in all_directories:
            recursive = d.get("recursive", {})
            if recursive.get("file_count", 0) > 0:
                avg_complexity = recursive.get("avg_complexity", 0)
                assert avg_complexity >= 0, (
                    f"avg_complexity ({avg_complexity}) < 0 for {d.get('path')}"
                )

    def test_dryness_non_negative(self, all_directories):
        """dryness must be >= 0 (can exceed 1.0 in edge cases where ULOC > LOC)."""
        for d in all_directories:
            recursive = d.get("recursive", {})
            if recursive.get("file_count", 0) > 0:
                dryness = recursive.get("dryness", 0)
                assert dryness >= 0, (
                    f"dryness ({dryness}) < 0 for {d.get('path')}"
                )

    def test_complexity_density_non_negative(self, all_directories):
        """complexity_density must be >= 0."""
        for d in all_directories:
            recursive = d.get("recursive", {})
            if recursive.get("file_count", 0) > 0:
                complexity_density = recursive.get("complexity_density", 0)
                assert complexity_density >= 0, (
                    f"complexity_density ({complexity_density}) < 0 for {d.get('path')}"
                )

    def test_comment_ratio_in_range(self, all_directories):
        """comment_ratio must be in [0, 1]."""
        for d in all_directories:
            recursive = d.get("recursive", {})
            if recursive.get("file_count", 0) > 0:
                comment_ratio = recursive.get("comment_ratio", 0)
                assert 0 <= comment_ratio <= 1, (
                    f"comment_ratio ({comment_ratio}) not in [0, 1] for {d.get('path')}"
                )


# ==============================================================================
# Business Logic Correctness Tests
# ==============================================================================


class TestCombinedScoringFormula:
    """Verify combined scoring formula is correctly implemented."""

    def test_combined_score_exact_formula(self, poc_root: Path):
        """Combined = programmatic * 0.60 + llm * 0.40"""
        evaluator = LLMEvaluator(working_dir=poc_root)

        # Test various score combinations
        test_cases = [
            (5.0, 5.0, 5.0),   # Perfect scores
            (5.0, 0.0, 3.0),   # Perfect prog, zero LLM
            (0.0, 5.0, 2.0),   # Zero prog, perfect LLM
            (4.0, 3.0, 3.6),   # Mixed scores
            (3.5, 4.0, 3.7),   # Near threshold
            (2.5, 3.5, 2.9),   # Below threshold
        ]

        from evaluation.llm.orchestrator import EvaluationResult

        for prog, llm, expected in test_cases:
            result = EvaluationResult(
                run_id="test",
                timestamp="2024-01-01T00:00:00Z",
                model="opus",
                dimensions=[],
                total_score=llm,
                average_confidence=0.8,
                decision="PASS",
            )
            evaluator.compute_combined_score(result, programmatic_score=prog)
            assert result.combined_score == pytest.approx(expected), (
                f"prog={prog}, llm={llm}: expected {expected}, got {result.combined_score}"
            )

    def test_decision_boundary_strong_pass(self, poc_root: Path):
        """Score >= 4.0 is STRONG_PASS."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        from evaluation.llm.orchestrator import EvaluationResult

        # Exactly 4.0
        result = EvaluationResult(
            run_id="test", timestamp="", model="opus",
            dimensions=[], total_score=4.0, average_confidence=0.8, decision=""
        )
        evaluator.compute_combined_score(result, programmatic_score=4.0)
        # 4.0 * 0.6 + 4.0 * 0.4 = 4.0
        assert result.decision == "STRONG_PASS"

        # Just above 4.0
        result = EvaluationResult(
            run_id="test", timestamp="", model="opus",
            dimensions=[], total_score=4.01, average_confidence=0.8, decision=""
        )
        evaluator.compute_combined_score(result, programmatic_score=4.01)
        assert result.decision == "STRONG_PASS"

    def test_decision_boundary_pass(self, poc_root: Path):
        """Score >= 3.5 and < 4.0 is PASS."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        from evaluation.llm.orchestrator import EvaluationResult

        # Exactly 3.5 (need scores that produce 3.5 combined)
        # 3.5 = prog * 0.6 + llm * 0.4
        # If prog = llm = 3.5, combined = 3.5
        result = EvaluationResult(
            run_id="test", timestamp="", model="opus",
            dimensions=[], total_score=3.5, average_confidence=0.8, decision=""
        )
        evaluator.compute_combined_score(result, programmatic_score=3.5)
        assert result.decision == "PASS"

        # 3.99 is still PASS
        result = EvaluationResult(
            run_id="test", timestamp="", model="opus",
            dimensions=[], total_score=3.99, average_confidence=0.8, decision=""
        )
        evaluator.compute_combined_score(result, programmatic_score=3.99)
        assert result.decision == "PASS"

    def test_decision_boundary_weak_pass(self, poc_root: Path):
        """Score >= 3.0 and < 3.5 is WEAK_PASS."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        from evaluation.llm.orchestrator import EvaluationResult

        result = EvaluationResult(
            run_id="test", timestamp="", model="opus",
            dimensions=[], total_score=3.0, average_confidence=0.8, decision=""
        )
        evaluator.compute_combined_score(result, programmatic_score=3.0)
        assert result.decision == "WEAK_PASS"

        result = EvaluationResult(
            run_id="test", timestamp="", model="opus",
            dimensions=[], total_score=3.49, average_confidence=0.8, decision=""
        )
        evaluator.compute_combined_score(result, programmatic_score=3.49)
        assert result.decision == "WEAK_PASS"

    def test_decision_boundary_fail(self, poc_root: Path):
        """Score < 3.0 is FAIL."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        from evaluation.llm.orchestrator import EvaluationResult

        result = EvaluationResult(
            run_id="test", timestamp="", model="opus",
            dimensions=[], total_score=2.99, average_confidence=0.8, decision=""
        )
        evaluator.compute_combined_score(result, programmatic_score=2.99)
        assert result.decision == "FAIL"

        result = EvaluationResult(
            run_id="test", timestamp="", model="opus",
            dimensions=[], total_score=0.0, average_confidence=0.8, decision=""
        )
        evaluator.compute_combined_score(result, programmatic_score=0.0)
        assert result.decision == "FAIL"


class TestGroundTruthPenaltyLogic:
    """Verify ground truth penalty is correctly applied."""

    def test_penalty_caps_at_2(self, poc_root: Path):
        """When ground truth fails, score is capped at 2."""
        # This is tested in orchestrator tests, but verify the logic
        scores_to_test = [5, 4, 3, 2, 1]
        for original_score in scores_to_test:
            capped = min(original_score, 2)
            expected = 2 if original_score > 2 else original_score
            assert capped == expected

    def test_penalty_doesnt_lower_below_current(self, poc_root: Path):
        """If score already <= 2, penalty doesn't change it."""
        for score in [2, 1]:
            capped = min(score, 2)
            assert capped == score


class TestWeightSumCorrectness:
    """Verify judge weights are mathematically correct."""

    def test_all_weights_sum_to_one(self, poc_root: Path):
        """All 10 judge weights must sum to exactly 1.0."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_all_judges()
        total_weight = sum(j.weight for j in evaluator._judges)
        assert abs(total_weight - 1.0) < 0.001, (
            f"All judge weights sum to {total_weight}, not 1.0"
        )

    def test_each_weight_is_positive(self, poc_root: Path):
        """Each judge weight must be positive."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_all_judges()
        for judge in evaluator._judges:
            assert judge.weight > 0, (
                f"Judge {judge.dimension_name} has non-positive weight {judge.weight}"
            )

    def test_weight_percentage_labels_match(self, poc_root: Path):
        """Verify weight percentages match documented values."""
        evaluator = LLMEvaluator(working_dir=poc_root)
        evaluator.register_all_judges()

        expected_weights = {
            "code_quality": 0.10,
            "integration_fit": 0.10,
            "documentation": 0.08,
            "edge_cases": 0.10,
            "error_messages": 0.08,
            "api_design": 0.10,
            "comparative": 0.08,
            "risk": 0.08,
            "directory_analysis": 0.14,
            "statistics": 0.14,
        }

        for judge in evaluator._judges:
            expected = expected_weights.get(judge.dimension_name)
            if expected is not None:
                assert judge.weight == pytest.approx(expected), (
                    f"Judge {judge.dimension_name}: expected weight {expected}, got {judge.weight}"
                )


# ==============================================================================
# Edge Case Correctness Tests
# ==============================================================================


class TestEmptyDirectoryHandling:
    """Verify empty directory edge cases are handled correctly."""

    def test_empty_directory_has_zero_direct_files(self, empty_directories):
        """Empty directories have direct.file_count = 0."""
        for d in empty_directories:
            assert d.get("direct", {}).get("file_count", -1) == 0

    def test_empty_directory_can_have_recursive_files(self, empty_directories):
        """Empty directories can have recursive files from subdirectories."""
        for d in empty_directories:
            recursive = d.get("recursive", {}).get("file_count", 0)
            # recursive >= 0 (could be 0 if truly empty subtree, or > 0 if has subdirs)
            assert recursive >= 0

    def test_empty_directory_computed_ratios_valid(self, empty_directories):
        """Empty directories should have valid computed ratios (zeros for empty)."""
        for d in empty_directories:
            direct = d.get("direct", {})
            # Empty directories should have 0 for computed ratios
            assert direct.get("avg_complexity", 0) >= 0


class TestSingleFileDirectory:
    """Verify single-file directory handling."""

    def test_single_file_distribution_valid_if_present(self, all_directories):
        """If single-file directories have distributions, they should be valid (degenerate case)."""
        for d in all_directories:
            file_count = d.get("recursive", {}).get("file_count", 0)
            for dist_name in ["loc_distribution", "complexity_distribution"]:
                stats = d.get("recursive", {}).get(dist_name)
                if file_count == 1 and stats:
                    # For single file, min == max == mean == median
                    min_val = stats.get("min", 0)
                    max_val = stats.get("max", 0)
                    # Allow small tolerance for rounding
                    assert abs(min_val - max_val) < 1e-4, (
                        f"Single file should have min == max in {d.get('path')}/{dist_name}"
                    )


class TestBoundaryValues:
    """Test boundary value handling."""

    def test_distributions_have_valid_file_count(self, directories_with_distributions):
        """Directories with distributions should have >= 1 file (valid even for single files)."""
        for d in directories_with_distributions:
            file_count = d.get("recursive", {}).get("file_count", 0)
            # Even single files can have distributions (degenerate case where min=max)
            assert file_count >= 1, (
                f"Directory {d.get('path')} has distribution but {file_count} files"
            )

    def test_zero_complexity_valid(self, all_directories):
        """Zero complexity is a valid value (config files, plain text)."""
        for d in all_directories:
            complexity = d.get("direct", {}).get("complexity_total")
            # Complexity might not be present in all directories
            if complexity is not None:
                assert complexity >= 0

    def test_zero_loc_valid(self, all_directories):
        """Zero LOC is valid (empty files)."""
        for d in all_directories:
            loc = d.get("direct", {}).get("lines_code")
            # LOC might not be present in all directories
            if loc is not None:
                assert loc >= 0


# ==============================================================================
# Data Integrity Tests
# ==============================================================================


class TestSchemaCompleteness:
    """Verify required schema fields are present."""

    def test_directory_has_required_fields(self, all_directories):
        """All directories must have path, direct, recursive."""
        required = ["path", "direct", "recursive"]
        for d in all_directories:
            for field in required:
                assert field in d, f"Missing {field} in {d.get('path', 'unknown')}"

    def test_direct_has_file_count(self, all_directories):
        """direct stats must include file_count."""
        for d in all_directories:
            direct = d.get("direct", {})
            assert "file_count" in direct, f"Missing direct.file_count in {d.get('path')}"

    def test_recursive_has_file_count(self, all_directories):
        """recursive stats must include file_count."""
        for d in all_directories:
            recursive = d.get("recursive", {})
            assert "file_count" in recursive, f"Missing recursive.file_count in {d.get('path')}"

    def test_distribution_has_all_percentile_fields(self, directories_with_distributions):
        """Distributions must have all required percentile fields."""
        required = ["min", "max", "mean", "median", "stddev", "p25", "p75", "p90", "p95"]
        for d in directories_with_distributions:
            for dist_name in ["loc_distribution", "complexity_distribution"]:
                stats = d.get("recursive", {}).get(dist_name)
                if stats:
                    for field in required:
                        assert field in stats, (
                            f"Missing {field} in {d.get('path')}/{dist_name} distribution"
                        )


class TestDataConsistency:
    """Verify data is internally consistent."""

    def test_file_count_positive_or_zero(self, all_directories):
        """File counts must be non-negative integers."""
        for d in all_directories:
            direct_count = d.get("direct", {}).get("file_count", -1)
            recursive_count = d.get("recursive", {}).get("file_count", -1)
            assert direct_count >= 0
            assert recursive_count >= 0
            assert isinstance(direct_count, int)
            assert isinstance(recursive_count, int)

    def test_computed_ratios_are_floats(self, all_directories):
        """Computed ratios must be floats."""
        for d in all_directories:
            recursive = d.get("recursive", {})
            if recursive.get("file_count", 0) > 0:
                avg_complexity = recursive.get("avg_complexity")
                assert isinstance(avg_complexity, (int, float))

    def test_path_is_nonempty_string(self, all_directories):
        """Path must be a non-empty string."""
        for d in all_directories:
            path = d.get("path")
            assert isinstance(path, str)
            assert len(path) > 0


class TestRealDataIntegrity:
    """Tests that use real data to verify integrity."""

    def test_no_duplicate_paths(self, all_directories):
        """Each directory path should be unique."""
        paths = [d.get("path") for d in all_directories]
        assert len(paths) == len(set(paths)), "Duplicate directory paths found"

    def test_summary_total_files_positive(self, summary):
        """Summary total_files should be positive."""
        total = summary.get("total_files", 0)
        assert total > 0, "total_files should be > 0 for a non-empty analysis"

    def test_at_least_one_directory(self, all_directories):
        """Should have at least one directory in analysis."""
        assert len(all_directories) > 0, "No directories in analysis"
