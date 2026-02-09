#!/usr/bin/env python3
"""CLI entry point for coverage-ingest tool.

Ingests test coverage reports from multiple formats (LCOV, Cobertura, JaCoCo,
Istanbul) and normalizes them into Caldera's standard output format.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add scripts directory and shared src to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from parsers import (
    BaseCoverageParser,
    FileCoverage,
    LcovParser,
    CoberturaParser,
    JacocoParser,
    IstanbulParser,
)
from shared.path_utils import normalize_file_path
from common.cli_parser import add_common_args, validate_common_args, CommitResolutionConfig
from common.envelope_formatter import create_envelope, get_current_timestamp

TOOL_VERSION = "1.0.0"

# Available parsers in detection order (most specific first)
PARSERS: list[BaseCoverageParser] = [
    JacocoParser(),
    CoberturaParser(),
    LcovParser(),
    IstanbulParser(),
]

FORMAT_TO_PARSER: dict[str, BaseCoverageParser] = {
    parser.format_name: parser for parser in PARSERS
}


def detect_format(content: str | bytes) -> BaseCoverageParser | None:
    """Auto-detect the coverage format from content.

    Args:
        content: File content

    Returns:
        Matching parser, or None if no format detected
    """
    for parser in PARSERS:
        if parser.detect(content):
            return parser
    return None


def normalize_coverage_paths(
    coverages: list[FileCoverage],
    repo_root: Path,
) -> list[dict]:
    """Normalize file paths in coverage data to repo-relative format.

    Args:
        coverages: List of FileCoverage records
        repo_root: Repository root path for normalization

    Returns:
        List of coverage dicts with normalized paths
    """
    results = []
    for cov in coverages:
        # Normalize the path
        normalized_path = normalize_file_path(cov.relative_path, repo_root)

        # Convert to dict for JSON output
        results.append({
            "relative_path": normalized_path,
            "line_coverage_pct": cov.line_coverage_pct,
            "branch_coverage_pct": cov.branch_coverage_pct,
            "lines_total": cov.lines_total,
            "lines_covered": cov.lines_covered,
            "lines_missed": cov.lines_missed,
            "branches_total": cov.branches_total,
            "branches_covered": cov.branches_covered,
            "uncovered_lines": cov.uncovered_lines,
        })

    return results


def compute_summary(coverages: list[dict]) -> dict:
    """Compute summary statistics from coverage data.

    Args:
        coverages: List of coverage dicts

    Returns:
        Summary statistics dict
    """
    total_files = len(coverages)
    files_with_coverage = sum(
        1 for c in coverages
        if c.get("lines_total", 0) > 0
    )

    total_lines = sum(c.get("lines_total", 0) for c in coverages)
    total_covered = sum(c.get("lines_covered", 0) for c in coverages)

    total_branches = sum(
        c.get("branches_total", 0) or 0
        for c in coverages
    )
    total_branches_covered = sum(
        c.get("branches_covered", 0) or 0
        for c in coverages
    )

    overall_line_pct = None
    if total_lines > 0:
        overall_line_pct = round((total_covered / total_lines) * 100, 2)

    overall_branch_pct = None
    if total_branches > 0:
        overall_branch_pct = round((total_branches_covered / total_branches) * 100, 2)

    return {
        "total_files": total_files,
        "files_with_coverage": files_with_coverage,
        "overall_line_coverage_pct": overall_line_pct,
        "overall_branch_coverage_pct": overall_branch_pct,
        "total_lines": total_lines,
        "total_lines_covered": total_covered,
        "total_branches": total_branches if total_branches > 0 else None,
        "total_branches_covered": total_branches_covered if total_branches > 0 else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest coverage reports from multiple formats"
    )
    add_common_args(parser)
    parser.add_argument(
        "--coverage-file",
        required=True,
        help="Path to coverage report file",
    )
    parser.add_argument(
        "--format",
        choices=["lcov", "cobertura", "jacoco", "istanbul", "auto"],
        default="auto",
        help="Coverage format (default: auto-detect)",
    )

    args = parser.parse_args()

    commit_config = CommitResolutionConfig.strict_with_fallback(Path(__file__).parent.parent)
    common = validate_common_args(args, commit_config=commit_config)

    coverage_path = Path(args.coverage_file)
    if not coverage_path.exists():
        print(f"Error: Coverage file not found: {coverage_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Reading coverage from: {coverage_path}")

    # Read coverage file
    content = coverage_path.read_bytes()

    # Determine parser
    if args.format == "auto":
        parser_instance = detect_format(content)
        if parser_instance is None:
            print("Error: Could not detect coverage format", file=sys.stderr)
            print("Try specifying --format explicitly", file=sys.stderr)
            sys.exit(1)
        print(f"Detected format: {parser_instance.format_name}")
    else:
        parser_instance = FORMAT_TO_PARSER.get(args.format)
        if parser_instance is None:
            print(f"Error: Unknown format: {args.format}", file=sys.stderr)
            sys.exit(1)
        print(f"Using format: {parser_instance.format_name}")

    # Parse coverage data
    try:
        coverages = parser_instance.parse(content)
    except ValueError as e:
        print(f"Error parsing coverage file: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Files in report: {len(coverages)}")

    # Normalize paths
    coverage_dicts = normalize_coverage_paths(coverages, common.repo_path.resolve())

    # Compute summary
    summary = compute_summary(coverage_dicts)

    # Build output data
    data = {
        "tool": "coverage-ingest",
        "tool_version": TOOL_VERSION,
        "source_format": parser_instance.format_name,
        "source_file": str(coverage_path),
        "files": coverage_dicts,
        "summary": summary,
    }

    # Create envelope
    timestamp = get_current_timestamp()
    output = create_envelope(
        data,
        tool_name="coverage-ingest",
        tool_version=TOOL_VERSION,
        run_id=common.run_id,
        repo_id=common.repo_id,
        branch=common.branch,
        commit=common.commit,
        timestamp=timestamp,
    )

    # Write output
    common.output_path.write_text(json.dumps(output, indent=2))

    print(f"Total files: {summary['total_files']}")
    print(f"Files with coverage: {summary['files_with_coverage']}")
    if summary['overall_line_coverage_pct'] is not None:
        print(f"Overall line coverage: {summary['overall_line_coverage_pct']:.1f}%")
    if summary['overall_branch_coverage_pct'] is not None:
        print(f"Overall branch coverage: {summary['overall_branch_coverage_pct']:.1f}%")
    print(f"Output: {common.output_path}")


if __name__ == "__main__":
    main()
