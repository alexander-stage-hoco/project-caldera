"""Tests for output formatting utilities and distribution statistics."""

import sys
from pathlib import Path

# Add scripts directory to path for importing smell_analyzer
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from smell_analyzer import (
    strip_ansi,
    truncate_path_middle,
    format_number,
    format_percent,
    compute_distribution,
    Distribution,
    compute_gini,
    compute_theil,
    compute_hoover,
    compute_palma,
    compute_top_share,
    compute_bottom_share,
    compute_skewness,
    compute_kurtosis,
    FileStats,
    result_to_dict,
    distribution_to_dict,
    AnalysisResult,
)


class TestStripAnsi:
    """Tests for strip_ansi function."""

    def test_strips_simple_color_code(self):
        """Test stripping simple ANSI color codes."""
        text = "\033[31mRed text\033[0m"
        assert strip_ansi(text) == "Red text"

    def test_strips_multiple_color_codes(self):
        """Test stripping multiple ANSI codes."""
        text = "\033[1m\033[32mBold green\033[0m"
        assert strip_ansi(text) == "Bold green"

    def test_preserves_plain_text(self):
        """Test plain text without ANSI codes is preserved."""
        text = "Plain text without colors"
        assert strip_ansi(text) == text

    def test_strips_dim_and_bright_codes(self):
        """Test stripping dim and bright ANSI codes."""
        text = "\033[2mDim\033[0m \033[91mBright Red\033[0m"
        assert strip_ansi(text) == "Dim Bright Red"

    def test_handles_empty_string(self):
        """Test handling of empty string."""
        assert strip_ansi("") == ""


class TestTruncatePathMiddle:
    """Tests for truncate_path_middle function."""

    def test_short_path_unchanged(self):
        """Test short paths are not truncated."""
        path = "src/main.py"
        assert truncate_path_middle(path, 50) == path

    def test_long_path_truncated(self):
        """Test long paths are truncated with ellipsis."""
        path = "src/very/long/path/to/some/deeply/nested/file.py"
        result = truncate_path_middle(path, 20)
        assert len(result) == 20
        assert "..." in result
        assert result.startswith("src/")
        assert result.endswith(".py")

    def test_preserves_start_and_end(self):
        """Test truncation preserves start and end of path."""
        path = "beginning/middle/section/end.txt"
        result = truncate_path_middle(path, 25)
        assert result.startswith("beg")
        assert result.endswith(".txt")

    def test_exact_max_length(self):
        """Test path at exact max length is unchanged."""
        path = "exactly20characters!"
        assert truncate_path_middle(path, 20) == path


class TestFormatNumber:
    """Tests for format_number function."""

    def test_formats_integer(self):
        """Test formatting integers."""
        assert format_number(1000) == "1,000"
        assert format_number(1000000) == "1,000,000"

    def test_formats_small_numbers(self):
        """Test formatting small numbers."""
        assert format_number(0) == "0"
        assert format_number(42) == "42"
        assert format_number(999) == "999"

    def test_formats_with_decimals(self):
        """Test formatting with decimal places."""
        assert format_number(3.14159, decimals=2) == "3.14"
        assert format_number(1000.5, decimals=1) == "1,000.5"

    def test_formats_float_as_integer(self):
        """Test formatting float as integer (default decimals=0)."""
        assert format_number(1234.56) == "1,234"


class TestFormatPercent:
    """Tests for format_percent function."""

    def test_formats_percentage(self):
        """Test formatting percentages."""
        assert format_percent(75.0) == "75.0%"
        assert format_percent(100.0) == "100.0%"
        assert format_percent(0.0) == "0.0%"

    def test_formats_decimal_percentage(self):
        """Test formatting decimal percentages."""
        assert format_percent(33.333) == "33.3%"
        assert format_percent(66.666) == "66.7%"


class TestDistributionStatistics:
    """Tests for distribution computation."""

    def test_empty_list_returns_default_distribution(self):
        """Test empty list returns default Distribution."""
        dist = Distribution.from_values([])
        assert dist.count == 0
        assert dist.mean == 0.0

    def test_single_value_distribution(self):
        """Test distribution of single value."""
        dist = Distribution.from_values([5.0])
        assert dist.count == 1
        assert dist.min == 5.0
        assert dist.max == 5.0
        assert dist.mean == 5.0

    def test_basic_statistics(self):
        """Test basic statistics (mean, median, min, max)."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        dist = Distribution.from_values(values)
        assert dist.count == 5
        assert dist.min == 1.0
        assert dist.max == 5.0
        assert dist.mean == 3.0
        assert dist.median == 3.0

    def test_standard_deviation(self):
        """Test standard deviation calculation."""
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        dist = Distribution.from_values(values)
        assert dist.stddev > 0

    def test_percentiles(self):
        """Test percentile calculations.

        Note: The implementation uses integer indexing (int(n * percentile)),
        which gives slightly different values than interpolation methods.
        """
        values = list(range(1, 101))  # 1 to 100
        dist = Distribution.from_values([float(v) for v in values])
        # Implementation uses sorted_vals[int(n * pct)] indexing
        # For n=100: p25 = sorted[25] = 26, p75 = sorted[75] = 76
        assert dist.p25 == 26.0
        assert dist.p50 == 50.5  # median uses statistics.median
        assert dist.p75 == 76.0

    def test_iqr_calculation(self):
        """Test interquartile range calculation."""
        values = list(range(1, 101))
        dist = Distribution.from_values([float(v) for v in values])
        assert dist.iqr == dist.p75 - dist.p25


class TestInequalityMetrics:
    """Tests for inequality metrics (Gini, Theil, Hoover, Palma)."""

    def test_gini_uniform_distribution(self):
        """Test Gini coefficient for uniform distribution is 0."""
        values = [10.0, 10.0, 10.0, 10.0, 10.0]
        gini = compute_gini(values)
        assert abs(gini) < 0.01  # Should be ~0

    def test_gini_concentrated_distribution(self):
        """Test Gini coefficient for concentrated distribution is high."""
        values = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 100.0]
        gini = compute_gini(values)
        assert gini > 0.8  # Should be close to 1

    def test_gini_empty_list(self):
        """Test Gini coefficient for empty list is 0."""
        assert compute_gini([]) == 0.0

    def test_theil_uniform_distribution(self):
        """Test Theil index for uniform distribution is 0."""
        values = [10.0, 10.0, 10.0, 10.0, 10.0]
        theil = compute_theil(values)
        assert abs(theil) < 0.01

    def test_theil_handles_zeros(self):
        """Test Theil index handles zero values correctly."""
        values = [0.0, 0.0, 5.0, 10.0, 15.0]
        theil = compute_theil(values)
        assert theil >= 0

    def test_hoover_uniform_distribution(self):
        """Test Hoover index for uniform distribution is 0."""
        values = [10.0, 10.0, 10.0, 10.0, 10.0]
        hoover = compute_hoover(values)
        assert abs(hoover) < 0.01

    def test_hoover_empty_list(self):
        """Test Hoover index for empty list is 0."""
        assert compute_hoover([]) == 0.0

    def test_palma_ratio(self):
        """Test Palma ratio calculation."""
        # Create distribution with known shares
        values = list(range(1, 101))  # 1 to 100
        palma = compute_palma([float(v) for v in values])
        assert palma > 0  # Should be positive

    def test_palma_small_list(self):
        """Test Palma ratio for small list returns 0."""
        values = [1.0, 2.0, 3.0]
        assert compute_palma(values) == 0.0


class TestShareMetrics:
    """Tests for share metrics (top_share, bottom_share)."""

    def test_top_10_share(self):
        """Test top 10% share calculation."""
        values = list(range(1, 101))  # Sum = 5050
        share = compute_top_share([float(v) for v in values], 0.10)
        # Top 10 values: 91-100 = 955
        assert share > 0.15  # 955/5050 = ~0.189

    def test_bottom_50_share(self):
        """Test bottom 50% share calculation."""
        values = list(range(1, 101))
        share = compute_bottom_share([float(v) for v in values], 0.50)
        # Bottom 50 values: 1-50 = 1275
        assert share < 0.30  # 1275/5050 = ~0.252

    def test_top_share_uniform_distribution(self):
        """Test top share for uniform distribution."""
        values = [10.0] * 10
        share = compute_top_share(values, 0.10)
        assert abs(share - 0.1) < 0.05  # Should be ~10%

    def test_share_empty_list(self):
        """Test share metrics for empty list."""
        assert compute_top_share([], 0.10) == 0.0
        assert compute_bottom_share([], 0.50) == 0.0


class TestShapeMetrics:
    """Tests for distribution shape metrics (skewness, kurtosis)."""

    def test_skewness_symmetric_distribution(self):
        """Test skewness for symmetric distribution is near 0."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 4.0, 3.0, 2.0, 1.0]
        skew = compute_skewness(values, sum(values) / len(values))
        assert abs(skew) < 0.5  # Should be near 0

    def test_skewness_right_skewed(self):
        """Test skewness for right-skewed distribution is positive."""
        values = [1.0, 1.0, 1.0, 1.0, 1.0, 10.0, 20.0, 50.0]
        mean = sum(values) / len(values)
        skew = compute_skewness(values, mean)
        assert skew > 0  # Right-skewed = positive

    def test_skewness_small_list(self):
        """Test skewness for small list returns 0."""
        assert compute_skewness([1.0, 2.0], 1.5) == 0

    def test_kurtosis_normal_like(self):
        """Test kurtosis for normal-like distribution."""
        # Normal distribution has excess kurtosis near 0
        import random
        random.seed(42)
        values = [random.gauss(0, 1) for _ in range(1000)]
        mean = sum(values) / len(values)
        kurt = compute_kurtosis(values, mean)
        assert abs(kurt) < 1  # Should be near 0 for normal

    def test_kurtosis_small_list(self):
        """Test kurtosis for small list returns 0."""
        assert compute_kurtosis([1.0, 2.0, 3.0], 2.0) == 0


class TestFileStats:
    """Tests for FileStats dataclass."""

    def test_file_stats_creation(self):
        """Test FileStats can be created with all fields."""
        stats = FileStats(
            path="src/main.py",
            language="python",
            lines=100,
            smell_count=5,
            smell_density=5.0,
            by_category={"error_handling": 3, "security": 2},
            by_severity={"HIGH": 3, "MEDIUM": 2},
            by_smell_type={"D1_EMPTY_CATCH": 2, "SQL_INJECTION": 2, "D2_CATCH_ALL": 1},
        )
        assert stats.path == "src/main.py"
        assert stats.language == "python"
        assert stats.lines == 100
        assert stats.smell_count == 5
        assert stats.smell_density == 5.0
        assert len(stats.by_category) == 2
        assert len(stats.by_severity) == 2

    def test_file_stats_defaults(self):
        """Test FileStats default values."""
        stats = FileStats(
            path="test.py",
            language="python",
            lines=10,
            smell_count=0,
            smell_density=0.0,
        )
        assert stats.by_category == {}
        assert stats.by_severity == {}
        assert stats.by_smell_type == {}
        assert stats.smells == []


class TestDistributionToDict:
    """Tests for distribution_to_dict serialization."""

    def test_converts_distribution_to_dict(self):
        """Test Distribution converts to dict with all 22 metrics."""
        dist = Distribution.from_values([1.0, 2.0, 3.0, 4.0, 5.0])
        d = distribution_to_dict(dist)

        assert d is not None
        assert "count" in d
        assert "min" in d
        assert "max" in d
        assert "mean" in d
        assert "median" in d
        assert "stddev" in d
        assert "p25" in d
        assert "p50" in d
        assert "p75" in d
        assert "p90" in d
        assert "p95" in d
        assert "p99" in d
        assert "skewness" in d
        assert "kurtosis" in d
        assert "cv" in d
        assert "iqr" in d
        assert "gini" in d
        assert "theil" in d
        assert "hoover" in d
        assert "palma" in d
        assert "top_10_pct_share" in d
        assert "top_20_pct_share" in d
        assert "bottom_50_pct_share" in d

    def test_none_distribution_returns_none(self):
        """Test None distribution returns None."""
        assert distribution_to_dict(None) is None


class TestResultToDict:
    """Tests for result_to_dict serialization."""

    def test_result_to_dict_has_required_sections(self):
        """Test result_to_dict produces all required sections."""
        result = AnalysisResult(
            schema_version="1.0.0",
            run_id="test-001",
            timestamp="2026-01-20T12:00:00",
            root_path="/test/path",
            semgrep_version="1.0.0",
        )
        d = result_to_dict(result)
        results = d["results"]

        assert "metadata" in results
        assert "summary" in results
        assert "directories" in results
        assert "files" in results
        assert "by_language" in results
        assert "statistics" in results

    def test_metadata_section_has_required_fields(self):
        """Test metadata section has all required fields."""
        result = AnalysisResult(
            schema_version="1.0.0",
            run_id="test-001",
            timestamp="2026-01-20T12:00:00",
            root_path="/test/path",
            semgrep_version="1.0.0",
            rules_used=["rule1", "rule2"],
            analysis_duration_ms=1500,
        )
        d = result_to_dict(result)
        metadata = d["results"]["metadata"]

        assert metadata["schema_version"] == "1.0.0"
        assert metadata["run_id"] == "test-001"
        assert metadata["timestamp"] == "2026-01-20T12:00:00"
        assert metadata["root_path"] == "/test/path"
        assert metadata["semgrep_version"] == "1.0.0"
        assert metadata["rules_used"] == ["rule1", "rule2"]
        assert metadata["analysis_duration_ms"] == 1500

    def test_summary_section_aggregates_counts(self):
        """Test summary section has aggregated counts."""
        result = AnalysisResult(
            schema_version="1.0.0",
            run_id="test-001",
            timestamp="2026-01-20T12:00:00",
            root_path="/test/path",
            semgrep_version="1.0.0",
            by_category={"security": 5, "error_handling": 3},
            by_severity={"CRITICAL": 2, "HIGH": 6},
        )
        result.files = [
            FileStats(
                path="f1.py", language="python", lines=100,
                smell_count=5, smell_density=5.0
            ),
            FileStats(
                path="f2.py", language="python", lines=50,
                smell_count=3, smell_density=6.0
            ),
        ]
        d = result_to_dict(result)
        summary = d["results"]["summary"]

        assert summary["total_files"] == 2
        assert summary["total_lines"] == 150
        assert summary["smells_by_category"]["security"] == 5
        assert summary["smells_by_severity"]["CRITICAL"] == 2
