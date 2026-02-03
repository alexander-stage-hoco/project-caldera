#!/usr/bin/env python3
"""Calibrate ground truth files from actual extractor output.

This script runs the AST extractor on each synthetic repo and generates calibrated
ground truth JSON files with accurate line numbers. Existing metadata and notes
are preserved from the original ground truth files.

Usage:
    python scripts/calibrate_ground_truth.py --all
    python scripts/calibrate_ground_truth.py --repo metaprogramming
    python scripts/calibrate_ground_truth.py --repo decorators-advanced --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path


def get_project_paths() -> tuple[Path, Path, Path]:
    """Get project directory paths.

    Returns:
        Tuple of (repos_dir, ground_truth_dir, scripts_dir)
    """
    scripts_dir = Path(__file__).parent
    project_root = scripts_dir.parent
    repos_dir = project_root / "eval-repos" / "synthetic"
    ground_truth_dir = project_root / "evaluation" / "ground-truth"
    return repos_dir, ground_truth_dir, scripts_dir


def run_extractor(repo_path: Path) -> dict:
    """Run the AST extractor on a repository.

    Args:
        repo_path: Path to the repository

    Returns:
        Extraction result as dict
    """
    # Import extractor from same package
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.extractors.python_extractor import PythonExtractor

    extractor = PythonExtractor()
    result = extractor.extract_directory(repo_path)

    # Convert to ground truth format
    symbols = []
    for s in result.symbols:
        sym = {
            "path": s.path,
            "symbol_name": s.symbol_name,
            "symbol_type": s.symbol_type,
            "line_start": s.line_start,
            "is_exported": s.is_exported,
        }
        if s.parameters is not None:
            sym["parameters"] = s.parameters
        symbols.append(sym)

    calls = []
    for c in result.calls:
        call = {
            "caller_file": c.caller_file,
            "caller_symbol": c.caller_symbol,
            "callee_symbol": c.callee_symbol,
            "callee_file": c.callee_file,
            "line_number": c.line_number,
            "call_type": c.call_type,
        }
        calls.append(call)

    imports = []
    for i in result.imports:
        imp = {
            "file": i.file,
            "imported_path": i.imported_path,
            "import_type": i.import_type,
            "line_number": i.line_number,
        }
        if i.imported_symbols:
            imp["imported_symbols"] = i.imported_symbols
        imports.append(imp)

    return {
        "symbols": symbols,
        "calls": calls,
        "imports": imports,
        "errors": result.errors,
    }


def load_existing_ground_truth(gt_file: Path) -> dict | None:
    """Load existing ground truth file if it exists.

    Args:
        gt_file: Path to ground truth file

    Returns:
        Ground truth data or None
    """
    if gt_file.exists():
        with open(gt_file) as f:
            return json.load(f)
    return None


def calibrate_repo(
    repo_name: str,
    repos_dir: Path,
    ground_truth_dir: Path,
    dry_run: bool = False,
) -> dict:
    """Calibrate ground truth for a single repository.

    Args:
        repo_name: Name of the repository
        repos_dir: Path to synthetic repos directory
        ground_truth_dir: Path to ground truth directory
        dry_run: If True, don't write files

    Returns:
        Calibrated ground truth dict
    """
    repo_path = repos_dir / repo_name
    gt_file = ground_truth_dir / f"{repo_name}.json"

    if not repo_path.exists():
        raise FileNotFoundError(f"Repository not found: {repo_path}")

    # Run extractor to get actual results
    extraction = run_extractor(repo_path)

    # Load existing ground truth for metadata
    existing_gt = load_existing_ground_truth(gt_file)

    # Build calibrated ground truth
    calibrated = {
        "metadata": existing_gt.get("metadata", {}) if existing_gt else {
            "repo": repo_name,
            "created": str(date.today()),
            "version": "1.0",
            "category": "synthetic",
            "description": f"Ground truth for {repo_name}",
        },
        "expected": {
            "symbols": extraction["symbols"],
            "calls": extraction["calls"],
            "imports": extraction["imports"],
            "summary": {
                "total_files": len(set(s["path"] for s in extraction["symbols"])),
                "total_symbols": len(extraction["symbols"]),
                "total_calls": len(extraction["calls"]),
                "total_imports": len(extraction["imports"]),
            },
        },
        "notes": existing_gt.get("notes", {}) if existing_gt else {},
    }

    # Update metadata version and date
    calibrated["metadata"]["version"] = "1.1-calibrated"
    calibrated["metadata"]["calibrated_date"] = str(date.today())

    # Add extraction errors to notes if any
    if extraction["errors"]:
        calibrated["notes"]["extraction_errors"] = extraction["errors"]

    if not dry_run:
        ground_truth_dir.mkdir(parents=True, exist_ok=True)
        with open(gt_file, "w") as f:
            json.dump(calibrated, f, indent=2)
        print(f"Calibrated: {gt_file}")
    else:
        print(f"[DRY RUN] Would calibrate: {gt_file}")

    return calibrated


def print_diff(repo_name: str, old_gt: dict | None, new_gt: dict) -> None:
    """Print a summary of changes between old and new ground truth.

    Args:
        repo_name: Name of the repository
        old_gt: Old ground truth (or None)
        new_gt: New ground truth
    """
    print(f"\n--- {repo_name} ---")

    if old_gt is None:
        print("  [NEW] No existing ground truth")
        print(f"  Symbols: {len(new_gt['expected']['symbols'])}")
        print(f"  Calls: {len(new_gt['expected']['calls'])}")
        print(f"  Imports: {len(new_gt['expected']['imports'])}")
        return

    old_symbols = {(s["path"], s["symbol_name"]): s for s in old_gt.get("expected", {}).get("symbols", [])}
    new_symbols = {(s["path"], s["symbol_name"]): s for s in new_gt["expected"]["symbols"]}

    # Count line number changes
    line_changes = 0
    for key, new_sym in new_symbols.items():
        if key in old_symbols:
            old_sym = old_symbols[key]
            if old_sym.get("line_start") != new_sym.get("line_start"):
                line_changes += 1

    # Count new/removed symbols
    new_keys = set(new_symbols.keys()) - set(old_symbols.keys())
    removed_keys = set(old_symbols.keys()) - set(new_symbols.keys())

    print(f"  Symbols: {len(old_symbols)} -> {len(new_symbols)}")
    print(f"  Line number changes: {line_changes}")
    if new_keys:
        print(f"  New symbols: {len(new_keys)}")
    if removed_keys:
        print(f"  Removed symbols: {len(removed_keys)}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Calibrate ground truth files from actual extractor output"
    )
    parser.add_argument(
        "--repo",
        help="Specific repository to calibrate",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Calibrate all repositories",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write files, just show what would change",
    )
    parser.add_argument(
        "--show-diff",
        action="store_true",
        help="Show differences between old and new ground truth",
    )
    parser.add_argument(
        "--skip",
        nargs="*",
        default=["partial-syntax-errors"],
        help="Repos to skip (default: partial-syntax-errors)",
    )
    args = parser.parse_args()

    if not args.repo and not args.all:
        parser.error("Must specify --repo or --all")

    repos_dir, ground_truth_dir, scripts_dir = get_project_paths()

    if args.all:
        # Find all repos with ground truth files
        repo_names = [
            gt_file.stem
            for gt_file in ground_truth_dir.glob("*.json")
        ]
        # Also include repos without ground truth
        for repo_dir in repos_dir.iterdir():
            if repo_dir.is_dir() and repo_dir.name not in repo_names:
                repo_names.append(repo_dir.name)
    else:
        repo_names = [args.repo]

    # Filter out skipped repos
    repo_names = [r for r in repo_names if r not in args.skip]

    print(f"Calibrating {len(repo_names)} repositories...")
    print(f"Skip list: {args.skip}")
    print()

    results = []
    for repo_name in sorted(repo_names):
        try:
            gt_file = ground_truth_dir / f"{repo_name}.json"
            old_gt = load_existing_ground_truth(gt_file)

            new_gt = calibrate_repo(
                repo_name,
                repos_dir,
                ground_truth_dir,
                dry_run=args.dry_run,
            )

            if args.show_diff:
                print_diff(repo_name, old_gt, new_gt)

            results.append((repo_name, True, None))
        except Exception as e:
            print(f"Error calibrating {repo_name}: {e}", file=sys.stderr)
            results.append((repo_name, False, str(e)))

    # Print summary
    print()
    print("=" * 60)
    print("CALIBRATION SUMMARY")
    print("=" * 60)

    success = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)

    print(f"Success: {success}/{len(results)}")
    if failed:
        print(f"Failed: {failed}")
        for repo_name, ok, error in results:
            if not ok:
                print(f"  - {repo_name}: {error}")


if __name__ == "__main__":
    main()
