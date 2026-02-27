"""Tests for cloud commands — verify delegation args."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

from caldera_cli.app import app

runner = CliRunner()


class TestCloudCleanupCommand:
    @patch("caldera_cli.commands.cloud.run_script")
    def test_cleanup_default(self, mock_script: object) -> None:
        mock_script.return_value = 0
        result = runner.invoke(app, ["cloud", "cleanup"])
        assert result.exit_code == 0
        mock_script.assert_called_once_with("cloud_cleanup.py", [])

    @patch("caldera_cli.commands.cloud.run_script")
    def test_cleanup_ttl_hours(self, mock_script: object) -> None:
        mock_script.return_value = 0
        result = runner.invoke(app, ["cloud", "cleanup", "--ttl-hours", "2"])
        assert result.exit_code == 0
        mock_script.assert_called_once_with("cloud_cleanup.py", ["--ttl-hours", "2.0"])

    @patch("caldera_cli.commands.cloud.run_script")
    def test_cleanup_dry_run(self, mock_script: object) -> None:
        mock_script.return_value = 0
        result = runner.invoke(app, ["cloud", "cleanup", "--dry-run"])
        assert result.exit_code == 0
        mock_script.assert_called_once_with("cloud_cleanup.py", ["--dry-run"])

    @patch("caldera_cli.commands.cloud.run_script")
    def test_cleanup_all_flags(self, mock_script: object) -> None:
        mock_script.return_value = 0
        result = runner.invoke(app, ["cloud", "cleanup", "--ttl-hours", "1", "--dry-run"])
        assert result.exit_code == 0
        mock_script.assert_called_once_with("cloud_cleanup.py", ["--ttl-hours", "1.0", "--dry-run"])


class TestCloudRunCommand:
    @patch("caldera_cli.commands.cloud.run_make")
    def test_run_basic(self, mock_make: object) -> None:
        mock_make.return_value = 0
        result = runner.invoke(app, ["cloud", "run", "https://github.com/org/repo"])
        assert result.exit_code == 0
        mock_make.assert_called_once_with("cloud-run", {"REPO": "https://github.com/org/repo"})

    @patch("caldera_cli.commands.cloud.run_make")
    def test_run_with_server_preset(self, mock_make: object) -> None:
        mock_make.return_value = 0
        result = runner.invoke(app, ["cloud", "run", "https://github.com/org/repo", "--server", "large"])
        assert result.exit_code == 0
        call_vars = mock_make.call_args[0][1]
        assert call_vars["CLOUD_SERVER"] == "large"

    @patch("caldera_cli.commands.cloud.run_make")
    def test_run_with_keep(self, mock_make: object) -> None:
        mock_make.return_value = 0
        result = runner.invoke(app, ["cloud", "run", "https://github.com/org/repo", "--keep"])
        assert result.exit_code == 0
        call_vars = mock_make.call_args[0][1]
        assert call_vars["KEEP_SERVER"] == "1"
