#!/usr/bin/env python3
"""Evaluation harness for symbol-scanner extractors.

Compares extractor output against ground truth and reports precision/recall/F1 metrics.
Supports two modes:
1. Direct extractor evaluation: Run extractors on repos and compare to ground truth
2. Analysis file evaluation: Load output.json from analyze.py and compare to ground truth
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# =============================================================================
# Constants
# =============================================================================

PASS_THRESHOLD = 0.95  # >= 95% = PASS
WARN_THRESHOLD = 0.85  # 85-95% = WARN, < 85% = FAIL

LINE_TOLERANCE = 2  # +/- 2 lines for fuzzy line matching

SYMBOL_WEIGHTS = {
    "exported": 1.0,   # Public symbols (full weight)
    "private": 0.5,    # Private symbols (_prefix, half weight)
}

BASELINE_PATH = Path(__file__).parent.parent / "evaluation" / "baseline.json"


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class Metrics:
    """Precision/recall/F1 metrics for a category."""

    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    @property
    def precision(self) -> float:
        """Of what we extracted, how much was correct."""
        if self.true_positives + self.false_positives == 0:
            return 1.0 if self.false_negatives == 0 else 0.0
        return self.true_positives / (self.true_positives + self.false_positives)

    @property
    def recall(self) -> float:
        """Of what exists, how much did we find."""
        if self.true_positives + self.false_negatives == 0:
            return 1.0 if self.false_positives == 0 else 0.0
        return self.true_positives / (self.true_positives + self.false_negatives)

    @property
    def f1(self) -> float:
        """Harmonic mean of precision and recall."""
        p, r = self.precision, self.recall
        if p + r == 0:
            return 0.0
        return 2 * (p * r) / (p + r)

    def __add__(self, other: Metrics) -> Metrics:
        """Combine metrics from multiple categories."""
        return Metrics(
            true_positives=self.true_positives + other.true_positives,
            false_positives=self.false_positives + other.false_positives,
            false_negatives=self.false_negatives + other.false_negatives,
        )


@dataclass
class CategoryMetrics:
    """Metrics broken down by subcategory."""

    by_type: dict[str, Metrics] = field(default_factory=dict)
    total: Metrics = field(default_factory=Metrics)

    def add(self, type_name: str, metrics: Metrics) -> None:
        """Add metrics for a subcategory."""
        self.by_type[type_name] = metrics
        self.total = self.total + metrics


@dataclass
class DetailedResult:
    """Detailed result showing what was found vs expected."""

    found: list[dict] = field(default_factory=list)
    missing: list[dict] = field(default_factory=list)  # FN
    extra: list[dict] = field(default_factory=list)  # FP


@dataclass
class EvaluationResult:
    """Complete evaluation result for a single repo."""

    repo_name: str
    strategy: str
    symbols: CategoryMetrics = field(default_factory=CategoryMetrics)
    calls: CategoryMetrics = field(default_factory=CategoryMetrics)
    imports: CategoryMetrics = field(default_factory=CategoryMetrics)
    details: dict[str, DetailedResult] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def overall_f1(self) -> float:
        """Overall F1 across all categories."""
        combined = self.symbols.total + self.calls.total + self.imports.total
        return combined.f1


# ============================================================================
# Ground Truth Loading
# ============================================================================


def load_ground_truth(ground_truth_dir: Path, repo_name: str | None = None) -> dict[str, dict]:
    """Load ground truth files from directory.

    Args:
        ground_truth_dir: Path to ground-truth directory
        repo_name: Optional specific repo to load

    Returns:
        Dict mapping repo names to ground truth data
    """
    ground_truth = {}
    if repo_name:
        gt_file = ground_truth_dir / f"{repo_name}.json"
        if gt_file.exists():
            with open(gt_file) as f:
                ground_truth[repo_name] = json.load(f)
    else:
        for gt_file in ground_truth_dir.glob("*.json"):
            with open(gt_file) as f:
                ground_truth[gt_file.stem] = json.load(f)
    return ground_truth


# ============================================================================
# Extractor Running
# ============================================================================


def run_extractor(strategy: str, repo_path: Path) -> dict:
    """Run an extractor on a repository and return results.

    Args:
        strategy: Extractor strategy ("ast", "treesitter", or "hybrid")
        repo_path: Path to the repository

    Returns:
        Extraction result as dict
    """
    # Import here to avoid circular imports
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from scripts.extractors.base import ExtractionResult

    if strategy == "ast":
        from scripts.extractors.python_extractor import PythonExtractor

        extractor = PythonExtractor()
    elif strategy == "treesitter":
        from scripts.extractors.treesitter_extractor import TreeSitterExtractor

        extractor = TreeSitterExtractor()
    elif strategy == "hybrid":
        from scripts.extractors.hybrid_extractor import HybridExtractor

        extractor = HybridExtractor()
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    result = extractor.extract_directory(repo_path)
    return _extraction_result_to_dict(result)


def _extraction_result_to_dict(result: Any) -> dict:
    """Convert ExtractionResult to dict format matching ground truth."""
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
    }


# ============================================================================
# Comparison Functions
# ============================================================================


def _symbol_key(s: dict) -> tuple:
    """Create a comparison key for a symbol."""
    return (s["path"], s["symbol_name"], s.get("line_start"))


def _symbol_key_fuzzy(s: dict) -> tuple:
    """Create a fuzzy comparison key for a symbol (path + name only)."""
    return (s["path"], s["symbol_name"])


def _build_fuzzy_map(symbols: list[dict]) -> dict[tuple, list[dict]]:
    """Build a fuzzy map from symbols, grouping by (path, name).

    Args:
        symbols: List of symbol dicts

    Returns:
        Dict mapping fuzzy keys to lists of symbols with that key
    """
    fuzzy_map: dict[tuple, list[dict]] = {}
    for s in symbols:
        key = _symbol_key_fuzzy(s)
        fuzzy_map.setdefault(key, []).append(s)
    return fuzzy_map


def _find_matching_symbol(
    expected: dict,
    actual_map: dict[tuple, list[dict]],
    matched_actual_keys: set[tuple] | None = None,
) -> dict | None:
    """Find matching symbol with line tolerance.

    Uses fuzzy matching: matches on path + name, then verifies line_start
    is within LINE_TOLERANCE. When multiple symbols share the same fuzzy key,
    finds the best match by line number.

    Args:
        expected: Expected symbol to match
        actual_map: Map of fuzzy keys to lists of actual symbols
        matched_actual_keys: Set of already-matched symbol keys to exclude

    Returns:
        Matching actual symbol if found within tolerance, None otherwise
    """
    if matched_actual_keys is None:
        matched_actual_keys = set()

    fuzzy_key = _symbol_key_fuzzy(expected)
    if fuzzy_key not in actual_map:
        return None

    exp_line = expected.get("line_start", 0)
    candidates = actual_map[fuzzy_key]

    # Find best match: closest line within tolerance, not already matched
    best_match = None
    best_distance = float("inf")

    for actual in candidates:
        actual_key = _symbol_key(actual)
        if actual_key in matched_actual_keys:
            continue

        act_line = actual.get("line_start", 0)
        if exp_line is None or act_line is None:
            # If either line is None, consider it a match on name/path alone
            return actual

        distance = abs(exp_line - act_line)
        if distance <= LINE_TOLERANCE and distance < best_distance:
            best_match = actual
            best_distance = distance

    return best_match


def _get_symbol_weight(symbol: dict) -> float:
    """Get weight based on symbol visibility.

    Exported symbols have full weight (1.0), private symbols (_prefix) have
    reduced weight (0.5).

    Args:
        symbol: Symbol dict with is_exported field

    Returns:
        Weight value (1.0 for exported, 0.5 for private)
    """
    if symbol.get("is_exported", True):
        return SYMBOL_WEIGHTS["exported"]
    return SYMBOL_WEIGHTS["private"]


def _call_key(c: dict) -> tuple:
    """Create a comparison key for a call."""
    return (
        c["caller_file"],
        c["caller_symbol"],
        c["callee_symbol"],
        c.get("line_number"),
    )


def _import_key(i: dict) -> tuple:
    """Create a comparison key for an import."""
    return (i["file"], i["imported_path"], i.get("line_number"))


def compare_symbols(
    expected: list[dict], actual: list[dict], use_fuzzy_matching: bool = True
) -> tuple[CategoryMetrics, DetailedResult]:
    """Compare expected vs actual symbols.

    Uses fuzzy matching by default: symbols match if path and name match
    and line_start is within LINE_TOLERANCE (+/- 2 lines).

    Args:
        expected: Expected symbols from ground truth
        actual: Actual symbols from extractor
        use_fuzzy_matching: Whether to use fuzzy line matching (default True)

    Returns:
        Tuple of (CategoryMetrics, DetailedResult)
    """
    metrics = CategoryMetrics()
    details = DetailedResult()

    # Build maps for matching
    if use_fuzzy_matching:
        # Fuzzy: key by (path, name), but store lists for duplicate keys
        actual_fuzzy_map = _build_fuzzy_map(actual)
        matched_expected: set[tuple] = set()
        matched_actual: set[tuple] = set()

        # Match expected symbols using fuzzy matching
        for exp in expected:
            match = _find_matching_symbol(exp, actual_fuzzy_map, matched_actual)
            if match:
                matched_expected.add(_symbol_key(exp))
                matched_actual.add(_symbol_key(match))
                details.found.append(exp)
            else:
                details.missing.append(exp)

        # Find extra symbols (in actual but not matched)
        for act in actual:
            if _symbol_key(act) not in matched_actual:
                details.extra.append(act)
    else:
        # Exact matching (original behavior)
        expected_map = {_symbol_key(s): s for s in expected}
        actual_map = {_symbol_key(s): s for s in actual}

        for key, s in expected_map.items():
            if key in actual_map:
                details.found.append(s)
            else:
                details.missing.append(s)

        for key, s in actual_map.items():
            if key not in expected_map:
                details.extra.append(s)

    # Group by type for metrics (use fuzzy for matching if enabled)
    type_expected: dict[str, list[dict]] = {}
    type_actual: dict[str, list[dict]] = {}

    for s in expected:
        t = s.get("symbol_type", "unknown")
        type_expected.setdefault(t, []).append(s)

    for s in actual:
        t = s.get("symbol_type", "unknown")
        type_actual.setdefault(t, []).append(s)

    all_types = set(type_expected.keys()) | set(type_actual.keys())

    for symbol_type in sorted(all_types):
        exp_list = type_expected.get(symbol_type, [])
        act_list = type_actual.get(symbol_type, [])

        if use_fuzzy_matching:
            # Build fuzzy map for this type (handles duplicate keys)
            act_fuzzy = _build_fuzzy_map(act_list)
            tp = 0
            fn = 0
            matched_act_keys: set[tuple] = set()

            for exp in exp_list:
                match = _find_matching_symbol(exp, act_fuzzy, matched_act_keys)
                if match:
                    tp += 1
                    matched_act_keys.add(_symbol_key(match))
                else:
                    fn += 1

            # FP: actual symbols that weren't matched
            fp = len(act_list) - len(matched_act_keys)
        else:
            exp_keys = {_symbol_key(s) for s in exp_list}
            act_keys = {_symbol_key(s) for s in act_list}

            tp = len(exp_keys & act_keys)
            fp = len(act_keys - exp_keys)
            fn = len(exp_keys - act_keys)

        metrics.add(symbol_type, Metrics(tp, fp, fn))

    return metrics, details


def compute_weighted_f1(
    expected: list[dict], actual: list[dict]
) -> tuple[float, float, float]:
    """Compute weighted precision, recall, and F1 for symbols.

    Weighs exported symbols at 1.0 and private symbols at 0.5.

    Args:
        expected: Expected symbols from ground truth
        actual: Actual symbols from extractor

    Returns:
        Tuple of (weighted_precision, weighted_recall, weighted_f1)
    """
    actual_fuzzy_map = {_symbol_key_fuzzy(s): s for s in actual}

    # Calculate weighted TP, FP, FN
    weighted_tp = 0.0
    weighted_fn = 0.0
    weighted_fp = 0.0

    matched_actual: set[tuple] = set()

    for exp in expected:
        weight = _get_symbol_weight(exp)
        match = _find_matching_symbol(exp, actual_fuzzy_map)
        if match:
            weighted_tp += weight
            matched_actual.add(_symbol_key_fuzzy(match))
        else:
            weighted_fn += weight

    for act in actual:
        if _symbol_key_fuzzy(act) not in matched_actual:
            weighted_fp += _get_symbol_weight(act)

    # Calculate weighted precision/recall/F1
    if weighted_tp + weighted_fp == 0:
        w_precision = 1.0 if weighted_fn == 0 else 0.0
    else:
        w_precision = weighted_tp / (weighted_tp + weighted_fp)

    if weighted_tp + weighted_fn == 0:
        w_recall = 1.0 if weighted_fp == 0 else 0.0
    else:
        w_recall = weighted_tp / (weighted_tp + weighted_fn)

    if w_precision + w_recall == 0:
        w_f1 = 0.0
    else:
        w_f1 = 2 * (w_precision * w_recall) / (w_precision + w_recall)

    return w_precision, w_recall, w_f1


def compare_calls(
    expected: list[dict], actual: list[dict]
) -> tuple[CategoryMetrics, DetailedResult]:
    """Compare expected vs actual calls.

    Args:
        expected: Expected calls from ground truth
        actual: Actual calls from extractor

    Returns:
        Tuple of (CategoryMetrics, DetailedResult)
    """
    metrics = CategoryMetrics()
    details = DetailedResult()

    expected_map = {_call_key(c): c for c in expected}
    actual_map = {_call_key(c): c for c in actual}

    # Group by call type
    type_expected: dict[str, list[dict]] = {}
    type_actual: dict[str, list[dict]] = {}

    for c in expected:
        t = c.get("call_type", "unknown")
        type_expected.setdefault(t, []).append(c)

    for c in actual:
        t = c.get("call_type", "unknown")
        type_actual.setdefault(t, []).append(c)

    all_types = set(type_expected.keys()) | set(type_actual.keys())

    for call_type in sorted(all_types):
        exp_list = type_expected.get(call_type, [])
        act_list = type_actual.get(call_type, [])

        exp_keys = {_call_key(c) for c in exp_list}
        act_keys = {_call_key(c) for c in act_list}

        tp = len(exp_keys & act_keys)
        fp = len(act_keys - exp_keys)
        fn = len(exp_keys - act_keys)

        metrics.add(call_type, Metrics(tp, fp, fn))

    # Detailed results
    for key, c in expected_map.items():
        if key in actual_map:
            details.found.append(c)
        else:
            details.missing.append(c)

    for key, c in actual_map.items():
        if key not in expected_map:
            details.extra.append(c)

    return metrics, details


def compare_imports(
    expected: list[dict], actual: list[dict]
) -> tuple[CategoryMetrics, DetailedResult]:
    """Compare expected vs actual imports.

    Args:
        expected: Expected imports from ground truth
        actual: Actual imports from extractor

    Returns:
        Tuple of (CategoryMetrics, DetailedResult)
    """
    metrics = CategoryMetrics()
    details = DetailedResult()

    expected_map = {_import_key(i): i for i in expected}
    actual_map = {_import_key(i): i for i in actual}

    # Group by import type
    type_expected: dict[str, list[dict]] = {}
    type_actual: dict[str, list[dict]] = {}

    for i in expected:
        t = i.get("import_type", "unknown")
        type_expected.setdefault(t, []).append(i)

    for i in actual:
        t = i.get("import_type", "unknown")
        type_actual.setdefault(t, []).append(i)

    all_types = set(type_expected.keys()) | set(type_actual.keys())

    for import_type in sorted(all_types):
        exp_list = type_expected.get(import_type, [])
        act_list = type_actual.get(import_type, [])

        exp_keys = {_import_key(i) for i in exp_list}
        act_keys = {_import_key(i) for i in act_list}

        tp = len(exp_keys & act_keys)
        fp = len(act_keys - exp_keys)
        fn = len(exp_keys - act_keys)

        metrics.add(import_type, Metrics(tp, fp, fn))

    # Detailed results
    for key, i in expected_map.items():
        if key in actual_map:
            details.found.append(i)
        else:
            details.missing.append(i)

    for key, i in actual_map.items():
        if key not in expected_map:
            details.extra.append(i)

    return metrics, details


# ============================================================================
# Evaluation Functions
# ============================================================================


def evaluate_repo(
    strategy: str,
    repo_name: str,
    repo_path: Path,
    ground_truth: dict,
) -> EvaluationResult:
    """Evaluate a single repository.

    Args:
        strategy: Extractor strategy to use
        repo_name: Name of the repository
        repo_path: Path to the repository
        ground_truth: Ground truth data for the repo

    Returns:
        EvaluationResult with metrics and details
    """
    result = EvaluationResult(repo_name=repo_name, strategy=strategy)

    try:
        actual = run_extractor(strategy, repo_path)
    except Exception as e:
        result.errors.append(f"Extraction failed: {e}")
        return result

    expected = ground_truth.get("expected", {})

    # Compare symbols
    result.symbols, result.details["symbols"] = compare_symbols(
        expected.get("symbols", []), actual.get("symbols", [])
    )

    # Compare calls
    result.calls, result.details["calls"] = compare_calls(
        expected.get("calls", []), actual.get("calls", [])
    )

    # Compare imports
    result.imports, result.details["imports"] = compare_imports(
        expected.get("imports", []), actual.get("imports", [])
    )

    return result


# ============================================================================
# Output Formatting
# ============================================================================


def _format_metrics_row(
    name: str,
    expected: int,
    found: int,
    tp: int,
    fp: int,
    fn: int,
    p: float,
    r: float,
    f1: float,
) -> str:
    """Format a single metrics row."""
    return (
        f"  {name:<20} {expected:>8} {found:>8} {tp:>5} {fp:>5} {fn:>5} "
        f"{p:>5.2f} {r:>6.2f} {f1:>6.2f}"
    )


def format_results(result: EvaluationResult, verbose: bool = False) -> str:
    """Format evaluation results as a string.

    Args:
        result: Evaluation result to format
        verbose: Include detailed findings

    Returns:
        Formatted string
    """
    lines = []
    lines.append("=" * 80)
    lines.append(f"EVALUATION RESULTS: {result.repo_name}")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Strategy: {result.strategy}")
    lines.append("")

    # Symbols section
    lines.append(
        f"{'SYMBOLS':<22} {'Expected':>8} {'Found':>8} {'TP':>5} {'FP':>5} {'FN':>5} "
        f"{'P':>5} {'R':>6} {'F1':>6}"
    )
    lines.append("-" * 80)

    for type_name, metrics in sorted(result.symbols.by_type.items()):
        expected = metrics.true_positives + metrics.false_negatives
        found = metrics.true_positives + metrics.false_positives
        lines.append(
            _format_metrics_row(
                type_name,
                expected,
                found,
                metrics.true_positives,
                metrics.false_positives,
                metrics.false_negatives,
                metrics.precision,
                metrics.recall,
                metrics.f1,
            )
        )

    # Symbols total
    total = result.symbols.total
    expected = total.true_positives + total.false_negatives
    found = total.true_positives + total.false_positives
    lines.append(
        _format_metrics_row(
            "TOTAL",
            expected,
            found,
            total.true_positives,
            total.false_positives,
            total.false_negatives,
            total.precision,
            total.recall,
            total.f1,
        )
    )
    lines.append("")

    # Calls section
    if result.calls.by_type or result.details.get("calls", DetailedResult()).missing:
        lines.append(
            f"{'CALLS':<22} {'Expected':>8} {'Found':>8} {'TP':>5} {'FP':>5} {'FN':>5} "
            f"{'P':>5} {'R':>6} {'F1':>6}"
        )
        lines.append("-" * 80)

        for type_name, metrics in sorted(result.calls.by_type.items()):
            expected = metrics.true_positives + metrics.false_negatives
            found = metrics.true_positives + metrics.false_positives
            lines.append(
                _format_metrics_row(
                    type_name,
                    expected,
                    found,
                    metrics.true_positives,
                    metrics.false_positives,
                    metrics.false_negatives,
                    metrics.precision,
                    metrics.recall,
                    metrics.f1,
                )
            )

        total = result.calls.total
        expected = total.true_positives + total.false_negatives
        found = total.true_positives + total.false_positives
        lines.append(
            _format_metrics_row(
                "TOTAL",
                expected,
                found,
                total.true_positives,
                total.false_positives,
                total.false_negatives,
                total.precision,
                total.recall,
                total.f1,
            )
        )
        lines.append("")

    # Imports section
    if result.imports.by_type or result.details.get("imports", DetailedResult()).missing:
        lines.append(
            f"{'IMPORTS':<22} {'Expected':>8} {'Found':>8} {'TP':>5} {'FP':>5} {'FN':>5} "
            f"{'P':>5} {'R':>6} {'F1':>6}"
        )
        lines.append("-" * 80)

        for type_name, metrics in sorted(result.imports.by_type.items()):
            expected = metrics.true_positives + metrics.false_negatives
            found = metrics.true_positives + metrics.false_positives
            lines.append(
                _format_metrics_row(
                    type_name,
                    expected,
                    found,
                    metrics.true_positives,
                    metrics.false_positives,
                    metrics.false_negatives,
                    metrics.precision,
                    metrics.recall,
                    metrics.f1,
                )
            )

        total = result.imports.total
        expected = total.true_positives + total.false_negatives
        found = total.true_positives + total.false_positives
        lines.append(
            _format_metrics_row(
                "TOTAL",
                expected,
                found,
                total.true_positives,
                total.false_positives,
                total.false_negatives,
                total.precision,
                total.recall,
                total.f1,
            )
        )
        lines.append("")

    # Overall F1
    lines.append(f"OVERALL F1: {result.overall_f1:.2f}")
    lines.append("")

    # Verbose details
    if verbose:
        # Missing symbols
        missing_symbols = result.details.get("symbols", DetailedResult()).missing
        if missing_symbols:
            lines.append("Missed symbols:")
            for s in missing_symbols:
                lines.append(
                    f"  - {s['path']}:{s.get('line_start', '?')} "
                    f"{s['symbol_type']} '{s['symbol_name']}'"
                )
            lines.append("")

        # Extra symbols
        extra_symbols = result.details.get("symbols", DetailedResult()).extra
        if extra_symbols:
            lines.append("Extra symbols:")
            for s in extra_symbols:
                lines.append(
                    f"  - {s['path']}:{s.get('line_start', '?')} "
                    f"{s['symbol_type']} '{s['symbol_name']}'"
                )
            lines.append("")

        # Missing calls
        missing_calls = result.details.get("calls", DetailedResult()).missing
        if missing_calls:
            lines.append("Missed calls:")
            for c in missing_calls:
                lines.append(
                    f"  - {c['caller_file']}:{c.get('line_number', '?')} "
                    f"{c['caller_symbol']}->{c['callee_symbol']} ({c.get('call_type', '?')})"
                )
            lines.append("")

        # Extra calls
        extra_calls = result.details.get("calls", DetailedResult()).extra
        if extra_calls:
            lines.append("Extra calls:")
            for c in extra_calls:
                lines.append(
                    f"  - {c['caller_file']}:{c.get('line_number', '?')} "
                    f"{c['caller_symbol']}->{c['callee_symbol']} ({c.get('call_type', '?')})"
                )
            lines.append("")

        # Missing imports
        missing_imports = result.details.get("imports", DetailedResult()).missing
        if missing_imports:
            lines.append("Missed imports:")
            for i in missing_imports:
                lines.append(
                    f"  - {i['file']}:{i.get('line_number', '?')} "
                    f"'{i['imported_path']}' ({i.get('import_type', '?')})"
                )
            lines.append("")

        # Extra imports
        extra_imports = result.details.get("imports", DetailedResult()).extra
        if extra_imports:
            lines.append("Extra imports:")
            for i in extra_imports:
                lines.append(
                    f"  - {i['file']}:{i.get('line_number', '?')} "
                    f"'{i['imported_path']}' ({i.get('import_type', '?')})"
                )
            lines.append("")

    # Errors
    if result.errors:
        lines.append("Errors:")
        for error in result.errors:
            lines.append(f"  - {error}")
        lines.append("")

    return "\n".join(lines)


def format_summary(results: list[EvaluationResult]) -> str:
    """Format a summary of multiple evaluation results.

    Args:
        results: List of evaluation results

    Returns:
        Formatted summary string
    """
    lines = []
    lines.append("=" * 80)
    lines.append("EVALUATION SUMMARY")
    lines.append("=" * 80)
    lines.append("")
    lines.append(
        f"{'Repo':<30} {'Strategy':<12} {'Symbols F1':>12} {'Calls F1':>12} "
        f"{'Imports F1':>12} {'Overall F1':>12}"
    )
    lines.append("-" * 90)

    for result in sorted(results, key=lambda r: r.repo_name):
        lines.append(
            f"{result.repo_name:<30} {result.strategy:<12} "
            f"{result.symbols.total.f1:>12.2f} {result.calls.total.f1:>12.2f} "
            f"{result.imports.total.f1:>12.2f} {result.overall_f1:>12.2f}"
        )

    # Aggregate metrics
    all_symbols = Metrics()
    all_calls = Metrics()
    all_imports = Metrics()
    for result in results:
        all_symbols = all_symbols + result.symbols.total
        all_calls = all_calls + result.calls.total
        all_imports = all_imports + result.imports.total

    combined = all_symbols + all_calls + all_imports
    lines.append("-" * 90)
    lines.append(
        f"{'AGGREGATE':<30} {'':<12} "
        f"{all_symbols.f1:>12.2f} {all_calls.f1:>12.2f} "
        f"{all_imports.f1:>12.2f} {combined.f1:>12.2f}"
    )
    lines.append("")

    return "\n".join(lines)


def format_comparison(ast_results: list[EvaluationResult], ts_results: list[EvaluationResult]) -> str:
    """Format a comparison between AST and tree-sitter results.

    Args:
        ast_results: Results from AST extractor
        ts_results: Results from tree-sitter extractor

    Returns:
        Formatted comparison string
    """
    lines = []
    lines.append("=" * 100)
    lines.append("STRATEGY COMPARISON: AST vs Tree-sitter")
    lines.append("=" * 100)
    lines.append("")
    lines.append(
        f"{'Repo':<25} {'AST F1':>10} {'TS F1':>10} {'Diff':>10} {'Winner':>12}"
    )
    lines.append("-" * 67)

    ast_map = {r.repo_name: r for r in ast_results}
    ts_map = {r.repo_name: r for r in ts_results}

    all_repos = sorted(set(ast_map.keys()) | set(ts_map.keys()))

    ast_wins = 0
    ts_wins = 0
    ties = 0

    for repo in all_repos:
        ast_f1 = ast_map[repo].overall_f1 if repo in ast_map else 0.0
        ts_f1 = ts_map[repo].overall_f1 if repo in ts_map else 0.0
        diff = ast_f1 - ts_f1

        if abs(diff) < 0.01:
            winner = "TIE"
            ties += 1
        elif diff > 0:
            winner = "AST"
            ast_wins += 1
        else:
            winner = "Tree-sitter"
            ts_wins += 1

        lines.append(
            f"{repo:<25} {ast_f1:>10.2f} {ts_f1:>10.2f} {diff:>+10.2f} {winner:>12}"
        )

    lines.append("-" * 67)
    lines.append(f"AST wins: {ast_wins}  |  Tree-sitter wins: {ts_wins}  |  Ties: {ties}")
    lines.append("")

    return "\n".join(lines)


def result_to_json(result: EvaluationResult) -> dict:
    """Convert evaluation result to JSON-serializable dict.

    Args:
        result: Evaluation result

    Returns:
        JSON-serializable dictionary
    """

    def metrics_to_dict(m: Metrics) -> dict:
        return {
            "true_positives": m.true_positives,
            "false_positives": m.false_positives,
            "false_negatives": m.false_negatives,
            "precision": m.precision,
            "recall": m.recall,
            "f1": m.f1,
        }

    def category_to_dict(c: CategoryMetrics) -> dict:
        return {
            "by_type": {k: metrics_to_dict(v) for k, v in c.by_type.items()},
            "total": metrics_to_dict(c.total),
        }

    return {
        "repo_name": result.repo_name,
        "strategy": result.strategy,
        "overall_f1": result.overall_f1,
        "symbols": category_to_dict(result.symbols),
        "calls": category_to_dict(result.calls),
        "imports": category_to_dict(result.imports),
        "errors": result.errors,
    }


# ============================================================================
# Analysis Mode Functions
# ============================================================================


def compute_decision(score: float) -> str:
    """Compute PASS/WARN/FAIL decision based on score thresholds.

    Args:
        score: Overall F1 score (0.0 to 1.0)

    Returns:
        "PASS" if score >= 95%, "WARN" if 85-95%, "FAIL" if < 85%
    """
    if score >= PASS_THRESHOLD:
        return "PASS"
    elif score >= WARN_THRESHOLD:
        return "WARN"
    else:
        return "FAIL"


def load_baseline() -> dict | None:
    """Load baseline scores for regression detection.

    Returns:
        Baseline dict with scores if file exists, None otherwise
    """
    if BASELINE_PATH.exists():
        try:
            return json.loads(BASELINE_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return None
    return None


def check_regression(
    current_score: float,
    baseline: dict | None,
    threshold: float = 0.02,
) -> list[str]:
    """Check if current score regressed beyond threshold.

    Args:
        current_score: Current overall F1 score
        baseline: Baseline dict from load_baseline()
        threshold: Maximum allowed regression (default 2%)

    Returns:
        List of warning messages if regression detected
    """
    warnings = []
    if baseline and "overall_f1" in baseline:
        baseline_score = baseline["overall_f1"]
        delta = baseline_score - current_score
        if delta > threshold:
            warnings.append(
                f"REGRESSION: Score dropped from {baseline_score:.2%} to {current_score:.2%} "
                f"(delta: {delta:.2%}, threshold: {threshold:.2%})"
            )
        elif delta > 0:
            warnings.append(
                f"Minor regression: {baseline_score:.2%} -> {current_score:.2%} "
                f"(within threshold)"
            )
    return warnings


def save_baseline(report: dict) -> None:
    """Save current evaluation scores as new baseline.

    Args:
        report: Evaluation report dict from generate_evaluation_report
    """
    baseline = {
        "timestamp": report["timestamp"],
        "overall_f1": report["aggregate"]["overall_f1"],
        "symbols_f1": report["aggregate"]["symbols"]["f1"],
        "calls_f1": report["aggregate"]["calls"]["f1"],
        "imports_f1": report["aggregate"]["imports"]["f1"],
        "total_repos": report["summary"]["total_repos"],
        "passed": report["summary"]["passed"],
    }
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(json.dumps(baseline, indent=2))


def _analysis_to_comparable(analysis: dict) -> dict:
    """Convert analyze.py output format to comparable format.

    The analyze.py output has metadata and data sections. This extracts
    the data section and normalizes it to match ground truth format.

    Args:
        analysis: Output from analyze.py (with metadata/data envelope)

    Returns:
        Dict with symbols/calls/imports lists matching ground truth format
    """
    data = analysis.get("data", analysis)

    # Normalize symbols
    symbols = []
    for s in data.get("symbols", []):
        symbols.append({
            "path": s["path"],
            "symbol_name": s["symbol_name"],
            "symbol_type": s["symbol_type"],
            "line_start": s.get("line_start"),
            "is_exported": s.get("is_exported", True),
            "parameters": s.get("parameters"),
        })

    # Normalize calls
    calls = []
    for c in data.get("calls", []):
        calls.append({
            "caller_file": c["caller_file"],
            "caller_symbol": c["caller_symbol"],
            "callee_symbol": c["callee_symbol"],
            "callee_file": c.get("callee_file"),
            "line_number": c.get("line_number"),
            "call_type": c.get("call_type", "direct"),
        })

    # Normalize imports
    imports = []
    for i in data.get("imports", []):
        imports.append({
            "file": i["file"],
            "imported_path": i["imported_path"],
            "import_type": i.get("import_type", "static"),
            "line_number": i.get("line_number"),
            "imported_symbols": i.get("imported_symbols"),
        })

    return {
        "symbols": symbols,
        "calls": calls,
        "imports": imports,
    }


def _compute_aggregate(results: list[EvaluationResult]) -> dict:
    """Compute aggregate metrics across all evaluation results.

    Args:
        results: List of per-repo evaluation results

    Returns:
        Dict with aggregate precision/recall/F1 for each category and overall
    """
    all_symbols = Metrics()
    all_calls = Metrics()
    all_imports = Metrics()

    for result in results:
        all_symbols = all_symbols + result.symbols.total
        all_calls = all_calls + result.calls.total
        all_imports = all_imports + result.imports.total

    combined = all_symbols + all_calls + all_imports

    return {
        "symbols": {
            "precision": all_symbols.precision,
            "recall": all_symbols.recall,
            "f1": all_symbols.f1,
        },
        "calls": {
            "precision": all_calls.precision,
            "recall": all_calls.recall,
            "f1": all_calls.f1,
        },
        "imports": {
            "precision": all_imports.precision,
            "recall": all_imports.recall,
            "f1": all_imports.f1,
        },
        "overall_f1": combined.f1,
    }


def evaluate_from_analysis(
    analysis_path: Path,
    ground_truth_dir: Path,
    repos_dir: Path,
    verbose: bool = False,
) -> tuple[list[EvaluationResult], dict]:
    """Evaluate analysis output against all ground truth files.

    This mode runs the extractors on each ground truth repo and compares
    against expected values. It's meant for compliance evaluation where
    we need to test against the full ground truth suite.

    Args:
        analysis_path: Path to output.json from analyze.py (unused in current impl)
        ground_truth_dir: Path to ground truth directory
        repos_dir: Path to synthetic repos directory
        verbose: Whether to print verbose output

    Returns:
        Tuple of (list of EvaluationResult, metadata dict)
    """
    # Load all ground truth
    ground_truth = load_ground_truth(ground_truth_dir)
    if not ground_truth:
        raise ValueError(f"No ground truth found in {ground_truth_dir}")

    results: list[EvaluationResult] = []

    # Evaluate each repo using the hybrid strategy (best performer)
    strategy = "hybrid"
    for repo_name, gt_data in sorted(ground_truth.items()):
        repo_path = repos_dir / repo_name
        if not repo_path.exists():
            print(f"Warning: Repository {repo_name} not found at {repo_path}", file=sys.stderr)
            continue

        result = evaluate_repo(strategy, repo_name, repo_path, gt_data)
        results.append(result)

        if verbose:
            print(format_results(result, verbose=False))
            print()

    metadata = {
        "strategy": strategy,
        "ground_truth_dir": str(ground_truth_dir),
        "repos_dir": str(repos_dir),
    }

    return results, metadata


def generate_evaluation_report(
    results: list[EvaluationResult],
    metadata: dict | None = None,
) -> dict:
    """Generate evaluation report JSON structure.

    Args:
        results: List of per-repo evaluation results
        metadata: Optional metadata to include

    Returns:
        Complete evaluation report dict
    """
    aggregate = _compute_aggregate(results)
    overall_score = aggregate["overall_f1"]
    decision = compute_decision(overall_score)

    # Compute summary stats
    passed = sum(1 for r in results if compute_decision(r.overall_f1) == "PASS")
    warned = sum(1 for r in results if compute_decision(r.overall_f1) == "WARN")
    failed = sum(1 for r in results if compute_decision(r.overall_f1) == "FAIL")
    avg_f1 = sum(r.overall_f1 for r in results) / len(results) if results else 0.0

    # Build checks list for compliance (one check per repo)
    checks = []
    for result in results:
        repo_decision = compute_decision(result.overall_f1)
        checks.append({
            "check_id": f"repo.{result.repo_name}",
            "name": f"Repository: {result.repo_name}",
            "passed": repo_decision != "FAIL",
            "message": f"F1={result.overall_f1:.2%}, {repo_decision}",
            "expected": f">= {WARN_THRESHOLD:.0%}",
            "actual": f"{result.overall_f1:.2%}",
            "evidence": {
                "symbols_f1": result.symbols.total.f1,
                "calls_f1": result.calls.total.f1,
                "imports_f1": result.imports.total.f1,
                "overall_f1": result.overall_f1,
                "decision": repo_decision,
            },
        })

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "score": round(overall_score, 4),
        "checks": checks,
        "summary": {
            "total_repos": len(results),
            "passed": passed,
            "warned": warned,
            "failed": failed,
            "average_f1": round(avg_f1, 4),
        },
        "aggregate": {
            "symbols": {
                "precision": round(aggregate["symbols"]["precision"], 4),
                "recall": round(aggregate["symbols"]["recall"], 4),
                "f1": round(aggregate["symbols"]["f1"], 4),
            },
            "calls": {
                "precision": round(aggregate["calls"]["precision"], 4),
                "recall": round(aggregate["calls"]["recall"], 4),
                "f1": round(aggregate["calls"]["f1"], 4),
            },
            "imports": {
                "precision": round(aggregate["imports"]["precision"], 4),
                "recall": round(aggregate["imports"]["recall"], 4),
                "f1": round(aggregate["imports"]["f1"], 4),
            },
            "overall_f1": round(aggregate["overall_f1"], 4),
        },
        "per_repo_results": [result_to_json(r) for r in results],
        "metadata": metadata or {},
    }


def generate_scorecard_md(report: dict) -> str:
    """Generate markdown scorecard from evaluation report.

    Args:
        report: Evaluation report dict from generate_evaluation_report

    Returns:
        Markdown string for scorecard.md
    """
    decision = report["decision"]
    score_pct = report["score"] * 100
    summary = report["summary"]
    aggregate = report["aggregate"]

    # Decision emoji
    decision_emoji = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(decision, "❓")

    lines = [
        "# Symbol Scanner Evaluation Scorecard",
        "",
        f"**Decision:** {decision_emoji} {decision}",
        f"**Score:** {score_pct:.1f}%",
        f"**Timestamp:** {report['timestamp']}",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total Repos | {summary['total_repos']} |",
        f"| Passed | {summary['passed']} |",
        f"| Warned | {summary['warned']} |",
        f"| Failed | {summary['failed']} |",
        f"| Average F1 | {summary['average_f1']:.2%} |",
        "",
        "## Aggregate Metrics",
        "",
        "| Category | Precision | Recall | F1 |",
        "|----------|-----------|--------|-----|",
        f"| Symbols | {aggregate['symbols']['precision']:.2%} | {aggregate['symbols']['recall']:.2%} | {aggregate['symbols']['f1']:.2%} |",
        f"| Calls | {aggregate['calls']['precision']:.2%} | {aggregate['calls']['recall']:.2%} | {aggregate['calls']['f1']:.2%} |",
        f"| Imports | {aggregate['imports']['precision']:.2%} | {aggregate['imports']['recall']:.2%} | {aggregate['imports']['f1']:.2%} |",
        f"| **Overall** | - | - | **{aggregate['overall_f1']:.2%}** |",
        "",
        "## Per-Repository Results",
        "",
        "| Repository | Symbols F1 | Calls F1 | Imports F1 | Overall F1 | Status |",
        "|------------|------------|----------|------------|------------|--------|",
    ]

    for result in report["per_repo_results"]:
        repo_name = result["repo_name"]
        symbols_f1 = result["symbols"]["total"]["f1"]
        calls_f1 = result["calls"]["total"]["f1"]
        imports_f1 = result["imports"]["total"]["f1"]
        overall_f1 = result["overall_f1"]
        status = compute_decision(overall_f1)
        status_emoji = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(status, "❓")

        lines.append(
            f"| {repo_name} | {symbols_f1:.2%} | {calls_f1:.2%} | {imports_f1:.2%} | {overall_f1:.2%} | {status_emoji} |"
        )

    lines.extend([
        "",
        "## Thresholds",
        "",
        f"- **PASS:** ≥ {PASS_THRESHOLD:.0%}",
        f"- **WARN:** {WARN_THRESHOLD:.0%} - {PASS_THRESHOLD:.0%}",
        f"- **FAIL:** < {WARN_THRESHOLD:.0%}",
        "",
    ])

    return "\n".join(lines)


# ============================================================================
# CLI
# ============================================================================


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate symbol-scanner extractors against ground truth"
    )
    parser.add_argument(
        "--strategy",
        choices=["ast", "treesitter", "hybrid"],
        default="ast",
        help="Extractor strategy to use (default: ast)",
    )
    parser.add_argument(
        "--repo",
        help="Specific repository to evaluate (by name)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Evaluate all repositories with ground truth",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare AST and tree-sitter strategies",
    )
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=Path(__file__).parent.parent / "evaluation" / "ground-truth",
        help="Path to ground truth directory",
    )
    parser.add_argument(
        "--repos-dir",
        type=Path,
        default=Path(__file__).parent.parent / "eval-repos" / "synthetic",
        help="Path to synthetic repos directory",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed results (missed/extra items)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write results to file (evaluation_report.json for --analysis mode)",
    )
    # Analysis mode arguments (for Makefile evaluate target)
    parser.add_argument(
        "--analysis",
        type=Path,
        help="Path to output.json from analyze.py (enables analysis mode)",
    )
    parser.add_argument(
        "--scorecard",
        type=Path,
        help="Directory to save scorecard.md (used with --analysis)",
    )
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Save current scores as new baseline for regression detection",
    )
    parser.add_argument(
        "--no-regression-check",
        action="store_true",
        help="Skip regression check against baseline",
    )
    args = parser.parse_args()

    # Analysis mode: evaluate against all ground truth and generate report
    if args.analysis:
        print("Running evaluation in analysis mode...")
        print(f"Ground truth: {args.ground_truth}")
        print(f"Repos dir: {args.repos_dir}")
        print()

        results, metadata = evaluate_from_analysis(
            analysis_path=args.analysis,
            ground_truth_dir=args.ground_truth,
            repos_dir=args.repos_dir,
            verbose=args.verbose,
        )

        if not results:
            print("No repositories evaluated.", file=sys.stderr)
            sys.exit(1)

        # Generate report
        report = generate_evaluation_report(results, metadata)

        # Print summary
        print(format_summary(results))
        print()
        print(f"Decision: {report['decision']}")
        print(f"Score: {report['score']:.2%}")

        # Check for regression against baseline
        regression_warnings = []
        if not args.no_regression_check:
            baseline = load_baseline()
            if baseline:
                print(f"\nBaseline: {baseline.get('overall_f1', 0):.2%} ({baseline.get('timestamp', 'unknown')})")
                regression_warnings = check_regression(report["score"], baseline)
                for warning in regression_warnings:
                    print(f"  {warning}", file=sys.stderr)
            else:
                print("\nNo baseline found. Use --save-baseline to create one.")

        # Save evaluation report
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            # Include regression info in report
            report["regression"] = {
                "baseline_found": load_baseline() is not None,
                "warnings": regression_warnings,
            }
            with open(args.output, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\nEvaluation report saved to {args.output}")

        # Save scorecard
        if args.scorecard:
            scorecard_path = args.scorecard / "scorecard.md"
            args.scorecard.mkdir(parents=True, exist_ok=True)
            scorecard_md = generate_scorecard_md(report)
            scorecard_path.write_text(scorecard_md)
            print(f"Scorecard saved to {scorecard_path}")

        # Save baseline if requested
        if args.save_baseline:
            save_baseline(report)
            print(f"Baseline saved to {BASELINE_PATH}")

        # Exit with appropriate code based on decision or regression
        if report["decision"] == "FAIL":
            sys.exit(1)
        if regression_warnings and any("REGRESSION:" in w for w in regression_warnings):
            print("\nExiting with error due to regression.", file=sys.stderr)
            sys.exit(1)
        return

    # Legacy mode: require one of the traditional arguments
    if not args.repo and not args.all and not args.compare:
        parser.error("Must specify --repo, --all, --compare, or --analysis")

    # Load ground truth
    ground_truth = load_ground_truth(args.ground_truth, args.repo if not args.all else None)
    if not ground_truth:
        print(f"No ground truth found in {args.ground_truth}", file=sys.stderr)
        sys.exit(1)

    results: list[EvaluationResult] = []

    if args.compare:
        # Run both strategies
        ast_results = []
        ts_results = []

        for repo_name, gt_data in ground_truth.items():
            repo_path = args.repos_dir / repo_name
            if not repo_path.exists():
                print(f"Warning: Repository {repo_name} not found at {repo_path}", file=sys.stderr)
                continue

            ast_result = evaluate_repo("ast", repo_name, repo_path, gt_data)
            ast_results.append(ast_result)

            ts_result = evaluate_repo("treesitter", repo_name, repo_path, gt_data)
            ts_results.append(ts_result)

        if args.json:
            output = {
                "ast": [result_to_json(r) for r in ast_results],
                "treesitter": [result_to_json(r) for r in ts_results],
            }
            print(json.dumps(output, indent=2))
        else:
            print(format_comparison(ast_results, ts_results))
            print(format_summary(ast_results))
            print(format_summary(ts_results))

    elif args.all:
        # Run specified strategy on all repos
        for repo_name, gt_data in ground_truth.items():
            repo_path = args.repos_dir / repo_name
            if not repo_path.exists():
                print(f"Warning: Repository {repo_name} not found at {repo_path}", file=sys.stderr)
                continue

            result = evaluate_repo(args.strategy, repo_name, repo_path, gt_data)
            results.append(result)

        if args.json:
            output = [result_to_json(r) for r in results]
            print(json.dumps(output, indent=2))
        else:
            for result in results:
                print(format_results(result, verbose=args.verbose))
                print()
            print(format_summary(results))

    else:
        # Single repo
        if args.repo not in ground_truth:
            print(f"No ground truth for repository: {args.repo}", file=sys.stderr)
            sys.exit(1)

        repo_path = args.repos_dir / args.repo
        if not repo_path.exists():
            print(f"Repository not found: {repo_path}", file=sys.stderr)
            sys.exit(1)

        result = evaluate_repo(args.strategy, args.repo, repo_path, ground_truth[args.repo])

        if args.json:
            print(json.dumps(result_to_json(result), indent=2))
        else:
            print(format_results(result, verbose=args.verbose))

    # Write to file if specified (legacy mode)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            if results:
                json.dump([result_to_json(r) for r in results], f, indent=2)
            else:
                json.dump(result_to_json(result), f, indent=2)
        print(f"Results written to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
