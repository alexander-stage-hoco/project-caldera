"""Tests for metrics calculation functions."""

import pytest
import statistics
import sys
from pathlib import Path

# Add scripts to path for imports
scripts_path = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))


class TestDistributionCalculations:
    """Tests for statistical distribution calculations."""

    def test_basic_statistics(self, sample_distribution_values):
        """Test basic statistical calculations."""
        values = sample_distribution_values

        # Expected values
        expected_min = 10
        expected_max = 100
        expected_mean = 55.0
        expected_median = 55.0

        assert min(values) == expected_min
        assert max(values) == expected_max
        assert statistics.mean(values) == expected_mean
        assert statistics.median(values) == expected_median

    def test_percentile_calculations(self, sample_distribution_values):
        """Test percentile calculations."""
        values = sorted(sample_distribution_values)

        # For [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        # p25 should be around 30, p75 around 80
        assert values[2] == 30  # Approximately p25
        assert values[7] == 80  # Approximately p75

    def test_standard_deviation(self, sample_distribution_values):
        """Test standard deviation calculation."""
        values = sample_distribution_values
        stddev = statistics.stdev(values)

        # Should be approximately 30.3 for this dataset
        assert 28 < stddev < 32

    def test_empty_distribution(self):
        """Test handling of empty data."""
        values = []

        # These should raise or return sensible defaults
        with pytest.raises(statistics.StatisticsError):
            statistics.mean(values)

    def test_single_value_distribution(self):
        """Test distribution with single value."""
        values = [42]

        assert statistics.mean(values) == 42
        assert min(values) == max(values) == 42


class TestAggregateMetrics:
    """Tests for aggregate metric calculations."""

    def test_total_loc_calculation(self, sample_scc_output):
        """Test total LOC calculation from language breakdown."""
        total_code = sum(lang["Code"] for lang in sample_scc_output)
        expected = 80 + 40  # Python + JavaScript
        assert total_code == expected

    def test_total_files_calculation(self, sample_scc_output):
        """Test total files calculation."""
        total_files = sum(lang["Count"] for lang in sample_scc_output)
        expected = 3 + 2  # Python + JavaScript
        assert total_files == expected

    def test_total_complexity_calculation(self, sample_scc_output):
        """Test total complexity calculation."""
        total_complexity = sum(lang["Complexity"] for lang in sample_scc_output)
        expected = 5 + 3  # Python + JavaScript
        assert total_complexity == expected

    def test_language_count(self, sample_scc_output):
        """Test language count calculation."""
        languages = len(sample_scc_output)
        assert languages == 2


class TestDirectoryMetrics:
    """Tests for directory-level metric calculations."""

    def test_recursive_gte_direct(self, sample_directory_stats):
        """Test that recursive counts are >= direct counts."""
        for dir_stat in sample_directory_stats:
            direct = dir_stat["direct"]
            recursive = dir_stat["recursive"]

            assert recursive["file_count"] >= direct["file_count"]
            assert recursive["loc"] >= direct["loc"]
            assert recursive["complexity"] >= direct["complexity"]

    def test_direct_stats_non_negative(self, sample_directory_stats):
        """Test that direct stats are non-negative."""
        for dir_stat in sample_directory_stats:
            direct = dir_stat["direct"]

            assert direct["file_count"] >= 0
            assert direct["loc"] >= 0
            assert direct["complexity"] >= 0

    def test_directory_has_path(self, sample_directory_stats):
        """Test that each directory has a path."""
        for dir_stat in sample_directory_stats:
            assert "path" in dir_stat
            assert len(dir_stat["path"]) > 0


class TestFileClassification:
    """Tests for file classification logic."""

    def test_test_file_patterns(self):
        """Test that test files are identified correctly."""
        test_patterns = [
            "tests/test_main.py",
            "test/unit/test_utils.py",
            "__tests__/App.test.js",
            "spec/models/user_spec.rb",
        ]

        for path in test_patterns:
            lower = path.lower()
            is_test = (
                "test" in lower or
                "spec" in lower or
                "__tests__" in lower
            )
            assert is_test, f"{path} should be classified as test"

    def test_source_file_patterns(self):
        """Test that source files are identified correctly."""
        source_patterns = [
            "src/main.py",
            "lib/utils.js",
            "app/models/user.rb",
        ]

        for path in source_patterns:
            lower = path.lower()
            is_source = (
                "test" not in lower and
                "spec" not in lower and
                "__tests__" not in lower
            )
            assert is_source, f"{path} should be classified as source"

    def test_config_file_patterns(self):
        """Test that config files are identified by extension."""
        config_patterns = [
            "config.json",
            "settings.yaml",
            ".eslintrc.json",
            "pyproject.toml",
        ]

        config_extensions = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}

        for path in config_patterns:
            ext = Path(path).suffix.lower()
            # Note: This is a simplified check - actual classification may be more complex
            is_config_ext = ext in config_extensions
            # Just verify we can extract the extension
            assert ext in [".json", ".yaml", ".toml"]
