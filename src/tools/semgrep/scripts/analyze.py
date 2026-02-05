#!/usr/bin/env python3
"""CLI entry point for Semgrep smell analysis.

Standard wrapper that translates orchestrator CLI args to smell_analyzer
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

from .smell_analyzer import (
    AnalysisResult,
    analyze_with_semgrep,
    display_dashboard,
    get_semgrep_version,
    set_color_enabled,
)

# Tool version and schema version
TOOL_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"


def result_to_data_dict(result: AnalysisResult) -> dict[str, Any]:
    """Convert AnalysisResult to the 'data' portion of envelope format.

    This produces the inner data structure without the envelope wrapper.
    """
    # Serialize files
    files = []
    for f in result.files:
        smells = []
        for s in f.smells:
            smells.append({
                "rule_id": s.rule_id,
                "dd_smell_id": s.dd_smell_id,
                "dd_category": s.dd_category,
                "line_start": s.line_start,
                "line_end": s.line_end,
                "column_start": s.column_start,
                "column_end": s.column_end,
                "severity": s.severity,
                "message": s.message,
                "code_snippet": s.code_snippet,
            })
        files.append({
            "path": f.path,
            "language": f.language,
            "lines": f.lines,
            "smell_count": f.smell_count,
            "smell_density": round(f.smell_density, 4),
            "by_category": f.by_category,
            "by_severity": f.by_severity,
            "by_smell_type": f.by_smell_type,
            "smells": smells,
        })

    # Serialize directories
    directories = []
    for d in result.directories:
        directories.append({
            "path": d.path,
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
            "smell_count": stats.smell_count,
            "categories_covered": list(stats.categories_covered),
        }

    return {
        "tool": "semgrep",
        "tool_version": result.semgrep_version,
        "summary": {
            "total_files": len(result.files),
            "total_directories": len(result.directories),
            "files_with_smells": sum(1 for f in result.files if f.smell_count > 0),
            "total_smells": len(result.smells),
            "total_lines": sum(f.lines for f in result.files),
            "smells_by_category": result.by_category,
            "smells_by_type": result.by_smell_type,
            "smells_by_severity": result.by_severity,
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
        "smell_count": stats.smell_count,
        "by_category": stats.by_category,
        "by_severity": stats.by_severity,
        "by_smell_type": stats.by_smell_type,
        "smell_density": round(stats.smell_density, 4) if stats.smell_density else 0,
    }


def to_envelope_format(
    data: dict[str, Any],
    run_id: str,
    repo_id: str,
    branch: str,
    commit: str,
    timestamp: str,
    semgrep_version: str,
) -> dict[str, Any]:
    """Convert analysis data to Caldera envelope output format."""
    return create_envelope(
        data,
        tool_name="semgrep",
        tool_version=semgrep_version,
        run_id=run_id,
        repo_id=repo_id,
        branch=branch,
        commit=commit,
        timestamp=timestamp,
        schema_version=SCHEMA_VERSION,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze code smells using Semgrep")
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
    args = parser.parse_args()

    common = validate_common_args(args)

    if args.no_color:
        set_color_enabled(False)

    # Set REPO_NAME env var for smell_analyzer
    os.environ["REPO_NAME"] = common.repo_name

    print(f"Analyzing: {common.repo_path}")

    # Run smell analysis
    result = analyze_with_semgrep(str(common.repo_path))

    # Get semgrep version
    semgrep_version = get_semgrep_version()

    print(f"Files analyzed: {len(result.files)}")
    print(f"Smells found: {len(result.smells)}")
    print(f"Duration: {result.analysis_duration_ms}ms")

    # Convert result to data dict
    data = result_to_data_dict(result)

    # Convert to envelope format
    timestamp = get_current_timestamp()
    output_dict = to_envelope_format(
        data,
        common.run_id,
        common.repo_id,
        common.branch,
        common.commit,
        timestamp,
        semgrep_version,
    )

    # Write output
    common.output_path.write_text(json.dumps(output_dict, indent=2, ensure_ascii=False))

    print(f"Output: {common.output_path}")

    # Display dashboard unless json-only
    if not args.json_only:
        display_dashboard(result)


if __name__ == "__main__":
    main()
