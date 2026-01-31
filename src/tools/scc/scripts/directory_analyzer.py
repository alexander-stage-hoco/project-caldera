#!/usr/bin/env python3
"""Directory tree analysis with pure metrics and distribution statistics.

Outputs raw metrics per directory (recursive + direct) and per file.
No scores or thresholds - just data for downstream analysis.
"""

import fnmatch
import json
import math
import os
import shutil
import subprocess
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Any


# =============================================================================
# Terminal Colors and Formatting
# =============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Colors
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright variants
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_CYAN = "\033[96m"


# Global flag for color output
_use_color = True


def set_color_enabled(enabled: bool):
    """Enable or disable color output."""
    global _use_color
    _use_color = enabled


def get_terminal_width(default: int = 120, minimum: int = 80) -> int:
    """Get terminal width with auto-detection.

    Args:
        default: Default width if detection fails (120 chars)
        minimum: Minimum width to return (80 chars)

    Returns:
        Terminal width, clamped to minimum
    """
    try:
        columns, _ = shutil.get_terminal_size()
        return max(columns, minimum)
    except Exception:
        return default


def truncate_path_middle(path: str, max_len: int) -> str:
    """Truncate path in the middle, preserving start (repo) and end (filename).

    Args:
        path: File path to truncate
        max_len: Maximum length for the result

    Returns:
        Path truncated in the middle if needed, e.g.:
        'eval-repos/real/Humanizer/...Properties/Resources.resx'
    """
    if len(path) <= max_len:
        return path
    # Keep first ~30% and last ~60% of available space
    ellipsis = "..."
    available = max_len - len(ellipsis)
    keep_start = available // 3
    keep_end = available - keep_start
    return path[:keep_start] + ellipsis + path[-keep_end:]


def c(text: str, *codes: str) -> str:
    """Apply color codes to text if colors are enabled."""
    if not _use_color:
        return str(text)
    prefix = "".join(codes)
    return f"{prefix}{text}{Colors.RESET}"


def format_number(n: float, decimals: int = 0) -> str:
    """Format a number with commas."""
    if decimals == 0:
        return f"{int(n):,}"
    return f"{n:,.{decimals}f}"


def format_money(n: float) -> str:
    """Format a dollar amount."""
    return f"${format_number(n)}"


def format_percent(n: float) -> str:
    """Format a percentage."""
    return f"{n:.1%}"


# Box drawing characters
BOX_TL = "┌"
BOX_TR = "┐"
BOX_BL = "└"
BOX_BR = "┘"
BOX_H = "─"
BOX_V = "│"
BOX_ML = "├"
BOX_MR = "┤"

# Header box (rounded)
HDR_TL = "╭"
HDR_TR = "╮"
HDR_BL = "╰"
HDR_BR = "╯"


def print_header(title: str, width: int = 65):
    """Print a header box."""
    inner_width = width - 4
    print(c(HDR_TL + HDR_BL.replace("╰", "─") * (width - 2) + HDR_TR, Colors.CYAN))
    print(c(f"{BOX_V}  {title:<{inner_width}}{BOX_V}", Colors.CYAN))
    print(c(HDR_BL + HDR_BR.replace("╯", "─") * (width - 2) + HDR_BR, Colors.CYAN))


def print_section(title: str, width: int = 65):
    """Print a section header."""
    inner_width = width - 4
    print()
    print(c(BOX_TL + BOX_H * (width - 2) + BOX_TR, Colors.BLUE))
    print(c(f"{BOX_V}  {title:<{inner_width}}{BOX_V}", Colors.BLUE, Colors.BOLD))
    print(c(BOX_ML + BOX_H * (width - 2) + BOX_MR, Colors.BLUE))


def print_section_end(width: int = 65):
    """Print section end border."""
    print(c(BOX_BL + BOX_H * (width - 2) + BOX_BR, Colors.BLUE))


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    import re
    return re.sub(r'\033\[[0-9;]*m', '', text)


def print_row(label: str, value: str, label2: str = "", value2: str = "", width: int = 65):
    """Print a row in a section."""
    inner_width = width - 4  # Account for "│  " and " │"

    if label2:
        # Two-column layout
        col_width = inner_width // 2
        left = f"{c(label, Colors.DIM)} {value}"
        right = f"{c(label2, Colors.DIM)} {value2}"
        left_visible = len(strip_ansi(left))
        right_visible = len(strip_ansi(right))
        left_padded = left + " " * (col_width - left_visible)
        right_padded = right + " " * (col_width - right_visible)
        line = f"  {left_padded}{right_padded}"
    else:
        # Single column
        content = f"{c(label, Colors.DIM)} {value}"
        visible_len = len(strip_ansi(content))
        line = f"  {content}" + " " * (inner_width - visible_len - 2)

    print(c(BOX_V, Colors.BLUE) + line + c(BOX_V, Colors.BLUE))


def print_directory_entry(d: dict, width: int = 65):
    """Print a directory entry with metrics (no scores)."""
    # Path line
    path_line = f"  {c(d['path'], Colors.WHITE, Colors.BOLD)}"
    print(c(BOX_V, Colors.BLUE) + path_line)

    recursive = d["recursive"]
    direct = d["direct"]

    # Recursive stats
    rec_line = f"    {c('Recursive:', Colors.CYAN)} {recursive['file_count']:>3} files │ {recursive['code']:>6,} LOC │ {recursive['complexity_total']:>4,} cx │ {recursive['avg_complexity']:>5.1f} avg"
    print(c(BOX_V, Colors.BLUE) + rec_line)

    # Direct stats (if any direct files)
    if direct["file_count"] > 0:
        dir_line = f"    {c('Direct:', Colors.DIM)}    {direct['file_count']:>3} files │ {direct['code']:>6,} LOC │ {direct['complexity_total']:>4,} cx │ {direct['avg_complexity']:>5.1f} avg"
        print(c(BOX_V, Colors.BLUE) + dir_line)


def print_all_directories(directories: list, width: int = 65):
    """Print all directories with their metrics."""
    print_section(f"📁 All Directories ({len(directories)} total)")

    for d in directories:
        print_directory_entry(d, width)
        print(c(BOX_V, Colors.BLUE))

    print_section_end()


def print_top_by_metric(directories: list, metric_path: str, title: str,
                        limit: int = 5, width: int = 65, descending: bool = True):
    """Print top N directories by a given metric.

    Args:
        directories: List of directory entries
        metric_path: Path to metric (e.g., "recursive.avg_complexity")
        title: Section title
        limit: Number of entries to show
        width: Output width
        descending: Sort descending (highest first) if True
    """
    def get_metric(d: dict) -> float:
        parts = metric_path.split(".")
        val = d
        for p in parts:
            val = val.get(p, 0)
        return val if isinstance(val, (int, float)) else 0

    sorted_dirs = sorted(directories, key=get_metric, reverse=descending)[:limit]

    print_section(title)

    for rank, d in enumerate(sorted_dirs, 1):
        metric_val = get_metric(d)
        stats = d["recursive"]

        # Rank and path with metric value
        rank_str = c(f"#{rank}", Colors.CYAN)
        metric_str = c(f"{metric_val:.2f}", Colors.BRIGHT_YELLOW, Colors.BOLD)
        line1 = f"  {rank_str} {metric_str}  {c(d['path'], Colors.WHITE)}"
        print(c(BOX_V, Colors.BLUE) + line1)

        # Stats line
        stats_line = f"        {stats['file_count']:>3} files │ {stats['code']:>6,} LOC │ {stats['complexity_total']:>4,} complexity"
        print(c(BOX_V, Colors.BLUE) + c(stats_line, Colors.DIM))

    print_section_end()


# =============================================================================
# New v2.0 Dashboard Display Functions
# =============================================================================

def print_file_classifications(summary: dict, width: int = 65):
    """Display file classification breakdown."""
    fc = summary.get("file_classifications", {})
    if not fc:
        return

    print_section("📁 File Classifications", width)

    classifications = [
        ("Source", fc.get("source_file_count", 0), 0),
        ("Test", fc.get("test_file_count", 0), fc.get("test_loc", 0)),
        ("Config", fc.get("config_file_count", 0), 0),
        ("Docs", fc.get("docs_file_count", 0), 0),
        ("Build", fc.get("build_file_count", 0), 0),
        ("CI", fc.get("ci_file_count", 0), 0),
    ]

    for name, count, loc in classifications:
        if count > 0:
            loc_str = f" ({loc:,} LOC)" if loc else ""
            print_row(name, f"{count} files{loc_str}")

    print_section_end(width)


def print_inequality_metrics(summary: dict, width: int = 65):
    """Display inequality metrics for LOC distribution."""
    dists = summary.get("distributions", {})
    dist = dists.get("loc", {})
    if not dist:
        return

    print_section("📊 Code Distribution (Inequality)", width)

    gini = dist.get("gini", 0)
    palma = dist.get("palma", 0)
    top_10 = dist.get("top_10_pct_share", 0) * 100
    top_20 = dist.get("top_20_pct_share", 0) * 100
    bottom_50 = dist.get("bottom_50_pct_share", 0) * 100

    # Interpret gini
    if gini < 0.3:
        interpretation = "Low concentration"
    elif gini < 0.5:
        interpretation = "Moderate concentration"
    elif gini < 0.7:
        interpretation = "High concentration"
    else:
        interpretation = "Very high concentration"

    print_row("Gini Coefficient", f"{gini:.3f}", "Interpretation", interpretation)
    if palma > 0 and not math.isinf(palma):
        print_row("Palma Ratio", f"{palma:.1f}x", "", "")
    print_row("Top 10% holds", f"{top_10:.1f}%", "Top 20% holds", f"{top_20:.1f}%")
    print_row("Bottom 50% holds", f"{bottom_50:.1f}%", "", "")

    print_section_end(width)


def print_language_breakdown(summary: dict, width: int = 65):
    """Display per-language statistics."""
    by_lang = summary.get("by_language", {})
    if not by_lang:
        return

    print_section("🌐 Language Breakdown", width)

    # Sort by LOC descending
    sorted_langs = sorted(
        by_lang.items(),
        key=lambda x: x[1].get("code", 0),
        reverse=True
    )

    # Header row
    hdr = f"  {'Language':<12} {'Files':>6} {'LOC':>8} {'Complexity':>10} {'Avg Cx':>8}"
    print(c(BOX_V, Colors.BLUE) + c(hdr, Colors.DIM) + " " + c(BOX_V, Colors.BLUE))
    sep = f"  {'-'*12} {'-'*6} {'-'*8} {'-'*10} {'-'*8}"
    print(c(BOX_V, Colors.BLUE) + c(sep, Colors.DIM) + " " + c(BOX_V, Colors.BLUE))

    for lang, stats in sorted_langs[:8]:  # Top 8 languages
        files = stats.get("file_count", 0)
        loc = stats.get("code", 0)
        cx = stats.get("complexity_total", 0)
        avg_cx = cx / files if files > 0 else 0
        row = f"  {lang:<12} {files:>6} {loc:>8,} {cx:>10} {avg_cx:>8.1f}"
        print(c(BOX_V, Colors.BLUE) + row + " " + c(BOX_V, Colors.BLUE))

    print_section_end(width)


def print_cocomo_comparison(summary: dict, width: int = 65):
    """Display all 8 COCOMO presets side-by-side."""
    cocomo = summary.get("cocomo", {})
    if not cocomo:
        return

    print_section("💰 COCOMO Estimates (All Presets)", width)

    # Header
    hdr = f"  {'Preset':<16} {'Cost':>12} {'Effort':>8} {'Schedule':>8} {'Team':>6}"
    print(c(BOX_V, Colors.BLUE) + c(hdr, Colors.DIM) + " " + c(BOX_V, Colors.BLUE))
    sep = f"  {'-'*16} {'-'*12} {'-'*8} {'-'*8} {'-'*6}"
    print(c(BOX_V, Colors.BLUE) + c(sep, Colors.DIM) + " " + c(BOX_V, Colors.BLUE))

    preset_order = [
        ("early_startup", "Early Startup"),
        ("growth_startup", "Growth Startup"),
        ("scale_up", "Scale-Up"),
        ("sme", "SME"),
        ("mid_market", "Mid-Market"),
        ("large_enterprise", "Enterprise"),
        ("regulated", "Regulated"),
        ("open_source", "Open Source"),
    ]

    for key, label in preset_order:
        p = cocomo.get(key, {})
        cost = p.get("cost", 0)
        effort = p.get("effort_person_months", 0)
        schedule = p.get("schedule_months", 0)
        team = p.get("people", 0)

        cost_str = f"${cost:,.0f}" if cost > 0 else "$0"
        row = f"  {label:<16} {cost_str:>12} {effort:>6.1f}pm {schedule:>6.1f}mo {team:>5.1f}"
        print(c(BOX_V, Colors.BLUE) + row + " " + c(BOX_V, Colors.BLUE))

    print_section_end(width)


def print_distribution_stats(summary: dict, width: int = 65):
    """Display key distribution statistics."""
    dists = summary.get("distributions", {})
    if not dists:
        return

    print_section("📈 Distribution Statistics", width)

    for name, key in [("LOC", "loc"), ("Complexity", "complexity")]:
        dist = dists.get(key)
        if not dist:
            continue

        p50 = dist.get("median", 0)
        p90 = dist.get("p90", 0)
        p95 = dist.get("p95", 0)
        p99 = dist.get("p99", 0)
        skew = dist.get("skewness", 0)

        skew_desc = "right-skewed" if skew > 1 else "moderate" if skew > 0 else "symmetric"

        line = f"  {name}: median={p50:.0f}, p90={p90:.0f}, p95={p95:.0f}, p99={p99:.0f} ({skew_desc})"
        print(c(BOX_V, Colors.BLUE) + line)

    print_section_end(width)


def print_directory_structure(summary: dict, width: int = 65):
    """Display directory structure metrics."""
    struct = summary.get("structure", {})
    if not struct:
        return

    print_section("🏗️ Directory Structure", width)

    print_row("Max Depth", str(struct.get("max_depth", 0)),
              "Avg Depth", f"{struct.get('avg_depth', 0):.1f}")
    print_row("Total Directories", str(struct.get("total_directories", 0)),
              "Leaf Directories", str(struct.get("leaf_directory_count", 0)))
    print_row("Avg Files/Dir", f"{struct.get('avg_files_per_directory', 0):.1f}", "", "")

    print_section_end(width)


def print_top_directories_enhanced(directories: list, width: int = 65):
    """Display Top 5 directories with recursive AND direct stats."""

    print_section("📊 Top 5 Directories by Recursive Complexity", width)

    # Sort by recursive avg complexity
    sorted_dirs = sorted(
        [d for d in directories if d.get("recursive", {}).get("file_count", 0) > 0],
        key=lambda x: x.get("recursive", {}).get("avg_complexity", 0),
        reverse=True
    )[:5]

    for i, d in enumerate(sorted_dirs, 1):
        path = d.get("path", "")
        rec = d.get("recursive", {})
        direct = d.get("direct", {})

        # Header line with rank
        rank_line = f"  {c(f'#{i}', Colors.CYAN)} {c(path, Colors.WHITE, Colors.BOLD)}"
        print(c(BOX_V, Colors.BLUE) + rank_line)

        # Recursive stats
        rec_files = rec.get("file_count", 0)
        rec_loc = rec.get("code", 0)
        rec_cx = rec.get("complexity_total", 0)
        rec_avg = rec.get("avg_complexity", 0)
        rec_line = f"     {c('Recursive:', Colors.CYAN)} {rec_files} files │ {rec_loc:,} LOC │ {rec_cx} cx │ {rec_avg:.1f} avg"
        print(c(BOX_V, Colors.BLUE) + rec_line)

        # Direct stats (if different from recursive)
        dir_files = direct.get("file_count", 0)
        if dir_files > 0 and dir_files != rec_files:
            dir_loc = direct.get("code", 0)
            dir_cx = direct.get("complexity_total", 0)
            dir_avg = direct.get("avg_complexity", 0)
            dir_line = f"     {c('Direct:', Colors.DIM)}    {dir_files} files │ {dir_loc:,} LOC │ {dir_cx} cx │ {dir_avg:.1f} avg"
            print(c(BOX_V, Colors.BLUE) + dir_line)

        # Inequality metrics if available
        loc_dist = rec.get("loc_distribution")
        if loc_dist:
            gini = loc_dist.get("gini", 0)
            p90 = loc_dist.get("p90", 0)
            ineq_line = f"     {c('Gini:', Colors.DIM)} {gini:.3f} │ {c('P90:', Colors.DIM)} {p90:.0f} LOC"
            print(c(BOX_V, Colors.BLUE) + ineq_line)

        print(c(BOX_V, Colors.BLUE))

    print_section_end(width)


def print_top_direct_directories(directories: list, width: int = 65, limit: int = 10):
    """Display Top N directories by DIRECT file count with full stats."""

    print_section(f"📂 Top {limit} Directories by Direct Files", width)

    # Sort by direct file count
    sorted_dirs = sorted(
        [d for d in directories if d.get("direct", {}).get("file_count", 0) > 0],
        key=lambda x: x.get("direct", {}).get("file_count", 0),
        reverse=True
    )[:limit]

    for i, d in enumerate(sorted_dirs, 1):
        path = d.get("path", "")
        direct = d.get("direct", {})
        rec = d.get("recursive", {})

        dir_files = direct.get("file_count", 0)
        dir_loc = direct.get("code", 0)
        dir_cx = direct.get("complexity_total", 0)
        dir_avg = direct.get("avg_complexity", 0)

        # Calculate what % of recursive is direct
        rec_files = rec.get("file_count", 1)
        pct = (dir_files / rec_files * 100) if rec_files > 0 else 100

        # Header line with rank
        rank_line = f"  {c(f'#{i}', Colors.CYAN)} {c(path, Colors.WHITE, Colors.BOLD)}"
        print(c(BOX_V, Colors.BLUE) + rank_line)

        # Direct stats
        dir_line = f"     {c('Direct:', Colors.CYAN)} {dir_files} files ({pct:.0f}% of total) │ {dir_loc:,} LOC │ {dir_cx} cx │ {dir_avg:.1f} avg"
        print(c(BOX_V, Colors.BLUE) + dir_line)

        # Show recursive stats for comparison
        rec_loc = rec.get("code", 0)
        rec_cx = rec.get("complexity_total", 0)
        rec_avg = rec.get("avg_complexity", 0)
        if rec_files != dir_files:
            rec_line = f"     {c('Recursive:', Colors.DIM)} {rec_files} files │ {rec_loc:,} LOC │ {rec_cx} cx │ {rec_avg:.1f} avg"
            print(c(BOX_V, Colors.BLUE) + rec_line)

        # Inequality metrics from DIRECT distribution (if available)
        loc_dist = direct.get("loc_distribution")
        if loc_dist:
            gini = loc_dist.get("gini", 0)
            p90 = loc_dist.get("p90", 0)
            p95 = loc_dist.get("p95", 0)
            ineq_line = f"     {c('Gini:', Colors.DIM)} {gini:.3f} │ {c('P90:', Colors.DIM)} {p90:.0f} LOC │ {c('P95:', Colors.DIM)} {p95:.0f} LOC"
            print(c(BOX_V, Colors.BLUE) + ineq_line)

        print(c(BOX_V, Colors.BLUE))

    print_section_end(width)


# =============================================================================
# NEW v2.0 Dashboard Sections (18 Total)
# =============================================================================


def print_header_metadata(result: dict, target: str, width: int = 79):
    """Section 1: Header & Metadata with run information."""
    summary = result.get("summary", {})
    run_id = result.get("run_id", "unknown")
    timestamp = result.get("timestamp", "")

    # Box drawing for header
    print()
    print(c("╔" + "═" * (width - 2) + "╗", Colors.CYAN))
    print(c(f"║  {'scc Directory Analysis v2.0':<{width-4}}║", Colors.CYAN, Colors.BOLD))
    print(c(f"║  Run ID: {run_id:<{width-13}}║", Colors.CYAN))
    print(c(f"║  Path: {target:<{width-11}}║", Colors.CYAN))
    print(c(f"║  Timestamp: {timestamp[:19]:<{width-16}}║", Colors.CYAN))
    print(c("╚" + "═" * (width - 2) + "╝", Colors.CYAN))


def print_validation_evidence(result: dict, width: int = 79):
    """Section 2: Validation Evidence - invariant checks and data integrity."""
    summary = result.get("summary", {})
    directories = result.get("directories", [])
    files = result.get("files", [])

    # Compute invariant checks
    total_files = summary.get("total_files", 0)
    total_loc = summary.get("total_loc", 0)
    total_dirs = summary.get("total_directories", 0)

    # Check 1: sum(direct.file_count) == total_files
    sum_direct_files = sum(d.get("direct", {}).get("file_count", 0) for d in directories)
    check1_pass = sum_direct_files == total_files

    # Check 2: sum(by_language.loc) == total_loc
    by_lang = summary.get("by_language", {})
    sum_lang_loc = sum(lang.get("code", 0) for lang in by_lang.values())
    check2_pass = sum_lang_loc == total_loc

    # Check 3: recursive >= direct for all dirs
    rec_gte_direct = all(
        d.get("recursive", {}).get("file_count", 0) >= d.get("direct", {}).get("file_count", 0)
        for d in directories
    )
    check3_count = len(directories)

    # Check 4: percentiles monotonic
    dists = summary.get("distributions", {})
    loc_dist = dists.get("loc", {}) or {}
    check4_pass = True
    if loc_dist:
        p25 = loc_dist.get("p25", 0)
        median = loc_dist.get("median", 0)
        p75 = loc_dist.get("p75", 0)
        p90 = loc_dist.get("p90", 0)
        p95 = loc_dist.get("p95", 0)
        p99 = loc_dist.get("p99", 0)
        max_val = loc_dist.get("max", 0)
        check4_pass = p25 <= median <= p75 <= p90 <= p95 <= p99 <= max_val

    # Check 5: gini in [0,1]
    gini = loc_dist.get("gini", 0) if loc_dist else 0
    check5_pass = 0 <= gini <= 1

    # Check 6: leaf dirs have child_count=0
    leaf_dirs = [d for d in directories if d.get("is_leaf", False)]
    leaf_check = all(d.get("child_count", 0) == 0 for d in leaf_dirs)
    leaf_count = len(leaf_dirs)

    # Check 7: file classification sum
    fc = summary.get("file_classifications", {})
    class_sum = (
        fc.get("test_file_count", 0) +
        fc.get("config_file_count", 0) +
        fc.get("docs_file_count", 0) +
        fc.get("build_file_count", 0) +
        fc.get("ci_file_count", 0) +
        fc.get("source_file_count", 0)
    )
    check7_pass = class_sum == total_files

    print_section("✓ VALIDATION EVIDENCE", width)

    # Invariant checks
    line = "  Invariant Checks:"
    print(c(BOX_V, Colors.BLUE) + line + " " * (width - len(strip_ansi(line)) - 2) + c(BOX_V, Colors.BLUE))

    def check_line(passed: bool, desc: str):
        icon = c("✓", Colors.GREEN) if passed else c("✗", Colors.RED)
        line = f"    {icon} {desc}"
        visible = len(strip_ansi(line))
        print(c(BOX_V, Colors.BLUE) + line + " " * (width - visible - 2) + c(BOX_V, Colors.BLUE))

    check_line(check1_pass, f"sum(direct.file_count) == total_files: {sum_direct_files} == {total_files}")
    check_line(check2_pass, f"sum(by_language.loc) == total_loc: {sum_lang_loc} == {total_loc}")
    check_line(rec_gte_direct, f"recursive >= direct for all dirs: {check3_count}/{check3_count} passed")
    check_line(check4_pass, "percentiles monotonic (p25 ≤ p50 ≤ p75 ≤ p90 ≤ p95 ≤ p99): PASS" if check4_pass else "percentiles monotonic: FAIL")
    check_line(check5_pass, f"gini in [0,1]: {gini:.3f} {'PASS' if check5_pass else 'FAIL'}")
    check_line(leaf_check, f"leaf dirs have child_count=0: {leaf_count}/{leaf_count} passed")
    check_line(check7_pass, f"file classifications sum: {class_sum} == {total_files}")

    # Raw data summary
    print(c(BOX_V, Colors.BLUE) + " " * (width - 2) + c(BOX_V, Colors.BLUE))
    line = "  Raw Data Checksums:"
    print(c(BOX_V, Colors.BLUE) + line + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    total_bytes = summary.get("total_bytes", 0)
    lang_count = summary.get("total_languages", 0)
    line = f"    Files scanned: {total_files}  │  Bytes processed: {total_bytes:,}"
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.DIM) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))
    line = f"    Languages detected: {lang_count}  │  Directories traversed: {total_dirs}"
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.DIM) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    print(c(BOX_V, Colors.BLUE) + " " * (width - 2) + c(BOX_V, Colors.BLUE))
    line = "  scc Version: 3.6.0  │  Schema: v2.0"
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.DIM) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    print_section_end(width)


def print_executive_summary(result: dict, width: int = 79):
    """Section 3: Enhanced Executive Summary with two-column layout."""
    summary = result.get("summary", {})
    ratios = summary.get("ratios", {})
    structure = summary.get("structure", {})
    languages = summary.get("languages", {})
    dists = summary.get("distributions", {})

    print_section("📊 EXECUTIVE SUMMARY", width)

    # Two-column header
    col_width = (width - 6) // 2
    left_header = "Codebase Size"
    right_header = "Code Quality"
    line = f"  {left_header:<{col_width}}{right_header:<{col_width}}"
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.CYAN, Colors.BOLD) + c(BOX_V, Colors.BLUE))

    left_sep = "─" * 20
    right_sep = "─" * 20
    line = f"  {left_sep:<{col_width}}{right_sep:<{col_width}}"
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.DIM) + c(BOX_V, Colors.BLUE))

    # Row helper
    def two_col(l_label, l_val, r_label, r_val):
        left = f"{l_label:<14} {l_val:>6}"
        right = f"{r_label:<18} {r_val:>6}"
        line = f"  {left:<{col_width}}{right:<{col_width}}"
        print(c(BOX_V, Colors.BLUE) + line + c(BOX_V, Colors.BLUE))

    two_col("Files", str(summary.get("total_files", 0)),
            "Avg Complexity", f"{ratios.get('avg_complexity', 0):.1f}")
    two_col("Directories", str(summary.get("total_directories", 0)),
            "Complexity Density", f"{ratios.get('complexity_density', 0):.3f}")
    two_col("Total LOC", f"{summary.get('total_loc', 0):,}",
            "DRYness (ULOC/LOC)", f"{ratios.get('dryness', 0):.1%}")
    two_col("Total Lines", f"{summary.get('total_lines', 0):,}",
            "Comment Ratio", f"{ratios.get('comment_ratio', 0):.1%}")
    two_col("Total Bytes", f"{summary.get('total_bytes', 0) // 1024} KB",
            "Blank Ratio", f"{ratios.get('blank_ratio', 0):.1%}")

    print(c(BOX_V, Colors.BLUE) + " " * (width - 2) + c(BOX_V, Colors.BLUE))

    # Languages and Structure row
    left_header = "Languages"
    right_header = "Structure"
    line = f"  {left_header:<{col_width}}{right_header:<{col_width}}"
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.CYAN, Colors.BOLD) + c(BOX_V, Colors.BLUE))

    left_sep = "─" * 20
    right_sep = "─" * 20
    line = f"  {left_sep:<{col_width}}{right_sep:<{col_width}}"
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.DIM) + c(BOX_V, Colors.BLUE))

    dominant = languages.get("dominant_language", "Unknown")
    dominant_pct = languages.get("dominant_language_pct", 0)
    polyglot = languages.get("polyglot_score", 0)

    two_col("Languages", str(summary.get("total_languages", 0)),
            "Max Depth", str(structure.get("max_depth", 0)))
    two_col("Dominant", f"{dominant} ({dominant_pct:.0%})",
            "Avg Depth", f"{structure.get('avg_depth', 0):.1f}")
    two_col("Polyglot Score", f"{polyglot:.2f}",
            "Leaf Directories", str(structure.get("leaf_directory_count", 0)))

    print_section_end(width)


def print_quality_indicators(result: dict, width: int = 79):
    """Section 4: Quality Indicators - test ratio, generated/minified detection."""
    summary = result.get("summary", {})
    fc = summary.get("file_classifications", {})
    ratios = summary.get("ratios", {})

    print_section("🎯 QUALITY INDICATORS", width)

    # File Classifications table
    line = "  File Classifications"
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.CYAN, Colors.BOLD) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))
    line = "  " + "─" * 70
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.DIM) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    # Header
    hdr = f"  {'Category':<14} {'Files':>6} {'LOC':>8} {'% of Total':>12}"
    print(c(BOX_V, Colors.BLUE) + c(hdr, Colors.DIM) + " " * (width - len(hdr) - 2) + c(BOX_V, Colors.BLUE))

    total_loc = summary.get("total_loc", 1)
    total_files = summary.get("total_files", 1)

    classifications = [
        ("Source", fc.get("source_file_count", 0), fc.get("source_loc", 0)),
        ("Test", fc.get("test_file_count", 0), fc.get("test_loc", 0)),
        ("Config", fc.get("config_file_count", 0), fc.get("config_loc", 0)),
        ("Documentation", fc.get("docs_file_count", 0), fc.get("docs_loc", 0)),
        ("Build", fc.get("build_file_count", 0), fc.get("build_loc", 0)),
        ("CI/CD", fc.get("ci_file_count", 0), fc.get("ci_loc", 0)),
    ]

    for name, count, loc in classifications:
        pct = (loc / total_loc * 100) if total_loc > 0 else 0
        row = f"  {name:<14} {count:>6} {loc:>8,} {pct:>11.1f}%"
        print(c(BOX_V, Colors.BLUE) + row + " " * (width - len(row) - 2) + c(BOX_V, Colors.BLUE))

    print(c(BOX_V, Colors.BLUE) + " " * (width - 2) + c(BOX_V, Colors.BLUE))

    # Code Health section
    line = "  Code Health"
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.CYAN, Colors.BOLD) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))
    line = "  " + "─" * 70
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.DIM) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    gen_ratio = ratios.get("generated_ratio", 0)
    min_ratio = ratios.get("minified_ratio", 0)

    line = f"  Generated Files    {gen_ratio:.1%}  │  Indicates auto-generated code"
    print(c(BOX_V, Colors.BLUE) + line + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))
    line = f"  Minified Files     {min_ratio:.1%}  │  Indicates bundled/compressed code"
    print(c(BOX_V, Colors.BLUE) + line + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    print(c(BOX_V, Colors.BLUE) + " " * (width - 2) + c(BOX_V, Colors.BLUE))

    # Assessment
    test_count = fc.get("test_file_count", 0)
    test_loc = fc.get("test_loc", 0)
    source_loc = fc.get("source_loc", 0)
    test_ratio = test_loc / source_loc if source_loc > 0 else 0

    if test_count == 0:
        assessment = c("⚠️  No test files detected - test coverage unknown", Colors.YELLOW)
    elif test_ratio < 0.3:
        assessment = c(f"⚠️  Low test ratio ({test_ratio:.1%}) - may need more tests", Colors.YELLOW)
    else:
        assessment = c(f"✓  Good test ratio ({test_ratio:.1%})", Colors.GREEN)

    line = f"  Assessment: {strip_ansi(str(assessment))}"
    print(c(BOX_V, Colors.BLUE) + "  Assessment: " + assessment + " " * max(0, width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    print_section_end(width)


def print_language_analysis(result: dict, width: int = 79):
    """Section 5: Enhanced Language Analysis with DRYness and density."""
    summary = result.get("summary", {})
    by_lang = summary.get("by_language", {})

    if not by_lang:
        return

    print_section("🌐 LANGUAGE ANALYSIS", width)

    # Sort by LOC descending
    sorted_langs = sorted(
        by_lang.items(),
        key=lambda x: x[1].get("code", 0),
        reverse=True
    )

    total_loc = summary.get("total_loc", 1)

    # Header
    hdr = f"  {'Language':<12} {'Files':>6} {'LOC':>8} {'%LOC':>6} {'Complexity':>10} {'Avg Cx':>7} {'Density':>8} {'DRYness':>8}"
    print(c(BOX_V, Colors.BLUE) + c(hdr, Colors.DIM) + c(BOX_V, Colors.BLUE))
    sep = f"  {'-'*12} {'-'*6} {'-'*8} {'-'*6} {'-'*10} {'-'*7} {'-'*8} {'-'*8}"
    print(c(BOX_V, Colors.BLUE) + c(sep, Colors.DIM) + c(BOX_V, Colors.BLUE))

    for lang, stats in sorted_langs[:8]:  # Top 8 languages
        files = stats.get("file_count", 0)
        loc = stats.get("code", 0)
        loc_pct = (loc / total_loc * 100) if total_loc > 0 else 0
        cx = stats.get("complexity_total", 0)
        avg_cx = stats.get("avg_complexity", 0)
        density = stats.get("complexity_density", 0)
        dryness = stats.get("dryness", 0)

        row = f"  {lang:<12} {files:>6} {loc:>8,} {loc_pct:>5.1f}% {cx:>10} {avg_cx:>7.1f} {density:>8.3f} {dryness:>7.1%}"
        print(c(BOX_V, Colors.BLUE) + row + c(BOX_V, Colors.BLUE))

    # Total row
    sep = f"  {'-'*12} {'-'*6} {'-'*8} {'-'*6} {'-'*10} {'-'*7} {'-'*8} {'-'*8}"
    print(c(BOX_V, Colors.BLUE) + c(sep, Colors.DIM) + c(BOX_V, Colors.BLUE))

    ratios = summary.get("ratios", {})
    row = f"  {'TOTAL':<12} {summary.get('total_files', 0):>6} {total_loc:>8,} {'100.0%':>6} {summary.get('total_complexity', 0):>10} {ratios.get('avg_complexity', 0):>7.1f} {ratios.get('complexity_density', 0):>8.3f} {ratios.get('dryness', 0):>7.1%}"
    print(c(BOX_V, Colors.BLUE) + c(row, Colors.BOLD) + c(BOX_V, Colors.BLUE))

    print_section_end(width)


def print_per_language_distributions(result: dict, width: int = 79):
    """Section 6: Per-Language Distribution Analysis."""
    summary = result.get("summary", {})
    by_lang = summary.get("by_language", {})

    if not by_lang:
        return

    print_section("📈 PER-LANGUAGE DISTRIBUTION ANALYSIS", width)

    # Header
    hdr = f"  {'Language':<11} │ {'LOC Distribution':<30} │ {'Complexity Distribution':<26}"
    print(c(BOX_V, Colors.BLUE) + c(hdr, Colors.DIM) + c(BOX_V, Colors.BLUE))
    sep = f"  {'-'*11}─┼─{'-'*30}─┼─{'-'*26}"
    print(c(BOX_V, Colors.BLUE) + c(sep, Colors.DIM) + c(BOX_V, Colors.BLUE))

    # Sort by LOC
    sorted_langs = sorted(
        by_lang.items(),
        key=lambda x: x[1].get("code", 0),
        reverse=True
    )[:5]  # Top 5 with distributions

    for lang, stats in sorted_langs:
        loc_dist = stats.get("loc_distribution")
        cx_dist = stats.get("complexity_distribution")

        if loc_dist and cx_dist:
            # First line: percentiles
            loc_str = f"median={loc_dist.get('median', 0):.0f}, p90={loc_dist.get('p90', 0):.0f}, p95={loc_dist.get('p95', 0):.0f}"
            cx_str = f"median={cx_dist.get('median', 0):.0f}, p90={cx_dist.get('p90', 0):.0f}, p95={cx_dist.get('p95', 0):.0f}"
            row = f"  {lang:<11} │ {loc_str:<30} │ {cx_str:<26}"
            print(c(BOX_V, Colors.BLUE) + row + c(BOX_V, Colors.BLUE))

            # Second line: inequality + shape
            loc_gini = loc_dist.get("gini", 0)
            loc_skew = loc_dist.get("skewness", 0)
            skew_desc = "right" if loc_skew > 0.5 else "left" if loc_skew < -0.5 else "sym"
            cx_gini = cx_dist.get("gini", 0)
            cx_skew = cx_dist.get("skewness", 0)
            cx_skew_desc = "right" if cx_skew > 0.5 else "left" if cx_skew < -0.5 else "sym"

            loc_str2 = f"gini={loc_gini:.2f}, skew={loc_skew:.1f} ({skew_desc})"
            cx_str2 = f"gini={cx_gini:.2f}, skew={cx_skew:.1f} ({cx_skew_desc})"
            row2 = f"  {'':<11} │ {loc_str2:<30} │ {cx_str2:<26}"
            print(c(BOX_V, Colors.BLUE) + c(row2, Colors.DIM) + c(BOX_V, Colors.BLUE))

            # Separator
            sep = f"  {'-'*11}─┼─{'-'*30}─┼─{'-'*26}"
            print(c(BOX_V, Colors.BLUE) + c(sep, Colors.DIM) + c(BOX_V, Colors.BLUE))

    print_section_end(width)


def print_inequality_analysis(result: dict, width: int = 79):
    """Section 7: Enhanced Code Inequality Analysis."""
    summary = result.get("summary", {})
    dists = summary.get("distributions", {})
    dist = dists.get("loc", {})

    if not dist:
        return

    print_section("📊 CODE INEQUALITY ANALYSIS", width)

    # Concentration Metrics
    line = "  Concentration Metrics (LOC)"
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.CYAN, Colors.BOLD) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))
    line = "  " + "─" * 70
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.DIM) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    gini = dist.get("gini", 0)
    theil = dist.get("theil", 0)
    hoover = dist.get("hoover", 0)
    palma = dist.get("palma", 0)

    # Interpret gini
    if gini < 0.3:
        gini_desc = "Low concentration"
    elif gini < 0.5:
        gini_desc = "Moderate concentration"
    elif gini < 0.7:
        gini_desc = "High concentration (>0.5 = concentrated)"
    else:
        gini_desc = "Very high concentration"

    line = f"  Gini Coefficient    {gini:.3f}   │ {gini_desc}"
    print(c(BOX_V, Colors.BLUE) + line + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    line = f"  Theil Index         {theil:.3f}   │ Entropy-based inequality measure"
    print(c(BOX_V, Colors.BLUE) + line + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    hoover_pct = hoover * 100
    line = f"  Hoover Index        {hoover:.3f}   │ {hoover_pct:.1f}% would need redistribution for equality"
    print(c(BOX_V, Colors.BLUE) + line + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    if palma > 0 and not math.isinf(palma):
        line = f"  Palma Ratio         {palma:.1f}x    │ Top 10% have {palma:.1f}x more than bottom 40%"
        print(c(BOX_V, Colors.BLUE) + line + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    print(c(BOX_V, Colors.BLUE) + " " * (width - 2) + c(BOX_V, Colors.BLUE))

    # Wealth Distribution
    line = "  Wealth Distribution"
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.CYAN, Colors.BOLD) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))
    line = "  " + "─" * 70
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.DIM) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    top_10 = dist.get("top_10_pct_share", 0) * 100
    top_20 = dist.get("top_20_pct_share", 0) * 100
    bottom_50 = dist.get("bottom_50_pct_share", 0) * 100

    line = f"  Top 10% of files hold    {top_10:.1f}% of all LOC"
    print(c(BOX_V, Colors.BLUE) + line + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))
    line = f"  Top 20% of files hold    {top_20:.1f}% of all LOC"
    print(c(BOX_V, Colors.BLUE) + line + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))
    line = f"  Bottom 50% of files hold  {bottom_50:.1f}% of all LOC"
    print(c(BOX_V, Colors.BLUE) + line + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    print(c(BOX_V, Colors.BLUE) + " " * (width - 2) + c(BOX_V, Colors.BLUE))

    # Interpretation
    total_files = summary.get("total_files", 0)
    top_file_count = max(1, int(total_files * 0.1))
    line = f"  Interpretation: Code is {'highly ' if gini > 0.5 else ''}concentrated in a few large files."
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.DIM) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))
    line = f"  The top {top_file_count} files contain nearly half of all code."
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.DIM) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    print_section_end(width)


def print_distribution_statistics_enhanced(result: dict, width: int = 79):
    """Section 8: Enhanced Distribution Statistics with 4-column table."""
    summary = result.get("summary", {})
    dists = summary.get("distributions", {})

    if not dists:
        return

    print_section("📈 DISTRIBUTION STATISTICS", width)

    loc = dists.get("loc", {}) or {}
    cx = dists.get("complexity", {}) or {}
    comment = dists.get("comment_ratio", {}) or {}
    bytes_d = dists.get("bytes", {}) or {}

    # Header
    hdr = f"  {'Metric':<18} {'LOC':>12} {'Complexity':>12} {'Comment%':>12} {'Bytes':>12}"
    print(c(BOX_V, Colors.BLUE) + c(hdr, Colors.DIM) + c(BOX_V, Colors.BLUE))
    sep = f"  {'-'*18} {'-'*12} {'-'*12} {'-'*12} {'-'*12}"
    print(c(BOX_V, Colors.BLUE) + c(sep, Colors.DIM) + c(BOX_V, Colors.BLUE))

    def row(label, loc_v, cx_v, comm_v, bytes_v, is_pct=False):
        if is_pct:
            line = f"  {label:<18} {loc_v:>12} {cx_v:>12} {comm_v:>11.1%} {bytes_v:>12}"
        else:
            line = f"  {label:<18} {loc_v:>12} {cx_v:>12} {comm_v:>11.1%} {bytes_v:>12,}"
        print(c(BOX_V, Colors.BLUE) + line + c(BOX_V, Colors.BLUE))

    # Basic stats
    row("Minimum", f"{loc.get('min', 0):,.0f}", f"{cx.get('min', 0):.0f}",
        comment.get('min', 0), bytes_d.get('min', 0))
    row("Maximum", f"{loc.get('max', 0):,.0f}", f"{cx.get('max', 0):.0f}",
        comment.get('max', 0), bytes_d.get('max', 0))
    row("Mean", f"{loc.get('mean', 0):,.1f}", f"{cx.get('mean', 0):.1f}",
        comment.get('mean', 0), bytes_d.get('mean', 0))
    row("Median", f"{loc.get('median', 0):,.0f}", f"{cx.get('median', 0):.0f}",
        comment.get('median', 0), bytes_d.get('median', 0))
    row("Std Dev", f"{loc.get('stddev', 0):,.1f}", f"{cx.get('stddev', 0):.1f}",
        comment.get('stddev', 0), bytes_d.get('stddev', 0))

    # Separator
    print(c(BOX_V, Colors.BLUE) + c(sep, Colors.DIM) + c(BOX_V, Colors.BLUE))

    # Percentiles
    row("P25", f"{loc.get('p25', 0):,.0f}", f"{cx.get('p25', 0):.0f}",
        comment.get('p25', 0), bytes_d.get('p25', 0))
    row("P75", f"{loc.get('p75', 0):,.0f}", f"{cx.get('p75', 0):.0f}",
        comment.get('p75', 0), bytes_d.get('p75', 0))
    row("P90", f"{loc.get('p90', 0):,.0f}", f"{cx.get('p90', 0):.0f}",
        comment.get('p90', 0), bytes_d.get('p90', 0))
    row("P95", f"{loc.get('p95', 0):,.0f}", f"{cx.get('p95', 0):.0f}",
        comment.get('p95', 0), bytes_d.get('p95', 0))
    row("P99", f"{loc.get('p99', 0):,.0f}", f"{cx.get('p99', 0):.0f}",
        comment.get('p99', 0), bytes_d.get('p99', 0))

    # Separator
    print(c(BOX_V, Colors.BLUE) + c(sep, Colors.DIM) + c(BOX_V, Colors.BLUE))

    # Shape metrics
    def skew_arrow(s):
        if s > 0.5:
            return f"{s:.2f} →"
        elif s < -0.5:
            return f"{s:.2f} ←"
        return f"{s:.2f}"

    line = f"  {'Skewness':<18} {skew_arrow(loc.get('skewness', 0)):>12} {skew_arrow(cx.get('skewness', 0)):>12} {skew_arrow(comment.get('skewness', 0)):>12} {skew_arrow(bytes_d.get('skewness', 0)):>12}"
    print(c(BOX_V, Colors.BLUE) + line + c(BOX_V, Colors.BLUE))

    line = f"  {'Kurtosis':<18} {loc.get('kurtosis', 0):>12.2f} {cx.get('kurtosis', 0):>12.2f} {comment.get('kurtosis', 0):>12.2f} {bytes_d.get('kurtosis', 0):>12.2f}"
    print(c(BOX_V, Colors.BLUE) + line + c(BOX_V, Colors.BLUE))

    line = f"  {'CV':<18} {loc.get('cv', 0):>12.2f} {cx.get('cv', 0):>12.2f} {comment.get('cv', 0):>12.2f} {bytes_d.get('cv', 0):>12.2f}"
    print(c(BOX_V, Colors.BLUE) + line + c(BOX_V, Colors.BLUE))

    line = f"  {'IQR':<18} {loc.get('iqr', 0):>12,.0f} {cx.get('iqr', 0):>12.0f} {comment.get('iqr', 0):>11.1%} {bytes_d.get('iqr', 0):>12,.0f}"
    print(c(BOX_V, Colors.BLUE) + line + c(BOX_V, Colors.BLUE))

    print(c(BOX_V, Colors.BLUE) + " " * (width - 2) + c(BOX_V, Colors.BLUE))
    line = "  Legend: → = right-skewed (long tail of large values)"
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.DIM) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    print_section_end(width)


def print_top_files_by_loc(result: dict, width: int = 79, limit: int = 20):
    """Section 10: Top N Files by Lines of Code."""
    files = result.get("files", [])

    if not files:
        return

    print_section(f"📁 TOP {limit} FILES BY LINES OF CODE", width)

    # Sort by LOC
    sorted_files = sorted(files, key=lambda f: f.get("code", 0), reverse=True)[:limit]

    # Header - wider path column (70 chars)
    hdr = f"  {'#':>3} {'File':<70} {'Lang':<10} {'LOC':>6} {'Cx':>4} {'Density':>7}"
    print(c(BOX_V, Colors.BLUE) + c(hdr, Colors.DIM) + c(BOX_V, Colors.BLUE))
    sep = f"  {'-'*3} {'-'*70} {'-'*10} {'-'*6} {'-'*4} {'-'*7}"
    print(c(BOX_V, Colors.BLUE) + c(sep, Colors.DIM) + c(BOX_V, Colors.BLUE))

    total_loc = 0
    total_cx = 0

    for i, f in enumerate(sorted_files, 1):
        path = f.get("path", "")
        # Truncate path in middle to preserve repo name and filename
        path = truncate_path_middle(path, 70)
        lang = f.get("language", "")[:10]
        loc = f.get("code", 0)
        cx = f.get("complexity", 0)
        density = f.get("complexity_density", 0)

        total_loc += loc
        total_cx += cx

        row = f"  {i:>3} {path:<70} {lang:<10} {loc:>6} {cx:>4} {density:>7.3f}"
        print(c(BOX_V, Colors.BLUE) + row + c(BOX_V, Colors.BLUE))

    # Summary
    sep = f"  {'-'*3} {'-'*70} {'-'*10} {'-'*6} {'-'*4} {'-'*7}"
    print(c(BOX_V, Colors.BLUE) + c(sep, Colors.DIM) + c(BOX_V, Colors.BLUE))

    summary = result.get("summary", {})
    total_codebase_loc = summary.get("total_loc", 1)
    total_codebase_cx = summary.get("total_complexity", 1)
    loc_pct = total_loc / total_codebase_loc * 100 if total_codebase_loc > 0 else 0
    cx_pct = total_cx / total_codebase_cx * 100 if total_codebase_cx > 0 else 0

    row = f"  Top {limit} Total{' ' * 65}{total_loc:>6} {total_cx:>4}"
    print(c(BOX_V, Colors.BLUE) + c(row, Colors.BOLD) + " " * (width - len(row) - 2) + c(BOX_V, Colors.BLUE))
    row = f"  % of Codebase{' ' * 65}{loc_pct:>5.1f}% {cx_pct:>4.1f}%"
    print(c(BOX_V, Colors.BLUE) + c(row, Colors.DIM) + " " * (width - len(row) - 2) + c(BOX_V, Colors.BLUE))

    print_section_end(width)


def print_top_files_by_complexity(result: dict, width: int = 79, limit: int = 20):
    """Section 11: Top N Files by Complexity."""
    files = result.get("files", [])

    if not files:
        return

    print_section(f"🔥 TOP {limit} FILES BY COMPLEXITY", width)

    # Sort by complexity
    sorted_files = sorted(files, key=lambda f: f.get("complexity", 0), reverse=True)[:limit]

    # Header - wider path column (70 chars)
    hdr = f"  {'#':>3} {'File':<70} {'Lang':<10} {'Cx':>4} {'LOC':>6} {'Density':>8}"
    print(c(BOX_V, Colors.BLUE) + c(hdr, Colors.DIM) + c(BOX_V, Colors.BLUE))
    sep = f"  {'-'*3} {'-'*70} {'-'*10} {'-'*4} {'-'*6} {'-'*8}"
    print(c(BOX_V, Colors.BLUE) + c(sep, Colors.DIM) + c(BOX_V, Colors.BLUE))

    high_cx_count = 0
    for i, f in enumerate(sorted_files, 1):
        path = f.get("path", "")
        # Truncate path in middle to preserve repo name and filename
        path = truncate_path_middle(path, 70)
        lang = f.get("language", "")[:10]
        cx = f.get("complexity", 0)
        loc = f.get("code", 0)
        density = f.get("complexity_density", 0)

        if cx > 50:
            high_cx_count += 1

        row = f"  {i:>3} {path:<70} {lang:<10} {cx:>4} {loc:>6} {density:>8.3f}"
        print(c(BOX_V, Colors.BLUE) + row + c(BOX_V, Colors.BLUE))

    print(c(BOX_V, Colors.BLUE) + " " * (width - 2) + c(BOX_V, Colors.BLUE))

    if high_cx_count > 0:
        line = f"  ⚠️  Files with Complexity > 50: {high_cx_count} (may benefit from refactoring)"
        print(c(BOX_V, Colors.BLUE) + c(line, Colors.YELLOW) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    print_section_end(width)


def print_top_files_by_density(result: dict, width: int = 79, limit: int = 20):
    """Section 12: Top N Files by Complexity Density."""
    files = result.get("files", [])

    if not files:
        return

    # Filter files with at least 10 LOC to avoid noise
    valid_files = [f for f in files if f.get("code", 0) >= 10]

    print_section(f"⚡ TOP {limit} FILES BY COMPLEXITY DENSITY (Cx/LOC)", width)

    # Sort by density
    sorted_files = sorted(valid_files, key=lambda f: f.get("complexity_density", 0), reverse=True)[:limit]

    # Header - wider path column (70 chars)
    hdr = f"  {'#':>3} {'File':<70} {'Lang':<10} {'Density':>8} {'Cx':>4} {'LOC':>6}"
    print(c(BOX_V, Colors.BLUE) + c(hdr, Colors.DIM) + c(BOX_V, Colors.BLUE))
    sep = f"  {'-'*3} {'-'*70} {'-'*10} {'-'*8} {'-'*4} {'-'*6}"
    print(c(BOX_V, Colors.BLUE) + c(sep, Colors.DIM) + c(BOX_V, Colors.BLUE))

    for i, f in enumerate(sorted_files, 1):
        path = f.get("path", "")
        # Truncate path in middle to preserve repo name and filename
        path = truncate_path_middle(path, 70)
        lang = f.get("language", "")[:10]
        density = f.get("complexity_density", 0)
        cx = f.get("complexity", 0)
        loc = f.get("code", 0)

        row = f"  {i:>3} {path:<70} {lang:<10} {density:>8.3f} {cx:>4} {loc:>6}"
        print(c(BOX_V, Colors.BLUE) + row + c(BOX_V, Colors.BLUE))

    print(c(BOX_V, Colors.BLUE) + " " * (width - 2) + c(BOX_V, Colors.BLUE))
    line = "  ℹ️  High density (>0.3) suggests concentrated logic - review for clarity"
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.DIM) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    print_section_end(width)


def print_directory_tree_enhanced(result: dict, width: int = 120):
    """Section 16: Complete Directory Tree with visual hierarchy.

    Shows BOTH recursive and direct stats for each directory:
    - Recursive: Total files/LOC in directory and all subdirectories
    - Direct: Files/LOC directly in this directory only (not subdirectories)
    """
    directories = result.get("directories", [])

    if not directories:
        return

    print_section("🌳 COMPLETE DIRECTORY TREE", width)

    # Calculate dynamic column widths based on terminal width
    # Layout: Directory | Recursive (Files, LOC, Cx) | Direct (Files, LOC, Cx)
    dir_col_width = max(50, width - 70)  # At least 50 chars for directory name

    # Header with both recursive and direct sections
    hdr1 = f"  {'Directory':<{dir_col_width}}  {'─── Recursive ───':^20}  {'──── Direct ────':^20}"
    print(c(BOX_V, Colors.BLUE) + c(hdr1, Colors.DIM) + c(BOX_V, Colors.BLUE))

    hdr2 = f"  {'':<{dir_col_width}}  {'Files':>6} {'LOC':>7} {'Cx':>5}  {'Files':>6} {'LOC':>7} {'Cx':>5}"
    print(c(BOX_V, Colors.BLUE) + c(hdr2, Colors.DIM) + c(BOX_V, Colors.BLUE))

    sep = f"  {'─'*dir_col_width}  {'─'*6} {'─'*7} {'─'*5}  {'─'*6} {'─'*7} {'─'*5}"
    print(c(BOX_V, Colors.BLUE) + c(sep, Colors.DIM) + c(BOX_V, Colors.BLUE))

    # Build tree structure
    min_depth = min(d.get("depth", 0) for d in directories) if directories else 0

    for d in directories:
        depth = d.get("depth", 0) - min_depth
        name = d.get("name", "")
        rec = d.get("recursive", {})
        direct = d.get("direct", {})

        # Tree prefix with visual connectors
        if depth == 0:
            prefix = ""
        else:
            prefix = "│   " * (depth - 1) + "├── "

        display_name = prefix + name
        # No artificial truncation - use full name up to column width
        if len(display_name) > dir_col_width:
            display_name = display_name[:dir_col_width - 3] + "..."

        # Recursive stats
        rec_files = rec.get("file_count", 0)
        rec_loc = rec.get("code", 0)
        rec_cx = rec.get("complexity_total", 0)

        # Direct stats
        dir_files = direct.get("file_count", 0)
        dir_loc = direct.get("code", 0)
        dir_cx = direct.get("complexity_total", 0)

        # Color coding: highlight directories with direct files
        if dir_files > 0:
            name_color = Colors.WHITE
        else:
            name_color = Colors.DIM

        row = f"  {display_name:<{dir_col_width}}  {rec_files:>6} {rec_loc:>7,} {rec_cx:>5}  {dir_files:>6} {dir_loc:>7,} {dir_cx:>5}"
        print(c(BOX_V, Colors.BLUE) + row + c(BOX_V, Colors.BLUE))

    print_section_end(width)


def print_analysis_summary(result: dict, width: int = 79):
    """Section 17: Analysis Summary with findings, concerns, and recommendations."""
    summary = result.get("summary", {})
    directories = result.get("directories", [])
    files = result.get("files", [])
    dists = summary.get("distributions", {})
    fc = summary.get("file_classifications", {})
    languages = summary.get("languages", {})

    print_section("📋 ANALYSIS SUMMARY", width)

    # Key Findings
    line = "  Key Findings:"
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.CYAN, Colors.BOLD) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))
    line = "  " + "─" * 70
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.DIM) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    # Finding 1: Code concentration
    loc_dist = dists.get("loc", {}) or {}
    gini = loc_dist.get("gini", 0)
    top_10 = loc_dist.get("top_10_pct_share", 0) * 100
    line = f"  1. Code Concentration: Top 10% of files hold {top_10:.1f}% of LOC (Gini={gini:.3f})"
    print(c(BOX_V, Colors.BLUE) + line + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    # Finding 2: Complexity hotspot
    if directories:
        top_dir = max(directories, key=lambda d: d.get("recursive", {}).get("complexity_total", 0))
        top_dir_name = top_dir.get("name", "unknown")
        top_dir_cx = top_dir.get("recursive", {}).get("complexity_total", 0)
        total_cx = summary.get("total_complexity", 1)
        cx_pct = (top_dir_cx / total_cx * 100) if total_cx > 0 else 0
        line = f"  2. Complexity Hotspot: {top_dir_name}/ directory has {cx_pct:.1f}% of complexity"
        print(c(BOX_V, Colors.BLUE) + line + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    # Finding 3: Language mix
    dominant = languages.get("dominant_language", "Unknown")
    dominant_pct = languages.get("dominant_language_pct", 0) * 100
    lang_count = summary.get("total_languages", 0)
    line = f"  3. Language Mix: {lang_count} languages, {dominant} dominant ({dominant_pct:.1f}% of LOC)"
    print(c(BOX_V, Colors.BLUE) + line + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    # Finding 4: Distribution shape
    skew = loc_dist.get("skewness", 0)
    skew_desc = "right-skewed" if skew > 0.5 else "left-skewed" if skew < -0.5 else "symmetric"
    line = f"  4. Distribution: {skew_desc.capitalize()} (skew={skew:.2f}) - {'few large files, many small' if skew > 0.5 else 'balanced'}"
    print(c(BOX_V, Colors.BLUE) + line + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    # Finding 5: Structure
    struct = summary.get("structure", {})
    max_depth = struct.get("max_depth", 0)
    line = f"  5. Structure: {'Shallow' if max_depth <= 3 else 'Deep'} (max depth {max_depth}), well-organized"
    print(c(BOX_V, Colors.BLUE) + line + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    print(c(BOX_V, Colors.BLUE) + " " * (width - 2) + c(BOX_V, Colors.BLUE))

    # Potential Concerns
    line = "  Potential Concerns:"
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.CYAN, Colors.BOLD) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))
    line = "  " + "─" * 70
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.DIM) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    concerns = []

    # Concern: No tests
    test_count = fc.get("test_file_count", 0)
    test_loc = fc.get("test_loc", 0)
    source_loc = fc.get("source_loc", 0)
    test_ratio = test_loc / source_loc if source_loc > 0 else 0
    if test_count == 0:
        concerns.append("⚠️  No test files detected (0 test:code ratio)")
    elif test_ratio < 0.3:
        concerns.append(f"⚠️  Low test ratio ({test_ratio:.1%})")

    # Concern: High complexity files
    high_cx_files = [f for f in files if f.get("complexity", 0) > 50]
    if high_cx_files:
        concerns.append(f"⚠️  {len(high_cx_files)} files exceed complexity threshold (>50)")

    # Concern: High concentration
    if gini > 0.5:
        concerns.append("⚠️  High code concentration suggests refactoring opportunities")

    for concern in concerns[:3]:
        line = f"  {concern}"
        print(c(BOX_V, Colors.BLUE) + c(line, Colors.YELLOW) + " " * (width - len(strip_ansi(line)) - 2) + c(BOX_V, Colors.BLUE))

    if not concerns:
        line = "  ✓  No major concerns detected"
        print(c(BOX_V, Colors.BLUE) + c(line, Colors.GREEN) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    print(c(BOX_V, Colors.BLUE) + " " * (width - 2) + c(BOX_V, Colors.BLUE))

    # Recommendations
    line = "  Recommendations:"
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.CYAN, Colors.BOLD) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))
    line = "  " + "─" * 70
    print(c(BOX_V, Colors.BLUE) + c(line, Colors.DIM) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    recommendations = []

    # Recommend: Review high complexity file
    if files:
        top_cx_file = max(files, key=lambda f: f.get("complexity", 0))
        cx = top_cx_file.get("complexity", 0)
        loc = top_cx_file.get("code", 0)
        path = top_cx_file.get("path", "")
        if len(path) > 40:
            path = "..." + path[-37:]
        if cx > 30:
            recommendations.append(f"→ Review {path} ({cx} complexity, {loc} LOC)")

    if test_count == 0:
        recommendations.append("→ Consider adding test coverage")

    if gini > 0.6:
        top_files = len([f for f in files if f.get("code", 0) > summary.get("total_loc", 0) * 0.1])
        recommendations.append(f"→ Split large files to reduce concentration (top {top_files} files = 50%+ of code)")

    for rec in recommendations[:3]:
        line = f"  {rec}"
        print(c(BOX_V, Colors.BLUE) + line + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    if not recommendations:
        line = "  ✓  No specific recommendations - codebase looks healthy"
        print(c(BOX_V, Colors.BLUE) + c(line, Colors.GREEN) + " " * (width - len(line) - 2) + c(BOX_V, Colors.BLUE))

    print_section_end(width)


def print_footer(output_path: str, run_time: float = 0, width: int = 79):
    """Section 18: Footer with completion status."""
    print()
    print(c("┌" + "─" * (width - 2) + "┐", Colors.GREEN))
    line = f"  ✅ Analysis complete │ JSON output: {output_path}"
    print(c("│", Colors.GREEN) + line + " " * (width - len(line) - 2) + c("│", Colors.GREEN))
    line = f"  Run time: {run_time:.2f}s │ scc v3.6.0"
    print(c("│", Colors.GREEN) + c(line, Colors.DIM) + " " * (width - len(line) - 2) + c("│", Colors.GREEN))
    print(c("└" + "─" * (width - 2) + "┘", Colors.GREEN))
    print()


# COCOMO Presets for different organization types
COCOMO_PRESETS = {
    "early_startup": {
        "a": 2.0, "b": 1.00, "c": 2.2, "d": 0.40,
        "avg_wage": 150000, "overhead": 1.5, "eaf": 0.8,
        "description": "< 10 employees, flat structure, no bureaucracy"
    },
    "growth_startup": {
        "a": 2.4, "b": 1.05, "c": 2.5, "d": 0.38,
        "avg_wage": 140000, "overhead": 1.8, "eaf": 0.9,
        "description": "10-50 employees, adding process"
    },
    "scale_up": {
        "a": 2.8, "b": 1.08, "c": 2.5, "d": 0.36,
        "avg_wage": 130000, "overhead": 2.2, "eaf": 1.0,
        "description": "50-200 employees, formal processes emerging"
    },
    "sme": {
        "a": 3.0, "b": 1.12, "c": 2.5, "d": 0.35,
        "avg_wage": 120000, "overhead": 2.4, "eaf": 1.0,
        "description": "200-500 employees, established processes"
    },
    "mid_market": {
        "a": 3.2, "b": 1.15, "c": 2.5, "d": 0.34,
        "avg_wage": 115000, "overhead": 2.6, "eaf": 1.1,
        "description": "500-2000 employees, compliance overhead"
    },
    "large_enterprise": {
        "a": 3.6, "b": 1.20, "c": 2.5, "d": 0.32,
        "avg_wage": 110000, "overhead": 3.0, "eaf": 1.2,
        "description": "2000+ employees, heavy governance"
    },
    "regulated": {
        "a": 4.0, "b": 1.25, "c": 2.8, "d": 0.30,
        "avg_wage": 120000, "overhead": 3.5, "eaf": 1.5,
        "description": "Finance, Healthcare, Defense, Government"
    },
    "open_source": {
        "a": 2.0, "b": 1.00, "c": 3.0, "d": 0.42,
        "avg_wage": 0, "overhead": 1.0, "eaf": 0.5,
        "description": "Volunteer, no cost model applicable"
    },
}


@dataclass
class MetricDistribution:
    """Statistical distribution for a metric."""
    # Basic stats
    min: float = 0
    max: float = 0
    mean: float = 0
    median: float = 0
    stddev: float = 0
    # Percentiles
    p25: float = 0
    p75: float = 0
    p90: float = 0
    p95: float = 0
    p99: float = 0
    # Shape
    skewness: float = 0
    kurtosis: float = 0
    cv: float = 0  # Coefficient of variation (stddev/mean)
    iqr: float = 0  # Interquartile range (p75 - p25)
    # Inequality metrics
    gini: float = 0
    theil: float = 0
    hoover: float = 0
    palma: float = 0
    top_10_pct_share: float = 0
    top_20_pct_share: float = 0
    bottom_50_pct_share: float = 0

    @classmethod
    def from_values(cls, values: List[float]) -> "MetricDistribution":
        """Compute distribution from a list of values."""
        if not values:
            return cls()

        n = len(values)
        sorted_vals = sorted(values)
        mean_val = statistics.mean(values)
        stddev_val = statistics.stdev(values) if n > 1 else 0
        p25_val = sorted_vals[int(n * 0.25)] if n >= 4 else sorted_vals[0]
        p75_val = sorted_vals[int(n * 0.75)] if n >= 4 else sorted_vals[-1]

        return cls(
            min=min(values),
            max=max(values),
            mean=round(mean_val, 4),
            median=round(statistics.median(values), 4),
            stddev=round(stddev_val, 4),
            p25=p25_val,
            p75=p75_val,
            p90=sorted_vals[int(n * 0.90)] if n >= 10 else sorted_vals[-1],
            p95=sorted_vals[int(n * 0.95)] if n >= 20 else sorted_vals[-1],
            p99=sorted_vals[int(n * 0.99)] if n >= 100 else sorted_vals[-1],
            skewness=round(compute_skewness(values, mean_val), 4) if n > 2 else 0,
            kurtosis=round(compute_kurtosis(values, mean_val), 4) if n > 3 else 0,
            cv=round(stddev_val / mean_val, 4) if mean_val > 0 else 0,
            iqr=round(p75_val - p25_val, 4),
            # Inequality metrics
            gini=round(compute_gini(values), 4),
            theil=round(compute_theil(values), 4),
            hoover=round(compute_hoover(values), 4),
            palma=round(compute_palma(values), 4) if n >= 10 else 0,
            top_10_pct_share=round(compute_top_share(values, 0.10), 4),
            top_20_pct_share=round(compute_top_share(values, 0.20), 4),
            bottom_50_pct_share=round(compute_bottom_share(values, 0.50), 4),
        )


def compute_skewness(values: List[float], mean: float) -> float:
    """Compute sample skewness (Fisher's definition)."""
    n = len(values)
    if n < 3:
        return 0
    std = statistics.stdev(values)
    if std == 0:
        return 0
    return sum((x - mean) ** 3 for x in values) / (n * std ** 3)


def compute_kurtosis(values: List[float], mean: float) -> float:
    """Compute excess kurtosis (Fisher's definition)."""
    n = len(values)
    if n < 4:
        return 0
    std = statistics.stdev(values)
    if std == 0:
        return 0
    return sum((x - mean) ** 4 for x in values) / (n * std ** 4) - 3


# =============================================================================
# Inequality Metrics
# =============================================================================

def compute_gini(values: List[float]) -> float:
    """Compute Gini coefficient (0=perfect equality, 1=perfect inequality).

    Uses the formula: G = (2 * sum(i * x_i) / (n * sum(x_i))) - (n + 1) / n
    where values are sorted ascending.
    """
    if not values or len(values) < 2:
        return 0.0

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    total = sum(sorted_vals)

    if total == 0:
        return 0.0

    # Weighted sum: sum of (rank * value)
    weighted_sum = sum((i + 1) * v for i, v in enumerate(sorted_vals))

    return (2 * weighted_sum) / (n * total) - (n + 1) / n


def compute_theil(values: List[float]) -> float:
    """Compute Theil entropy index (0=equality, higher=more inequality).

    Theil T = (1/n) * sum((x_i / mean) * ln(x_i / mean))
    """
    if not values or len(values) < 2:
        return 0.0

    # Filter out zeros for log calculation
    positive_vals = [v for v in values if v > 0]
    if not positive_vals:
        return 0.0

    mean_val = statistics.mean(positive_vals)
    if mean_val == 0:
        return 0.0

    n = len(positive_vals)
    theil_sum = sum((v / mean_val) * math.log(v / mean_val) for v in positive_vals)

    return theil_sum / n


def compute_hoover(values: List[float]) -> float:
    """Compute Hoover/Robin Hood index (0=equality, 1=all in one).

    Hoover = 0.5 * sum(|x_i - mean|) / sum(x_i)
    Represents the fraction that must be redistributed for equality.
    """
    if not values or len(values) < 2:
        return 0.0

    total = sum(values)
    if total == 0:
        return 0.0

    mean_val = total / len(values)
    deviation_sum = sum(abs(v - mean_val) for v in values)

    return 0.5 * deviation_sum / total


def compute_palma(values: List[float]) -> float:
    """Compute Palma ratio (top 10% share / bottom 40% share).

    Higher values indicate more inequality.
    """
    if not values or len(values) < 10:
        return 0.0

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    # Bottom 40%
    bottom_40_idx = int(n * 0.4)
    bottom_40_sum = sum(sorted_vals[:bottom_40_idx])

    # Top 10%
    top_10_idx = int(n * 0.9)
    top_10_sum = sum(sorted_vals[top_10_idx:])

    if bottom_40_sum == 0:
        return float('inf') if top_10_sum > 0 else 0.0

    return top_10_sum / bottom_40_sum


def compute_top_share(values: List[float], top_pct: float) -> float:
    """Compute share of total held by top X%.

    Args:
        values: List of values
        top_pct: Percentage as decimal (e.g., 0.10 for top 10%)

    Returns:
        Share as decimal (0 to 1)
    """
    if not values:
        return 0.0

    total = sum(values)
    if total == 0:
        return 0.0

    sorted_vals = sorted(values, reverse=True)
    n = len(sorted_vals)
    top_count = max(1, int(n * top_pct))

    top_sum = sum(sorted_vals[:top_count])
    return top_sum / total


def compute_bottom_share(values: List[float], bottom_pct: float) -> float:
    """Compute share of total held by bottom X%.

    Args:
        values: List of values
        bottom_pct: Percentage as decimal (e.g., 0.50 for bottom 50%)

    Returns:
        Share as decimal (0 to 1)
    """
    if not values:
        return 0.0

    total = sum(values)
    if total == 0:
        return 0.0

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    bottom_count = max(1, int(n * bottom_pct))

    bottom_sum = sum(sorted_vals[:bottom_count])
    return bottom_sum / total


def compute_cocomo(kloc: float, params: dict) -> dict:
    """Compute COCOMO cost estimates.

    Args:
        kloc: Thousands of lines of code
        params: COCOMO parameters (a, b, c, d, avg_wage, overhead, eaf)

    Returns:
        Dict with effort, schedule, people, and cost
    """
    if kloc <= 0:
        return {
            "effort_person_months": 0,
            "schedule_months": 0,
            "people": 0,
            "cost": 0,
        }

    effort = params["a"] * (kloc ** params["b"]) * params["eaf"]
    schedule = params["c"] * (effort ** params["d"])
    cost = effort * (params["avg_wage"] / 12) * params["overhead"]
    people = effort / schedule if schedule > 0 else 0

    return {
        "effort_person_months": round(effort, 2),
        "schedule_months": round(schedule, 2),
        "people": round(people, 2),
        "cost": round(cost, 2),
    }


# =============================================================================
# File Classification
# =============================================================================


def classify_file(path: str, filename: str, extension: str) -> Optional[str]:
    """Classify a file into a category based on name/path patterns.

    Args:
        path: Full file path
        filename: Just the filename
        extension: File extension (e.g., ".py")

    Returns:
        Classification string ("test", "config", "docs", "build", "ci") or None for source
    """
    path_lower = path.lower()
    filename_lower = filename.lower()

    # Test files - by pattern
    test_patterns = [
        "test_*.py", "*_test.py",      # Python
        "*.test.ts", "*.spec.ts",      # TypeScript
        "*.test.js", "*.spec.js",      # JavaScript
        "*Test.java", "*Tests.java",   # Java
        "*_test.go", "test_*.go",      # Go
        "*_test.rs",                   # Rust
        "*Test.cs", "*Tests.cs",       # C#
    ]
    for pattern in test_patterns:
        if fnmatch.fnmatch(filename_lower, pattern.lower()):
            return "test"

    # Test files - by directory
    test_dirs = ["tests/", "__tests__/", "test/", "spec/", "testing/"]
    for test_dir in test_dirs:
        if test_dir in path_lower:
            return "test"

    # CI files - by directory
    ci_dirs = [".github/", ".gitlab-ci", ".circleci/", ".travis"]
    for ci_dir in ci_dirs:
        if ci_dir in path_lower:
            return "ci"

    # CI files - by name
    ci_files = ["jenkinsfile", "azure-pipelines.yml", "azure-pipelines.yaml",
                ".travis.yml", "appveyor.yml", "bitbucket-pipelines.yml"]
    if filename_lower in ci_files:
        return "ci"

    # Build files - specific names (check before extension-based matches)
    build_files = ["makefile", "cmakelists.txt", "pom.xml", "build.gradle",
                   "build.gradle.kts", "gulpfile.js", "gruntfile.js",
                   "rakefile", "justfile"]
    if filename_lower in build_files:
        return "build"

    # Build files - by extension
    build_extensions = [".csproj", ".fsproj", ".vbproj", ".sln", ".gradle"]
    if extension.lower() in build_extensions:
        return "build"

    # Config files - specific names (check before extension-based matches)
    config_files = ["package.json", "tsconfig.json", "pyproject.toml",
                    "setup.py", "setup.cfg", "requirements.txt",
                    "cargo.toml", "go.mod", "go.sum"]
    if filename_lower in config_files:
        return "config"

    # Config files - by name pattern
    config_patterns = ["*.config.*", ".env*", "*.conf", "settings.*"]
    for pattern in config_patterns:
        if fnmatch.fnmatch(filename_lower, pattern.lower()):
            return "config"

    # Config files - by extension (for plain config files)
    config_extensions = [".yaml", ".yml", ".toml", ".ini", ".cfg"]
    if extension.lower() in config_extensions:
        # Exclude CI files that happen to be yaml
        if not any(ci in path_lower for ci in [".github/", ".gitlab-ci", ".circleci/"]):
            return "config"

    # Docs - by extension
    doc_extensions = [".md", ".rst", ".txt", ".adoc", ".asciidoc"]
    if extension.lower() in doc_extensions:
        return "docs"

    # Docs - by directory
    doc_dirs = ["docs/", "documentation/", "doc/"]
    for doc_dir in doc_dirs:
        if doc_dir in path_lower:
            return "docs"

    # Source file (no classification)
    return None


# Field mapping from scc PascalCase to snake_case
SCC_FIELD_MAPPING = {
    "Name": "name",
    "Lines": "lines",
    "Code": "code",
    "Comment": "comment",
    "Blank": "blank",
    "Complexity": "complexity",
    "Bytes": "bytes",
    "Language": "language",
    "Location": "location",
    "WeightedComplexity": "weighted_complexity",
    "ULOC": "uloc",
    "Binary": "binary",
    "Minified": "minified",
    "Generated": "generated",
    "Files": "files",
}


def normalize_field_names(obj: dict) -> dict:
    """Normalize scc PascalCase field names to snake_case.

    Args:
        obj: Dictionary with PascalCase field names from scc

    Returns:
        New dictionary with snake_case field names
    """
    normalized = {}
    for key, value in obj.items():
        new_key = SCC_FIELD_MAPPING.get(key, key.lower())
        normalized[new_key] = value
    return normalized


def run_scc_by_file(scc_path: Path, target: str, cwd: Path = None) -> tuple:
    """Run scc with --by-file and return all files plus raw output.

    Args:
        scc_path: Path to scc binary
        target: Target directory to analyze
        cwd: Working directory for scc (defaults to scc_path parent)

    Returns:
        Tuple of (files_list, raw_json_data):
        - files_list: List of file entries with normalized snake_case field names
        - raw_json_data: Original scc JSON output for archival (PascalCase preserved)

    Note:
        Supports incremental analysis via CHANGED_FILES environment variable.
        If set (newline-separated file paths), only those files will be analyzed.
    """
    if cwd is None:
        cwd = scc_path.parent.parent  # Assume bin/scc structure

    # Check for incremental analysis (CHANGED_FILES env var)
    changed_files = os.environ.get("CHANGED_FILES", "").strip()
    if changed_files:
        # Incremental mode: analyze specific files
        file_list = [f.strip() for f in changed_files.split('\n') if f.strip()]
        if file_list:
            # Build absolute paths for the files
            target_path = Path(target)
            abs_files = [str(target_path / f) for f in file_list if (target_path / f).exists()]
            if abs_files:
                cmd = [str(scc_path), "--by-file", "--uloc", "--min", "--gen", "-f", "json"] + abs_files
            else:
                # No files to analyze (all changed files might not exist or be filtered)
                return [], []
        else:
            cmd = [str(scc_path), target, "--by-file", "--uloc", "--min", "--gen", "-f", "json"]
    else:
        # Full analysis mode
        cmd = [str(scc_path), target, "--by-file", "--uloc", "--min", "--gen", "-f", "json"]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
        cwd=cwd,
    )

    if result.returncode != 0:
        raise RuntimeError(f"scc failed: {result.stderr}")

    raw_json = result.stdout
    data = json.loads(raw_json)
    all_files = []

    for lang_entry in data:
        lang_name = lang_entry.get("Name", "Unknown")
        for f in lang_entry.get("Files", []):
            # Normalize field names from PascalCase to snake_case
            normalized = normalize_field_names(f)
            normalized["language"] = lang_name  # Add language (already snake_case)
            all_files.append(normalized)

    return all_files, data


def get_scc_version(scc_path: Path) -> str:
    """Get scc version string."""
    try:
        result = subprocess.run(
            [str(scc_path), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def create_run_folder(
    output_base: Path,
    repo_name: str,
    target_path: str,
    raw_scc_data: list,
    analysis_result: dict,
    scc_path: Path,
    cocomo_preset: str,
) -> Path:
    """Create timestamped run folder with all outputs.

    Args:
        output_base: Base output directory (e.g., 'output')
        repo_name: Name of the repository being analyzed
        target_path: Path to the target directory
        raw_scc_data: Raw scc JSON output
        analysis_result: Processed analysis result
        scc_path: Path to scc binary
        cocomo_preset: COCOMO preset used

    Returns:
        Path to the created run folder
    """
    # Create timestamp-based folder name
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    run_name = f"{timestamp}_{repo_name}"
    run_folder = output_base / run_name

    # Create folder structure
    run_folder.mkdir(parents=True, exist_ok=True)

    # 1. Save raw scc output
    raw_path = run_folder / "raw_scc.json"
    with open(raw_path, "w") as f:
        json.dump(raw_scc_data, f, indent=2)

    # Also save a stable per-file raw output for evaluation fixtures
    full_output_path = output_base / "raw_scc_full.json"
    with open(full_output_path, "w") as f:
        json.dump(raw_scc_data, f, indent=2)

    # 2. Save analysis result
    analysis_path = run_folder / "analysis.json"
    with open(analysis_path, "w") as f:
        json.dump(analysis_result, f, indent=2)

    # 3. Save metadata
    metadata = {
        "run_id": analysis_result.get("run_id", "unknown"),
        "timestamp": analysis_result.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "repo_name": repo_name,
        "target_path": target_path,
        "scc_version": get_scc_version(scc_path),
        "scc_command": f"{scc_path} {target_path} --by-file --uloc --min --gen -f json",
        "cocomo_preset": cocomo_preset,
        "schema_version": analysis_result.get("schema_version", "2.0"),
        "file_count": len(analysis_result.get("files", [])),
        "total_loc": analysis_result.get("summary", {}).get("total_loc", 0),
        "outputs": {
            "raw_scc": "raw_scc.json",
            "analysis": "analysis.json",
            "metadata": "metadata.json",
        },
    }
    metadata_path = run_folder / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    # 4. Update 'latest' symlink
    latest_link = output_base / "latest"
    if latest_link.is_symlink():
        latest_link.unlink()
    elif latest_link.exists():
        # If it's a regular file/dir, remove it
        import shutil
        shutil.rmtree(latest_link) if latest_link.is_dir() else latest_link.unlink()
    latest_link.symlink_to(run_folder.relative_to(output_base), target_is_directory=True)

    return run_folder


def compute_language_stats(files: List[dict]) -> Dict[str, dict]:
    """Compute full stats for each language in the file list.

    Args:
        files: List of file entries from scc

    Returns:
        Dictionary mapping language name to stats dict
    """
    by_lang: Dict[str, List[dict]] = defaultdict(list)
    for f in files:
        by_lang[f.get("language", "Unknown")].append(f)

    result = {}
    for lang, lang_files in by_lang.items():
        file_count = len(lang_files)
        lines_total = sum(f.get("lines", 0) for f in lang_files)
        lines_code = sum(f.get("code", 0) for f in lang_files)
        lines_comment = sum(f.get("comment", 0) for f in lang_files)
        lines_blank = sum(f.get("blank", 0) for f in lang_files)
        total_bytes = sum(f.get("bytes", 0) for f in lang_files)
        complexity_total = sum(f.get("complexity", 0) for f in lang_files)
        uloc = sum(f.get("uloc", 0) for f in lang_files)

        # Collect lists for distributions
        lines_code_list = [f.get("code", 0) for f in lang_files]
        complexity_list = [f.get("complexity", 0) for f in lang_files]

        result[lang] = {
            "file_count": file_count,
            "lines": lines_total,
            "code": lines_code,
            "comment": lines_comment,
            "blank": lines_blank,
            "bytes": total_bytes,
            "complexity_total": complexity_total,
            "uloc": uloc,

            # Computed ratios
            "avg_file_loc": round(lines_code / file_count, 2) if file_count > 0 else 0,
            "avg_complexity": round(complexity_total / file_count, 2) if file_count > 0 else 0,
            "comment_ratio": round(lines_comment / lines_total, 4) if lines_total > 0 else 0,
            "dryness": round(uloc / lines_code, 4) if lines_code > 0 else 0,
            "complexity_density": round(complexity_total / lines_code, 4) if lines_code > 0 else 0,

            # Distributions (only if >= 3 files)
            "loc_distribution": asdict(MetricDistribution.from_values(lines_code_list)) if file_count >= 3 else None,
            "complexity_distribution": asdict(MetricDistribution.from_values(complexity_list)) if file_count >= 3 else None,
        }

    return result


def compute_directory_stats(files: List[dict]) -> dict:
    """Compute aggregate statistics for a set of files.

    Args:
        files: List of file entries from scc

    Returns:
        Dictionary with aggregate stats, computed ratios, distributions, and by_language
    """
    if not files:
        return {
            # Counts & Totals
            "file_count": 0,
            "lines": 0,
            "code": 0,
            "comment": 0,
            "blank": 0,
            "bytes": 0,
            "complexity_total": 0,
            "uloc": 0,
            "language_count": 0,
            "minified_count": 0,
            "generated_count": 0,
            # Computed Ratios
            "avg_file_loc": 0,
            "avg_complexity": 0,
            "comment_ratio": 0,
            "blank_ratio": 0,
            "dryness": 0,
            "complexity_density": 0,
            "generated_ratio": 0,
            "minified_ratio": 0,
            # File classifications
            "test_file_count": 0,
            "test_loc": 0,
            "config_file_count": 0,
            "docs_file_count": 0,
            "build_file_count": 0,
            "ci_file_count": 0,
            # Distributions
            "loc_distribution": None,
            "complexity_distribution": None,
            "comment_ratio_distribution": None,
            "bytes_distribution": None,
            # Per-language breakdown
            "by_language": {},
        }

    # Collect per-file metrics
    lines_code_list = [f.get("code", 0) for f in files]
    complexity_list = [f.get("complexity", 0) for f in files]
    comment_ratio_list = [
        f.get("comment", 0) / f.get("lines", 1) if f.get("lines", 0) > 0 else 0
        for f in files
    ]
    bytes_list = [f.get("bytes", 0) for f in files]

    # Language breakdown
    languages = defaultdict(int)
    for f in files:
        languages[f.get("language", "Unknown")] += 1

    # Compute totals
    file_count = len(files)
    lines_total = sum(f.get("lines", 0) for f in files)
    lines_code = sum(lines_code_list)
    lines_comment = sum(f.get("comment", 0) for f in files)
    lines_blank = sum(f.get("blank", 0) for f in files)
    total_bytes = sum(f.get("bytes", 0) for f in files)
    complexity_total = sum(complexity_list)
    uloc = sum(f.get("uloc", 0) for f in files)
    minified_count = sum(1 for f in files if f.get("minified", False))
    generated_count = sum(1 for f in files if f.get("generated", False))

    # Classify files
    classifications = []
    for f in files:
        loc = f.get("location", "")
        path_obj = Path(loc)
        classifications.append(classify_file(loc, path_obj.name, path_obj.suffix))

    test_files = [f for f, c in zip(files, classifications) if c == "test"]
    config_files = [f for f, c in zip(files, classifications) if c == "config"]
    docs_files = [f for f, c in zip(files, classifications) if c == "docs"]
    build_files = [f for f, c in zip(files, classifications) if c == "build"]
    ci_files = [f for f, c in zip(files, classifications) if c == "ci"]

    test_loc = sum(f.get("code", 0) for f in test_files)

    return {
        # Counts & Totals
        "file_count": file_count,
        "lines": lines_total,
        "code": lines_code,
        "comment": lines_comment,
        "blank": lines_blank,
        "bytes": total_bytes,
        "complexity_total": complexity_total,
        "uloc": uloc,
        "language_count": len(languages),
        "minified_count": minified_count,
        "generated_count": generated_count,
        # Computed Ratios
        "avg_file_loc": round(lines_code / file_count, 2) if file_count > 0 else 0,
        "avg_complexity": round(complexity_total / file_count, 2) if file_count > 0 else 0,
        "comment_ratio": round(lines_comment / lines_total, 4) if lines_total > 0 else 0,
        "blank_ratio": round(lines_blank / lines_total, 4) if lines_total > 0 else 0,
        "dryness": round(uloc / lines_code, 4) if lines_code > 0 else 0,
        "complexity_density": round(complexity_total / lines_code, 4) if lines_code > 0 else 0,
        "generated_ratio": round(generated_count / file_count, 4) if file_count > 0 else 0,
        "minified_ratio": round(minified_count / file_count, 4) if file_count > 0 else 0,
        # File classifications
        "test_file_count": len(test_files),
        "test_loc": test_loc,
        "config_file_count": len(config_files),
        "docs_file_count": len(docs_files),
        "build_file_count": len(build_files),
        "ci_file_count": len(ci_files),
        # Distributions (only if >= 3 files)
        "loc_distribution": asdict(MetricDistribution.from_values(lines_code_list)) if file_count >= 3 else None,
        "complexity_distribution": asdict(MetricDistribution.from_values(complexity_list)) if file_count >= 3 else None,
        "comment_ratio_distribution": asdict(MetricDistribution.from_values(comment_ratio_list)) if file_count >= 3 else None,
        "bytes_distribution": asdict(MetricDistribution.from_values(bytes_list)) if file_count >= 3 else None,
        # Per-language breakdown
        "by_language": compute_language_stats(files),
    }


def format_file_entry(f: dict) -> dict:
    """Format a file entry for output.

    Args:
        f: Raw file entry from scc (keys are lowercase after normalization)

    Returns:
        Formatted file entry with computed ratios and classification
    """
    # Keys are normalized to lowercase by run_scc_by_file
    location = f.get("location", "") or f.get("Location", "")
    path_obj = Path(location)
    lines = f.get("lines", 0)
    code = f.get("code", 0)
    comment = f.get("comment", 0)
    blank = f.get("blank", 0)
    uloc = f.get("uloc", 0) or f.get("Uloc", 0)
    complexity = f.get("complexity", 0)
    bytes_val = f.get("bytes", 0)
    filename = path_obj.name
    extension = path_obj.suffix

    return {
        # Identity
        "path": location,
        "filename": filename,
        "directory": str(path_obj.parent),
        "language": f.get("language", "Unknown"),
        "extension": extension,

        # Line counts
        "lines": lines,
        "code": code,
        "comment": comment,
        "blank": blank,
        "bytes": bytes_val,
        "complexity": complexity,
        "uloc": uloc,

        # Ratios
        "comment_ratio": round(comment / lines, 4) if lines > 0 else 0,
        "blank_ratio": round(blank / lines, 4) if lines > 0 else 0,
        "code_ratio": round(code / lines, 4) if lines > 0 else 0,
        "complexity_density": round(complexity / code, 4) if code > 0 else 0,
        "dryness": round(uloc / code, 4) if code > 0 else 0,
        "bytes_per_loc": round(bytes_val / code, 2) if code > 0 else 0,

        # Flags (keys are lowercase after normalization)
        "is_minified": f.get("minified", False) or f.get("Minified", False),
        "is_generated": f.get("generated", False) or f.get("Generated", False),
        "is_binary": f.get("binary", False) or f.get("Binary", False),

        # Classification
        "classification": classify_file(location, filename, extension),
    }


def analyze_directories(files: List[dict], cocomo_preset: str = "sme") -> dict:
    """Analyze files and build directory tree with statistics.

    Args:
        files: List of file entries from scc
        cocomo_preset: Name of COCOMO preset to use

    Returns:
        Complete analysis result with directories, files, and summary
    """
    if not files:
        return {
            "schema_version": "2.1",
            "run_id": f"dir-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "root_path": "",
            "directories": [],
            "files": [],
            "summary": {
                "total_files": 0,
                "total_directories": 0,
                "total_loc": 0,
                "total_lines": 0,
                "total_comment": 0,
                "total_blank": 0,
                "total_bytes": 0,
                "total_complexity": 0,
                "total_uloc": 0,
                "total_languages": 0,
                "structure": {"max_depth": 0, "avg_depth": 0, "leaf_directory_count": 0, "avg_files_per_directory": 0},
                "ratios": {},
                "file_classifications": {},
                "languages": {},
                "distributions": {},
                "by_language": {},
                "cocomo": {},
            },
        }

    # Build directory structure
    dir_files = defaultdict(list)  # path -> [files directly in this dir]
    all_dirs = set()

    for f in files:
        location = f.get("location", "")
        path = Path(location)
        parent = str(path.parent)
        dir_files[parent].append(f)

        # Track all ancestor directories
        for i in range(1, len(path.parts)):
            all_dirs.add("/".join(path.parts[:i]))

    all_dirs = sorted(all_dirs)

    # Compute root depth for relative depth calculation
    root_depth = min(d.count("/") for d in all_dirs) if all_dirs else 0

    # Compute stats for each directory
    directories = []

    for dir_path in all_dirs:
        # Direct files (only in this directory)
        direct_files = dir_files.get(dir_path, [])

        # Recursive files (this directory + all subdirectories)
        recursive_files = []
        for other_path, other_files in dir_files.items():
            if other_path == dir_path or other_path.startswith(dir_path + "/"):
                recursive_files.extend(other_files)

        # Compute stats
        direct_stats = compute_directory_stats(direct_files)
        recursive_stats = compute_directory_stats(recursive_files)

        # Immediate subdirectories
        subdirs = [
            d for d in all_dirs
            if d.startswith(dir_path + "/") and d.count("/") == dir_path.count("/") + 1
        ]

        # Structural metrics
        is_leaf = len(subdirs) == 0
        child_count = len(subdirs)
        depth = dir_path.count("/") - root_depth

        directories.append({
            "path": dir_path,
            "name": Path(dir_path).name,
            "depth": depth,
            "is_leaf": is_leaf,
            "child_count": child_count,
            "direct": direct_stats,
            "recursive": recursive_stats,
            "subdirectories": sorted(subdirs),
        })

    # Sort by path for output
    directories.sort(key=lambda d: d["path"])

    # Format all files at root level
    all_formatted_files = [format_file_entry(f) for f in files]

    # Compute summary totals
    total_loc = sum(f.get("code", 0) for f in files)
    total_lines = sum(f.get("lines", 0) for f in files)
    total_comment = sum(f.get("comment", 0) for f in files)
    total_blank = sum(f.get("blank", 0) for f in files)
    total_bytes = sum(f.get("bytes", 0) for f in files)
    total_complexity = sum(f.get("complexity", 0) for f in files)
    total_uloc = sum(f.get("uloc", 0) for f in files)
    total_minified = sum(1 for f in files if f.get("minified", False))
    total_generated = sum(1 for f in files if f.get("generated", False))

    # Language counts
    lang_file_counts: Dict[str, int] = defaultdict(int)
    lang_loc_counts: Dict[str, int] = defaultdict(int)
    for f in files:
        lang = f.get("language", "Unknown")
        lang_file_counts[lang] += 1
        lang_loc_counts[lang] += f.get("code", 0)

    # File classifications at summary level
    classifications = []
    for f in files:
        loc = f.get("location", "")
        path_obj = Path(loc)
        classifications.append(classify_file(loc, path_obj.name, path_obj.suffix))

    test_files = [(f, c) for f, c in zip(files, classifications) if c == "test"]
    config_files = [(f, c) for f, c in zip(files, classifications) if c == "config"]
    docs_files = [(f, c) for f, c in zip(files, classifications) if c == "docs"]
    build_files = [(f, c) for f, c in zip(files, classifications) if c == "build"]
    ci_files = [(f, c) for f, c in zip(files, classifications) if c == "ci"]
    source_files = [(f, c) for f, c in zip(files, classifications) if c is None]

    test_loc = sum(f.get("code", 0) for f, _ in test_files)
    config_loc = sum(f.get("code", 0) for f, _ in config_files)
    docs_loc = sum(f.get("code", 0) for f, _ in docs_files)
    build_loc = sum(f.get("code", 0) for f, _ in build_files)
    ci_loc = sum(f.get("code", 0) for f, _ in ci_files)
    source_loc = sum(f.get("code", 0) for f, _ in source_files)

    # Structure metrics
    max_depth = max(d["depth"] for d in directories) if directories else 0
    avg_depth = sum(d["depth"] for d in directories) / len(directories) if directories else 0
    leaf_count = sum(1 for d in directories if d["is_leaf"])
    avg_files_per_dir = len(files) / len(directories) if directories else 0

    # Distribution lists for summary
    loc_list = [f.get("code", 0) for f in files]
    complexity_list = [f.get("complexity", 0) for f in files]
    comment_ratio_list = [
        f.get("comment", 0) / f.get("lines", 1) if f.get("lines", 0) > 0 else 0
        for f in files
    ]
    bytes_list = [f.get("bytes", 0) for f in files]

    # Dominant language
    dominant_lang = max(lang_loc_counts, key=lang_loc_counts.get) if lang_loc_counts else "Unknown"
    dominant_loc = lang_loc_counts.get(dominant_lang, 0)
    dominant_pct = dominant_loc / total_loc if total_loc > 0 else 0
    polyglot_score = 1 - dominant_pct if total_loc > 0 else 0

    # Single file languages
    single_file_langs = [lang for lang, count in lang_file_counts.items() if count == 1]

    # Compute all COCOMO presets
    kloc = total_loc / 1000
    cocomo_all = {
        preset_name: compute_cocomo(kloc, preset_params)
        for preset_name, preset_params in COCOMO_PRESETS.items()
    }

    # Root path detection
    root_path = ""
    if files:
        first_loc = files[0].get("location", "")
        parts = first_loc.split("/")
        if len(parts) > 1:
            root_path = parts[0]

    return {
        "schema_version": "2.1",
        "run_id": f"dir-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "root_path": root_path,

        "directories": directories,
        "files": all_formatted_files,

        "summary": {
            "total_files": len(files),
            "total_directories": len(directories),
            "total_loc": total_loc,
            "total_lines": total_lines,
            "total_comment": total_comment,
            "total_blank": total_blank,
            "total_bytes": total_bytes,
            "total_complexity": total_complexity,
            "total_uloc": total_uloc,
            "total_languages": len(lang_file_counts),

            "structure": {
                "max_depth": max_depth,
                "avg_depth": round(avg_depth, 2),
                "leaf_directory_count": leaf_count,
                "avg_files_per_directory": round(avg_files_per_dir, 2),
            },

            "ratios": {
                "avg_file_loc": round(total_loc / len(files), 2) if files else 0,
                "avg_complexity": round(total_complexity / len(files), 2) if files else 0,
                "comment_ratio": round(total_comment / total_lines, 4) if total_lines > 0 else 0,
                "blank_ratio": round(total_blank / total_lines, 4) if total_lines > 0 else 0,
                "dryness": round(total_uloc / total_loc, 4) if total_loc > 0 else 0,
                "complexity_density": round(total_complexity / total_loc, 4) if total_loc > 0 else 0,
                "generated_ratio": round(total_generated / len(files), 4) if files else 0,
                "minified_ratio": round(total_minified / len(files), 4) if files else 0,
            },

            "file_classifications": {
                "test_file_count": len(test_files),
                "test_loc": test_loc,
                "test_ratio": round(len(test_files) / len(files), 4) if files else 0,
                "test_to_code_ratio": round(test_loc / source_loc, 4) if source_loc > 0 else 0,
                "config_file_count": len(config_files),
                "config_loc": config_loc,
                "docs_file_count": len(docs_files),
                "docs_loc": docs_loc,
                "build_file_count": len(build_files),
                "build_loc": build_loc,
                "ci_file_count": len(ci_files),
                "ci_loc": ci_loc,
                "source_file_count": len(source_files),
                "source_loc": source_loc,
            },

            "languages": {
                "by_files": dict(lang_file_counts),
                "by_loc": dict(lang_loc_counts),
                "dominant_language": dominant_lang,
                "dominant_language_pct": round(dominant_pct, 4),
                "polyglot_score": round(polyglot_score, 4),
                "single_file_languages": single_file_langs,
            },

            "distributions": {
                "loc": asdict(MetricDistribution.from_values(loc_list)) if len(files) >= 3 else None,
                "complexity": asdict(MetricDistribution.from_values(complexity_list)) if len(files) >= 3 else None,
                "comment_ratio": asdict(MetricDistribution.from_values(comment_ratio_list)) if len(files) >= 3 else None,
                "bytes": asdict(MetricDistribution.from_values(bytes_list)) if len(files) >= 3 else None,
            },

            "by_language": compute_language_stats(files),

            "cocomo": cocomo_all,
        },
    }


# =============================================================================
# Multi-Repository Discovery and Interactive Menu
# =============================================================================

def discover_repos(eval_repos_path: str) -> List[Dict[str, Any]]:
    """Scan eval-repos directory for all analyzable repositories.

    Discovers:
    - Synthetic repos: Each language subdirectory in eval-repos/synthetic/
    - Real repos: Git submodules in eval-repos/real/

    Args:
        eval_repos_path: Path to eval-repos directory

    Returns:
        List of repo dictionaries with name, path, type, and description
    """
    repos = []

    # Check synthetic (each language subdirectory is a separate repo)
    synthetic_path = os.path.join(eval_repos_path, "synthetic")
    if os.path.isdir(synthetic_path):
        for name in sorted(os.listdir(synthetic_path)):
            lang_path = os.path.join(synthetic_path, name)
            if os.path.isdir(lang_path) and not name.startswith("."):
                repos.append({
                    "name": name,
                    "path": lang_path,
                    "type": "synthetic",
                    "initialized": True,
                    "description": f"Synthetic {name.title()} repo"
                })

    # Check real (git submodules)
    real_path = os.path.join(eval_repos_path, "real")
    if os.path.isdir(real_path):
        for name in sorted(os.listdir(real_path)):
            repo_path = os.path.join(real_path, name)
            if os.path.isdir(repo_path) and not name.startswith("."):
                # Check if initialized (has files beyond .git)
                try:
                    contents = os.listdir(repo_path)
                    has_content = any(f for f in contents if f != ".git")
                except OSError:
                    has_content = False
                repos.append({
                    "name": name,
                    "path": repo_path,
                    "type": "real",
                    "initialized": has_content,
                    "description": "Real OSS repository"
                })

    return repos


def show_repo_menu(repos: List[Dict[str, Any]], width: int) -> Optional[Dict[str, Any]]:
    """Display interactive repository selection menu.

    Args:
        repos: List of discovered repositories
        width: Terminal width for formatting

    Returns:
        Selected repo dict, or None if user quit
    """
    print()
    print_section("📁 REPOSITORY SELECTOR", width)

    # Header
    hdr = f"  {'#':>3}   {'Type':<10} {'Repository':<20} {'Status':<15} {'Description':<40}"
    print(c(BOX_V, Colors.BLUE) + c(hdr, Colors.DIM) + c(BOX_V, Colors.BLUE))
    sep = f"  {'─'*3} {'─'*10} {'─'*20} {'─'*15} {'─'*40}"
    print(c(BOX_V, Colors.BLUE) + c(sep, Colors.DIM) + c(BOX_V, Colors.BLUE))

    # List repos
    for i, repo in enumerate(repos, 1):
        status = c("Ready", Colors.GREEN) if repo.get("initialized", True) else c("Not initialized", Colors.YELLOW)
        status_plain = "Ready" if repo.get("initialized", True) else "Not initialized"
        type_color = Colors.CYAN if repo["type"] == "synthetic" else Colors.MAGENTA
        row = f"  {i:>3}   {c(repo['type'], type_color):<10} {repo['name']:<20} {status_plain:<15} {repo['description']:<40}"
        # Handle color in status
        if repo.get("initialized", True):
            row = f"  {i:>3}   {c(repo['type'], type_color):<21} {repo['name']:<20} {c('Ready', Colors.GREEN):<25} {repo['description']:<40}"
        else:
            row = f"  {i:>3}   {c(repo['type'], type_color):<21} {repo['name']:<20} {c('Not initialized', Colors.YELLOW):<25} {repo['description']:<40}"
        print(c(BOX_V, Colors.BLUE) + row + c(BOX_V, Colors.BLUE))

    print(c(BOX_V, Colors.BLUE) + " " * (width - 2) + c(BOX_V, Colors.BLUE))
    print_section_end(width)

    # Prompt for selection
    while True:
        try:
            choice = input(f"\n  Enter number (1-{len(repos)}), 'q' to quit: ").strip().lower()
            if choice == 'q':
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(repos):
                selected = repos[idx]
                if not selected.get("initialized", True):
                    print(c(f"  ⚠️  Repository '{selected['name']}' is not initialized.", Colors.YELLOW))
                    print(c("     Run: git submodule update --init --recursive", Colors.DIM))
                    continue
                return selected
            print(f"  Invalid choice. Enter 1-{len(repos)} or 'q'.")
        except ValueError:
            print(f"  Invalid choice. Enter 1-{len(repos)} or 'q'.")
        except (KeyboardInterrupt, EOFError):
            print()
            return None


def run_analysis_dashboard(result: dict, target_path: str, output_file: str, start_time: float, width: int):
    """Print the complete v2.0 analysis dashboard.

    Args:
        result: Analysis result dictionary
        target_path: Path that was analyzed
        output_file: Output JSON file path
        start_time: Time when analysis started (for run time calculation)
        width: Terminal width for formatting
    """
    import time

    # =========================================================================
    # v2.0 DASHBOARD - 18 Sections
    # =========================================================================

    # Section 1: Header & Metadata
    print_header_metadata(result, target_path, width)

    # Section 2: Validation Evidence
    print_validation_evidence(result, width)

    # Section 3: Executive Summary
    print_executive_summary(result, width)

    # Section 4: Quality Indicators
    print_quality_indicators(result, width)

    # Section 5: Language Analysis
    print_language_analysis(result, width)

    # Section 6: Per-Language Distributions
    print_per_language_distributions(result, width)

    # Section 7: Code Inequality Analysis
    print_inequality_analysis(result, width)

    # Section 8: Distribution Statistics
    print_distribution_statistics_enhanced(result, width)

    # Section 9: COCOMO Cost Estimates
    print_cocomo_comparison(result["summary"], width)

    # Section 10: Top 20 Files by LOC
    print_top_files_by_loc(result, width, limit=20)

    # Section 11: Top 20 Files by Complexity
    print_top_files_by_complexity(result, width, limit=20)

    # Section 12: Top 20 Files by Density
    print_top_files_by_density(result, width, limit=20)

    # Section 13: Directory Structure Overview
    print_directory_structure(result["summary"], width)

    # Section 14: Top 10 Directories by Complexity
    print_top_directories_enhanced(result["directories"], width)

    # Section 15: Top 10 Directories by Direct Files
    print_top_direct_directories(result["directories"], width, limit=10)

    # Section 16: Complete Directory Tree
    print_directory_tree_enhanced(result, width)

    # Section 17: Analysis Summary
    print_analysis_summary(result, width)

    # Section 18: Footer
    run_time = time.time() - start_time
    print_footer(output_file, run_time, width)


def main():
    """Main entry point for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze directory tree with pure metrics and distribution statistics"
    )
    parser.add_argument("target", nargs="?", default=".", help="Target directory to analyze (or eval-repos for interactive mode)")
    parser.add_argument("--scc", default="./bin/scc", help="Path to scc binary")
    parser.add_argument(
        "--output", "-o",
        default="outputs/directory_analysis.json",
        help="Output file path"
    )
    parser.add_argument(
        "--cocomo-preset",
        default="sme",
        choices=list(COCOMO_PRESETS.keys()),
        help="COCOMO preset for cost estimation"
    )
    parser.add_argument(
        "--list-presets",
        action="store_true",
        help="List available COCOMO presets and exit"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive mode: discover and select repositories from eval-repos"
    )

    args = parser.parse_args()

    # Handle color settings
    if args.no_color or not sys.stdout.isatty():
        set_color_enabled(False)

    # List presets if requested
    if args.list_presets:
        print(c("Available COCOMO presets:", Colors.CYAN, Colors.BOLD))
        print()
        for name, params in COCOMO_PRESETS.items():
            desc = params.get("description", "")
            print(f"  {c(name, Colors.GREEN):<30s} {c(desc, Colors.DIM)}")
            print(c(f"    a={params['a']}, b={params['b']}, c={params['c']}, d={params['d']}", Colors.DIM))
            print(c(f"    avg_wage=${params['avg_wage']:,}, overhead={params['overhead']}, eaf={params['eaf']}", Colors.DIM))
            print()
        return

    import time

    # Dashboard width - auto-detect terminal size (default 120, minimum 80)
    width = get_terminal_width()

    # Interactive mode: discover and analyze multiple repositories
    if args.interactive or (os.path.isdir(os.path.join(args.target, "synthetic")) and
                            os.path.isdir(os.path.join(args.target, "real"))):
        repos = discover_repos(args.target)
        if not repos:
            print(c(f"No repositories found in {args.target}", Colors.RED))
            return

        scc_path = Path(args.scc)

        while True:
            selected = show_repo_menu(repos, width)
            if selected is None:
                print(c("\n  Goodbye! 👋", Colors.CYAN))
                return

            target_path = selected["path"]
            repo_name = selected["name"]

            print()
            print(c(f"═══════════════════════════════════════════════════════════════════════", Colors.CYAN))
            print(c(f"  Analyzing: {repo_name} ({selected['type']})", Colors.CYAN, Colors.BOLD))
            print(c(f"  Path: {target_path}", Colors.DIM))
            print(c(f"═══════════════════════════════════════════════════════════════════════", Colors.CYAN))

            start_time = time.time()

            # Run analysis
            print()
            print(c("⏳ Running scc...", Colors.DIM), end=" ", flush=True)
            files, raw_scc_data = run_scc_by_file(scc_path, target_path)
            print(c(f"{len(files)} files found", Colors.GREEN))

            result = analyze_directories(files, args.cocomo_preset)

            # Save output to timestamped run folder
            output_base = Path("outputs")
            run_folder = create_run_folder(
                output_base=output_base,
                repo_name=repo_name,
                target_path=target_path,
                raw_scc_data=raw_scc_data,
                analysis_result=result,
                scc_path=scc_path,
                cocomo_preset=args.cocomo_preset,
            )
            output_file = str(run_folder / "analysis.json")

            # Print dashboard
            run_analysis_dashboard(result, target_path, output_file, start_time, width)
            print(c(f"  📂 Run folder: {run_folder}", Colors.DIM))

            # Prompt to continue
            print()
            cont = input(c("  Press Enter to select another repo (or 'q' to quit): ", Colors.DIM)).strip().lower()
            if cont == 'q':
                print(c("\n  Goodbye! 👋", Colors.CYAN))
                return

        return

    # Single target mode (original behavior)
    start_time = time.time()

    # Run scc
    print()
    print(c("⏳ Running scc...", Colors.DIM), end=" ", flush=True)
    scc_path = Path(args.scc)
    files, raw_scc_data = run_scc_by_file(scc_path, args.target)
    print(c(f"{len(files)} files found", Colors.GREEN))

    # Analyze
    result = analyze_directories(files, args.cocomo_preset)

    # Derive repo name from target path
    repo_name = Path(args.target).name or "analysis"

    # Determine output location
    output_path = Path(args.output)
    is_default_output = args.output == "outputs/directory_analysis.json"

    if is_default_output:
        # Legacy behavior: create timestamped run folder
        output_base = Path("outputs")
        run_folder = create_run_folder(
            output_base=output_base,
            repo_name=repo_name,
            target_path=args.target,
            raw_scc_data=raw_scc_data,
            analysis_result=result,
            scc_path=scc_path,
            cocomo_preset=args.cocomo_preset,
        )
        output_file = str(run_folder / "analysis.json")
    else:
        # Direct output: write directly to specified path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_file = str(output_path)
        run_folder = output_path.parent
        # Write analysis result
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)

    # Print dashboard
    run_analysis_dashboard(result, args.target, output_file, start_time, width)
    print(c(f"  📂 Run folder: {run_folder}", Colors.DIM))


if __name__ == "__main__":
    main()
