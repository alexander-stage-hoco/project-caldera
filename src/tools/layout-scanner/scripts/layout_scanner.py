#!/usr/bin/env python3
"""
Layout Scanner - Fast filesystem-based repository layout scanner.

Scans a repository to create a canonical registry of all files and directories,
with sophisticated file classification and hierarchy information.

Usage:
    python layout_scanner.py /path/to/repo -o output.json
    python layout_scanner.py /path/to/repo --config config.json
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .classifier import (
    ClassificationResult,
    LanguageResult,
    classify_directory,
    classify_directory_by_name,
    classify_file,
    detect_language,
)
from .config_loader import ScannerConfig, load_config
from .hierarchy_builder import DirectoryMetrics, HierarchyInfo, build_hierarchy
from .ignore_filter import load_ignore_filter
from .output_writer import build_output, write_output
from .rule_loader import RuleSet, find_rules_file, load_default_rules, load_rules, merge_rules
from .tree_walker import WalkResult, walk_repository


def scan_repository(
    repo_path: Path,
    config: Optional[ScannerConfig] = None,
    enable_git: bool = False,
    enable_content: bool = False,
    rules: Optional[RuleSet] = None,
) -> Tuple[Dict[str, Any], int]:
    """
    Scan a repository and produce structured output.

    Args:
        repo_path: Path to repository root
        config: Scanner configuration (uses defaults if None)
        enable_git: Enable git metadata enrichment pass
        enable_content: Enable content metadata enrichment pass
        rules: Classification rules (uses defaults if None)

    Returns:
        Tuple of (output dict, scan duration in ms)
    """
    repo_path = Path(repo_path).resolve()

    if not repo_path.is_dir():
        raise ValueError(f"Repository path does not exist: {repo_path}")

    # Load config if not provided
    if config is None:
        config = load_config(repo_path)

    # Start timing
    start_time = time.perf_counter()

    # Load ignore filter
    ignore_filter = load_ignore_filter(
        repo_path,
        additional_patterns=config.ignore.additional_patterns,
        respect_gitignore=config.ignore.respect_gitignore,
    )

    # Walk the repository
    walk_result = walk_repository(repo_path, ignore_filter=ignore_filter)

    # Classify files
    file_classifications: Dict[str, ClassificationResult] = {}
    file_languages: Dict[str, LanguageResult] = {}

    for path, file_info in walk_result.files.items():
        # Classify file
        classification = classify_file(
            path=path,
            name=file_info.name,
            extension=file_info.extension,
            custom_path_rules=config.classification.custom_path_rules,
            custom_filename_rules=config.classification.custom_filename_rules,
            custom_extension_rules=config.classification.custom_extension_rules,
            overrides=config.classification.overrides,
            rules=rules,
            weights=config.classification.weights,
        )
        file_classifications[path] = classification

        # Detect language
        language = detect_language(file_info.name, file_info.extension)
        file_languages[path] = language

    # Build hierarchy and compute directory metrics
    file_class_map = {p: c.category for p, c in file_classifications.items()}
    file_lang_map = {p: l.language for p, l in file_languages.items()}

    hierarchy, dir_metrics = build_hierarchy(
        walk_result, file_class_map, file_lang_map
    )

    # Classify directories based on their contents
    dir_classifications: Dict[str, Tuple[str, str]] = {}
    for path, dir_info in walk_result.directories.items():
        metrics = dir_metrics.get(path)
        # Build list of classifications from distribution (empty if no files)
        classifications = []
        if metrics and metrics.classification_distribution:
            for cat, count in metrics.classification_distribution.items():
                classifications.extend([cat] * count)
        # Always use classify_directory_by_name - it handles empty lists
        # by checking directory name heuristics first
        category, reason = classify_directory_by_name(dir_info.name, classifications)
        dir_classifications[path] = (category, reason)

    # Git metadata enrichment (optional)
    git_metadata = None
    if enable_git:
        from .git_enricher import enrich_files as git_enrich

        git_result = git_enrich(repo_path, list(walk_result.files.keys()))
        git_metadata = git_result.file_metadata if git_result.is_git_repo else None

    # Content metadata enrichment (optional)
    content_metadata = None
    if enable_content:
        from .content_enricher import enrich_files as content_enrich

        content_result = content_enrich(repo_path, list(walk_result.files.keys()))
        content_metadata = content_result.file_metadata

    # Calculate scan duration
    end_time = time.perf_counter()
    scan_duration_ms = int((end_time - start_time) * 1000)

    # Build output
    output = build_output(
        walk_result=walk_result,
        file_classifications=file_classifications,
        file_languages=file_languages,
        dir_classifications=dir_classifications,
        dir_metrics=dir_metrics,
        hierarchy=hierarchy,
        repo_name=repo_path.name,
        repo_path=str(repo_path),
        scan_duration_ms=scan_duration_ms,
        git_metadata=git_metadata,
        content_metadata=content_metadata,
    )

    return output, scan_duration_ms


def main(args: Optional[list] = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fast filesystem-based repository layout scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/repo
  %(prog)s /path/to/repo -o output.json
  %(prog)s /path/to/repo --config .layout-scanner.json
  %(prog)s /path/to/repo --ignore "*.log" --ignore "tmp/"
        """,
    )

    parser.add_argument(
        "repo_path",
        type=Path,
        help="Path to repository to scan",
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output JSON file path (default: stdout)",
    )

    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file",
    )

    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        help="Additional patterns to ignore (can be specified multiple times)",
    )

    parser.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Don't respect .gitignore",
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress output",
    )

    parser.add_argument(
        "--git",
        action="store_true",
        help="Enable git metadata enrichment pass (adds commit history info)",
    )

    parser.add_argument(
        "--content",
        action="store_true",
        help="Enable content metadata enrichment pass (adds line counts, hashes)",
    )

    parser.add_argument(
        "--rules",
        type=Path,
        help="Path to YAML classification rules file",
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate output against JSON schema before writing",
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if validation errors occur (requires --validate)",
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed progress and error information",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="layout-scanner 1.0.0",
    )

    parsed_args = parser.parse_args(args)

    # Build CLI overrides
    cli_overrides: Dict[str, Any] = {}

    if parsed_args.ignore:
        cli_overrides.setdefault("ignore", {})["additional_patterns"] = parsed_args.ignore

    if parsed_args.no_gitignore:
        cli_overrides.setdefault("ignore", {})["respect_gitignore"] = False

    # Load configuration
    config = load_config(
        repo_path=parsed_args.repo_path,
        config_path=parsed_args.config,
        cli_overrides=cli_overrides if cli_overrides else None,
    )

    # Load classification rules
    rules: Optional[RuleSet] = None
    rules_source: Optional[str] = None

    if parsed_args.rules:
        # CLI-specified rules file
        rules = load_rules(parsed_args.rules)
        rules_source = str(parsed_args.rules)
    elif config.classification.rules_path:
        # Config-specified rules file
        rules = load_rules(config.classification.rules_path)
        rules_source = str(config.classification.rules_path)
    else:
        # Auto-discover rules file in repo
        discovered = find_rules_file(parsed_args.repo_path)
        if discovered:
            rules = load_rules(discovered)
            rules_source = str(discovered)

    # Merge with defaults if custom rules were loaded
    if rules:
        default_rules = load_default_rules()
        rules = merge_rules(default_rules, rules)

    try:
        # Scan repository
        if not parsed_args.quiet:
            print(f"Scanning {parsed_args.repo_path}...", file=sys.stderr)
            if rules_source:
                print(f"Using classification rules from {rules_source}", file=sys.stderr)
            if parsed_args.git:
                print("Git metadata enrichment enabled", file=sys.stderr)
            if parsed_args.content:
                print("Content metadata enrichment enabled", file=sys.stderr)

        output, scan_duration_ms = scan_repository(
            parsed_args.repo_path,
            config,
            enable_git=parsed_args.git,
            enable_content=parsed_args.content,
            rules=rules,
        )

        if not parsed_args.quiet:
            stats = output["statistics"]
            print(
                f"Scanned {stats['total_files']} files, "
                f"{stats['total_directories']} directories "
                f"in {scan_duration_ms}ms",
                file=sys.stderr,
            )

            # Show skipped count if any
            if stats.get("skipped_count", 0) > 0:
                print(f"Warning: {stats['skipped_count']} directories skipped (permission denied)", file=sys.stderr)

        # Verbose output
        if parsed_args.verbose:
            print("\nClassification distribution:", file=sys.stderr)
            for cat, count in sorted(stats["by_classification"].items(), key=lambda x: -x[1]):
                print(f"  {cat}: {count}", file=sys.stderr)

            print("\nLanguage distribution:", file=sys.stderr)
            for lang, count in sorted(stats["by_language"].items(), key=lambda x: -x[1])[:10]:
                print(f"  {lang}: {count}", file=sys.stderr)

            if stats.get("skipped_count", 0) > 0:
                # Get skipped paths from walk_result (need to access through scan_repository return)
                print(f"\nSkipped {stats['skipped_count']} directories due to access errors", file=sys.stderr)

        # Validate output if requested
        if parsed_args.validate:
            from .schema_validator import SchemaValidator

            if not parsed_args.quiet:
                print("Validating output...", file=sys.stderr)

            validator = SchemaValidator()
            validation_result = validator.validate(output)

            if not validation_result.valid:
                print("Validation errors:", file=sys.stderr)
                for error in validation_result.all_errors[:10]:
                    print(f"  - {error}", file=sys.stderr)

                if parsed_args.strict:
                    print("Strict mode: aborting due to validation errors", file=sys.stderr)
                    return 1
                else:
                    print("Continuing despite validation errors (use --strict to abort)", file=sys.stderr)
            else:
                if not parsed_args.quiet:
                    print("Validation passed (schema, referential, consistency)", file=sys.stderr)

            if validation_result.all_warnings:
                print("Validation warnings:", file=sys.stderr)
                for warning in validation_result.all_warnings[:5]:
                    print(f"  - {warning}", file=sys.stderr)

        # Write output
        if parsed_args.output:
            write_output(output, parsed_args.output)
            if not parsed_args.quiet:
                print(f"Output written to {parsed_args.output}", file=sys.stderr)
        else:
            import json
            print(json.dumps(output, indent=2))

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
