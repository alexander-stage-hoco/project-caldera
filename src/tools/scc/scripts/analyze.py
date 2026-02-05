#!/usr/bin/env python3
"""CLI entry point for scc directory analysis.

Standard wrapper that translates orchestrator CLI args to directory_analyzer.
"""

from __future__ import annotations

import argparse
import json
import sys
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
from common.cli_parser import add_common_args, validate_common_args, CommitResolutionConfig
from common.envelope_formatter import create_envelope, get_current_timestamp


def _resolve_scc_path(path_arg: str | None) -> Path:
    """Resolve scc binary path."""
    if path_arg:
        return Path(path_arg)
    script_dir = Path(__file__).parent
    return script_dir.parent / "bin" / "scc"


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

    return create_envelope(
        result,
        tool_name="scc",
        tool_version=tool_version,
        run_id=run_id,
        repo_id=repo_id,
        branch=branch,
        commit=commit,
        timestamp=timestamp,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze directory structure using scc")
    add_common_args(parser)
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

    commit_config = CommitResolutionConfig.strict_with_fallback(Path(__file__).parent.parent)
    common = validate_common_args(args, commit_config=commit_config)

    scc_path = _resolve_scc_path(args.scc)
    if not scc_path.exists():
        print(f"Error: scc binary not found at {scc_path}", file=sys.stderr)
        print("Run 'make setup' to install scc", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing: {common.repo_path}")
    print(f"Using scc: {scc_path}")

    # Run scc analysis
    files, raw_scc_data = run_scc_by_file(scc_path, str(common.repo_path))
    print(f"Files found: {len(files)}")

    # Analyze directory structure
    result = analyze_directories(files, args.cocomo_preset)
    _normalize_result_paths(result, common.repo_path.resolve())

    # Convert to standard output format
    timestamp = get_current_timestamp()
    tool_version = get_scc_version(scc_path)
    output_dict = to_standard_output(
        result,
        common.run_id,
        common.repo_id,
        common.branch,
        common.commit,
        tool_version,
        timestamp,
    )

    # Write output
    common.output_path.write_text(json.dumps(output_dict, indent=2, default=str))

    summary = output_dict["data"].get("summary", {})
    print(f"Total files: {summary.get('total_files', 0)}")
    print(f"Total lines: {summary.get('total_lines', 0):,}")
    print(f"Output: {common.output_path}")


if __name__ == "__main__":
    main()
