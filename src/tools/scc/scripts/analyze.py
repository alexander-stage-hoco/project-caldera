#!/usr/bin/env python3
"""CLI entry point for scc directory analysis.

Standard wrapper that translates orchestrator CLI args to directory_analyzer.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add scripts directory and shared src to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from directory_analyzer import (
    run_scc_by_file,
    analyze_directories,
    get_scc_version,
)
from common.path_normalization import normalize_file_path, normalize_dir_path


def _resolve_scc_path(path_arg: str | None) -> Path:
    """Resolve scc binary path."""
    if path_arg:
        return Path(path_arg)
    script_dir = Path(__file__).parent
    return script_dir.parent / "bin" / "scc"

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


def _normalize_result_paths(result: dict, repo_root: Path) -> None:
    """Normalize known path fields in the analysis result."""
    for file_entry in result.get("files", []):
        file_entry["path"] = normalize_file_path(file_entry.get("path", ""), repo_root)
        file_entry["directory"] = normalize_dir_path(
            file_entry.get("directory", ""), repo_root
        )
        if not file_entry.get("path"):
            file_entry["path"] = "unknown"

    for directory_entry in result.get("directories", []):
        directory_entry["path"] = normalize_dir_path(
            directory_entry.get("path", ""), repo_root
        )
        if not directory_entry.get("path"):
            directory_entry["path"] = "."


def to_standard_output(
    result: dict,
    repo_name: str,
    repo_path: str,
    run_id: str,
    repo_id: str,
    branch: str,
    commit: str,
    tool_version: str,
    timestamp: str,
) -> dict:
    """Convert analyze_directories result to envelope output format."""
    # Remove schema_version from result (will be in metadata)
    result.pop("schema_version", None)
    result.pop("timestamp", None)

    if "languages" not in result:
        by_language = result.get("summary", {}).get("by_language", {})
        result["languages"] = [
            {
                "name": lang,
                "files": stats.get("file_count", 0),
                "lines": stats.get("lines", 0),
                "code": stats.get("code", 0),
                "comment": stats.get("comment", 0),
                "blank": stats.get("blank", 0),
                "bytes": stats.get("bytes", 0),
                "complexity": stats.get("complexity_total", 0),
            }
            for lang, stats in by_language.items()
        ]

    # Add tool info to results
    result["tool"] = "scc"
    result["tool_version"] = tool_version

    return {
        "metadata": {
            "tool_name": "scc",
            "tool_version": tool_version,
            "run_id": run_id,
            "repo_id": repo_id,
            "branch": branch,
            "commit": commit,
            "timestamp": timestamp,
            "schema_version": "1.0.0",
        },
        "data": result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze directory structure using scc")
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
        help="Commit SHA (required)",
    )
    parser.add_argument(
        "--scc",
        help="Path to scc binary (default: ./bin/scc)",
    )
    parser.add_argument(
        "--cocomo-preset",
        default="sme",
        help="COCOMO preset for cost estimation (default: sme)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    args = parser.parse_args()

    repo_path = Path(args.repo_path)
    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {repo_path}", file=sys.stderr)
        sys.exit(1)

    repo_name = args.repo_name or repo_path.resolve().name
    scc_path = _resolve_scc_path(args.scc)
    if not scc_path.exists():
        print(f"Error: scc binary not found at {scc_path}", file=sys.stderr)
        print("Run 'make setup' to install scc", file=sys.stderr)
        sys.exit(1)

    if not args.run_id:
        print("Error: --run-id is required", file=sys.stderr)
        sys.exit(1)
    if not args.repo_id:
        print("Error: --repo-id is required", file=sys.stderr)
        sys.exit(1)
    try:
        commit = _resolve_commit(repo_path.resolve(), args.commit, Path(__file__).parent.parent)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else Path("outputs") / args.run_id
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "output.json"

    print(f"Analyzing: {repo_path}")
    print(f"Using scc: {scc_path}")

    # Run scc analysis
    files, raw_scc_data = run_scc_by_file(scc_path, str(repo_path))
    print(f"Files found: {len(files)}")

    # Analyze directory structure
    result = analyze_directories(files, args.cocomo_preset)
    _normalize_result_paths(result, repo_path.resolve())

    # Convert to standard output format
    timestamp = datetime.now(timezone.utc).isoformat()
    tool_version = get_scc_version(scc_path)
    output_dict = to_standard_output(
        result,
        repo_name,
        str(repo_path.resolve()),
        args.run_id,
        args.repo_id,
        args.branch,
        commit,
        tool_version,
        timestamp,
    )

    # Write output
    output_path.write_text(json.dumps(output_dict, indent=2, default=str))

    summary = output_dict["data"].get("summary", {})
    print(f"Total files: {summary.get('total_files', 0)}")
    print(f"Total lines: {summary.get('total_lines', 0):,}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
