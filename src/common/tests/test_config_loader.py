"""Tests for config_loader module."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from ..config_loader import ConfigError, ToolConfig, load_and_validate_config


class TestToolConfig:
    """Tests for ToolConfig frozen dataclass."""

    def test_valid_config(self):
        """Should create a ToolConfig with valid schema_version."""
        cfg = ToolConfig(schema_version="1.0.0")
        assert cfg.schema_version == "1.0.0"
        assert cfg.repo_path is None
        assert cfg.tool_specific == {}

    def test_all_fields(self):
        """Should accept all optional fields."""
        cfg = ToolConfig(
            schema_version="1.2.3",
            repo_path="/repo",
            repo_name="my-repo",
            output_dir="/out",
            run_id="run-1",
            repo_id="repo-1",
            branch="develop",
            commit="abc123",
            tool_specific={"key": "value"},
        )
        assert cfg.repo_path == "/repo"
        assert cfg.tool_specific == {"key": "value"}

    def test_frozen(self):
        """Should be immutable."""
        cfg = ToolConfig(schema_version="1.0.0")
        with pytest.raises(AttributeError):
            cfg.repo_path = "/new"  # type: ignore[misc]

    def test_rejects_invalid_semver(self):
        """Should reject non-semver schema_version."""
        with pytest.raises(ConfigError, match="semver"):
            ToolConfig(schema_version="1.0")

    def test_rejects_wrong_major_version(self):
        """Should reject unsupported major version."""
        with pytest.raises(ConfigError, match="Unsupported config schema major version 2"):
            ToolConfig(schema_version="2.0.0")

    def test_rejects_major_version_zero(self):
        """Should reject major version 0."""
        with pytest.raises(ConfigError, match="Unsupported config schema major version 0"):
            ToolConfig(schema_version="0.1.0")


class TestLoadAndValidateConfig:
    """Tests for load_and_validate_config function."""

    def test_loads_valid_config(self, tmp_path: Path):
        """Should load and validate a minimal config file."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"schema_version": "1.0.0"}))

        cfg = load_and_validate_config(config_file)

        assert cfg.schema_version == "1.0.0"
        assert cfg.repo_path is None

    def test_loads_full_config(self, tmp_path: Path):
        """Should load all fields from config file."""
        data = {
            "schema_version": "1.0.0",
            "repo_path": "/my/repo",
            "repo_name": "my-repo",
            "output_dir": "/my/output",
            "run_id": "run-123",
            "repo_id": "repo-456",
            "branch": "feature/x",
            "commit": "abc123def",
            "tool_specific": {"threshold": 10},
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(data))

        cfg = load_and_validate_config(config_file)

        assert cfg.repo_path == "/my/repo"
        assert cfg.repo_name == "my-repo"
        assert cfg.run_id == "run-123"
        assert cfg.tool_specific == {"threshold": 10}

    def test_file_not_found(self, tmp_path: Path):
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            load_and_validate_config(tmp_path / "missing.json")

    def test_invalid_json(self, tmp_path: Path):
        """Should raise ConfigError for malformed JSON."""
        config_file = tmp_path / "bad.json"
        config_file.write_text("{bad json")

        with pytest.raises(ConfigError, match="Invalid JSON"):
            load_and_validate_config(config_file)

    def test_schema_validation_missing_version(self, tmp_path: Path):
        """Should reject config missing required schema_version."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"repo_path": "/repo"}))

        with pytest.raises(ConfigError, match="schema_version"):
            load_and_validate_config(config_file)

    def test_schema_validation_bad_version_format(self, tmp_path: Path):
        """Should reject config with non-semver schema_version."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"schema_version": "not-semver"}))

        with pytest.raises(ConfigError):
            load_and_validate_config(config_file)

    def test_schema_validation_extra_property(self, tmp_path: Path):
        """Should reject config with unknown properties."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "schema_version": "1.0.0",
            "unknown_field": "bad",
        }))

        with pytest.raises(ConfigError, match="schema validation failed"):
            load_and_validate_config(config_file)

    def test_major_version_mismatch(self, tmp_path: Path):
        """Should reject config with wrong major version."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"schema_version": "2.0.0"}))

        with pytest.raises(ConfigError):
            load_and_validate_config(config_file)

    def test_minor_version_difference_ok(self, tmp_path: Path):
        """Should accept config with different minor/patch version."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"schema_version": "1.99.99"}))

        cfg = load_and_validate_config(config_file)
        assert cfg.schema_version == "1.99.99"
