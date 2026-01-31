"""
Statistical Utilities for Layout Scanner.

Provides functions to compute distribution statistics including
percentiles, mean, standard deviation, skewness, and kurtosis.
"""

import math
import statistics
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Sequence, Union

# Try to import scipy for skewness/kurtosis
try:
    from scipy import stats as scipy_stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


@dataclass
class DistributionStats:
    """Statistical summary of a distribution."""

    count: int
    min: float
    max: float
    mean: float
    std_dev: float
    p25: float  # 25th percentile
    p50: float  # 50th percentile (median)
    p75: float  # 75th percentile
    skewness: Optional[float] = None  # None if scipy not available or insufficient data
    kurtosis: Optional[float] = None  # None if scipy not available or insufficient data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


def compute_percentile(sorted_values: List[float], percentile: float) -> float:
    """Compute percentile using linear interpolation.

    Args:
        sorted_values: Pre-sorted list of values.
        percentile: Percentile to compute (0-100).

    Returns:
        The percentile value.
    """
    if not sorted_values:
        return 0.0

    n = len(sorted_values)
    if n == 1:
        return sorted_values[0]

    # Convert percentile to rank
    rank = (percentile / 100) * (n - 1)
    lower_idx = int(rank)
    upper_idx = min(lower_idx + 1, n - 1)
    fraction = rank - lower_idx

    return sorted_values[lower_idx] + fraction * (sorted_values[upper_idx] - sorted_values[lower_idx])


def compute_skewness(values: List[float], mean: float, std_dev: float) -> Optional[float]:
    """Compute Fisher-Pearson skewness coefficient.

    Uses scipy if available, otherwise computes manually.
    Skewness indicates asymmetry:
    - Positive skew: tail extends to the right
    - Negative skew: tail extends to the left
    - Zero: symmetric

    Args:
        values: List of values.
        mean: Pre-computed mean.
        std_dev: Pre-computed standard deviation.

    Returns:
        Skewness value, or None if insufficient data.
    """
    n = len(values)
    if n < 3 or std_dev == 0:
        return None

    if SCIPY_AVAILABLE:
        return float(scipy_stats.skew(values, bias=False))

    # Manual calculation using Fisher-Pearson formula
    m3 = sum((x - mean) ** 3 for x in values) / n
    return m3 / (std_dev ** 3)


def compute_kurtosis(values: List[float], mean: float, std_dev: float) -> Optional[float]:
    """Compute excess kurtosis.

    Uses scipy if available, otherwise computes manually.
    Kurtosis indicates "tailedness":
    - Positive kurtosis: heavier tails than normal
    - Negative kurtosis: lighter tails than normal
    - Zero: similar to normal distribution

    Args:
        values: List of values.
        mean: Pre-computed mean.
        std_dev: Pre-computed standard deviation.

    Returns:
        Excess kurtosis value, or None if insufficient data.
    """
    n = len(values)
    if n < 4 or std_dev == 0:
        return None

    if SCIPY_AVAILABLE:
        return float(scipy_stats.kurtosis(values, bias=False))

    # Manual calculation using excess kurtosis formula
    m4 = sum((x - mean) ** 4 for x in values) / n
    return (m4 / (std_dev ** 4)) - 3


def compute_stats(values: Sequence[Union[int, float]]) -> DistributionStats:
    """Compute comprehensive distribution statistics.

    Args:
        values: Sequence of numeric values.

    Returns:
        DistributionStats with all computed metrics.

    Example:
        >>> values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        >>> stats = compute_stats(values)
        >>> stats.mean
        5.5
        >>> stats.p50
        5.5
    """
    # Convert to list of floats
    float_values = [float(v) for v in values]
    n = len(float_values)

    if n == 0:
        return DistributionStats(
            count=0,
            min=0.0,
            max=0.0,
            mean=0.0,
            std_dev=0.0,
            p25=0.0,
            p50=0.0,
            p75=0.0,
            skewness=None,
            kurtosis=None,
        )

    # Sort for percentile calculations
    sorted_values = sorted(float_values)

    # Basic statistics
    min_val = sorted_values[0]
    max_val = sorted_values[-1]
    mean_val = statistics.mean(float_values)

    # Standard deviation (sample std dev if n > 1)
    if n > 1:
        std_dev = statistics.stdev(float_values)
    else:
        std_dev = 0.0

    # Percentiles
    p25 = compute_percentile(sorted_values, 25)
    p50 = compute_percentile(sorted_values, 50)
    p75 = compute_percentile(sorted_values, 75)

    # Skewness and kurtosis
    skewness = compute_skewness(float_values, mean_val, std_dev)
    kurtosis = compute_kurtosis(float_values, mean_val, std_dev)

    return DistributionStats(
        count=n,
        min=round(min_val, 2),
        max=round(max_val, 2),
        mean=round(mean_val, 2),
        std_dev=round(std_dev, 2),
        p25=round(p25, 2),
        p50=round(p50, 2),
        p75=round(p75, 2),
        skewness=round(skewness, 4) if skewness is not None else None,
        kurtosis=round(kurtosis, 4) if kurtosis is not None else None,
    )


def compute_depth_distribution_stats(
    depth_distribution: Dict[int, int]
) -> DistributionStats:
    """Compute statistics from a depth distribution map.

    Args:
        depth_distribution: Mapping of depth -> count.

    Returns:
        DistributionStats for the distribution.
    """
    # Expand distribution into individual values
    values = []
    for depth, count in depth_distribution.items():
        values.extend([depth] * count)

    return compute_stats(values)


def compute_files_per_directory_stats(
    dir_file_counts: Sequence[int]
) -> DistributionStats:
    """Compute statistics for files per directory.

    Args:
        dir_file_counts: List of file counts per directory.

    Returns:
        DistributionStats for the distribution.
    """
    return compute_stats(dir_file_counts)


def compute_file_size_stats(
    file_sizes: Sequence[int]
) -> DistributionStats:
    """Compute statistics for file sizes.

    Args:
        file_sizes: List of file sizes in bytes.

    Returns:
        DistributionStats for the distribution.
    """
    return compute_stats(file_sizes)


def get_statistics_capabilities() -> Dict[str, bool]:
    """Get information about available statistics capabilities.

    Returns:
        Dictionary indicating which features are available.
    """
    return {
        "scipy_available": SCIPY_AVAILABLE,
        "skewness_available": True,  # Always available (fallback to manual)
        "kurtosis_available": True,  # Always available (fallback to manual)
    }


__all__ = [
    "DistributionStats",
    "compute_stats",
    "compute_depth_distribution_stats",
    "compute_files_per_directory_stats",
    "compute_file_size_stats",
    "compute_percentile",
    "compute_skewness",
    "compute_kurtosis",
    "get_statistics_capabilities",
    "SCIPY_AVAILABLE",
]
