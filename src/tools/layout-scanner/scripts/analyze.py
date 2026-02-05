#!/usr/bin/env python3
"""CLI entry point for layout scanner analysis.

Standard wrapper that translates orchestrator CLI args to layout_scanner
and produces Caldera envelope output format.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Add shared src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from common.cli_parser import add_common_args, validate_common_args
from common.envelope_formatter import create_envelope, get_current_timestamp

from .layout_scanner import load_config, scan_repository
from .output_writer import TOOL_VERSION, SCHEMA_VERSION


def to_envelope_format(
    scan_result: dict[str, Any],
    run_id: str,
    repo_id: str,
    branch: str,
    commit: str,
    timestamp: str,
) -> dict[str, Any]:
    """Convert layout_scanner result to Caldera envelope output format."""
    return create_envelope(
        scan_result,
        tool_name="layout-scanner",
        tool_version=TOOL_VERSION,
        run_id=run_id,
        repo_id=repo_id,
        branch=branch,
        commit=commit,
        timestamp=timestamp,
        schema_version=SCHEMA_VERSION,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze repository layout using layout-scanner")
    add_common_args(parser)
    parser.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Ignore .gitignore rules",
    )
    parser.add_argument(
        "--git",
        action="store_true",
        help="Enable git metadata enrichment",
    )
    parser.add_argument(
        "--content",
        action="store_true",
        help="Enable content metadata enrichment",
    )
    args = parser.parse_args()

    common = validate_common_args(args)

    print(f"Analyzing: {common.repo_path}")

    # Run layout scanner analysis
    config = load_config(common.repo_path)
    if args.no_gitignore:
        config.ignore.respect_gitignore = False

    scan_result, scan_duration_ms = scan_repository(
        common.repo_path,
        config=config,
        enable_git=args.git,
        enable_content=args.content,
    )
    scan_result["repository_path"] = common.repo_name
    scan_result["schema_version"] = SCHEMA_VERSION

    print(f"Files found: {scan_result.get('statistics', {}).get('total_files', 0)}")
    print(f"Directories: {scan_result.get('statistics', {}).get('total_directories', 0)}")
    print(f"Scan duration: {scan_duration_ms}ms")

    # Convert to envelope format
    timestamp = get_current_timestamp()
    output_dict = to_envelope_format(
        scan_result,
        common.run_id,
        common.repo_id,
        common.branch,
        common.commit,
        timestamp,
    )

    # Write output
    common.output_path.write_text(json.dumps(output_dict, indent=2, ensure_ascii=False))

    print(f"Output: {common.output_path}")


if __name__ == "__main__":
    main()
