#!/usr/bin/env python3
"""CLI entry point for symbol-scanner tool."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

# Add shared src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from common.path_normalization import normalize_file_path

from extractors import PythonExtractor, TreeSitterExtractor

TOOL_NAME = "symbol-scanner"
TOOL_VERSION = "0.1.0"
SCHEMA_VERSION = "1.0.0"


def _git_run(repo_path: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a git command in the target repository."""
    return subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True,
        text=True,
    )


def _git_head(repo_path: Path) -> str | None:
    """Return HEAD commit for repo_path if available."""
    result = _git_run(repo_path, ["rev-parse", "HEAD"])
    return result.stdout.strip() if result.returncode == 0 else None


def _commit_exists(repo_path: Path, commit: str) -> bool:
    """Check whether a commit exists in the given repo."""
    result = _git_run(repo_path, ["cat-file", "-e", f"{commit}^{{commit}}"])
    return result.returncode == 0


def _fallback_commit_hash(repo_path: Path) -> str:
    """Return the standard fallback commit hash for non-git repositories."""
    return "0" * 40


def _is_fallback_commit(commit: str) -> bool:
    """Check if commit is a fallback value (all zeros or empty)."""
    return not commit or commit == "0" * 40


def _resolve_commit(repo_path: Path, commit_arg: str, fallback_repo: Path | None) -> str:
    """Resolve a valid commit SHA for the target repo."""
    # Accept fallback commits directly
    if _is_fallback_commit(commit_arg):
        # Try to get actual HEAD first
        head = _git_head(repo_path)
        if head:
            return head
        if fallback_repo:
            head = _git_head(fallback_repo)
            if head:
                return head
        # Return the fallback hash
        return "0" * 40

    if commit_arg:
        if _commit_exists(repo_path, commit_arg):
            return commit_arg
        if fallback_repo and _commit_exists(fallback_repo, commit_arg):
            return commit_arg
        raise ValueError(f"Commit not found in repo: {commit_arg}")

    head = _git_head(repo_path)
    if head:
        return head
    if fallback_repo:
        head = _git_head(fallback_repo)
        if head:
            return head
    return _fallback_commit_hash(repo_path if repo_path.exists() else fallback_repo or repo_path)


def build_output_envelope(
    result,
    run_id: str,
    repo_id: str,
    branch: str,
    commit: str,
    timestamp: str,
) -> dict:
    """Build the standard output envelope with metadata and data sections."""
    # Convert dataclass objects to dicts
    symbols = []
    for s in result.symbols:
        symbol_dict = {
            "path": s.path,
            "symbol_name": s.symbol_name,
            "symbol_type": s.symbol_type,
            "line_start": s.line_start,
            "line_end": s.line_end,
            "is_exported": s.is_exported,
            "parameters": s.parameters,
        }
        # Only include parent_symbol and docstring if present
        if s.parent_symbol:
            symbol_dict["parent_symbol"] = s.parent_symbol
        if s.docstring:
            symbol_dict["docstring"] = s.docstring
        symbols.append(symbol_dict)

    calls = []
    for c in result.calls:
        call_dict = {
            "caller_file": c.caller_file,
            "caller_symbol": c.caller_symbol,
            "callee_symbol": c.callee_symbol,
            "line_number": c.line_number,
            "call_type": c.call_type,
        }
        # Only include callee_file if resolved
        if c.callee_file:
            call_dict["callee_file"] = c.callee_file
        # Only include is_dynamic_code_execution if true
        if c.is_dynamic_code_execution:
            call_dict["is_dynamic_code_execution"] = True
        # Only include callee_object if present
        if c.callee_object:
            call_dict["callee_object"] = c.callee_object
        calls.append(call_dict)

    imports = []
    for i in result.imports:
        import_dict = {
            "file": i.file,
            "imported_path": i.imported_path,
            "import_type": i.import_type,
            "line_number": i.line_number,
        }
        # Only include imported_symbols if present
        if i.imported_symbols:
            import_dict["imported_symbols"] = i.imported_symbols
        imports.append(import_dict)

    return {
        "metadata": {
            "tool_name": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "run_id": run_id,
            "repo_id": repo_id,
            "branch": branch,
            "commit": commit,
            "timestamp": timestamp,
            "schema_version": SCHEMA_VERSION,
        },
        "data": {
            "tool": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "symbols": symbols,
            "calls": calls,
            "imports": imports,
            "summary": result.summary,
        },
        "errors": result.errors if result.errors else [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract symbols, calls, and imports from Python source code"
    )
    parser.add_argument(
        "--repo-path",
        default=os.environ.get("REPO_PATH", "eval-repos/synthetic/simple-functions"),
        help="Path to repository to analyze",
    )
    parser.add_argument(
        "--repo-name",
        default=os.environ.get("REPO_NAME", ""),
        help="Repository name for output naming",
    )
    parser.add_argument(
        "--output-dir",
        default=os.environ.get("OUTPUT_DIR"),
        help="Directory to write analysis output (default: outputs/<run-id>)",
    )
    parser.add_argument(
        "--run-id",
        default=os.environ.get("RUN_ID", ""),
        help="Run identifier (required)",
    )
    parser.add_argument(
        "--repo-id",
        default=os.environ.get("REPO_ID", ""),
        help="Repository identifier (required)",
    )
    parser.add_argument(
        "--branch",
        default=os.environ.get("BRANCH", "main"),
        help="Branch analyzed",
    )
    parser.add_argument(
        "--commit",
        default=os.environ.get("COMMIT", ""),
        help="Commit SHA (default: repo HEAD)",
    )
    parser.add_argument(
        "--no-resolve-calls",
        action="store_true",
        help="Skip call resolution (Phase 1 behavior)",
    )
    parser.add_argument(
        "--strategy",
        choices=["ast", "treesitter"],
        default="ast",
        help="Extraction strategy: ast (default, uses Python AST module) or treesitter",
    )
    args = parser.parse_args()

    repo_path = Path(args.repo_path)
    if not repo_path.exists():
        raise FileNotFoundError(f"Repository not found at {repo_path}")

    repo_name = args.repo_name or repo_path.resolve().name
    print(f"Symbol Scanner v{TOOL_VERSION}")
    print()

    if not args.run_id:
        raise ValueError("--run-id is required")
    if not args.repo_id:
        raise ValueError("--repo-id is required")

    try:
        commit = _resolve_commit(repo_path.resolve(), args.commit, Path(__file__).parent.parent)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc

    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else Path("outputs") / args.run_id
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "output.json"

    print(f"Analyzing {repo_name}...")
    print(f"Repository: {repo_path.resolve()}")
    print()

    # Create extractor based on strategy
    if args.strategy == "treesitter":
        extractor = TreeSitterExtractor()
    else:
        extractor = PythonExtractor()
    resolve_calls = not args.no_resolve_calls
    result = extractor.extract_directory(
        repo_path.resolve(),
        repo_path.resolve(),
        resolve_calls=resolve_calls,
    )

    # Normalize paths
    repo_root = repo_path.resolve()
    for symbol in result.symbols:
        symbol.path = normalize_file_path(symbol.path, repo_root)
    for call in result.calls:
        call.caller_file = normalize_file_path(call.caller_file, repo_root)
        if call.callee_file:
            call.callee_file = normalize_file_path(call.callee_file, repo_root)
    for imp in result.imports:
        imp.file = normalize_file_path(imp.file, repo_root)

    # Build output envelope
    timestamp = datetime.now(timezone.utc).isoformat()
    envelope = build_output_envelope(
        result,
        run_id=args.run_id,
        repo_id=args.repo_id,
        branch=args.branch,
        commit=commit,
        timestamp=timestamp,
    )

    # Write output
    output_path.write_text(json.dumps(envelope, indent=2, default=str))

    # Print summary
    summary = result.summary
    print(f"Files analyzed: {summary['total_files']}")
    print(f"Symbols found: {summary['total_symbols']}")
    print(f"  - Functions: {summary['symbols_by_type'].get('function', 0)}")
    print(f"  - Classes: {summary['symbols_by_type'].get('class', 0)}")
    print(f"  - Methods: {summary['symbols_by_type'].get('method', 0)}")
    print(f"  - Variables: {summary['symbols_by_type'].get('variable', 0)}")
    print(f"Calls found: {summary['total_calls']}")
    print(f"  - Direct: {summary['calls_by_type'].get('direct', 0)}")
    print(f"  - Dynamic: {summary['calls_by_type'].get('dynamic', 0)}")
    print(f"  - Async: {summary['calls_by_type'].get('async', 0)}")
    if "resolution" in summary:
        res = summary["resolution"]
        print(f"  - Resolved: {res['total_resolved']}")
        print(f"    - Same file: {res['resolved_same_file']}")
        print(f"    - Cross file: {res['resolved_cross_file']}")
        print(f"  - Unresolved: {res['total_unresolved']}")
    print(f"Imports found: {summary['total_imports']}")
    print(f"  - Static: {summary['imports_by_type'].get('static', 0)}")
    print(f"  - Dynamic: {summary['imports_by_type'].get('dynamic', 0)}")
    if result.errors:
        print(f"Errors: {len(result.errors)}")
    print()
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
