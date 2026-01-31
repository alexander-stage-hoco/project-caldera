"""Tests for output formatting and JSON structure."""

import json
import sys
from pathlib import Path

import pytest

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from function_analyzer import (
    AnalysisResult,
    AnalysisSummary,
    Distribution,
    DirectoryInfo,
    DirectoryStats,
    DirectoryStructure,
    FunctionInfo,
    FileInfo,
    truncate_path_middle,
    format_number,
    strip_ansi,
    c,
    Colors,
    set_color_enabled,
)
from common.path_normalization import normalize_file_path


class TestPathTruncation:
    """Tests for path truncation helper."""

    def test_short_path_unchanged(self):
        """Test that short paths are not truncated."""
        path = "src/main.py"
        assert truncate_path_middle(path, 50) == path

    def test_long_path_truncated(self):
        """Test that long paths are truncated."""
        path = "/very/long/path/to/some/deeply/nested/directory/file.py"
        truncated = truncate_path_middle(path, 30)
        assert len(truncated) <= 30
        assert "..." in truncated

    def test_preserves_start_and_end(self):
        """Test that truncation preserves start and end of path."""
        path = "/start/middle/end.py"
        truncated = truncate_path_middle(path, 20)
        # Should contain parts of start and end
        assert truncated.startswith("/")
        assert truncated.endswith(".py")

    def test_exact_length(self):
        """Test path at exact max length."""
        path = "exactly_this_long"
        assert truncate_path_middle(path, len(path)) == path

    def test_normalize_strips_repo_prefix_without_leading_slash(self):
        """Repo prefix without leading slash is removed from paths."""
        repo_root = Path("/tmp/keepass2android")
        input_path = "tmp/keepass2android/.github/PULL_REQUEST_TEMPLATE.md"
        normalized = normalize_file_path(input_path, repo_root)
        assert normalized == ".github/PULL_REQUEST_TEMPLATE.md"


class TestNumberFormatting:
    """Tests for number formatting helper."""

    def test_integer_formatting(self):
        """Test integer formatting with commas."""
        assert format_number(1000) == "1,000"
        assert format_number(1000000) == "1,000,000"
        assert format_number(42) == "42"

    def test_decimal_formatting(self):
        """Test decimal formatting."""
        assert format_number(3.14159, 2) == "3.14"
        assert format_number(1000.5, 1) == "1,000.5"

    def test_zero(self):
        """Test formatting zero."""
        assert format_number(0) == "0"
        assert format_number(0.0, 2) == "0.00"


class TestAnsiHandling:
    """Tests for ANSI color code handling."""

    def test_strip_ansi_codes(self):
        """Test stripping ANSI codes from text."""
        colored = "\033[31mRed text\033[0m"
        assert strip_ansi(colored) == "Red text"

    def test_strip_multiple_codes(self):
        """Test stripping multiple ANSI codes."""
        colored = "\033[1m\033[32mBold green\033[0m normal"
        assert strip_ansi(colored) == "Bold green normal"

    def test_strip_no_codes(self):
        """Test text without ANSI codes is unchanged."""
        plain = "Plain text"
        assert strip_ansi(plain) == plain

    def test_color_disabled(self):
        """Test color function when colors are disabled."""
        set_color_enabled(False)
        result = c("text", Colors.RED)
        assert result == "text"
        set_color_enabled(True)  # Reset for other tests

    def test_color_enabled(self):
        """Test color function when colors are enabled."""
        set_color_enabled(True)
        result = c("text", Colors.RED)
        assert Colors.RED in result
        assert Colors.RESET in result
        assert "text" in result


class TestDataclassSerialization:
    """Tests for dataclass to dict conversion."""

    def test_function_info_to_dict(self, sample_function_info):
        """Test FunctionInfo can be converted to dict."""
        # Dataclasses should have __dict__ or be convertible
        func_dict = vars(sample_function_info)

        assert func_dict["name"] == "process_data"
        assert func_dict["ccn"] == 8
        assert func_dict["nloc"] == 35

    def test_distribution_to_dict(self):
        """Test Distribution can be serialized to JSON."""
        dist = Distribution(
            count=10,
            min=1.0,
            max=25.0,
            mean=7.1,
            median=4.0,
            stddev=7.5,
            p25=1.0,
            p50=4.0,
            p75=10.0,
            p90=15.0,
            p95=25.0,
            p99=25.0,
            gini=0.4,
        )

        # Should be JSON serializable
        dist_dict = vars(dist)
        json_str = json.dumps(dist_dict)
        loaded = json.loads(json_str)

        assert loaded["count"] == 10
        assert loaded["mean"] == 7.1
        assert loaded["gini"] == 0.4

    def test_file_info_with_functions_to_dict(self, sample_file_info):
        """Test FileInfo with nested functions can be serialized."""
        # Convert to dict recursively
        def to_dict(obj):
            if hasattr(obj, '__dict__'):
                return {k: to_dict(v) for k, v in vars(obj).items()}
            elif isinstance(obj, list):
                return [to_dict(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: to_dict(v) for k, v in obj.items()}
            return obj

        file_dict = to_dict(sample_file_info)

        # Should be JSON serializable
        json_str = json.dumps(file_dict)
        loaded = json.loads(json_str)

        assert loaded["path"] == "/src/processor.py"
        assert loaded["language"] == "Python"
        assert len(loaded["functions"]) == 2
        assert loaded["functions"][0]["name"] == "process_data"


class TestAnalysisResultStructure:
    """Tests for AnalysisResult JSON structure."""

    def test_schema_version_present(self, sample_analysis_result):
        """Test that schema version is present."""
        assert sample_analysis_result.schema_version == "2.0.0"

    def test_required_fields_present(self, sample_analysis_result):
        """Test that all required fields are present."""
        assert sample_analysis_result.run_id is not None
        assert sample_analysis_result.timestamp is not None
        assert sample_analysis_result.root_path is not None
        assert sample_analysis_result.files is not None
        assert sample_analysis_result.summary is not None

    def test_summary_structure(self, sample_analysis_result):
        """Test summary has expected structure."""
        summary = sample_analysis_result.summary

        assert hasattr(summary, "total_files")
        assert hasattr(summary, "total_functions")
        assert hasattr(summary, "total_nloc")
        assert hasattr(summary, "total_ccn")
        assert hasattr(summary, "avg_ccn")
        assert hasattr(summary, "max_ccn")
        assert hasattr(summary, "functions_over_threshold")
        assert hasattr(summary, "ccn_threshold")

    def test_by_language_structure(self, sample_analysis_result):
        """Test by_language has expected structure."""
        by_lang = sample_analysis_result.by_language

        assert "Python" in by_lang
        python_stats = by_lang["Python"]
        assert "files" in python_stats
        assert "functions" in python_stats
        assert "nloc" in python_stats
        assert "ccn" in python_stats


class TestDirectoryInfoStructure:
    """Tests for DirectoryInfo structure."""

    def test_directory_info_creation(self):
        """Test creating DirectoryInfo."""
        dir_info = DirectoryInfo(
            path="src/core",
            name="core",
            depth=1,
            is_leaf=False,
            child_count=3,
            direct=DirectoryStats(file_count=5, function_count=20),
            recursive=DirectoryStats(file_count=15, function_count=80),
            subdirectories=["handlers", "utils", "models"],
        )

        assert dir_info.path == "src/core"
        assert dir_info.depth == 1
        assert dir_info.direct.file_count == 5
        assert dir_info.recursive.file_count == 15
        assert len(dir_info.subdirectories) == 3

    def test_directory_structure_metadata(self):
        """Test DirectoryStructure metadata."""
        structure = DirectoryStructure(
            max_depth=4,
            avg_depth=2.5,
            leaf_directory_count=10,
            avg_functions_per_directory=15.3,
        )

        assert structure.max_depth == 4
        assert structure.avg_depth == 2.5
        assert structure.leaf_directory_count == 10


class TestOutputJsonValidity:
    """Tests for JSON output validity."""

    def test_full_result_json_serializable(self, sample_analysis_result):
        """Test that full result can be serialized to valid JSON."""
        def to_dict(obj):
            if hasattr(obj, '__dict__'):
                return {k: to_dict(v) for k, v in vars(obj).items()}
            elif isinstance(obj, list):
                return [to_dict(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: to_dict(v) for k, v in obj.items()}
            return obj

        result_dict = to_dict(sample_analysis_result)

        # Should not raise
        json_str = json.dumps(result_dict, default=str)

        # Should parse back
        loaded = json.loads(json_str)
        assert loaded["schema_version"] == "2.0.0"

    def test_no_nan_or_inf_values(self, sample_analysis_result):
        """Test that result doesn't contain NaN or Inf values."""
        def check_values(obj, path=""):
            if isinstance(obj, float):
                assert not (obj != obj), f"NaN found at {path}"  # NaN != NaN
                assert obj != float('inf'), f"Inf found at {path}"
                assert obj != float('-inf'), f"-Inf found at {path}"
            elif hasattr(obj, '__dict__'):
                for k, v in vars(obj).items():
                    check_values(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_values(item, f"{path}[{i}]")
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    check_values(v, f"{path}.{k}")

        check_values(sample_analysis_result)
