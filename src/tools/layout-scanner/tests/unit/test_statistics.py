"""
Unit tests for statistics.py
"""

import pytest
from scripts.statistics import (
    DistributionStats,
    compute_stats,
    compute_percentile,
    compute_skewness,
    compute_kurtosis,
    compute_depth_distribution_stats,
    compute_files_per_directory_stats,
    compute_file_size_stats,
    get_statistics_capabilities,
    SCIPY_AVAILABLE,
)


class TestDistributionStats:
    """Tests for DistributionStats dataclass."""

    def test_distribution_stats_fields(self):
        """DistributionStats should have all required fields."""
        stats = DistributionStats(
            count=100,
            min=1.0,
            max=100.0,
            mean=50.5,
            std_dev=29.01,
            p25=25.75,
            p50=50.5,
            p75=75.25,
            skewness=0.0,
            kurtosis=-1.2,
        )
        assert stats.count == 100
        assert stats.min == 1.0
        assert stats.max == 100.0
        assert stats.mean == 50.5
        assert stats.std_dev == 29.01
        assert stats.p25 == 25.75
        assert stats.p50 == 50.5
        assert stats.p75 == 75.25
        assert stats.skewness == 0.0
        assert stats.kurtosis == -1.2

    def test_distribution_stats_to_dict(self):
        """DistributionStats.to_dict() should return a dictionary."""
        stats = DistributionStats(
            count=10,
            min=1.0,
            max=10.0,
            mean=5.5,
            std_dev=3.03,
            p25=3.25,
            p50=5.5,
            p75=7.75,
            skewness=0.0,
            kurtosis=-1.2,
        )
        result = stats.to_dict()
        assert isinstance(result, dict)
        assert result["count"] == 10
        assert result["mean"] == 5.5
        assert result["p50"] == 5.5

    def test_distribution_stats_optional_fields(self):
        """DistributionStats skewness and kurtosis can be None."""
        stats = DistributionStats(
            count=2,
            min=1.0,
            max=2.0,
            mean=1.5,
            std_dev=0.71,
            p25=1.25,
            p50=1.5,
            p75=1.75,
            skewness=None,
            kurtosis=None,
        )
        assert stats.skewness is None
        assert stats.kurtosis is None


class TestComputePercentile:
    """Tests for compute_percentile function."""

    def test_percentile_empty_list(self):
        """Percentile of empty list should be 0."""
        assert compute_percentile([], 50) == 0.0

    def test_percentile_single_value(self):
        """Percentile of single value should be that value."""
        assert compute_percentile([5.0], 0) == 5.0
        assert compute_percentile([5.0], 50) == 5.0
        assert compute_percentile([5.0], 100) == 5.0

    def test_percentile_two_values(self):
        """Percentile of two values should interpolate."""
        values = [0.0, 10.0]
        assert compute_percentile(values, 0) == 0.0
        assert compute_percentile(values, 50) == 5.0
        assert compute_percentile(values, 100) == 10.0

    def test_percentile_standard_distribution(self):
        """Percentile should work on standard distributions."""
        # 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
        values = list(range(1, 11))
        sorted_values = [float(v) for v in values]

        # Median
        p50 = compute_percentile(sorted_values, 50)
        assert p50 == 5.5  # Interpolated between 5 and 6

        # Min/max
        assert compute_percentile(sorted_values, 0) == 1.0
        assert compute_percentile(sorted_values, 100) == 10.0

    def test_percentile_quartiles(self):
        """Percentile should compute quartiles correctly."""
        # 100 values: 0, 1, 2, ..., 99
        values = [float(i) for i in range(100)]

        p25 = compute_percentile(values, 25)
        p50 = compute_percentile(values, 50)
        p75 = compute_percentile(values, 75)

        assert 24 <= p25 <= 25
        assert 49 <= p50 <= 50
        assert 74 <= p75 <= 75


class TestComputeStats:
    """Tests for compute_stats function."""

    def test_compute_stats_empty(self):
        """compute_stats with empty list should return zeros."""
        stats = compute_stats([])
        assert stats.count == 0
        assert stats.min == 0.0
        assert stats.max == 0.0
        assert stats.mean == 0.0
        assert stats.std_dev == 0.0
        assert stats.p25 == 0.0
        assert stats.p50 == 0.0
        assert stats.p75 == 0.0
        assert stats.skewness is None
        assert stats.kurtosis is None

    def test_compute_stats_single_value(self):
        """compute_stats with single value should have zero std_dev."""
        stats = compute_stats([5])
        assert stats.count == 1
        assert stats.min == 5.0
        assert stats.max == 5.0
        assert stats.mean == 5.0
        assert stats.std_dev == 0.0
        assert stats.p50 == 5.0
        assert stats.skewness is None  # Needs at least 3 values
        assert stats.kurtosis is None  # Needs at least 4 values

    def test_compute_stats_two_values(self):
        """compute_stats with two values should compute basic stats."""
        stats = compute_stats([0, 10])
        assert stats.count == 2
        assert stats.min == 0.0
        assert stats.max == 10.0
        assert stats.mean == 5.0
        assert stats.std_dev > 0  # Should be ~7.07
        assert stats.p50 == 5.0
        assert stats.skewness is None  # Needs at least 3 values

    def test_compute_stats_uniform(self):
        """compute_stats with uniform distribution should have known properties."""
        # Values 1-10
        values = list(range(1, 11))
        stats = compute_stats(values)

        assert stats.count == 10
        assert stats.min == 1.0
        assert stats.max == 10.0
        assert stats.mean == 5.5
        assert 2.5 < stats.std_dev < 3.5  # ~3.03 for sample std dev
        assert stats.p50 == 5.5

    def test_compute_stats_skewed(self):
        """compute_stats with skewed distribution should show positive skewness."""
        # Right-skewed distribution (many small, few large)
        values = [1, 1, 1, 1, 1, 2, 2, 3, 5, 100]
        stats = compute_stats(values)

        # Should show positive skewness (tail to right)
        if stats.skewness is not None:
            assert stats.skewness > 0

    def test_compute_stats_integers(self):
        """compute_stats should handle integers."""
        stats = compute_stats([1, 2, 3, 4, 5])
        assert stats.count == 5
        assert stats.mean == 3.0

    def test_compute_stats_floats(self):
        """compute_stats should handle floats."""
        stats = compute_stats([1.5, 2.5, 3.5, 4.5, 5.5])
        assert stats.count == 5
        assert stats.mean == 3.5

    def test_compute_stats_mixed(self):
        """compute_stats should handle mixed int/float."""
        stats = compute_stats([1, 2.5, 3, 4.5, 5])
        assert stats.count == 5
        assert stats.mean == 3.2


class TestComputeSkewness:
    """Tests for compute_skewness function."""

    def test_skewness_insufficient_data(self):
        """Skewness should be None for < 3 values."""
        assert compute_skewness([], 0, 1) is None
        assert compute_skewness([1], 1, 0) is None
        assert compute_skewness([1, 2], 1.5, 0.71) is None

    def test_skewness_zero_std(self):
        """Skewness should be None for zero std dev."""
        assert compute_skewness([1, 1, 1], 1, 0) is None

    def test_skewness_symmetric(self):
        """Skewness of symmetric distribution should be near zero."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        mean = 3.0
        std = 1.58  # Approximate

        skew = compute_skewness(values, mean, std)
        assert skew is not None
        assert -0.5 < skew < 0.5  # Should be close to 0


class TestComputeKurtosis:
    """Tests for compute_kurtosis function."""

    def test_kurtosis_insufficient_data(self):
        """Kurtosis should be None for < 4 values."""
        assert compute_kurtosis([], 0, 1) is None
        assert compute_kurtosis([1], 1, 0) is None
        assert compute_kurtosis([1, 2], 1.5, 0.71) is None
        assert compute_kurtosis([1, 2, 3], 2, 1) is None

    def test_kurtosis_zero_std(self):
        """Kurtosis should be None for zero std dev."""
        assert compute_kurtosis([1, 1, 1, 1], 1, 0) is None


class TestComputeDepthDistributionStats:
    """Tests for compute_depth_distribution_stats function."""

    def test_depth_stats_empty(self):
        """Empty distribution should return zero stats."""
        stats = compute_depth_distribution_stats({})
        assert stats.count == 0

    def test_depth_stats_single_level(self):
        """Single depth level should work."""
        stats = compute_depth_distribution_stats({0: 10})
        assert stats.count == 10
        assert stats.min == 0.0
        assert stats.max == 0.0
        assert stats.mean == 0.0
        assert stats.p50 == 0.0

    def test_depth_stats_multiple_levels(self):
        """Multiple depth levels should be aggregated."""
        # depth 0: 1 dir, depth 1: 5 dirs, depth 2: 10 dirs, depth 3: 5 dirs
        distribution = {0: 1, 1: 5, 2: 10, 3: 5}
        stats = compute_depth_distribution_stats(distribution)

        assert stats.count == 21
        assert stats.min == 0.0
        assert stats.max == 3.0
        # Mean should be weighted towards depth 2
        assert 1.5 < stats.mean < 2.5


class TestComputeFilesPerDirectoryStats:
    """Tests for compute_files_per_directory_stats function."""

    def test_files_per_dir_empty(self):
        """Empty list should return zero stats."""
        stats = compute_files_per_directory_stats([])
        assert stats.count == 0

    def test_files_per_dir_uniform(self):
        """Uniform distribution should work."""
        # 10 directories, each with 5 files
        counts = [5] * 10
        stats = compute_files_per_directory_stats(counts)

        assert stats.count == 10
        assert stats.min == 5.0
        assert stats.max == 5.0
        assert stats.mean == 5.0
        assert stats.std_dev == 0.0

    def test_files_per_dir_varied(self):
        """Varied file counts should show spread."""
        # Some empty, some with files
        counts = [0, 0, 1, 2, 5, 10, 25, 100]
        stats = compute_files_per_directory_stats(counts)

        assert stats.count == 8
        assert stats.min == 0.0
        assert stats.max == 100.0
        assert stats.std_dev > 0


class TestComputeFileSizeStats:
    """Tests for compute_file_size_stats function."""

    def test_file_size_stats_empty(self):
        """Empty list should return zero stats."""
        stats = compute_file_size_stats([])
        assert stats.count == 0

    def test_file_size_stats_typical(self):
        """Typical file sizes should work."""
        # Mix of small and large files
        sizes = [100, 500, 1000, 2000, 5000, 10000, 50000, 100000]
        stats = compute_file_size_stats(sizes)

        assert stats.count == 8
        assert stats.min == 100.0
        assert stats.max == 100000.0
        assert stats.mean > 0


class TestGetStatisticsCapabilities:
    """Tests for get_statistics_capabilities function."""

    def test_capabilities_returns_dict(self):
        """Capabilities should return a dictionary."""
        caps = get_statistics_capabilities()
        assert isinstance(caps, dict)

    def test_capabilities_has_required_keys(self):
        """Capabilities should have expected keys."""
        caps = get_statistics_capabilities()
        assert "scipy_available" in caps
        assert "skewness_available" in caps
        assert "kurtosis_available" in caps

    def test_capabilities_scipy_reflects_import(self):
        """scipy_available should match actual import status."""
        caps = get_statistics_capabilities()
        assert caps["scipy_available"] == SCIPY_AVAILABLE

    def test_skewness_always_available(self):
        """Skewness should always be available (with fallback)."""
        caps = get_statistics_capabilities()
        assert caps["skewness_available"] is True

    def test_kurtosis_always_available(self):
        """Kurtosis should always be available (with fallback)."""
        caps = get_statistics_capabilities()
        assert caps["kurtosis_available"] is True
