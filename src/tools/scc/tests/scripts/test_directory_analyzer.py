"""Non-trivial correctness tests for directory_analyzer.py.

All tests verify mathematical correctness or would catch real bugs.
NO MOCKING - uses real data and real function calls.
"""

from __future__ import annotations

import statistics
import sys
from pathlib import Path

import pytest

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from directory_analyzer import (
    COCOMO_PRESETS,
    MetricDistribution,
    analyze_directories,
    compute_cocomo,
    compute_directory_stats,
    compute_kurtosis,
    compute_skewness,
)


# =============================================================================
# Helper Functions (defined here to avoid import issues)
# =============================================================================

def make_stats(
    file_count: int = 10,
    complexity_total: int = 50,
    code: int = 1000,
    lines: int = 1200,
    comment: int = 100,
    blank: int = 100,
    bytes_total: int = 50000,
    uloc: int = 800,
    languages: dict = None,
    distribution: dict = None,
) -> dict:
    """Create a stats dict for testing compute_directory_stats."""
    return {
        "file_count": file_count,
        "lines": lines,
        "code": code,
        "comment": comment,
        "blank": blank,
        "bytes": bytes_total,
        "complexity_total": complexity_total,
        "uloc": uloc,
        "languages": languages or {"Python": file_count},
        "minified_count": 0,
        "generated_count": 0,
        "distribution": distribution,
    }


def make_file(
    location: str,
    code: int = 100,
    lines: int = 120,
    comment: int = 10,
    blank: int = 10,
    complexity: int = 5,
    language: str = "Python",
) -> dict:
    """Create a file dict for testing.

    Uses snake_case field names to match the normalized output from run_scc_by_file.
    """
    return {
        "location": location,
        "filename": Path(location).name,
        "language": language,
        "lines": lines,
        "code": code,
        "comment": comment,
        "blank": blank,
        "bytes": code * 50,
        "complexity": complexity,
        "uloc": int(code * 0.8),
        "minified": False,
        "generated": False,
    }


def generate_test_files(count: int = 20, max_depth: int = 3) -> list:
    """Generate test files with various directory depths."""
    files = []
    dirs = ["src", "src/utils", "src/utils/helpers", "src/core", "tests"]

    for i in range(count):
        dir_idx = i % len(dirs)
        parent = dirs[min(dir_idx, max_depth)]
        files.append(make_file(
            location=f"{parent}/file_{i}.py",
            code=50 + (i * 10),
            complexity=2 + (i % 10),
        ))

    return files


# =============================================================================
# 1. Statistical Formula Verification Tests
# =============================================================================

class TestSkewnessCorrectness:
    """Verify skewness calculation properties and consistency."""

    def test_skewness_positive_for_right_tail(self):
        """Right-skewed distribution should have positive skewness."""
        values = [1, 1, 1, 1, 100]  # One large outlier
        mean = statistics.mean(values)
        skewness = compute_skewness(values, mean)
        assert skewness > 0, f"Right-skewed distribution should have positive skewness, got {skewness}"

    def test_skewness_negative_for_left_tail(self):
        """Left-skewed distribution should have negative skewness."""
        values = [1, 100, 100, 100, 100]  # One small outlier
        mean = statistics.mean(values)
        skewness = compute_skewness(values, mean)
        assert skewness < 0, f"Left-skewed distribution should have negative skewness, got {skewness}"

    def test_skewness_near_zero_for_symmetric(self):
        """Symmetric distribution should have skewness near zero."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        mean = statistics.mean(values)
        skewness = compute_skewness(values, mean)
        assert abs(skewness) < 0.5, f"Symmetric distribution should have near-zero skewness, got {skewness}"

    def test_skewness_zero_for_identical_values(self):
        """All identical values should have zero skewness."""
        values = [5, 5, 5, 5, 5, 5, 5, 5, 5, 5]
        mean = statistics.mean(values)
        skewness = compute_skewness(values, mean)
        assert skewness == 0, f"Identical values should have zero skewness, got {skewness}"

    def test_skewness_magnitude_increases_with_outlier(self):
        """Larger outliers should produce larger skewness magnitude (with larger samples)."""
        # Need larger sample to avoid saturation at small n
        base_values = list(range(1, 21))  # 1 to 20

        values_small_outlier = base_values + [50]
        values_large_outlier = base_values + [500]

        mean1 = statistics.mean(values_small_outlier)
        mean2 = statistics.mean(values_large_outlier)

        skew1 = compute_skewness(values_small_outlier, mean1)
        skew2 = compute_skewness(values_large_outlier, mean2)

        assert skew2 > skew1, f"Larger outlier should produce larger skewness: {skew2} > {skew1}"


class TestKurtosisCorrectness:
    """Verify kurtosis calculation properties and consistency."""

    def test_kurtosis_positive_for_heavy_tails(self):
        """Distribution with heavy tails should have positive excess kurtosis."""
        values = [1, 2, 2, 2, 2, 2, 2, 2, 2, 100]  # One large outlier
        mean = statistics.mean(values)
        kurtosis = compute_kurtosis(values, mean)
        assert kurtosis > 0, f"Heavy-tailed distribution should have positive kurtosis, got {kurtosis}"

    def test_kurtosis_negative_for_uniform_like(self):
        """Uniform-like distribution should have negative excess kurtosis."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        mean = statistics.mean(values)
        kurtosis = compute_kurtosis(values, mean)
        assert kurtosis < 0, f"Uniform-like distribution should have negative kurtosis, got {kurtosis}"

    def test_kurtosis_zero_for_identical_values(self):
        """All identical values should have zero kurtosis."""
        values = [5, 5, 5, 5, 5, 5, 5, 5]
        mean = statistics.mean(values)
        kurtosis = compute_kurtosis(values, mean)
        assert kurtosis == 0, f"Identical values should have zero kurtosis, got {kurtosis}"

    def test_kurtosis_consistent_with_formula(self):
        """Verify kurtosis formula: sum((x-mean)^4) / (n*std^4) - 3."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        mean = statistics.mean(values)
        std = statistics.stdev(values)
        n = len(values)

        # Manual calculation
        fourth_moment = sum((x - mean) ** 4 for x in values) / n
        expected = fourth_moment / (std ** 4) - 3

        computed = compute_kurtosis(values, mean)
        assert abs(computed - expected) < 0.001, (
            f"Kurtosis doesn't match formula: computed={computed}, expected={expected}"
        )


class TestPercentileMatchesNumpy:
    """Verify our percentile calculation matches numpy."""

    @pytest.mark.parametrize("values,percentile", [
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 25),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 50),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 75),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 90),
        (list(range(1, 101)), 25),  # 100 values
        (list(range(1, 101)), 95),
    ])
    def test_percentile_matches_numpy(self, values, percentile):
        """Verify our percentile index calculation is reasonable."""
        try:
            import numpy as np
        except ImportError:
            pytest.skip("numpy not installed")

        dist = MetricDistribution.from_values(values)

        # Get our computed percentile
        if percentile == 25:
            computed = dist.p25
        elif percentile == 50:
            computed = dist.median
        elif percentile == 75:
            computed = dist.p75
        elif percentile == 90:
            computed = dist.p90
        elif percentile == 95:
            computed = dist.p95
        else:
            pytest.skip(f"Unknown percentile {percentile}")

        # Our implementation uses simple index-based percentiles
        # numpy uses interpolation, so allow reasonable tolerance
        expected = np.percentile(values, percentile)

        # Allow 10% tolerance for different interpolation methods
        tolerance = max(abs(expected) * 0.1, 1.0)
        assert abs(computed - expected) < tolerance, (
            f"Percentile {percentile} mismatch: computed={computed}, numpy={expected}"
        )


class TestStddevMatchesStatistics:
    """Verify stddev uses sample formula (N-1 denominator)."""

    def test_stddev_uses_sample_formula(self):
        """Stddev should match statistics.stdev (N-1 denominator)."""
        values = [2, 4, 4, 4, 5, 5, 7, 9]  # Known dataset
        dist = MetricDistribution.from_values(values)

        expected = statistics.stdev(values)  # Uses N-1
        assert abs(dist.stddev - expected) < 0.0001, (
            f"Stddev mismatch: computed={dist.stddev}, expected={expected}"
        )

    def test_stddev_single_value_is_zero(self):
        """Single value should have stddev=0."""
        dist = MetricDistribution.from_values([42])
        assert dist.stddev == 0


# =============================================================================
# 2. COCOMO Formula Verification Tests
# =============================================================================

class TestCOCOMOEffortFormula:
    """Verify COCOMO effort formula: effort = a * KLOC^b * EAF."""

    def test_cocomo_effort_formula_exact(self):
        """Verify effort = a * KLOC^b * EAF with known values."""
        params = COCOMO_PRESETS["sme"]  # a=3.0, b=1.12, eaf=1.0
        result = compute_cocomo(10.0, params)  # 10 KLOC

        # Manual calculation
        expected_effort = params["a"] * (10.0 ** params["b"]) * params["eaf"]
        assert abs(result["effort_person_months"] - expected_effort) < 0.1, (
            f"Effort mismatch: computed={result['effort_person_months']}, expected={expected_effort}"
        )

    @pytest.mark.parametrize("preset_name", list(COCOMO_PRESETS.keys()))
    def test_cocomo_all_presets_produce_positive_effort(self, preset_name):
        """All presets should produce positive effort for positive KLOC."""
        params = COCOMO_PRESETS[preset_name]
        result = compute_cocomo(5.0, params)

        # Open source has avg_wage=0, so cost will be 0, but effort should be positive
        assert result["effort_person_months"] > 0


class TestCOCOMOScheduleFormula:
    """Verify COCOMO schedule formula: schedule = c * effort^d."""

    def test_cocomo_schedule_formula_exact(self):
        """Verify schedule = c * effort^d with known values."""
        params = COCOMO_PRESETS["sme"]  # c=2.5, d=0.35
        result = compute_cocomo(10.0, params)

        effort = result["effort_person_months"]
        expected_schedule = params["c"] * (effort ** params["d"])
        assert abs(result["schedule_months"] - expected_schedule) < 0.1, (
            f"Schedule mismatch: computed={result['schedule_months']}, expected={expected_schedule}"
        )


class TestCOCOMOCostFormula:
    """Verify COCOMO cost formula: cost = effort * (wage/12) * overhead."""

    def test_cocomo_cost_formula_exact(self):
        """Verify cost = effort * (wage/12) * overhead."""
        params = COCOMO_PRESETS["sme"]  # avg_wage=120000, overhead=2.4
        result = compute_cocomo(10.0, params)

        effort = result["effort_person_months"]
        expected_cost = effort * (params["avg_wage"] / 12) * params["overhead"]
        # Allow 0.1% tolerance for rounding
        tolerance = max(100.0, expected_cost * 0.001)
        assert abs(result["cost"] - expected_cost) < tolerance, (
            f"Cost mismatch: computed={result['cost']}, expected={expected_cost}"
        )

    def test_cocomo_zero_kloc_returns_zeros(self):
        """Zero KLOC should return all zeros."""
        params = COCOMO_PRESETS["sme"]
        result = compute_cocomo(0, params)

        assert result["effort_person_months"] == 0
        assert result["schedule_months"] == 0
        assert result["cost"] == 0
        assert result["people"] == 0


# =============================================================================
# 3. Aggregation Invariant Tests
# =============================================================================

class TestAggregationInvariants:
    """Verify mathematical properties that MUST hold for aggregation."""

    def test_recursive_is_superset_of_direct(self):
        """recursive stats >= direct stats for all directories."""
        files = [
            make_file("src/a.py", code=100, complexity=10),
            make_file("src/utils/b.py", code=200, complexity=20),
            make_file("src/utils/helpers/c.py", code=300, complexity=30),
        ]
        result = analyze_directories(files)

        for d in result["directories"]:
            direct = d["direct"]
            recursive = d["recursive"]

            assert recursive["file_count"] >= direct["file_count"], (
                f"Directory {d['path']}: recursive.file_count < direct.file_count"
            )
            assert recursive["code"] >= direct["code"], (
                f"Directory {d['path']}: recursive.code < direct.code"
            )
            assert recursive["complexity_total"] >= direct["complexity_total"], (
                f"Directory {d['path']}: recursive.complexity < direct.complexity"
            )

    def test_sum_of_direct_equals_total(self):
        """Sum of all direct.file_count must equal summary.total_files."""
        files = generate_test_files(count=50, max_depth=3)
        result = analyze_directories(files)

        sum_direct = sum(d["direct"]["file_count"] for d in result["directories"])
        total_files = result["summary"]["total_files"]

        assert sum_direct == total_files, (
            f"sum(direct.file_count)={sum_direct} != total_files={total_files}"
        )

    def test_leaf_directories_have_direct_equals_recursive(self):
        """Directories with no subdirectories: direct == recursive."""
        files = [
            make_file("src/a.py", code=100),
            make_file("src/utils/b.py", code=200),
            make_file("src/utils/helpers/c.py", code=300),
        ]
        result = analyze_directories(files)

        for d in result["directories"]:
            if not d["subdirectories"]:  # Leaf directory
                assert d["direct"]["file_count"] == d["recursive"]["file_count"], (
                    f"Leaf dir {d['path']}: direct != recursive file_count"
                )
                assert d["direct"]["code"] == d["recursive"]["code"], (
                    f"Leaf dir {d['path']}: direct != recursive code"
                )

    def test_parent_recursive_includes_child_files(self):
        """Parent directory recursive count includes all child files."""
        files = [
            make_file("src/a.py", code=100),
            make_file("src/utils/b.py", code=200),
            make_file("src/utils/helpers/c.py", code=300),
        ]
        result = analyze_directories(files)

        # Find src directory
        src_dir = next((d for d in result["directories"] if d["path"] == "src"), None)
        assert src_dir is not None, "src directory not found"

        # src should have 1 direct file and 3 recursive files
        assert src_dir["direct"]["file_count"] == 1
        assert src_dir["recursive"]["file_count"] == 3


# =============================================================================
# 4. Integration Tests with Real Output
# =============================================================================

class TestRealOutputInvariants:
    """Validate all invariants on real production output."""

    def test_real_output_sum_invariant(self, all_directories, summary):
        """Sum of direct.file_count equals total_files."""
        if not all_directories:
            pytest.skip("No directories in real output")

        sum_direct = sum(d["direct"]["file_count"] for d in all_directories)
        total_files = summary.get("total_files", 0)

        assert sum_direct == total_files, (
            f"sum(direct.file_count)={sum_direct} != total_files={total_files}"
        )

    def test_real_output_recursive_gte_direct(self, all_directories):
        """recursive >= direct for all directories."""
        for d in all_directories:
            direct = d["direct"]["file_count"]
            recursive = d["recursive"]["file_count"]
            assert recursive >= direct, (
                f"Directory {d['path']}: recursive ({recursive}) < direct ({direct})"
            )

    def test_real_output_computed_ratios_valid(self, all_directories):
        """Computed ratios are in valid ranges."""
        for d in all_directories:
            recursive = d["recursive"]
            if recursive["file_count"] > 0:
                # avg_complexity should be non-negative
                assert recursive["avg_complexity"] >= 0, (
                    f"Directory {d['path']}: avg_complexity < 0"
                )
                # dryness should be non-negative (ULOC can exceed LOC in edge cases)
                assert recursive["dryness"] >= 0, (
                    f"Directory {d['path']}: dryness {recursive['dryness']} < 0"
                )
                # comment_ratio should be in [0, 1]
                assert 0 <= recursive["comment_ratio"] <= 1, (
                    f"Directory {d['path']}: comment_ratio {recursive['comment_ratio']} out of range"
                )

    def test_real_output_percentiles_monotonic(self, all_directories):
        """Percentiles are monotonic: p25 <= median <= p75 <= p90 <= p95."""
        tolerance = 1e-4

        for d in all_directories:
            recursive = d["recursive"]
            for dist_name in ["loc_distribution", "complexity_distribution"]:
                stats = recursive.get(dist_name)
                if stats:
                    assert stats["p25"] <= stats["median"] + tolerance, (
                        f"p25 > median in {d['path']}/{dist_name}"
                    )
                    assert stats["median"] <= stats["p75"] + tolerance, (
                        f"median > p75 in {d['path']}/{dist_name}"
                    )
                    assert stats["p75"] <= stats["p90"] + tolerance, (
                        f"p75 > p90 in {d['path']}/{dist_name}"
                    )
                    assert stats["p90"] <= stats["p95"] + tolerance, (
                        f"p90 > p95 in {d['path']}/{dist_name}"
                    )

    def test_real_output_cv_and_iqr_valid(self, all_directories):
        """CV (coefficient of variation) and IQR are non-negative."""
        for d in all_directories:
            recursive = d["recursive"]
            for dist_name in ["loc_distribution", "complexity_distribution"]:
                stats = recursive.get(dist_name)
                if stats:
                    assert stats["cv"] >= 0, (
                        f"CV < 0 in {d['path']}/{dist_name}"
                    )
                    assert stats["iqr"] >= 0, (
                        f"IQR < 0 in {d['path']}/{dist_name}"
                    )
