#!/usr/bin/env python3
"""CLI entry point for scancode license analysis.

Standard wrapper that translates orchestrator CLI args to license_analyzer.
Produces Caldera envelope format output.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add scripts directory and shared src to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from license_analyzer import analyze_repository, LicenseAnalysis
from common.path_normalization import normalize_file_path, normalize_dir_path
from common.cli_parser import add_common_args, validate_common_args, CommitResolutionConfig
from common.envelope_formatter import create_envelope, get_current_timestamp


TOOL_VERSION = "1.0.0"


def _normalize_analysis_paths(analysis: LicenseAnalysis, repo_root: Path) -> None:
    """Normalize all file paths in the analysis to be repo-relative."""
    # Normalize findings
    for finding in analysis.findings:
        finding.file_path = normalize_file_path(finding.file_path, repo_root)

    # Normalize file summaries - need to rebuild the dict with normalized keys
    normalized_files = {}
    for file_path, summary in analysis.files.items():
        normalized_path = normalize_file_path(file_path, repo_root)
        summary.file_path = normalized_path
        normalized_files[normalized_path] = summary
    analysis.files.clear()
    analysis.files.update(normalized_files)

    # Normalize directory paths
    for directory in analysis.directories:
        directory.path = normalize_dir_path(directory.path, repo_root)


def to_envelope_output(
    analysis: LicenseAnalysis,
    repo_name: str,
    repo_path: str,
    run_id: str,
    repo_id: str,
    branch: str,
    commit: str,
    timestamp: str,
) -> dict:
    """Convert analysis to Caldera envelope output format."""
    # Get the raw analysis dict
    raw_dict = analysis.to_dict()

    # Extract data from the old format - the results object becomes data
    data = raw_dict.get("results", {})

    return create_envelope(
        data,
        tool_name="scancode",
        tool_version=TOOL_VERSION,
        run_id=run_id,
        repo_id=repo_id,
        branch=branch,
        commit=commit,
        timestamp=timestamp,
        extra_metadata={"repo_name": repo_name, "repo_path": repo_path},
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze repositories for licenses"
    )
    add_common_args(parser)
    args = parser.parse_args()

    commit_config = CommitResolutionConfig.strict_with_fallback(Path(__file__).parent.parent)
    common = validate_common_args(args, commit_config=commit_config)

    # Resolve repo_path for analysis (common.repo_path is not resolved)
    repo_path_resolved = common.repo_path.resolve()

    print(f"Analyzing: {repo_path_resolved}")

    # Run analysis
    analysis = analyze_repository(repo_path_resolved)

    # Normalize paths
    _normalize_analysis_paths(analysis, repo_path_resolved)

    # Convert to envelope format
    timestamp = get_current_timestamp()
    output_dict = to_envelope_output(
        analysis,
        common.repo_name,
        str(common.repo_path),  # Use original path (relative), not resolved
        common.run_id,
        common.repo_id,
        common.branch,
        common.commit,
        timestamp,
    )

    print(f"Licenses found: {analysis.licenses_found or ['none']}")
    print(f"Overall risk: {analysis.overall_risk}")
    print(f"Files with licenses: {analysis.files_with_licenses}")

    # Write output
    common.output_path.write_text(json.dumps(output_dict, indent=2, default=str))
    print(f"Output: {common.output_path}")


if __name__ == "__main__":
    main()
