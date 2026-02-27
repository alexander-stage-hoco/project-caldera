"""Tests for infra/cloud_pricing.py — pricing utilities."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add infra/ to import path so cloud_pricing is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "infra"))

from cloud_pricing import estimate_cost_eur, get_preset_info, load_presets, resolve_server_type


class TestLoadPresets:
    def test_returns_dict_with_expected_keys(self) -> None:
        data = load_presets()
        assert "presets" in data
        assert "pricing_eur_per_hour" in data
        assert "billing_increment_seconds" in data
        assert "default_preset" in data


class TestResolveServerType:
    def test_preset_name(self) -> None:
        assert resolve_server_type("small") == "cx23"

    def test_raw_type(self) -> None:
        assert resolve_server_type("cx43") == "cx43"

    def test_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown preset or server type"):
            resolve_server_type("nonexistent")


class TestEstimateCostEur:
    def test_one_hour(self) -> None:
        result = estimate_cost_eur("cx33", 3600)
        assert result["estimated_cost_eur"] == 0.013
        assert result["pricing_eur_per_hour"] == 0.013
        assert result["billable_hours"] == 1

    def test_partial_hour_rounds_up(self) -> None:
        result = estimate_cost_eur("cx33", 1800)
        assert result["billable_hours"] == 1

    def test_zero_duration(self) -> None:
        result = estimate_cost_eur("cx33", 0)
        assert result["estimated_cost_eur"] == 0
        assert result["billable_hours"] == 0

    def test_unknown_type_returns_zero_rate(self) -> None:
        result = estimate_cost_eur("unknown-type", 3600)
        assert result["pricing_eur_per_hour"] == 0.0
        assert result["estimated_cost_eur"] == 0.0


class TestGetPresetInfo:
    def test_exists(self) -> None:
        info = get_preset_info("medium")
        assert info is not None
        assert info["server_type"] == "cx33"
        assert "vcpu" in info
        assert "ram_gb" in info

    def test_missing(self) -> None:
        assert get_preset_info("nonexistent") is None
