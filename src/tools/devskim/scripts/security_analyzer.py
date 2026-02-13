#!/usr/bin/env python3
"""Security analysis using DevSkim.

Detects security vulnerabilities using Microsoft's DevSkim regex-based analyzer.
Works on non-compiling code - ideal for due diligence on partial codebases.
Includes 16-section dashboard visualization.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shared.path_utils import normalize_file_path, normalize_dir_path
from shared.severity import normalize_severity


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


def format_percent(n: float) -> str:
    """Format a percentage."""
    return f"{n:.1f}%"


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
# DevSkim Rule-to-Category Mapping
# =============================================================================

# Map DevSkim rule IDs to DD security categories
# Note: Some DevSkim rules cover multiple issues. We'll use message-based mapping for accuracy.
RULE_TO_CATEGORY_MAP = {
    # SQL Injection
    "DS104456": "sql_injection",  # Dynamic SQL query construction
    "DS127888": "sql_injection",  # SQL command from user input

    # Hardcoded Secrets
    "DS134411": "hardcoded_secret",  # Hardcoded credentials
    "DS114352": "hardcoded_secret",  # Hardcoded API keys
    "DS173237": "hardcoded_secret",  # Hardcoded password
    "DS117838": "hardcoded_secret",  # Hardcoded symmetric key
    "DS148264": "insecure_random",  # Weak/non-cryptographic random number generator
    "DS127901": "hardcoded_secret",  # Password in config
    "DS160340": "hardcoded_secret",  # AWS access key
    "DS114375": "hardcoded_secret",  # Private key in code
    "DS115656": "hardcoded_secret",  # Hardcoded token

    # Insecure Cryptography
    "DS161085": "insecure_crypto",  # Weak cryptographic algorithm (MD5/SHA1)
    "DS126858": "insecure_crypto",  # Weak/Broken Hash Algorithm (MD5/SHA1)
    "DS144436": "insecure_crypto",  # ECB mode usage
    "DS197800": "insecure_crypto",  # DES usage
    "DS106863": "insecure_crypto",  # DES block cipher
    "DS187371": "insecure_crypto",  # Weak cipher mode / RC2/RC4 usage
    "DS168931": "insecure_crypto",  # Weak PRNG
    "DS156603": "insecure_crypto",  # Insufficient key size
    "DS109501": "insecure_crypto",  # Hardcoded IV
    "DS173287": "insecure_crypto",  # Weak hash algorithm
    "DS176620": "insecure_crypto",  # Disabled certificate validation
    "DS195456": "insecure_crypto",  # Outdated TLS version

    # Path Traversal
    "DS175862": "path_traversal",  # Path traversal vulnerability
    "DS162155": "path_traversal",  # File path from user input
    "DS172411": "path_traversal",  # Directory traversal

    # Cross-Site Scripting (XSS)
    "DS137138": "xss",  # Cross-site scripting
    "DS115253": "xss",  # HTML injection
    "DS183166": "xss",  # DOM-based XSS
    "DS126188": "xss",  # JavaScript eval

    # Deserialization
    "DS181731": "deserialization",  # Insecure deserialization
    "DS113853": "deserialization",  # BinaryFormatter usage
    "DS162963": "deserialization",  # TypeNameHandling
    "DS172185": "deserialization",  # JavaScriptSerializer unsafe
    "DS425040": "deserialization",  # Do not deserialize untrusted data

    # XXE (XML External Entity)
    "DS168931": "xxe",  # XML external entity injection
    "DS131307": "xxe",  # DTD processing enabled
    "DS132956": "xxe",  # External entity resolution

    # Command Injection
    "DS112860": "command_injection",  # OS command injection
    "DS117840": "command_injection",  # Shell execution
    "DS161095": "command_injection",  # Process.Start with user input

    # LDAP Injection
    "DS137138": "ldap_injection",  # LDAP injection

    # Open Redirect
    "DS176209": "open_redirect",  # Open redirect vulnerability

    # SSRF
    "DS173262": "ssrf",  # Server-side request forgery

    # CSRF
    "DS180683": "csrf",  # Missing anti-forgery token

    # Information Disclosure
    "DS186372": "information_disclosure",  # Debug mode enabled
    "DS126857": "information_disclosure",  # Stack trace exposure
    "DS142853": "information_disclosure",  # Error details exposed
    "DS162092": "information_disclosure",  # Debug code in production

    # Broken Access Control
    "DS137139": "broken_access_control",  # Missing authorization

    # Security Misconfiguration
    "DS176195": "security_misconfiguration",  # Debug compilation
    "DS101136": "security_misconfiguration",  # Trace enabled
    "DS135675": "security_misconfiguration",  # Custom errors disabled
    "DS119977": "security_misconfiguration",  # HTTPS not enforced

    # Custom Caldera Rules
    "CALDERA001": "insecure_random",  # System.Random for security
    "CALDERA002": "xxe",  # XmlResolver XXE
    "CALDERA003": "xxe",  # DtdProcessing XXE
    "CALDERA004": "xxe",  # XmlTextReader XXE
    "CALDERA005": "command_injection",  # Process.Start with concatenation
    "CALDERA006": "command_injection",  # Shell command execution
    "CALDERA007": "security_misconfiguration",  # HttpOnly=false
    "CALDERA008": "security_misconfiguration",  # Secure=false
    "CALDERA009": "security_misconfiguration",  # CORS AllowAnyOrigin
}

# Map DevSkim rule IDs to CWE IDs for traceability
RULE_TO_CWE_MAP: dict[str, list[str]] = {
    # Custom Caldera Rules
    "CALDERA001": ["CWE-330"],   # Insufficient Random Values
    "CALDERA002": ["CWE-611"],   # XXE Injection
    "CALDERA003": ["CWE-611"],   # XXE Injection
    "CALDERA004": ["CWE-611"],   # XXE Injection
    "CALDERA005": ["CWE-78"],    # OS Command Injection
    "CALDERA006": ["CWE-78"],    # OS Command Injection
    "CALDERA007": ["CWE-1004"],  # Cookie Without HttpOnly Flag
    "CALDERA008": ["CWE-614"],   # Cookie Without Secure Attribute
    "CALDERA009": ["CWE-942"],   # Permissive Cross-domain Policy

    # DevSkim built-in rules
    "DS126858": ["CWE-328"],     # Weak hash algorithm (MD5/SHA1)
    "DS187371": ["CWE-327"],     # Weak cipher mode (RC2/RC4)
    "DS106863": ["CWE-326"],     # DES usage (inadequate key size)
    "DS197800": ["CWE-326"],     # DES usage
    "DS425040": ["CWE-502"],     # Insecure deserialization
    "DS137138": ["CWE-319"],     # Cleartext transmission (insecure transport)
    "DS162092": ["CWE-489"],     # Debug code in production
    "DS104456": ["CWE-89"],      # SQL injection
    "DS127888": ["CWE-89"],      # SQL command from user input
    "DS134411": ["CWE-798"],     # Hardcoded credentials
    "DS114352": ["CWE-798"],     # Hardcoded API keys
    "DS173237": ["CWE-798"],     # Hardcoded password
    "DS117838": ["CWE-321"],     # Hardcoded symmetric key
    "DS148264": ["CWE-330"],     # Weak/non-cryptographic PRNG
    "DS175862": ["CWE-22"],      # Path traversal
    "DS162155": ["CWE-22"],      # File path from user input
    "DS172411": ["CWE-22"],      # Directory traversal
    "DS181731": ["CWE-502"],     # Insecure deserialization
    "DS113853": ["CWE-502"],     # BinaryFormatter usage
    "DS162963": ["CWE-502"],     # TypeNameHandling
    "DS168931": ["CWE-611"],     # XML external entity injection
    "DS131307": ["CWE-611"],     # DTD processing enabled
    "DS132956": ["CWE-611"],     # External entity resolution
    "DS112860": ["CWE-78"],      # OS command injection
    "DS117840": ["CWE-78"],      # Shell execution
    "DS161095": ["CWE-78"],      # Process.Start with user input
    "DS176209": ["CWE-601"],     # Open redirect
    "DS173262": ["CWE-918"],     # SSRF
    "DS180683": ["CWE-352"],     # Missing anti-forgery token (CSRF)
    "DS186372": ["CWE-489"],     # Debug mode enabled
    "DS126857": ["CWE-209"],     # Stack trace exposure
    "DS142853": ["CWE-209"],     # Error details exposed
    "DS115253": ["CWE-79"],      # HTML injection (XSS)
    "DS183166": ["CWE-79"],      # DOM-based XSS
    "DS126188": ["CWE-79"],      # JavaScript eval
    "DS161085": ["CWE-327"],     # Weak cryptographic algorithm
    "DS144436": ["CWE-327"],     # ECB mode usage
    "DS156603": ["CWE-326"],     # Insufficient key size
    "DS109501": ["CWE-329"],     # Hardcoded IV
    "DS173287": ["CWE-328"],     # Weak hash algorithm
    "DS176620": ["CWE-295"],     # Disabled certificate validation
    "DS195456": ["CWE-327"],     # Outdated TLS version
}

# NOTE: Severity normalization now uses shared.severity.normalize_severity()

# DevSkim severity mapping (for backward compatibility with tests)
SEVERITY_MAP: dict[str, str] = {
    "Critical": "CRITICAL",
    "Important": "HIGH",
    "Moderate": "MEDIUM",
    "BestPractice": "LOW",
    "ManualReview": "INFO",
}

# DD Security Categories
SECURITY_CATEGORIES = [
    "sql_injection",
    "hardcoded_secret",
    "insecure_crypto",
    "insecure_random",
    "path_traversal",
    "xss",
    "deserialization",
    "xxe",
    "command_injection",
    "ldap_injection",
    "open_redirect",
    "ssrf",
    "csrf",
    "information_disclosure",
    "broken_access_control",
    "security_misconfiguration",
]


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class SecurityFinding:
    """A single security finding."""
    rule_id: str
    dd_category: str
    cwe_ids: list[str]
    file_path: str
    line_start: int
    line_end: int
    column_start: int
    column_end: int
    severity: str
    message: str
    code_snippet: str = ""
    fix_suggestion: str = ""


@dataclass
class FileStats:
    """Statistics for a single file."""
    path: str
    language: str
    lines: int
    issue_count: int
    issue_density: float
    by_category: dict[str, int] = field(default_factory=dict)
    by_severity: dict[str, int] = field(default_factory=dict)
    issues: list[SecurityFinding] = field(default_factory=list)


# =============================================================================
# Distribution Statistics Helper Functions
# =============================================================================

def compute_skewness(values: list[float], mean: float) -> float:
    """Compute sample skewness (Fisher's definition)."""
    n = len(values)
    if n < 3:
        return 0
    std = statistics.stdev(values)
    if std == 0:
        return 0
    return sum((x - mean) ** 3 for x in values) / (n * std ** 3)


def compute_kurtosis(values: list[float], mean: float) -> float:
    """Compute excess kurtosis (Fisher's definition)."""
    n = len(values)
    if n < 4:
        return 0
    std = statistics.stdev(values)
    if std == 0:
        return 0
    return sum((x - mean) ** 4 for x in values) / (n * std ** 4) - 3


def compute_gini(values: list[float]) -> float:
    """Compute Gini coefficient (0=perfect equality, 1=perfect inequality)."""
    if not values or len(values) < 2:
        return 0.0

    sorted_vals = sorted(values)
    n = len(sorted_vals)
    total = sum(sorted_vals)

    if total == 0:
        return 0.0

    weighted_sum = sum((i + 1) * v for i, v in enumerate(sorted_vals))
    return (2 * weighted_sum) / (n * total) - (n + 1) / n


def compute_theil(values: list[float]) -> float:
    """Compute Theil entropy index (0=equality, higher=more inequality)."""
    if not values or len(values) < 2:
        return 0.0

    positive_vals = [v for v in values if v > 0]
    if not positive_vals:
        return 0.0

    mean_val = statistics.mean(positive_vals)
    if mean_val == 0:
        return 0.0

    n = len(positive_vals)
    theil_sum = sum((v / mean_val) * math.log(v / mean_val) for v in positive_vals)
    return theil_sum / n


def compute_hoover(values: list[float]) -> float:
    """Compute Hoover/Robin Hood index (0=equality, 1=all in one)."""
    if not values or len(values) < 2:
        return 0.0

    total = sum(values)
    if total == 0:
        return 0.0

    mean_val = total / len(values)
    deviation_sum = sum(abs(v - mean_val) for v in values)
    return 0.5 * deviation_sum / total


def compute_palma(values: list[float]) -> float:
    """Compute Palma ratio (top 10% share / bottom 40% share)."""
    if not values or len(values) < 10:
        return 0.0

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    bottom_40_idx = int(n * 0.4)
    bottom_40_sum = sum(sorted_vals[:bottom_40_idx])

    top_10_idx = int(n * 0.9)
    top_10_sum = sum(sorted_vals[top_10_idx:])

    if bottom_40_sum == 0:
        return float('inf') if top_10_sum > 0 else 0.0

    return top_10_sum / bottom_40_sum


def compute_top_share(values: list[float], top_pct: float) -> float:
    """Compute share of total held by top X%."""
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


def compute_bottom_share(values: list[float], bottom_pct: float) -> float:
    """Compute share of total held by bottom X%."""
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


# =============================================================================
# Distribution Dataclass (22 metrics)
# =============================================================================

@dataclass
class Distribution:
    """Statistical distribution with 22 metrics."""
    count: int = 0
    min: float = 0.0
    max: float = 0.0
    mean: float = 0.0
    median: float = 0.0
    stddev: float = 0.0
    p25: float = 0.0
    p50: float = 0.0
    p75: float = 0.0
    p90: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    skewness: float = 0.0
    kurtosis: float = 0.0
    cv: float = 0.0
    iqr: float = 0.0
    gini: float = 0.0
    theil: float = 0.0
    hoover: float = 0.0
    palma: float = 0.0
    top_10_pct_share: float = 0.0
    top_20_pct_share: float = 0.0
    bottom_50_pct_share: float = 0.0

    @classmethod
    def from_values(cls, values: list[float]) -> "Distribution":
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
            count=n,
            min=min(values),
            max=max(values),
            mean=round(mean_val, 4),
            median=round(statistics.median(values), 4),
            stddev=round(stddev_val, 4),
            p25=p25_val,
            p50=round(statistics.median(values), 4),
            p75=p75_val,
            p90=sorted_vals[int(n * 0.90)] if n >= 10 else sorted_vals[-1],
            p95=sorted_vals[int(n * 0.95)] if n >= 20 else sorted_vals[-1],
            p99=sorted_vals[int(n * 0.99)] if n >= 100 else sorted_vals[-1],
            skewness=round(compute_skewness(values, mean_val), 4) if n > 2 else 0,
            kurtosis=round(compute_kurtosis(values, mean_val), 4) if n > 3 else 0,
            cv=round(stddev_val / mean_val, 4) if mean_val > 0 else 0,
            iqr=round(p75_val - p25_val, 4),
            gini=round(compute_gini(values), 4),
            theil=round(compute_theil(values), 4),
            hoover=round(compute_hoover(values), 4),
            palma=round(compute_palma(values), 4) if n >= 10 else 0,
            top_10_pct_share=round(compute_top_share(values, 0.10), 4),
            top_20_pct_share=round(compute_top_share(values, 0.20), 4),
            bottom_50_pct_share=round(compute_bottom_share(values, 0.50), 4),
        )


@dataclass
class LanguageStats:
    """Statistics for a language."""
    files: int = 0
    lines: int = 0
    issue_count: int = 0
    categories_covered: set = field(default_factory=set)


@dataclass
class DirectoryStats:
    """Aggregated statistics for a directory."""
    file_count: int = 0
    lines_code: int = 0
    issue_count: int = 0
    by_category: dict[str, int] = field(default_factory=dict)
    by_severity: dict[str, int] = field(default_factory=dict)
    issue_density: float = 0.0
    issue_distribution: Distribution | None = None


@dataclass
class DirectoryEntry:
    """Complete directory entry with direct vs recursive rollups."""
    path: str = ""
    name: str = ""
    depth: int = 0
    is_leaf: bool = False
    child_count: int = 0
    subdirectories: list[str] = field(default_factory=list)
    direct: DirectoryStats = field(default_factory=DirectoryStats)
    recursive: DirectoryStats = field(default_factory=DirectoryStats)


@dataclass
class AnalysisResult:
    """Full analysis result with directory rollups (v2.0 schema)."""
    schema_version: str = "2.0.0"
    generated_at: str = ""
    repo_name: str = ""
    repo_path: str = ""
    run_id: str = ""
    timestamp: str = ""
    root_path: str = ""
    devskim_version: str = ""
    rules_used: list[str] = field(default_factory=list)
    analysis_duration_ms: int = 0
    directories: list[DirectoryEntry] = field(default_factory=list)
    files: list[FileStats] = field(default_factory=list)
    findings: list[SecurityFinding] = field(default_factory=list)
    by_language: dict[str, LanguageStats] = field(default_factory=dict)
    by_category: dict[str, int] = field(default_factory=dict)
    by_severity: dict[str, int] = field(default_factory=dict)
    issue_distribution: Distribution | None = None


# =============================================================================
# DevSkim Runner
# =============================================================================

def get_devskim_cmd() -> str:
    """Get the devskim command."""
    return "devskim"


def get_devskim_env() -> dict:
    """Get environment variables for running DevSkim."""
    env = os.environ.copy()
    # Enable roll-forward to support running on newer .NET versions
    env["DOTNET_ROLL_FORWARD"] = "LatestMajor"
    return env


def get_devskim_version() -> str:
    """Get DevSkim version string."""
    try:
        result = subprocess.run(
            [get_devskim_cmd(), "--version"],
            capture_output=True,
            text=True,
            check=True,
            env=get_devskim_env(),
        )
        # DevSkim outputs version to stderr, not stdout
        version = result.stdout.strip() or result.stderr.strip()
        return version if version else "unknown"
    except Exception:
        return "unknown"


def run_devskim(
    target_path: str,
    include_files: list[str] | None = None,
    custom_rules_path: str | None = None,
) -> dict:
    """Run DevSkim analysis on target path.

    Args:
        target_path: Path to analyze
        include_files: Optional list of specific files to analyze (for incremental analysis)
        custom_rules_path: Optional path to directory containing custom rule JSON files

    Returns:
        Parsed SARIF results
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sarif', delete=False) as f:
        sarif_path = f.name

    try:
        cmd = [
            get_devskim_cmd(), "analyze",
            "-I", target_path,
            "-f", "sarif",
            "-O", sarif_path,
            "--severity", "Critical,Important,Moderate,BestPractice,ManualReview",
            "--confidence", "High,Medium,Low",
        ]

        # Add custom rules path if provided
        if custom_rules_path and os.path.isdir(custom_rules_path):
            cmd.extend(["-r", custom_rules_path])

        # Run DevSkim
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=get_devskim_env(),
        )

        # DevSkim returns 0 for clean, non-zero for findings or errors
        # Check if SARIF file was created
        if os.path.exists(sarif_path):
            with open(sarif_path, 'r') as f:
                sarif_content = f.read()
                if sarif_content:
                    return json.loads(sarif_content)

        # If no SARIF output, return empty results
        return {"runs": [{"results": []}]}

    except Exception as e:
        print(f"DevSkim error: {e}", file=sys.stderr)
        return {"runs": [{"results": []}]}
    finally:
        # Clean up temp file
        if os.path.exists(sarif_path):
            os.unlink(sarif_path)


def parse_sarif_results(sarif: dict, target_path: str) -> list[SecurityFinding]:
    """Parse SARIF output into SecurityFinding objects.

    Args:
        sarif: SARIF JSON output from DevSkim
        target_path: Base path for relative path calculation

    Returns:
        List of SecurityFinding objects
    """
    findings = []
    abs_target = os.path.abspath(target_path)

    for run in sarif.get("runs", []):
        for result in run.get("results", []):
            rule_id = result.get("ruleId", "unknown")
            message = result.get("message", {}).get("text", "")

            # Get severity from result level using shared severity normalization
            level = result.get("level", "warning")
            # SARIF levels: error->HIGH, warning->MEDIUM, note->LOW in shared.severity
            # DevSkim treats error as CRITICAL and warning as HIGH for security issues
            if level == "error":
                severity = "CRITICAL"
            else:
                severity = normalize_severity(level, default="MEDIUM")

            # Map rule to DD category (use message for disambiguation)
            dd_category = map_rule_to_category(rule_id, message)

            # Look up CWE IDs for traceability
            cwe_ids = RULE_TO_CWE_MAP.get(rule_id, [])

            # Process locations
            for location in result.get("locations", []):
                physical = location.get("physicalLocation", {})
                artifact = physical.get("artifactLocation", {})
                region = physical.get("region", {})

                raw_path = artifact.get("uri", "")
                # Strip file:// prefix if present
                if raw_path.startswith("file://"):
                    raw_path = raw_path[7:]
                # Normalize to repo-relative path using Caldera path normalization
                file_path = normalize_file_path(raw_path, Path(abs_target))

                # Get code snippet if available
                snippet = physical.get("contextRegion", {}).get("snippet", {}).get("text", "")
                if not snippet:
                    snippet = region.get("snippet", {}).get("text", "")

                finding = SecurityFinding(
                    rule_id=rule_id,
                    dd_category=dd_category,
                    cwe_ids=cwe_ids,
                    file_path=file_path,
                    line_start=region.get("startLine", 0),
                    line_end=region.get("endLine", region.get("startLine", 0)),
                    column_start=region.get("startColumn", 0),
                    column_end=region.get("endColumn", 0),
                    severity=severity,
                    message=message,
                    code_snippet=snippet.strip() if snippet else "",
                )
                findings.append(finding)

    return findings


def map_rule_to_category(rule_id: str, message: str = "") -> str:
    """Map a DevSkim rule ID to DD security category.

    Uses both rule ID and message content for accurate mapping.

    Args:
        rule_id: The DevSkim rule ID (e.g., "DS126858")
        message: The message text from the finding (for disambiguation)

    Returns:
        DD security category string
    """
    # Message-based mapping (most accurate when available)
    if message:
        message_lower = message.lower()

        # Insecure crypto patterns in messages
        if any(kw in message_lower for kw in ["hash", "md5", "sha1", "des ", "cipher", "ecb", "weak crypto", "weak algorithm"]):
            return "insecure_crypto"

        # SQL injection patterns
        if any(kw in message_lower for kw in ["sql", "query"]):
            return "sql_injection"

        # Hardcoded secrets patterns
        if any(kw in message_lower for kw in ["password", "secret", "credential", "api key", "hardcoded"]):
            return "hardcoded_secret"

        # Path traversal patterns
        if any(kw in message_lower for kw in ["path", "traversal", "directory"]):
            return "path_traversal"

        # XSS patterns
        if any(kw in message_lower for kw in ["xss", "cross-site", "script injection", "html injection"]):
            return "xss"

        # Deserialization patterns
        if any(kw in message_lower for kw in ["deserial", "binaryformatter", "typename"]):
            return "deserialization"

    # Direct rule ID mapping
    if rule_id in RULE_TO_CATEGORY_MAP:
        return RULE_TO_CATEGORY_MAP[rule_id]

    # Pattern-based mapping on rule_id (fallback)
    rule_lower = rule_id.lower()

    if "sql" in rule_lower or "injection" in rule_lower:
        return "sql_injection"
    if "password" in rule_lower or "secret" in rule_lower or "credential" in rule_lower:
        return "hardcoded_secret"
    if "crypto" in rule_lower or "md5" in rule_lower or "sha1" in rule_lower or "des" in rule_lower:
        return "insecure_crypto"
    if "path" in rule_lower or "traversal" in rule_lower:
        return "path_traversal"
    if "xss" in rule_lower or "script" in rule_lower:
        return "xss"
    if "deserial" in rule_lower or "binaryformatter" in rule_lower:
        return "deserialization"
    if "xml" in rule_lower or "xxe" in rule_lower:
        return "xxe"
    if "command" in rule_lower or "exec" in rule_lower or "shell" in rule_lower:
        return "command_injection"

    return "unknown"


def detect_language(file_path: str) -> str:
    """Detect language from file extension."""
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".cs": "csharp",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".cob": "cobol",
        ".cbl": "cobol",
    }
    ext = Path(file_path).suffix.lower()
    return ext_map.get(ext, "unknown")


def count_lines(file_path: str) -> int:
    """Count lines in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def compute_distribution(values: list[float]) -> Distribution:
    """Compute distribution statistics (22 metrics)."""
    return Distribution.from_values(values)


# =============================================================================
# Directory Rollup System
# =============================================================================

def compute_directory_issue_stats(files: list[FileStats]) -> DirectoryStats:
    """Compute aggregated issue statistics for a set of files."""
    if not files:
        return DirectoryStats()

    file_count = len(files)
    lines_code = sum(f.lines for f in files)
    issue_count = sum(f.issue_count for f in files)

    by_category: dict[str, int] = defaultdict(int)
    by_severity: dict[str, int] = defaultdict(int)

    for f in files:
        for cat, count in f.by_category.items():
            by_category[cat] += count
        for sev, count in f.by_severity.items():
            by_severity[sev] += count

    issue_density = (issue_count / lines_code * 100) if lines_code > 0 else 0.0
    issue_counts = [float(f.issue_count) for f in files]
    issue_distribution = compute_distribution(issue_counts) if len(files) >= 3 else None

    return DirectoryStats(
        file_count=file_count,
        lines_code=lines_code,
        issue_count=issue_count,
        by_category=dict(by_category),
        by_severity=dict(by_severity),
        issue_density=round(issue_density, 4),
        issue_distribution=issue_distribution,
    )


def build_directory_entries(files: list[FileStats], root_path: str) -> list[DirectoryEntry]:
    """Build directory tree with direct vs recursive rollups."""
    if not files:
        return []

    dir_files: dict[str, list[FileStats]] = defaultdict(list)
    all_dirs: set[str] = set()

    for f in files:
        path = Path(f.path)
        parent = str(path.parent)
        if parent == ".":
            parent = "."
        dir_files[parent].append(f)
        all_dirs.add(parent)

        for i in range(1, len(path.parts)):
            ancestor = "/".join(path.parts[:i])
            if ancestor:
                all_dirs.add(ancestor)

    all_dirs_sorted = sorted(all_dirs)
    non_root_dirs = [d for d in all_dirs_sorted if d != "."]
    root_depth = min(d.count("/") for d in non_root_dirs) if non_root_dirs else 0

    directories = []

    for dir_path in all_dirs_sorted:
        direct_files = dir_files.get(dir_path, [])

        recursive_files = []
        for other_path, other_files in dir_files.items():
            if dir_path == ".":
                recursive_files.extend(other_files)
            elif other_path == dir_path or other_path.startswith(dir_path + "/"):
                recursive_files.extend(other_files)

        direct_stats = compute_directory_issue_stats(direct_files)
        recursive_stats = compute_directory_issue_stats(recursive_files)

        if dir_path == ".":
            subdirs = [d for d in all_dirs_sorted if d != "." and "/" not in d]
        else:
            subdirs = [
                d for d in all_dirs_sorted
                if d.startswith(dir_path + "/") and d.count("/") == dir_path.count("/") + 1
            ]

        is_leaf = len(subdirs) == 0 and len(direct_files) > 0
        child_count = len(subdirs)
        depth = 0 if dir_path == "." else dir_path.count("/") - root_depth + 1
        name = "(root)" if dir_path == "." else Path(dir_path).name

        directories.append(DirectoryEntry(
            path=dir_path,
            name=name,
            depth=depth,
            is_leaf=is_leaf,
            child_count=child_count,
            subdirectories=sorted(subdirs),
            direct=direct_stats,
            recursive=recursive_stats,
        ))

    directories.sort(key=lambda d: ("" if d.path == "." else d.path))
    return directories


# =============================================================================
# Analysis
# =============================================================================

def analyze_with_devskim(
    target_path: str,
    repo_name: str = "",
    repo_path: str = "",
    custom_rules_path: str | None = None,
) -> AnalysisResult:
    """Run full DevSkim analysis and return structured results."""
    start_time = datetime.now(timezone.utc)
    abs_target = os.path.abspath(target_path)

    # Check for incremental analysis (CHANGED_FILES env var)
    changed_files_env = os.environ.get("CHANGED_FILES", "").strip()
    incremental_mode = bool(changed_files_env)
    include_files: list[str] | None = None
    changed_files_set: set[str] | None = None

    if incremental_mode:
        include_files = [f.strip() for f in changed_files_env.split('\n') if f.strip()]
        changed_files_set = set(include_files) if include_files else None
        if include_files:
            print(f"  Incremental mode: {len(include_files)} changed files to analyze")
        else:
            print("  Incremental mode: no changed files to analyze")
            return AnalysisResult(
                generated_at=start_time.isoformat(),
                repo_name=repo_name or os.path.basename(abs_target),
                repo_path=repo_path or abs_target,
                run_id=f"devskim-{start_time.strftime('%Y%m%d-%H%M%S')}",
                timestamp=start_time.isoformat(),
                root_path=abs_target,
                devskim_version=get_devskim_version(),
            )

    # Run DevSkim
    sarif_output = run_devskim(target_path, include_files, custom_rules_path)

    # Initialize result
    result = AnalysisResult(
        generated_at=start_time.isoformat(),
        repo_name=repo_name or os.path.basename(abs_target),
        repo_path=repo_path or abs_target,
        run_id=f"devskim-{start_time.strftime('%Y%m%d-%H%M%S')}",
        timestamp=start_time.isoformat(),
        root_path=abs_target,
        devskim_version=get_devskim_version(),
    )

    # Parse SARIF and create findings
    findings = parse_sarif_results(sarif_output, target_path)
    result.findings = findings

    # Group findings by file
    file_findings: dict[str, list[SecurityFinding]] = defaultdict(list)
    for finding in findings:
        file_findings[finding.file_path].append(finding)
        result.by_category[finding.dd_category] = result.by_category.get(finding.dd_category, 0) + 1
        result.by_severity[finding.severity] = result.by_severity.get(finding.severity, 0) + 1

    # Collect rules used
    result.rules_used = list(set(f.rule_id for f in findings))

    # Build file stats - scan all source files
    all_files = set()
    source_extensions = ('.py', '.js', '.ts', '.tsx', '.cs', '.java', '.go', '.rs', '.c', '.cpp', '.h', '.hpp', '.cob', '.cbl', '.php', '.rb')

    abs_target = Path(target_path).resolve()
    for root, _, files in os.walk(target_path):
        for f in files:
            if f.endswith(source_extensions):
                full_path = os.path.join(root, f)
                rel_path = normalize_file_path(full_path, abs_target)
                if incremental_mode and changed_files_set:
                    if rel_path not in changed_files_set:
                        continue
                all_files.add(rel_path)

    # Also include files with findings that might not have been walked
    for file_path in file_findings.keys():
        all_files.add(file_path)

    issue_counts = []
    for file_path in all_files:
        full_path = os.path.join(target_path, file_path)
        loc = count_lines(full_path)
        lang = detect_language(file_path)
        issues = file_findings.get(file_path, [])
        issue_count = len(issues)
        issue_density = issue_count / loc * 100 if loc > 0 else 0

        file_by_category: dict[str, int] = defaultdict(int)
        file_by_severity: dict[str, int] = defaultdict(int)
        for issue in issues:
            file_by_category[issue.dd_category] += 1
            file_by_severity[issue.severity] += 1

        file_stat = FileStats(
            path=file_path,
            language=lang,
            lines=loc,
            issue_count=issue_count,
            issue_density=issue_density,
            by_category=dict(file_by_category),
            by_severity=dict(file_by_severity),
            issues=issues,
        )
        result.files.append(file_stat)
        issue_counts.append(issue_count)

        # Update language stats
        if lang not in result.by_language:
            result.by_language[lang] = LanguageStats()
        result.by_language[lang].files += 1
        result.by_language[lang].lines += loc
        result.by_language[lang].issue_count += issue_count
        for issue in issues:
            result.by_language[lang].categories_covered.add(issue.dd_category)

    # Compute distribution
    if issue_counts:
        result.issue_distribution = compute_distribution([float(x) for x in issue_counts])

    # Build directory tree
    result.directories = build_directory_entries(result.files, target_path)

    # Calculate duration
    end_time = datetime.now(timezone.utc)
    result.analysis_duration_ms = int((end_time - start_time).total_seconds() * 1000)

    return result


# =============================================================================
# Dashboard Display
# =============================================================================

def display_dashboard(result: AnalysisResult, width: int = 100):
    """Display the 16-section analysis dashboard."""

    # Section 1: Header
    print()
    print_header("DEVSKIM SECURITY ANALYSIS", width)

    # Section 2: Run Metadata
    print_section("1. Run Metadata", width)
    print_row("Run ID:", result.run_id, "Timestamp:", result.timestamp[:19], width)
    print_row("Target:", truncate_path_middle(result.root_path, 40),
              "DevSkim:", result.devskim_version, width)
    print_row("Duration:", f"{result.analysis_duration_ms}ms",
              "Rules Triggered:", str(len(result.rules_used)), width)
    print_section_end(width)

    # Section 3: Overall Summary
    print_section("2. Overall Summary", width)
    total_files = len(result.files)
    files_with_issues = sum(1 for f in result.files if f.issue_count > 0)
    total_issues = len(result.findings)
    total_lines = sum(f.lines for f in result.files)

    print_row("Total Files:", format_number(total_files),
              "Files with Issues:", format_number(files_with_issues), width)
    issue_color = Colors.RED if total_issues > 10 else (Colors.YELLOW if total_issues > 0 else Colors.GREEN)
    print_row("Total Issues:", c(format_number(total_issues), issue_color),
              "Total Lines:", format_number(total_lines), width)
    issue_rate = files_with_issues / total_files * 100 if total_files > 0 else 0
    density = total_issues / total_lines * 1000 if total_lines > 0 else 0
    print_row("Issue Rate:", format_percent(issue_rate),
              "Issues/KLOC:", f"{density:.2f}", width)
    print_section_end(width)

    # Section 4: Issues by Security Category
    print_section("3. Issues by Security Category", width)
    for cat in SECURITY_CATEGORIES:
        count = result.by_category.get(cat, 0)
        if count > 0:
            color = Colors.RED if count > 5 else (Colors.YELLOW if count > 0 else Colors.GREEN)
            print_row(f"  {cat}:", c(str(count), color), "", "", width)
    unknown = result.by_category.get("unknown", 0)
    if unknown > 0:
        print_row(f"  unknown:", c(str(unknown), Colors.DIM), "", "", width)
    if not any(result.by_category.get(cat, 0) > 0 for cat in SECURITY_CATEGORIES + ["unknown"]):
        print_row("  No issues detected", c("CLEAN", Colors.GREEN), "", "", width)
    print_section_end(width)

    # Section 5: Issues by Severity
    print_section("4. Issues by Severity", width)
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
        count = result.by_severity.get(sev, 0)
        if count > 0:
            color = Colors.BRIGHT_RED if sev == "CRITICAL" else (
                Colors.RED if sev == "HIGH" else (
                    Colors.YELLOW if sev == "MEDIUM" else Colors.CYAN
                )
            )
            print_row(f"  {sev}:", c(str(count), color), "", "", width)
    print_section_end(width)

    # Section 6: Top Rule IDs
    print_section("5. Top DevSkim Rules Triggered", width)
    rule_counts: dict[str, int] = defaultdict(int)
    for finding in result.findings:
        rule_counts[finding.rule_id] += 1
    sorted_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    for rule_id, count in sorted_rules:
        category = map_rule_to_category(rule_id)
        print_row(f"  {rule_id}:", f"{count} ({category})", "", "", width)
    if not sorted_rules:
        print_row("  No rules triggered", "", "", "", width)
    print_section_end(width)

    # Section 7: Language Coverage
    print_section("6. Language Coverage", width)
    for lang, stats in sorted(result.by_language.items(), key=lambda x: x[1].files, reverse=True):
        cats_str = ", ".join(sorted(stats.categories_covered)[:3]) if stats.categories_covered else "none"
        print_row(f"  {lang}:",
                  f"{stats.files} files, {stats.issue_count} issues",
                  "Categories:", cats_str, width)
    print_section_end(width)

    # Section 8: Files with Most Issues
    print_section("7. Files with Most Issues (Top 10)", width)
    sorted_files = sorted(result.files, key=lambda x: x.issue_count, reverse=True)[:10]
    for f in sorted_files:
        if f.issue_count > 0:
            color = Colors.RED if f.issue_count > 5 else (Colors.YELLOW if f.issue_count > 2 else Colors.WHITE)
            print_row(f"  {truncate_path_middle(f.path, 50)}:",
                      c(f"{f.issue_count} issues", color),
                      "Density:", f"{f.issue_density:.1f}/100 LOC", width)
    if not any(f.issue_count > 0 for f in sorted_files):
        print_row("  All files are clean!", "", "", "", width)
    print_section_end(width)

    # Section 9: Clean Files
    print_section("8. Clean Files Summary", width)
    clean_files = [f for f in result.files if f.issue_count == 0]
    print_row("Clean Files:", c(format_number(len(clean_files)), Colors.GREEN),
              "Percentage:", c(format_percent(len(clean_files) / total_files * 100 if total_files > 0 else 0), Colors.GREEN), width)
    print_section_end(width)

    # Section 10: Distribution Statistics
    if result.issue_distribution and result.issue_distribution.count > 0:
        print_section("9. Issue Distribution Statistics", width)
        dist = result.issue_distribution
        print_row("Min:", str(int(dist.min)), "Max:", str(int(dist.max)), width)
        print_row("Mean:", f"{dist.mean:.2f}", "Median:", f"{dist.median:.2f}", width)
        print_row("Std Dev:", f"{dist.stddev:.2f}", "P90:", f"{dist.p90:.1f}", width)
        print_section_end(width)

    # Section 11: Sample Findings
    print_section("10. Sample Findings (First 5)", width)
    for finding in result.findings[:5]:
        location = f"{truncate_path_middle(finding.file_path, 30)}:{finding.line_start}"
        print_row(f"  {finding.dd_category}:", location, "Severity:", finding.severity, width)
    if not result.findings:
        print_row("  No findings to display", "", "", "", width)
    print_section_end(width)

    # Section 12: Directory Tree View
    if result.directories:
        print_section("11. Directory Tree", width)
        for d in result.directories[:10]:
            indent = "  " * d.depth
            name = d.name if d.name != "(root)" else "(root)"
            issues_str = f"{d.recursive.issue_count} issues" if d.recursive.issue_count > 0 else "clean"
            color = Colors.RED if d.recursive.issue_count > 10 else (
                Colors.YELLOW if d.recursive.issue_count > 0 else Colors.GREEN
            )
            print_row(f"  {indent}{name}/:", c(issues_str, color),
                      "Files:", str(d.recursive.file_count), width)
        print_section_end(width)

    # Section 13: Issue Concentration Analysis
    if result.issue_distribution and result.issue_distribution.count > 0:
        print_section("12. Issue Concentration (Inequality)", width)
        dist = result.issue_distribution
        gini_color = Colors.RED if dist.gini > 0.7 else (Colors.YELLOW if dist.gini > 0.5 else Colors.GREEN)
        print_row("Gini:", c(f"{dist.gini:.3f}", gini_color),
                  "Theil:", f"{dist.theil:.3f}", width)
        print_row("Hoover:", f"{dist.hoover:.3f}",
                  "Palma:", f"{dist.palma:.2f}x", width)
        print_row("Top 10% Share:", f"{dist.top_10_pct_share:.1%}",
                  "Bottom 50% Share:", f"{dist.bottom_50_pct_share:.1%}", width)
        print_section_end(width)

    # Section 14: Key Findings Summary
    print_section("13. Key Findings", width)
    findings_list = []
    if total_issues == 0:
        findings_list.append(("No security issues detected", Colors.GREEN))
    else:
        if result.by_severity.get("CRITICAL", 0) > 0:
            findings_list.append((f"{result.by_severity['CRITICAL']} CRITICAL severity issues", Colors.BRIGHT_RED))
        if result.by_severity.get("HIGH", 0) > 0:
            findings_list.append((f"{result.by_severity['HIGH']} HIGH severity issues", Colors.RED))
        if result.by_category.get("sql_injection", 0) > 0:
            findings_list.append((f"{result.by_category['sql_injection']} SQL injection vulnerabilities", Colors.RED))
        if result.by_category.get("hardcoded_secret", 0) > 0:
            findings_list.append((f"{result.by_category['hardcoded_secret']} hardcoded secrets", Colors.RED))
        if result.by_category.get("insecure_crypto", 0) > 0:
            findings_list.append((f"{result.by_category['insecure_crypto']} insecure crypto issues", Colors.YELLOW))
        if result.issue_distribution and result.issue_distribution.gini > 0.6:
            findings_list.append(("Issues concentrated in few files (Gini > 0.6)", Colors.YELLOW))

    for finding_text, color in findings_list[:5]:
        print_row("  •", c(finding_text, color), "", "", width)
    if not findings_list:
        print_row("  •", "Analysis complete, no significant findings", "", "", width)
    print_section_end(width)

    # Section 15: Recommendations
    print_section("14. Recommendations", width)
    recommendations = []
    if result.by_severity.get("CRITICAL", 0) > 0:
        recommendations.append("URGENT: Address CRITICAL severity issues immediately")
    if result.by_category.get("sql_injection", 0) > 0:
        recommendations.append("Use parameterized queries to prevent SQL injection")
    if result.by_category.get("hardcoded_secret", 0) > 0:
        recommendations.append("Move secrets to environment variables or secure vault")
    if result.by_category.get("insecure_crypto", 0) > 0:
        recommendations.append("Replace weak crypto (MD5/SHA1/DES) with modern algorithms")
    if result.by_category.get("path_traversal", 0) > 0:
        recommendations.append("Validate and sanitize file paths from user input")
    if result.by_category.get("xss", 0) > 0:
        recommendations.append("Encode output and validate user input for XSS prevention")
    if result.by_category.get("deserialization", 0) > 0:
        recommendations.append("Use type-safe serialization instead of BinaryFormatter")

    for rec in recommendations[:4]:
        print_row("  →", rec, "", "", width)
    if not recommendations:
        print_row("  →", "Keep up the good security practices!", "", "", width)
    print_section_end(width)

    # Final summary
    print()
    if total_issues == 0:
        print(c("  ANALYSIS COMPLETE: No security issues detected!", Colors.GREEN, Colors.BOLD))
    else:
        critical = result.by_severity.get("CRITICAL", 0)
        high = result.by_severity.get("HIGH", 0)
        if critical > 0:
            print(c(f"  ANALYSIS COMPLETE: {total_issues} security issues found ({critical} CRITICAL, {high} HIGH)",
                    Colors.BRIGHT_RED, Colors.BOLD))
        elif high > 0:
            print(c(f"  ANALYSIS COMPLETE: {total_issues} security issues found ({high} HIGH severity)",
                    Colors.RED, Colors.BOLD))
        else:
            print(c(f"  ANALYSIS COMPLETE: {total_issues} security issues found across {files_with_issues} files",
                    Colors.YELLOW, Colors.BOLD))
    print()


# =============================================================================
# Output Generation
# =============================================================================

def distribution_to_dict(d: Distribution | None) -> dict | None:
    """Convert Distribution to JSON-serializable dict with all 22 metrics."""
    if not d:
        return None
    return {
        "count": d.count,
        "min": d.min,
        "max": d.max,
        "mean": round(d.mean, 4),
        "median": round(d.median, 4),
        "stddev": round(d.stddev, 4),
        "p25": d.p25,
        "p50": round(d.p50, 4),
        "p75": d.p75,
        "p90": round(d.p90, 4),
        "p95": round(d.p95, 4),
        "p99": round(d.p99, 4),
        "skewness": round(d.skewness, 4),
        "kurtosis": round(d.kurtosis, 4),
        "cv": round(d.cv, 4),
        "iqr": round(d.iqr, 4),
        "gini": round(d.gini, 4),
        "theil": round(d.theil, 4),
        "hoover": round(d.hoover, 4),
        "palma": round(d.palma, 4) if d.palma != float('inf') else None,
        "top_10_pct_share": round(d.top_10_pct_share, 4),
        "top_20_pct_share": round(d.top_20_pct_share, 4),
        "bottom_50_pct_share": round(d.bottom_50_pct_share, 4),
    }


def directory_stats_to_dict(stats: DirectoryStats) -> dict:
    """Convert DirectoryStats to JSON-serializable dict."""
    return {
        "file_count": stats.file_count,
        "lines_code": stats.lines_code,
        "issue_count": stats.issue_count,
        "by_category": stats.by_category,
        "by_severity": stats.by_severity,
        "issue_density": round(stats.issue_density, 4),
        "issue_distribution": distribution_to_dict(stats.issue_distribution),
    }


def result_to_dict(result: AnalysisResult) -> dict:
    """Convert AnalysisResult to JSON-serializable dict (v2.0 schema)."""
    # Serialize files
    files = []
    for f in result.files:
        issues = []
        for issue in f.issues:
            issues.append({
                "rule_id": issue.rule_id,
                "cwe_ids": issue.cwe_ids,
                "dd_category": issue.dd_category,
                "line_start": issue.line_start,
                "line_end": issue.line_end,
                "column_start": issue.column_start,
                "column_end": issue.column_end,
                "severity": issue.severity,
                "message": issue.message,
                "code_snippet": issue.code_snippet,
            })
        files.append({
            "path": f.path,
            "language": f.language,
            "lines": f.lines,
            "issue_count": f.issue_count,
            "issue_density": round(f.issue_density, 4),
            "by_category": f.by_category,
            "by_severity": f.by_severity,
            "issues": issues,
        })

    # Serialize directories
    directories = []
    for d in result.directories:
        directories.append({
            "path": d.path,
            "name": d.name,
            "depth": d.depth,
            "is_leaf": d.is_leaf,
            "child_count": d.child_count,
            "subdirectories": d.subdirectories,
            "direct": directory_stats_to_dict(d.direct),
            "recursive": directory_stats_to_dict(d.recursive),
        })

    # Serialize language stats
    by_language = {}
    for lang, stats in result.by_language.items():
        by_language[lang] = {
            "files": stats.files,
            "lines": stats.lines,
            "issue_count": stats.issue_count,
            "categories_covered": list(stats.categories_covered),
        }

    return {
        "schema_version": result.schema_version,
        "generated_at": result.generated_at,
        "repo_name": result.repo_name,
        "repo_path": result.repo_path,
        "results": {
            "tool": "devskim",
            "tool_version": result.devskim_version,
            "metadata": {
                "tool": "devskim",
                "run_id": result.run_id,
                "analysis_duration_ms": result.analysis_duration_ms,
                "devskim_version": result.devskim_version,
                "rules_used": result.rules_used,
            },
            "summary": {
                "total_files": len(result.files),
                "total_directories": len(result.directories),
                "files_with_issues": sum(1 for f in result.files if f.issue_count > 0),
                "total_issues": len(result.findings),
                "total_lines": sum(f.lines for f in result.files),
                "issues_by_category": result.by_category,
                "issues_by_severity": result.by_severity,
            },
            "directories": directories,
            "files": files,
            "by_language": by_language,
            "statistics": {
                "issue_distribution": distribution_to_dict(result.issue_distribution),
            },
        },
    }


def save_output(result: AnalysisResult, output_path: str):
    """Save analysis result to JSON file."""
    output = result_to_dict(result)
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Analyze security vulnerabilities using DevSkim"
    )
    parser.add_argument(
        "target",
        help="Target directory to analyze",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file path",
        default="output/runs/security_analysis.json",
    )
    parser.add_argument(
        "--repo-name",
        help="Repository name for output",
        default="",
    )
    parser.add_argument(
        "--repo-path",
        help="Repository path for output",
        default="",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Only output JSON, no dashboard",
    )
    parser.add_argument(
        "--custom-rules",
        help="Path to directory containing custom DevSkim rule JSON files",
        default=None,
    )

    args = parser.parse_args()

    if args.no_color:
        set_color_enabled(False)

    # Validate target
    if not os.path.exists(args.target):
        print(f"Error: Target path does not exist: {args.target}", file=sys.stderr)
        sys.exit(1)

    # Run analysis
    result = analyze_with_devskim(args.target, args.repo_name, args.repo_path, args.custom_rules)

    # Create output directory
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Save output
    save_output(result, args.output)

    # Display dashboard
    if not args.json_only:
        width = get_terminal_width(100, 80)
        display_dashboard(result, width)
        print(f"  Results saved to: {args.output}")
        print()


if __name__ == "__main__":
    main()
