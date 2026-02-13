#!/usr/bin/env python3
"""CLI entry point for DevSkim security analysis.

Standard wrapper that translates orchestrator CLI args to security_analyzer
and produces Caldera envelope output format.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# Add shared src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from common.cli_parser import add_common_args, validate_common_args
from common.envelope_formatter import create_envelope, get_current_timestamp
from common.path_normalization import normalize_file_path, normalize_dir_path

from .security_analyzer import (
    AnalysisResult,
    analyze_with_devskim,
    display_dashboard,
    get_devskim_version,
    set_color_enabled,
    RULE_TO_CATEGORY_MAP,
)

# Tool version and schema version
TOOL_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"


def result_to_data_dict(result: AnalysisResult, repo_root: Path | None = None) -> dict[str, Any]:
    """Convert AnalysisResult to the 'data' portion of envelope format.

    This produces the inner data structure without the envelope wrapper.
    """
    # Serialize files
    files = []
    for f in result.files:
        issues = []
        for issue in f.issues:
            issues.append({
                "rule_id": issue.rule_id,
                "cwe_ids": issue.cwe_ids,
                "dd_category": issue.dd_category,
                "line_start": issue.line_start,
                "line_end": issue.line_end,
                "column_start": issue.column_start,
                "column_end": issue.column_end,
                "severity": issue.severity,
                "message": issue.message,
                "code_snippet": issue.code_snippet,
            })
        files.append({
            "path": normalize_file_path(f.path, repo_root),
            "language": f.language,
            "lines": f.lines,
            "issue_count": f.issue_count,
            "issue_density": round(f.issue_density, 4),
            "by_category": f.by_category,
            "by_severity": f.by_severity,
            "issues": issues,
        })

    # Serialize directories
    directories = []
    for d in result.directories:
        directories.append({
            "path": normalize_dir_path(d.path, repo_root),
            "name": d.name,
            "depth": d.depth,
            "is_leaf": d.is_leaf,
            "child_count": d.child_count,
            "subdirectories": d.subdirectories,
            "direct": _directory_stats_to_dict(d.direct),
            "recursive": _directory_stats_to_dict(d.recursive),
        })

    # Serialize language stats
    by_language = {}
    for lang, stats in result.by_language.items():
        by_language[lang] = {
            "files": stats.files,
            "lines": stats.lines,
            "issue_count": stats.issue_count,
            "categories_covered": list(stats.categories_covered),
        }

    return {
        "tool": "devskim",
        "tool_version": result.devskim_version,
        "summary": {
            "total_files": len(result.files),
            "total_directories": len(result.directories),
            "files_with_issues": sum(1 for f in result.files if f.issue_count > 0),
            "total_issues": len(result.findings),
            "total_lines": sum(f.lines for f in result.files),
            "issues_by_category": result.by_category,
            "issues_by_severity": result.by_severity,
        },
        "files": files,
        "directories": directories,
        "by_language": by_language,
        "analysis_duration_ms": result.analysis_duration_ms,
        "rules_used": result.rules_used,
    }


def _directory_stats_to_dict(stats) -> dict[str, Any]:
    """Convert DirectoryStats to dict."""
    return {
        "file_count": stats.file_count,
        "lines_code": stats.lines_code,
        "issue_count": stats.issue_count,
        "by_category": stats.by_category,
        "by_severity": stats.by_severity,
        "issue_density": round(stats.issue_density, 4) if stats.issue_density else 0,
    }


def to_envelope_format(
    data: dict[str, Any],
    run_id: str,
    repo_id: str,
    branch: str,
    commit: str,
    timestamp: str,
    devskim_version: str,
) -> dict[str, Any]:
    """Convert analysis data to Caldera envelope output format."""
    return create_envelope(
        data,
        tool_name="devskim",
        tool_version=devskim_version,
        run_id=run_id,
        repo_id=repo_id,
        branch=branch,
        commit=commit,
        timestamp=timestamp,
        schema_version=SCHEMA_VERSION,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze security issues using DevSkim")
    add_common_args(parser)
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Only output JSON, no dashboard",
    )
    parser.add_argument(
        "--custom-rules",
        help="Path to directory containing custom DevSkim rule JSON files",
        default=None,
    )
    args = parser.parse_args()

    common = validate_common_args(args)

    if args.no_color:
        set_color_enabled(False)

    # Set REPO_NAME env var for security_analyzer
    os.environ["REPO_NAME"] = common.repo_name

    print(f"Analyzing: {common.repo_path}")

    # Resolve custom rules path relative to tool directory if provided
    custom_rules_path = None
    if args.custom_rules:
        custom_rules = Path(args.custom_rules)
        if not custom_rules.is_absolute():
            # Resolve relative to devskim tool directory
            tool_dir = Path(__file__).resolve().parents[1]
            custom_rules = tool_dir / custom_rules
        custom_rules_path = str(custom_rules) if custom_rules.exists() else None

    # Run security analysis
    result = analyze_with_devskim(str(common.repo_path), common.repo_name, str(common.repo_path), custom_rules_path)

    # Get devskim version
    devskim_version = get_devskim_version()

    print(f"Files analyzed: {len(result.files)}")
    print(f"Issues found: {len(result.findings)}")
    print(f"Duration: {result.analysis_duration_ms}ms")

    # Convert result to data dict
    data = result_to_data_dict(result, repo_root=common.repo_path)

    # Convert to envelope format
    timestamp = get_current_timestamp()
    output_dict = to_envelope_format(
        data,
        common.run_id,
        common.repo_id,
        common.branch,
        common.commit,
        timestamp,
        devskim_version,
    )

    # Write output
    common.output_path.write_text(json.dumps(output_dict, indent=2, ensure_ascii=False))

    print(f"Output: {common.output_path}")

    # Display dashboard unless json-only
    if not args.json_only:
        display_dashboard(result)


if __name__ == "__main__":
    main()
