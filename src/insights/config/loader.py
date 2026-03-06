"""Configuration loader for evidence categories and parameter sets.

Loads YAML configuration and provides typed access to category definitions
and parameter sets with inheritance (named sets inherit from ``default``).
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

from ..evidence.entities import CategoryDefinition, CategoryRegistry, ParameterSet

_CONFIG_DIR = Path(__file__).resolve().parent


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* onto a deep copy of *base*."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


class ConfigLoader:
    """Loads and validates evidence configuration from YAML files."""

    @staticmethod
    def load_categories(path: Path | None = None) -> CategoryRegistry:
        """Load category definitions from YAML and return a ``CategoryRegistry``."""
        config_path = path or (_CONFIG_DIR / "categories.yml")
        with config_path.open() as f:
            data = yaml.safe_load(f)

        categories: dict[str, CategoryDefinition] = {}
        for name, cfg in data.get("categories", {}).items():
            categories[name] = CategoryDefinition(
                name=name,
                abbreviation=cfg["abbreviation"],
                description=cfg.get("description", ""),
                tools=tuple(cfg.get("tools", [])),
                query_name=cfg["query_name"],
                optional=cfg.get("optional", False),
            )
        return CategoryRegistry(categories)

    @staticmethod
    def load_parameter_set(
        name: str,
        path: Path | None = None,
    ) -> ParameterSet:
        """Load a named parameter set, inheriting from ``default``.

        Non-default sets are deep-merged onto ``default`` so they only
        need to specify overrides.
        """
        config_path = path or (_CONFIG_DIR / "parameter_sets.yml")
        with config_path.open() as f:
            data = yaml.safe_load(f)

        sets = data.get("parameter_sets", {})
        if name not in sets:
            available = list(sets.keys())
            raise ValueError(
                f"Unknown parameter set: {name!r}. Available: {available}"
            )

        default_raw = sets.get("default", {})
        if name == "default":
            merged = default_raw
        else:
            merged = _deep_merge(default_raw, sets[name])

        return ParameterSet(
            name=name,
            description=merged.get("description", ""),
            query_params=merged.get("query_params", {}),
            claim_params=merged.get("claim_params", {}),
            risk_params=merged.get("risk_params", {}),
            action_params=merged.get("action_params", {}),
        )

    @staticmethod
    def list_parameter_sets(path: Path | None = None) -> list[str]:
        """Return the names of all available parameter sets."""
        config_path = path or (_CONFIG_DIR / "parameter_sets.yml")
        with config_path.open() as f:
            data = yaml.safe_load(f)
        return list(data.get("parameter_sets", {}).keys())
