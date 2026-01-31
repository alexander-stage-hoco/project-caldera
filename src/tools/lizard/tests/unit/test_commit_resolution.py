"""Tests for commit resolution helpers."""

from __future__ import annotations

import pytest

from scripts import analyze


class DummyResult:
    """Minimal subprocess result stub for git commands."""

    def __init__(self, returncode: int, stdout: str = ""):
        self.returncode = returncode
        self.stdout = stdout


def test_resolve_commit_accepts_valid_commit(monkeypatch, tmp_path):
    """Provided commit is accepted when it exists."""
    def fake_git_run(repo_path, args):
        if args[:2] == ["cat-file", "-e"]:
            return DummyResult(0)
        return DummyResult(1)

    monkeypatch.setattr(analyze, "_git_run", fake_git_run)
    commit = analyze._resolve_commit(tmp_path, "a" * 40, None)
    assert commit == "a" * 40


def test_resolve_commit_uses_head(monkeypatch, tmp_path):
    """Missing commit uses HEAD from repo."""
    def fake_git_run(repo_path, args):
        if args[:2] == ["rev-parse", "HEAD"]:
            return DummyResult(0, "b" * 40)
        return DummyResult(1)

    monkeypatch.setattr(analyze, "_git_run", fake_git_run)
    commit = analyze._resolve_commit(tmp_path, "", None)
    assert commit == "b" * 40


def test_resolve_commit_unversioned_when_missing_head(monkeypatch, tmp_path):
    """Missing git metadata falls back to standard zero hash."""
    def fake_git_run(repo_path, args):
        return DummyResult(1)

    monkeypatch.setattr(analyze, "_git_run", fake_git_run)
    commit = analyze._resolve_commit(tmp_path, "", None)
    assert commit == "0" * 40


def test_resolve_commit_errors_on_missing(monkeypatch, tmp_path):
    """Invalid commit raises a ValueError."""
    def fake_git_run(repo_path, args):
        return DummyResult(1)

    monkeypatch.setattr(analyze, "_git_run", fake_git_run)
    with pytest.raises(ValueError):
        analyze._resolve_commit(tmp_path, "deadbeef", None)
