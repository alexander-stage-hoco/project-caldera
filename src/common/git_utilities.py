"""Shared git utilities for tool analysis scripts.

Provides common git operations used across multiple tools for commit resolution,
validation, and repository inspection.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

# Standard fallback commit hash for non-git repositories
FALLBACK_COMMIT = "0" * 40


def git_run(repo_path: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a git command in the target repository.

    Args:
        repo_path: Path to the git repository.
        args: Git command arguments (without 'git' prefix).

    Returns:
        CompletedProcess with stdout/stderr captured as text.

    Example:
        result = git_run(repo, ["rev-parse", "HEAD"])
        if result.returncode == 0:
            commit = result.stdout.strip()
    """
    return subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True,
        text=True,
    )


def git_head(repo_path: Path) -> str | None:
    """Return HEAD commit SHA for repo_path if available.

    Args:
        repo_path: Path to the git repository.

    Returns:
        The full 40-character SHA of HEAD, or None if not a git repo
        or HEAD cannot be resolved.
    """
    result = git_run(repo_path, ["rev-parse", "HEAD"])
    return result.stdout.strip() if result.returncode == 0 else None


def commit_exists(repo_path: Path, commit: str) -> bool:
    """Check whether a commit exists in the given repository.

    Args:
        repo_path: Path to the git repository.
        commit: Commit SHA or reference to check.

    Returns:
        True if the commit exists, False otherwise.
    """
    result = git_run(repo_path, ["cat-file", "-e", f"{commit}^{{commit}}"])
    return result.returncode == 0


def fallback_commit_hash() -> str:
    """Return the standard fallback commit hash for non-git repositories.

    Returns:
        A 40-character string of zeros ("0" * 40).
    """
    return FALLBACK_COMMIT


def is_fallback_commit(commit: str) -> bool:
    """Check if a commit hash is the fallback placeholder.

    Args:
        commit: Commit SHA to check.

    Returns:
        True if the commit is the fallback hash (all zeros), False otherwise.
    """
    return commit == FALLBACK_COMMIT


def resolve_commit(
    repo_path: Path,
    commit_arg: str | None,
    fallback_repo: Path | None = None,
    *,
    strict: bool = False,
) -> str:
    """Resolve a valid commit SHA for the target repository.

    This function handles commit resolution with two different strategies based
    on the `strict` parameter:

    - strict=True (for scc, lizard, scancode, symbol-scanner, trivy):
      Raises ValueError if commit_arg is provided but not found in either
      repo_path or fallback_repo.

    - strict=False (for semgrep, devskim, layout-scanner, sonarqube):
      Trusts the orchestrator and returns commit_arg as-is if provided,
      without validation.

    Args:
        repo_path: Path to the target repository.
        commit_arg: Commit SHA provided via CLI argument, or None.
        fallback_repo: Optional secondary repository to check for the commit
            (useful when analyzing subdirectories of a larger repo).
        strict: If True, raise ValueError when commit_arg is not found.
            If False, trust the orchestrator and return commit_arg as-is.

    Returns:
        A valid commit SHA string. Priority order:
        1. commit_arg if provided and (found or strict=False)
        2. HEAD of repo_path
        3. HEAD of fallback_repo (if provided)
        4. fallback_commit_hash() for non-git directories

    Raises:
        ValueError: When strict=True and commit_arg is not found in any repo.

    Example:
        # Strict mode (raises on missing commit)
        commit = resolve_commit(repo, args.commit, strict=True)

        # Lenient mode (trusts orchestrator)
        commit = resolve_commit(repo, args.commit, strict=False)
    """
    # Treat the all-zeros placeholder as "no commit provided" so strict tools
    # can still run against non-git repos (or repos where the orchestrator
    # intentionally passed a fallback sentinel).
    if commit_arg and not is_fallback_commit(commit_arg):
        if commit_exists(repo_path, commit_arg):
            return commit_arg
        if fallback_repo and commit_exists(fallback_repo, commit_arg):
            return commit_arg
        if strict:
            raise ValueError(f"Commit not found in repo: {commit_arg}")
        # Non-strict: trust the orchestrator, return as-is
        return commit_arg

    # No commit_arg provided - auto-detect
    head = git_head(repo_path)
    if head:
        return head

    if fallback_repo:
        head = git_head(fallback_repo)
        if head:
            return head

    return fallback_commit_hash()
