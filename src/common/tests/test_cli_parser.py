"""Tests for cli_parser module."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ..cli_parser import (
    CommonArgs,
    CommitResolutionConfig,
    ValidationError,
    add_common_args,
    validate_common_args,
    validate_common_args_raising,
)


class TestCommitResolutionConfig:
    """Tests for CommitResolutionConfig dataclass."""

    def test_strict_with_fallback(self):
        """Should create config with strict=True and fallback_repo set."""
        config = CommitResolutionConfig.strict_with_fallback(Path("/tool"))

        assert config.strict is True
        assert config.fallback_repo == Path("/tool")

    def test_lenient(self):
        """Should create config with strict=False and no fallback."""
        config = CommitResolutionConfig.lenient()

        assert config.strict is False
        assert config.fallback_repo is None

    def test_strict_no_fallback(self):
        """Should create config with strict=True and no fallback."""
        config = CommitResolutionConfig.strict_no_fallback()

        assert config.strict is True
        assert config.fallback_repo is None


class TestAddCommonArgs:
    """Tests for add_common_args function."""

    def test_adds_all_seven_arguments(self):
        """Should add all 7 standard arguments to parser."""
        parser = argparse.ArgumentParser()
        add_common_args(parser)

        # Parse with all defaults
        args = parser.parse_args([])

        assert hasattr(args, "repo_path")
        assert hasattr(args, "repo_name")
        assert hasattr(args, "output_dir")
        assert hasattr(args, "run_id")
        assert hasattr(args, "repo_id")
        assert hasattr(args, "branch")
        assert hasattr(args, "commit")

    def test_default_repo_path(self):
        """Should use default repo_path value."""
        parser = argparse.ArgumentParser()
        add_common_args(parser)

        args = parser.parse_args([])

        assert args.repo_path == "eval-repos/synthetic"

    def test_custom_default_repo_path(self):
        """Should use custom default_repo_path when provided."""
        parser = argparse.ArgumentParser()
        add_common_args(parser, default_repo_path="/custom/path")

        args = parser.parse_args([])

        assert args.repo_path == "/custom/path"

    def test_no_default_repo_path(self):
        """Should allow None default_repo_path for required repo-path."""
        parser = argparse.ArgumentParser()
        add_common_args(parser, default_repo_path=None)

        args = parser.parse_args([])

        assert args.repo_path is None

    def test_default_branch(self):
        """Should default branch to 'main'."""
        parser = argparse.ArgumentParser()
        add_common_args(parser)

        args = parser.parse_args([])

        assert args.branch == "main"

    def test_cli_overrides_defaults(self):
        """Should allow CLI arguments to override defaults."""
        parser = argparse.ArgumentParser()
        add_common_args(parser)

        args = parser.parse_args([
            "--repo-path", "/my/repo",
            "--repo-name", "my-repo",
            "--output-dir", "/my/output",
            "--run-id", "test-run",
            "--repo-id", "test-repo-id",
            "--branch", "develop",
            "--commit", "abc123",
        ])

        assert args.repo_path == "/my/repo"
        assert args.repo_name == "my-repo"
        assert args.output_dir == "/my/output"
        assert args.run_id == "test-run"
        assert args.repo_id == "test-repo-id"
        assert args.branch == "develop"
        assert args.commit == "abc123"

    @patch.dict("os.environ", {"REPO_PATH": "/env/repo", "BRANCH": "feature"})
    def test_env_vars_override_defaults(self):
        """Should use environment variables over defaults."""
        parser = argparse.ArgumentParser()
        add_common_args(parser)

        args = parser.parse_args([])

        assert args.repo_path == "/env/repo"
        assert args.branch == "feature"

    @patch.dict("os.environ", {"REPO_PATH": "/env/repo"})
    def test_cli_overrides_env_vars(self):
        """Should allow CLI arguments to override env vars."""
        parser = argparse.ArgumentParser()
        add_common_args(parser)

        args = parser.parse_args(["--repo-path", "/cli/repo"])

        assert args.repo_path == "/cli/repo"

    def test_tool_specific_args_can_be_added(self):
        """Should allow adding tool-specific arguments after common args."""
        parser = argparse.ArgumentParser()
        add_common_args(parser)
        parser.add_argument("--my-tool-option", help="Tool-specific option")

        args = parser.parse_args(["--my-tool-option", "value"])

        assert args.my_tool_option == "value"
        assert args.repo_path == "eval-repos/synthetic"


class TestValidateCommonArgsRaising:
    """Tests for validate_common_args_raising function."""

    @patch("subprocess.run")
    def test_returns_common_args_dataclass(self, mock_run: MagicMock, tmp_path: Path):
        """Should return a CommonArgs dataclass on success."""
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
            "--repo-id", "test-repo-id",
        ])

        result = validate_common_args_raising(args)

        assert isinstance(result, CommonArgs)
        assert result.repo_path == repo_dir
        assert result.run_id == "test-run"
        assert result.repo_id == "test-repo-id"

    def test_raises_validation_error_on_missing_repo_path(self):
        """Should raise ValidationError when repo_path is missing."""
        parser = argparse.ArgumentParser()
        add_common_args(parser, default_repo_path=None)
        args = parser.parse_args([
            "--run-id", "test-run",
            "--repo-id", "test-repo-id",
        ])

        with pytest.raises(ValidationError, match="--repo-path is required"):
            validate_common_args_raising(args)

    def test_raises_file_not_found_on_missing_repo(self):
        """Should raise FileNotFoundError when repo_path doesn't exist."""
        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args([
            "--repo-path", "/nonexistent/path",
            "--run-id", "test-run",
            "--repo-id", "test-repo-id",
        ])

        with pytest.raises(FileNotFoundError, match="Repository not found"):
            validate_common_args_raising(args)

    def test_raises_validation_error_on_missing_run_id(self, tmp_path: Path):
        """Should raise ValidationError when run_id is missing."""
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()

        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args([
            "--repo-path", str(repo_dir),
            "--repo-id", "test-repo-id",
        ])

        with pytest.raises(ValidationError, match="--run-id is required"):
            validate_common_args_raising(args)

    def test_raises_validation_error_on_missing_repo_id(self, tmp_path: Path):
        """Should raise ValidationError when repo_id is missing."""
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()

        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args([
            "--repo-path", str(repo_dir),
            "--run-id", "test-run",
        ])

        with pytest.raises(ValidationError, match="--repo-id is required"):
            validate_common_args_raising(args)

    @patch("subprocess.run")
    def test_derives_repo_name_from_path(self, mock_run: MagicMock, tmp_path: Path):
        """Should derive repo_name from repo_path when not provided."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="abc123\n", stderr=""
        )

        repo_dir = tmp_path / "my-repo"
        repo_dir.mkdir()

        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args([
            "--repo-path", str(repo_dir),
            "--run-id", "test-run",
            "--repo-id", "test-repo-id",
        ])

        result = validate_common_args_raising(args)

        assert result.repo_name == "my-repo"

    @patch("subprocess.run")
    def test_uses_provided_repo_name(self, mock_run: MagicMock, tmp_path: Path):
        """Should use provided repo_name when available."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="abc123\n", stderr=""
        )

        repo_dir = tmp_path / "some-dir"
        repo_dir.mkdir()

        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args([
            "--repo-path", str(repo_dir),
            "--repo-name", "custom-name",
            "--run-id", "test-run",
            "--repo-id", "test-repo-id",
        ])

        result = validate_common_args_raising(args)

        assert result.repo_name == "custom-name"

    @patch("subprocess.run")
    def test_creates_output_directory(self, mock_run: MagicMock, tmp_path: Path):
        """Should create output directory when create_output_dir=True."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="abc123\n", stderr=""
        )

        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        output_dir = tmp_path / "outputs" / "test-run"

        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args([
            "--repo-path", str(repo_dir),
            "--output-dir", str(output_dir),
            "--run-id", "test-run",
            "--repo-id", "test-repo-id",
        ])

        result = validate_common_args_raising(args, create_output_dir=True)

        assert output_dir.exists()
        assert result.output_dir == output_dir
        assert result.output_path == output_dir / "output.json"

    @patch("subprocess.run")
    def test_skips_output_dir_creation(self, mock_run: MagicMock, tmp_path: Path):
        """Should not create output directory when create_output_dir=False."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="abc123\n", stderr=""
        )

        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        output_dir = tmp_path / "outputs" / "test-run"

        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args([
            "--repo-path", str(repo_dir),
            "--output-dir", str(output_dir),
            "--run-id", "test-run",
            "--repo-id", "test-repo-id",
        ])

        result = validate_common_args_raising(args, create_output_dir=False)

        assert not output_dir.exists()
        assert result.output_dir == output_dir

    @patch("subprocess.run")
    def test_uses_default_output_dir(self, mock_run: MagicMock, tmp_path: Path):
        """Should use outputs/<run-id> as default output directory."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="abc123\n", stderr=""
        )

        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()

        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args([
            "--repo-path", str(repo_dir),
            "--run-id", "test-run-123",
            "--repo-id", "test-repo-id",
        ])

        result = validate_common_args_raising(args, create_output_dir=False)

        assert result.output_dir == Path("outputs") / "test-run-123"
        assert result.output_path == Path("outputs") / "test-run-123" / "output.json"

    @patch("subprocess.run")
    def test_raises_value_error_in_strict_mode(self, mock_run: MagicMock, tmp_path: Path):
        """Should raise ValueError when commit not found in strict mode."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=128, stdout="", stderr="not found"
        )

        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()

        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args([
            "--repo-path", str(repo_dir),
            "--run-id", "test-run",
            "--repo-id", "test-repo-id",
            "--commit", "nonexistent",
        ])

        config = CommitResolutionConfig.strict_no_fallback()

        with pytest.raises(ValueError, match="Commit not found"):
            validate_common_args_raising(args, commit_config=config)

    @patch("subprocess.run")
    def test_lenient_mode_trusts_commit(self, mock_run: MagicMock, tmp_path: Path):
        """Should accept commit as-is in lenient mode."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=128, stdout="", stderr="not found"
        )

        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()

        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args([
            "--repo-path", str(repo_dir),
            "--run-id", "test-run",
            "--repo-id", "test-repo-id",
            "--commit", "trusted-commit",
        ])

        config = CommitResolutionConfig.lenient()

        result = validate_common_args_raising(args, commit_config=config)

        assert result.commit == "trusted-commit"


class TestValidateCommonArgs:
    """Tests for validate_common_args function (exits on error)."""

    @patch("subprocess.run")
    def test_returns_common_args_on_success(self, mock_run: MagicMock, tmp_path: Path):
        """Should return CommonArgs on successful validation."""
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
            "--repo-id", "test-repo-id",
        ])

        result = validate_common_args(args)

        assert isinstance(result, CommonArgs)

    def test_exits_on_missing_run_id(self, tmp_path: Path):
        """Should exit with code 1 on missing run_id."""
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()

        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args([
            "--repo-path", str(repo_dir),
            "--repo-id", "test-repo-id",
        ])

        with pytest.raises(SystemExit) as exc_info:
            validate_common_args(args)

        assert exc_info.value.code == 1

    def test_exits_on_missing_repo_path(self):
        """Should exit with code 1 when repo_path doesn't exist."""
        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args([
            "--repo-path", "/nonexistent/path",
            "--run-id", "test-run",
            "--repo-id", "test-repo-id",
        ])

        with pytest.raises(SystemExit) as exc_info:
            validate_common_args(args)

        assert exc_info.value.code == 1

    @patch("subprocess.run")
    def test_exits_on_strict_commit_failure(self, mock_run: MagicMock, tmp_path: Path):
        """Should exit with code 1 when strict commit validation fails."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=128, stdout="", stderr="not found"
        )

        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()

        parser = argparse.ArgumentParser()
        add_common_args(parser)
        args = parser.parse_args([
            "--repo-path", str(repo_dir),
            "--run-id", "test-run",
            "--repo-id", "test-repo-id",
            "--commit", "nonexistent",
        ])

        config = CommitResolutionConfig.strict_no_fallback()

        with pytest.raises(SystemExit) as exc_info:
            validate_common_args(args, commit_config=config)

        assert exc_info.value.code == 1


class TestCommonArgsDataclass:
    """Tests for CommonArgs dataclass."""

    def test_is_frozen(self):
        """CommonArgs should be immutable (frozen)."""
        common = CommonArgs(
            repo_path=Path("/repo"),
            repo_name="test",
            output_dir=Path("/output"),
            output_path=Path("/output/output.json"),
            run_id="run-1",
            repo_id="repo-1",
            branch="main",
            commit="abc123",
        )

        with pytest.raises(AttributeError):
            common.repo_name = "modified"

    def test_all_fields_accessible(self):
        """All fields should be accessible."""
        common = CommonArgs(
            repo_path=Path("/repo"),
            repo_name="test",
            output_dir=Path("/output"),
            output_path=Path("/output/output.json"),
            run_id="run-1",
            repo_id="repo-1",
            branch="main",
            commit="abc123",
        )

        assert common.repo_path == Path("/repo")
        assert common.repo_name == "test"
        assert common.output_dir == Path("/output")
        assert common.output_path == Path("/output/output.json")
        assert common.run_id == "run-1"
        assert common.repo_id == "repo-1"
        assert common.branch == "main"
        assert common.commit == "abc123"
