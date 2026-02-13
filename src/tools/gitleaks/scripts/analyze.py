#!/usr/bin/env python3
"""CLI entry point for gitleaks secret analysis.

Caldera-compliant wrapper that produces envelope format output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

# Add scripts directory and shared src to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from common.cli_parser import add_common_args, validate_common_args, CommitResolutionConfig
from common.envelope_formatter import create_envelope
from common.git_utilities import resolve_commit, is_fallback_commit
from common.path_normalization import normalize_file_path, normalize_dir_path

from secret_analyzer import analyze_repository, get_gitleaks_version

TOOL_NAME = "gitleaks"
SCHEMA_VERSION = "1.0.0"


def _resolve_gitleaks_path(path_arg: str | None) -> Path:
    if path_arg:
        return Path(path_arg)
    script_dir = Path(__file__).parent
    return script_dir.parent / "bin" / "gitleaks"


def _compute_content_hash(repo_path: Path) -> str:
    """Compute a deterministic hash for non-git repos.

    Used as a fallback when analyzing directories that are not git repositories.
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


def build_analysis_data(analysis, tool_version: str, repo_root: Path | None = None) -> dict:
    """Build the data section from SecretAnalysis results.

    Args:
        analysis: SecretAnalysis object from secret_analyzer
        tool_version: Version of gitleaks

    Returns:
        Dictionary with all analysis data for the envelope data section
    """
    return {
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
                "file_path": normalize_file_path(f.file_path, repo_root),
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
            normalize_file_path(k, repo_root): {
                "file_path": normalize_file_path(v.file_path, repo_root),
                "secret_count": v.secret_count,
                "rule_ids": v.rule_ids,
                "earliest_commit": v.earliest_commit,
                "latest_commit": v.latest_commit,
            }
            for k, v in analysis.files.items()
        },
        "directories": {
            normalize_dir_path(k, repo_root): {
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze secrets using gitleaks")
    add_common_args(parser, default_repo_path=None)
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

    # Use lenient commit mode since gitleaks has special content-hash fallback
    common = validate_common_args(
        args,
        commit_config=CommitResolutionConfig.lenient(),
        create_output_dir=True,
    )

    gitleaks_path = _resolve_gitleaks_path(args.gitleaks)
    if not gitleaks_path.exists():
        print(f"Error: gitleaks not found at {gitleaks_path}", file=sys.stderr)
        print("Run 'make setup' to install gitleaks", file=sys.stderr)
        return 1

    # Resolve commit - use content hash for non-git repos
    commit = resolve_commit(common.repo_path, args.commit or None)
    if is_fallback_commit(commit):
        # For non-git directories, compute a content-based hash
        commit = _compute_content_hash(common.repo_path)

    print(f"Analyzing: {common.repo_path}")
    print(f"Using gitleaks: {gitleaks_path}")
    print(f"Gitleaks version: {get_gitleaks_version(gitleaks_path)}")

    # Run analysis
    analysis = analyze_repository(
        gitleaks_path=gitleaks_path,
        repo_path=common.repo_path,
        config_path=Path(args.config) if args.config else None,
        baseline_path=Path(args.baseline) if args.baseline else None,
        repo_name_override=common.repo_name,
    )

    # Get tool version
    tool_version = get_gitleaks_version(gitleaks_path)

    # Build data and create envelope
    data = build_analysis_data(analysis, tool_version, repo_root=common.repo_path)
    envelope = create_envelope(
        data,
        tool_name=TOOL_NAME,
        tool_version=tool_version,
        run_id=common.run_id,
        repo_id=common.repo_id,
        branch=common.branch,
        commit=commit,
        schema_version=SCHEMA_VERSION,
    )

    # Write output
    common.output_path.write_text(json.dumps(envelope, indent=2, default=str))

    print(f"Secrets found: {analysis.total_secrets}")
    print(f"Output: {common.output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
