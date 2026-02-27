"""Tests for _shared utilities."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from caldera_cli._shared import find_project_root, get_db_path, DEFAULT_DB_PATH


class TestGetDbPath:
    def test_explicit_path_wins(self) -> None:
        p = Path("/tmp/explicit.duckdb")
        assert get_db_path(p) == p

    def test_caldera_db_path_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CALDERA_DB_PATH", "/tmp/env.duckdb")
        assert get_db_path() == Path("/tmp/env.duckdb")

    def test_db_path_env_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DB_PATH", "/tmp/fallback.duckdb")
        assert get_db_path() == Path("/tmp/fallback.duckdb")

    def test_caldera_db_path_takes_precedence(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CALDERA_DB_PATH", "/tmp/primary.duckdb")
        monkeypatch.setenv("DB_PATH", "/tmp/secondary.duckdb")
        assert get_db_path() == Path("/tmp/primary.duckdb")

    def test_default(self) -> None:
        assert get_db_path() == DEFAULT_DB_PATH

    def test_explicit_overrides_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CALDERA_DB_PATH", "/tmp/env.duckdb")
        p = Path("/tmp/explicit.duckdb")
        assert get_db_path(p) == p


class TestFindProjectRoot:
    def test_finds_root(self, project_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(project_root / "src" / "tools")
        # Clear the lru_cache so fresh lookup happens
        find_project_root.cache_clear()
        assert find_project_root() == project_root

    def test_fails_when_not_in_project(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        find_project_root.cache_clear()
        with pytest.raises(SystemExit):
            find_project_root()
