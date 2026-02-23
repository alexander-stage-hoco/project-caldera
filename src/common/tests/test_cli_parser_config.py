"""Integration tests for CLI + config file merge precedence."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ..cli_parser import (
    CommonArgs,
    CommitResolutionConfig,
    ValidationError,
    add_common_args,
    validate_common_args_raising,
)
from ..config_loader import ConfigError


def _make_config(tmp_path: Path, data: dict) -> Path:
    """Write a config JSON file and return its path."""
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(data))
    return config_file


class TestConfigPrecedence:
    """Tests for CLI > config > env > default precedence."""

    @patch("subprocess.run")
    def test_config_provides_defaults(self, mock_run: MagicMock, tmp_path: Path):
        """Config values should fill in when CLI args are not provided."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="abc123\n", stderr=""
        )

        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()

        config_file = _make_config(tmp_path, {
            "schema_version": "1.0.0",
            "repo_path": str(repo_dir),
            "run_id": "config-run",
            "repo_id": "config-repo",
            "branch": "config-branch",
        })

        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args(["--config", str(config_file)])

        result = validate_common_args_raising(args)

        assert result.repo_path == repo_dir
        assert result.run_id == "config-run"
        assert result.repo_id == "config-repo"
        assert result.branch == "config-branch"

    @patch("subprocess.run")
    def test_cli_overrides_config(self, mock_run: MagicMock, tmp_path: Path):
        """CLI args should take precedence over config file values."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="abc123\n", stderr=""
        )

        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()

        config_file = _make_config(tmp_path, {
            "schema_version": "1.0.0",
            "repo_path": "/config/repo",
            "run_id": "config-run",
            "repo_id": "config-repo",
            "branch": "config-branch",
        })

        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args([
            "--config", str(config_file),
            "--repo-path", str(repo_dir),
            "--run-id", "cli-run",
            "--repo-id", "cli-repo",
            "--branch", "cli-branch",
        ])

        result = validate_common_args_raising(args)

        assert result.repo_path == repo_dir
        assert result.run_id == "cli-run"
        assert result.repo_id == "cli-repo"
        assert result.branch == "cli-branch"

    @patch("subprocess.run")
    @patch.dict("os.environ", {"BRANCH": "env-branch"})
    def test_config_overrides_env(self, mock_run: MagicMock, tmp_path: Path):
        """Config values should take precedence over environment variables."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="abc123\n", stderr=""
        )

        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()

        config_file = _make_config(tmp_path, {
            "schema_version": "1.0.0",
            "repo_path": str(repo_dir),
            "run_id": "config-run",
            "repo_id": "config-repo",
            "branch": "config-branch",
        })

        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args(["--config", str(config_file)])

        result = validate_common_args_raising(args)

        assert result.branch == "config-branch"

    @patch("subprocess.run")
    @patch.dict("os.environ", {"BRANCH": "env-branch", "RUN_ID": "env-run", "REPO_ID": "env-repo"})
    def test_env_overrides_default(self, mock_run: MagicMock, tmp_path: Path):
        """Env vars should take precedence over built-in defaults (no config)."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="abc123\n", stderr=""
        )

        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()

        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args(["--repo-path", str(repo_dir)])

        result = validate_common_args_raising(args)

        assert result.branch == "env-branch"
        assert result.run_id == "env-run"
        assert result.repo_id == "env-repo"

    @patch("subprocess.run")
    def test_default_repo_path_used_when_no_config(self, mock_run: MagicMock, tmp_path: Path):
        """Built-in default_repo_path should be used when no CLI/config/env."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="abc123\n", stderr=""
        )

        parser = argparse.ArgumentParser()
        add_common_args(parser, default_repo_path=str(tmp_path))

        args = parser.parse_args([
            "--run-id", "test-run",
            "--repo-id", "test-repo",
        ])

        result = validate_common_args_raising(args)
        assert result.repo_path == tmp_path

    def test_invalid_config_raises(self, tmp_path: Path):
        """Should raise ConfigError for invalid config file."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{bad json")

        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args(["--config", str(config_file)])

        with pytest.raises(ConfigError, match="Invalid JSON"):
            validate_common_args_raising(args)

    def test_missing_config_file_raises(self, tmp_path: Path):
        """Should raise FileNotFoundError for missing config file."""
        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args(["--config", str(tmp_path / "missing.json")])

        with pytest.raises(FileNotFoundError, match="Config file not found"):
            validate_common_args_raising(args)

    @patch("subprocess.run")
    def test_no_config_backward_compatible(self, mock_run: MagicMock, tmp_path: Path):
        """Existing CLI-only usage should still work without --config."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="abc123\n", stderr=""
        )

        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()

        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args([
            "--repo-path", str(repo_dir),
            "--run-id", "test-run",
            "--repo-id", "test-repo",
        ])

        result = validate_common_args_raising(args)

        assert isinstance(result, CommonArgs)
        assert result.run_id == "test-run"
        assert result.branch == "main"  # built-in default
