"""Tests for rewrite risk section."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from insights.sections.rewrite_risk import (
    RewriteRiskSection,
    _classify_constraint,
    _generate_assumption,
    _generate_explanation,
    _generate_trigger,
)


# ---------------------------------------------------------------------------
# _classify_constraint tests
# ---------------------------------------------------------------------------


class TestClassifyConstraint:
    """Tests for _classify_constraint helper."""

    def test_monolith_plus_coupling_plus_silo_is_structural_high(self):
        ct, rl = _classify_constraint(
            ["monolith", "bidirectional_coupling", "knowledge_silo"], loc_total=5000
        )
        assert ct == "structural"
        assert rl == "high"

    def test_monolith_plus_coupling_is_structural_high(self):
        ct, rl = _classify_constraint(["monolith", "unidirectional_coupling"], loc_total=2000)
        assert ct == "structural"
        assert rl == "high"

    def test_monolith_alone_is_structural_medium(self):
        ct, rl = _classify_constraint(["monolith"], loc_total=1500)
        assert ct == "structural"
        assert rl == "medium"

    def test_bidirectional_coupling_alone_is_structural_medium(self):
        ct, rl = _classify_constraint(["bidirectional_coupling"], loc_total=1000)
        assert ct == "structural"
        assert rl == "medium"

    def test_unidirectional_coupling_alone_is_addressable_medium(self):
        ct, rl = _classify_constraint(["unidirectional_coupling"], loc_total=1000)
        assert ct == "addressable"
        assert rl == "medium"

    def test_untested_core_large_is_addressable_high(self):
        ct, rl = _classify_constraint(["untested_core"], loc_total=4000)
        assert ct == "addressable"
        assert rl == "high"

    def test_untested_core_small_is_addressable_medium(self):
        ct, rl = _classify_constraint(["untested_core"], loc_total=1000)
        assert ct == "addressable"
        assert rl == "medium"

    def test_knowledge_silo_alone_is_addressable_low(self):
        ct, rl = _classify_constraint(["knowledge_silo"], loc_total=500)
        assert ct == "addressable"
        assert rl == "low"

    def test_empty_signals_fallback(self):
        ct, rl = _classify_constraint([], loc_total=100)
        assert ct == "addressable"
        assert rl == "low"

    def test_monolith_beats_silo_priority(self):
        """Monolith + silo without coupling: monolith dominates → structural/medium."""
        ct, rl = _classify_constraint(["monolith", "knowledge_silo"], loc_total=2000)
        assert ct == "structural"
        assert rl == "medium"


# ---------------------------------------------------------------------------
# _generate_assumption tests
# ---------------------------------------------------------------------------


class TestGenerateAssumption:
    """Tests for _generate_assumption helper."""

    def test_monolith_assumption(self):
        assert "extract services" in _generate_assumption("monolith")

    def test_coupling_assumption(self):
        assert "data model" in _generate_assumption("bidirectional_coupling")

    def test_silo_assumption(self):
        assert "key contributor" in _generate_assumption("knowledge_silo")

    def test_untested_assumption(self):
        assert "regressions" in _generate_assumption("untested_core")

    def test_unknown_signal_fallback(self):
        result = _generate_assumption("unknown_signal")
        assert "feasible" in result.lower()


# ---------------------------------------------------------------------------
# _generate_explanation / _generate_trigger tests
# ---------------------------------------------------------------------------


class TestGenerateExplanation:
    """Tests for _generate_explanation helper."""

    def test_monolith_explanation_mentions_gini(self):
        assert "Gini" in _generate_explanation("monolith")

    def test_unknown_signal_has_fallback(self):
        result = _generate_explanation("nonexistent")
        assert len(result) > 0


class TestGenerateTrigger:
    """Tests for _generate_trigger helper."""

    def test_monolith_trigger_mentions_split(self):
        assert "split" in _generate_trigger("monolith").lower()

    def test_silo_trigger_mentions_contributor(self):
        assert "contributor" in _generate_trigger("knowledge_silo").lower()

    def test_unknown_trigger_has_fallback(self):
        result = _generate_trigger("nonexistent")
        assert "module" in result.lower()


# ---------------------------------------------------------------------------
# RewriteRiskSection tests
# ---------------------------------------------------------------------------


class TestRewriteRiskSection:
    """Tests for RewriteRiskSection.fetch_data."""

    def test_config(self):
        section = RewriteRiskSection()
        assert section.config.name == "rewrite_risk"
        assert section.config.priority == 3

    def test_fetch_data_with_constraints(self, mock_fetcher: MagicMock):
        section = RewriteRiskSection()

        mock_constraints = [
            {
                "directory_path": "src/core",
                "loc_total": 5000,
                "file_count": 20,
                "signal": "monolith",
                "constraint_type": "structural",
                "risk_level": "high",
                "loc_gini": 0.85,
                "loc_top_10_pct": 72.0,
                "avg_ccn": 12.5,
                "ccn_p90": 25.0,
                "coupling_fan_out": 15,
                "coupling_fan_in": 10,
                "coverage_line_pct": 30.0,
                "single_author_loc": 2000,
                "blame_total_loc": 5000,
            },
            {
                "directory_path": "src/core",
                "loc_total": 5000,
                "file_count": 20,
                "signal": "bidirectional_coupling",
                "constraint_type": "structural",
                "risk_level": "medium",
                "loc_gini": 0.85,
                "loc_top_10_pct": 72.0,
                "avg_ccn": 12.5,
                "ccn_p90": 25.0,
                "coupling_fan_out": 15,
                "coupling_fan_in": 10,
                "coverage_line_pct": 30.0,
                "single_author_loc": 2000,
                "blame_total_loc": 5000,
            },
            {
                "directory_path": "src/utils",
                "loc_total": 800,
                "file_count": 5,
                "signal": "knowledge_silo",
                "constraint_type": "addressable",
                "risk_level": "low",
                "loc_gini": 0.4,
                "loc_top_10_pct": 40.0,
                "avg_ccn": 3.0,
                "ccn_p90": 8.0,
                "coupling_fan_out": 3,
                "coupling_fan_in": 2,
                "coverage_line_pct": 50.0,
                "single_author_loc": 600,
                "blame_total_loc": 800,
            },
        ]

        mock_fetcher.fetch.return_value = mock_constraints

        data = section.fetch_data(mock_fetcher, run_pk=1)

        assert data["has_data"] is True
        # Two directories → two merged constraints
        assert data["total_constraints"] == 2
        assert data["structural_count"] == 1
        assert data["addressable_count"] == 1
        assert data["assessment"] == "significant rewrite risk"

        # src/core should be merged with two signals
        core = next(c for c in data["constraints"] if c["directory"] == "src/core")
        assert "monolith" in core["signals"]
        assert "bidirectional_coupling" in core["signals"]
        assert core["constraint_type"] == "structural"
        assert core["risk_level"] == "high"
        assert core["loc_total"] == 5000
        assert "assumption_that_fails" in core
        assert "why_it_fails" in core
        assert "trigger_condition" in core

    def test_fetch_data_no_constraints(self, mock_fetcher: MagicMock):
        section = RewriteRiskSection()
        mock_fetcher.fetch.return_value = []

        data = section.fetch_data(mock_fetcher, run_pk=1)

        assert data["has_data"] is False
        assert data["total_constraints"] == 0
        assert data["assessment"] == "incremental evolution viable"
        assert data["structural_count"] == 0
        assert data["addressable_count"] == 0

    def test_fetch_data_only_addressable(self, mock_fetcher: MagicMock):
        """All addressable constraints → incremental evolution viable."""
        section = RewriteRiskSection()
        mock_fetcher.fetch.return_value = [
            {
                "directory_path": "src/lib",
                "loc_total": 1200,
                "file_count": 8,
                "signal": "untested_core",
                "constraint_type": "addressable",
                "risk_level": "medium",
                "loc_gini": 0.3,
                "loc_top_10_pct": 35.0,
                "avg_ccn": 7.0,
                "ccn_p90": 15.0,
                "coupling_fan_out": 4,
                "coupling_fan_in": 2,
                "coverage_line_pct": 5.0,
                "single_author_loc": 0,
                "blame_total_loc": 1200,
            },
        ]

        data = section.fetch_data(mock_fetcher, run_pk=1)

        assert data["has_data"] is True
        assert data["structural_count"] == 0
        assert data["addressable_count"] == 1
        assert data["assessment"] == "incremental evolution viable"

    def test_fetch_data_structural_medium_only(self, mock_fetcher: MagicMock):
        """Structural constraints at medium → viable with constraints."""
        section = RewriteRiskSection()
        mock_fetcher.fetch.return_value = [
            {
                "directory_path": "src/engine",
                "loc_total": 3000,
                "file_count": 12,
                "signal": "monolith",
                "constraint_type": "structural",
                "risk_level": "medium",
                "loc_gini": 0.75,
                "loc_top_10_pct": 65.0,
                "avg_ccn": 8.0,
                "ccn_p90": 20.0,
                "coupling_fan_out": 5,
                "coupling_fan_in": 3,
                "coverage_line_pct": 40.0,
                "single_author_loc": 0,
                "blame_total_loc": 3000,
            },
        ]

        data = section.fetch_data(mock_fetcher, run_pk=1)

        assert data["has_data"] is True
        assert data["structural_count"] == 1
        assert data["high_count"] == 0
        assert data["assessment"] == "viable with constraints"

    def test_fallback_data(self):
        section = RewriteRiskSection()
        fallback = section.get_fallback_data()

        assert fallback["has_data"] is False
        assert fallback["constraints"] == []
        assert fallback["total_constraints"] == 0
        assert fallback["structural_count"] == 0
        assert fallback["addressable_count"] == 0
        assert fallback["assessment"] == "incremental evolution viable"
        assert "structural" in fallback["matrix"]
        assert "addressable" in fallback["matrix"]

    def test_matrix_counts(self, mock_fetcher: MagicMock):
        """Matrix should correctly count constraint_type × risk_level."""
        section = RewriteRiskSection()
        mock_fetcher.fetch.return_value = [
            {
                "directory_path": "src/a",
                "loc_total": 5000,
                "file_count": 20,
                "signal": "monolith",
                "constraint_type": "structural",
                "risk_level": "medium",
                "loc_gini": 0.8,
                "loc_top_10_pct": 70.0,
                "avg_ccn": 10.0,
                "ccn_p90": 20.0,
                "coupling_fan_out": 3,
                "coupling_fan_in": 2,
                "coverage_line_pct": 45.0,
                "single_author_loc": 0,
                "blame_total_loc": 5000,
            },
            {
                "directory_path": "src/b",
                "loc_total": 4000,
                "file_count": 10,
                "signal": "untested_core",
                "constraint_type": "addressable",
                "risk_level": "high",
                "loc_gini": 0.3,
                "loc_top_10_pct": 30.0,
                "avg_ccn": 9.0,
                "ccn_p90": 18.0,
                "coupling_fan_out": 2,
                "coupling_fan_in": 1,
                "coverage_line_pct": 2.0,
                "single_author_loc": 0,
                "blame_total_loc": 4000,
            },
        ]

        data = section.fetch_data(mock_fetcher, run_pk=1)

        assert data["matrix"]["structural"]["medium"] == 1
        assert data["matrix"]["addressable"]["high"] == 1
        assert data["matrix"]["structural"]["high"] == 0

    def test_template_name(self):
        section = RewriteRiskSection()
        assert section.get_template_name() == "rewrite_risk.html.j2"
        assert section.get_markdown_template_name() == "rewrite_risk.md.j2"

    def test_constraints_sorted_by_severity(self, mock_fetcher: MagicMock):
        """Constraints should be sorted: high before medium before low."""
        section = RewriteRiskSection()
        mock_fetcher.fetch.return_value = [
            {
                "directory_path": "src/low",
                "loc_total": 500,
                "file_count": 3,
                "signal": "knowledge_silo",
                "constraint_type": "addressable",
                "risk_level": "low",
                "loc_gini": 0.3,
                "loc_top_10_pct": 30.0,
                "avg_ccn": 2.0,
                "ccn_p90": 5.0,
                "coupling_fan_out": 2,
                "coupling_fan_in": 1,
                "coverage_line_pct": 60.0,
                "single_author_loc": 400,
                "blame_total_loc": 500,
            },
            {
                "directory_path": "src/high",
                "loc_total": 6000,
                "file_count": 25,
                "signal": "monolith",
                "constraint_type": "structural",
                "risk_level": "high",
                "loc_gini": 0.9,
                "loc_top_10_pct": 80.0,
                "avg_ccn": 15.0,
                "ccn_p90": 30.0,
                "coupling_fan_out": 20,
                "coupling_fan_in": 12,
                "coverage_line_pct": 10.0,
                "single_author_loc": 0,
                "blame_total_loc": 6000,
            },
            {
                "directory_path": "src/high",
                "loc_total": 6000,
                "file_count": 25,
                "signal": "bidirectional_coupling",
                "constraint_type": "structural",
                "risk_level": "medium",
                "loc_gini": 0.9,
                "loc_top_10_pct": 80.0,
                "avg_ccn": 15.0,
                "ccn_p90": 30.0,
                "coupling_fan_out": 20,
                "coupling_fan_in": 12,
                "coverage_line_pct": 10.0,
                "single_author_loc": 0,
                "blame_total_loc": 6000,
            },
        ]

        data = section.fetch_data(mock_fetcher, run_pk=1)

        levels = [c["risk_level"] for c in data["constraints"]]
        # High should come before low
        assert levels.index("high") < levels.index("low")
