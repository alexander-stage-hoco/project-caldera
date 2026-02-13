#!/usr/bin/env python3
"""CLI entry point for symbol-scanner tool."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

# Add shared src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from shared.path_utils import normalize_file_path
from common.git_utilities import is_fallback_commit, resolve_commit
from common.cli_parser import add_common_args, validate_common_args_raising, CommitResolutionConfig, ValidationError
from common.envelope_formatter import create_envelope, get_current_timestamp

from extractors import (
    PythonExtractor,
    TreeSitterExtractor,
    CSharpTreeSitterExtractor,
    CSharpRoslynExtractor,
    CSharpHybridExtractor,
    JavaScriptTreeSitterExtractor,
    TypeScriptTreeSitterExtractor,
)

TOOL_NAME = "symbol-scanner"
TOOL_VERSION = "0.1.0"
SCHEMA_VERSION = "1.0.0"


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

    data = {
        "tool": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "symbols": symbols,
        "calls": calls,
        "imports": imports,
        "summary": result.summary,
    }

    envelope = create_envelope(
        data,
        tool_name=TOOL_NAME,
        tool_version=TOOL_VERSION,
        run_id=run_id,
        repo_id=repo_id,
        branch=branch,
        commit=commit,
        timestamp=timestamp,
        schema_version=SCHEMA_VERSION,
    )
    # Add errors field outside standard envelope if present
    envelope["errors"] = result.errors if result.errors else []

    return envelope


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract symbols, calls, and imports from source code (Python, C#, JavaScript, TypeScript)"
    )
    add_common_args(parser, default_repo_path="eval-repos/synthetic/simple-functions")
    parser.add_argument(
        "--no-resolve-calls",
        action="store_true",
        help="Skip call resolution (Phase 1 behavior)",
    )
    parser.add_argument(
        "--language",
        choices=["python", "csharp", "javascript", "typescript"],
        default="python",
        help="Language to analyze: python (default), csharp, javascript, or typescript",
    )
    parser.add_argument(
        "--strategy",
        choices=["ast", "treesitter", "roslyn", "hybrid"],
        default="ast",
        help="Extraction strategy. Python: ast (default), treesitter. C#: treesitter, roslyn, hybrid (default for csharp). JS/TS: treesitter only.",
    )
    args = parser.parse_args()

    # Validate strategy for language
    if args.language == "python" and args.strategy in ("roslyn", "hybrid"):
        parser.error(f"Strategy '{args.strategy}' is not available for Python. Use 'ast' or 'treesitter'.")
    if args.language == "csharp" and args.strategy == "ast":
        # Default to hybrid for C# if ast was specified (the default)
        args.strategy = "hybrid"
    if args.language in ("javascript", "typescript") and args.strategy != "treesitter":
        # JS/TS only supports treesitter
        args.strategy = "treesitter"

    # Handle fallback commits specially - try to get real HEAD first
    if args.commit and is_fallback_commit(args.commit):
        args.commit = ""  # Let resolve_commit auto-detect HEAD

    commit_config = CommitResolutionConfig.strict_with_fallback(Path(__file__).parent.parent)
    common = validate_common_args_raising(args, commit_config=commit_config)

    print(f"Symbol Scanner v{TOOL_VERSION}")
    print()

    print(f"Analyzing {common.repo_name}...")
    print(f"Repository: {common.repo_path.resolve()}")
    print()

    # Create extractor based on language and strategy
    if args.language == "python":
        if args.strategy == "treesitter":
            extractor = TreeSitterExtractor()
        else:
            extractor = PythonExtractor()
    elif args.language == "csharp":
        if args.strategy == "treesitter":
            extractor = CSharpTreeSitterExtractor()
        elif args.strategy == "roslyn":
            extractor = CSharpRoslynExtractor()
        else:  # hybrid (default for C#)
            extractor = CSharpHybridExtractor()
    elif args.language == "javascript":
        extractor = JavaScriptTreeSitterExtractor()
    elif args.language == "typescript":
        extractor = TypeScriptTreeSitterExtractor()
    resolve_calls = not args.no_resolve_calls
    repo_root = common.repo_path.resolve()
    result = extractor.extract_directory(
        repo_root,
        repo_root,
        resolve_calls=resolve_calls,
    )

    # Normalize paths
    for symbol in result.symbols:
        symbol.path = normalize_file_path(symbol.path, repo_root)
    for call in result.calls:
        call.caller_file = normalize_file_path(call.caller_file, repo_root)
        if call.callee_file:
            call.callee_file = normalize_file_path(call.callee_file, repo_root)
    for imp in result.imports:
        imp.file = normalize_file_path(imp.file, repo_root)

    # Build output envelope
    timestamp = get_current_timestamp()
    envelope = build_output_envelope(
        result,
        run_id=common.run_id,
        repo_id=common.repo_id,
        branch=common.branch,
        commit=common.commit,
        timestamp=timestamp,
    )

    # Write output
    common.output_path.write_text(json.dumps(envelope, indent=2, default=str))

    # Print summary
    summary = result.summary
    print(f"Files analyzed: {summary['total_files']}")
    print(f"Symbols found: {summary['total_symbols']}")
    print(f"  - Functions: {summary['symbols_by_type'].get('function', 0)}")
    print(f"  - Classes: {summary['symbols_by_type'].get('class', 0)}")
    print(f"  - Methods: {summary['symbols_by_type'].get('method', 0)}")
    print(f"  - Variables: {summary['symbols_by_type'].get('variable', 0)}")
    # C#-specific symbol types
    if summary['symbols_by_type'].get('property', 0) > 0:
        print(f"  - Properties: {summary['symbols_by_type'].get('property', 0)}")
    if summary['symbols_by_type'].get('field', 0) > 0:
        print(f"  - Fields: {summary['symbols_by_type'].get('field', 0)}")
    if summary['symbols_by_type'].get('event', 0) > 0:
        print(f"  - Events: {summary['symbols_by_type'].get('event', 0)}")
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
    print(f"Output: {common.output_path}")


if __name__ == "__main__":
    main()
