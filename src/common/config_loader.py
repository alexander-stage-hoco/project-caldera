"""Configuration file loader for Caldera tools.

Loads and validates JSON config files that can be used alongside or instead of
CLI arguments. Config values have lower precedence than explicit CLI args but
higher precedence than environment variables.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema

# Current schema major version — MAJOR mismatch = error
_SUPPORTED_MAJOR = 1

_SCHEMA_PATH = Path(__file__).parent / "schemas" / "config.schema.json"


class ConfigError(Exception):
    """Raised when config loading or validation fails."""


@dataclass(frozen=True)
class ToolConfig:
    """Validated tool configuration loaded from a JSON config file.

    All fields are optional — they serve as defaults that can be overridden
    by CLI arguments.
    """

    schema_version: str
    repo_path: str | None = None
    repo_name: str | None = None
    output_dir: str | None = None
    run_id: str | None = None
    repo_id: str | None = None
    branch: str | None = None
    commit: str | None = None
    tool_specific: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_schema_version(self.schema_version)


def _validate_schema_version(version: str) -> None:
    """Validate schema_version is semver and MAJOR matches."""
    parts = version.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ConfigError(
            f"schema_version must be semver (e.g. '1.0.0'), got '{version}'"
        )
    major = int(parts[0])
    if major != _SUPPORTED_MAJOR:
        raise ConfigError(
            f"Unsupported config schema major version {major} "
            f"(supported: {_SUPPORTED_MAJOR})"
        )


def load_and_validate_config(config_path: Path) -> ToolConfig:
    """Load a JSON config file, validate against schema, and return ToolConfig.

    Args:
        config_path: Path to the JSON config file.

    Returns:
        Validated ToolConfig dataclass.

    Raises:
        ConfigError: On file read, JSON parse, schema validation, or version errors.
        FileNotFoundError: When the config file does not exist.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in config file: {exc}") from exc

    # Validate against JSON Schema
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(raw), key=str)
    if errors:
        messages = []
        for error in errors:
            location = "/".join(str(p) for p in error.path) or "<root>"
            messages.append(f"{location}: {error.message}")
        raise ConfigError(
            f"Config schema validation failed ({len(errors)} error(s)):\n"
            + "\n".join(f"  - {m}" for m in messages)
        )

    return ToolConfig(
        schema_version=raw["schema_version"],
        repo_path=raw.get("repo_path"),
        repo_name=raw.get("repo_name"),
        output_dir=raw.get("output_dir"),
        run_id=raw.get("run_id"),
        repo_id=raw.get("repo_id"),
        branch=raw.get("branch"),
        commit=raw.get("commit"),
        tool_specific=raw.get("tool_specific", {}),
    )
