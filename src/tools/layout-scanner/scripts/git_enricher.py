"""
Git metadata enricher for Layout Scanner.

This module collects git history metadata for files in a repository,
populating fields like first_commit_date, last_commit_date, commit_count,
and author_count.
"""

import subprocess
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class GitFileMetadata:
    """Git metadata for a single file."""

    first_commit_date: Optional[str] = None
    last_commit_date: Optional[str] = None
    commit_count: int = 0
    author_count: int = 0


@dataclass
class GitEnrichmentResult:
    """Result of git enrichment pass."""

    is_git_repo: bool
    file_metadata: Dict[str, GitFileMetadata] = field(default_factory=dict)
    tracked_file_count: int = 0
    enriched_file_count: int = 0
    duration_ms: int = 0
    error: Optional[str] = None


def is_git_repository(repo_path: Path) -> bool:
    """
    Check if a path is inside a git repository.

    Args:
        repo_path: Path to check

    Returns:
        True if path is in a git repository, False otherwise
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def get_tracked_files(repo_path: Path) -> Set[str]:
    """
    Get set of files tracked by git.

    Args:
        repo_path: Path to git repository

    Returns:
        Set of relative file paths tracked by git
    """
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            logger.warning(f"git ls-files failed: {result.stderr}")
            return set()

        return {line.strip() for line in result.stdout.splitlines() if line.strip()}
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.warning(f"Failed to get tracked files: {e}")
        return set()


def _parse_git_log_output(output: str) -> Dict[str, List[Tuple[str, str]]]:
    """
    Parse git log output with commit info and file names.

    Expected format per commit:
    <hash>|<author_email>|<iso_date>
    <empty line>
    file1.py
    file2.py

    Args:
        output: Raw git log output

    Returns:
        Dict mapping file paths to list of (author_email, iso_date) tuples
    """
    file_commits: Dict[str, List[Tuple[str, str]]] = {}

    if not output.strip():
        return file_commits

    current_commit_info = None

    # Process line by line to handle mixed commit headers and file names
    for line in output.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        # Check if this is a commit header (hash|email|date format)
        if "|" in line:
            parts = line.split("|")
            if len(parts) >= 3:
                # commit_hash = parts[0]  # Not currently used
                author_email = parts[1]
                iso_date = parts[2]
                current_commit_info = (author_email, iso_date)
        elif current_commit_info:
            # This is a file name for the current commit
            if line not in file_commits:
                file_commits[line] = []
            file_commits[line].append(current_commit_info)

    return file_commits


def get_file_git_metadata(
    repo_path: Path,
    file_paths: List[str],
    timeout_seconds: int = 120,
) -> Dict[str, GitFileMetadata]:
    """
    Get git metadata for multiple files in a single batch operation.

    Args:
        repo_path: Path to git repository
        file_paths: List of relative file paths to get metadata for
        timeout_seconds: Timeout for git command

    Returns:
        Dict mapping file paths to their GitFileMetadata
    """
    if not file_paths:
        return {}

    # Get tracked files to filter input
    tracked = get_tracked_files(repo_path)
    files_to_query = [f for f in file_paths if f in tracked]

    if not files_to_query:
        logger.debug("No tracked files to query")
        return {}

    # Build git log command
    # --format: hash|author_email|iso_date
    # --name-only: list modified files after each commit
    # --follow: track file renames (only works with single file, so we skip it)
    cmd = [
        "git",
        "log",
        "--format=%H|%ae|%aI",
        "--name-only",
        "--",
    ] + files_to_query

    try:
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )

        if result.returncode != 0:
            logger.warning(f"git log failed: {result.stderr}")
            return {}

        # Parse the output
        file_commits = _parse_git_log_output(result.stdout)

        # Convert to GitFileMetadata
        metadata: Dict[str, GitFileMetadata] = {}

        for file_path, commits in file_commits.items():
            if not commits:
                continue

            # Extract unique authors and dates
            authors = {c[0] for c in commits}
            dates = [c[1] for c in commits]

            # Sort dates to find first/last
            sorted_dates = sorted(dates)

            metadata[file_path] = GitFileMetadata(
                first_commit_date=sorted_dates[0] if sorted_dates else None,
                last_commit_date=sorted_dates[-1] if sorted_dates else None,
                commit_count=len(commits),
                author_count=len(authors),
            )

        return metadata

    except subprocess.TimeoutExpired:
        logger.warning(f"Git log timed out after {timeout_seconds}s")
        return {}
    except (FileNotFoundError, OSError) as e:
        logger.warning(f"Failed to run git log: {e}")
        return {}


def enrich_files(
    repo_path: Path,
    file_paths: List[str],
    timeout_seconds: int = 120,
) -> GitEnrichmentResult:
    """
    Enrich files with git metadata.

    This is the main entry point for git enrichment.

    Args:
        repo_path: Path to repository
        file_paths: List of relative file paths to enrich
        timeout_seconds: Timeout for git operations

    Returns:
        GitEnrichmentResult with metadata for all enriched files
    """
    start_time = datetime.now()

    # Check if this is a git repository
    if not is_git_repository(repo_path):
        duration = int((datetime.now() - start_time).total_seconds() * 1000)
        return GitEnrichmentResult(
            is_git_repo=False,
            duration_ms=duration,
        )

    # Get tracked files
    tracked = get_tracked_files(repo_path)
    tracked_in_scan = [f for f in file_paths if f in tracked]

    try:
        # Get metadata for all tracked files
        metadata = get_file_git_metadata(
            repo_path,
            tracked_in_scan,
            timeout_seconds=timeout_seconds,
        )

        duration = int((datetime.now() - start_time).total_seconds() * 1000)

        return GitEnrichmentResult(
            is_git_repo=True,
            file_metadata=metadata,
            tracked_file_count=len(tracked_in_scan),
            enriched_file_count=len(metadata),
            duration_ms=duration,
        )

    except Exception as e:
        logger.error(f"Git enrichment failed: {e}")
        duration = int((datetime.now() - start_time).total_seconds() * 1000)
        return GitEnrichmentResult(
            is_git_repo=True,
            duration_ms=duration,
            error=str(e),
        )
