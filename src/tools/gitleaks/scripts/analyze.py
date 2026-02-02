#!/usr/bin/env python3
"""CLI entry point for gitleaks secret analysis.

Caldera-compliant wrapper that produces envelope format output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add scripts directory and shared src to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from secret_analyzer import analyze_repository, get_gitleaks_version

TOOL_NAME = "gitleaks"
SCHEMA_VERSION = "1.0.0"


def _resolve_gitleaks_path(path_arg: str | None) -> Path:
    if path_arg:
        return Path(path_arg)
    script_dir = Path(__file__).parent
    return script_dir.parent / "bin" / "gitleaks"


def _compute_content_hash(repo_path: Path) -> str:
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


def _resolve_commit(repo_path: Path, commit_arg: str | None) -> str:
    """Resolve commit SHA, falling back to content hash."""
    if commit_arg and len(commit_arg) == 40 and commit_arg != "0" * 40:
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
        return _compute_content_hash(repo_path)


def to_caldera_envelope(
    analysis,
    run_id: str,
    repo_id: str,
    branch: str,
    commit: str,
    tool_version: str,
    timestamp: str,
) -> dict:
    """Convert SecretAnalysis to Caldera envelope format with metadata + data."""
    # Build the data section with analysis results
    data = {
        "tool": TOOL_NAME,
        "tool_version": tool_version,
        "total_secrets": analysis.total_secrets,
        "unique_secrets": analysis.unique_secrets,
        "secrets_in_head": analysis.secrets_in_head,
        "secrets_in_history": analysis.secrets_in_history,
        "files_with_secrets": analysis.files_with_secrets,
        "commits_with_secrets": analysis.commits_with_secrets,
        "secrets_by_rule": analysis.secrets_by_rule,
        "secrets_by_severity": analysis.secrets_by_severity,
        "findings": [
            {
                "file_path": f.file_path,
                "line_number": f.line_number,
                "rule_id": f.rule_id,
                "secret_type": f.secret_type,
                "description": f.description,
                "secret_preview": f.secret_preview,
                "entropy": f.entropy,
                "commit_hash": f.commit_hash,
                "commit_author": f.commit_author,
                "commit_date": f.commit_date,
                "fingerprint": f.fingerprint,
                "in_current_head": f.in_current_head,
                "severity": f.severity,
            }
            for f in analysis.findings
        ],
        "files": {
            k: {
                "file_path": v.file_path,
                "secret_count": v.secret_count,
                "rule_ids": v.rule_ids,
                "earliest_commit": v.earliest_commit,
                "latest_commit": v.latest_commit,
            }
            for k, v in analysis.files.items()
        },
        "directories": {
            k: {
                "direct_secret_count": v.direct_secret_count,
                "recursive_secret_count": v.recursive_secret_count,
                "direct_file_count": v.direct_file_count,
                "recursive_file_count": v.recursive_file_count,
                "rule_id_counts": v.rule_id_counts,
            }
            for k, v in analysis.directories.items()
        },
        "scan_time_ms": analysis.scan_time_ms,
    }

    return {
        "metadata": {
            "tool_name": TOOL_NAME,
            "tool_version": tool_version,
            "run_id": run_id,
            "repo_id": repo_id,
            "branch": branch,
            "commit": commit,
            "timestamp": timestamp,
            "schema_version": SCHEMA_VERSION,
        },
        "data": data,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze secrets using gitleaks")
    parser.add_argument(
        "--repo-path",
        required=True,
        type=Path,
        help="Path to repository to analyze",
    )
    parser.add_argument(
        "--repo-name",
        required=True,
        help="Repository name for output naming",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory to write analysis output",
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Run identifier (UUID)",
    )
    parser.add_argument(
        "--repo-id",
        required=True,
        help="Repository identifier (UUID)",
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Branch analyzed",
    )
    parser.add_argument(
        "--commit",
        default=None,
        help="Commit SHA (40-character hex)",
    )
    parser.add_argument(
        "--gitleaks",
        help="Path to gitleaks binary",
    )
    parser.add_argument(
        "--config",
        help="Path to gitleaks config file",
    )
    parser.add_argument(
        "--baseline",
        help="Path to baseline report for comparison",
    )
    args = parser.parse_args()

    repo_path = args.repo_path.resolve()
    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {repo_path}", file=sys.stderr)
        return 1

    repo_name = args.repo_name or repo_path.name

    gitleaks_path = _resolve_gitleaks_path(args.gitleaks)
    if not gitleaks_path.exists():
        print(f"Error: gitleaks not found at {gitleaks_path}", file=sys.stderr)
        print("Run 'make setup' to install gitleaks", file=sys.stderr)
        return 1

    # Resolve commit
    commit = _resolve_commit(repo_path, args.commit)

    print(f"Analyzing: {repo_path}")
    print(f"Using gitleaks: {gitleaks_path}")
    print(f"Gitleaks version: {get_gitleaks_version(gitleaks_path)}")

    # Run analysis
    analysis = analyze_repository(
        gitleaks_path=gitleaks_path,
        repo_path=repo_path,
        config_path=Path(args.config) if args.config else None,
        baseline_path=Path(args.baseline) if args.baseline else None,
        repo_name_override=repo_name,
    )

    # Get tool version
    tool_version = get_gitleaks_version(gitleaks_path)
    timestamp = datetime.now(timezone.utc).isoformat()

    # Convert to Caldera envelope format
    envelope = to_caldera_envelope(
        analysis,
        run_id=args.run_id,
        repo_id=args.repo_id,
        branch=args.branch,
        commit=commit,
        tool_version=tool_version,
        timestamp=timestamp,
    )

    # Write output
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "output.json"
    output_path.write_text(json.dumps(envelope, indent=2, default=str))

    print(f"Secrets found: {analysis.total_secrets}")
    print(f"Output: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
