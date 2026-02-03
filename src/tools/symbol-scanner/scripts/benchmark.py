#!/usr/bin/env python3
"""Benchmark AST vs Tree-sitter extractors.

Compares performance, accuracy, and error handling between the two extraction
strategies.
"""

from __future__ import annotations

import argparse
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import sys

sys.path.insert(0, str(Path(__file__).parent))

from extractors import PythonExtractor, TreeSitterExtractor
from extractors.base import ExtractionResult

if TYPE_CHECKING:
    from extractors.base import BaseExtractor


@dataclass
class BenchmarkResult:
    """Results from benchmarking a single extractor."""

    strategy: str
    times: list[float]
    symbols: int
    calls: int
    imports: int
    errors: int

    @property
    def mean_time(self) -> float:
        return statistics.mean(self.times)

    @property
    def median_time(self) -> float:
        return statistics.median(self.times)

    @property
    def stdev_time(self) -> float:
        return statistics.stdev(self.times) if len(self.times) > 1 else 0.0

    @property
    def min_time(self) -> float:
        return min(self.times)

    @property
    def max_time(self) -> float:
        return max(self.times)


@dataclass
class ComparisonResult:
    """Comparison between two extraction results."""

    symbols_match: bool
    calls_match: bool
    imports_match: bool
    symbol_diff: list[str]
    call_diff: list[str]
    import_diff: list[str]

    @property
    def all_match(self) -> bool:
        return self.symbols_match and self.calls_match and self.imports_match

    @property
    def accuracy_percent(self) -> float:
        """Calculate overall accuracy as percentage."""
        matches = sum([self.symbols_match, self.calls_match, self.imports_match])
        return (matches / 3) * 100


def benchmark_extractor(
    extractor: BaseExtractor,
    repo_path: Path,
    iterations: int = 5,
) -> tuple[BenchmarkResult, ExtractionResult]:
    """Benchmark an extractor over multiple iterations.

    Args:
        extractor: Extractor instance to benchmark
        repo_path: Path to repository to analyze
        iterations: Number of iterations to run

    Returns:
        Tuple of (benchmark results, final extraction result)
    """
    times = []
    result = None

    for _ in range(iterations):
        start = time.perf_counter()
        result = extractor.extract_directory(repo_path, resolve_calls=False)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    assert result is not None

    strategy = "treesitter" if isinstance(extractor, TreeSitterExtractor) else "ast"

    return BenchmarkResult(
        strategy=strategy,
        times=times,
        symbols=len(result.symbols),
        calls=len(result.calls),
        imports=len(result.imports),
        errors=len(result.errors),
    ), result


def compare_results(
    ast_result: ExtractionResult,
    ts_result: ExtractionResult,
) -> ComparisonResult:
    """Compare extraction results for accuracy.

    Args:
        ast_result: Result from AST extractor
        ts_result: Result from tree-sitter extractor

    Returns:
        Comparison result with diff details
    """
    # Compare symbols by (path, name, type)
    ast_symbols = {
        (s.path, s.symbol_name, s.symbol_type)
        for s in ast_result.symbols
    }
    ts_symbols = {
        (s.path, s.symbol_name, s.symbol_type)
        for s in ts_result.symbols
    }

    symbol_only_ast = ast_symbols - ts_symbols
    symbol_only_ts = ts_symbols - ast_symbols
    symbols_match = ast_symbols == ts_symbols
    symbol_diff = []
    if symbol_only_ast:
        symbol_diff.append(f"Only in AST: {symbol_only_ast}")
    if symbol_only_ts:
        symbol_diff.append(f"Only in tree-sitter: {symbol_only_ts}")

    # Compare calls by (caller_file, caller_symbol, callee_symbol, line)
    ast_calls = {
        (c.caller_file, c.caller_symbol, c.callee_symbol, c.line_number)
        for c in ast_result.calls
    }
    ts_calls = {
        (c.caller_file, c.caller_symbol, c.callee_symbol, c.line_number)
        for c in ts_result.calls
    }

    call_only_ast = ast_calls - ts_calls
    call_only_ts = ts_calls - ast_calls
    calls_match = ast_calls == ts_calls
    call_diff = []
    if call_only_ast:
        call_diff.append(f"Only in AST: {call_only_ast}")
    if call_only_ts:
        call_diff.append(f"Only in tree-sitter: {call_only_ts}")

    # Compare imports by (file, path, symbols)
    ast_imports = {
        (i.file, i.imported_path, i.imported_symbols)
        for i in ast_result.imports
    }
    ts_imports = {
        (i.file, i.imported_path, i.imported_symbols)
        for i in ts_result.imports
    }

    import_only_ast = ast_imports - ts_imports
    import_only_ts = ts_imports - ast_imports
    imports_match = ast_imports == ts_imports
    import_diff = []
    if import_only_ast:
        import_diff.append(f"Only in AST: {import_only_ast}")
    if import_only_ts:
        import_diff.append(f"Only in tree-sitter: {import_only_ts}")

    return ComparisonResult(
        symbols_match=symbols_match,
        calls_match=calls_match,
        imports_match=imports_match,
        symbol_diff=symbol_diff,
        call_diff=call_diff,
        import_diff=import_diff,
    )


def format_time(seconds: float) -> str:
    """Format time as milliseconds with 2 decimal places."""
    return f"{seconds * 1000:.2f}"


def print_benchmark_table(
    ast_bench: BenchmarkResult,
    ts_bench: BenchmarkResult,
    comparison: ComparisonResult,
) -> None:
    """Print formatted benchmark comparison table."""
    print("\n" + "=" * 75)
    print("BENCHMARK RESULTS")
    print("=" * 75)

    # Header
    print(f"\n{'Strategy':<12} | {'Time (ms)':<12} | {'Symbols':<8} | {'Calls':<8} | {'Imports':<8} | {'Errors':<6}")
    print("-" * 75)

    # AST row
    print(
        f"{'ast':<12} | "
        f"{format_time(ast_bench.mean_time):>12} | "
        f"{ast_bench.symbols:>8} | "
        f"{ast_bench.calls:>8} | "
        f"{ast_bench.imports:>8} | "
        f"{ast_bench.errors:>6}"
    )

    # Tree-sitter row
    print(
        f"{'treesitter':<12} | "
        f"{format_time(ts_bench.mean_time):>12} | "
        f"{ts_bench.symbols:>8} | "
        f"{ts_bench.calls:>8} | "
        f"{ts_bench.imports:>8} | "
        f"{ts_bench.errors:>6}"
    )

    print("-" * 75)

    # Timing details
    print("\nTiming Details (ms):")
    print(f"  AST:         mean={format_time(ast_bench.mean_time)}, "
          f"median={format_time(ast_bench.median_time)}, "
          f"stdev={format_time(ast_bench.stdev_time)}, "
          f"min={format_time(ast_bench.min_time)}, "
          f"max={format_time(ast_bench.max_time)}")
    print(f"  Tree-sitter: mean={format_time(ts_bench.mean_time)}, "
          f"median={format_time(ts_bench.median_time)}, "
          f"stdev={format_time(ts_bench.stdev_time)}, "
          f"min={format_time(ts_bench.min_time)}, "
          f"max={format_time(ts_bench.max_time)}")

    # Speedup
    if ts_bench.mean_time > 0 and ast_bench.mean_time > 0:
        if ts_bench.mean_time < ast_bench.mean_time:
            speedup = ast_bench.mean_time / ts_bench.mean_time
            print(f"\nTree-sitter is {speedup:.2f}x faster than AST")
        else:
            speedup = ts_bench.mean_time / ast_bench.mean_time
            print(f"\nAST is {speedup:.2f}x faster than tree-sitter")

    # Accuracy
    print("\n" + "-" * 75)
    print("ACCURACY COMPARISON")
    print("-" * 75)

    if comparison.all_match:
        print("\n  All entities match between AST and tree-sitter extractors!")
        print(f"  Accuracy: 100%")
    else:
        print(f"\n  Accuracy: {comparison.accuracy_percent:.1f}%")
        print(f"  Symbols match: {comparison.symbols_match}")
        print(f"  Calls match: {comparison.calls_match}")
        print(f"  Imports match: {comparison.imports_match}")

        if comparison.symbol_diff:
            print("\n  Symbol differences:")
            for diff in comparison.symbol_diff:
                print(f"    {diff}")

        if comparison.call_diff:
            print("\n  Call differences:")
            for diff in comparison.call_diff:
                print(f"    {diff}")

        if comparison.import_diff:
            print("\n  Import differences:")
            for diff in comparison.import_diff:
                print(f"    {diff}")

    print("\n" + "=" * 75)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark AST vs Tree-sitter extractors"
    )
    parser.add_argument(
        "--repo-path",
        default="eval-repos/synthetic/cross-module-calls",
        help="Path to repository to analyze",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=5,
        help="Number of benchmark iterations (default: 5)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output",
    )
    args = parser.parse_args()

    repo_path = Path(args.repo_path)
    if not repo_path.exists():
        print(f"Error: Repository not found at {repo_path}")
        sys.exit(1)

    print(f"Benchmarking extractors on: {repo_path}")
    print(f"Iterations: {args.iterations}")

    # Initialize extractors
    ast_extractor = PythonExtractor()
    ts_extractor = TreeSitterExtractor()

    # Run benchmarks
    print("\nRunning AST extractor...")
    ast_bench, ast_result = benchmark_extractor(
        ast_extractor, repo_path, args.iterations
    )

    print("Running tree-sitter extractor...")
    ts_bench, ts_result = benchmark_extractor(
        ts_extractor, repo_path, args.iterations
    )

    # Compare results
    print("Comparing results...")
    comparison = compare_results(ast_result, ts_result)

    # Print results
    print_benchmark_table(ast_bench, ts_bench, comparison)

    # Verbose output
    if args.verbose:
        print("\nAST Extraction Details:")
        print(f"  Symbols: {[s.symbol_name for s in ast_result.symbols]}")
        print(f"  Calls: {[(c.caller_symbol, c.callee_symbol) for c in ast_result.calls]}")
        print(f"  Imports: {[i.imported_path for i in ast_result.imports]}")

        print("\nTree-sitter Extraction Details:")
        print(f"  Symbols: {[s.symbol_name for s in ts_result.symbols]}")
        print(f"  Calls: {[(c.caller_symbol, c.callee_symbol) for c in ts_result.calls]}")
        print(f"  Imports: {[i.imported_path for i in ts_result.imports]}")


if __name__ == "__main__":
    main()
