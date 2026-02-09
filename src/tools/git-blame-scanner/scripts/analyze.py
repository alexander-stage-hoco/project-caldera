"""Main analysis script for git-blame-scanner.

Provides per-file authorship metrics to complement git-fame's per-author metrics.
This enables knowledge concentration and bus factor analysis at the file level.

Key metrics per file:
- unique_authors: Number of distinct contributors
- top_author_pct: Ownership concentration by top contributor
- churn_30d/churn_90d: Recent activity (commits in last 30/90 days)
- last_modified: Date of most recent change

Key metrics per author:
- exclusive_files: Files where author is sole contributor
- total_files: Total files touched by author
- avg_ownership_pct: Average ownership across files
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

# Add shared src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

TOOL_NAME = "git-blame-scanner"
TOOL_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"


@dataclass
class FileBlameStats:
    """Per-file blame statistics."""
    relative_path: str
    total_lines: int
    unique_authors: int
    top_author: str
    top_author_lines: int
    top_author_pct: float
    last_modified: str  # YYYY-MM-DD
    churn_30d: int
    churn_90d: int
    authors: dict[str, int]  # author_email -> lines


@dataclass
class AuthorStats:
    """Per-author aggregate statistics."""
    author_email: str
    total_files: int
    total_lines: int
    exclusive_files: int
    avg_ownership_pct: float


def compute_content_hash(repo_path: Path) -> str:
    """Compute a deterministic hash for non-git repos."""
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


def resolve_commit(repo_path: Path, commit_arg: str | None) -> str:
    """Resolve commit SHA, falling back to content hash."""
    if commit_arg and len(commit_arg) == 40:
        return commit_arg
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return compute_content_hash(repo_path)


def get_tracked_files(repo_path: Path) -> list[str]:
    """Get list of files tracked by git."""
    result = subprocess.run(
        ["git", "-C", str(repo_path), "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [f for f in result.stdout.strip().split("\n") if f]


def get_file_blame_stats(repo_path: Path, relative_path: str) -> dict[str, int] | None:
    """Get per-author line counts for a file using git blame.

    Returns dict mapping author_email -> line_count, or None if file cannot be blamed.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "blame", "--line-porcelain", "--", relative_path],
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return None

    # Decode with errors='replace' to handle non-UTF8 content in blame output
    try:
        stdout = result.stdout.decode("utf-8", errors="replace")
    except Exception:
        return None

    author_lines: dict[str, int] = defaultdict(int)
    current_author = None

    for line in stdout.split("\n"):
        if line.startswith("author-mail "):
            # Extract email, removing < and >
            email = line[12:].strip().strip("<>")
            current_author = email
        elif line.startswith("\t"):
            # This is a content line - count it for current author
            if current_author:
                author_lines[current_author] += 1

    return dict(author_lines) if author_lines else None


def get_file_last_modified(repo_path: Path, relative_path: str) -> str | None:
    """Get the last modified date for a file."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "log", "-1", "--format=%cs", "--", relative_path],
            capture_output=True,
            text=True,
            check=True,
        )
        date_str = result.stdout.strip()
        return date_str if date_str else None
    except subprocess.CalledProcessError:
        return None


def get_commit_activity(repo_path: Path, days: int) -> dict[str, int]:
    """Get commit counts per file in the last N days.

    Returns dict mapping relative_path -> commit_count.
    """
    since_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "log", "--name-only", "--format=", f"--since={since_date}"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return {}

    file_commits: dict[str, int] = defaultdict(int)
    for line in result.stdout.strip().split("\n"):
        line = line.strip()
        if line:
            file_commits[line] += 1

    return dict(file_commits)


def analyze_file(
    repo_path: Path,
    relative_path: str,
    churn_30d_map: dict[str, int],
    churn_90d_map: dict[str, int],
) -> FileBlameStats | None:
    """Analyze a single file for authorship metrics."""
    # Get blame data
    author_lines = get_file_blame_stats(repo_path, relative_path)
    if not author_lines:
        return None

    total_lines = sum(author_lines.values())
    if total_lines == 0:
        return None

    # Find top author
    top_author = max(author_lines, key=author_lines.get)
    top_author_lines = author_lines[top_author]
    top_author_pct = round((top_author_lines / total_lines) * 100, 2)

    # Get last modified date
    last_modified = get_file_last_modified(repo_path, relative_path)

    return FileBlameStats(
        relative_path=relative_path,
        total_lines=total_lines,
        unique_authors=len(author_lines),
        top_author=top_author,
        top_author_lines=top_author_lines,
        top_author_pct=top_author_pct,
        last_modified=last_modified or "unknown",
        churn_30d=churn_30d_map.get(relative_path, 0),
        churn_90d=churn_90d_map.get(relative_path, 0),
        authors=author_lines,
    )


def compute_author_stats(file_stats: list[FileBlameStats]) -> list[AuthorStats]:
    """Compute per-author aggregate statistics from file data."""
    author_data: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"files": 0, "lines": 0, "exclusive": 0, "ownership_pcts": []}
    )

    for fs in file_stats:
        for email, lines in fs.authors.items():
            data = author_data[email]
            data["files"] += 1
            data["lines"] += lines

            # Calculate this author's ownership percentage for this file
            ownership_pct = (lines / fs.total_lines) * 100 if fs.total_lines > 0 else 0
            data["ownership_pcts"].append(ownership_pct)

            # Is this author the sole contributor?
            if fs.unique_authors == 1:
                data["exclusive"] += 1

    return [
        AuthorStats(
            author_email=email,
            total_files=data["files"],
            total_lines=data["lines"],
            exclusive_files=data["exclusive"],
            avg_ownership_pct=round(
                sum(data["ownership_pcts"]) / len(data["ownership_pcts"]), 2
            ) if data["ownership_pcts"] else 0,
        )
        for email, data in author_data.items()
    ]


def analyze_repo(repo_path: Path) -> dict:
    """Run git-blame-scanner analysis on the repository.

    Returns the data section of the Caldera envelope.
    """
    print(f"Getting tracked files...")
    files = get_tracked_files(repo_path)
    print(f"Found {len(files)} tracked files")

    # Get commit activity for churn metrics
    print(f"Calculating 30-day churn...")
    churn_30d_map = get_commit_activity(repo_path, 30)
    print(f"Calculating 90-day churn...")
    churn_90d_map = get_commit_activity(repo_path, 90)

    # Analyze each file
    file_stats: list[FileBlameStats] = []
    print(f"Analyzing files with git blame...")

    for i, relative_path in enumerate(files):
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(files)} files...")

        stats = analyze_file(repo_path, relative_path, churn_30d_map, churn_90d_map)
        if stats:
            file_stats.append(stats)

    print(f"Successfully analyzed {len(file_stats)} files")

    # Compute author aggregates
    author_stats = compute_author_stats(file_stats)

    # Compute summary metrics
    single_author_files = sum(1 for fs in file_stats if fs.unique_authors == 1)
    high_concentration_files = sum(1 for fs in file_stats if fs.top_author_pct >= 80)
    stale_files = sum(
        1 for fs in file_stats
        if fs.churn_90d == 0 and fs.last_modified != "unknown"
    )

    # Find knowledge silos (files with single author that are critical)
    # For now, define "critical" as files > 100 lines
    knowledge_silos = [
        fs.relative_path for fs in file_stats
        if fs.unique_authors == 1 and fs.total_lines > 100
    ]

    return {
        "tool": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "files": [
            {
                "path": fs.relative_path,
                "total_lines": fs.total_lines,
                "unique_authors": fs.unique_authors,
                "top_author": fs.top_author,
                "top_author_lines": fs.top_author_lines,
                "top_author_pct": fs.top_author_pct,
                "last_modified": fs.last_modified,
                "churn_30d": fs.churn_30d,
                "churn_90d": fs.churn_90d,
            }
            for fs in file_stats
        ],
        "authors": [
            {
                "author_email": a.author_email,
                "total_files": a.total_files,
                "total_lines": a.total_lines,
                "exclusive_files": a.exclusive_files,
                "avg_ownership_pct": a.avg_ownership_pct,
            }
            for a in sorted(author_stats, key=lambda x: x.total_lines, reverse=True)
        ],
        "summary": {
            "total_files_analyzed": len(file_stats),
            "total_authors": len(author_stats),
            "single_author_files": single_author_files,
            "single_author_pct": round(
                (single_author_files / len(file_stats)) * 100, 2
            ) if file_stats else 0,
            "high_concentration_files": high_concentration_files,
            "high_concentration_pct": round(
                (high_concentration_files / len(file_stats)) * 100, 2
            ) if file_stats else 0,
            "stale_files_90d": stale_files,
            "knowledge_silo_count": len(knowledge_silos),
            "avg_authors_per_file": round(
                sum(fs.unique_authors for fs in file_stats) / len(file_stats), 2
            ) if file_stats else 0,
        },
        "knowledge_silos": knowledge_silos[:20],  # Top 20 silos
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=f"{TOOL_NAME} analysis tool")
    parser.add_argument("--repo-path", required=True, type=Path)
    parser.add_argument("--repo-name", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--commit", default=None)
    args = parser.parse_args()

    repo_path = args.repo_path.resolve()
    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {repo_path}", file=sys.stderr)
        return 1

    # Check if this is a git repository
    if not (repo_path / ".git").exists():
        print(f"Error: Not a git repository: {repo_path}", file=sys.stderr)
        return 1

    # Resolve commit
    commit = resolve_commit(repo_path, args.commit)

    print("=" * 60)
    print(f"{TOOL_NAME} - Per-file Authorship Analysis")
    print("=" * 60)
    print(f"Repository: {repo_path}")
    print(f"Commit: {commit[:12]}...")
    print()

    # Run analysis
    data = analyze_repo(repo_path)

    # Create envelope
    envelope = {
        "metadata": {
            "tool_name": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "run_id": args.run_id,
            "repo_id": args.repo_id,
            "branch": args.branch,
            "commit": commit,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "schema_version": SCHEMA_VERSION,
        },
        "data": data,
    }

    # Write output
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "output.json"
    output_path.write_text(json.dumps(envelope, indent=2))

    # Print summary
    summary = data["summary"]
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Files analyzed: {summary['total_files_analyzed']}")
    print(f"Authors: {summary['total_authors']}")
    print(f"Single-author files: {summary['single_author_files']} ({summary['single_author_pct']}%)")
    print(f"High concentration (>80%): {summary['high_concentration_files']} ({summary['high_concentration_pct']}%)")
    print(f"Knowledge silos (>100 LOC, single author): {summary['knowledge_silo_count']}")
    print(f"Stale files (no commits in 90d): {summary['stale_files_90d']}")
    print()
    print(f"Analysis complete. Output: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
