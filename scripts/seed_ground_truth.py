#!/usr/bin/env python3
"""Ground truth auto-seeding script for Project Caldera.

This script extracts key metrics from tool analysis output and generates
ground truth files that can be used for evaluation. The generated ground
truth files are meant to be reviewed and refined by developers.

Usage:
    python scripts/seed_ground_truth.py <tool-name> <output-file> [options]

Examples:
    # Seed ground truth from scc output
    python scripts/seed_ground_truth.py scc src/tools/scc/outputs/run-1/output.json

    # Seed ground truth with custom output name
    python scripts/seed_ground_truth.py lizard src/tools/lizard/outputs/run-1/output.json \
        --output-name my_repo

    # Dry run to see what would be generated
    python scripts/seed_ground_truth.py scc output.json --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def seed_scc_ground_truth(data: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    """Extract ground truth expectations from scc output.

    Args:
        data: The 'data' section of the tool output
        metadata: The 'metadata' section of the tool output

    Returns:
        Ground truth dictionary suitable for scc evaluation
    """
    ground_truth = {
        "schema_version": "2.0",
        "description": f"Auto-seeded ground truth from {metadata.get('run_id', 'unknown')}",
        "repository": metadata.get("repo_id", "unknown"),
        "seeded_at": datetime.now(timezone.utc).isoformat(),
        "seeded_from": {
            "run_id": metadata.get("run_id"),
            "commit": metadata.get("commit"),
            "timestamp": metadata.get("timestamp"),
        },
        "verification_status": "pending_review",
    }

    # Extract language statistics from directories
    directories = data.get("directories", [])
    if directories:
        # Get root directory stats (recursive)
        root = directories[0] if directories else {}
        recursive = root.get("recursive", {})
        by_language = recursive.get("by_language", {})

        # Build language expectations
        languages = {}
        for lang_name, lang_stats in by_language.items():
            languages[lang_name] = {
                "expected_language_name": lang_name,
                "expected_file_count": lang_stats.get("file_count", 0),
                "expected_loc_range": [
                    int(lang_stats.get("code", 0) * 0.9),  # Allow 10% variance
                    int(lang_stats.get("code", 0) * 1.1),
                ],
            }
        ground_truth["languages"] = languages

        # Aggregate expectations
        ground_truth["aggregate_expectations"] = {
            "total_languages": len(by_language),
            "total_files": recursive.get("file_count", 0),
            "minimum_total_loc": int(recursive.get("code", 0) * 0.9),
            "maximum_total_loc": int(recursive.get("code", 0) * 1.1),
            "total_complexity_range": [
                int(recursive.get("complexity_total", 0) * 0.9),
                int(recursive.get("complexity_total", 0) * 1.1),
            ],
        }

        # Directory count
        ground_truth["directory_analysis"] = {
            "expected_directory_count": len(directories),
            "invariants": {
                "recursive_gte_direct": "recursive.file_count >= direct.file_count for all directories",
                "sum_of_direct_equals_total": "sum of direct file counts equals total files",
            },
        }

    return ground_truth


def seed_lizard_ground_truth(data: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    """Extract ground truth expectations from lizard output.

    Args:
        data: The 'data' section of the tool output
        metadata: The 'metadata' section of the tool output

    Returns:
        Ground truth dictionary suitable for lizard evaluation
    """
    ground_truth = {
        "schema_version": "2.0",
        "description": f"Auto-seeded ground truth from {metadata.get('run_id', 'unknown')}",
        "seeded_at": datetime.now(timezone.utc).isoformat(),
        "seeded_from": {
            "run_id": metadata.get("run_id"),
            "commit": metadata.get("commit"),
            "timestamp": metadata.get("timestamp"),
        },
        "verification_status": "pending_review",
        "verification": {
            "method": "auto_seeded",
            "methodology": "Extracted from lizard analysis output - requires manual verification",
            "cross_validated_with": [],
            "verification_notes": "TODO: Manually verify CCN values for key functions",
        },
    }

    files = data.get("files", [])
    if not files:
        return ground_truth

    # Aggregate stats
    total_functions = 0
    total_ccn = 0
    files_data = {}

    for file_entry in files:
        file_path = file_entry.get("file_path", "unknown")
        functions = file_entry.get("functions", [])
        file_ccn = sum(f.get("ccn", 0) for f in functions)

        total_functions += len(functions)
        total_ccn += file_ccn

        # Build per-file expectations
        file_data = {
            "expected_functions": len(functions),
            "total_ccn": file_ccn,
            "functions": {},
        }

        for func in functions:
            func_name = func.get("name", "unknown")
            file_data["functions"][func_name] = {
                "ccn": func.get("ccn", 0),
                "nloc": func.get("nloc", 0),
                "params": func.get("params", 0),
                "start_line": func.get("start_line", 0),
                "end_line": func.get("end_line", 0),
            }

        files_data[file_path] = file_data

    ground_truth["total_files"] = len(files)
    ground_truth["total_functions"] = total_functions
    ground_truth["total_ccn"] = total_ccn
    ground_truth["files"] = files_data

    return ground_truth


def seed_semgrep_ground_truth(data: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    """Extract ground truth expectations from semgrep output.

    Args:
        data: The 'data' section of the tool output
        metadata: The 'metadata' section of the tool output

    Returns:
        Ground truth dictionary suitable for semgrep evaluation
    """
    ground_truth = {
        "schema_version": "2.0",
        "description": f"Auto-seeded ground truth from {metadata.get('run_id', 'unknown')}",
        "seeded_at": datetime.now(timezone.utc).isoformat(),
        "seeded_from": {
            "run_id": metadata.get("run_id"),
            "commit": metadata.get("commit"),
            "timestamp": metadata.get("timestamp"),
        },
        "verification_status": "pending_review",
    }

    findings = data.get("findings", [])
    if not findings:
        ground_truth["total_findings"] = 0
        ground_truth["findings_by_severity"] = {}
        ground_truth["findings_by_rule"] = {}
        return ground_truth

    # Aggregate by severity and rule
    severity_counts: Counter[str] = Counter()
    rule_counts: Counter[str] = Counter()
    file_findings: dict[str, list[dict]] = {}

    for finding in findings:
        severity = finding.get("severity", "unknown")
        rule_id = finding.get("rule_id", "unknown")
        file_path = finding.get("file_path", "unknown")

        severity_counts[severity] += 1
        rule_counts[rule_id] += 1

        if file_path not in file_findings:
            file_findings[file_path] = []
        file_findings[file_path].append({
            "rule_id": rule_id,
            "severity": severity,
            "line_start": finding.get("line_start", 0),
            "line_end": finding.get("line_end", 0),
        })

    ground_truth["total_findings"] = len(findings)
    ground_truth["findings_by_severity"] = dict(severity_counts)
    ground_truth["findings_by_rule"] = dict(rule_counts)
    ground_truth["findings_by_file"] = {
        path: {
            "count": len(findings_list),
            "findings": findings_list,
        }
        for path, findings_list in file_findings.items()
    }

    return ground_truth


def seed_layout_ground_truth(data: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    """Extract ground truth expectations from layout-scanner output.

    Args:
        data: The 'data' section of the tool output
        metadata: The 'metadata' section of the tool output

    Returns:
        Ground truth dictionary suitable for layout-scanner evaluation
    """
    ground_truth = {
        "schema_version": "2.0",
        "description": f"Auto-seeded ground truth from {metadata.get('run_id', 'unknown')}",
        "seeded_at": datetime.now(timezone.utc).isoformat(),
        "seeded_from": {
            "run_id": metadata.get("run_id"),
            "commit": metadata.get("commit"),
            "timestamp": metadata.get("timestamp"),
        },
        "verification_status": "pending_review",
    }

    files = data.get("files", [])
    directories = data.get("directories", [])

    # File classification expectations
    classification_counts: Counter[str] = Counter()
    language_counts: Counter[str] = Counter()

    for file in files:
        classification = file.get("classification", "unknown")
        language = file.get("language", "unknown")
        classification_counts[classification] += 1
        language_counts[language] += 1

    ground_truth["file_expectations"] = {
        "total_files": len(files),
        "classification_counts": dict(classification_counts),
        "language_counts": dict(language_counts),
    }

    # Directory expectations
    purpose_counts: Counter[str] = Counter()
    for directory in directories:
        purpose = directory.get("purpose", "unknown")
        purpose_counts[purpose] += 1

    ground_truth["directory_expectations"] = {
        "total_directories": len(directories),
        "purpose_counts": dict(purpose_counts),
    }

    return ground_truth


def seed_roslyn_ground_truth(data: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    """Extract ground truth expectations from roslyn-analyzers output.

    Args:
        data: The 'data' section of the tool output
        metadata: The 'metadata' section of the tool output

    Returns:
        Ground truth dictionary suitable for roslyn-analyzers evaluation
    """
    ground_truth = {
        "schema_version": "2.0",
        "description": f"Auto-seeded ground truth from {metadata.get('run_id', 'unknown')}",
        "seeded_at": datetime.now(timezone.utc).isoformat(),
        "seeded_from": {
            "run_id": metadata.get("run_id"),
            "commit": metadata.get("commit"),
            "timestamp": metadata.get("timestamp"),
        },
        "verification_status": "pending_review",
    }

    violations = data.get("violations", [])
    if not violations:
        ground_truth["total_violations"] = 0
        ground_truth["violations_by_severity"] = {}
        ground_truth["violations_by_rule"] = {}
        return ground_truth

    # Aggregate by severity and rule
    severity_counts: Counter[str] = Counter()
    rule_counts: Counter[str] = Counter()
    file_violations: dict[str, list[dict]] = {}

    for violation in violations:
        severity = violation.get("severity", "unknown")
        rule_id = violation.get("rule_id", "unknown")
        file_path = violation.get("file_path", "unknown")

        severity_counts[severity] += 1
        rule_counts[rule_id] += 1

        if file_path not in file_violations:
            file_violations[file_path] = []
        file_violations[file_path].append({
            "rule_id": rule_id,
            "severity": severity,
            "line": violation.get("line", 0),
        })

    ground_truth["total_violations"] = len(violations)
    ground_truth["violations_by_severity"] = dict(severity_counts)
    ground_truth["violations_by_rule"] = dict(rule_counts)
    ground_truth["violations_by_file"] = {
        path: {
            "count": len(viol_list),
            "violations": viol_list,
        }
        for path, viol_list in file_violations.items()
    }

    return ground_truth


def seed_trivy_ground_truth(data: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    """Extract ground truth expectations from trivy output.

    Args:
        data: The 'data' section of the tool output
        metadata: The 'metadata' section of the tool output

    Returns:
        Ground truth dictionary suitable for trivy evaluation
    """
    ground_truth = {
        "schema_version": "2.0",
        "description": f"Auto-seeded ground truth from {metadata.get('run_id', 'unknown')}",
        "seeded_at": datetime.now(timezone.utc).isoformat(),
        "seeded_from": {
            "run_id": metadata.get("run_id"),
            "commit": metadata.get("commit"),
            "timestamp": metadata.get("timestamp"),
        },
        "verification_status": "pending_review",
    }

    vulnerabilities = data.get("vulnerabilities", [])
    misconfigs = data.get("misconfigurations", data.get("iac_misconfigs", []))

    # Vulnerability expectations
    vuln_severity_counts: Counter[str] = Counter()
    vuln_package_counts: Counter[str] = Counter()

    for vuln in vulnerabilities:
        severity = vuln.get("severity", "unknown")
        package = vuln.get("package_name", vuln.get("package", "unknown"))
        vuln_severity_counts[severity] += 1
        vuln_package_counts[package] += 1

    ground_truth["vulnerability_expectations"] = {
        "total_vulnerabilities": len(vulnerabilities),
        "by_severity": dict(vuln_severity_counts),
        "by_package": dict(vuln_package_counts),
    }

    # Misconfiguration expectations
    misconfig_severity_counts: Counter[str] = Counter()
    misconfig_type_counts: Counter[str] = Counter()

    for misconfig in misconfigs:
        severity = misconfig.get("severity", "unknown")
        misconfig_type = misconfig.get("type", "unknown")
        misconfig_severity_counts[severity] += 1
        misconfig_type_counts[misconfig_type] += 1

    ground_truth["misconfiguration_expectations"] = {
        "total_misconfigurations": len(misconfigs),
        "by_severity": dict(misconfig_severity_counts),
        "by_type": dict(misconfig_type_counts),
    }

    return ground_truth


def seed_git_sizer_ground_truth(data: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    """Extract ground truth expectations from git-sizer output.

    Args:
        data: The 'data' section of the tool output
        metadata: The 'metadata' section of the tool output

    Returns:
        Ground truth dictionary suitable for git-sizer evaluation
    """
    ground_truth = {
        "schema_version": "2.0",
        "description": f"Auto-seeded ground truth from {metadata.get('run_id', 'unknown')}",
        "seeded_at": datetime.now(timezone.utc).isoformat(),
        "seeded_from": {
            "run_id": metadata.get("run_id"),
            "commit": metadata.get("commit"),
            "timestamp": metadata.get("timestamp"),
        },
        "verification_status": "pending_review",
    }

    metrics = data.get("metrics", {})
    violations = data.get("violations", [])
    lfs_candidates = data.get("lfs_candidates", [])

    # Metric expectations
    ground_truth["metric_expectations"] = {}
    for category, category_metrics in metrics.items():
        if isinstance(category_metrics, dict):
            ground_truth["metric_expectations"][category] = {
                name: {
                    "expected_value": value,
                    "tolerance_percent": 10,  # Allow 10% variance
                }
                for name, value in category_metrics.items()
                if isinstance(value, (int, float))
            }

    # Violation expectations
    violation_levels: Counter[str] = Counter()
    for violation in violations:
        level = violation.get("level", "unknown")
        violation_levels[level] += 1

    ground_truth["violation_expectations"] = {
        "total_violations": len(violations),
        "by_level": dict(violation_levels),
    }

    # LFS candidate expectations
    ground_truth["lfs_candidate_expectations"] = {
        "total_candidates": len(lfs_candidates),
    }

    return ground_truth


def seed_symbol_scanner_ground_truth(data: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    """Extract ground truth expectations from symbol-scanner output.

    Args:
        data: The 'data' section of the tool output
        metadata: The 'metadata' section of the tool output

    Returns:
        Ground truth dictionary suitable for symbol-scanner evaluation
    """
    ground_truth = {
        "schema_version": "2.0",
        "description": f"Auto-seeded ground truth from {metadata.get('run_id', 'unknown')}",
        "seeded_at": datetime.now(timezone.utc).isoformat(),
        "seeded_from": {
            "run_id": metadata.get("run_id"),
            "commit": metadata.get("commit"),
            "timestamp": metadata.get("timestamp"),
        },
        "verification_status": "pending_review",
        "verification": {
            "method": "auto_seeded",
            "methodology": "Extracted from symbol-scanner output - requires manual verification",
            "cross_validated_with": [],
            "verification_notes": "TODO: Manually verify symbol counts and call relationships",
        },
    }

    symbols = data.get("symbols", [])
    calls = data.get("calls", [])
    imports = data.get("imports", [])
    summary = data.get("summary", {})

    # Summary expectations
    ground_truth["summary_expectations"] = {
        "total_files": summary.get("total_files", 0),
        "total_symbols": summary.get("total_symbols", len(symbols)),
        "total_calls": summary.get("total_calls", len(calls)),
        "total_imports": summary.get("total_imports", len(imports)),
    }

    # Symbol type distribution
    symbol_types: Counter[str] = Counter()
    for symbol in symbols:
        symbol_type = symbol.get("symbol_type", "unknown")
        symbol_types[symbol_type] += 1

    ground_truth["symbol_expectations"] = {
        "by_type": dict(symbol_types),
        "total": len(symbols),
    }

    # Call type distribution
    call_types: Counter[str] = Counter()
    for call in calls:
        call_type = call.get("call_type", "unknown")
        call_types[call_type] += 1

    ground_truth["call_expectations"] = {
        "by_type": dict(call_types),
        "total": len(calls),
    }

    # Import type distribution
    import_types: Counter[str] = Counter()
    for imp in imports:
        import_type = imp.get("import_type", "unknown")
        import_types[import_type] += 1

    ground_truth["import_expectations"] = {
        "by_type": dict(import_types),
        "total": len(imports),
    }

    # Resolution statistics (if available in summary)
    resolution = summary.get("resolution", {})
    if resolution:
        ground_truth["resolution_expectations"] = {
            "total_resolved": resolution.get("total_resolved", 0),
            "total_unresolved": resolution.get("total_unresolved", 0),
            "resolved_same_file": resolution.get("resolved_same_file", 0),
            "resolved_cross_file": resolution.get("resolved_cross_file", 0),
        }

    # Per-file symbol counts (top 10 files by symbol count)
    file_symbol_counts: Counter[str] = Counter()
    for symbol in symbols:
        file_path = symbol.get("path", symbol.get("file_path", "unknown"))
        file_symbol_counts[file_path] += 1

    top_files = file_symbol_counts.most_common(10)
    ground_truth["top_files_by_symbols"] = {
        path: count for path, count in top_files
    }

    return ground_truth


# Tool name to seeding function mapping
TOOL_SEEDERS = {
    "scc": seed_scc_ground_truth,
    "lizard": seed_lizard_ground_truth,
    "semgrep": seed_semgrep_ground_truth,
    "layout-scanner": seed_layout_ground_truth,
    "roslyn-analyzers": seed_roslyn_ground_truth,
    "trivy": seed_trivy_ground_truth,
    "git-sizer": seed_git_sizer_ground_truth,
    "symbol-scanner": seed_symbol_scanner_ground_truth,
}


def seed_ground_truth(tool_name: str, output_path: Path, output_name: str | None = None) -> dict[str, Any]:
    """Seed ground truth from a tool output file.

    Args:
        tool_name: Name of the tool (scc, lizard, etc.)
        output_path: Path to the tool output JSON file
        output_name: Optional name for the ground truth file (defaults to run_id)

    Returns:
        Ground truth dictionary

    Raises:
        ValueError: If tool is not supported or output format is invalid
    """
    if tool_name not in TOOL_SEEDERS:
        raise ValueError(f"Unsupported tool: {tool_name}. Supported: {list(TOOL_SEEDERS.keys())}")

    if not output_path.exists():
        raise ValueError(f"Output file not found: {output_path}")

    try:
        with open(output_path) as f:
            output = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in output file: {e}")

    if "metadata" not in output or "data" not in output:
        raise ValueError("Output must have 'metadata' and 'data' sections")

    seeder = TOOL_SEEDERS[tool_name]
    return seeder(output["data"], output["metadata"])


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Seed ground truth files from tool analysis output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("tool_name", help="Name of the tool (scc, lizard, semgrep, etc.)")
    parser.add_argument("output_file", type=Path, help="Path to tool output JSON file")
    parser.add_argument(
        "--output-name",
        help="Name for the ground truth file (defaults to run_id from output)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory (defaults to tool's evaluation/ground-truth/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated ground truth without writing file",
    )

    args = parser.parse_args()

    try:
        ground_truth = seed_ground_truth(args.tool_name, args.output_file, args.output_name)

        if args.dry_run:
            print(json.dumps(ground_truth, indent=2))
            return 0

        # Determine output path
        if args.output_dir:
            output_dir = args.output_dir
        else:
            # Default to tool's ground-truth directory
            output_dir = Path(f"src/tools/{args.tool_name}/evaluation/ground-truth")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine filename
        if args.output_name:
            filename = f"{args.output_name}.json"
        else:
            # Use run_id from seeded_from or generate a name
            run_id = ground_truth.get("seeded_from", {}).get("run_id", "seeded")
            filename = f"{run_id}.json"

        output_path = output_dir / filename

        with open(output_path, "w") as f:
            json.dump(ground_truth, f, indent=2)
            f.write("\n")

        print(f"Ground truth seeded: {output_path}")
        print(f"Verification status: {ground_truth.get('verification_status', 'unknown')}")
        print("\nNext steps:")
        print("  1. Review the generated ground truth file")
        print("  2. Verify key values (CCN, file counts, etc.) manually")
        print("  3. Update verification_status to 'verified' once confirmed")

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
