"""Tests for directory_analyzer.py - focusing on correctness."""

import sys
from pathlib import Path

import pytest

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from directory_analyzer import (
    MetricDistribution,
    compute_gini,
    compute_theil,
    compute_hoover,
    compute_palma,
    compute_top_share,
    compute_bottom_share,
    classify_file,
    compute_directory_stats,
    compute_language_stats,
    analyze_directories,
    format_file_entry,
)


# =============================================================================
# Test Fixtures
# =============================================================================


def create_test_file_tree():
    """Create a nested file structure for testing."""
    return [
        {"Location": "src/main.py", "Code": 100, "Lines": 120, "Comment": 10, "Blank": 10, "Bytes": 2500, "Complexity": 15, "Uloc": 90, "Language": "Python"},
        {"Location": "src/utils.py", "Code": 80, "Lines": 95, "Comment": 8, "Blank": 7, "Bytes": 2000, "Complexity": 8, "Uloc": 75, "Language": "Python"},
        {"Location": "src/lib/helper.py", "Code": 60, "Lines": 70, "Comment": 5, "Blank": 5, "Bytes": 1500, "Complexity": 5, "Uloc": 55, "Language": "Python"},
        {"Location": "src/lib/core.py", "Code": 200, "Lines": 230, "Comment": 20, "Blank": 10, "Bytes": 5000, "Complexity": 25, "Uloc": 180, "Language": "Python"},
        {"Location": "tests/test_main.py", "Code": 50, "Lines": 60, "Comment": 5, "Blank": 5, "Bytes": 1200, "Complexity": 3, "Uloc": 45, "Language": "Python"},
        {"Location": "tests/test_utils.py", "Code": 40, "Lines": 50, "Comment": 5, "Blank": 5, "Bytes": 1000, "Complexity": 2, "Uloc": 35, "Language": "Python"},
    ]


def create_polyglot_files():
    """Create files with multiple languages."""
    return [
        {"Location": "src/main.py", "Code": 100, "Lines": 120, "Comment": 10, "Blank": 10, "Bytes": 2500, "Complexity": 10, "Uloc": 90, "Language": "Python"},
        {"Location": "src/utils.py", "Code": 80, "Lines": 95, "Comment": 8, "Blank": 7, "Bytes": 2000, "Complexity": 8, "Uloc": 75, "Language": "Python"},
        {"Location": "src/helper.py", "Code": 60, "Lines": 70, "Comment": 5, "Blank": 5, "Bytes": 1500, "Complexity": 5, "Uloc": 55, "Language": "Python"},
        {"Location": "src/app.ts", "Code": 150, "Lines": 180, "Comment": 15, "Blank": 15, "Bytes": 4000, "Complexity": 12, "Uloc": 140, "Language": "TypeScript"},
        {"Location": "src/index.ts", "Code": 120, "Lines": 140, "Comment": 12, "Blank": 8, "Bytes": 3000, "Complexity": 9, "Uloc": 110, "Language": "TypeScript"},
        {"Location": "src/types.ts", "Code": 80, "Lines": 90, "Comment": 5, "Blank": 5, "Bytes": 2000, "Complexity": 2, "Uloc": 75, "Language": "TypeScript"},
        {"Location": "src/server.go", "Code": 200, "Lines": 240, "Comment": 20, "Blank": 20, "Bytes": 5000, "Complexity": 20, "Uloc": 180, "Language": "Go"},
        {"Location": "src/handler.go", "Code": 100, "Lines": 120, "Comment": 10, "Blank": 10, "Bytes": 2500, "Complexity": 10, "Uloc": 90, "Language": "Go"},
        {"Location": "src/utils.go", "Code": 80, "Lines": 100, "Comment": 10, "Blank": 10, "Bytes": 2000, "Complexity": 8, "Uloc": 70, "Language": "Go"},
    ]


def create_mixed_file_tree():
    """Create files with various classifications."""
    return [
        {"Location": "src/main.py", "Code": 100, "Lines": 120, "Comment": 10, "Blank": 10, "Bytes": 2500, "Complexity": 10, "Uloc": 90, "Language": "Python"},
        {"Location": "src/app.ts", "Code": 150, "Lines": 180, "Comment": 15, "Blank": 15, "Bytes": 4000, "Complexity": 12, "Uloc": 140, "Language": "TypeScript"},
        {"Location": "tests/test_main.py", "Code": 50, "Lines": 60, "Comment": 5, "Blank": 5, "Bytes": 1200, "Complexity": 3, "Uloc": 45, "Language": "Python"},
        {"Location": "tests/test_app.spec.ts", "Code": 80, "Lines": 100, "Comment": 10, "Blank": 10, "Bytes": 2000, "Complexity": 5, "Uloc": 70, "Language": "TypeScript"},
        {"Location": "config.yaml", "Code": 30, "Lines": 35, "Comment": 5, "Blank": 0, "Bytes": 800, "Complexity": 0, "Uloc": 25, "Language": "YAML"},
        {"Location": "README.md", "Code": 0, "Lines": 100, "Comment": 0, "Blank": 10, "Bytes": 3000, "Complexity": 0, "Uloc": 0, "Language": "Markdown"},
        {"Location": "Makefile", "Code": 50, "Lines": 60, "Comment": 5, "Blank": 5, "Bytes": 1500, "Complexity": 0, "Uloc": 45, "Language": "Makefile"},
        {"Location": ".github/workflows/ci.yml", "Code": 40, "Lines": 50, "Comment": 5, "Blank": 5, "Bytes": 1200, "Complexity": 0, "Uloc": 35, "Language": "YAML"},
    ]


# =============================================================================
# Unit Tests: Inequality Metrics
# =============================================================================


class TestInequalityMetrics:
    """Test inequality metric computations against known values."""

    def test_gini_perfect_equality(self):
        """All equal values -> Gini = 0."""
        values = [100, 100, 100, 100, 100]
        assert compute_gini(values) == 0.0

    def test_gini_perfect_inequality(self):
        """One has everything -> Gini = 1 - 1/n."""
        values = [0, 0, 0, 0, 1000]
        gini = compute_gini(values)
        # With zeros, formula gives (n-1)/n = 0.8
        assert 0.79 <= gini <= 0.81

    def test_gini_known_distribution(self):
        """Verify against hand-calculated example."""
        values = [1, 2, 3, 4, 10]
        gini = compute_gini(values)
        # Known Gini for this distribution is approximately 0.32-0.40
        assert 0.30 <= gini <= 0.41  # Allow floating-point tolerance

    def test_gini_empty_or_single(self):
        """Edge cases for empty or single value."""
        assert compute_gini([]) == 0.0
        assert compute_gini([100]) == 0.0

    def test_theil_perfect_equality(self):
        """All equal values -> Theil = 0."""
        values = [50, 50, 50, 50]
        assert compute_theil(values) == 0.0

    def test_theil_high_inequality(self):
        """Highly unequal -> Theil > 0.5."""
        values = [1, 1, 1, 1, 100]
        theil = compute_theil(values)
        assert theil > 0.5

    def test_theil_empty_or_single(self):
        """Edge cases for Theil."""
        assert compute_theil([]) == 0.0
        assert compute_theil([100]) == 0.0

    def test_theil_with_zeros(self):
        """Theil handles zeros by filtering them."""
        values = [0, 0, 50, 50]
        theil = compute_theil(values)
        assert theil == 0.0  # Only equal positive values

    def test_hoover_perfect_equality(self):
        """All equal -> Hoover = 0."""
        values = [25, 25, 25, 25]
        assert compute_hoover(values) == 0.0

    def test_hoover_interpretation(self):
        """Hoover represents % that must be redistributed."""
        values = [0, 0, 50, 50]
        hoover = compute_hoover(values)
        # 50% of total (100) is above mean (25), so hoover = 0.5
        assert 0.45 <= hoover <= 0.55

    def test_hoover_empty(self):
        """Edge case for empty list."""
        assert compute_hoover([]) == 0.0

    def test_palma_balanced(self):
        """Roughly equal distribution -> Palma close to 1."""
        values = list(range(1, 11))  # 1-10
        palma = compute_palma(values)
        assert 0.3 <= palma <= 3.0

    def test_palma_minimum_size(self):
        """Palma requires at least 10 values."""
        values = [10, 20, 30, 40, 50]
        assert compute_palma(values) == 0.0

    def test_share_computation(self):
        """Verify top share calculations."""
        values = [10, 20, 30, 40]  # Total = 100
        # Top 25% (1 value = 40) should be 0.4
        top_25 = compute_top_share(values, 0.25)
        assert 0.38 <= top_25 <= 0.42

    def test_bottom_share_computation(self):
        """Verify bottom share calculations."""
        values = [10, 20, 30, 40]  # Total = 100
        # Bottom 50% (10+20=30) should be 0.3
        bottom_50 = compute_bottom_share(values, 0.50)
        assert 0.28 <= bottom_50 <= 0.32

    def test_shares_empty(self):
        """Edge cases for share functions."""
        assert compute_top_share([], 0.10) == 0.0
        assert compute_bottom_share([], 0.50) == 0.0

    def test_shares_all_zeros(self):
        """All zeros returns 0."""
        values = [0, 0, 0, 0]
        assert compute_top_share(values, 0.10) == 0.0
        assert compute_bottom_share(values, 0.50) == 0.0


# =============================================================================
# Unit Tests: File Classification
# =============================================================================


class TestFileClassification:
    """Test file classification logic."""

    @pytest.mark.parametrize("filename,expected", [
        # Test files - Python
        ("test_utils.py", "test"),
        ("utils_test.py", "test"),
        # Test files - TypeScript/JavaScript
        ("component.test.ts", "test"),
        ("component.spec.ts", "test"),
        ("component.test.js", "test"),
        ("component.spec.js", "test"),
        # Test files - Java
        ("UserServiceTest.java", "test"),
        ("UserServiceTests.java", "test"),
        # Test files - Go
        ("service_test.go", "test"),
        ("test_service.go", "test"),
        # Test files - Rust
        ("utils_test.rs", "test"),
        # Test files - C#
        ("ServiceTest.cs", "test"),
        ("ServiceTests.cs", "test"),
        # Config files
        ("config.yaml", "config"),
        ("settings.yml", "config"),
        ("app.toml", "config"),
        ("settings.ini", "config"),
        ("app.cfg", "config"),
        # Config files - specific names
        ("package.json", "config"),
        ("tsconfig.json", "config"),
        ("pyproject.toml", "config"),
        ("requirements.txt", "config"),
        ("cargo.toml", "config"),
        ("go.mod", "config"),
        # Config files - patterns
        ("app.config.js", "config"),
        (".env", "config"),
        (".env.local", "config"),
        # Docs
        ("README.md", "docs"),
        ("CHANGELOG.md", "docs"),
        ("api.rst", "docs"),
        ("notes.txt", "docs"),
        # Build
        ("Makefile", "build"),
        ("CMakeLists.txt", "build"),
        ("pom.xml", "build"),
        ("build.gradle", "build"),
        ("gulpfile.js", "build"),
        # Build - extensions
        ("Project.csproj", "build"),
        ("App.sln", "build"),
        # CI
        ("Jenkinsfile", "ci"),
        ("azure-pipelines.yml", "ci"),
        (".travis.yml", "ci"),
        # Source (no classification)
        ("main.py", None),
        ("server.go", None),
        ("App.tsx", None),
        ("index.js", None),
    ])
    def test_filename_classification(self, filename, expected):
        result = classify_file(f"/some/path/{filename}", filename, Path(filename).suffix)
        assert result == expected, f"Expected {expected} for {filename}, got {result}"

    def test_directory_based_classification_test(self):
        """Files in test directories get classified as test."""
        assert classify_file("tests/helper.py", "helper.py", ".py") == "test"
        assert classify_file("src/__tests__/util.js", "util.js", ".js") == "test"
        assert classify_file("test/fixtures.py", "fixtures.py", ".py") == "test"
        assert classify_file("spec/support.rb", "support.rb", ".rb") == "test"

    def test_directory_based_classification_ci(self):
        """Files in CI directories get classified as CI."""
        assert classify_file(".github/workflows/ci.yml", "ci.yml", ".yml") == "ci"
        assert classify_file(".circleci/config.yml", "config.yml", ".yml") == "ci"

    def test_directory_based_classification_docs(self):
        """Files in docs directories get classified as docs."""
        assert classify_file("docs/api/reference.md", "reference.md", ".md") == "docs"
        assert classify_file("documentation/guide.rst", "guide.rst", ".rst") == "docs"

    def test_yaml_in_ci_dir_is_ci_not_config(self):
        """YAML files in CI directories should be CI, not config."""
        assert classify_file(".github/workflows/test.yml", "test.yml", ".yml") == "ci"


# =============================================================================
# Unit Tests: Distribution Statistical Validity
# =============================================================================


class TestDistributionValidity:
    """Test distribution statistics are mathematically valid."""

    def test_percentile_monotonicity(self):
        """p25 <= median <= p75 <= p90 <= p95 <= p99."""
        import random
        random.seed(42)
        values = [random.randint(1, 1000) for _ in range(100)]
        dist = MetricDistribution.from_values(values)

        assert dist.min <= dist.p25
        assert dist.p25 <= dist.median
        assert dist.median <= dist.p75
        assert dist.p75 <= dist.p90
        assert dist.p90 <= dist.p95
        assert dist.p95 <= dist.p99
        assert dist.p99 <= dist.max

    def test_mean_within_bounds(self):
        """Mean must be between min and max."""
        values = [5, 10, 15, 100, 200]
        dist = MetricDistribution.from_values(values)
        assert dist.min <= dist.mean <= dist.max

    def test_stddev_non_negative(self):
        """Standard deviation >= 0."""
        values = [1, 1, 1, 1]  # All same
        dist = MetricDistribution.from_values(values)
        assert dist.stddev >= 0

    def test_cv_zero_for_uniform(self):
        """CV = 0 when all values are equal."""
        values = [50, 50, 50, 50]
        dist = MetricDistribution.from_values(values)
        assert dist.cv == 0

    def test_iqr_equals_p75_minus_p25(self):
        """IQR = P75 - P25."""
        values = list(range(1, 101))
        dist = MetricDistribution.from_values(values)
        assert abs(dist.iqr - (dist.p75 - dist.p25)) < 0.001

    def test_inequality_metrics_in_range(self):
        """All inequality metrics should be in valid ranges."""
        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        dist = MetricDistribution.from_values(values)

        # Gini: [0, 1]
        assert 0 <= dist.gini <= 1
        # Theil: [0, ln(n)] but practically [0, ~2] for most data
        assert dist.theil >= 0
        # Hoover: [0, 1]
        assert 0 <= dist.hoover <= 1
        # Palma: [0, inf) but typically < 10
        assert dist.palma >= 0
        # Shares: [0, 1]
        assert 0 <= dist.top_10_pct_share <= 1
        assert 0 <= dist.top_20_pct_share <= 1
        assert 0 <= dist.bottom_50_pct_share <= 1

    def test_empty_distribution(self):
        """Empty values should return zeroed distribution."""
        dist = MetricDistribution.from_values([])
        assert dist.min == 0
        assert dist.max == 0
        assert dist.mean == 0
        assert dist.gini == 0


# =============================================================================
# Integration Tests: Directory Stats Aggregation
# =============================================================================


class TestDirectoryAggregation:
    """Test that stats roll up correctly."""

    def test_recursive_gte_direct(self):
        """Recursive stats >= direct stats for all directories."""
        files = create_test_file_tree()
        result = analyze_directories(files)

        for d in result["directories"]:
            direct = d["direct"]
            recursive = d["recursive"]

            assert recursive["file_count"] >= direct["file_count"], \
                f"At {d['path']}: recursive {recursive['file_count']} < direct {direct['file_count']}"
            assert recursive["lines_code"] >= direct["lines_code"], \
                f"At {d['path']}: recursive LOC < direct LOC"
            assert recursive["complexity_total"] >= direct["complexity_total"], \
                f"At {d['path']}: recursive complexity < direct complexity"
            assert recursive["bytes"] >= direct["bytes"], \
                f"At {d['path']}: recursive bytes < direct bytes"

    def test_sum_direct_equals_total(self):
        """Sum of all direct.file_count should equal total files."""
        files = create_test_file_tree()
        result = analyze_directories(files)

        sum_direct = sum(d["direct"]["file_count"] for d in result["directories"])
        assert sum_direct == result["summary"]["total_files"]

    def test_root_recursive_equals_summary(self):
        """Top-level directories' recursive stats should sum to summary totals."""
        files = create_test_file_tree()
        result = analyze_directories(files)

        # Find all root directories (minimum depth)
        # When files are in multiple top-level dirs (src/, tests/),
        # all depth-0 dirs combined should match summary
        min_depth = min(d["depth"] for d in result["directories"])
        root_dirs = [d for d in result["directories"] if d["depth"] == min_depth]

        # Sum of all root directories' recursive stats should equal summary
        total_root_loc = sum(d["recursive"]["lines_code"] for d in root_dirs)
        total_root_files = sum(d["recursive"]["file_count"] for d in root_dirs)

        assert total_root_loc == result["summary"]["total_loc"]
        assert total_root_files == result["summary"]["total_files"]


# =============================================================================
# Integration Tests: Per-Language Breakdown
# =============================================================================


class TestLanguageBreakdown:
    """Test per-language stats are consistent."""

    def test_language_totals_match_aggregate(self):
        """Sum of by_language stats should equal aggregate stats."""
        files = create_polyglot_files()
        stats = compute_directory_stats(files)

        # Sum LOC across languages
        lang_loc_sum = sum(
            lang_stats["lines_code"]
            for lang_stats in stats["by_language"].values()
        )
        assert lang_loc_sum == stats["lines_code"]

        # Sum file counts
        lang_file_sum = sum(
            lang_stats["file_count"]
            for lang_stats in stats["by_language"].values()
        )
        assert lang_file_sum == stats["file_count"]

    def test_language_distributions_valid(self):
        """Each language's distributions should be valid."""
        files = create_polyglot_files()
        stats = compute_directory_stats(files)

        for lang, lang_stats in stats["by_language"].items():
            if lang_stats["file_count"] >= 3:
                dist = lang_stats["loc_distribution"]
                assert dist is not None, f"Language {lang} with {lang_stats['file_count']} files should have distribution"
                assert dist["min"] <= dist["mean"] <= dist["max"]
                assert dist["p25"] <= dist["median"] <= dist["p75"]


# =============================================================================
# Integration Tests: File Classification Counts
# =============================================================================


class TestFileClassificationCounts:
    """Test file classification aggregation."""

    def test_classifications_accounted_for(self):
        """All files should be accounted for in classifications."""
        files = create_mixed_file_tree()
        stats = compute_directory_stats(files)

        classified_count = (
            stats["test_file_count"] +
            stats["config_file_count"] +
            stats["docs_file_count"] +
            stats["build_file_count"] +
            stats["ci_file_count"]
        )
        # Some files are source (no classification)
        # All files should be either classified or source
        assert classified_count <= stats["file_count"]

    def test_test_loc_matches_test_files(self):
        """test_loc should be sum of LOC in test files only."""
        files = [
            {"Location": "tests/test_foo.py", "Code": 100, "Lines": 120, "Comment": 10, "Blank": 10, "Bytes": 2500, "Complexity": 5, "Uloc": 90, "Language": "Python"},
            {"Location": "src/foo.py", "Code": 200, "Lines": 230, "Comment": 20, "Blank": 10, "Bytes": 5000, "Complexity": 10, "Uloc": 180, "Language": "Python"},
            {"Location": "tests/test_bar.py", "Code": 150, "Lines": 170, "Comment": 10, "Blank": 10, "Bytes": 3500, "Complexity": 8, "Uloc": 140, "Language": "Python"},
        ]
        stats = compute_directory_stats(files)

        assert stats["test_file_count"] == 2
        assert stats["test_loc"] == 250  # 100 + 150


# =============================================================================
# Integration Tests: Structural Metrics
# =============================================================================


class TestStructuralMetrics:
    """Test structural directory metrics."""

    def test_leaf_detection(self):
        """Leaf directories have no subdirectories."""
        result = analyze_directories(create_test_file_tree())

        for d in result["directories"]:
            if d["is_leaf"]:
                assert d["child_count"] == 0
                assert len(d["subdirectories"]) == 0
            else:
                assert d["child_count"] > 0
                assert len(d["subdirectories"]) == d["child_count"]

    def test_depth_non_negative(self):
        """Depth should be non-negative."""
        result = analyze_directories(create_test_file_tree())

        for d in result["directories"]:
            assert d["depth"] >= 0

    def test_summary_structure_metrics(self):
        """Summary should have valid structural stats."""
        result = analyze_directories(create_test_file_tree())
        summary = result["summary"]

        assert summary["structure"]["max_depth"] >= 0
        assert summary["structure"]["avg_depth"] >= 0
        assert summary["structure"]["leaf_directory_count"] > 0
        assert summary["structure"]["avg_files_per_directory"] > 0


# =============================================================================
# Integration Tests: COCOMO All Presets
# =============================================================================


class TestCocomoPresets:
    """Test all 8 COCOMO presets are computed."""

    EXPECTED_PRESETS = [
        "early_startup", "growth_startup", "scale_up", "sme",
        "mid_market", "large_enterprise", "regulated", "open_source"
    ]

    def test_all_presets_present(self):
        """All 8 presets should be in summary.cocomo."""
        result = analyze_directories(create_test_file_tree())
        cocomo = result["summary"]["cocomo"]

        for preset in self.EXPECTED_PRESETS:
            assert preset in cocomo, f"Missing COCOMO preset: {preset}"
            assert "effort_person_months" in cocomo[preset]
            assert "schedule_months" in cocomo[preset]
            assert "people" in cocomo[preset]
            assert "cost" in cocomo[preset]

    def test_cocomo_ordering(self):
        """Larger orgs should have higher effort estimates."""
        result = analyze_directories(create_test_file_tree())
        cocomo = result["summary"]["cocomo"]

        # Effort should increase with org size
        assert cocomo["early_startup"]["effort_person_months"] < \
               cocomo["large_enterprise"]["effort_person_months"]

        # Open source cost should be 0
        assert cocomo["open_source"]["cost"] == 0


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_files_list(self):
        """Empty file list should return valid structure."""
        result = analyze_directories([])

        assert result["schema_version"] == "2.0"
        assert result["directories"] == []
        assert result["files"] == []
        assert result["summary"]["total_files"] == 0

    def test_single_file(self):
        """Single file should have valid stats but no distribution."""
        files = [{"Location": "src/main.py", "Code": 100, "Lines": 120, "Comment": 10, "Blank": 10, "Bytes": 2500, "Complexity": 5, "Uloc": 90, "Language": "Python"}]
        stats = compute_directory_stats(files)

        assert stats["file_count"] == 1
        assert stats["lines_code"] == 100
        # Distributions require >= 3 files
        assert stats["loc_distribution"] is None

    def test_two_files(self):
        """Two files: still no distribution."""
        files = [
            {"Location": "a.py", "Code": 50, "Lines": 60, "Comment": 5, "Blank": 5, "Bytes": 1000, "Complexity": 3, "Uloc": 45, "Language": "Python"},
            {"Location": "b.py", "Code": 100, "Lines": 120, "Comment": 10, "Blank": 10, "Bytes": 2500, "Complexity": 5, "Uloc": 90, "Language": "Python"},
        ]
        stats = compute_directory_stats(files)
        assert stats["loc_distribution"] is None

    def test_three_files(self):
        """Three files: distribution should be computed."""
        files = [
            {"Location": "a.py", "Code": 50, "Lines": 60, "Comment": 5, "Blank": 5, "Bytes": 1000, "Complexity": 3, "Uloc": 45, "Language": "Python"},
            {"Location": "b.py", "Code": 100, "Lines": 120, "Comment": 10, "Blank": 10, "Bytes": 2500, "Complexity": 5, "Uloc": 90, "Language": "Python"},
            {"Location": "c.py", "Code": 150, "Lines": 180, "Comment": 15, "Blank": 15, "Bytes": 3500, "Complexity": 10, "Uloc": 140, "Language": "Python"},
        ]
        stats = compute_directory_stats(files)
        assert stats["loc_distribution"] is not None
        assert stats["loc_distribution"]["min"] == 50
        assert stats["loc_distribution"]["max"] == 150

    def test_all_zero_values(self):
        """Handle files with zero complexity/loc."""
        files = [
            {"Location": "empty1.py", "Code": 0, "Lines": 0, "Comment": 0, "Blank": 0, "Bytes": 0, "Complexity": 0, "Uloc": 0, "Language": "Python"},
            {"Location": "empty2.py", "Code": 0, "Lines": 0, "Comment": 0, "Blank": 0, "Bytes": 0, "Complexity": 0, "Uloc": 0, "Language": "Python"},
            {"Location": "empty3.py", "Code": 0, "Lines": 0, "Comment": 0, "Blank": 0, "Bytes": 0, "Complexity": 0, "Uloc": 0, "Language": "Python"},
        ]
        stats = compute_directory_stats(files)

        assert stats["lines_code"] == 0
        assert stats["complexity_density"] == 0  # Avoid division by zero
        assert stats["dryness"] == 0

    def test_single_language(self):
        """Single language should still have by_language entry."""
        files = [
            {"Location": "a.py", "Code": 100, "Lines": 120, "Comment": 10, "Blank": 10, "Bytes": 2500, "Complexity": 5, "Uloc": 90, "Language": "Python"},
            {"Location": "b.py", "Code": 200, "Lines": 230, "Comment": 20, "Blank": 10, "Bytes": 5000, "Complexity": 10, "Uloc": 180, "Language": "Python"},
            {"Location": "c.py", "Code": 150, "Lines": 180, "Comment": 15, "Blank": 15, "Bytes": 3500, "Complexity": 8, "Uloc": 140, "Language": "Python"},
        ]
        stats = compute_directory_stats(files)

        assert "Python" in stats["by_language"]
        assert stats["by_language"]["Python"]["file_count"] == 3
        assert stats["by_language"]["Python"]["lines_code"] == 450


# =============================================================================
# Tests: Format File Entry
# =============================================================================


class TestFormatFileEntry:
    """Test format_file_entry function."""

    def test_basic_fields(self):
        """Test that all basic fields are present."""
        f = {
            "Location": "src/main.py",
            "Lines": 120,
            "Code": 100,
            "Comment": 10,
            "Blank": 10,
            "Bytes": 2500,
            "Complexity": 15,
            "Uloc": 90,
            "Language": "Python",
            "Minified": False,
            "Generated": False,
        }
        result = format_file_entry(f)

        assert result["path"] == "src/main.py"
        assert result["filename"] == "main.py"
        assert result["directory"] == "src"
        assert result["language"] == "Python"
        assert result["extension"] == ".py"
        assert result["lines_total"] == 120
        assert result["lines_code"] == 100
        assert result["lines_comment"] == 10
        assert result["lines_blank"] == 10
        assert result["complexity"] == 15

    def test_ratios_calculated(self):
        """Test that ratios are calculated correctly."""
        f = {
            "Location": "src/main.py",
            "Lines": 100,
            "Code": 80,
            "Comment": 10,
            "Blank": 10,
            "Bytes": 2000,
            "Complexity": 8,
            "Uloc": 72,
            "Language": "Python",
        }
        result = format_file_entry(f)

        assert result["comment_ratio"] == 0.1  # 10/100
        assert result["blank_ratio"] == 0.1  # 10/100
        assert result["code_ratio"] == 0.8  # 80/100
        assert result["complexity_density"] == 0.1  # 8/80
        assert result["dryness"] == 0.9  # 72/80

    def test_classification_applied(self):
        """Test that classification is applied."""
        f = {
            "Location": "tests/test_main.py",
            "Lines": 50,
            "Code": 40,
            "Comment": 5,
            "Blank": 5,
            "Bytes": 1000,
            "Complexity": 3,
            "Uloc": 35,
            "Language": "Python",
        }
        result = format_file_entry(f)
        assert result["classification"] == "test"

    def test_zero_lines_no_division_error(self):
        """Test that zero lines doesn't cause division error."""
        f = {
            "Location": "empty.py",
            "Lines": 0,
            "Code": 0,
            "Comment": 0,
            "Blank": 0,
            "Bytes": 0,
            "Complexity": 0,
            "Uloc": 0,
            "Language": "Python",
        }
        result = format_file_entry(f)
        assert result["comment_ratio"] == 0
        assert result["blank_ratio"] == 0
        assert result["code_ratio"] == 0
        assert result["complexity_density"] == 0
        assert result["dryness"] == 0
