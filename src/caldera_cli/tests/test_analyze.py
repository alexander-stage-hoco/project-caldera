"""Tests for analyze command — verify Make delegation args."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from caldera_cli.app import app

runner = CliRunner()


class TestAnalyzeRunCommand:
    @patch("caldera_cli.commands.analyze.run_make")
    def test_basic_analyze(self, mock_make: object) -> None:
        mock_make.return_value = 0
        result = runner.invoke(app, ["analyze", "run", "/path/to/repo"])
        assert result.exit_code == 0
        mock_make.assert_called_once_with("analyze", {"REPO": "/path/to/repo"})

    @patch("caldera_cli.commands.analyze.run_make")
    def test_analyze_with_replace(self, mock_make: object) -> None:
        mock_make.return_value = 0
        result = runner.invoke(app, ["analyze", "run", "/path/to/repo", "--replace"])
        assert result.exit_code == 0
        call_vars = mock_make.call_args[0][1]
        assert call_vars["REPLACE"] == "1"
        assert call_vars["REPO"] == "/path/to/repo"

    @patch("caldera_cli.commands.analyze.run_make")
    def test_analyze_skip_tools(self, mock_make: object) -> None:
        mock_make.return_value = 0
        result = runner.invoke(app, ["analyze", "run", "/path/to/repo", "--skip-tools", "trivy,gitleaks"])
        assert result.exit_code == 0
        call_vars = mock_make.call_args[0][1]
        assert call_vars["SKIP_TOOLS"] == "trivy,gitleaks"

    @patch("caldera_cli.commands.analyze.run_make")
    def test_analyze_no_llm(self, mock_make: object) -> None:
        mock_make.return_value = 0
        result = runner.invoke(app, ["analyze", "run", "/path/to/repo", "--no-llm"])
        assert result.exit_code == 0
        call_vars = mock_make.call_args[0][1]
        assert call_vars["PIPELINE_LLM"] == "0"

    @patch("caldera_cli.commands.analyze.run_make")
    def test_analyze_propagates_exit_code(self, mock_make: object) -> None:
        mock_make.return_value = 2
        result = runner.invoke(app, ["analyze", "run", "/path/to/repo"])
        assert result.exit_code == 2


class TestBundleCommand:
    @patch("caldera_cli.commands.analyze.run_make")
    def test_bundle(self, mock_make: object) -> None:
        mock_make.return_value = 0
        result = runner.invoke(app, ["analyze", "bundle", "/path/to/repo", "--bundle", "/tmp/bundle"])
        assert result.exit_code == 0
        mock_make.assert_called_once_with("analyze-bundle", {"REPO": "/path/to/repo", "BUNDLE": "/tmp/bundle"})


class TestCollectCommand:
    @patch("caldera_cli.commands.analyze.run_make")
    def test_collect(self, mock_make: object) -> None:
        mock_make.return_value = 0
        result = runner.invoke(app, ["analyze", "collect", "/path/to/repo"])
        assert result.exit_code == 0
        mock_make.assert_called_once_with("collect", {"REPO": "/path/to/repo"})

    @patch("caldera_cli.commands.analyze.run_make")
    def test_collect_no_tar(self, mock_make: object) -> None:
        mock_make.return_value = 0
        result = runner.invoke(app, ["analyze", "collect", "/path/to/repo", "--no-tar"])
        assert result.exit_code == 0
        call_vars = mock_make.call_args[0][1]
        assert call_vars["BUNDLE_TAR"] == "0"
