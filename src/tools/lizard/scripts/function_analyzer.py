#!/usr/bin/env python3
"""Function-level complexity analysis using Lizard.

Outputs per-function metrics including cyclomatic complexity (CCN), NLOC,
token count, and parameter count. Includes 12-section dashboard visualization.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import shutil
import statistics
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import lizard


# =============================================================================
# File Exclusion Patterns
# =============================================================================

# Path-based patterns for files to exclude (fnmatch syntax)
EXCLUDE_PATTERNS = [
    # Minified files
    '*.min.js', '*.min.css', '*.min.ts',

    # Bundled/compiled output
    '*.bundle.js', '*.chunk.js', '*.umd.js',

    # Common vendor libraries by name
    'jquery*.js', 'jquery-ui*.js', 'bootstrap*.js',
    'angular*.js', 'react*.js', 'vue*.js',
    'lodash*.js', 'moment*.js', 'd3*.js',

    # Generated code
    '*.designer.cs', '*.Designer.cs', '*.g.cs', '*.generated.*',
    '*_pb2.py', '*.pb.go', '*_pb2_grpc.py',
    '*.d.ts',  # TypeScript declarations (often generated)

    # Source maps (not code but often large)
    '*.map',
]

# Languages where content-based minification detection should be applied
MINIFICATION_CHECK_LANGUAGES = {'JavaScript', 'TypeScript'}


def matches_exclude_pattern(filepath: Path, patterns: list[str]) -> str | None:
    """Check if a filepath matches any of the exclusion patterns.

    Args:
        filepath: Path to the file
        patterns: List of fnmatch-style patterns

    Returns:
        The matched pattern if file matches any exclusion pattern, None otherwise
    """
    filename = filepath.name
    for pattern in patterns:
        if fnmatch.fnmatch(filename, pattern):
            return pattern
    return None


def is_likely_minified(filepath: Path, sample_size: int = 8192) -> bool:
    """Detect minified files via content heuristics.

    Minified files typically have:
    - Very long lines (>500 chars average)
    - Few newlines relative to file size
    - Single lines >1000 chars in first few lines

    Args:
        filepath: Path to the file to check
        sample_size: Number of bytes to read for analysis

    Returns:
        True if the file appears to be minified
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(sample_size)

        if not content:
            return False

        lines = content.split('\n')
        if not lines:
            return False

        # Heuristic 1: Average line length > 500 chars
        avg_line_length = len(content) / len(lines)
        if avg_line_length > 500:
            return True

        # Heuristic 2: Single line > 1000 chars in first 10 lines
        for line in lines[:10]:
            if len(line) > 1000:
                return True

        # Heuristic 3: Very few newlines (< 1 per 500 chars)
        newline_ratio = len(lines) / len(content) if content else 0
        if newline_ratio < 0.002:  # < 1 newline per 500 chars
            return True

        return False
    except Exception:
        return False  # If we can't read it, don't exclude

# Add shared src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from common.git_utilities import resolve_commit
from common.envelope_formatter import create_envelope


# =============================================================================
# Terminal Colors and Formatting
# =============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_CYAN = "\033[96m"


_use_color = True


def set_color_enabled(enabled: bool):
    """Enable or disable color output."""
    global _use_color
    _use_color = enabled


def get_terminal_width(default: int = 120, minimum: int = 80) -> int:
    """Get terminal width with auto-detection."""
    try:
        columns, _ = shutil.get_terminal_size()
        return max(columns, minimum)
    except Exception:
        return default


def c(text: str, *codes: str) -> str:
    """Apply color codes to text if colors are enabled."""
    if not _use_color:
        return str(text)
    prefix = "".join(codes)
    return f"{prefix}{text}{Colors.RESET}"


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    import re
    return re.sub(r'\033\[[0-9;]*m', '', text)


def truncate_path_middle(path: str, max_len: int) -> str:
    """Truncate path in the middle, preserving start and end."""
    if len(path) <= max_len:
        return path
    ellipsis = "..."
    available = max_len - len(ellipsis)
    keep_start = available // 3
    keep_end = available - keep_start
    return path[:keep_start] + ellipsis + path[-keep_end:]


def format_number(n: float, decimals: int = 0) -> str:
    """Format a number with commas."""
    if decimals == 0:
        return f"{int(n):,}"
    return f"{n:,.{decimals}f}"


# Box drawing characters
BOX_TL = "┌"
BOX_TR = "┐"
BOX_BL = "└"
BOX_BR = "┘"
BOX_H = "─"
BOX_V = "│"
BOX_ML = "├"
BOX_MR = "┤"

HDR_TL = "╭"
HDR_TR = "╮"
HDR_BL = "╰"
HDR_BR = "╯"


# =============================================================================
# Progress Reporter
# =============================================================================

class ProgressReporter:
    """Simple progress reporter for terminal output."""

    def __init__(self, enabled: bool = True, interval: float = 1.0):
        """Initialize the progress reporter.

        Args:
            enabled: Whether to show progress output
            interval: Minimum seconds between progress updates
        """
        self.enabled = enabled
        self.interval = interval
        self._last_update = 0.0
        self._phase_start = 0.0
        self._total_start = 0.0
        self._phases: list[tuple[str, float]] = []
        self._current_phase = ""

    def start(self) -> None:
        """Start the overall timer."""
        self._total_start = time.perf_counter()

    def phase(self, name: str) -> None:
        """Start a new phase, recording the previous one's duration."""
        now = time.perf_counter()
        if self._current_phase:
            self._phases.append((self._current_phase, now - self._phase_start))
        self._phase_start = now
        self._current_phase = name
        if self.enabled:
            print(f"  [{name}]", flush=True)

    def progress(self, current: int, total: int) -> None:
        """Show progress (rate-limited to self.interval)."""
        if not self.enabled or total == 0:
            return
        now = time.perf_counter()
        if now - self._last_update < self.interval:
            return
        self._last_update = now

        elapsed = now - self._phase_start
        rate = current / elapsed if elapsed > 0 else 0
        remaining = total - current
        eta = remaining / rate if rate > 0 else 0
        pct = current / total * 100

        # In-place update with carriage return
        print(f"\r    {current:,}/{total:,} ({pct:.0f}%) | {rate:.1f} files/s | ETA: {eta:.0f}s   ", end="", flush=True)

    def end_progress(self) -> None:
        """End progress line (print newline)."""
        if self.enabled:
            print()  # Move to next line

    def finish(self) -> None:
        """Finish and print timing breakdown."""
        now = time.perf_counter()
        if self._current_phase:
            self._phases.append((self._current_phase, now - self._phase_start))

        total = now - self._total_start

        if self.enabled and self._phases:
            print(f"\n  Timing:")
            for phase_name, duration in self._phases:
                pct = duration / total * 100 if total > 0 else 0
                print(f"    {phase_name}: {duration:.1f}s ({pct:.0f}%)")
            print(f"    Total: {total:.1f}s")


def print_header(title: str, width: int = 80):
    """Print a header box."""
    inner_width = width - 4
    print(c(HDR_TL + "─" * (width - 2) + HDR_TR, Colors.CYAN))
    print(c(f"{BOX_V}  {title:<{inner_width}}{BOX_V}", Colors.CYAN))
    print(c(HDR_BL + "─" * (width - 2) + HDR_BR, Colors.CYAN))


def print_section(title: str, width: int = 80):
    """Print a section header."""
    inner_width = width - 4
    print()
    print(c(BOX_TL + BOX_H * (width - 2) + BOX_TR, Colors.BLUE))
    print(c(f"{BOX_V}  {title:<{inner_width}}{BOX_V}", Colors.BLUE, Colors.BOLD))
    print(c(BOX_ML + BOX_H * (width - 2) + BOX_MR, Colors.BLUE))


def print_section_end(width: int = 80):
    """Print section end border."""
    print(c(BOX_BL + BOX_H * (width - 2) + BOX_BR, Colors.BLUE))


def print_row(label: str, value: str, label2: str = "", value2: str = "", width: int = 80):
    """Print a row in a section."""
    inner_width = width - 4

    if label2:
        col_width = inner_width // 2
        left = f"{c(label, Colors.DIM)} {value}"
        right = f"{c(label2, Colors.DIM)} {value2}"
        left_visible = len(strip_ansi(left))
        right_visible = len(strip_ansi(right))
        left_padded = left + " " * (col_width - left_visible)
        right_padded = right + " " * (col_width - right_visible)
        line = f"  {left_padded}{right_padded}"
    else:
        content = f"{c(label, Colors.DIM)} {value}"
        visible_len = len(strip_ansi(content))
        line = f"  {content}" + " " * (inner_width - visible_len - 2)

    print(c(BOX_V, Colors.BLUE) + line + c(BOX_V, Colors.BLUE))


def print_empty_row(width: int = 80):
    """Print an empty row."""
    print(c(BOX_V, Colors.BLUE) + " " * (width - 2) + c(BOX_V, Colors.BLUE))


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class ExcludedFile:
    """Information about an excluded file."""
    path: str           # Repo-relative path
    reason: str         # 'pattern', 'minified', 'large', 'language'
    language: str       # Detected language (if applicable)
    details: str = ""   # Additional info (e.g., matched pattern, file size)


@dataclass
class FunctionInfo:
    """Information about a single function."""
    name: str
    long_name: str
    start_line: int
    end_line: int
    nloc: int
    ccn: int
    token_count: int
    parameter_count: int
    length: int


@dataclass
class FileInfo:
    """Information about a single file."""
    path: str
    language: str
    nloc: int
    functions: List[FunctionInfo] = field(default_factory=list)
    function_count: int = 0
    total_ccn: int = 0
    avg_ccn: float = 0.0
    max_ccn: int = 0


@dataclass
class Distribution:
    """Distribution statistics for a metric (22 metrics total)."""
    count: int = 0
    # Basic stats
    min: float = 0.0
    max: float = 0.0
    mean: float = 0.0
    median: float = 0.0
    stddev: float = 0.0
    # Percentiles
    p25: float = 0.0
    p50: float = 0.0
    p75: float = 0.0
    p90: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    # Shape metrics
    skewness: float = 0.0
    kurtosis: float = 0.0
    cv: float = 0.0  # Coefficient of variation
    iqr: float = 0.0  # Interquartile range
    # Inequality metrics
    gini: float = 0.0
    theil: float = 0.0
    hoover: float = 0.0
    palma: float = 0.0  # Ratio of top 10% to bottom 40%
    top_10_pct_share: float = 0.0
    top_20_pct_share: float = 0.0
    bottom_50_pct_share: float = 0.0


@dataclass
class DirectoryStats:
    """Statistics for a directory (direct or recursive)."""
    file_count: int = 0
    function_count: int = 0
    nloc: int = 0
    ccn: int = 0
    avg_ccn: float = 0.0
    max_ccn: int = 0
    avg_nloc: float = 0.0
    max_nloc: int = 0
    avg_params: float = 0.0
    max_params: int = 0
    functions_over_threshold: int = 0
    ccn_distribution: Distribution | None = None
    nloc_distribution: Distribution | None = None
    params_distribution: Distribution | None = None


@dataclass
class DirectoryInfo:
    """Information about a directory with both direct and recursive stats."""
    path: str
    name: str
    depth: int
    is_leaf: bool
    child_count: int
    direct: DirectoryStats = field(default_factory=DirectoryStats)
    recursive: DirectoryStats = field(default_factory=DirectoryStats)
    subdirectories: List[str] = field(default_factory=list)


@dataclass
class DirectoryStructure:
    """Overall directory structure metadata."""
    max_depth: int = 0
    avg_depth: float = 0.0
    leaf_directory_count: int = 0
    avg_functions_per_directory: float = 0.0


@dataclass
class AnalysisSummary:
    """Summary of the analysis."""
    total_files: int = 0
    total_functions: int = 0
    total_nloc: int = 0
    total_ccn: int = 0
    avg_ccn: float = 0.0
    max_ccn: int = 0
    functions_over_threshold: int = 0
    ccn_threshold: int = 10
    total_directories: int = 0
    # Excluded file counts
    excluded_count: int = 0
    excluded_by_pattern: int = 0
    excluded_by_minified: int = 0
    excluded_by_size: int = 0
    excluded_by_language: int = 0
    structure: DirectoryStructure | None = None
    ccn_distribution: Distribution | None = None
    nloc_distribution: Distribution | None = None


@dataclass
class AnalysisResult:
    """Full analysis result (v2.0 schema, aligned with TOOL_REQUIREMENTS.md)."""
    # Root-level fields per TOOL_REQUIREMENTS.md
    schema_version: str = "2.0.0"
    generated_at: str = ""
    repo_name: str = ""
    repo_path: str = ""
    repo_id: str = ""
    branch: str = ""
    commit: str = ""
    # Tool-specific results
    run_id: str = ""
    timestamp: str = ""
    root_path: str = ""
    directories: List[DirectoryInfo] = field(default_factory=list)
    files: List[FileInfo] = field(default_factory=list)
    excluded_files: List[ExcludedFile] = field(default_factory=list)
    summary: AnalysisSummary | None = None
    by_language: Dict[str, Dict] = field(default_factory=dict)


# =============================================================================
# Statistics Functions
# =============================================================================

def compute_distribution(values: List[float]) -> Distribution:
    """Compute distribution statistics for a list of values (22 metrics)."""
    if not values:
        return Distribution()

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    total = sum(values)
    mean_val = statistics.mean(values)
    stddev_val = statistics.stdev(values) if n > 1 else 0.0

    # Percentiles helper
    def percentile(p: float) -> float:
        idx = int(p / 100.0 * (n - 1))
        return sorted_vals[min(idx, n - 1)]

    p25 = percentile(25)
    p50 = percentile(50)
    p75 = percentile(75)
    p90 = percentile(90)
    p95 = percentile(95)
    p99 = percentile(99)

    # Shape metrics
    skewness = compute_skewness(values, mean_val, stddev_val) if n > 2 else 0.0
    kurtosis = compute_kurtosis(values, mean_val, stddev_val) if n > 3 else 0.0
    cv = stddev_val / mean_val if mean_val > 0 else 0.0
    iqr = p75 - p25

    # Inequality metrics
    gini = compute_gini(values)
    theil = compute_theil(values) if total > 0 else 0.0
    hoover = compute_hoover(values) if total > 0 else 0.0

    # Share metrics
    top_10_pct_share = compute_top_share(sorted_vals, 0.10) if total > 0 else 0.0
    top_20_pct_share = compute_top_share(sorted_vals, 0.20) if total > 0 else 0.0
    bottom_50_pct_share = compute_bottom_share(sorted_vals, 0.50) if total > 0 else 0.0

    # Palma ratio (top 10% / bottom 40%)
    palma = compute_palma(sorted_vals) if total > 0 else 0.0

    return Distribution(
        count=n,
        min=min(values),
        max=max(values),
        mean=mean_val,
        median=statistics.median(values),
        stddev=stddev_val,
        p25=p25,
        p50=p50,
        p75=p75,
        p90=p90,
        p95=p95,
        p99=p99,
        skewness=skewness,
        kurtosis=kurtosis,
        cv=cv,
        iqr=iqr,
        gini=gini,
        theil=theil,
        hoover=hoover,
        palma=palma,
        top_10_pct_share=top_10_pct_share,
        top_20_pct_share=top_20_pct_share,
        bottom_50_pct_share=bottom_50_pct_share,
    )


def compute_gini(values: List[float]) -> float:
    """Compute Gini coefficient (0 = equality, 1 = inequality)."""
    if not values or sum(values) == 0:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    cumsum = 0.0
    for i, val in enumerate(sorted_vals):
        cumsum += (2 * (i + 1) - n - 1) * val
    return cumsum / (n * sum(sorted_vals))


def compute_skewness(values: List[float], mean: float, stddev: float) -> float:
    """Compute Fisher-Pearson skewness coefficient."""
    if stddev == 0 or len(values) < 3:
        return 0.0
    n = len(values)
    m3 = sum((x - mean) ** 3 for x in values) / n
    return m3 / (stddev ** 3)


def compute_kurtosis(values: List[float], mean: float, stddev: float) -> float:
    """Compute excess kurtosis (Fisher's definition, normal = 0)."""
    if stddev == 0 or len(values) < 4:
        return 0.0
    n = len(values)
    m4 = sum((x - mean) ** 4 for x in values) / n
    return (m4 / (stddev ** 4)) - 3


def compute_theil(values: List[float]) -> float:
    """Compute Theil index (entropy-based inequality measure)."""
    if not values:
        return 0.0
    total = sum(values)
    if total == 0:
        return 0.0
    n = len(values)
    mean_val = total / n
    if mean_val == 0:
        return 0.0
    theil_sum = 0.0
    for x in values:
        if x > 0:
            ratio = x / mean_val
            theil_sum += ratio * (ratio if ratio > 0 else 0)
    # Actually compute Theil T index
    import math
    theil_t = 0.0
    for x in values:
        if x > 0:
            ratio = x / mean_val
            theil_t += ratio * math.log(ratio)
    return theil_t / n


def compute_hoover(values: List[float]) -> float:
    """Compute Hoover index (Robin Hood index)."""
    if not values:
        return 0.0
    total = sum(values)
    if total == 0:
        return 0.0
    mean_val = total / len(values)
    return sum(abs(x - mean_val) for x in values) / (2 * total)


def compute_top_share(sorted_vals: List[float], fraction: float) -> float:
    """Compute share of total held by top fraction."""
    if not sorted_vals:
        return 0.0
    total = sum(sorted_vals)
    if total == 0:
        return 0.0
    n = len(sorted_vals)
    top_count = max(1, int(n * fraction))
    top_sum = sum(sorted_vals[-top_count:])
    return top_sum / total


def compute_bottom_share(sorted_vals: List[float], fraction: float) -> float:
    """Compute share of total held by bottom fraction."""
    if not sorted_vals:
        return 0.0
    total = sum(sorted_vals)
    if total == 0:
        return 0.0
    n = len(sorted_vals)
    bottom_count = max(1, int(n * fraction))
    bottom_sum = sum(sorted_vals[:bottom_count])
    return bottom_sum / total


def compute_palma(sorted_vals: List[float]) -> float:
    """Compute Palma ratio (top 10% / bottom 40%)."""
    if not sorted_vals:
        return 0.0
    n = len(sorted_vals)
    top_10_count = max(1, int(n * 0.10))
    bottom_40_count = max(1, int(n * 0.40))
    top_10_sum = sum(sorted_vals[-top_10_count:])
    bottom_40_sum = sum(sorted_vals[:bottom_40_count])
    if bottom_40_sum == 0:
        return float('inf') if top_10_sum > 0 else 0.0
    return top_10_sum / bottom_40_sum


# =============================================================================
# Directory Analysis Functions
# =============================================================================

def compute_directory_stats(
    functions: List[FunctionInfo],
    files: List[FileInfo],
    ccn_threshold: int = 10
) -> DirectoryStats:
    """Compute aggregate statistics for a list of functions from files in a directory."""
    if not functions:
        return DirectoryStats()

    ccn_values = [f.ccn for f in functions]
    nloc_values = [f.nloc for f in functions]
    param_values = [f.parameter_count for f in functions]

    return DirectoryStats(
        file_count=len(files),
        function_count=len(functions),
        nloc=sum(nloc_values),
        ccn=sum(ccn_values),
        avg_ccn=statistics.mean(ccn_values) if ccn_values else 0.0,
        max_ccn=max(ccn_values) if ccn_values else 0,
        avg_nloc=statistics.mean(nloc_values) if nloc_values else 0.0,
        max_nloc=max(nloc_values) if nloc_values else 0,
        avg_params=statistics.mean(param_values) if param_values else 0.0,
        max_params=max(param_values) if param_values else 0,
        functions_over_threshold=sum(1 for c in ccn_values if c > ccn_threshold),
        ccn_distribution=compute_distribution(ccn_values) if ccn_values else None,
        nloc_distribution=compute_distribution(nloc_values) if nloc_values else None,
        params_distribution=compute_distribution(param_values) if param_values else None,
    )


def analyze_directories(
    files: List[FileInfo],
    root_path: str,
    ccn_threshold: int = 10
) -> tuple[List[DirectoryInfo], DirectoryStructure]:
    """Analyze directory structure with both direct and recursive stats.

    Uses bottom-up aggregation for O(n) complexity instead of O(n × depth).
    Directories are processed from leaves to root, with each directory's
    recursive stats computed by aggregating its direct stats plus cached
    child stats.

    Returns:
        Tuple of (list of DirectoryInfo, DirectoryStructure metadata)
    """
    if not files:
        return [], DirectoryStructure()

    root = Path(root_path)

    # Build a mapping of directory -> direct files
    dir_to_files: Dict[str, List[FileInfo]] = defaultdict(list)
    all_dirs: set[str] = set()

    for f in files:
        file_path = Path(f.path)
        # Get relative path from root
        try:
            rel_path = file_path.relative_to(root)
            parent_dir = str(rel_path.parent) if rel_path.parent != Path('.') else '.'
        except ValueError:
            # File is not under root, use absolute parent
            parent_dir = str(file_path.parent)

        dir_to_files[parent_dir].append(f)

        # Track all directories in the path
        parts = Path(parent_dir).parts
        for i in range(len(parts) + 1):
            if i == 0:
                all_dirs.add('.')
            else:
                all_dirs.add(str(Path(*parts[:i])))

    # Build parent-child relationships
    dir_children: Dict[str, List[str]] = defaultdict(list)
    for d in all_dirs:
        if d == '.':
            continue
        parent = str(Path(d).parent) if Path(d).parent != Path('.') else '.'
        if parent in all_dirs:
            dir_children[parent].append(d)

    # Helper to get all functions in a directory (direct only)
    def get_direct_functions(dir_path: str) -> List[FunctionInfo]:
        functions = []
        for f in dir_to_files.get(dir_path, []):
            functions.extend(f.functions)
        return functions

    # Process directories bottom-up (leaves first) for O(n) aggregation
    # Sort by depth descending so children are processed before parents
    sorted_dirs = sorted(all_dirs, key=lambda d: d.count('/') if d != '.' else -1, reverse=True)

    # Cache for recursive data: {dir_path: (files, functions)}
    recursive_cache: Dict[str, tuple[List[FileInfo], List[FunctionInfo]]] = {}

    for dir_path in sorted_dirs:
        direct_files = dir_to_files.get(dir_path, [])
        direct_functions = get_direct_functions(dir_path)

        # Start with direct data
        recursive_files = list(direct_files)
        recursive_functions = list(direct_functions)

        # Aggregate from already-computed children
        for child in dir_children.get(dir_path, []):
            child_files, child_funcs = recursive_cache[child]
            recursive_files.extend(child_files)
            recursive_functions.extend(child_funcs)

        recursive_cache[dir_path] = (recursive_files, recursive_functions)

    # Build DirectoryInfo objects
    directory_infos: List[DirectoryInfo] = []
    depths: List[int] = []

    for dir_path in sorted(all_dirs):
        depth = 0 if dir_path == '.' else len(Path(dir_path).parts)
        depths.append(depth)

        direct_files = dir_to_files.get(dir_path, [])
        direct_functions = get_direct_functions(dir_path)
        recursive_files, recursive_functions = recursive_cache[dir_path]

        children = dir_children.get(dir_path, [])
        is_leaf = len(children) == 0

        dir_info = DirectoryInfo(
            path=dir_path,
            name=Path(dir_path).name if dir_path != '.' else root.name,
            depth=depth,
            is_leaf=is_leaf,
            child_count=len(children),
            direct=compute_directory_stats(direct_functions, direct_files, ccn_threshold),
            recursive=compute_directory_stats(recursive_functions, recursive_files, ccn_threshold),
            subdirectories=sorted(children),
        )
        directory_infos.append(dir_info)

    # Compute structure metadata
    dirs_with_functions = [d for d in directory_infos if d.direct.function_count > 0]
    structure = DirectoryStructure(
        max_depth=max(depths) if depths else 0,
        avg_depth=statistics.mean(depths) if depths else 0.0,
        leaf_directory_count=sum(1 for d in directory_infos if d.is_leaf),
        avg_functions_per_directory=statistics.mean([d.direct.function_count for d in dirs_with_functions]) if dirs_with_functions else 0.0,
    )

    return directory_infos, structure


# =============================================================================
# Analysis Functions
# =============================================================================

def get_lizard_version() -> str:
    """Get the lizard version."""
    try:
        return f"lizard {lizard.version}"
    except AttributeError:
        return "lizard (version unknown)"


def detect_language(filename: str) -> str:
    """Detect language from file extension."""
    ext_map = {
        '.py': 'Python',
        '.cs': 'C#',
        '.java': 'Java',
        '.js': 'JavaScript',
        '.jsx': 'JavaScript',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript',
        '.go': 'Go',
        '.rs': 'Rust',
        '.c': 'C',
        '.h': 'C',
        '.cpp': 'C++',
        '.hpp': 'C++',
        '.cc': 'C++',
        '.php': 'PHP',
        '.rb': 'Ruby',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
    }
    ext = Path(filename).suffix.lower()
    return ext_map.get(ext, 'Unknown')


def analyze_directory(
    target_path: str,
    threads: int = None,
    exclude_tests: bool = True,
    languages: List[str] = None,
    max_file_size_kb: int = 500,
    show_progress: bool = True,
    extra_exclude_patterns: List[str] = None,
    detect_minified: bool = True,
    include_vendor: bool = False,
) -> AnalysisResult:
    """Analyze all files in a directory using Lizard.

    Args:
        target_path: Path to directory to analyze
        threads: Number of threads (default: CPU count)
        exclude_tests: Exclude test directories (default: True)
        languages: List of languages to include (e.g., ['C#', 'Python'])
        max_file_size_kb: Skip files larger than this (default: 500KB)
        show_progress: Show progress during analysis (default: True)
        extra_exclude_patterns: Additional filename patterns to exclude (fnmatch syntax)
        detect_minified: Enable content-based minified file detection (default: True)
        include_vendor: Include vendor/library files (default: False)
    """
    import multiprocessing
    target = Path(target_path)
    now = datetime.now(timezone.utc)
    run_id = f"fn-{now.strftime('%Y%m%d-%H%M%S')}"
    timestamp = now.isoformat()

    # Get repo_name from environment or derive from path
    repo_name = os.environ.get("REPO_NAME", "") or target.name

    # Default to half of logical CPU count (approximates physical cores), max 4
    # This avoids thread thrashing on machines with hyperthreading
    if threads is None:
        threads = min(multiprocessing.cpu_count() // 2 or 1, 4)

    result = AnalysisResult(
        # Root-level fields per TOOL_REQUIREMENTS.md
        generated_at=timestamp,
        repo_name=repo_name,
        repo_path=str(target),
        # Tool-specific results
        run_id=run_id,
        timestamp=timestamp,
        root_path=str(target),
    )

    # Initialize progress reporter
    reporter = ProgressReporter(enabled=show_progress)
    reporter.start()
    reporter.phase("Discovering files")

    # Directories to always exclude
    exclude_dirs = {
        '__pycache__', 'bin', 'obj',
        '.git', '.vs', '.idea', 'TestResults',
        'wwwroot', 'dist', 'build', 'coverage', 'artifacts',
        '.venv', 'venv', 'env', 'virtualenv',  # Virtual environments
    }

    # Vendor directories (excluded by default, can be included with --include-vendor)
    vendor_dirs = {
        'node_modules', 'vendor', 'packages', 'bower_components',
        'jspm_packages', 'lib', 'libs', 'third_party', 'thirdparty',
        'external', 'externals',
    }

    if not include_vendor:
        exclude_dirs.update(vendor_dirs)

    # Optionally exclude test directories
    if exclude_tests:
        exclude_dirs.update({
            'test', 'tests', 'Test', 'Tests',
            'UnitTests', 'IntegrationTests', 'Benchmarks',
            '__tests__', 'spec', 'specs',
        })

    # Build combined exclusion patterns list
    all_exclude_patterns = list(EXCLUDE_PATTERNS)
    if extra_exclude_patterns:
        all_exclude_patterns.extend(extra_exclude_patterns)

    # Build language filter set (lowercase for comparison)
    lang_filter = None
    if languages:
        lang_filter = {lang.lower() for lang in languages}

    # Check for incremental analysis (CHANGED_FILES env var)
    changed_files_env = os.environ.get("CHANGED_FILES", "").strip()
    incremental_mode = bool(changed_files_env)
    changed_files_set = None
    if incremental_mode:
        changed_files_set = set(f.strip() for f in changed_files_env.split('\n') if f.strip())
        if changed_files_set:
            print(f"  Incremental mode: {len(changed_files_set)} changed files to analyze")
        else:
            # No changed files, return empty result
            print("  Incremental mode: no changed files to analyze")
            return result

    # Collect all source files and track excluded files
    source_files = []
    excluded_files: List[ExcludedFile] = []
    max_size_bytes = max_file_size_kb * 1024

    for root, dirs, files in os.walk(target):
        # Skip excluded directories (in-place modification)
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in exclude_dirs]

        for f in files:
            filepath = Path(root) / f
            lang = detect_language(str(filepath))

            if lang == 'Unknown':
                continue

            # Get repo-relative path for tracking
            try:
                rel_path = str(filepath.relative_to(target))
            except ValueError:
                rel_path = str(filepath)

            # Filter by language if specified
            if lang_filter and lang.lower() not in lang_filter:
                excluded_files.append(ExcludedFile(
                    path=rel_path,
                    reason='language',
                    language=lang,
                    details=f"filtered (not in {', '.join(languages)})"
                ))
                continue

            # Skip files matching exclusion patterns (minified, vendor libs, generated)
            matched_pattern = matches_exclude_pattern(filepath, all_exclude_patterns)
            if matched_pattern:
                excluded_files.append(ExcludedFile(
                    path=rel_path,
                    reason='pattern',
                    language=lang,
                    details=matched_pattern
                ))
                continue

            # Content-based minification detection for JS/TS files
            if detect_minified and lang in MINIFICATION_CHECK_LANGUAGES:
                if is_likely_minified(filepath):
                    excluded_files.append(ExcludedFile(
                        path=rel_path,
                        reason='minified',
                        language=lang,
                        details='content-based detection'
                    ))
                    continue

            # Skip very large files
            try:
                file_size = filepath.stat().st_size
                if file_size > max_size_bytes:
                    size_mb = file_size / (1024 * 1024)
                    excluded_files.append(ExcludedFile(
                        path=rel_path,
                        reason='large',
                        language=lang,
                        details=f"{size_mb:.1f}MB > {max_file_size_kb}KB limit"
                    ))
                    continue
            except OSError:
                continue

            # Filter by changed files in incremental mode
            if incremental_mode and changed_files_set:
                if rel_path not in changed_files_set:
                    continue

            source_files.append(str(filepath))

    # Compute exclusion counts for progress reporting
    excluded_by_pattern = sum(1 for e in excluded_files if e.reason == 'pattern')
    excluded_by_minified = sum(1 for e in excluded_files if e.reason == 'minified')
    excluded_by_size = sum(1 for e in excluded_files if e.reason == 'large')
    excluded_by_language = sum(1 for e in excluded_files if e.reason == 'language')

    # Report discovery results
    if show_progress:
        skip_info = []
        if excluded_by_pattern > 0:
            skip_info.append(f"{excluded_by_pattern} vendor/generated")
        if excluded_by_minified > 0:
            skip_info.append(f"{excluded_by_minified} minified")
        if excluded_by_size > 0:
            skip_info.append(f"{excluded_by_size} large")
        if excluded_by_language > 0:
            skip_info.append(f"{excluded_by_language} filtered")
        skip_str = f" (skipped: {', '.join(skip_info)})" if skip_info else ""
        print(f"    Found {len(source_files):,} source files{skip_str}")

    if not source_files:
        reporter.finish()
        return result

    reporter.phase("Analyzing functions")
    if show_progress:
        print(f"    {len(source_files):,} files with {threads} threads...")

    # Analyze with Lizard
    analysis = lizard.analyze(source_files, threads=threads)
    total_files = len(source_files)

    all_functions = []
    by_language = defaultdict(lambda: {
        'files': 0, 'functions': 0, 'nloc': 0, 'ccn': 0,
        'avg_ccn': 0.0, 'max_ccn': 0
    })

    files_processed = 0
    for file_analysis in analysis:
        language = detect_language(file_analysis.filename)

        functions = []
        file_ccn = 0
        file_max_ccn = 0

        for func in file_analysis.function_list:
            func_info = FunctionInfo(
                name=func.name,
                long_name=func.long_name,
                start_line=func.start_line,
                end_line=func.end_line,
                nloc=func.nloc,
                ccn=func.cyclomatic_complexity,
                token_count=func.token_count,
                parameter_count=len(func.parameters) if hasattr(func, 'parameters') else func.parameter_count,
                length=func.length,
            )
            functions.append(func_info)
            all_functions.append(func_info)
            file_ccn += func.cyclomatic_complexity
            file_max_ccn = max(file_max_ccn, func.cyclomatic_complexity)

        file_info = FileInfo(
            path=file_analysis.filename,
            language=language,
            nloc=file_analysis.nloc,
            functions=functions,
            function_count=len(functions),
            total_ccn=file_ccn,
            avg_ccn=file_ccn / len(functions) if functions else 0.0,
            max_ccn=file_max_ccn,
        )
        result.files.append(file_info)

        # Aggregate by language
        lang_stats = by_language[language]
        lang_stats['files'] += 1
        lang_stats['functions'] += len(functions)
        lang_stats['nloc'] += file_analysis.nloc
        lang_stats['ccn'] += file_ccn
        lang_stats['max_ccn'] = max(lang_stats['max_ccn'], file_max_ccn)

        # Update progress
        files_processed += 1
        reporter.progress(files_processed, total_files)

    reporter.end_progress()

    # Compute language averages
    for lang, stats in by_language.items():
        if stats['functions'] > 0:
            stats['avg_ccn'] = stats['ccn'] / stats['functions']

    result.by_language = dict(by_language)

    reporter.phase("Computing directory stats")

    # Compute summary
    ccn_values = [f.ccn for f in all_functions]
    nloc_values = [f.nloc for f in all_functions]
    ccn_threshold = 10

    # Analyze directory structure
    directories, dir_structure = analyze_directories(result.files, str(target), ccn_threshold)
    result.directories = directories

    reporter.phase("Finalizing")

    # Store excluded files in result
    result.excluded_files = excluded_files

    result.summary = AnalysisSummary(
        total_files=len(result.files),
        total_functions=len(all_functions),
        total_nloc=sum(f.nloc for f in result.files),
        total_ccn=sum(ccn_values) if ccn_values else 0,
        avg_ccn=statistics.mean(ccn_values) if ccn_values else 0.0,
        max_ccn=max(ccn_values) if ccn_values else 0,
        functions_over_threshold=sum(1 for c in ccn_values if c > ccn_threshold),
        ccn_threshold=ccn_threshold,
        total_directories=len(directories),
        # Excluded file counts
        excluded_count=len(excluded_files),
        excluded_by_pattern=excluded_by_pattern,
        excluded_by_minified=excluded_by_minified,
        excluded_by_size=excluded_by_size,
        excluded_by_language=excluded_by_language,
        structure=dir_structure,
        ccn_distribution=compute_distribution(ccn_values) if ccn_values else Distribution(),
        nloc_distribution=compute_distribution(nloc_values) if nloc_values else Distribution(),
    )

    reporter.finish()

    return result


# =============================================================================
# Dashboard Printing
# =============================================================================

def print_dashboard(result: AnalysisResult, width: int = 80):
    """Print the 12-section dashboard."""
    summary = result.summary

    # 1. Header
    print()
    print_header(f"Function Analysis: {result.root_path}", width)
    print(f"  {c('Run ID:', Colors.DIM)} {result.run_id}")
    print(f"  {c('Timestamp:', Colors.DIM)} {result.timestamp}")
    print(f"  {c('Lizard:', Colors.DIM)} {get_lizard_version()}")

    # 2. Quick Stats
    print_section("Quick Stats", width)
    print_row("Files:", format_number(summary.total_files),
              "Functions:", format_number(summary.total_functions), width)
    print_row("Total NLOC:", format_number(summary.total_nloc),
              "Total CCN:", format_number(summary.total_ccn), width)
    print_row("Avg CCN:", f"{summary.avg_ccn:.2f}",
              "Max CCN:", format_number(summary.max_ccn), width)
    print_row("Over threshold:", f"{summary.functions_over_threshold} (CCN > {summary.ccn_threshold})",
              "", "", width)
    print_section_end(width)

    # 3. CCN Distribution
    if summary.ccn_distribution and summary.ccn_distribution.count > 0:
        dist = summary.ccn_distribution
        print_section("CCN Distribution", width)
        print_row("Min:", f"{dist.min:.0f}", "Max:", f"{dist.max:.0f}", width)
        print_row("Mean:", f"{dist.mean:.2f}", "Median:", f"{dist.median:.0f}", width)
        print_row("Std Dev:", f"{dist.stddev:.2f}", "Gini:", f"{dist.gini:.3f}", width)
        print_row("P25:", f"{dist.p25:.0f}", "P75:", f"{dist.p75:.0f}", width)
        print_row("P90:", f"{dist.p90:.0f}", "P95:", f"{dist.p95:.0f}", width)
        print_section_end(width)

    # 4. Hotspot Functions (Top 10 by CCN)
    all_functions = []
    for f in result.files:
        for func in f.functions:
            all_functions.append((f.path, func))

    top_by_ccn = sorted(all_functions, key=lambda x: x[1].ccn, reverse=True)[:10]
    if top_by_ccn:
        print_section("Hotspot Functions (Top 10 by CCN)", width)
        path_width = 40
        name_width = 30
        header = f"  {'Path':<{path_width}} {'Function':<{name_width}} {'CCN':>5} {'NLOC':>6}"
        print(c(BOX_V, Colors.BLUE) + c(header, Colors.DIM) + " " * (width - len(header) - 2) + c(BOX_V, Colors.BLUE))
        for path, func in top_by_ccn:
            path_trunc = truncate_path_middle(path, path_width)
            name_trunc = truncate_path_middle(func.name, name_width)
            ccn_color = Colors.BRIGHT_RED if func.ccn > 20 else (Colors.YELLOW if func.ccn > 10 else Colors.GREEN)
            line = f"  {path_trunc:<{path_width}} {name_trunc:<{name_width}} {c(f'{func.ccn:>5}', ccn_color)} {func.nloc:>6}"
            visible_len = len(strip_ansi(line))
            print(c(BOX_V, Colors.BLUE) + line + " " * (width - visible_len - 2) + c(BOX_V, Colors.BLUE))
        print_section_end(width)

    # 5. Large Functions (Top 10 by NLOC)
    top_by_nloc = sorted(all_functions, key=lambda x: x[1].nloc, reverse=True)[:10]
    if top_by_nloc:
        print_section("Large Functions (Top 10 by NLOC)", width)
        header = f"  {'Path':<{path_width}} {'Function':<{name_width}} {'NLOC':>6} {'CCN':>5}"
        print(c(BOX_V, Colors.BLUE) + c(header, Colors.DIM) + " " * (width - len(header) - 2) + c(BOX_V, Colors.BLUE))
        for path, func in top_by_nloc:
            path_trunc = truncate_path_middle(path, path_width)
            name_trunc = truncate_path_middle(func.name, name_width)
            nloc_color = Colors.BRIGHT_RED if func.nloc > 100 else (Colors.YELLOW if func.nloc > 50 else Colors.GREEN)
            line = f"  {path_trunc:<{path_width}} {name_trunc:<{name_width}} {c(f'{func.nloc:>6}', nloc_color)} {func.ccn:>5}"
            visible_len = len(strip_ansi(line))
            print(c(BOX_V, Colors.BLUE) + line + " " * (width - visible_len - 2) + c(BOX_V, Colors.BLUE))
        print_section_end(width)

    # 6. Parameter-Heavy Functions (5+ params)
    param_heavy = [(p, f) for p, f in all_functions if f.parameter_count >= 5]
    param_heavy = sorted(param_heavy, key=lambda x: x[1].parameter_count, reverse=True)[:10]
    if param_heavy:
        print_section("Parameter-Heavy Functions (5+ params)", width)
        header = f"  {'Path':<{path_width}} {'Function':<{name_width}} {'Params':>6} {'CCN':>5}"
        print(c(BOX_V, Colors.BLUE) + c(header, Colors.DIM) + " " * (width - len(header) - 2) + c(BOX_V, Colors.BLUE))
        for path, func in param_heavy:
            path_trunc = truncate_path_middle(path, path_width)
            name_trunc = truncate_path_middle(func.name, name_width)
            line = f"  {path_trunc:<{path_width}} {name_trunc:<{name_width}} {func.parameter_count:>6} {func.ccn:>5}"
            visible_len = len(strip_ansi(line))
            print(c(BOX_V, Colors.BLUE) + line + " " * (width - visible_len - 2) + c(BOX_V, Colors.BLUE))
        print_section_end(width)

    # 7. Per-Language Summary
    if result.by_language:
        print_section("Per-Language Summary", width)
        header = f"  {'Language':<15} {'Files':>6} {'Funcs':>7} {'NLOC':>8} {'CCN':>7} {'Avg':>6} {'Max':>5}"
        print(c(BOX_V, Colors.BLUE) + c(header, Colors.DIM) + " " * (width - len(header) - 2) + c(BOX_V, Colors.BLUE))
        for lang, stats in sorted(result.by_language.items()):
            line = f"  {lang:<15} {stats['files']:>6} {stats['functions']:>7} {stats['nloc']:>8,} {stats['ccn']:>7} {stats['avg_ccn']:>6.1f} {stats['max_ccn']:>5}"
            print(c(BOX_V, Colors.BLUE) + line + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))
        print_section_end(width)

    # 8. File Summary (Top 10 by function count)
    files_by_func_count = sorted(result.files, key=lambda x: x.function_count, reverse=True)[:10]
    if files_by_func_count:
        print_section("Top Files by Function Count", width)
        path_col = 55
        header = f"  {'Path':<{path_col}} {'Funcs':>6} {'CCN':>6} {'Avg':>6}"
        print(c(BOX_V, Colors.BLUE) + c(header, Colors.DIM) + " " * (width - len(header) - 2) + c(BOX_V, Colors.BLUE))
        for f in files_by_func_count:
            path_trunc = truncate_path_middle(f.path, path_col)
            line = f"  {path_trunc:<{path_col}} {f.function_count:>6} {f.total_ccn:>6} {f.avg_ccn:>6.1f}"
            print(c(BOX_V, Colors.BLUE) + line + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))
        print_section_end(width)

    # 9. Threshold Violations
    violations = [(p, f) for p, f in all_functions if f.ccn > summary.ccn_threshold]
    violations = sorted(violations, key=lambda x: x[1].ccn, reverse=True)[:15]
    if violations:
        print_section(f"Threshold Violations (CCN > {summary.ccn_threshold})", width)
        header = f"  {'Path':<{path_width}} {'Function':<{name_width}} {'CCN':>5} {'NLOC':>6}"
        print(c(BOX_V, Colors.BLUE) + c(header, Colors.DIM) + " " * (width - len(header) - 2) + c(BOX_V, Colors.BLUE))
        for path, func in violations:
            path_trunc = truncate_path_middle(path, path_width)
            name_trunc = truncate_path_middle(func.name, name_width)
            ccn_color = Colors.BRIGHT_RED if func.ccn > 20 else Colors.YELLOW
            line = f"  {path_trunc:<{path_width}} {name_trunc:<{name_width}} {c(f'{func.ccn:>5}', ccn_color)} {func.nloc:>6}"
            visible_len = len(strip_ansi(line))
            print(c(BOX_V, Colors.BLUE) + line + " " * (width - visible_len - 2) + c(BOX_V, Colors.BLUE))
        print_section_end(width)

    # 10. Complexity Density (CCN per NLOC)
    density_funcs = [(p, f, f.ccn / f.nloc if f.nloc > 0 else 0) for p, f in all_functions if f.nloc > 0]
    density_funcs = sorted(density_funcs, key=lambda x: x[2], reverse=True)[:10]
    if density_funcs:
        print_section("Complexity Density (Top 10 by CCN/NLOC)", width)
        header = f"  {'Path':<{path_width}} {'Function':<{name_width}} {'Density':>7} {'CCN':>5}"
        print(c(BOX_V, Colors.BLUE) + c(header, Colors.DIM) + " " * (width - len(header) - 2) + c(BOX_V, Colors.BLUE))
        for path, func, density in density_funcs:
            path_trunc = truncate_path_middle(path, path_width)
            name_trunc = truncate_path_middle(func.name, name_width)
            line = f"  {path_trunc:<{path_width}} {name_trunc:<{name_width}} {density:>7.3f} {func.ccn:>5}"
            print(c(BOX_V, Colors.BLUE) + line + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))
        print_section_end(width)

    # 11. Function Size Distribution
    if summary.nloc_distribution and summary.nloc_distribution.count > 0:
        dist = summary.nloc_distribution
        print_section("Function Size Distribution (NLOC)", width)
        print_row("Min:", f"{dist.min:.0f}", "Max:", f"{dist.max:.0f}", width)
        print_row("Mean:", f"{dist.mean:.2f}", "Median:", f"{dist.median:.0f}", width)
        print_row("Std Dev:", f"{dist.stddev:.2f}", "Gini:", f"{dist.gini:.3f}", width)
        print_row("P90:", f"{dist.p90:.0f}", "P95:", f"{dist.p95:.0f}", width)
        print_section_end(width)

    # 13. Directory Structure
    if result.directories and summary.structure:
        print_section("Directory Structure", width)
        print_row("Total directories:", format_number(summary.total_directories),
                  "Max depth:", format_number(summary.structure.max_depth), width)
        print_row("Leaf directories:", format_number(summary.structure.leaf_directory_count),
                  "Avg depth:", f"{summary.structure.avg_depth:.1f}", width)
        print_row("Avg functions/dir:", f"{summary.structure.avg_functions_per_directory:.1f}",
                  "", "", width)
        print_section_end(width)

    # 14. Top Directories by Recursive CCN
    if result.directories:
        top_by_ccn = sorted(
            [d for d in result.directories if d.recursive.ccn > 0],
            key=lambda x: x.recursive.ccn,
            reverse=True
        )[:10]
        if top_by_ccn:
            print_section("Top Directories by Recursive CCN", width)
            dir_col = 45
            header = f"  {'Directory':<{dir_col}} {'Files':>6} {'Funcs':>6} {'CCN':>7} {'Avg':>6}"
            print(c(BOX_V, Colors.BLUE) + c(header, Colors.DIM) + " " * (width - len(header) - 2) + c(BOX_V, Colors.BLUE))
            for d in top_by_ccn:
                dir_trunc = truncate_path_middle(d.path, dir_col)
                ccn_color = Colors.BRIGHT_RED if d.recursive.ccn > 100 else (Colors.YELLOW if d.recursive.ccn > 50 else Colors.GREEN)
                line = f"  {dir_trunc:<{dir_col}} {d.recursive.file_count:>6} {d.recursive.function_count:>6} {c(f'{d.recursive.ccn:>7}', ccn_color)} {d.recursive.avg_ccn:>6.1f}"
                visible_len = len(strip_ansi(line))
                print(c(BOX_V, Colors.BLUE) + line + " " * (width - visible_len - 2) + c(BOX_V, Colors.BLUE))
            print_section_end(width)

    # 15. Top Directories by Direct Functions
    if result.directories:
        top_by_funcs = sorted(
            [d for d in result.directories if d.direct.function_count > 0],
            key=lambda x: x.direct.function_count,
            reverse=True
        )[:10]
        if top_by_funcs:
            print_section("Top Directories by Direct Functions", width)
            dir_col = 45
            header = f"  {'Directory':<{dir_col}} {'Files':>6} {'Funcs':>6} {'CCN':>7} {'Max':>5}"
            print(c(BOX_V, Colors.BLUE) + c(header, Colors.DIM) + " " * (width - len(header) - 2) + c(BOX_V, Colors.BLUE))
            for d in top_by_funcs:
                dir_trunc = truncate_path_middle(d.path, dir_col)
                line = f"  {dir_trunc:<{dir_col}} {d.direct.file_count:>6} {d.direct.function_count:>6} {d.direct.ccn:>7} {d.direct.max_ccn:>5}"
                print(c(BOX_V, Colors.BLUE) + line + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))
            print_section_end(width)

    # 16. Complete Directory Tree
    if result.directories:
        print_section("Complete Directory Tree", width)
        # Header
        inner = width - 4
        tree_col = 35
        header = f"  {'Directory':<{tree_col}} ─── Recursive ───  ──── Direct ────"
        print(c(BOX_V, Colors.BLUE) + c(header, Colors.DIM) + " " * (inner - len(header)) + c(BOX_V, Colors.BLUE))
        subheader = f"  {'':<{tree_col}} {'Files':>5} {'Funcs':>5} {'CCN':>6}  {'Files':>5} {'Funcs':>5} {'CCN':>6}"
        print(c(BOX_V, Colors.BLUE) + c(subheader, Colors.DIM) + " " * (inner - len(subheader)) + c(BOX_V, Colors.BLUE))
        print(c(BOX_V, Colors.BLUE) + "  " + "─" * (inner - 2) + c(BOX_V, Colors.BLUE))

        # Build tree visualization
        sorted_dirs = sorted(result.directories, key=lambda x: x.path)
        for i, d in enumerate(sorted_dirs):
            # Create tree prefix
            if d.depth == 0:
                prefix = ""
            else:
                # Check if this is the last child at its level
                is_last = True
                for other in sorted_dirs[i + 1:]:
                    if other.depth <= d.depth:
                        break
                    if other.depth == d.depth:
                        is_last = False
                        break
                prefix = "  " * (d.depth - 1) + ("└── " if is_last else "├── ")

            name = d.name if d.depth > 0 else d.name
            dir_display = prefix + name
            dir_trunc = truncate_path_middle(dir_display, tree_col)

            line = f"  {dir_trunc:<{tree_col}} {d.recursive.file_count:>5} {d.recursive.function_count:>5} {d.recursive.ccn:>6}  {d.direct.file_count:>5} {d.direct.function_count:>5} {d.direct.ccn:>6}"
            print(c(BOX_V, Colors.BLUE) + line + " " * (inner - len(line)) + c(BOX_V, Colors.BLUE))

        print_section_end(width)

    # 16. Analysis Summary (renumbered from 12)
    print_section("Analysis Summary", width)
    print_row("Files analyzed:", format_number(summary.total_files), "", "", width)
    print_row("Functions found:", format_number(summary.total_functions), "", "", width)
    print_row("Languages:", str(len(result.by_language)), "", "", width)
    print_empty_row(width)

    # Key findings
    findings = []
    if summary.max_ccn > 30:
        findings.append(f"High complexity: {summary.max_ccn} CCN max (consider refactoring)")
    if summary.functions_over_threshold > 0:
        pct = summary.functions_over_threshold / summary.total_functions * 100 if summary.total_functions > 0 else 0
        findings.append(f"{summary.functions_over_threshold} functions ({pct:.1f}%) exceed threshold")
    if summary.ccn_distribution and summary.ccn_distribution.gini > 0.5:
        findings.append(f"Uneven complexity distribution (Gini: {summary.ccn_distribution.gini:.2f})")
    if param_heavy:
        findings.append(f"{len(param_heavy)} functions with 5+ parameters")

    if findings:
        for finding in findings:
            line = f"  {c('•', Colors.YELLOW)} {finding}"
            visible_len = len(strip_ansi(line))
            print(c(BOX_V, Colors.BLUE) + line + " " * (width - visible_len - 2) + c(BOX_V, Colors.BLUE))
    else:
        line = f"  {c('✓', Colors.GREEN)} No significant complexity issues found"
        visible_len = len(strip_ansi(line))
        print(c(BOX_V, Colors.BLUE) + line + " " * (width - visible_len - 2) + c(BOX_V, Colors.BLUE))

    print_section_end(width)
    print()


# =============================================================================
# Run Folder and Output
# =============================================================================

def to_dict(obj):
    """Convert a dataclass/object to dict for JSON serialization."""
    if hasattr(obj, '__dict__'):
        return {k: to_dict(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, list):
        return [to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    else:
        return obj


def result_to_output(result: AnalysisResult) -> dict:
    """Convert AnalysisResult to JSON-serializable dict (envelope schema)."""
    tool_version = get_lizard_version().replace("lizard ", "")
    data = {
        "tool": "lizard",
        "tool_version": tool_version,
        "run_id": result.run_id,
        "timestamp": result.timestamp,
        "root_path": result.root_path,
        "lizard_version": get_lizard_version(),
        "directories": [to_dict(d) for d in result.directories],
        "files": [to_dict(f) for f in result.files],
        "excluded_files": [to_dict(e) for e in result.excluded_files],
        "summary": to_dict(result.summary),
        "by_language": result.by_language,
    }
    return create_envelope(
        data,
        tool_name="lizard",
        tool_version=tool_version,
        run_id=result.run_id,
        repo_id=result.repo_id,
        branch=result.branch,
        commit=result.commit,
        timestamp=result.timestamp,
    )


def create_run_folder(
    output_base: Path,
    repo_name: str,
    target_path: str,
    result: AnalysisResult,
) -> Path:
    """Create output files for a single analysis run."""
    output_base.mkdir(parents=True, exist_ok=True)

    result_dict = result_to_output(result)
    output_path = output_base / "output.json"
    with open(output_path, 'w') as f:
        json.dump(result_dict, f, indent=2, default=str)

    metadata = {
        "run_id": result.run_id,
        "timestamp": result.timestamp,
        "repo_name": repo_name,
        "target_path": target_path,
        "lizard_version": get_lizard_version(),
        "schema_version": result.schema_version,
        "file_count": result.summary.total_files if result.summary else 0,
        "function_count": result.summary.total_functions if result.summary else 0,
        "total_ccn": result.summary.total_ccn if result.summary else 0,
        "outputs": {
            "analysis": "output.json",
            "metadata": "metadata.json",
        }
    }
    with open(output_base / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)

    return output_base


# =============================================================================
# Interactive Mode
# =============================================================================

def discover_repos(base_path: Path) -> List[Path]:
    """Discover all analyzable repositories under a path."""
    repos = []

    # Check for synthetic repos
    synthetic = base_path / "synthetic"
    if synthetic.exists():
        for lang_dir in sorted(synthetic.iterdir()):
            if lang_dir.is_dir() and not lang_dir.name.startswith('.'):
                repos.append(lang_dir)

    # Check for real repos
    real = base_path / "real"
    if real.exists():
        for repo_dir in sorted(real.iterdir()):
            if repo_dir.is_dir() and not repo_dir.name.startswith('.'):
                repos.append(repo_dir)

    # If no subdirs found, treat the path itself as a repo
    if not repos and base_path.exists():
        repos.append(base_path)

    return repos


def run_interactive(base_path: Path, output_root: Path, commit_override: str | None, fallback_repo: Path):
    """Run interactive multi-repo analysis."""
    repos = discover_repos(base_path)

    if not repos:
        print(f"No repositories found under {base_path}")
        return

    width = get_terminal_width()
    print()
    print(c(f"Found {len(repos)} repositories:", Colors.CYAN, Colors.BOLD))
    for i, repo in enumerate(repos, 1):
        print(f"  {i:2}. {repo.name}")

    print()
    print(c("Enter repository number (or 'q' to quit):", Colors.YELLOW))

    while True:
        try:
            choice = input("> ").strip()
            if choice.lower() in ('q', 'quit', 'exit'):
                break

            idx = int(choice) - 1
            if 0 <= idx < len(repos):
                repo = repos[idx]
                print()
                print(c(f"Analyzing {repo.name}...", Colors.CYAN))

                result = analyze_directory(str(repo))
                print_dashboard(result, width)
                try:
                    result.commit = resolve_commit(
                        repo.resolve(),
                        commit_override,
                        fallback_repo=fallback_repo,
                        strict=True,
                    )
                except ValueError as exc:
                    print(c(f"  ⚠️  {exc}", Colors.YELLOW))

                # Save output bundle
                run_folder = create_run_folder(
                    output_root / result.run_id,
                    repo.name,
                    str(repo),
                    result,
                )
                print(f"  {c('Output:', Colors.DIM)} {run_folder}")
                print()
                print(c("Enter repository number (or 'q' to quit):", Colors.YELLOW))
            else:
                print(f"Invalid choice. Enter 1-{len(repos)}")
        except ValueError:
            print(f"Invalid input. Enter a number 1-{len(repos)} or 'q'")
        except KeyboardInterrupt:
            print()
            break


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Function-level complexity analysis using Lizard"
    )
    parser.add_argument(
        "target",
        help="Directory to analyze"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (JSON)"
    )
    parser.add_argument(
        "--output-dir",
        default=os.environ.get("OUTPUT_DIR"),
        help="Directory to write analysis output (default: outputs/<run-id>)",
    )
    parser.add_argument(
        "--commit",
        default=os.environ.get("COMMIT"),
        help="Commit SHA (default: repo HEAD)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive multi-repo mode"
    )
    parser.add_argument(
        "--ccn-threshold",
        type=int,
        default=10,
        help="CCN threshold for violations (default: 10)"
    )
    # Performance tuning options
    parser.add_argument(
        "-t", "--threads",
        type=int,
        default=None,
        help="Number of threads (default: CPU count)"
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test directories (excluded by default)"
    )
    parser.add_argument(
        "-l", "--languages",
        nargs="+",
        help="Only analyze specific languages (e.g., 'C#' 'Python')"
    )
    parser.add_argument(
        "--max-file-size",
        type=int,
        default=500,
        help="Skip files larger than N KB (default: 500)"
    )
    parser.add_argument(
        "--exclude-patterns",
        nargs="+",
        default=None,
        help="Additional filename patterns to exclude (fnmatch syntax, e.g., '*.generated.js')"
    )
    parser.add_argument(
        "--no-minified-detection",
        action="store_true",
        help="Disable content-based minified file detection"
    )
    parser.add_argument(
        "--include-vendor",
        action="store_true",
        help="Include vendor/library files (normally excluded)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress progress output during analysis"
    )

    args = parser.parse_args()

    if args.no_color:
        set_color_enabled(False)

    target = Path(args.target)
    if not target.exists():
        print(f"Error: {target} does not exist")
        sys.exit(1)

    # Determine output base
    script_dir = Path(__file__).parent.parent
    output_root = Path(args.output_dir) if args.output_dir else script_dir / "outputs"
    output_root.mkdir(parents=True, exist_ok=True)

    width = get_terminal_width()

    if args.interactive:
        run_interactive(target, output_root, args.commit, script_dir)
    else:
        result = analyze_directory(
            str(target),
            threads=args.threads,
            exclude_tests=not args.include_tests,
            languages=args.languages,
            max_file_size_kb=args.max_file_size,
            show_progress=not args.quiet,
            extra_exclude_patterns=args.exclude_patterns,
            detect_minified=not args.no_minified_detection,
            include_vendor=args.include_vendor,
        )
        print_dashboard(result, width)
        try:
            result.commit = resolve_commit(
                target.resolve(),
                args.commit or None,
                fallback_repo=script_dir,
                strict=True,
            )
        except ValueError as exc:
            print(f"Error: {exc}")
            sys.exit(1)

        # Save output bundle
        repo_name = target.name
        run_folder = create_run_folder(
            output_root / result.run_id if args.output_dir is None else output_root,
            repo_name,
            str(target),
            result,
        )
        print(f"  {c('Output saved to:', Colors.DIM)} {run_folder}")

        # Also save to specified output file if provided
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w') as f:
                json.dump(result_to_output(result), f, indent=2, default=str)
            print(f"  {c('JSON output:', Colors.DIM)} {output_path}")


if __name__ == "__main__":
    main()
