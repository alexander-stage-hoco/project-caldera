#!/usr/bin/env python3
"""
git-sizer repository health analyzer for Caldera.

Analyzes Git repositories for size, health, and scaling issues.
Outputs Caldera-compliant envelope format with structured metrics.

Usage:
    python -m scripts.analyze \
        --repo-path /path/to/repo \
        --repo-name my-repo \
        --output-dir output \
        --run-id <uuid> \
        --repo-id <uuid> \
        --branch main \
        --commit <sha>
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .binary_manager import ensure_binary, get_version as get_binary_version_raw
import re


def get_binary_version() -> str:
    """Get the git-sizer version, extracting just the semver."""
    raw_version = get_binary_version_raw()
    # Extract semver from strings like "git-sizer release 1.5.0"
    match = re.search(r"(\d+\.\d+\.\d+)", raw_version)
    if match:
        return match.group(1)
    return raw_version  # Fallback to raw if no match


# =============================================================================
# Constants
# =============================================================================

SCHEMA_VERSION = "1.0.0"
TOOL_NAME = "git-sizer"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ThresholdViolation:
    """A threshold violation detected by git-sizer."""
    metric: str
    value: str
    raw_value: int
    level: int  # Number of stars (1-4)
    object_ref: str = ""

    def to_dict(self) -> dict:
        result = {
            "metric": self.metric,
            "level": self.level,
        }
        if self.value:
            result["value"] = self.value
        if self.raw_value:
            result["raw_value"] = self.raw_value
        if self.object_ref:
            result["object_ref"] = self.object_ref
        return result


@dataclass
class RepositoryMetrics:
    """Metrics from git-sizer analysis."""
    # Commits
    commit_count: int = 0
    commit_total_size: int = 0
    max_commit_size: int = 0
    max_history_depth: int = 0
    max_parent_count: int = 0

    # Trees
    tree_count: int = 0
    tree_total_size: int = 0
    tree_total_entries: int = 0
    max_tree_entries: int = 0

    # Blobs
    blob_count: int = 0
    blob_total_size: int = 0
    max_blob_size: int = 0

    # Tags
    tag_count: int = 0
    max_tag_depth: int = 0

    # References
    reference_count: int = 0
    branch_count: int = 0

    # Paths
    max_path_depth: int = 0
    max_path_length: int = 0

    # Expanded (checkout)
    expanded_tree_count: int = 0
    expanded_blob_count: int = 0
    expanded_blob_size: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RepositoryAnalysis:
    """Complete repository analysis result."""
    git_sizer_version: str
    duration_ms: int
    metrics: RepositoryMetrics
    violations: list[ThresholdViolation] = field(default_factory=list)
    health_grade: str = "A"
    lfs_candidates: list[str] = field(default_factory=list)
    raw_output: dict = field(default_factory=dict)


# =============================================================================
# Git-Sizer Runner
# =============================================================================

def run_git_sizer(repo_path: Path) -> tuple[dict, int]:
    """Run git-sizer on a repository.

    Returns:
        Tuple of (JSON output dict, duration in ms)
    """
    binary_path = ensure_binary()
    start_time = time.time()

    try:
        result = subprocess.run(
            [str(binary_path), "--json", "-v"],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(repo_path),
        )

        duration_ms = int((time.time() - start_time) * 1000)

        if result.returncode != 0 and not result.stdout:
            raise RuntimeError(f"git-sizer failed: {result.stderr}")

        # Parse JSON output
        output = json.loads(result.stdout)
        return output, duration_ms

    except subprocess.TimeoutExpired:
        duration_ms = int((time.time() - start_time) * 1000)
        raise RuntimeError(f"git-sizer timed out after {duration_ms}ms")


# =============================================================================
# Analysis Functions
# =============================================================================

def format_bytes(size: int) -> str:
    """Format bytes to human-readable string."""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KiB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MiB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GiB"


def calculate_threshold_level(metric: str, value: int) -> int:
    """Calculate threshold level (0-4 stars) based on git-sizer thresholds."""
    thresholds = {
        "max_blob_size": [
            (1 * 1024 * 1024, 1),    # 1 MiB = *
            (10 * 1024 * 1024, 2),   # 10 MiB = **
            (50 * 1024 * 1024, 3),   # 50 MiB = ***
            (100 * 1024 * 1024, 4),  # 100 MiB = !!!!
        ],
        "blob_total_size": [
            (100 * 1024 * 1024, 1),   # 100 MiB = *
            (500 * 1024 * 1024, 2),   # 500 MiB = **
            (1024 * 1024 * 1024, 3),  # 1 GiB = ***
            (5 * 1024 * 1024 * 1024, 4),  # 5 GiB = !!!!
        ],
        "commit_count": [
            (10000, 1),   # 10k = *
            (50000, 2),   # 50k = **
            (200000, 3),  # 200k = ***
            (1000000, 4), # 1M = !!!!
        ],
        "max_tree_entries": [
            (1000, 1),    # 1k = *
            (5000, 2),    # 5k = **
            (10000, 3),   # 10k = ***
            (50000, 4),   # 50k = !!!!
        ],
        "max_history_depth": [
            (10000, 1),   # 10k = *
            (50000, 2),   # 50k = **
            (200000, 3),  # 200k = ***
            (500000, 4),  # 500k = !!!!
        ],
        "max_path_depth": [
            (10, 1),   # 10 = *
            (15, 2),   # 15 = **
            (20, 3),   # 20 = ***
            (30, 4),   # 30 = !!!!
        ],
        "expanded_blob_count": [
            (10000, 1),   # 10k = *
            (50000, 2),   # 50k = **
            (100000, 3),  # 100k = ***
            (500000, 4),  # 500k = !!!!
        ],
    }

    if metric not in thresholds:
        return 0

    for threshold, level in thresholds[metric]:
        if value >= threshold:
            continue
        else:
            return max(0, level - 1)

    return 4


def calculate_health_grade(violations: list[ThresholdViolation]) -> str:
    """Calculate overall health grade (A-F) based on violations."""
    if not violations:
        return "A"

    max_level = max(v.level for v in violations)
    total_violations = len(violations)

    if max_level >= 4:
        return "F"
    elif max_level >= 3:
        return "D" if total_violations > 2 else "D+"
    elif max_level >= 2:
        return "C" if total_violations > 3 else "C+"
    elif max_level >= 1:
        return "B" if total_violations > 5 else "B+"
    return "A"


def identify_lfs_candidates(raw_output: dict, threshold_bytes: int = 1024 * 1024) -> list[str]:
    """Identify files that should be in Git LFS."""
    candidates = []

    max_blob_size = raw_output.get("max_blob_size", 0)
    if max_blob_size >= threshold_bytes:
        blob_ref = raw_output.get("max_blob_size_blob", "")
        if blob_ref:
            # Extract path from ref like "refs/heads/master:path/to/file"
            if ":" in blob_ref:
                path = blob_ref.split(":", 1)[1].strip(")")
                candidates.append(path)

    return candidates


def analyze_repository(repo_path: Path) -> RepositoryAnalysis:
    """Analyze a single repository."""
    raw_output, duration_ms = run_git_sizer(repo_path)

    # Extract metrics
    metrics = RepositoryMetrics(
        commit_count=raw_output.get("unique_commit_count", 0),
        commit_total_size=raw_output.get("unique_commit_size", 0),
        max_commit_size=raw_output.get("max_commit_size", 0),
        max_history_depth=raw_output.get("max_history_depth", 0),
        max_parent_count=raw_output.get("max_parent_count", 0),
        tree_count=raw_output.get("unique_tree_count", 0),
        tree_total_size=raw_output.get("unique_tree_size", 0),
        tree_total_entries=raw_output.get("unique_tree_entries", 0),
        max_tree_entries=raw_output.get("max_tree_entries", 0),
        blob_count=raw_output.get("unique_blob_count", 0),
        blob_total_size=raw_output.get("unique_blob_size", 0),
        max_blob_size=raw_output.get("max_blob_size", 0),
        tag_count=raw_output.get("unique_tag_count", 0),
        max_tag_depth=raw_output.get("max_tag_depth", 0),
        reference_count=raw_output.get("reference_count", 0),
        branch_count=raw_output.get("reference_groups", {}).get("branches", 0),
        max_path_depth=raw_output.get("max_path_depth", 0),
        max_path_length=raw_output.get("max_path_length", 0),
        expanded_tree_count=raw_output.get("max_expanded_tree_count", 0),
        expanded_blob_count=raw_output.get("max_expanded_blob_count", 0),
        expanded_blob_size=raw_output.get("max_expanded_blob_size", 0),
    )

    # Detect violations
    violations = []
    metrics_to_check = [
        ("max_blob_size", metrics.max_blob_size, raw_output.get("max_blob_size_blob", "")),
        ("blob_total_size", metrics.blob_total_size, ""),
        ("commit_count", metrics.commit_count, ""),
        ("max_tree_entries", metrics.max_tree_entries, raw_output.get("max_tree_entries_tree", "")),
        ("max_history_depth", metrics.max_history_depth, ""),
        ("max_path_depth", metrics.max_path_depth, raw_output.get("max_path_depth_tree", "")),
        ("expanded_blob_count", metrics.expanded_blob_count, ""),
    ]

    for metric_name, value, object_ref in metrics_to_check:
        level = calculate_threshold_level(metric_name, value)
        if level > 0:
            violations.append(ThresholdViolation(
                metric=metric_name,
                value=format_bytes(value) if "size" in metric_name else str(value),
                raw_value=value,
                level=level,
                object_ref=object_ref,
            ))

    # Calculate health grade
    health_grade = calculate_health_grade(violations)

    # Identify LFS candidates
    lfs_candidates = identify_lfs_candidates(raw_output)

    return RepositoryAnalysis(
        git_sizer_version=get_binary_version(),
        duration_ms=duration_ms,
        metrics=metrics,
        violations=violations,
        health_grade=health_grade,
        lfs_candidates=lfs_candidates,
        raw_output=raw_output,
    )


def build_caldera_envelope(
    analysis: RepositoryAnalysis,
    run_id: str,
    repo_id: str,
    repo_name: str,
    branch: str,
    commit: str,
) -> dict:
    """Build Caldera envelope format output.

    Args:
        analysis: The repository analysis results
        run_id: UUID for the collection run
        repo_id: UUID for the repository
        branch: Git branch analyzed
        commit: 40-character commit SHA

    Returns:
        Caldera envelope dict with metadata and data sections
    """
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    return {
        "metadata": {
            "tool_name": TOOL_NAME,
            "tool_version": analysis.git_sizer_version,
            "run_id": run_id,
            "repo_id": repo_id,
            "repo_name": repo_name,
            "branch": branch,
            "commit": commit,
            "timestamp": timestamp,
            "schema_version": SCHEMA_VERSION,
        },
        "data": {
            "tool": TOOL_NAME,
            "tool_version": analysis.git_sizer_version,
            "repo_name": repo_name,
            "health_grade": analysis.health_grade,
            "duration_ms": analysis.duration_ms,
            "metrics": analysis.metrics.to_dict(),
            "violations": [v.to_dict() for v in analysis.violations],
            "lfs_candidates": analysis.lfs_candidates,
            "raw_output": analysis.raw_output,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze Git repository health using git-sizer (Caldera format)"
    )
    parser.add_argument(
        "--repo-path",
        required=True,
        help="Path to repository to analyze",
    )
    parser.add_argument(
        "--repo-name",
        help="Repository name (for logging)",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to write output.json",
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="UUID for the collection run",
    )
    parser.add_argument(
        "--repo-id",
        required=True,
        help="UUID for the repository",
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Git branch (default: main)",
    )
    parser.add_argument(
        "--commit",
        help="40-character commit SHA (default: HEAD)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "--exit-zero",
        action="store_true",
        help="Always exit 0 on successful analysis (ignore health grade)",
    )

    args = parser.parse_args()

    repo_path = Path(args.repo_path).resolve()
    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {repo_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_commit(path: Path) -> str:
        if args.commit:
            return args.commit
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=str(path),
            )
            value = result.stdout.strip()
            return value if len(value) == 40 else "0" * 40
        except Exception:
            return "0" * 40

    def _analyze_one(path: Path, name: str, primary: bool) -> tuple[RepositoryAnalysis, Path]:
        commit_value = _resolve_commit(path)
        if len(commit_value) != 40:
            raise ValueError(f"commit must be a 40-character SHA, got: {commit_value}")
        print(f"Analyzing: {path}")
        analysis = analyze_repository(path)
        output = build_caldera_envelope(
            analysis=analysis,
            run_id=args.run_id,
            repo_id=args.repo_id,
            repo_name=name,
            branch=args.branch,
            commit=commit_value,
        )
        target_dir = output_dir / name
        target_dir.mkdir(parents=True, exist_ok=True)
        output_path = target_dir / "output.json"
        output_path.write_text(json.dumps(output, indent=2, default=str))
        print(f"Output: {output_path}")
        return analysis, output_path

    if (repo_path / ".git").exists():
        repo_name = args.repo_name or repo_path.name
        analysis, _ = _analyze_one(repo_path, repo_name, primary=True)
        primary_path = output_dir / "output.json"
        if primary_path.parent != output_dir:
            primary_path.parent.mkdir(parents=True, exist_ok=True)
        primary_path.write_text((output_dir / repo_name / "output.json").read_text())
        exit_code = 0 if analysis.health_grade[0] in "ABC" else 1
    else:
        subrepos = [
            p for p in repo_path.iterdir()
            if p.is_dir() and (p / ".git").exists()
        ]
        if not subrepos:
            print(f"Error: Not a git repository: {repo_path}", file=sys.stderr)
            sys.exit(1)
        print(f"Found {len(subrepos)} git repositories under {repo_path}")
        first_analysis = None
        for idx, subrepo in enumerate(sorted(subrepos)):
            name = subrepo.name
            analysis, output_path = _analyze_one(subrepo, name, primary=(idx == 0))
            first_analysis = first_analysis or analysis
            if idx == 0:
                primary_path = output_dir / "output.json"
                primary_path.write_text(output_path.read_text())
        exit_code = 0 if (first_analysis and first_analysis.health_grade[0] in "ABC") else 1

    if args.exit_zero:
        sys.exit(0)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
