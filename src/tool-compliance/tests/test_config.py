"""Tests for tool-compliance config loader."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure the tool-compliance package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import HAS_YAML, load_yaml_file, RULES_DIR


def test_load_yaml_file_uses_pyyaml() -> None:
    """Verify common.yaml loads correctly with PyYAML present."""
    common_path = RULES_DIR / "common.yaml"
    result = load_yaml_file(common_path)
    assert isinstance(result, dict)
    assert "required_paths" in result


def test_load_yaml_file_raises_without_pyyaml(monkeypatch: pytest.MonkeyPatch) -> None:
    """When HAS_YAML is False, load_yaml_file raises ImportError."""
    import config as config_mod

    monkeypatch.setattr(config_mod, "HAS_YAML", False)
    common_path = RULES_DIR / "common.yaml"
    with pytest.raises(ImportError, match="PyYAML is required"):
        load_yaml_file(common_path)


def test_count_list_pairs_parsed_correctly() -> None:
    """Verify count_list_pairs is a list of dicts with expected keys."""
    common_path = RULES_DIR / "common.yaml"
    config = load_yaml_file(common_path)
    pairs = config.get("data_completeness_rules", {}).get("count_list_pairs", [])
    assert isinstance(pairs, list)
    assert len(pairs) > 0
    for pair in pairs:
        assert isinstance(pair, dict), f"Expected dict, got {type(pair)}: {pair}"
        assert "count_field" in pair, f"Missing count_field in {pair}"
        assert "list_field" in pair, f"Missing list_field in {pair}"


def test_cross_reference_sections_parsed_correctly() -> None:
    """Verify cross_reference_sections is a list of dicts with source/target keys."""
    common_path = RULES_DIR / "common.yaml"
    config = load_yaml_file(common_path)
    sections = config.get("path_consistency_rules", {}).get("cross_reference_sections", [])
    assert isinstance(sections, list)
    assert len(sections) > 0
    for section in sections:
        assert isinstance(section, dict), f"Expected dict, got {type(section)}: {section}"
        assert "source" in section, f"Missing source in {section}"
        assert "target" in section, f"Missing target in {section}"
