"""Tests for sampling rationale section."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from insights.sections.sampling_rationale import (
    SamplingRationaleSection,
    _build_rationale,
    _compute_risk_drivers,
)


# ---------------------------------------------------------------------------
# _build_rationale tests
# ---------------------------------------------------------------------------


class TestBuildRationale:
    """Tests for _build_rationale helper."""

    def test_single_author_knowledge_silo(self):
        row = {
            "ccn_score": 0.3,
            "coupling_score": 0.2,
            "ownership_score": 0.5,
            "coverage_score": 0.3,
            "quality_score": 0.1,
            "unique_authors": 1,
            "churn_30d": 0,
            "total_coupling": 5,
        }
        rationale = _build_rationale(row)
        assert "single-author knowledge silo" in rationale

    def test_complex_plus_untested(self):
        row = {
            "ccn_score": 0.9,
            "coupling_score": 0.2,
            "ownership_score": 0.1,
            "coverage_score": 0.8,
            "quality_score": 0.1,
            "unique_authors": 3,
            "churn_30d": 0,
            "total_coupling": 5,
        }
        rationale = _build_rationale(row)
        assert "complex + untested" in rationale
        # Should NOT also say "low test coverage" since ccn > 0.7 triggers combined
        assert "low test coverage" not in rationale

    def test_high_coupling_with_value(self):
        row = {
            "ccn_score": 0.3,
            "coupling_score": 0.8,
            "ownership_score": 0.1,
            "coverage_score": 0.3,
            "quality_score": 0.1,
            "unique_authors": 5,
            "churn_30d": 0,
            "total_coupling": 25,
        }
        rationale = _build_rationale(row)
        assert "high coupling (fan_out + fan_in = 25)" in rationale

    def test_recently_changed_concentrated_ownership(self):
        row = {
            "ccn_score": 0.3,
            "coupling_score": 0.2,
            "ownership_score": 0.6,
            "coverage_score": 0.3,
            "quality_score": 0.1,
            "unique_authors": 3,
            "churn_30d": 5,
            "total_coupling": 5,
        }
        rationale = _build_rationale(row)
        assert "recently changed + concentrated ownership" in rationale

    def test_moderate_risk_fallback(self):
        row = {
            "ccn_score": 0.3,
            "coupling_score": 0.2,
            "ownership_score": 0.2,
            "coverage_score": 0.3,
            "quality_score": 0.1,
            "unique_authors": 5,
            "churn_30d": 0,
            "total_coupling": 3,
        }
        rationale = _build_rationale(row)
        assert "moderate multi-dimensional risk" in rationale

    def test_high_quality_issues(self):
        row = {
            "ccn_score": 0.3,
            "coupling_score": 0.2,
            "ownership_score": 0.1,
            "coverage_score": 0.3,
            "quality_score": 0.9,
            "unique_authors": 5,
            "churn_30d": 0,
            "total_coupling": 3,
        }
        rationale = _build_rationale(row)
        assert "high issue density" in rationale

    def test_none_scores_treated_as_zero(self):
        """Scores that come back as None should not cause errors."""
        row = {
            "ccn_score": None,
            "coupling_score": None,
            "ownership_score": None,
            "coverage_score": None,
            "quality_score": None,
            "unique_authors": None,
            "churn_30d": None,
            "total_coupling": None,
        }
        rationale = _build_rationale(row)
        assert "moderate multi-dimensional risk" in rationale

    def test_multiple_reasons_combined(self):
        row = {
            "ccn_score": 0.9,
            "coupling_score": 0.8,
            "ownership_score": 0.8,
            "coverage_score": 0.8,
            "quality_score": 0.9,
            "unique_authors": 1,
            "churn_30d": 0,
            "total_coupling": 20,
        }
        rationale = _build_rationale(row)
        # Should contain multiple reasons
        assert "complex + untested" in rationale
        assert "high coupling" in rationale
        assert "single-author knowledge silo" in rationale
        assert "high issue density" in rationale


# ---------------------------------------------------------------------------
# _compute_risk_drivers tests
# ---------------------------------------------------------------------------


class TestComputeRiskDrivers:
    """Tests for _compute_risk_drivers helper."""

    def test_different_dominant_factors(self):
        targets = [
            {"ccn_score": 0.9, "coupling_score": 0.1, "ownership_score": 0.1, "coverage_score": 0.1, "quality_score": 0.1},
            {"ccn_score": 0.1, "coupling_score": 0.9, "ownership_score": 0.1, "coverage_score": 0.1, "quality_score": 0.1},
            {"ccn_score": 0.1, "coupling_score": 0.1, "ownership_score": 0.9, "coverage_score": 0.1, "quality_score": 0.1},
        ]
        drivers = _compute_risk_drivers(targets)
        assert drivers["complexity"] == 1
        assert drivers["coupling"] == 1
        assert drivers["ownership"] == 1
        assert drivers["coverage"] == 0
        assert drivers["quality"] == 0

    def test_empty_targets(self):
        drivers = _compute_risk_drivers([])
        assert all(v == 0 for v in drivers.values())

    def test_all_same_dominant(self):
        targets = [
            {"ccn_score": 0.8, "coupling_score": 0.1, "ownership_score": 0.1, "coverage_score": 0.1, "quality_score": 0.1},
            {"ccn_score": 0.7, "coupling_score": 0.2, "ownership_score": 0.1, "coverage_score": 0.1, "quality_score": 0.1},
        ]
        drivers = _compute_risk_drivers(targets)
        assert drivers["complexity"] == 2
        assert sum(drivers.values()) == 2

    def test_none_scores_default_to_zero(self):
        targets = [
            {"ccn_score": None, "coupling_score": None, "ownership_score": 0.5, "coverage_score": None, "quality_score": None},
        ]
        drivers = _compute_risk_drivers(targets)
        assert drivers["ownership"] == 1


# ---------------------------------------------------------------------------
# SamplingRationaleSection tests
# ---------------------------------------------------------------------------


class TestSamplingRationaleSection:
    """Tests for SamplingRationaleSection.fetch_data."""

    def test_fetch_data_with_targets(self, mock_fetcher: MagicMock):
        """Verify fetch_data wires data correctly when targets exist."""
        section = SamplingRationaleSection()

        mock_targets = [
            {
                "relative_path": "src/engine.py",
                "composite_score": 0.75,
                "ccn_score": 0.9,
                "coupling_score": 0.6,
                "ownership_score": 0.5,
                "coverage_score": 0.8,
                "quality_score": 0.3,
                "total_coupling": 12,
                "unique_authors": 2,
                "top_author_pct": 85.0,
                "churn_30d": 3,
                "loc_total": 500,
                "complexity_max": 25,
                "coverage_line_pct": 20.0,
            },
        ]
        mock_summary = [
            {"total_files": 200, "total_loc": 50000, "eligible_files": 150, "eligible_loc": 45000},
        ]

        def fetch_side_effect(query_name: str, run_pk: int, **kwargs):
            if query_name == "sampling_targets":
                return mock_targets
            if query_name == "sampling_summary":
                return mock_summary
            return []

        mock_fetcher.fetch.side_effect = fetch_side_effect

        data = section.fetch_data(mock_fetcher, run_pk=1)

        assert data["has_data"] is True
        assert data["target_count"] == 1
        assert data["targets"][0]["file_path"] == "src/engine.py"
        assert data["targets"][0]["total_coupling"] == 12
        assert data["targets"][0]["unique_authors"] == 2
        assert "rationale" in data["targets"][0]

        # Sampling coverage
        assert data["sampling_coverage"]["sampled_files"] == 1
        assert data["sampling_coverage"]["total_files"] == 200
        assert data["sampling_coverage"]["sampled_pct"] == 1.0

        # Risk drivers
        assert isinstance(data["risk_drivers"], dict)
        assert sum(data["risk_drivers"].values()) == 1

    def test_fetch_data_empty(self, mock_fetcher: MagicMock):
        """Verify graceful degradation with no targets."""
        section = SamplingRationaleSection()

        def fetch_side_effect(query_name: str, run_pk: int, **kwargs):
            if query_name == "sampling_summary":
                return [{"total_files": 10, "total_loc": 500, "eligible_files": 3, "eligible_loc": 300}]
            return []

        mock_fetcher.fetch.side_effect = fetch_side_effect

        data = section.fetch_data(mock_fetcher, run_pk=1)

        assert data["has_data"] is False
        assert data["target_count"] == 0
        assert data["sampling_coverage"]["sampled_files"] == 0
        assert data["sampling_coverage"]["sampled_pct"] == 0

    def test_fallback_data(self):
        """Verify fallback data structure."""
        section = SamplingRationaleSection()
        fallback = section.get_fallback_data()

        assert fallback["has_data"] is False
        assert fallback["targets"] == []
        assert fallback["risk_drivers"] == {}
        assert fallback["sampling_coverage"] == {}

    def test_config(self):
        section = SamplingRationaleSection()
        assert section.config.name == "sampling_rationale"
        assert section.config.priority == 97
