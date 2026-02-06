#!/usr/bin/env python3
"""Run git-fame analysis on repositories.

Produces authorship attribution metrics including:
- Per-author LOC ownership
- Bus factor calculation
- HHI (Herfindahl-Hirschman Index) for concentration
- Per-file attribution breakdown

Output follows Caldera envelope format with metadata/data sections.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import gitfame
except Exception:  # pragma: no cover - environment dependent
    gitfame = None


# Schema version for this output format
SCHEMA_VERSION = "1.0.0"


def run_git_fame(
    repo_path: Path,
    by_extension: bool = False,
    since: str | None = None,
    until: str | None = None,
    loc_mode: str = "surviving",
) -> dict[str, Any]:
    """Run git-fame and return parsed JSON output.

    Args:
        repo_path: Path to the git repository
        by_extension: Show stats per file extension
        since: Date from which to check (e.g., 2020-01-01 or 3.months)
        until: Date up to which to check
        loc_mode: LOC counting mode - "surviving" (default), "ins", or "del"
    """
    cmd = [
        sys.executable, "-m", "gitfame",
        "--format", "json",
        "--branch", "HEAD",  # Use current HEAD
        "--loc", loc_mode,
    ]

    if by_extension:
        cmd.append("--bytype")
    if since:
        cmd.extend(["--since", since])
    if until:
        cmd.extend(["--until", until])

    result = subprocess.run(
        cmd,
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"git-fame error: {result.stderr}")
        return {}

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Output: {result.stdout[:500]}")
        return {}


def extract_author_metric(raw_output: dict[str, Any], metric_col: str = "loc") -> dict[str, int]:
    """Extract author name → metric value mapping from git-fame output.

    Args:
        raw_output: Raw git-fame JSON output
        metric_col: Column name to extract (default "loc")

    Returns:
        Dict mapping author name to metric value
    """
    data_rows = raw_output.get("data", [])
    columns = raw_output.get("columns", [])
    col_idx = {col: i for i, col in enumerate(columns)}

    result = {}
    for row in data_rows:
        author = row[col_idx.get("Author", 0)]
        value = row[col_idx.get(metric_col, col_idx.get("loc", 1))]
        result[author] = int(value) if isinstance(value, (int, float)) else 0
    return result


def compute_hhi(ownership_pcts: list[float]) -> float:
    """Compute Herfindahl-Hirschman Index for ownership concentration.

    HHI = sum of squared ownership percentages (as decimals)
    Range: 1/n (perfect equality) to 1.0 (monopoly)

    Args:
        ownership_pcts: List of ownership percentages (0-100)

    Returns:
        HHI value between 0 and 1
    """
    if not ownership_pcts:
        return 0.0
    # Convert percentages to decimals and square them
    decimals = [p / 100.0 for p in ownership_pcts]
    return sum(d * d for d in decimals)


def compute_bus_factor(ownership_pcts: list[float], threshold: float = 50.0) -> int:
    """Compute bus factor - minimum authors needed for threshold% coverage.

    Args:
        ownership_pcts: List of ownership percentages, sorted descending
        threshold: Coverage threshold (default 50%)

    Returns:
        Number of authors needed to cover threshold%
    """
    if not ownership_pcts:
        return 0

    sorted_pcts = sorted(ownership_pcts, reverse=True)
    cumulative = 0.0
    for i, pct in enumerate(sorted_pcts, 1):
        cumulative += pct
        if cumulative >= threshold:
            return i
    return len(sorted_pcts)


def get_git_info(repo_path: Path) -> tuple[str, str]:
    """Get git branch and commit from repository.

    Args:
        repo_path: Path to the git repository

    Returns:
        Tuple of (branch, commit_sha)
    """
    try:
        # Get current branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

        # Get current commit
        commit_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        commit = commit_result.stdout.strip() if commit_result.returncode == 0 else fallback_commit_hash(repo_path)

        return branch, commit
    except Exception:
        return "unknown", fallback_commit_hash(repo_path)


def fallback_commit_hash(repo_path: Path) -> str:
    """Compute a deterministic content hash for non-git repos.

    Args:
        repo_path: Path to repository

    Returns:
        40-character SHA1 hash based on file contents
    """
    sha1 = hashlib.sha1()
    for path in sorted(repo_path.rglob("*")):
        if path.is_file() and ".git" not in path.parts:
            sha1.update(path.relative_to(repo_path).as_posix().encode())
            sha1.update(b"\0")
            try:
                sha1.update(path.read_bytes())
            except OSError:
                continue
    return sha1.hexdigest()


def transform_output(
    raw_output: dict[str, Any],
    insertions_map: dict[str, int],
    deletions_map: dict[str, int],
    repo_path: Path,
    run_id: str,
    repo_id: str,
    branch: str,
    commit: str,
) -> dict[str, Any]:
    """Transform git-fame output to Caldera envelope format.

    Args:
        raw_output: Raw git-fame JSON output (from surviving LOC run)
        insertions_map: Author name → total insertions mapping
        deletions_map: Author name → total deletions mapping
        repo_path: Path to the repository
        run_id: Unique run identifier
        repo_id: Repository identifier
        branch: Git branch name
        commit: 40-character git SHA

    Returns:
        Dict in Caldera envelope format with metadata and data sections
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    repo_name = repo_path.name
    tool_version = getattr(gitfame, "__version__", "3.1.1") if gitfame else "3.1.1"

    # Parse git-fame output
    # git-fame returns: {"data": [[author, loc, ins, del, commits, files, months], ...], "columns": [...]}
    data_rows = raw_output.get("data", [])
    columns = raw_output.get("columns", [])

    # Build metadata section (required by Caldera envelope)
    metadata = {
        "tool_name": "git-fame",
        "tool_version": tool_version,
        "run_id": run_id,
        "repo_id": repo_id,
        "branch": branch,
        "commit": commit,
        "timestamp": timestamp,
        "schema_version": SCHEMA_VERSION,
    }

    if not data_rows:
        return {
            "metadata": metadata,
            "data": {
                "tool": "git-fame",
                "tool_version": tool_version,
                "repo_name": repo_name,
                "error": "No data returned from git-fame",
                "provenance": {
                    "tool": "git-fame",
                    "commands": [
                        "git-fame --format json --branch HEAD --loc surviving",
                        "git-fame --format json --branch HEAD --loc ins",
                        "git-fame --format json --branch HEAD --loc del",
                    ],
                },
                "summary": {
                    "author_count": 0,
                    "total_loc": 0,
                    "hhi_index": 0.0,
                    "bus_factor": 0,
                    "top_author_pct": 0.0,
                    "top_two_pct": 0.0,
                },
                "authors": [],
            },
        }

    # Map columns to indices
    col_idx = {col: i for i, col in enumerate(columns)}

    # Extract author metrics
    authors = []
    total_loc = 0

    for row in data_rows:
        author_name = row[col_idx.get("Author", 0)]
        # git-fame uses lowercase column names: "loc", "coms", "fils"
        # Also support uppercase for compatibility: "LOC", "Commits", "Files"
        loc = row[col_idx.get("loc", col_idx.get("LOC", 1))] if len(row) > 1 else 0
        # Commits: git-fame uses "coms" for commit count
        commits = row[col_idx.get("coms", col_idx.get("Commits", 2))] if len(row) > 2 else 0
        # Files: git-fame uses "fils" for file count
        files = row[col_idx.get("fils", col_idx.get("Files", 3))] if len(row) > 3 else 0

        # Ensure commits and files are integers (git-fame returns integers, not floats)
        commits = int(commits) if isinstance(commits, (int, float)) else 0
        files = int(files) if isinstance(files, (int, float)) else 0

        total_loc += loc
        authors.append({
            "name": author_name,
            "surviving_loc": loc,
            "insertions_total": insertions_map.get(author_name, 0),
            "deletions_total": deletions_map.get(author_name, 0),
            "commit_count": commits,
            "files_touched": files,
        })

    # Compute ownership percentages
    for author in authors:
        if total_loc > 0:
            author["ownership_pct"] = round(author["surviving_loc"] / total_loc * 100, 2)
        else:
            author["ownership_pct"] = 0.0

    # Sort by ownership descending
    authors.sort(key=lambda a: a["ownership_pct"], reverse=True)

    # Compute concentration metrics
    ownership_pcts = [a["ownership_pct"] for a in authors]
    hhi = compute_hhi(ownership_pcts)
    bus_factor = compute_bus_factor(ownership_pcts)

    return {
        "metadata": metadata,
        "data": {
            "tool": "git-fame",
            "tool_version": tool_version,
            "repo_name": repo_name,
            "provenance": {
                "tool": "git-fame",
                "commands": [
                    "git-fame --format json --branch HEAD --loc surviving",
                    "git-fame --format json --branch HEAD --loc ins",
                    "git-fame --format json --branch HEAD --loc del",
                ],
            },
            "summary": {
                "author_count": len(authors),
                "total_loc": total_loc,
                "hhi_index": round(hhi, 4),
                "bus_factor": bus_factor,
                "top_author_pct": authors[0]["ownership_pct"] if authors else 0.0,
                "top_two_pct": sum(a["ownership_pct"] for a in authors[:2]) if len(authors) >= 2 else (authors[0]["ownership_pct"] if authors else 0.0),
            },
            "authors": authors,
        },
    }


def analyze_repo(
    repo_path: Path,
    output_path: Path,
    by_extension: bool = False,
    since: str | None = None,
    until: str | None = None,
    run_id: str | None = None,
    repo_id: str | None = None,
) -> dict[str, Any]:
    """Analyze a single repository.

    Args:
        repo_path: Path to repository
        output_path: Output file path (.json) or directory
        by_extension: Show stats per file extension
        since: Date from which to check
        until: Date up to which to check
        run_id: Optional run ID (from orchestrator)
        repo_id: Optional repo ID (from orchestrator)
    """
    repo_name = repo_path.name

    # Get git info from repo
    branch, commit = get_git_info(repo_path)

    # Use provided IDs or generate new ones
    if not run_id:
        run_id = os.environ.get("RUN_ID", str(uuid.uuid4()))
    if not repo_id:
        repo_id = os.environ.get("REPO_ID", str(uuid.uuid4()))

    print(f"Analyzing {repo_path}...")

    # Run 1: Default (surviving LOC, commits, files)
    raw_output = run_git_fame(repo_path, by_extension, since, until, loc_mode="surviving")

    if not raw_output:
        print("  No output from git-fame")
        return {}

    # Run 2: Insertions
    ins_output = run_git_fame(repo_path, by_extension, since, until, loc_mode="ins")
    insertions_map = extract_author_metric(ins_output)

    # Run 3: Deletions
    del_output = run_git_fame(repo_path, by_extension, since, until, loc_mode="del")
    deletions_map = extract_author_metric(del_output)

    # Transform output to Caldera envelope format with all data
    analysis = transform_output(
        raw_output, insertions_map, deletions_map, repo_path, run_id, repo_id, branch, commit
    )

    # Check if output_path is a file (.json) or directory
    is_file_output = str(output_path).endswith('.json')

    if is_file_output:
        # Direct file output - just write the analysis JSON
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(analysis, indent=2))
        print(f"  Results: {output_path}")
    else:
        # Legacy directory output with run structure
        run_dir = output_path / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Save raw output
        raw_file = run_dir / "raw_git_fame.json"
        raw_file.write_text(json.dumps(raw_output, indent=2))

        # Save analysis
        analysis_file = run_dir / "analysis.json"
        analysis_file.write_text(json.dumps(analysis, indent=2))

        # Save run metadata file
        run_metadata = {
            "run_id": run_id,
            "timestamp": analysis["metadata"]["timestamp"],
            "repo_path": str(repo_path),
            "outputs": {
                "raw": "raw_git_fame.json",
                "analysis": "analysis.json",
            },
        }
        metadata_file = run_dir / "metadata.json"
        metadata_file.write_text(json.dumps(run_metadata, indent=2))

        # Update latest symlink
        latest_link = output_path / "latest"
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
        latest_link.symlink_to(f"runs/{run_id}")

        print(f"  Results: {run_dir}")

    # Print summary (use data section from Caldera envelope)
    data_section = analysis.get("data", {})
    summary = data_section.get("summary", {})
    print(f"  Authors: {summary.get('author_count', 0)}")
    print(f"  Total LOC: {summary.get('total_loc', 0)}")
    print(f"  Bus Factor: {summary.get('bus_factor', 0)}")
    print(f"  HHI Index: {summary.get('hhi_index', 0):.4f}")
    print(f"  Top Author: {summary.get('top_author_pct', 0):.1f}%")

    return analysis


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run git-fame authorship analysis")
    parser.add_argument("repo_path", type=Path, help="Path to repository or directory of repos")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output directory")
    parser.add_argument(
        "--by-extension",
        action="store_true",
        help="Show stats per file extension (uses git-fame --bytype)",
    )
    parser.add_argument(
        "--since",
        type=str,
        default=None,
        help="Date from which to check (e.g., 2020-01-01 or 3.months)",
    )
    parser.add_argument(
        "--until",
        type=str,
        default=None,
        help="Date up to which to check (e.g., 2023-12-31 or 1.week)",
    )
    args = parser.parse_args()

    # Determine output path - can be file (.json) or directory
    base_dir = Path(__file__).parent.parent
    output_path = args.output or base_dir / "output"

    # Check if output is a file path (.json) or directory
    is_file_output = str(output_path).endswith('.json')

    if is_file_output:
        # File output - create parent directory
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        # Directory output - create the directory
        output_path.mkdir(parents=True, exist_ok=True)

    repo_path = args.repo_path.resolve()

    print("=" * 60)
    print("git-fame Authorship Analysis")
    print("=" * 60)

    # Check if this is a single repo or directory of repos
    if (repo_path / ".git").exists():
        # Single repository
        analyze_repo(
            repo_path, output_path, args.by_extension, args.since, args.until
        )
    else:
        # Directory of repositories
        repos = [d for d in repo_path.iterdir() if d.is_dir() and (d / ".git").exists()]
        if not repos:
            print(f"No git repositories found in {repo_path}")
            return

        print(f"Found {len(repos)} repositories to analyze")
        print()

        all_results = {}
        for repo in sorted(repos):
            result = analyze_repo(
                repo, output_path, args.by_extension, args.since, args.until
            )
            if result:
                all_results[repo.name] = result
            print()

        # Save combined results
        if is_file_output:
            # If output_path is a file, put combined next to it
            combined_file = output_path.parent / "combined_analysis.json"
        else:
            combined_file = output_path / "combined_analysis.json"
        combined_file.write_text(json.dumps(all_results, indent=2))
        print(f"Combined results: {combined_file}")

    print("=" * 60)
    print("Analysis complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
