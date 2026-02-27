"""Verify all --help commands render without error."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from caldera_cli.app import app

runner = CliRunner()


@pytest.mark.parametrize(
    "args",
    [
        ["--help"],
        ["analyze", "--help"],
        ["analyze", "run", "--help"],
        ["analyze", "bundle", "--help"],
        ["analyze", "collect", "--help"],
        ["report", "--help"],
        ["report", "generate", "--help"],
        ["report", "list-sections", "--help"],
        ["report", "list-profiles", "--help"],
        ["report", "tool-readiness", "--help"],
        ["db", "--help"],
        ["db", "runs", "--help"],
        ["db", "collections", "--help"],
        ["db", "status", "--help"],
        ["compliance", "--help"],
        ["compliance", "check", "--help"],
        ["compliance", "observability", "--help"],
        ["tools", "--help"],
        ["tools", "setup", "--help"],
        ["tools", "analyze", "--help"],
        ["tools", "test", "--help"],
        ["tools", "create", "--help"],
        ["dbt", "--help"],
        ["dbt", "run", "--help"],
        ["dbt", "test", "--help"],
        ["export", "--help"],
        ["cloud", "--help"],
        ["cloud", "setup", "--help"],
        ["cloud", "run", "--help"],
        ["cloud", "status", "--help"],
        ["cloud", "destroy", "--help"],
        ["docker", "--help"],
        ["docker", "build", "--help"],
        ["docker", "pull", "--help"],
        ["docker", "test", "--help"],
        ["status", "--help"],
    ],
)
def test_help_renders(args: list[str]) -> None:
    result = runner.invoke(app, args)
    assert result.exit_code == 0, f"Failed for {args}: {result.output}"
    assert "Usage" in result.output or "help" in result.output.lower() or "--help" in result.output
