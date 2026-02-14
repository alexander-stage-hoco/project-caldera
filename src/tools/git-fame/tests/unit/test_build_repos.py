"""Unit tests for git-fame build_repos.py functions.

Tests the synthetic repository construction functions used to create
evaluation test repos with controlled authorship patterns.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch, call

import pytest

# Add scripts directory to path for imports
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from build_repos import (
    AUTHORS,
    run_git,
    init_repo,
    add_file,
    build_single_author,
    build_multi_author,
    build_bus_factor_1,
    build_balanced,
    build_multi_branch,
)


# =============================================================================
# AUTHORS constant tests
# =============================================================================


class TestAuthorsConstant:
    """Test the AUTHORS configuration constant."""

    def test_authors_has_four_entries(self):
        """AUTHORS should contain exactly 4 author configurations."""
        assert len(AUTHORS) == 4

    def test_each_author_has_name_and_email(self):
        """Each author entry should have (name, email) tuple."""
        for key, (name, email) in AUTHORS.items():
            assert isinstance(name, str)
            assert isinstance(email, str)
            assert "@" in email

    def test_expected_author_keys(self):
        """AUTHORS should contain alice, bob, carol, dave."""
        assert set(AUTHORS.keys()) == {"alice", "bob", "carol", "dave"}


# =============================================================================
# run_git Tests
# =============================================================================


class TestRunGit:
    """Test the run_git helper function."""

    def test_run_git_basic_command(self, tmp_path: Path):
        """Should execute git command in specified directory."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output\n"
        mock_result.stderr = ""

        with patch("build_repos.subprocess.run", return_value=mock_result) as mock_run:
            result = run_git(tmp_path, "status")

        mock_run.assert_called_once()
        cmd_args = mock_run.call_args[0][0]
        assert cmd_args == ["git", "status"]
        assert mock_run.call_args[1]["cwd"] == tmp_path

    def test_run_git_with_author(self, tmp_path: Path):
        """Should set GIT_AUTHOR_* and GIT_COMMITTER_* env vars for author."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("build_repos.subprocess.run", return_value=mock_result) as mock_run:
            run_git(tmp_path, "commit", "-m", "test", author="alice")

        env = mock_run.call_args[1]["env"]
        assert env["GIT_AUTHOR_NAME"] == "Alice Developer"
        assert env["GIT_AUTHOR_EMAIL"] == "alice@example.com"
        assert env["GIT_COMMITTER_NAME"] == "Alice Developer"
        assert env["GIT_COMMITTER_EMAIL"] == "alice@example.com"

    def test_run_git_without_author(self, tmp_path: Path):
        """Without author, should use default environment."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("build_repos.subprocess.run", return_value=mock_result) as mock_run:
            run_git(tmp_path, "init")

        env = mock_run.call_args[1]["env"]
        # Should not have GIT_AUTHOR_NAME set beyond what's in os.environ
        assert "GIT_AUTHOR_NAME" not in env or env["GIT_AUTHOR_NAME"] == os.environ.get("GIT_AUTHOR_NAME", "")

    def test_run_git_returns_stdout(self, tmp_path: Path):
        """Should return stdout from the git command."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "result text"
        mock_result.stderr = ""

        with patch("build_repos.subprocess.run", return_value=mock_result):
            result = run_git(tmp_path, "log")

        assert result == "result text"

    def test_run_git_prints_error_on_failure(self, tmp_path: Path, capsys):
        """Should print error message when git command fails."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "fatal: not a git repository"

        with patch("build_repos.subprocess.run", return_value=mock_result):
            run_git(tmp_path, "log")

        captured = capsys.readouterr()
        assert "Git error" in captured.out


# =============================================================================
# init_repo Tests
# =============================================================================


class TestInitRepo:
    """Test repository initialization."""

    def test_init_repo_creates_directory(self, tmp_path: Path):
        """Should create repo directory and init git."""
        repo_path = tmp_path / "test-repo"

        with patch("build_repos.run_git") as mock_git:
            init_repo(repo_path)

        assert repo_path.exists()
        # Should call git init, config user.name, config user.email
        assert mock_git.call_count == 3

    def test_init_repo_removes_existing(self, tmp_path: Path):
        """Should remove existing directory before creating new one."""
        repo_path = tmp_path / "test-repo"
        repo_path.mkdir()
        (repo_path / "old-file.txt").write_text("old content")

        with patch("build_repos.run_git"):
            init_repo(repo_path)

        assert repo_path.exists()
        assert not (repo_path / "old-file.txt").exists()


# =============================================================================
# add_file Tests
# =============================================================================


class TestAddFile:
    """Test file addition and commit."""

    def test_add_file_creates_file(self, tmp_path: Path):
        """Should create the file at the specified path."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        with patch("build_repos.run_git"):
            add_file(repo_path, "main.py", 50, "alice", "Add main")

        assert (repo_path / "main.py").exists()

    def test_add_file_creates_subdirectories(self, tmp_path: Path):
        """Should create parent directories for nested files."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        with patch("build_repos.run_git"):
            add_file(repo_path, "src/core/engine.py", 30, "bob", "Add engine")

        assert (repo_path / "src" / "core" / "engine.py").exists()

    def test_add_file_calls_git_add_and_commit(self, tmp_path: Path):
        """Should call git add and git commit with correct author."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()

        with patch("build_repos.run_git") as mock_git:
            add_file(repo_path, "test.py", 10, "carol", "Add test")

        # Should have called git add and git commit
        calls = mock_git.call_args_list
        assert any("add" in str(c) for c in calls)
        assert any("commit" in str(c) for c in calls)
        # Commit should use the author
        commit_call = [c for c in calls if "commit" in str(c)][0]
        assert commit_call.kwargs.get("author") == "carol" or commit_call[1].get("author") == "carol"


# =============================================================================
# build_* function tests
# =============================================================================


class TestBuildFunctions:
    """Test the build_* functions that create synthetic repos."""

    def test_build_single_author_creates_four_files(self, tmp_path: Path):
        """build_single_author should create 4 files, all by alice."""
        with patch("build_repos.init_repo") as mock_init, \
             patch("build_repos.add_file") as mock_add:
            build_single_author(tmp_path)

        mock_init.assert_called_once()
        assert mock_add.call_count == 4
        # All files should be by alice
        for c in mock_add.call_args_list:
            assert c[0][3] == "alice"  # author arg

    def test_build_multi_author_creates_six_files(self, tmp_path: Path):
        """build_multi_author should create 6 files across 3 authors."""
        with patch("build_repos.init_repo"), \
             patch("build_repos.add_file") as mock_add:
            build_multi_author(tmp_path)

        assert mock_add.call_count == 6
        authors = [c[0][3] for c in mock_add.call_args_list]
        assert authors.count("alice") == 2
        assert authors.count("bob") == 2
        assert authors.count("carol") == 2

    def test_build_bus_factor_1_has_dominant_alice(self, tmp_path: Path):
        """build_bus_factor_1 should have alice as dominant contributor."""
        with patch("build_repos.init_repo"), \
             patch("build_repos.add_file") as mock_add:
            build_bus_factor_1(tmp_path)

        assert mock_add.call_count == 6
        authors = [c[0][3] for c in mock_add.call_args_list]
        assert authors.count("alice") == 4  # Alice has 4 files
        assert authors.count("bob") == 1
        assert authors.count("carol") == 1

    def test_build_balanced_creates_eight_files(self, tmp_path: Path):
        """build_balanced should create 8 files, 2 per author."""
        with patch("build_repos.init_repo"), \
             patch("build_repos.add_file") as mock_add:
            build_balanced(tmp_path)

        assert mock_add.call_count == 8
        authors = [c[0][3] for c in mock_add.call_args_list]
        assert authors.count("alice") == 2
        assert authors.count("bob") == 2
        assert authors.count("carol") == 2
        assert authors.count("dave") == 2

    def test_build_multi_branch_uses_branches(self, tmp_path: Path):
        """build_multi_branch should create and merge branches."""
        with patch("build_repos.init_repo"), \
             patch("build_repos.add_file"), \
             patch("build_repos.run_git") as mock_git:
            build_multi_branch(tmp_path)

        git_commands = [str(c) for c in mock_git.call_args_list]
        # Should have checkout, merge, and branch creation commands
        assert any("checkout" in c for c in git_commands)
        assert any("merge" in c for c in git_commands)

    def test_build_functions_use_correct_repo_paths(self, tmp_path: Path):
        """Each build function should create its repo at the expected path."""
        with patch("build_repos.init_repo") as mock_init, \
             patch("build_repos.add_file"):
            build_single_author(tmp_path)

        expected_path = tmp_path / "single-author"
        mock_init.assert_called_once_with(expected_path)

    def test_build_multi_author_repo_path(self, tmp_path: Path):
        """build_multi_author should use correct repo name."""
        with patch("build_repos.init_repo") as mock_init, \
             patch("build_repos.add_file"):
            build_multi_author(tmp_path)

        mock_init.assert_called_once_with(tmp_path / "multi-author")

    def test_build_bus_factor_1_repo_path(self, tmp_path: Path):
        """build_bus_factor_1 should use correct repo name."""
        with patch("build_repos.init_repo") as mock_init, \
             patch("build_repos.add_file"):
            build_bus_factor_1(tmp_path)

        mock_init.assert_called_once_with(tmp_path / "bus-factor-1")

    def test_build_balanced_repo_path(self, tmp_path: Path):
        """build_balanced should use correct repo name."""
        with patch("build_repos.init_repo") as mock_init, \
             patch("build_repos.add_file"):
            build_balanced(tmp_path)

        mock_init.assert_called_once_with(tmp_path / "balanced")
