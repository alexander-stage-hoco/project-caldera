#!/usr/bin/env python3
"""CLI entry point for lizard function complexity analysis."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from function_analyzer import (
    analyze_directory,
    result_to_output,
    set_color_enabled,
    get_lizard_version,
)
# Add shared src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from common.path_normalization import normalize_file_path, normalize_dir_path
from common.cli_parser import (
    add_common_args,
    validate_common_args_raising,
    CommitResolutionConfig,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze function complexity using lizard"
    )
    add_common_args(parser)
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "-t", "--threads",
        type=int,
        default=None,
        help="Number of threads (default: CPU count)",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test directories (excluded by default)",
    )
    parser.add_argument(
        "-l", "--languages",
        nargs="+",
        help="Only analyze specific languages (e.g., 'C#' 'Python')",
    )
    parser.add_argument(
        "--max-file-size",
        type=int,
        default=500,
        help="Skip files larger than N KB (default: 500)",
    )
    args = parser.parse_args()

    if args.no_color:
        set_color_enabled(False)

    commit_config = CommitResolutionConfig.strict_with_fallback(Path(__file__).parent.parent)
    common = validate_common_args_raising(args, commit_config=commit_config)

    print(f"Lizard version: {get_lizard_version()}")
    print()

    # Set REPO_NAME env var so analyze_directory can use it
    os.environ["REPO_NAME"] = common.repo_name

    print(f"Analyzing {common.repo_name}...")
    result = analyze_directory(
        target_path=str(common.repo_path),
        threads=args.threads,
        exclude_tests=not args.include_tests,
        languages=args.languages,
        max_file_size_kb=args.max_file_size,
    )

    # Override repo_name/repo_path from CLI if provided
    result.repo_name = common.repo_name
    result.repo_path = str(common.repo_path.resolve())
    result.repo_id = common.repo_id
    result.branch = common.branch
    result.commit = common.commit
    timestamp = datetime.now(timezone.utc).isoformat()
    result.generated_at = timestamp
    result.timestamp = timestamp
    result.run_id = common.run_id

    repo_root = common.repo_path.resolve()
    for file_entry in result.files:
        file_entry.path = normalize_file_path(file_entry.path, repo_root)

    for directory_entry in result.directories:
        directory_entry.path = normalize_dir_path(directory_entry.path, repo_root)

    result.root_path = "."
    common.output_path.write_text(json.dumps(result_to_output(result), indent=2, default=str))

    summary = result.summary
    print()
    print(f"Files analyzed: {summary.total_files if summary else 0}")
    print(f"Functions found: {summary.total_functions if summary else 0}")
    print(f"Total CCN: {summary.total_ccn if summary else 0}")
    print(f"Avg CCN: {summary.avg_ccn:.2f}" if summary else "Avg CCN: 0.00")
    print(f"Max CCN: {summary.max_ccn if summary else 0}")
    print(f"Functions over threshold: {summary.functions_over_threshold if summary else 0}")
    print(f"Output: {common.output_path}")


if __name__ == "__main__":
    main()
