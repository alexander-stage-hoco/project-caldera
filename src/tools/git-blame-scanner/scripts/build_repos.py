#!/usr/bin/env python3
"""Build synthetic git repositories with controlled authorship patterns.

Creates test repositories for git-blame-scanner evaluation:
1. single-author: All files by one author (knowledge silos)
2. balanced: Equal contribution from 3 authors
3. concentrated: 80% from one author (high concentration)
4. high-churn: Many recent commits for churn validation
"""

from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


# Author configurations
AUTHORS = {
    "alice": ("Alice Developer", "alice@example.com"),
    "bob": ("Bob Engineer", "bob@example.com"),
    "carol": ("Carol Coder", "carol@example.com"),
}


def run_git(
    repo_path: Path,
    *args: str,
    author: str | None = None,
    date: datetime | None = None,
) -> str:
    """Run a git command in the repository."""
    env = os.environ.copy()
    if author:
        name, email = AUTHORS[author]
        env["GIT_AUTHOR_NAME"] = name
        env["GIT_AUTHOR_EMAIL"] = email
        env["GIT_COMMITTER_NAME"] = name
        env["GIT_COMMITTER_EMAIL"] = email

    if date:
        date_str = date.strftime("%Y-%m-%d %H:%M:%S")
        env["GIT_AUTHOR_DATE"] = date_str
        env["GIT_COMMITTER_DATE"] = date_str

    result = subprocess.run(
        ["git"] + list(args),
        cwd=repo_path,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0 and result.stderr:
        print(f"Git error: {result.stderr}")
    return result.stdout


def init_repo(repo_path: Path) -> None:
    """Initialize a fresh git repository."""
    if repo_path.exists():
        shutil.rmtree(repo_path)
    repo_path.mkdir(parents=True)
    run_git(repo_path, "init")
    run_git(repo_path, "config", "user.name", "Test User")
    run_git(repo_path, "config", "user.email", "test@example.com")


def write_file(repo_path: Path, filename: str, lines: int) -> None:
    """Write a file with the specified number of lines."""
    filepath = repo_path / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)

    content_lines = [f'"""Module: {filename}"""', ""]
    for i in range(lines - 2):
        content_lines.append(f"line_{i} = {i}")

    filepath.write_text("\n".join(content_lines) + "\n")


def add_file(
    repo_path: Path,
    filename: str,
    lines: int,
    author: str,
    message: str,
    date: datetime | None = None,
) -> None:
    """Add a file with specified number of lines and commit."""
    write_file(repo_path, filename, lines)
    run_git(repo_path, "add", filename)
    run_git(repo_path, "commit", "-m", message, author=author, date=date)


def modify_file(
    repo_path: Path,
    filename: str,
    additional_lines: int,
    author: str,
    message: str,
    date: datetime | None = None,
) -> None:
    """Append lines to an existing file and commit."""
    filepath = repo_path / filename
    existing_content = filepath.read_text()
    new_lines = [f"added_line_{i} = {i}" for i in range(additional_lines)]
    filepath.write_text(existing_content + "\n".join(new_lines) + "\n")

    run_git(repo_path, "add", filename)
    run_git(repo_path, "commit", "-m", message, author=author, date=date)


def build_single_author(base_path: Path) -> None:
    """Build repo where one author owns 100% of all files."""
    repo_path = base_path / "single-author"
    print(f"Building {repo_path}...")
    init_repo(repo_path)

    # All files by Alice - these should all be knowledge silos
    add_file(repo_path, "src/main.py", 150, "alice", "Initial main module")
    add_file(repo_path, "src/utils.py", 120, "alice", "Add utility functions")
    add_file(repo_path, "src/config.py", 80, "alice", "Add configuration")
    add_file(repo_path, "tests/test_main.py", 60, "alice", "Add tests")

    print("  Created: 4 files, 1 author")
    print("  Expected: unique_authors=1 for all, 4 knowledge silos (>100 LOC)")


def build_balanced(base_path: Path) -> None:
    """Build repo with equal contribution from 3 authors per file."""
    repo_path = base_path / "balanced"
    print(f"Building {repo_path}...")
    init_repo(repo_path)

    # Create files with contributions from all authors
    # File 1: Alice creates, Bob and Carol add equal amounts
    add_file(repo_path, "src/core.py", 40, "alice", "Initial core module")
    modify_file(repo_path, "src/core.py", 40, "bob", "Add Bob's contributions")
    modify_file(repo_path, "src/core.py", 40, "carol", "Add Carol's contributions")

    # File 2: Bob creates, Alice and Carol add equal amounts
    add_file(repo_path, "src/api.py", 40, "bob", "Initial API module")
    modify_file(repo_path, "src/api.py", 40, "alice", "Add Alice's contributions")
    modify_file(repo_path, "src/api.py", 40, "carol", "Add Carol's API work")

    # File 3: Carol creates, Alice and Bob add equal amounts
    add_file(repo_path, "src/models.py", 40, "carol", "Initial models")
    modify_file(repo_path, "src/models.py", 40, "alice", "Add Alice's models")
    modify_file(repo_path, "src/models.py", 40, "bob", "Add Bob's models")

    print("  Created: 3 files, 3 authors per file")
    print("  Expected: unique_authors=3 for all, top_author_pct ~33%")


def build_concentrated(base_path: Path) -> None:
    """Build repo where one author dominates (>80% ownership)."""
    repo_path = base_path / "concentrated"
    print(f"Building {repo_path}...")
    init_repo(repo_path)

    # File 1: Alice owns 90%, Bob 10%
    add_file(repo_path, "src/engine.py", 90, "alice", "Initial engine")
    modify_file(repo_path, "src/engine.py", 10, "bob", "Minor fixes")

    # File 2: Alice owns 85%, Carol 15%
    add_file(repo_path, "src/processor.py", 85, "alice", "Initial processor")
    modify_file(repo_path, "src/processor.py", 15, "carol", "Add edge cases")

    # File 3: Bob owns 100% (single author knowledge silo)
    add_file(repo_path, "tests/test_engine.py", 120, "bob", "Add comprehensive tests")

    # File 4: Alice owns 80%, Bob and Carol share 20%
    add_file(repo_path, "src/utils.py", 80, "alice", "Initial utils")
    modify_file(repo_path, "src/utils.py", 10, "bob", "Add helper functions")
    modify_file(repo_path, "src/utils.py", 10, "carol", "Add validation helpers")

    print("  Created: 4 files, 3 authors")
    print("  Expected: high_concentration_files=3 (>80%), knowledge_silos=1")


def build_high_churn(base_path: Path) -> None:
    """Build repo with many recent commits for churn testing."""
    repo_path = base_path / "high-churn"
    print(f"Building {repo_path}...")
    init_repo(repo_path)

    now = datetime.now()

    # File 1: Created 120 days ago, many recent commits
    old_date = now - timedelta(days=120)
    add_file(repo_path, "src/active.py", 50, "alice", "Initial active module", date=old_date)

    # Add commits in the last 30 days
    for i in range(5):
        commit_date = now - timedelta(days=25 - i * 5)
        modify_file(
            repo_path, "src/active.py", 10, "alice",
            f"Update active module ({i+1})", date=commit_date
        )

    # Add commits in the 30-90 day range
    for i in range(3):
        commit_date = now - timedelta(days=60 - i * 10)
        modify_file(
            repo_path, "src/active.py", 10, "bob",
            f"Collaborate on active ({i+1})", date=commit_date
        )

    # File 2: Created 180 days ago, NO recent commits (stale)
    stale_date = now - timedelta(days=180)
    add_file(repo_path, "src/stale.py", 100, "carol", "Initial stale module", date=stale_date)

    # File 3: Created 60 days ago, moderate churn
    moderate_date = now - timedelta(days=60)
    add_file(repo_path, "src/moderate.py", 60, "bob", "Initial moderate module", date=moderate_date)

    for i in range(2):
        commit_date = now - timedelta(days=45 - i * 15)
        modify_file(
            repo_path, "src/moderate.py", 15, "alice",
            f"Update moderate ({i+1})", date=commit_date
        )

    print("  Created: 3 files, 3 authors")
    print("  Expected: active.py churn_30d=5, churn_90d=8; stale.py churn_90d=0")


def main():
    """Build all synthetic repositories."""
    base_path = Path(__file__).parent.parent / "eval-repos" / "synthetic"

    print("=" * 60)
    print("Building Synthetic Test Repositories for git-blame-scanner")
    print("=" * 60)

    build_single_author(base_path)
    build_balanced(base_path)
    build_concentrated(base_path)
    build_high_churn(base_path)

    print("=" * 60)
    print("All synthetic repositories created!")
    print("=" * 60)


if __name__ == "__main__":
    main()
