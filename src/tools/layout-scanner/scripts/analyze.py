#!/usr/bin/env python3
"""CLI entry point for layout scanner analysis.

Standard wrapper that translates orchestrator CLI args to layout_scanner
and produces Caldera envelope output format.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .layout_scanner import load_config, scan_repository
from .output_writer import TOOL_VERSION, SCHEMA_VERSION


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


def _resolve_commit(repo_path: Path, commit_arg: str | None) -> str:
    """Resolve a valid commit SHA for the target repo."""
    if commit_arg:
        if _commit_exists(repo_path, commit_arg):
            return commit_arg
        # Commit specified but not found - use it anyway (orchestrator may have validated)
        return commit_arg

    head = _git_head(repo_path)
    if head:
        return head
    return _fallback_commit_hash(repo_path)


def to_envelope_format(
    scan_result: dict[str, Any],
    run_id: str,
    repo_id: str,
    branch: str,
    commit: str,
    timestamp: str,
) -> dict[str, Any]:
    """Convert layout_scanner result to Caldera envelope output format."""
    # The scan_result already has most fields we need in the data section
    # We just need to wrap it in the envelope format

    return {
        "metadata": {
            "tool_name": "layout-scanner",
            "tool_version": TOOL_VERSION,
            "run_id": run_id,
            "repo_id": repo_id,
            "branch": branch,
            "commit": commit,
            "timestamp": timestamp,
            "schema_version": SCHEMA_VERSION,
        },
        "data": scan_result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze repository layout using layout-scanner")
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
        help="Commit SHA (auto-detected if not provided)",
    )
    parser.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Ignore .gitignore rules",
    )
    parser.add_argument(
        "--git",
        action="store_true",
        help="Enable git metadata enrichment",
    )
    parser.add_argument(
        "--content",
        action="store_true",
        help="Enable content metadata enrichment",
    )
    args = parser.parse_args()

    repo_path = Path(args.repo_path)
    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {repo_path}", file=sys.stderr)
        sys.exit(1)

    repo_name = args.repo_name or repo_path.resolve().name

    if not args.run_id:
        print("Error: --run-id is required", file=sys.stderr)
        sys.exit(1)
    if not args.repo_id:
        print("Error: --repo-id is required", file=sys.stderr)
        sys.exit(1)

    commit = _resolve_commit(repo_path.resolve(), args.commit or None)

    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else Path("outputs") / args.run_id
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "output.json"

    print(f"Analyzing: {repo_path}")

    # Run layout scanner analysis
    config = load_config(repo_path)
    if args.no_gitignore:
        config.ignore.respect_gitignore = False

    scan_result, scan_duration_ms = scan_repository(
        repo_path,
        config=config,
        enable_git=args.git,
        enable_content=args.content,
    )
    scan_result["repository_path"] = repo_name
    scan_result["schema_version"] = SCHEMA_VERSION

    print(f"Files found: {scan_result.get('statistics', {}).get('total_files', 0)}")
    print(f"Directories: {scan_result.get('statistics', {}).get('total_directories', 0)}")
    print(f"Scan duration: {scan_duration_ms}ms")

    # Convert to envelope format
    timestamp = datetime.now(timezone.utc).isoformat()
    output_dict = to_envelope_format(
        scan_result,
        args.run_id,
        args.repo_id,
        args.branch,
        commit,
        timestamp,
    )

    # Write output
    output_path.write_text(json.dumps(output_dict, indent=2, ensure_ascii=False))

    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
