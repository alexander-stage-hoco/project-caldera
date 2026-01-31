#!/usr/bin/env python3
"""
Standardized analyze.py wrapper for Roslyn Analyzers.

Provides consistent CLI interface for Project Caldera orchestration:
    python scripts/analyze.py --repo-path /path/to/repo --repo-name myrepo --output-dir /tmp/output \
        --run-id <uuid> --repo-id <uuid> --branch main --commit <sha>

This wrapper invokes roslyn_analyzer.py and wraps the output in Caldera's envelope format.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Add shared src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from common.path_normalization import normalize_file_path

from roslyn_analyzer import analyze

TOOL_NAME = "roslyn-analyzers"
TOOL_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"


def wrap_in_envelope(
    analysis_output: dict[str, Any],
    run_id: str,
    repo_id: str,
    branch: str,
    commit: str,
    repo_path: Path,
) -> dict[str, Any]:
    """Wrap roslyn analyzer output in Caldera envelope format."""
    results = analysis_output.get("results", {})
    repo_root = repo_path.resolve()

    # Map files to Caldera format (smells per file)
    files = []
    for file_entry in results.get("files", []):
        # Normalize path to repo-relative
        raw_path = file_entry.get("relative_path", file_entry.get("path", ""))
        relative_path = normalize_file_path(raw_path, repo_root)

        # Map violations to smells format expected by adapter
        smells = []
        for violation in file_entry.get("violations", []):
            smells.append({
                "rule_id": violation.get("rule_id", ""),
                "dd_category": violation.get("dd_category", "other"),
                "severity": _map_severity(violation.get("dd_severity", "medium")),
                "message": violation.get("message", ""),
                "line_start": violation.get("line_start"),
                "line_end": violation.get("line_end"),
                "column_start": violation.get("column_start"),
                "column_end": violation.get("column_end"),
            })

        files.append({
            "path": relative_path,
            "language": file_entry.get("language", "C#"),
            "lines_of_code": file_entry.get("lines_of_code", 0),
            "violation_count": file_entry.get("violation_count", 0),
            "violations": smells,
        })

    # Normalize directory_rollup paths to repo-relative
    directory_rollup = []
    for entry in results.get("directory_rollup", []):
        raw_dir = entry.get("directory", "")
        # Normalize directory path to repo-relative
        normalized_dir = normalize_file_path(raw_dir, repo_root)
        directory_rollup.append({
            **entry,
            "directory": normalized_dir,
        })

    envelope = {
        "metadata": {
            "tool_name": TOOL_NAME,
            "tool_version": results.get("tool_version", TOOL_VERSION),
            "run_id": run_id,
            "repo_id": repo_id,
            "branch": branch,
            "commit": commit,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "schema_version": SCHEMA_VERSION,
        },
        "data": {
            "tool": TOOL_NAME,
            "tool_version": results.get("tool_version", TOOL_VERSION),
            "analysis_duration_ms": results.get("analysis_duration_ms", 0),
            "summary": results.get("summary", {}),
            "files": files,
            "statistics": results.get("statistics", {}),
            "directory_rollup": directory_rollup,
        },
    }
    return envelope


def _map_severity(dd_severity: str) -> str:
    """Map dd_severity to standard severity values."""
    severity_map = {
        "critical": "CRITICAL",
        "high": "HIGH",
        "medium": "MEDIUM",
        "low": "LOW",
        "info": "INFO",
    }
    return severity_map.get(dd_severity.lower(), "MEDIUM")


def main() -> None:
    """Main entry point with standardized CLI."""
    parser = argparse.ArgumentParser(
        description="Run Roslyn Analyzers on .NET projects (Caldera wrapper)"
    )

    # Standard arguments (required for orchestration)
    parser.add_argument(
        "--repo-path",
        required=True,
        type=Path,
        help="Path to repository to analyze",
    )
    parser.add_argument(
        "--repo-name",
        required=True,
        help="Name of the repository (used for output filename)",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Output directory for results",
    )

    # Caldera orchestrator arguments
    parser.add_argument(
        "--run-id",
        required=True,
        help="Unique identifier for this run (UUID)",
    )
    parser.add_argument(
        "--repo-id",
        required=True,
        help="Unique identifier for the repository (UUID)",
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Git branch being analyzed",
    )
    parser.add_argument(
        "--commit",
        default="0" * 40,
        help="Git commit SHA (40 hex characters)",
    )

    # Tool-specific arguments
    parser.add_argument(
        "--build-timeout",
        type=int,
        default=900,
        help="Build timeout in seconds (default: 900 = 15 minutes)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )

    args = parser.parse_args()

    # Validate repo path exists
    if not args.repo_path.exists():
        print(f"Error: Repository path does not exist: {args.repo_path}")
        sys.exit(1)

    # Validate commit format
    if len(args.commit) != 40:
        print(f"Warning: Commit SHA should be 40 characters, got {len(args.commit)}")

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Temporary file for roslyn_analyzer output
    temp_output = args.output_dir / f".{args.repo_name}_temp.json"
    final_output = args.output_dir / "output.json"

    # Run analysis
    try:
        analyze(
            target_path=args.repo_path,
            output_path=temp_output,
            no_color=args.no_color,
            build_timeout=args.build_timeout,
        )
    except Exception as e:
        print(f"Error running analysis: {e}")
        sys.exit(1)

    # Load raw output and wrap in envelope
    try:
        with open(temp_output, "r") as f:
            raw_output = json.load(f)

        envelope = wrap_in_envelope(
            raw_output,
            run_id=args.run_id,
            repo_id=args.repo_id,
            branch=args.branch,
            commit=args.commit,
            repo_path=args.repo_path,
        )

        with open(final_output, "w") as f:
            json.dump(envelope, f, indent=2)

        # Clean up temp file
        temp_output.unlink()

        print(f"Results saved to {final_output}")

    except Exception as e:
        print(f"Error wrapping output: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
