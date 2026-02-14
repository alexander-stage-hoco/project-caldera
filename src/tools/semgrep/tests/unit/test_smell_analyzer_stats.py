"""Tests for smell_analyzer.py statistical functions and data models.

Covers:
- Distribution.from_values (22-metric distribution computation)
- compute_* inequality/shape helpers
- compute_directory_smell_stats
- build_directory_entries
- count_lines
- format helpers (truncate_path_middle, format_number, format_percent)
- SEVERITY_MAP
- SmellInstance, FileStats, DirectoryStats, DirectoryEntry data models
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from smell_analyzer import (
    Distribution,
    FileStats,
    DirectoryStats,
    DirectoryEntry,
    SmellInstance,
    LanguageStats,
    AnalysisResult,
    compute_skewness,
    compute_kurtosis,
    compute_gini,
    compute_theil,
    compute_hoover,
    compute_palma,
    compute_top_share,
    compute_bottom_share,
    compute_directory_smell_stats,
    build_directory_entries,
    count_lines,
    detect_language,
    truncate_path_middle,
    format_number,
    format_percent,
    set_color_enabled,
    c,
    strip_ansi,
    Colors,
    SEVERITY_MAP,
)


# ===========================================================================
# Distribution.from_values
# ===========================================================================

class TestDistributionFromValues:
    def test_empty_list(self):
        d = Distribution.from_values([])
        assert d.count == 0
        assert d.mean == 0.0

    def test_single_value(self):
        d = Distribution.from_values([5.0])
        assert d.count == 1
        assert d.min == 5.0
        assert d.max == 5.0
        assert d.mean == 5.0
        assert d.stddev == 0

    def test_two_values(self):
        d = Distribution.from_values([0.0, 10.0])
        assert d.count == 2
        assert d.min == 0.0
        assert d.max == 10.0
        assert d.mean == 5.0
        assert d.skewness == 0  # n < 3

    def test_uniform_values(self):
        vals = [5.0] * 20
        d = Distribution.from_values(vals)
        assert d.mean == 5.0
        assert d.stddev == 0.0
        assert d.cv == 0  # stddev/mean when stddev=0
        assert d.gini == 0.0

    def test_large_list(self):
        vals = list(range(100))
        d = Distribution.from_values([float(v) for v in vals])
        assert d.count == 100
        assert d.min == 0.0
        assert d.max == 99.0
        assert d.p25 == vals[25]
        assert d.p75 == vals[75]
        assert d.p90 == vals[90]
        assert d.p95 == vals[95]
        assert d.p99 == vals[99]
        assert d.iqr == d.p75 - d.p25

    def test_cv_computed(self):
        vals = [1.0, 2.0, 3.0, 4.0, 5.0]
        d = Distribution.from_values(vals)
        # cv = stddev / mean
        assert d.cv > 0

    def test_palma_zero_when_few_values(self):
        # compute_palma requires n >= 10
        d = Distribution.from_values([1.0, 2.0, 3.0])
        assert d.palma == 0

    def test_all_metrics_present(self):
        d = Distribution.from_values([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        # Ensure all expected metrics are computed (via dataclass fields)
        fields = [f.name for f in d.__dataclass_fields__.values()]
        assert len(fields) >= 22


# ===========================================================================
# Inequality / Shape helpers
# ===========================================================================

class TestComputeSkewness:
    def test_symmetric(self):
        # Symmetric values => skewness ~0
        vals = [1.0, 2.0, 3.0, 4.0, 5.0]
        s = compute_skewness(vals, 3.0)
        assert abs(s) < 0.1

    def test_few_values(self):
        assert compute_skewness([1.0, 2.0], 1.5) == 0

    def test_zero_std(self):
        assert compute_skewness([5.0, 5.0, 5.0], 5.0) == 0


class TestComputeKurtosis:
    def test_few_values(self):
        assert compute_kurtosis([1.0, 2.0, 3.0], 2.0) == 0

    def test_zero_std(self):
        assert compute_kurtosis([5.0, 5.0, 5.0, 5.0], 5.0) == 0

    def test_normal_like(self):
        vals = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        k = compute_kurtosis(vals, 5.5)
        # Excess kurtosis for uniform is about -1.2
        assert isinstance(k, float)


class TestComputeGini:
    def test_empty(self):
        assert compute_gini([]) == 0.0

    def test_single(self):
        assert compute_gini([5.0]) == 0.0

    def test_equal(self):
        # All equal => Gini ~0
        g = compute_gini([10.0, 10.0, 10.0, 10.0])
        assert abs(g) < 0.01

    def test_all_zero(self):
        assert compute_gini([0.0, 0.0, 0.0]) == 0.0

    def test_unequal(self):
        g = compute_gini([0.0, 0.0, 0.0, 0.0, 100.0])
        assert g > 0.5


class TestComputeTheil:
    def test_empty(self):
        assert compute_theil([]) == 0.0

    def test_single(self):
        assert compute_theil([5.0]) == 0.0

    def test_all_zero(self):
        assert compute_theil([0.0, 0.0]) == 0.0

    def test_positive(self):
        t = compute_theil([1.0, 10.0, 100.0])
        assert t > 0


class TestComputeHoover:
    def test_empty(self):
        assert compute_hoover([]) == 0.0

    def test_single(self):
        assert compute_hoover([5.0]) == 0.0

    def test_all_zero(self):
        assert compute_hoover([0.0, 0.0]) == 0.0

    def test_equal(self):
        h = compute_hoover([10.0, 10.0, 10.0])
        assert abs(h) < 0.001

    def test_unequal(self):
        h = compute_hoover([0.0, 0.0, 100.0])
        assert h > 0.3


class TestComputePalma:
    def test_empty(self):
        assert compute_palma([]) == 0.0

    def test_few_values(self):
        assert compute_palma([1.0, 2.0, 3.0]) == 0.0

    def test_equal(self):
        vals = [10.0] * 20
        p = compute_palma(vals)
        # For equal values: top 10% = 2 items = 20, bottom 40% = 8 items = 80
        # palma = 20/80 = 0.25
        assert abs(p - 0.25) < 0.01

    def test_bottom_zero(self):
        vals = [0.0] * 10 + [100.0]
        # bottom 40% = 0 => inf
        p = compute_palma(vals)
        assert p == float('inf')

    def test_all_zero(self):
        vals = [0.0] * 10
        assert compute_palma(vals) == 0.0


class TestComputeTopShare:
    def test_empty(self):
        assert compute_top_share([], 0.10) == 0.0

    def test_all_zero(self):
        assert compute_top_share([0.0, 0.0], 0.10) == 0.0

    def test_basic(self):
        vals = [1.0, 2.0, 3.0, 4.0, 5.0]
        share = compute_top_share(vals, 0.20)
        # top 20% => top 1 item = 5.0 out of 15.0
        assert abs(share - 5.0 / 15.0) < 0.01


class TestComputeBottomShare:
    def test_empty(self):
        assert compute_bottom_share([], 0.50) == 0.0

    def test_all_zero(self):
        assert compute_bottom_share([0.0, 0.0], 0.50) == 0.0

    def test_basic(self):
        vals = [1.0, 2.0, 3.0, 4.0, 5.0]
        share = compute_bottom_share(vals, 0.40)
        # bottom 40% => bottom 2 items = 1+2=3 out of 15
        assert abs(share - 3.0 / 15.0) < 0.01


# ===========================================================================
# compute_directory_smell_stats
# ===========================================================================

class TestComputeDirectorySmellStats:
    def test_empty_files(self):
        ds = compute_directory_smell_stats([])
        assert ds.file_count == 0
        assert ds.smell_count == 0

    def test_single_file(self):
        f = FileStats(
            path="src/a.py", language="python", lines=100,
            smell_count=3, smell_density=3.0,
            by_category={"error_handling": 2, "security": 1},
            by_severity={"HIGH": 3},
            by_smell_type={"D1_EMPTY_CATCH": 2, "SQL_INJECTION": 1},
        )
        ds = compute_directory_smell_stats([f])
        assert ds.file_count == 1
        assert ds.lines_code == 100
        assert ds.smell_count == 3
        assert ds.by_category["error_handling"] == 2
        assert ds.smell_density == 3.0

    def test_multiple_files_aggregation(self):
        files = [
            FileStats(path="a.py", language="python", lines=50, smell_count=2, smell_density=4.0,
                      by_category={"security": 2}, by_severity={"HIGH": 2}, by_smell_type={"SQL_INJECTION": 2}),
            FileStats(path="b.py", language="python", lines=50, smell_count=1, smell_density=2.0,
                      by_category={"security": 1}, by_severity={"MEDIUM": 1}, by_smell_type={"XSS_VULNERABILITY": 1}),
        ]
        ds = compute_directory_smell_stats(files)
        assert ds.file_count == 2
        assert ds.lines_code == 100
        assert ds.smell_count == 3
        assert ds.by_category["security"] == 3
        assert ds.smell_distribution is None  # < 3 files

    def test_distribution_computed_for_three_plus_files(self):
        files = [
            FileStats(path=f"f{i}.py", language="python", lines=10, smell_count=i, smell_density=float(i))
            for i in range(5)
        ]
        ds = compute_directory_smell_stats(files)
        assert ds.smell_distribution is not None
        assert ds.smell_distribution.count == 5


# ===========================================================================
# build_directory_entries
# ===========================================================================

class TestBuildDirectoryEntries:
    def test_empty_files(self):
        assert build_directory_entries([], "/repo") == []

    def test_flat_structure(self):
        files = [
            FileStats(path="a.py", language="python", lines=10, smell_count=1, smell_density=10.0),
            FileStats(path="b.py", language="python", lines=20, smell_count=2, smell_density=10.0),
        ]
        entries = build_directory_entries(files, "/repo")
        # Should have root directory "."
        assert len(entries) >= 1
        root = next((e for e in entries if e.path == "."), None)
        assert root is not None
        assert root.recursive.file_count == 2
        assert root.recursive.smell_count == 3

    def test_nested_structure(self):
        files = [
            FileStats(path="src/a.py", language="python", lines=10, smell_count=1, smell_density=10.0),
            FileStats(path="src/lib/b.py", language="python", lines=20, smell_count=2, smell_density=10.0),
        ]
        entries = build_directory_entries(files, "/repo")
        paths = [e.path for e in entries]
        assert "src" in paths
        assert "src/lib" in paths

        src_entry = next(e for e in entries if e.path == "src")
        # Direct: only a.py
        assert src_entry.direct.file_count == 1
        # Recursive: a.py + lib/b.py
        assert src_entry.recursive.file_count == 2

    def test_leaf_detection(self):
        files = [
            FileStats(path="src/lib/c.py", language="python", lines=10, smell_count=0, smell_density=0.0),
        ]
        entries = build_directory_entries(files, "/repo")
        lib_entry = next(e for e in entries if e.path == "src/lib")
        assert lib_entry.is_leaf is True

    def test_subdirectories_populated(self):
        files = [
            FileStats(path="src/a.py", language="python", lines=10, smell_count=0, smell_density=0.0),
            FileStats(path="src/sub1/b.py", language="python", lines=10, smell_count=0, smell_density=0.0),
            FileStats(path="src/sub2/c.py", language="python", lines=10, smell_count=0, smell_density=0.0),
        ]
        entries = build_directory_entries(files, "/repo")
        src_entry = next(e for e in entries if e.path == "src")
        assert "src/sub1" in src_entry.subdirectories
        assert "src/sub2" in src_entry.subdirectories
        assert src_entry.child_count == 2


# ===========================================================================
# count_lines
# ===========================================================================

class TestCountLines:
    def test_count_lines(self, tmp_path: Path):
        f = tmp_path / "test.py"
        f.write_text("line1\nline2\nline3\n")
        assert count_lines(str(f)) == 3

    def test_nonexistent_file(self):
        assert count_lines("/nonexistent/file.py") == 0

    def test_empty_file(self, tmp_path: Path):
        f = tmp_path / "empty.py"
        f.write_text("")
        assert count_lines(str(f)) == 0


# ===========================================================================
# Format helpers
# ===========================================================================

class TestTruncatePathMiddle:
    def test_short_path(self):
        assert truncate_path_middle("src/a.py", 20) == "src/a.py"

    def test_long_path(self):
        path = "a" * 100
        result = truncate_path_middle(path, 20)
        assert len(result) == 20
        assert "..." in result


class TestFormatNumber:
    def test_integer(self):
        assert format_number(1234) == "1,234"

    def test_float(self):
        assert format_number(1234.567, 2) == "1,234.57"


class TestFormatPercent:
    def test_basic(self):
        assert format_percent(75.123) == "75.1%"


class TestColorHelpers:
    def test_color_enabled(self):
        set_color_enabled(True)
        result = c("hello", Colors.RED)
        assert "\033[" in result
        assert "hello" in result

    def test_color_disabled(self):
        set_color_enabled(False)
        result = c("hello", Colors.RED)
        assert result == "hello"
        set_color_enabled(True)  # Reset

    def test_strip_ansi(self):
        colored = f"\033[31mhello\033[0m"
        assert strip_ansi(colored) == "hello"


# ===========================================================================
# SEVERITY_MAP
# ===========================================================================

class TestSeverityMap:
    def test_error_maps_to_critical(self):
        assert SEVERITY_MAP["ERROR"] == "CRITICAL"

    def test_warning_maps_to_high(self):
        assert SEVERITY_MAP["WARNING"] == "HIGH"

    def test_info_maps_to_medium(self):
        assert SEVERITY_MAP["INFO"] == "MEDIUM"
