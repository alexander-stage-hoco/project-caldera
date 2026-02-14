"""Unit tests for git-blame-scanner build_repos.py.

Tests cover the helper functions used to construct synthetic repos:
- write_file: file creation with controlled line counts
- run_git: git command execution with author/date env
- init_repo: fresh repo initialization
- add_file / modify_file: commit workflows
- build_* functions: overall repo construction
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

from scripts.build_repos import (
    AUTHORS,
    run_git,
    init_repo,
    write_file,
    add_file,
    modify_file,
    build_single_author,
    build_balanced,
    build_concentrated,
    build_high_churn,
    main,
)


# ---------------------------------------------------------------------------
# write_file
# ---------------------------------------------------------------------------

class TestWriteFile:
    """Tests for write_file helper."""

    def test_creates_file_with_correct_lines(self, tmp_path: Path):
        """File should have the requested number of lines."""
        write_file(tmp_path, "module.py", 10)
        content = (tmp_path / "module.py").read_text()
        # Content ends with \n so split produces an extra empty string
        lines = content.rstrip("\n").split("\n")
        assert len(lines) == 10

    def test_creates_nested_directories(self, tmp_path: Path):
        """Parent directories should be created automatically."""
        write_file(tmp_path, "src/deep/nested/file.py", 5)
        assert (tmp_path / "src" / "deep" / "nested" / "file.py").exists()

    def test_first_line_is_docstring(self, tmp_path: Path):
        """First line should be a module docstring."""
        write_file(tmp_path, "mod.py", 5)
        content = (tmp_path / "mod.py").read_text()
        assert content.startswith('"""Module: mod.py"""')

    def test_minimum_lines(self, tmp_path: Path):
        """With lines=2, produces docstring + blank line (no data lines)."""
        write_file(tmp_path, "tiny.py", 2)
        content = (tmp_path / "tiny.py").read_text()
        # Content is: '"""Module: tiny.py"""\n\n' (docstring + blank + trailing newline)
        assert content.startswith('"""Module: tiny.py"""')
        # range(lines-2) == range(0), so no line_N entries
        assert "line_0" not in content


# ---------------------------------------------------------------------------
# run_git
# ---------------------------------------------------------------------------

class TestRunGit:
    """Tests for run_git helper."""

    def test_sets_author_env(self, tmp_path: Path):
        """Author name/email should be set in environment."""
        proc = MagicMock(returncode=0, stdout="ok", stderr="")
        with patch("scripts.build_repos.subprocess.run", return_value=proc) as mock_run:
            run_git(tmp_path, "commit", "-m", "test", author="alice")

        call_kwargs = mock_run.call_args
        env = call_kwargs.kwargs["env"]
        assert env["GIT_AUTHOR_NAME"] == "Alice Developer"
        assert env["GIT_AUTHOR_EMAIL"] == "alice@example.com"
        assert env["GIT_COMMITTER_NAME"] == "Alice Developer"
        assert env["GIT_COMMITTER_EMAIL"] == "alice@example.com"

    def test_sets_date_env(self, tmp_path: Path):
        """Date should be set in environment when provided."""
        dt = datetime(2025, 6, 15, 12, 30, 0)
        proc = MagicMock(returncode=0, stdout="ok", stderr="")
        with patch("scripts.build_repos.subprocess.run", return_value=proc) as mock_run:
            run_git(tmp_path, "log", date=dt)

        env = mock_run.call_args.kwargs["env"]
        assert env["GIT_AUTHOR_DATE"] == "2025-06-15 12:30:00"
        assert env["GIT_COMMITTER_DATE"] == "2025-06-15 12:30:00"

    def test_no_author_no_date_env(self, tmp_path: Path):
        """Without author/date, those env vars should not be overridden."""
        proc = MagicMock(returncode=0, stdout="ok", stderr="")
        with patch("scripts.build_repos.subprocess.run", return_value=proc) as mock_run:
            run_git(tmp_path, "status")

        env = mock_run.call_args.kwargs["env"]
        assert "GIT_AUTHOR_NAME" not in env
        assert "GIT_AUTHOR_DATE" not in env

    def test_returns_stdout(self, tmp_path: Path):
        """Should return the stdout of the command."""
        proc = MagicMock(returncode=0, stdout="abc123\n", stderr="")
        with patch("scripts.build_repos.subprocess.run", return_value=proc):
            result = run_git(tmp_path, "rev-parse", "HEAD")
        assert result == "abc123\n"

    def test_cwd_is_repo_path(self, tmp_path: Path):
        """Command should run in repo_path directory."""
        proc = MagicMock(returncode=0, stdout="", stderr="")
        with patch("scripts.build_repos.subprocess.run", return_value=proc) as mock_run:
            run_git(tmp_path, "status")
        assert mock_run.call_args.kwargs["cwd"] == tmp_path


# ---------------------------------------------------------------------------
# init_repo
# ---------------------------------------------------------------------------

class TestInitRepo:
    """Tests for init_repo helper."""

    def test_creates_directory(self, tmp_path: Path):
        """Should create repo directory if it does not exist."""
        repo_path = tmp_path / "new-repo"
        with patch("scripts.build_repos.run_git") as mock_git:
            init_repo(repo_path)
        assert repo_path.exists()

    def test_removes_existing_directory(self, tmp_path: Path):
        """Should remove existing directory before creating fresh repo."""
        repo_path = tmp_path / "existing"
        repo_path.mkdir()
        (repo_path / "old_file.txt").write_text("stale")

        with patch("scripts.build_repos.run_git"):
            init_repo(repo_path)

        assert repo_path.exists()
        assert not (repo_path / "old_file.txt").exists()

    def test_calls_git_init_and_config(self, tmp_path: Path):
        """Should call git init and set user config."""
        repo_path = tmp_path / "repo"
        with patch("scripts.build_repos.run_git") as mock_git:
            init_repo(repo_path)

        calls = mock_git.call_args_list
        # First call: git init
        assert calls[0] == call(repo_path, "init")
        # Second: git config user.name
        assert calls[1] == call(repo_path, "config", "user.name", "Test User")
        # Third: git config user.email
        assert calls[2] == call(repo_path, "config", "user.email", "test@example.com")


# ---------------------------------------------------------------------------
# add_file / modify_file
# ---------------------------------------------------------------------------

class TestAddFile:
    """Tests for add_file helper."""

    def test_creates_file_and_commits(self, tmp_path: Path):
        """Should write file, git add, and git commit."""
        with patch("scripts.build_repos.run_git") as mock_git:
            add_file(tmp_path, "src/new.py", 10, "alice", "Add new module")

        assert (tmp_path / "src" / "new.py").exists()
        calls = mock_git.call_args_list
        assert calls[0] == call(tmp_path, "add", "src/new.py")
        assert calls[1] == call(
            tmp_path, "commit", "-m", "Add new module",
            author="alice", date=None,
        )


class TestModifyFile:
    """Tests for modify_file helper."""

    def test_appends_lines_and_commits(self, tmp_path: Path):
        """Should append lines to existing file and commit."""
        # Create initial file
        (tmp_path / "existing.py").write_text("line1\nline2\n")

        with patch("scripts.build_repos.run_git") as mock_git:
            modify_file(tmp_path, "existing.py", 3, "bob", "Add more lines")

        content = (tmp_path / "existing.py").read_text()
        assert "added_line_0" in content
        assert "added_line_1" in content
        assert "added_line_2" in content

        calls = mock_git.call_args_list
        assert calls[0] == call(tmp_path, "add", "existing.py")
        assert calls[1] == call(
            tmp_path, "commit", "-m", "Add more lines",
            author="bob", date=None,
        )


# ---------------------------------------------------------------------------
# build_* functions
# ---------------------------------------------------------------------------

class TestBuildFunctions:
    """Tests for the build_* repo construction functions."""

    def test_build_single_author_calls_init_and_add(self, tmp_path: Path):
        """build_single_author should init repo and add 4 files."""
        with patch("scripts.build_repos.init_repo") as mock_init, \
             patch("scripts.build_repos.add_file") as mock_add:
            build_single_author(tmp_path)

        mock_init.assert_called_once_with(tmp_path / "single-author")
        assert mock_add.call_count == 4

    def test_build_balanced_calls_init_add_modify(self, tmp_path: Path):
        """build_balanced should init, create 3 files, modify each twice."""
        with patch("scripts.build_repos.init_repo") as mock_init, \
             patch("scripts.build_repos.add_file") as mock_add, \
             patch("scripts.build_repos.modify_file") as mock_modify:
            build_balanced(tmp_path)

        mock_init.assert_called_once_with(tmp_path / "balanced")
        assert mock_add.call_count == 3
        assert mock_modify.call_count == 6  # 2 modifications per file

    def test_build_concentrated_structure(self, tmp_path: Path):
        """build_concentrated should create 4 files with specific authors."""
        with patch("scripts.build_repos.init_repo"), \
             patch("scripts.build_repos.add_file") as mock_add, \
             patch("scripts.build_repos.modify_file") as mock_modify:
            build_concentrated(tmp_path)

        assert mock_add.call_count == 4
        # Verify bob's exclusive test file
        bob_calls = [c for c in mock_add.call_args_list if c.args[3] == "bob"]
        assert len(bob_calls) == 1
        assert "test_engine.py" in bob_calls[0].args[1]

    def test_build_high_churn_commits(self, tmp_path: Path):
        """build_high_churn should create files with many dated commits."""
        with patch("scripts.build_repos.init_repo"), \
             patch("scripts.build_repos.add_file") as mock_add, \
             patch("scripts.build_repos.modify_file") as mock_modify:
            build_high_churn(tmp_path)

        # 3 initial files + 5 active + 3 collaborative + 2 moderate modifications
        assert mock_add.call_count == 3
        assert mock_modify.call_count == 10  # 5 + 3 + 2


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

class TestBuildReposMain:
    """Tests for the build_repos main function."""

    def test_calls_all_builders(self):
        """main should invoke all four build functions."""
        with patch("scripts.build_repos.build_single_author") as b1, \
             patch("scripts.build_repos.build_balanced") as b2, \
             patch("scripts.build_repos.build_concentrated") as b3, \
             patch("scripts.build_repos.build_high_churn") as b4:
            main()

        b1.assert_called_once()
        b2.assert_called_once()
        b3.assert_called_once()
        b4.assert_called_once()


# ---------------------------------------------------------------------------
# AUTHORS constant
# ---------------------------------------------------------------------------

class TestAuthorsConstant:
    """Tests for the AUTHORS configuration."""

    def test_three_authors_defined(self):
        """Should have alice, bob, and carol."""
        assert "alice" in AUTHORS
        assert "bob" in AUTHORS
        assert "carol" in AUTHORS

    def test_author_tuples_have_name_and_email(self):
        """Each author should be a (name, email) tuple."""
        for key, (name, email) in AUTHORS.items():
            assert isinstance(name, str) and len(name) > 0
            assert "@" in email
