#!/usr/bin/env python3
"""CLI entry point for scancode license analysis.

Standard wrapper that translates orchestrator CLI args to license_analyzer.
Produces Caldera envelope format output.
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

from license_analyzer import analyze_repository, LicenseAnalysis
from common.path_normalization import normalize_file_path, normalize_dir_path


TOOL_VERSION = "1.0.0"


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


def _normalize_analysis_paths(analysis: LicenseAnalysis, repo_root: Path) -> None:
    """Normalize all file paths in the analysis to be repo-relative."""
    # Normalize findings
    for finding in analysis.findings:
        finding.file_path = normalize_file_path(finding.file_path, repo_root)

    # Normalize file summaries - need to rebuild the dict with normalized keys
    normalized_files = {}
    for file_path, summary in analysis.files.items():
        normalized_path = normalize_file_path(file_path, repo_root)
        summary.file_path = normalized_path
        normalized_files[normalized_path] = summary
    analysis.files.clear()
    analysis.files.update(normalized_files)

    # Normalize directory paths
    for directory in analysis.directories:
        directory.path = normalize_dir_path(directory.path, repo_root)


def to_envelope_output(
    analysis: LicenseAnalysis,
    repo_name: str,
    repo_path: str,
    run_id: str,
    repo_id: str,
    branch: str,
    commit: str,
    timestamp: str,
) -> dict:
    """Convert analysis to Caldera envelope output format."""
    # Get the raw analysis dict
    raw_dict = analysis.to_dict()

    # Extract data from the old format - the results object becomes data
    data = raw_dict.get("results", {})

    # Build envelope format
    return {
        "metadata": {
            "tool_name": "scancode",
            "tool_version": TOOL_VERSION,
            "run_id": run_id,
            "repo_id": repo_id,
            "repo_name": repo_name,
            "repo_path": repo_path,
            "branch": branch,
            "commit": commit,
            "timestamp": timestamp,
            "schema_version": "1.0.0",
        },
        "data": data,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze repositories for licenses"
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
        help="Commit SHA",
    )
    args = parser.parse_args()

    repo_path = Path(args.repo_path).resolve()
    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {repo_path}", file=sys.stderr)
        sys.exit(1)

    repo_name = args.repo_name or repo_path.name

    if not args.run_id:
        print("Error: --run-id is required", file=sys.stderr)
        sys.exit(1)
    if not args.repo_id:
        print("Error: --repo-id is required", file=sys.stderr)
        sys.exit(1)

    try:
        commit = _resolve_commit(repo_path, args.commit, Path(__file__).parent.parent)
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

    # Run analysis
    analysis = analyze_repository(repo_path)

    # Normalize paths
    _normalize_analysis_paths(analysis, repo_path)

    # Convert to envelope format
    timestamp = datetime.now(timezone.utc).isoformat()
    output_dict = to_envelope_output(
        analysis,
        repo_name,
        str(repo_path),
        args.run_id,
        args.repo_id,
        args.branch,
        commit,
        timestamp,
    )

    print(f"Licenses found: {analysis.licenses_found or ['none']}")
    print(f"Overall risk: {analysis.overall_risk}")
    print(f"Files with licenses: {analysis.files_with_licenses}")

    # Write output
    output_path.write_text(json.dumps(output_dict, indent=2, default=str))
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
