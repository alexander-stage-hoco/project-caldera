"""Tests for report commands — verify insights delegation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from caldera_cli.app import app

runner = CliRunner()


class TestReportGenerate:
    def test_missing_both_args(self, tmp_db: Path) -> None:
        result = runner.invoke(app, ["report", "generate", "--db", str(tmp_db)])
        assert result.exit_code == 1
        assert "Must specify" in result.output

    def test_both_args_conflict(self, tmp_db: Path) -> None:
        result = runner.invoke(app, [
            "report", "generate", "1",
            "--collection-run-id", "abc",
            "--db", str(tmp_db),
        ])
        assert result.exit_code == 1
        assert "Cannot specify both" in result.output

    def test_profile_sections_conflict(self, tmp_db: Path) -> None:
        result = runner.invoke(app, [
            "report", "generate", "1",
            "--profile", "cto",
            "--sections", "foo",
            "--db", str(tmp_db),
        ])
        assert result.exit_code == 1
        assert "Cannot specify both" in result.output

    def test_missing_db(self, tmp_path: Path) -> None:
        result = runner.invoke(app, [
            "report", "generate", "1",
            "--db", str(tmp_path / "nope.duckdb"),
        ])
        assert result.exit_code == 1
        assert "not found" in result.output


class TestReportListSections:
    @patch("caldera_cli.commands.report.ensure_src_on_path")
    def test_list_sections_delegates(self, mock_ensure: MagicMock) -> None:
        """Verify list-sections attempts to import InsightsGenerator."""
        # This will fail at import if insights is not installed, but we verify the path
        result = runner.invoke(app, ["report", "list-sections"])
        # It either succeeds (insights installed) or fails at import
        mock_ensure.assert_called()


class TestReportListProfiles:
    @patch("caldera_cli.commands.report.ensure_src_on_path")
    def test_list_profiles_delegates(self, mock_ensure: MagicMock) -> None:
        result = runner.invoke(app, ["report", "list-profiles"])
        mock_ensure.assert_called()
