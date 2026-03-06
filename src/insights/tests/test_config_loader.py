"""Tests for ConfigLoader and configuration system."""

from __future__ import annotations

import pytest

from insights.config.loader import ConfigLoader, _deep_merge
from insights.evidence.entities import CategoryDefinition, CategoryRegistry, ParameterSet


class TestDeepMerge:
    def test_flat_override(self):
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        assert _deep_merge(base, override) == {"a": 1, "b": 3, "c": 4}

    def test_nested_override(self):
        base = {"x": {"a": 1, "b": 2}}
        override = {"x": {"b": 3}}
        assert _deep_merge(base, override) == {"x": {"a": 1, "b": 3}}

    def test_does_not_mutate_base(self):
        base = {"x": {"a": 1}}
        override = {"x": {"b": 2}}
        _deep_merge(base, override)
        assert base == {"x": {"a": 1}}


class TestLoadCategories:
    def test_loads_default_categories(self):
        registry = ConfigLoader.load_categories()
        assert isinstance(registry, CategoryRegistry)
        assert len(registry) >= 6  # At least the original 6

    def test_all_original_categories_present(self):
        registry = ConfigLoader.load_categories()
        for cat in ("complexity", "security", "coupling", "coverage", "ownership", "quality"):
            assert registry.is_valid(cat), f"Missing category: {cat}"

    def test_new_categories_present(self):
        registry = ConfigLoader.load_categories()
        for cat in ("maintainability", "architecture", "dependencies", "duplication"):
            assert registry.is_valid(cat), f"Missing new category: {cat}"

    def test_abbreviations_correct(self):
        registry = ConfigLoader.load_categories()
        assert registry.abbreviation("complexity") == "CCN"
        assert registry.abbreviation("security") == "SEC"
        assert registry.abbreviation("coupling") == "COUP"
        assert registry.abbreviation("maintainability") == "MAINT"
        assert registry.abbreviation("duplication") == "DUP"

    def test_optional_query_names(self):
        registry = ConfigLoader.load_categories()
        optional = registry.optional_query_names()
        assert "evidence_coupling" in optional
        assert "evidence_coverage" in optional
        assert "evidence_ownership" in optional
        assert "evidence_complexity" not in optional

    def test_invalid_category_raises(self):
        registry = ConfigLoader.load_categories()
        with pytest.raises(KeyError, match="Unknown evidence category"):
            registry.get("nonexistent")

    def test_category_definition_fields(self):
        registry = ConfigLoader.load_categories()
        ccn = registry.get("complexity")
        assert isinstance(ccn, CategoryDefinition)
        assert ccn.name == "complexity"
        assert ccn.abbreviation == "CCN"
        assert ccn.query_name == "evidence_complexity"
        assert "lizard" in ccn.tools
        assert ccn.optional is False


class TestLoadParameterSet:
    def test_loads_default(self):
        ps = ConfigLoader.load_parameter_set("default")
        assert isinstance(ps, ParameterSet)
        assert ps.name == "default"
        assert ps.query_params["evidence_complexity"]["threshold"] == 15
        assert ps.query_params["evidence_complexity"]["limit"] == 100

    def test_default_claim_params(self):
        ps = ConfigLoader.load_parameter_set("default")
        assert ps.claim_params["HighCouplingRule"]["fan_out_multiplier"] == 3
        assert ps.claim_params["KnowledgeSiloRule"]["max_authors"] == 1
        assert ps.claim_params["CoverageGapRule"]["max_coverage"] == 50

    def test_default_risk_params(self):
        ps = ConfigLoader.load_parameter_set("default")
        assert ps.risk_params["Security exposure"]["min_claims"] == 1
        assert ps.risk_params["Systemic debt"]["min_claims"] == 3

    def test_conservative_inherits_from_default(self):
        ps = ConfigLoader.load_parameter_set("conservative")
        assert ps.name == "conservative"
        # Overridden
        assert ps.query_params["evidence_complexity"]["threshold"] == 25
        # Inherited from default
        assert ps.query_params["evidence_security"]["limit"] == 50

    def test_pe_due_diligence_overrides(self):
        ps = ConfigLoader.load_parameter_set("pe_due_diligence")
        assert ps.query_params["evidence_complexity"]["threshold"] == 10
        assert ps.query_params["evidence_complexity"]["limit"] == 200
        assert ps.risk_params["Security exposure"]["default_severity"] == "critical"

    def test_query_params_for_helper(self):
        ps = ConfigLoader.load_parameter_set("default")
        params = ps.query_params_for("evidence_complexity")
        assert params["threshold"] == 15
        assert params["limit"] == 100

    def test_query_params_for_missing_returns_empty(self):
        ps = ConfigLoader.load_parameter_set("default")
        assert ps.query_params_for("nonexistent") == {}

    def test_claim_params_for_helper(self):
        ps = ConfigLoader.load_parameter_set("default")
        params = ps.claim_params_for("HighCouplingRule")
        assert params["fan_out_multiplier"] == 3

    def test_unknown_set_raises(self):
        with pytest.raises(ValueError, match="Unknown parameter set"):
            ConfigLoader.load_parameter_set("nonexistent")

    def test_list_parameter_sets(self):
        names = ConfigLoader.list_parameter_sets()
        assert "default" in names
        assert "conservative" in names
        assert "pe_due_diligence" in names
