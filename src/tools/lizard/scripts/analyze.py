#!/usr/bin/env python3
"""CLI entry point for lizard function complexity analysis."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import sys
from function_analyzer import (
    analyze_directory,
    result_to_output,
    set_color_enabled,
    get_lizard_version,
)
# Add shared src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from common.path_normalization import normalize_file_path, normalize_dir_path


def _git_run(repo_path: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a git command in the target repository."""
    return subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True,
        text=True,
    )


def _git_head(repo_path: Path) -> str | None:
    """Return HEAD commit for repo_path if available."""
    result = _git_run(repo_path, ["rev-parse", "HEAD"])
    return result.stdout.strip() if result.returncode == 0 else None


def _commit_exists(repo_path: Path, commit: str) -> bool:
    """Check whether a commit exists in the given repo."""
    result = _git_run(repo_path, ["cat-file", "-e", f"{commit}^{{commit}}"])
    return result.returncode == 0


def _fallback_commit_hash(repo_path: Path) -> str:
    """Return the standard fallback commit hash for non-git repositories."""
    return "0" * 40


def _resolve_commit(repo_path: Path, commit_arg: str, fallback_repo: Path | None) -> str:
    """Resolve a valid commit SHA for the target repo."""
    if commit_arg:
        if _commit_exists(repo_path, commit_arg):
            return commit_arg
        if fallback_repo and _commit_exists(fallback_repo, commit_arg):
            return commit_arg
        raise ValueError(f"Commit not found in repo: {commit_arg}")

    head = _git_head(repo_path)
    if head:
        return head
    if fallback_repo:
        head = _git_head(fallback_repo)
        if head:
            return head
    return _fallback_commit_hash(repo_path if repo_path.exists() else fallback_repo or repo_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze function complexity using lizard"
    )
    parser.add_argument(
        "--repo-path",
        default=os.environ.get("REPO_PATH", "eval-repos/synthetic"),
        help="Path to repository to analyze",
    )
    parser.add_argument(
        "--repo-name",
        default=os.environ.get("REPO_NAME", ""),
        help="Repository name for output naming",
    )
    parser.add_argument(
        "--output-dir",
        default=os.environ.get("OUTPUT_DIR"),
        help="Directory to write analysis output (default: outputs/<run-id>)",
    )
    parser.add_argument(
        "--run-id",
        default=os.environ.get("RUN_ID", ""),
        help="Run identifier (required)",
    )
    parser.add_argument(
        "--repo-id",
        default=os.environ.get("REPO_ID", ""),
        help="Repository identifier (required)",
    )
    parser.add_argument(
        "--branch",
        default=os.environ.get("BRANCH", "main"),
        help="Branch analyzed",
    )
    parser.add_argument(
        "--commit",
        default=os.environ.get("COMMIT", ""),
        help="Commit SHA (default: repo HEAD)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "-t", "--threads",
        type=int,
        default=None,
        help="Number of threads (default: CPU count)",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test directories (excluded by default)",
    )
    parser.add_argument(
        "-l", "--languages",
        nargs="+",
        help="Only analyze specific languages (e.g., 'C#' 'Python')",
    )
    parser.add_argument(
        "--max-file-size",
        type=int,
        default=500,
        help="Skip files larger than N KB (default: 500)",
    )
    args = parser.parse_args()

    if args.no_color:
        set_color_enabled(False)

    repo_path = Path(args.repo_path)
    if not repo_path.exists():
        raise FileNotFoundError(f"Repository not found at {repo_path}")

    repo_name = args.repo_name or repo_path.resolve().name
    print(f"Lizard version: {get_lizard_version()}")
    print()

    if not args.run_id:
        raise ValueError("--run-id is required")
    if not args.repo_id:
        raise ValueError("--repo-id is required")
    try:
        commit = _resolve_commit(repo_path.resolve(), args.commit, Path(__file__).parent.parent)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc

    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else Path("outputs") / args.run_id
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "output.json"

    # Set REPO_NAME env var so analyze_directory can use it
    os.environ["REPO_NAME"] = repo_name

    print(f"Analyzing {repo_name}...")
    result = analyze_directory(
        target_path=str(repo_path),
        threads=args.threads,
        exclude_tests=not args.include_tests,
        languages=args.languages,
        max_file_size_kb=args.max_file_size,
    )

    # Override repo_name/repo_path from CLI if provided
    result.repo_name = repo_name
    result.repo_path = str(repo_path.resolve())
    result.repo_id = args.repo_id
    result.branch = args.branch
    result.commit = commit
    timestamp = datetime.now(timezone.utc).isoformat()
    result.generated_at = timestamp
    result.timestamp = timestamp
    result.run_id = args.run_id

    repo_root = repo_path.resolve()
    for file_entry in result.files:
        file_entry.path = normalize_file_path(file_entry.path, repo_root)

    for directory_entry in result.directories:
        directory_entry.path = normalize_dir_path(directory_entry.path, repo_root)

    result.root_path = "."
    output_path.write_text(json.dumps(result_to_output(result), indent=2, default=str))

    summary = result.summary
    print()
    print(f"Files analyzed: {summary.total_files if summary else 0}")
    print(f"Functions found: {summary.total_functions if summary else 0}")
    print(f"Total CCN: {summary.total_ccn if summary else 0}")
    print(f"Avg CCN: {summary.avg_ccn:.2f}" if summary else "Avg CCN: 0.00")
    print(f"Max CCN: {summary.max_ccn if summary else 0}")
    print(f"Functions over threshold: {summary.functions_over_threshold if summary else 0}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
