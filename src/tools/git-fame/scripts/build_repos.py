#!/usr/bin/env python3
"""Build synthetic git repositories with controlled authorship patterns.

Creates 5 test repositories:
1. single-author: All code by one author (bus_factor=1, HHI=1.0)
2. multi-author: 3 authors with 50/30/20 split (bus_factor=2, HHI=0.38)
3. bus-factor-1: Dominant author 90%, others 5% each (bus_factor=1, HHI=0.82)
4. balanced: 4 authors with ~25% each (bus_factor=3, HHI=0.25)
5. multi-branch: Multiple branches with activity across different periods
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


# Author configurations
AUTHORS = {
    "alice": ("Alice Developer", "alice@example.com"),
    "bob": ("Bob Engineer", "bob@example.com"),
    "carol": ("Carol Coder", "carol@example.com"),
    "dave": ("Dave Designer", "dave@example.com"),
}


def run_git(repo_path: Path, *args: str, author: str | None = None) -> str:
    """Run a git command in the repository."""
    env = os.environ.copy()
    if author:
        name, email = AUTHORS[author]
        env["GIT_AUTHOR_NAME"] = name
        env["GIT_AUTHOR_EMAIL"] = email
        env["GIT_COMMITTER_NAME"] = name
        env["GIT_COMMITTER_EMAIL"] = email

    result = subprocess.run(
        ["git"] + list(args),
        cwd=repo_path,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
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


def add_file(repo_path: Path, filename: str, lines: int, author: str, message: str) -> None:
    """Add a file with specified number of lines and commit."""
    filepath = repo_path / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Generate Python code with specified line count
    content = f'"""Module: {filename}"""\n\n'
    for i in range(lines - 3):
        content += f"def function_{i}():\n    pass\n\n"

    filepath.write_text(content[:lines * 40])  # Approximate line count

    run_git(repo_path, "add", filename)
    run_git(repo_path, "commit", "-m", message, author=author)


def build_single_author(base_path: Path) -> None:
    """Build repo where one author owns 100% of code."""
    repo_path = base_path / "single-author"
    print(f"Building {repo_path}...")
    init_repo(repo_path)

    # All files by Alice
    add_file(repo_path, "main.py", 100, "alice", "Initial main module")
    add_file(repo_path, "utils.py", 80, "alice", "Add utility functions")
    add_file(repo_path, "config.py", 50, "alice", "Add configuration")
    add_file(repo_path, "models.py", 120, "alice", "Add data models")

    print("  Created: 4 files, 1 author, ~350 LOC")


def build_multi_author(base_path: Path) -> None:
    """Build repo with 3 authors: 50%, 30%, 20% split."""
    repo_path = base_path / "multi-author"
    print(f"Building {repo_path}...")
    init_repo(repo_path)

    # Alice: 50% (~175 LOC)
    add_file(repo_path, "core/engine.py", 100, "alice", "Add core engine")
    add_file(repo_path, "core/processor.py", 75, "alice", "Add processor")

    # Bob: 30% (~105 LOC)
    add_file(repo_path, "api/handlers.py", 60, "bob", "Add API handlers")
    add_file(repo_path, "api/routes.py", 45, "bob", "Add API routes")

    # Carol: 20% (~70 LOC)
    add_file(repo_path, "utils/helpers.py", 40, "carol", "Add helper functions")
    add_file(repo_path, "utils/validators.py", 30, "carol", "Add validators")

    print("  Created: 6 files, 3 authors, ~350 LOC (50/30/20 split)")


def build_bus_factor_1(base_path: Path) -> None:
    """Build repo with dominant author (90%) + minor contributors."""
    repo_path = base_path / "bus-factor-1"
    print(f"Building {repo_path}...")
    init_repo(repo_path)

    # Alice: 90% (~315 LOC)
    add_file(repo_path, "main.py", 80, "alice", "Initial main")
    add_file(repo_path, "core.py", 100, "alice", "Add core logic")
    add_file(repo_path, "services.py", 85, "alice", "Add services")
    add_file(repo_path, "models.py", 50, "alice", "Add models")

    # Bob: 5% (~18 LOC)
    add_file(repo_path, "tests/test_main.py", 18, "bob", "Add tests")

    # Carol: 5% (~17 LOC)
    add_file(repo_path, "config.py", 17, "carol", "Add config")

    print("  Created: 6 files, 3 authors, ~350 LOC (90/5/5 split)")


def build_balanced(base_path: Path) -> None:
    """Build repo with 4 authors, each ~25%."""
    repo_path = base_path / "balanced"
    print(f"Building {repo_path}...")
    init_repo(repo_path)

    # Alice: 25% (~88 LOC)
    add_file(repo_path, "module_a/main.py", 50, "alice", "Add module A main")
    add_file(repo_path, "module_a/utils.py", 38, "alice", "Add module A utils")

    # Bob: 25% (~88 LOC)
    add_file(repo_path, "module_b/main.py", 50, "bob", "Add module B main")
    add_file(repo_path, "module_b/utils.py", 38, "bob", "Add module B utils")

    # Carol: 25% (~88 LOC)
    add_file(repo_path, "module_c/main.py", 50, "carol", "Add module C main")
    add_file(repo_path, "module_c/utils.py", 38, "carol", "Add module C utils")

    # Dave: 25% (~86 LOC)
    add_file(repo_path, "module_d/main.py", 50, "dave", "Add module D main")
    add_file(repo_path, "module_d/utils.py", 36, "dave", "Add module D utils")

    print("  Created: 8 files, 4 authors, ~350 LOC (25/25/25/25 split)")


def build_multi_branch(base_path: Path) -> None:
    """Build repo with multiple branches and contributors across different time periods."""
    repo_path = base_path / "multi-branch"
    print(f"Building {repo_path}...")
    init_repo(repo_path)

    # Main branch: Initial setup by Alice
    add_file(repo_path, "main.py", 60, "alice", "Initial main module")
    add_file(repo_path, "config.py", 40, "alice", "Add configuration")

    # Create develop branch
    run_git(repo_path, "checkout", "-b", "develop")

    # Develop branch: Bob adds features
    add_file(repo_path, "features/auth.py", 80, "bob", "Add authentication module")
    add_file(repo_path, "features/api.py", 70, "bob", "Add API endpoints")

    # Create feature-payments branch from develop
    run_git(repo_path, "checkout", "-b", "feature-payments")

    # Feature branch: Carol adds payment logic
    add_file(repo_path, "features/payments.py", 90, "carol", "Add payment processing")
    add_file(repo_path, "features/invoices.py", 50, "carol", "Add invoice generation")

    # Create feature-notifications branch from develop
    run_git(repo_path, "checkout", "develop")
    run_git(repo_path, "checkout", "-b", "feature-notifications")

    # Feature branch: Dave adds notification system
    add_file(repo_path, "features/notifications.py", 70, "dave", "Add notification service")
    add_file(repo_path, "features/templates.py", 45, "dave", "Add email templates")

    # Merge feature-notifications back to develop
    run_git(repo_path, "checkout", "develop")
    run_git(repo_path, "merge", "feature-notifications", "--no-ff", "-m", "Merge feature-notifications")

    # Merge feature-payments back to develop
    run_git(repo_path, "merge", "feature-payments", "--no-ff", "-m", "Merge feature-payments")

    # Alice adds more to develop
    add_file(repo_path, "utils/helpers.py", 55, "alice", "Add utility helpers")

    # Merge develop to main
    run_git(repo_path, "checkout", "master")
    run_git(repo_path, "merge", "develop", "--no-ff", "-m", "Merge develop into main")

    # Create release branch
    run_git(repo_path, "checkout", "-b", "release-1.0")
    add_file(repo_path, "version.py", 10, "alice", "Bump version to 1.0")

    # Back to main for final state
    run_git(repo_path, "checkout", "master")

    print("  Created: 10 files, 4 authors, ~570 LOC, 5 branches")


def main():
    """Build all synthetic repositories."""
    base_path = Path(__file__).parent.parent / "eval-repos" / "synthetic"

    print("=" * 60)
    print("Building Synthetic Test Repositories")
    print("=" * 60)

    build_single_author(base_path)
    build_multi_author(base_path)
    build_bus_factor_1(base_path)
    build_balanced(base_path)
    build_multi_branch(base_path)

    print("=" * 60)
    print("All synthetic repositories created!")
    print("=" * 60)


if __name__ == "__main__":
    main()
