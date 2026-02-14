"""Unit tests for create_synthetic_repos dataclasses and SYNTHETIC_REPOS specs."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from create_synthetic_repos import (
    RepoSpec,
    SecretSpec,
    SYNTHETIC_REPOS,
    create_repo,
    run_git,
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
class TestSecretSpec:
    """Tests for SecretSpec dataclass."""

    def test_minimal_secret_spec(self) -> None:
        spec = SecretSpec(
            file_path=".env",
            secret_type="generic-api-key",
            secret_value="API_KEY=abc123",
            rule_id="generic-api-key",
        )
        assert spec.file_path == ".env"
        assert spec.line_number == 1  # default
        assert spec.commit_message == "Add configuration"  # default
        assert spec.deleted_in_later_commit is False  # default

    def test_historical_secret_spec(self) -> None:
        spec = SecretSpec(
            file_path="config/secrets.py",
            secret_type="aws-access-key-id",
            secret_value="AWS_KEY='AKIAIOSFODNN7EXAMPLE'",
            rule_id="aws-access-key-id",
            line_number=5,
            deleted_in_later_commit=True,
        )
        assert spec.deleted_in_later_commit is True
        assert spec.line_number == 5


class TestRepoSpec:
    """Tests for RepoSpec dataclass."""

    def test_minimal_repo_spec(self) -> None:
        spec = RepoSpec(name="test", description="Test repo")
        assert spec.name == "test"
        assert spec.secrets == []
        assert spec.files == {}

    def test_repo_spec_with_content(self) -> None:
        spec = RepoSpec(
            name="complex",
            description="Complex repo",
            secrets=[
                SecretSpec(
                    file_path=".env",
                    secret_type="key",
                    secret_value="KEY=val",
                    rule_id="key",
                ),
            ],
            files={"README.md": "# Hello"},
        )
        assert len(spec.secrets) == 1
        assert len(spec.files) == 1


# ---------------------------------------------------------------------------
# SYNTHETIC_REPOS data integrity
# ---------------------------------------------------------------------------
class TestSyntheticRepos:
    """Validate the SYNTHETIC_REPOS constant definitions."""

    def test_repos_not_empty(self) -> None:
        assert len(SYNTHETIC_REPOS) > 0

    def test_all_have_unique_names(self) -> None:
        names = [r.name for r in SYNTHETIC_REPOS]
        assert len(names) == len(set(names))

    def test_all_have_descriptions(self) -> None:
        for spec in SYNTHETIC_REPOS:
            assert spec.description, f"{spec.name} missing description"

    def test_no_secrets_repo_exists(self) -> None:
        """There should be a baseline repo with zero secrets."""
        names = [r.name for r in SYNTHETIC_REPOS]
        assert "no-secrets" in names
        no_secrets = next(r for r in SYNTHETIC_REPOS if r.name == "no-secrets")
        assert len(no_secrets.secrets) == 0

    def test_historical_secrets_repo_exists(self) -> None:
        """There should be a repo with deleted-but-findable secrets."""
        historical = next(
            (r for r in SYNTHETIC_REPOS if r.name == "historical-secrets"), None
        )
        assert historical is not None
        has_deleted = any(s.deleted_in_later_commit for s in historical.secrets)
        assert has_deleted

    def test_api_keys_repo_has_secrets(self) -> None:
        api_keys = next(
            (r for r in SYNTHETIC_REPOS if r.name == "api-keys"), None
        )
        assert api_keys is not None
        assert len(api_keys.secrets) > 0

    def test_mixed_secrets_has_multiple_types(self) -> None:
        mixed = next(
            (r for r in SYNTHETIC_REPOS if r.name == "mixed-secrets"), None
        )
        assert mixed is not None
        rule_ids = {s.rule_id for s in mixed.secrets}
        assert len(rule_ids) > 1


# ---------------------------------------------------------------------------
# run_git
# ---------------------------------------------------------------------------
class TestRunGit:
    """Tests for run_git helper."""

    def test_run_git_calls_subprocess(self) -> None:
        with patch("create_synthetic_repos.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            run_git(Path("/tmp/repo"), "init")
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args[0] == "git"
            assert "-C" in args
            assert "init" in args


# ---------------------------------------------------------------------------
# create_repo
# ---------------------------------------------------------------------------
class TestCreateRepo:
    """Tests for create_repo function."""

    def test_creates_clean_repo(self, tmp_path: Path) -> None:
        """Create a no-secrets repo and verify directory structure."""
        spec = RepoSpec(
            name="clean",
            description="Clean repo",
            files={"README.md": "# Test", "src/main.py": "print('hi')"},
        )

        with patch("create_synthetic_repos.run_git") as mock_git:
            create_repo(tmp_path, spec)

        repo_dir = tmp_path / "clean"
        assert repo_dir.exists()
        assert (repo_dir / "README.md").read_text() == "# Test"
        assert (repo_dir / "src" / "main.py").read_text() == "print('hi')"
        # git init + config email + config name + add + commit = 5 calls
        assert mock_git.call_count >= 4

    def test_creates_repo_with_historical_secrets(self, tmp_path: Path) -> None:
        """Repo with deleted secrets should have two commits."""
        spec = RepoSpec(
            name="hist",
            description="Historical secrets",
            secrets=[
                SecretSpec(
                    file_path="config/secrets.py",
                    secret_type="aws-access-key-id",
                    secret_value="KEY='AKIAIOSFODNN7EXAMPLE'",
                    rule_id="aws-access-key-id",
                    deleted_in_later_commit=True,
                ),
            ],
            files={
                "config/secrets.py": "# Cleaned up",
                "README.md": "# Hist repo",
            },
        )

        with patch("create_synthetic_repos.run_git") as mock_git:
            create_repo(tmp_path, spec)

        # Second commit for cleanup
        commit_calls = [
            c for c in mock_git.call_args_list
            if "commit" in c[0][1:]
        ]
        assert len(commit_calls) >= 2  # Initial + cleanup

    def test_overwrites_existing_directory(self, tmp_path: Path) -> None:
        """Existing repo directory should be cleaned up first."""
        repo_dir = tmp_path / "existing"
        repo_dir.mkdir()
        (repo_dir / "old_file.txt").write_text("old")

        spec = RepoSpec(
            name="existing",
            description="Overwrite test",
            files={"new_file.txt": "new content"},
        )

        with patch("create_synthetic_repos.run_git"):
            create_repo(tmp_path, spec)

        assert not (repo_dir / "old_file.txt").exists()
        assert (repo_dir / "new_file.txt").exists()

    def test_env_file_historical_deletion(self, tmp_path: Path) -> None:
        """Historical .env secret should create then delete the file."""
        spec = RepoSpec(
            name="env-hist",
            description="Env historical",
            secrets=[
                SecretSpec(
                    file_path=".env",
                    secret_type="generic-api-key",
                    secret_value="API_KEY=secret",
                    rule_id="generic-api-key",
                    deleted_in_later_commit=True,
                ),
            ],
            files={"README.md": "# Test"},
        )

        with patch("create_synthetic_repos.run_git"):
            create_repo(tmp_path, spec)

        repo_dir = tmp_path / "env-hist"
        # .env should be deleted in cleanup (empty new_content means delete)
        assert not (repo_dir / ".env").exists()
