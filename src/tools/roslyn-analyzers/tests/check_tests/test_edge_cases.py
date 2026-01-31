"""Tests for roslyn-analyzers edge case checks (EC-9 to EC-12).

Tests the new edge case checks including:
- EC-9: NuGet analyzers evaluation
- EC-10: Severity mapping validation
- EC-11: Framework-specific rules
- EC-12: Multi-targeting evaluation
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from checks import CheckResult
from checks.edge_cases import (
    ec9_nuget_analyzers,
    ec10_severity_mapping,
    ec11_framework_specific,
    ec12_multi_targeting,
    run_all_edge_case_checks,
)


class TestEC9NuGetAnalyzers:
    """Tests for EC-9: NuGet-delivered analyzers evaluation."""

    def test_ec9_passes_with_nuget_package_info(self):
        """EC-9 should pass with full score when NuGet packages are documented."""
        analysis = {
            "metadata": {
                "nuget_analyzer_packages": [
                    "Microsoft.CodeAnalysis.NetAnalyzers",
                    "StyleCop.Analyzers",
                ],
                "analyzer_assemblies": [
                    "Microsoft.CodeAnalysis.CSharp.dll",
                ],
            },
            "files": [
                {"violations": [{"rule_id": "CA1001", "message": "Test"}]},
            ],
        }

        result = ec9_nuget_analyzers(analysis, {})

        assert result.check_id == "EC-9"
        assert result.category == "edge_cases"
        assert result.passed is True
        assert result.score == 1.0
        assert "nuget analyzer info" in result.message.lower()

    def test_ec9_partial_with_ca_diagnostics(self):
        """EC-9 should have partial score when CA diagnostics are detected."""
        analysis = {
            "metadata": {},
            "files": [
                {"violations": [
                    {"rule_id": "CA1001", "message": "Test"},
                    {"rule_id": "CA2000", "message": "Test"},
                ]},
            ],
        }

        result = ec9_nuget_analyzers(analysis, {})

        assert result.check_id == "EC-9"
        assert result.passed is True
        assert result.score == 0.8
        assert "ca diagnostics" in result.message.lower()
        assert "CA" in result.evidence["diagnostic_prefixes"]

    def test_ec9_passes_default_without_nuget_info(self):
        """EC-9 should pass with lower score when no NuGet metadata."""
        analysis = {
            "metadata": {},
            "files": [
                {"violations": [{"rule_id": "CS8618", "message": "Test"}]},
            ],
        }

        result = ec9_nuget_analyzers(analysis, {})

        assert result.check_id == "EC-9"
        assert result.passed is True
        assert result.score == 0.5
        assert "no nuget analyzer metadata" in result.message.lower()

    def test_ec9_extracts_multiple_prefixes(self):
        """EC-9 should extract all diagnostic prefixes."""
        analysis = {
            "metadata": {},
            "files": [
                {"violations": [
                    {"rule_id": "CA1001", "message": "Test"},
                    {"rule_id": "CS8618", "message": "Test"},
                    {"rule_id": "IDE0060", "message": "Test"},
                    {"rule_id": "SA1234", "message": "Test"},
                ]},
            ],
        }

        result = ec9_nuget_analyzers(analysis, {})

        assert result.check_id == "EC-9"
        prefixes = result.evidence["diagnostic_prefixes"]
        assert "CA" in prefixes
        assert "CS" in prefixes
        assert "IDE" in prefixes
        assert "SA" in prefixes

    def test_ec9_handles_empty_analysis(self):
        """EC-9 should handle empty analysis gracefully."""
        analysis = {
            "metadata": {},
            "files": [],
        }

        result = ec9_nuget_analyzers(analysis, {})

        assert result.check_id == "EC-9"
        assert result.passed is True


class TestEC10SeverityMapping:
    """Tests for EC-10: Severity mapping validation."""

    def test_ec10_passes_with_correct_severities(self):
        """EC-10 should pass when severities match ground truth."""
        analysis = {
            "files": [
                {
                    "path": "src/test.cs",
                    "violations": [
                        {"rule_id": "CA1001", "severity": "error"},
                        {"rule_id": "CA2000", "severity": "warning"},
                    ],
                },
            ],
        }
        ground_truth = {
            "files": {
                "test.cs": {
                    "expected_diagnostics": [
                        {"id": "CA1001", "expected_severity": "error"},
                        {"id": "CA2000", "expected_severity": "warning"},
                    ],
                },
            },
        }

        result = ec10_severity_mapping(analysis, ground_truth)

        assert result.check_id == "EC-10"
        assert result.category == "edge_cases"
        assert result.passed is True
        assert result.score == 1.0
        assert "2/2" in result.message

    def test_ec10_fails_with_mismatched_severities(self):
        """EC-10 should fail when severities don't match."""
        analysis = {
            "files": [
                {
                    "path": "src/test.cs",
                    "violations": [
                        {"rule_id": "CA1001", "severity": "warning"},  # Wrong
                        {"rule_id": "CA2000", "severity": "info"},  # Wrong
                    ],
                },
            ],
        }
        ground_truth = {
            "files": {
                "test.cs": {
                    "expected_diagnostics": [
                        {"id": "CA1001", "expected_severity": "error"},
                        {"id": "CA2000", "expected_severity": "warning"},
                    ],
                },
            },
        }

        result = ec10_severity_mapping(analysis, ground_truth)

        assert result.check_id == "EC-10"
        assert result.passed is False
        assert result.score == 0.0
        assert len(result.evidence["mismatches"]) == 2

    def test_ec10_partial_match_scores_correctly(self):
        """EC-10 should score partial severity matches."""
        analysis = {
            "files": [
                {
                    "path": "src/test.cs",
                    "violations": [
                        {"rule_id": "CA1001", "severity": "error"},  # Correct
                        {"rule_id": "CA2000", "severity": "info"},  # Wrong
                    ],
                },
            ],
        }
        ground_truth = {
            "files": {
                "test.cs": {
                    "expected_diagnostics": [
                        {"id": "CA1001", "expected_severity": "error"},
                        {"id": "CA2000", "expected_severity": "warning"},
                    ],
                },
            },
        }

        result = ec10_severity_mapping(analysis, ground_truth)

        assert result.check_id == "EC-10"
        assert result.score == 0.5
        assert result.passed is False  # Below 0.8 threshold

    def test_ec10_skips_without_severity_expectations(self):
        """EC-10 should skip when no severity expectations in ground truth."""
        analysis = {
            "files": [
                {
                    "path": "src/test.cs",
                    "violations": [{"rule_id": "CA1001", "severity": "error"}],
                },
            ],
        }
        ground_truth = {
            "files": {
                "test.cs": {
                    "expected_diagnostics": [
                        {"id": "CA1001"},  # No expected_severity
                    ],
                },
            },
        }

        result = ec10_severity_mapping(analysis, ground_truth)

        assert result.check_id == "EC-10"
        assert result.passed is True
        assert result.score == 1.0
        assert "skipped" in result.message.lower()

    def test_ec10_handles_case_insensitive_severity(self):
        """EC-10 should compare severities case-insensitively."""
        analysis = {
            "files": [
                {
                    "path": "test.cs",
                    "violations": [{"rule_id": "CA1001", "severity": "ERROR"}],
                },
            ],
        }
        ground_truth = {
            "files": {
                "test.cs": {
                    "expected_diagnostics": [
                        {"id": "CA1001", "expected_severity": "error"},
                    ],
                },
            },
        }

        result = ec10_severity_mapping(analysis, ground_truth)

        assert result.check_id == "EC-10"
        assert result.passed is True
        assert result.score == 1.0


class TestEC11FrameworkSpecific:
    """Tests for EC-11: Framework-specific rules validation."""

    def test_ec11_passes_with_tfm_info(self):
        """EC-11 should pass with full score when TFM is captured."""
        analysis = {
            "metadata": {
                "target_frameworks": ["net8.0"],
                "target_framework_moniker": "net8.0",
            },
            "files": [],
        }

        result = ec11_framework_specific(analysis, {})

        assert result.check_id == "EC-11"
        assert result.category == "edge_cases"
        assert result.passed is True
        assert result.score == 1.0
        assert "target framework captured" in result.message.lower()

    def test_ec11_partial_with_framework_diagnostics(self):
        """EC-11 should have partial score when framework-specific diagnostics detected."""
        analysis = {
            "metadata": {},
            "files": [
                {
                    "violations": [
                        {"rule_id": "CA1234", "message": "This API is not available in .NET Framework 4.8"},
                    ],
                },
            ],
        }

        result = ec11_framework_specific(analysis, {})

        assert result.check_id == "EC-11"
        assert result.passed is True
        assert result.score == 0.8
        assert "framework-specific diagnostics" in result.message.lower()

    def test_ec11_detects_multiple_framework_keywords(self):
        """EC-11 should detect various framework keywords."""
        analysis = {
            "metadata": {},
            "files": [
                {
                    "violations": [
                        {"rule_id": "CA1234", "message": "Only available in .NET Core"},
                        {"rule_id": "CA2345", "message": "Deprecated in netstandard"},
                        {"rule_id": "CA3456", "message": "Use net6 instead"},
                    ],
                },
            ],
        }

        result = ec11_framework_specific(analysis, {})

        assert result.check_id == "EC-11"
        assert result.passed is True
        assert result.score == 0.8
        assert len(result.evidence["framework_specific_diagnostics"]) >= 1

    def test_ec11_passes_default_without_framework_info(self):
        """EC-11 should pass with lower score when no framework info."""
        analysis = {
            "metadata": {},
            "files": [
                {"violations": [{"rule_id": "CA1001", "message": "Generic message"}]},
            ],
        }

        result = ec11_framework_specific(analysis, {})

        assert result.check_id == "EC-11"
        assert result.passed is True
        assert result.score == 0.5

    def test_ec11_handles_empty_analysis(self):
        """EC-11 should handle empty analysis gracefully."""
        analysis = {"metadata": {}, "files": []}

        result = ec11_framework_specific(analysis, {})

        assert result.check_id == "EC-11"
        assert result.passed is True


class TestEC12MultiTargeting:
    """Tests for EC-12: Multi-targeting evaluation."""

    def test_ec12_passes_with_full_tfm_breakdown(self):
        """EC-12 should pass with full score when per-TFM diagnostics available."""
        analysis = {
            "metadata": {
                "target_frameworks": ["net48", "net6.0"],
                "project_properties": {"TargetFrameworks": "net48;net6.0"},
                "diagnostics_by_tfm": {
                    "net48": [{"rule_id": "CA1001"}],
                    "net6.0": [{"rule_id": "CA2000"}],
                },
            },
            "files": [],
        }

        result = ec12_multi_targeting(analysis, {})

        assert result.check_id == "EC-12"
        assert result.category == "edge_cases"
        assert result.passed is True
        assert result.score == 1.0
        assert "fully supported" in result.message.lower()
        assert result.evidence["has_per_tfm_breakdown"] is True

    def test_ec12_partial_with_multi_target_no_breakdown(self):
        """EC-12 should have partial score when multi-target detected but no breakdown."""
        analysis = {
            "metadata": {
                "target_frameworks": ["net48", "net6.0"],
                "project_properties": {"TargetFrameworks": "net48;net6.0"},
            },
            "files": [],
        }

        result = ec12_multi_targeting(analysis, {})

        assert result.check_id == "EC-12"
        assert result.passed is True
        assert result.score == 0.7
        assert "no per-tfm breakdown" in result.message.lower()

    def test_ec12_detects_multi_target_from_project_props(self):
        """EC-12 should detect multi-targeting from project properties."""
        analysis = {
            "metadata": {
                "project_properties": {"TargetFrameworks": "netstandard2.0;net6.0;net8.0"},
            },
            "files": [],
        }

        result = ec12_multi_targeting(analysis, {})

        assert result.check_id == "EC-12"
        assert result.passed is True
        assert result.score == 0.7
        assert result.evidence["is_multi_target"] is True

    def test_ec12_passes_for_single_target(self):
        """EC-12 should pass with lower score for single-target projects."""
        analysis = {
            "metadata": {
                "target_frameworks": ["net8.0"],
                "project_properties": {"TargetFramework": "net8.0"},
            },
            "files": [],
        }

        result = ec12_multi_targeting(analysis, {})

        assert result.check_id == "EC-12"
        assert result.passed is True
        assert result.score == 0.5
        assert "single-target" in result.message.lower()
        assert result.evidence["is_multi_target"] is False

    def test_ec12_handles_empty_metadata(self):
        """EC-12 should handle missing metadata gracefully."""
        analysis = {
            "metadata": {},
            "files": [],
        }

        result = ec12_multi_targeting(analysis, {})

        assert result.check_id == "EC-12"
        assert result.passed is True
        assert result.score == 0.5

    def test_ec12_provides_diagnostics_count_by_tfm(self):
        """EC-12 should report diagnostic counts per TFM."""
        analysis = {
            "metadata": {
                "diagnostics_by_tfm": {
                    "net48": [{"id": 1}, {"id": 2}, {"id": 3}],
                    "net6.0": [{"id": 1}],
                },
            },
            "files": [],
        }

        result = ec12_multi_targeting(analysis, {})

        assert result.check_id == "EC-12"
        assert result.evidence["diagnostics_by_tfm"] == {"net48": 3, "net6.0": 1}


class TestRunAllEdgeCaseChecks:
    """Tests for run_all_edge_case_checks including EC-9 through EC-12."""

    @pytest.fixture
    def sample_analysis(self):
        """Sample analysis result for testing."""
        return {
            "metadata": {
                "timestamp": "2026-01-30T10:00:00Z",
                "analysis_duration_ms": 1000,
            },
            "files": [
                {
                    "path": "src/test.cs",
                    "lines_of_code": 100,
                    "violations": [
                        {"rule_id": "CA1001", "severity": "error", "message": "Test"},
                    ],
                },
            ],
        }

    @pytest.fixture
    def sample_ground_truth(self):
        """Sample ground truth for testing."""
        return {
            "files": {},
        }

    def test_includes_ec9_through_ec12(self, sample_analysis, sample_ground_truth):
        """run_all_edge_case_checks should include EC-9 through EC-12."""
        results = run_all_edge_case_checks(sample_analysis, sample_ground_truth)

        check_ids = [r.check_id for r in results]
        assert "EC-9" in check_ids
        assert "EC-10" in check_ids
        assert "EC-11" in check_ids
        assert "EC-12" in check_ids

    def test_returns_twelve_checks(self, sample_analysis, sample_ground_truth):
        """run_all_edge_case_checks should return all 12 checks."""
        results = run_all_edge_case_checks(sample_analysis, sample_ground_truth)

        assert len(results) == 12
        check_ids = [r.check_id for r in results]
        for i in range(1, 13):
            assert f"EC-{i}" in check_ids, f"EC-{i} should be included"

    def test_all_checks_return_check_result(self, sample_analysis, sample_ground_truth):
        """All edge case checks should return CheckResult objects."""
        results = run_all_edge_case_checks(sample_analysis, sample_ground_truth)

        for result in results:
            assert isinstance(result, CheckResult)
            assert result.category == "edge_cases"
            assert isinstance(result.passed, bool)
            assert 0.0 <= result.score <= 1.0
