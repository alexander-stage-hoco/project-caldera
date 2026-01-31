"""Tests for metrics calculation functions."""

import math
import sys
from pathlib import Path

import pytest

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from function_analyzer import (
    compute_distribution,
    compute_gini,
    compute_skewness,
    compute_kurtosis,
    compute_theil,
    compute_hoover,
    compute_top_share,
    compute_bottom_share,
    compute_palma,
    compute_directory_stats,
    Distribution,
    FunctionInfo,
    FileInfo,
)


class TestDistributionBasics:
    """Tests for basic distribution statistics."""

    def test_empty_list(self):
        """Test distribution with empty list."""
        dist = compute_distribution([])
        assert dist.count == 0
        assert dist.mean == 0.0
        assert dist.min == 0.0
        assert dist.max == 0.0

    def test_single_value(self):
        """Test distribution with single value."""
        dist = compute_distribution([5])
        assert dist.count == 1
        assert dist.min == 5
        assert dist.max == 5
        assert dist.mean == 5
        assert dist.median == 5
        assert dist.stddev == 0.0  # No variation with single value

    def test_basic_statistics(self, sample_ccn_values):
        """Test basic statistics computation."""
        dist = compute_distribution(sample_ccn_values)

        assert dist.count == 10
        assert dist.min == 1
        assert dist.max == 25
        # Mean of [1, 1, 1, 2, 3, 5, 8, 10, 15, 25] = 71/10 = 7.1
        assert abs(dist.mean - 7.1) < 0.01
        # Median of sorted list is average of 5th and 6th elements (3+5)/2 = 4
        assert dist.median == 4.0
        assert dist.stddev > 0

    def test_percentiles(self, sample_ccn_values):
        """Test percentile calculations."""
        dist = compute_distribution(sample_ccn_values)

        # Percentiles should be monotonically increasing
        assert dist.p25 <= dist.p50
        assert dist.p50 <= dist.p75
        assert dist.p75 <= dist.p90
        assert dist.p90 <= dist.p95
        assert dist.p95 <= dist.p99

        # All percentiles should be within min-max range
        assert dist.min <= dist.p25 <= dist.max
        assert dist.min <= dist.p99 <= dist.max


class TestInequalityMetrics:
    """Tests for inequality metrics (Gini, Theil, Hoover)."""

    def test_gini_perfect_equality(self, equal_distribution_values):
        """Test Gini coefficient for perfect equality."""
        gini = compute_gini(equal_distribution_values)
        # Perfect equality should have Gini close to 0
        assert abs(gini) < 0.01

    def test_gini_high_inequality(self, unequal_distribution_values):
        """Test Gini coefficient for high inequality."""
        gini = compute_gini(unequal_distribution_values)
        # High inequality should have Gini > 0.5
        assert gini > 0.5
        # Gini should be <= 1
        assert gini <= 1.0

    def test_gini_empty_list(self):
        """Test Gini with empty list."""
        assert compute_gini([]) == 0.0

    def test_gini_all_zeros(self):
        """Test Gini with all zeros."""
        assert compute_gini([0, 0, 0]) == 0.0

    def test_hoover_perfect_equality(self, equal_distribution_values):
        """Test Hoover index for perfect equality."""
        hoover = compute_hoover(equal_distribution_values)
        # Perfect equality should have Hoover close to 0
        assert abs(hoover) < 0.01

    def test_hoover_high_inequality(self, unequal_distribution_values):
        """Test Hoover index for high inequality."""
        hoover = compute_hoover(unequal_distribution_values)
        # High inequality should have higher Hoover
        assert hoover > 0.3

    def test_theil_perfect_equality(self, equal_distribution_values):
        """Test Theil index for perfect equality."""
        theil = compute_theil(equal_distribution_values)
        # Perfect equality should have Theil close to 0
        assert abs(theil) < 0.01

    def test_theil_empty_list(self):
        """Test Theil with empty list."""
        assert compute_theil([]) == 0.0


class TestShareMetrics:
    """Tests for top/bottom share metrics."""

    def test_top_share(self):
        """Test top share calculation."""
        # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] - sorted
        values = list(range(1, 11))
        sorted_vals = sorted(values)

        # Top 10% (1 value) = 10, total = 55
        top_10 = compute_top_share(sorted_vals, 0.10)
        assert abs(top_10 - 10/55) < 0.01

    def test_bottom_share(self):
        """Test bottom share calculation."""
        values = list(range(1, 11))
        sorted_vals = sorted(values)

        # Bottom 50% (5 values) = 1+2+3+4+5 = 15, total = 55
        bottom_50 = compute_bottom_share(sorted_vals, 0.50)
        assert abs(bottom_50 - 15/55) < 0.01

    def test_palma_ratio(self):
        """Test Palma ratio calculation."""
        values = list(range(1, 11))
        sorted_vals = sorted(values)

        # Palma = top 10% / bottom 40%
        # Top 10% = 10, Bottom 40% = 1+2+3+4 = 10
        palma = compute_palma(sorted_vals)
        assert abs(palma - 1.0) < 0.1

    def test_palma_empty(self):
        """Test Palma with empty list."""
        assert compute_palma([]) == 0.0


class TestShapeMetrics:
    """Tests for distribution shape metrics (skewness, kurtosis)."""

    def test_skewness_symmetric(self):
        """Test skewness for symmetric distribution."""
        # Symmetric distribution should have skewness near 0
        symmetric = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        mean = sum(symmetric) / len(symmetric)
        stddev = (sum((x - mean) ** 2 for x in symmetric) / len(symmetric)) ** 0.5
        skew = compute_skewness(symmetric, mean, stddev)
        assert abs(skew) < 0.5  # Near zero for symmetric

    def test_skewness_right_skewed(self, unequal_distribution_values):
        """Test skewness for right-skewed distribution."""
        values = unequal_distribution_values
        mean = sum(values) / len(values)
        stddev = (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5
        skew = compute_skewness(values, mean, stddev)
        # Right-skewed should have positive skewness
        assert skew > 0

    def test_skewness_insufficient_data(self):
        """Test skewness with insufficient data."""
        # Need at least 3 values
        assert compute_skewness([1, 2], 1.5, 0.5) == 0.0
        assert compute_skewness([1], 1, 0) == 0.0

    def test_kurtosis_insufficient_data(self):
        """Test kurtosis with insufficient data."""
        # Need at least 4 values
        assert compute_kurtosis([1, 2, 3], 2, 1) == 0.0

    def test_cv_calculation(self, sample_ccn_values):
        """Test coefficient of variation in distribution."""
        dist = compute_distribution(sample_ccn_values)
        # CV = stddev / mean
        expected_cv = dist.stddev / dist.mean if dist.mean > 0 else 0
        assert abs(dist.cv - expected_cv) < 0.01

    def test_iqr_calculation(self, sample_ccn_values):
        """Test interquartile range calculation."""
        dist = compute_distribution(sample_ccn_values)
        # IQR = P75 - P25
        assert dist.iqr == dist.p75 - dist.p25


class TestDirectoryStats:
    """Tests for directory statistics computation."""

    def test_empty_functions(self):
        """Test stats with no functions."""
        stats = compute_directory_stats([], [])
        assert stats.file_count == 0
        assert stats.function_count == 0
        assert stats.nloc == 0

    def test_basic_directory_stats(self, sample_function_info):
        """Test basic directory stats computation."""
        functions = [sample_function_info]
        files = [FileInfo(
            path="/test/file.py",
            language="Python",
            nloc=35,
            functions=functions,
            function_count=1,
            total_ccn=8,
            avg_ccn=8.0,
            max_ccn=8,
        )]

        stats = compute_directory_stats(functions, files, ccn_threshold=10)

        assert stats.file_count == 1
        assert stats.function_count == 1
        assert stats.nloc == 35
        assert stats.ccn == 8
        assert stats.avg_ccn == 8.0
        assert stats.max_ccn == 8
        assert stats.functions_over_threshold == 0  # 8 < 10

    def test_threshold_counting(self):
        """Test counting functions over threshold."""
        functions = [
            FunctionInfo("f1", "f1", 1, 10, 10, 5, 50, 0, 9),   # CCN=5, under threshold
            FunctionInfo("f2", "f2", 11, 20, 15, 12, 60, 1, 9), # CCN=12, over threshold
            FunctionInfo("f3", "f3", 21, 30, 20, 15, 80, 2, 9), # CCN=15, over threshold
        ]
        files = [FileInfo("/test.py", "Python", 45, functions, 3, 32, 10.67, 15)]

        stats = compute_directory_stats(functions, files, ccn_threshold=10)

        assert stats.functions_over_threshold == 2
