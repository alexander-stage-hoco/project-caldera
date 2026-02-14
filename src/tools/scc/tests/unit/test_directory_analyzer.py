"""Tests for scripts/directory_analyzer.py - distribution stats, COCOMO, file classification."""
from __future__ import annotations

import math

import pytest
from scripts.directory_analyzer import (
    MetricDistribution,
    compute_skewness,
    compute_kurtosis,
    compute_gini,
    compute_theil,
    compute_hoover,
    compute_palma,
    compute_top_share,
    compute_bottom_share,
    compute_cocomo,
    classify_file,
    normalize_field_names,
    format_number,
    format_money,
    format_percent,
    truncate_path_middle,
    set_color_enabled,
    c,
    Colors,
    strip_ansi,
    COCOMO_PRESETS,
)


# ---------------------------------------------------------------------------
# Tests: MetricDistribution.from_values
# ---------------------------------------------------------------------------

class TestMetricDistribution:
    """Tests for the MetricDistribution dataclass."""

    def test_empty_values_returns_zeros(self):
        dist = MetricDistribution.from_values([])
        assert dist.min == 0
        assert dist.max == 0
        assert dist.mean == 0
        assert dist.gini == 0

    def test_single_value(self):
        dist = MetricDistribution.from_values([42.0])
        assert dist.min == 42.0
        assert dist.max == 42.0
        assert dist.mean == 42.0
        assert dist.median == 42.0
        assert dist.stddev == 0
        assert dist.skewness == 0
        assert dist.kurtosis == 0

    def test_two_values(self):
        dist = MetricDistribution.from_values([10.0, 20.0])
        assert dist.min == 10.0
        assert dist.max == 20.0
        assert dist.mean == 15.0
        assert dist.median == 15.0
        assert dist.p25 == 10.0
        assert dist.p75 == 20.0

    def test_uniform_values_low_gini(self):
        dist = MetricDistribution.from_values([10.0] * 20)
        assert dist.gini == 0.0
        assert dist.theil == 0.0
        assert dist.hoover == 0.0

    def test_skewed_values(self):
        # One very large value, many small
        values = [1.0] * 19 + [1000.0]
        dist = MetricDistribution.from_values(values)
        assert dist.skewness > 0  # Right-skewed
        assert dist.gini > 0.5  # High inequality

    def test_percentiles_monotonic(self):
        values = list(range(1, 101))
        dist = MetricDistribution.from_values([float(x) for x in values])
        assert dist.p25 <= dist.median
        assert dist.median <= dist.p75
        assert dist.p75 <= dist.p90
        assert dist.p90 <= dist.p95
        assert dist.p95 <= dist.p99
        assert dist.p99 <= dist.max

    def test_cv_coefficient_of_variation(self):
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        dist = MetricDistribution.from_values(values)
        assert dist.cv > 0
        # CV = stddev / mean
        expected_cv = dist.stddev / dist.mean
        assert dist.cv == pytest.approx(expected_cv, abs=0.001)

    def test_iqr(self):
        values = [float(x) for x in range(1, 101)]
        dist = MetricDistribution.from_values(values)
        assert dist.iqr == dist.p75 - dist.p25
        assert dist.iqr > 0

    def test_top_and_bottom_shares(self):
        # With uniform values, shares should be proportional
        values = [10.0] * 100
        dist = MetricDistribution.from_values(values)
        assert dist.top_10_pct_share == pytest.approx(0.1, abs=0.02)
        assert dist.top_20_pct_share == pytest.approx(0.2, abs=0.02)
        assert dist.bottom_50_pct_share == pytest.approx(0.5, abs=0.02)

    def test_highly_unequal_distribution(self):
        # One file has all the code
        values = [0.0] * 9 + [1000.0]
        dist = MetricDistribution.from_values(values)
        assert dist.top_10_pct_share == 1.0
        assert dist.bottom_50_pct_share == 0.0

    def test_small_sample_percentiles(self):
        # With fewer than 10 values, p90 defaults to max
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        dist = MetricDistribution.from_values(values)
        assert dist.p90 == 5.0  # Falls back to max
        assert dist.p95 == 5.0
        assert dist.p99 == 5.0


# ---------------------------------------------------------------------------
# Tests: Individual inequality metrics
# ---------------------------------------------------------------------------

class TestComputeGini:
    """Tests for compute_gini."""

    def test_perfect_equality(self):
        assert compute_gini([10, 10, 10, 10]) == pytest.approx(0.0, abs=0.01)

    def test_perfect_inequality(self):
        # One person has everything
        values = [0, 0, 0, 0, 0, 0, 0, 0, 0, 100]
        gini = compute_gini(values)
        assert gini > 0.8

    def test_moderate_inequality(self):
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        gini = compute_gini(values)
        assert 0.1 < gini < 0.5

    def test_empty_returns_zero(self):
        assert compute_gini([]) == 0.0

    def test_single_value_returns_zero(self):
        assert compute_gini([42]) == 0.0

    def test_all_zeros_returns_zero(self):
        assert compute_gini([0, 0, 0]) == 0.0


class TestComputeTheil:
    """Tests for compute_theil."""

    def test_equal_values(self):
        assert compute_theil([10, 10, 10, 10]) == pytest.approx(0.0, abs=0.001)

    def test_unequal_values(self):
        values = [1, 2, 3, 4, 100]
        assert compute_theil(values) > 0

    def test_empty_returns_zero(self):
        assert compute_theil([]) == 0.0

    def test_single_value(self):
        assert compute_theil([42]) == 0.0

    def test_all_zeros_returns_zero(self):
        assert compute_theil([0, 0, 0]) == 0.0

    def test_mixed_zero_nonzero(self):
        # Zeros are filtered out for log calculation
        result = compute_theil([0, 10, 10])
        assert result == pytest.approx(0.0, abs=0.001)


class TestComputeHoover:
    """Tests for compute_hoover."""

    def test_equal_values(self):
        assert compute_hoover([10, 10, 10, 10]) == pytest.approx(0.0, abs=0.001)

    def test_unequal_values(self):
        values = [0, 0, 0, 100]
        hoover = compute_hoover(values)
        assert 0 < hoover <= 1

    def test_empty_returns_zero(self):
        assert compute_hoover([]) == 0.0

    def test_single_value(self):
        assert compute_hoover([42]) == 0.0

    def test_all_zeros(self):
        assert compute_hoover([0, 0, 0]) == 0.0


class TestComputePalma:
    """Tests for compute_palma."""

    def test_equal_values(self):
        values = [10] * 20
        palma = compute_palma(values)
        # Top 10% share / bottom 40% share ~ 10%/40% ~ 0.25
        assert palma == pytest.approx(0.25, abs=0.1)

    def test_very_unequal(self):
        values = [1] * 9 + [1000]
        palma = compute_palma(values)
        assert palma > 10  # Very high inequality

    def test_too_few_values(self):
        assert compute_palma([1, 2, 3]) == 0.0

    def test_bottom_zero_returns_inf(self):
        values = [0] * 9 + [100]
        palma = compute_palma(values)
        assert math.isinf(palma)


class TestComputeTopShare:
    """Tests for compute_top_share."""

    def test_uniform(self):
        values = [10] * 10
        assert compute_top_share(values, 0.10) == pytest.approx(0.1, abs=0.02)

    def test_all_in_top(self):
        values = [0] * 9 + [100]
        assert compute_top_share(values, 0.10) == 1.0

    def test_empty(self):
        assert compute_top_share([], 0.10) == 0.0

    def test_all_zeros(self):
        assert compute_top_share([0, 0, 0], 0.10) == 0.0


class TestComputeBottomShare:
    """Tests for compute_bottom_share."""

    def test_uniform(self):
        values = [10] * 10
        assert compute_bottom_share(values, 0.50) == pytest.approx(0.5, abs=0.02)

    def test_bottom_has_nothing(self):
        values = [0] * 5 + [100] * 5
        assert compute_bottom_share(values, 0.50) == 0.0

    def test_empty(self):
        assert compute_bottom_share([], 0.50) == 0.0


# ---------------------------------------------------------------------------
# Tests: Skewness and Kurtosis
# ---------------------------------------------------------------------------

class TestComputeSkewness:
    """Tests for compute_skewness."""

    def test_symmetric_distribution(self):
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        skew = compute_skewness(values, 5.5)
        assert abs(skew) < 0.5  # Nearly symmetric

    def test_right_skewed(self):
        values = [1, 1, 1, 1, 1, 1, 1, 1, 1, 100]
        mean = sum(values) / len(values)
        skew = compute_skewness(values, mean)
        assert skew > 0

    def test_too_few_values(self):
        assert compute_skewness([1, 2], 1.5) == 0

    def test_zero_stddev(self):
        assert compute_skewness([5, 5, 5], 5.0) == 0


class TestComputeKurtosis:
    """Tests for compute_kurtosis."""

    def test_too_few_values(self):
        assert compute_kurtosis([1, 2, 3], 2.0) == 0

    def test_zero_stddev(self):
        assert compute_kurtosis([5, 5, 5, 5], 5.0) == 0

    def test_normal_like(self):
        # Uniform distribution has kurtosis of -1.2
        values = list(range(1, 101))
        mean = sum(values) / len(values)
        kurtosis = compute_kurtosis([float(v) for v in values], mean)
        assert kurtosis < 0  # Platykurtic (flatter than normal)


# ---------------------------------------------------------------------------
# Tests: COCOMO
# ---------------------------------------------------------------------------

class TestComputeCocomo:
    """Tests for compute_cocomo."""

    def test_zero_kloc(self):
        params = COCOMO_PRESETS["sme"]
        result = compute_cocomo(0, params)
        assert result["effort_person_months"] == 0
        assert result["schedule_months"] == 0
        assert result["people"] == 0
        assert result["cost"] == 0

    def test_negative_kloc(self):
        params = COCOMO_PRESETS["sme"]
        result = compute_cocomo(-5, params)
        assert result["cost"] == 0

    def test_sme_preset_produces_positive_values(self):
        params = COCOMO_PRESETS["sme"]
        result = compute_cocomo(10.0, params)  # 10 KLOC
        assert result["effort_person_months"] > 0
        assert result["schedule_months"] > 0
        assert result["people"] > 0
        assert result["cost"] > 0

    def test_larger_codebase_costs_more(self):
        params = COCOMO_PRESETS["sme"]
        small = compute_cocomo(5.0, params)
        large = compute_cocomo(50.0, params)
        assert large["cost"] > small["cost"]
        assert large["effort_person_months"] > small["effort_person_months"]

    def test_enterprise_costs_more_than_startup(self):
        kloc = 10.0
        startup = compute_cocomo(kloc, COCOMO_PRESETS["early_startup"])
        enterprise = compute_cocomo(kloc, COCOMO_PRESETS["large_enterprise"])
        assert enterprise["cost"] > startup["cost"]

    def test_open_source_zero_cost(self):
        # avg_wage=0 means cost=0
        result = compute_cocomo(10.0, COCOMO_PRESETS["open_source"])
        assert result["cost"] == 0
        assert result["effort_person_months"] > 0

    def test_all_presets_produce_valid_results(self):
        for name, params in COCOMO_PRESETS.items():
            result = compute_cocomo(10.0, params)
            assert result["effort_person_months"] >= 0, f"{name} effort < 0"
            assert result["schedule_months"] >= 0, f"{name} schedule < 0"
            assert result["people"] >= 0, f"{name} people < 0"
            assert result["cost"] >= 0, f"{name} cost < 0"


# ---------------------------------------------------------------------------
# Tests: File Classification
# ---------------------------------------------------------------------------

class TestClassifyFile:
    """Tests for classify_file."""

    def test_python_test_file(self):
        assert classify_file("tests/test_main.py", "test_main.py", ".py") == "test"

    def test_python_test_suffix(self):
        assert classify_file("src/main_test.py", "main_test.py", ".py") == "test"

    def test_typescript_spec_file(self):
        assert classify_file("src/app.spec.ts", "app.spec.ts", ".ts") == "test"

    def test_javascript_test_file(self):
        assert classify_file("src/app.test.js", "app.test.js", ".js") == "test"

    def test_csharp_test_file(self):
        assert classify_file("Tests/MyTests.cs", "MyTests.cs", ".cs") == "test"

    def test_go_test_file(self):
        assert classify_file("pkg/main_test.go", "main_test.go", ".go") == "test"

    def test_test_directory(self):
        assert classify_file("tests/helpers/util.py", "util.py", ".py") == "test"

    def test_jest_directory(self):
        assert classify_file("__tests__/app.js", "app.js", ".js") == "test"

    def test_ci_github_actions(self):
        assert classify_file(".github/workflows/ci.yml", "ci.yml", ".yml") == "ci"

    def test_ci_jenkinsfile(self):
        assert classify_file("Jenkinsfile", "Jenkinsfile", "") == "ci"

    def test_build_makefile(self):
        assert classify_file("Makefile", "Makefile", "") == "build"

    def test_build_csproj(self):
        assert classify_file("src/App.csproj", "App.csproj", ".csproj") == "build"

    def test_config_package_json(self):
        assert classify_file("package.json", "package.json", ".json") == "config"

    def test_config_yaml(self):
        assert classify_file("config/settings.yaml", "settings.yaml", ".yaml") == "config"

    def test_config_toml(self):
        assert classify_file("pyproject.toml", "pyproject.toml", ".toml") == "config"

    def test_docs_markdown(self):
        assert classify_file("README.md", "README.md", ".md") == "docs"

    def test_docs_directory(self):
        assert classify_file("docs/guide.html", "guide.html", ".html") == "docs"

    def test_source_file(self):
        assert classify_file("src/main.py", "main.py", ".py") is None

    def test_source_csharp(self):
        assert classify_file("src/App.cs", "App.cs", ".cs") is None

    def test_github_yaml_is_ci_not_config(self):
        # .github YAML should be classified as CI, not config
        assert classify_file(".github/workflows/test.yml", "test.yml", ".yml") == "ci"


# ---------------------------------------------------------------------------
# Tests: normalize_field_names
# ---------------------------------------------------------------------------

class TestNormalizeFieldNames:
    """Tests for normalize_field_names."""

    def test_maps_known_fields(self):
        raw = {"Name": "Python", "Lines": 100, "Code": 80, "Complexity": 5}
        result = normalize_field_names(raw)
        assert result["name"] == "Python"
        assert result["lines"] == 100
        assert result["code"] == 80
        assert result["complexity"] == 5

    def test_unknown_fields_lowercased(self):
        raw = {"CustomField": "value"}
        result = normalize_field_names(raw)
        assert result["customfield"] == "value"

    def test_preserves_values(self):
        raw = {"Binary": True, "ULOC": 42}
        result = normalize_field_names(raw)
        assert result["binary"] is True
        assert result["uloc"] == 42


# ---------------------------------------------------------------------------
# Tests: Formatting helpers
# ---------------------------------------------------------------------------

class TestFormattingHelpers:
    """Tests for terminal formatting helpers."""

    def test_format_number_integer(self):
        assert format_number(1234) == "1,234"

    def test_format_number_decimals(self):
        assert format_number(1234.567, 2) == "1,234.57"

    def test_format_money(self):
        assert format_money(50000) == "$50,000"

    def test_format_percent(self):
        assert format_percent(0.753) == "75.3%"

    def test_truncate_path_short_enough(self):
        assert truncate_path_middle("src/main.py", 50) == "src/main.py"

    def test_truncate_path_too_long(self):
        long_path = "a" * 100
        result = truncate_path_middle(long_path, 30)
        assert len(result) == 30
        assert "..." in result

    def test_color_disabled(self):
        set_color_enabled(False)
        result = c("hello", Colors.RED)
        assert result == "hello"
        assert "\033" not in result
        set_color_enabled(True)  # Reset

    def test_color_enabled(self):
        set_color_enabled(True)
        result = c("hello", Colors.RED)
        assert "\033" in result
        assert "hello" in result

    def test_strip_ansi(self):
        colored = f"\033[31mhello\033[0m"
        assert strip_ansi(colored) == "hello"

    def test_strip_ansi_plain(self):
        assert strip_ansi("hello") == "hello"
