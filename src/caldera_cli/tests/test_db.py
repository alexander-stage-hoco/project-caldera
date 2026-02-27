"""Tests for db commands — direct DuckDB queries."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from caldera_cli.app import app

runner = CliRunner()


class TestDbRuns:
    def test_list_runs(self, tmp_db: Path) -> None:
        result = runner.invoke(app, ["db", "runs", "--db", str(tmp_db)])
        assert result.exit_code == 0
        assert "scc" in result.output
        assert "lizard" in result.output

    def test_list_runs_limit(self, tmp_db: Path) -> None:
        result = runner.invoke(app, ["db", "runs", "--db", str(tmp_db), "--limit", "1"])
        assert result.exit_code == 0
        # Should have at most 1 data row (plus table chrome)
        assert "lizard" in result.output  # run_pk=2 is most recent

    def test_missing_db(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["db", "runs", "--db", str(tmp_path / "nope.duckdb")])
        assert result.exit_code == 1
        assert "not found" in result.output


class TestDbCollections:
    def test_list_collections(self, tmp_db: Path) -> None:
        result = runner.invoke(app, ["db", "collections", "--db", str(tmp_db)])
        assert result.exit_code == 0
        assert "my-repo" in result.output
        assert "completed" in result.output

    def test_list_collections_limit(self, tmp_db: Path) -> None:
        result = runner.invoke(app, ["db", "collections", "--db", str(tmp_db), "--limit", "1"])
        assert result.exit_code == 0


class TestDbStatus:
    def test_status(self, tmp_db: Path) -> None:
        result = runner.invoke(app, ["db", "status", "--db", str(tmp_db)])
        assert result.exit_code == 0
        assert "Collection runs" in result.output
        assert "2" in result.output  # 2 collection runs

    def test_status_missing_db(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["db", "status", "--db", str(tmp_path / "nope.duckdb")])
        assert result.exit_code == 1
