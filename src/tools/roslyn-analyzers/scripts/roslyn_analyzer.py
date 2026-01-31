#!/usr/bin/env python3
"""
Roslyn Analyzers - Main Analysis Script

Runs Roslyn code analysis on .NET projects and generates normalized output
compatible with DD Analyzer evaluation framework.

Usage:
    python scripts/roslyn_analyzer.py <target_path> [--output <output.json>]
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Rule to DD category mapping
DD_CATEGORY_MAP = {
    # ==========================================================================
    # Microsoft.CodeAnalysis.NetAnalyzers (Built-in)
    # ==========================================================================

    # Security rules (CA3xxx, CA5xxx, CA2xxx for serialization)
    "CA3001": "security",   # SQL Injection
    "CA3002": "security",   # XSS
    "CA2100": "security",   # SQL Review
    "CA5350": "security",   # Weak Crypto (DES)
    "CA5351": "security",   # Broken Crypto (MD5)
    "CA5385": "security",   # RSA Key Size
    "CA5390": "security",   # Hardcoded Keys
    "CA5364": "security",   # Deprecated TLS
    "CA5397": "security",   # Deprecated SSL
    "CA2300": "security",   # BinaryFormatter
    "CA2301": "security",   # BinaryFormatter without binder
    "CA2305": "security",   # LosFormatter
    "CA2311": "security",   # NetDataContractSerializer
    "CA2315": "security",   # ObjectStateFormatter
    "CA3147": "security",   # Missing CSRF
    "CA5391": "security",   # Missing Antiforgery
    "CA5396": "security",   # HttpOnly Cookie
    "CA5365": "security",   # HTTP Headers
    "CA5386": "security",   # Hardcoded Protocol
    "CA2326": "security",   # TypeNameHandling (JSON.NET)
    "CA2327": "security",   # TypeNameHandling with custom binder
    "CA1062": "security",   # Validate arguments of public methods
    "CS0618": "security",   # Obsolete member usage (often security-related)

    # Design rules
    "CA1051": "design",     # Visible Instance Fields
    "CA1040": "design",     # Empty Interfaces
    "CA1000": "design",     # Static on Generics
    "CA1061": "design",     # Hidden Base Methods
    "CA1502": "design",     # Excessive Complexity
    "CA1506": "design",     # Excessive Coupling
    "CA1012": "design",     # Abstract Public Ctor
    "CA1065": "design",     # Exceptions in Unexpected Locations
    "CA1050": "design",     # Types Not in Namespace
    "IDE0040": "design",    # Missing Accessibility
    "CA1002": "design",     # Do not expose generic lists
    "CA1024": "design",     # Use properties where appropriate
    "CA1054": "design",     # URI parameters should not be strings
    "CA2234": "design",     # Pass System.Uri objects instead of strings
    "CA1852": "design",     # Seal internal types
    "CS0628": "design",     # Protected member in sealed type

    # Resource management rules
    "CA1001": "resource",   # Missing IDisposable
    "CA1063": "resource",   # Improper IDisposable
    "CA2000": "resource",   # Objects Not Disposed
    "CA2016": "resource",   # Missing CancellationToken
    "CA2007": "resource",   # Task Await Issues
    "CA2008": "resource",   # TaskScheduler Issues
    "CA2012": "resource",   # ValueTask Issues
    "CA1821": "resource",   # Finalizer Issues

    # Dead code rules
    "IDE0005": "dead_code", # Unused Imports
    "IDE0060": "dead_code", # Unused Parameters
    "CA1801": "dead_code",  # Unused Parameters
    "IDE0052": "dead_code", # Unused Private Members
    "IDE0059": "dead_code", # Unused Locals
    "CA1812": "dead_code",  # Uninstantiated Classes
    "CA1823": "dead_code",  # Avoid unused private fields
    "CS0169": "dead_code",  # Field is never used

    # Performance rules
    "CA1826": "performance", # LINQ Alternatives
    "CA1829": "performance", # Length/Count Property
    "CA1825": "performance", # Empty Array Allocation
    "CA1805": "performance", # Unnecessary Initialization
    "CA1810": "performance", # Static Ctor Issues
    "CA1834": "performance", # StringBuilder.Append
    "CA1858": "performance", # StartsWith char
    "CA1822": "performance", # Mark members as static
    "CA1850": "performance", # Prefer static HashData
    "CA1859": "performance", # Use concrete type
    "CA1802": "performance", # Use literals where possible
    "CA1872": "performance", # Prefer Convert over BitArray
    "CA2022": "performance", # Avoid inexact read with Stream.Read
    "CA1513": "performance", # Use ObjectDisposedException.ThrowIf

    # Globalization rules
    "CA1303": "design",     # Do not pass literals as localized parameters
    "CA1304": "design",     # Specify CultureInfo
    "CA1305": "design",     # Specify IFormatProvider
    "CA1307": "design",     # Specify StringComparison
    "CA1311": "design",     # Specify culture or use ordinal

    # Design rules (additional)
    "CA1816": "resource",   # Call GC.SuppressFinalize correctly
    "CA1819": "design",     # Properties should not return arrays
    "CA1813": "design",     # Avoid unsealed attributes
    "CA1815": "design",     # Override equals and operator equals
    "CA1711": "design",     # Identifiers should not have incorrect suffix
    "CA1707": "design",     # Remove underscores from member names
    "CA1030": "design",     # Use events where appropriate
    "CA1031": "security",   # Do not catch general exception types
    "CA1034": "design",     # Nested types should not be visible
    "CA1055": "design",     # URI return values should not be strings
    "CA1067": "design",     # Override Equals when implementing IEquatable
    "CA2211": "design",     # Non-constant fields should not be visible
    "CA2215": "resource",   # Dispose methods should call base class dispose
    "CA1510": "design",     # Use ArgumentNullException.ThrowIfNull

    # IDisposableAnalyzers (additional)
    "IDISP025": "resource", # Seal class that implements IDisposable

    # Compiler warnings (CS codes)
    "CS0219": "dead_code",  # Variable assigned but never used
    "CS0414": "dead_code",  # Field assigned but never read
    "CS0649": "dead_code",  # Field never assigned
    "CS0067": "dead_code",  # Event never used

    # SYSLIB codes (obsolete/deprecated)
    "SYSLIB0011": "security", # BinaryFormatter is obsolete
    "SYSLIB0014": "security", # WebRequest is obsolete

    # ==========================================================================
    # SecurityCodeScan.VS2019 (P0 - L7 Security)
    # ==========================================================================
    "SCS0001": "security",   # SQL Injection
    "SCS0002": "security",   # XSS
    "SCS0003": "security",   # XPath Injection
    "SCS0004": "security",   # Certificate Validation Disabled
    "SCS0005": "security",   # Weak Random Number Generator
    "SCS0006": "security",   # Weak Hashing Function (MD5/SHA1)
    "SCS0007": "security",   # XML eXternal Entity Injection (XXE)
    "SCS0008": "security",   # Cookie Without Secure Flag
    "SCS0009": "security",   # Cookie Without HttpOnly Flag
    "SCS0010": "security",   # Weak Cipher Mode
    "SCS0011": "security",   # Weak CBC Mode
    "SCS0012": "security",   # Weak ECB Mode
    "SCS0013": "security",   # Potential SQL Injection (LINQ)
    "SCS0014": "security",   # Potential SQL Injection (WebControls)
    "SCS0015": "security",   # Hardcoded Password
    "SCS0016": "security",   # CSRF Missing
    "SCS0017": "security",   # Request Validation Disabled
    "SCS0018": "security",   # Path Traversal
    "SCS0019": "security",   # OutputCache Conflict
    "SCS0020": "security",   # SQL Injection (OleDb)
    "SCS0021": "security",   # Request Validation Disabled (Attribute)
    "SCS0022": "security",   # Event Validation Disabled
    "SCS0023": "security",   # View State Not Encrypted
    "SCS0024": "security",   # View State MAC Disabled
    "SCS0025": "security",   # SQL Injection (Odbc)
    "SCS0026": "security",   # LDAP Injection
    "SCS0027": "security",   # Open Redirect
    "SCS0028": "security",   # Insecure Deserialization
    "SCS0029": "security",   # XPath Injection (XmlDocument)
    "SCS0030": "security",   # Request Validation Disabled (MVC)
    "SCS0031": "security",   # Command Injection
    "SCS0032": "security",   # Password Complexity
    "SCS0033": "security",   # Password Length
    "SCS0034": "security",   # Password Lockout
    "SCS0035": "security",   # SQL Injection (Entity Framework)

    # ==========================================================================
    # IDisposableAnalyzers (P0 - L2 Resource Management)
    # ==========================================================================
    "IDISP001": "resource",  # Dispose created
    "IDISP002": "resource",  # Dispose member
    "IDISP003": "resource",  # Dispose previous before assignment
    "IDISP004": "resource",  # Don't ignore return value of type IDisposable
    "IDISP005": "resource",  # Return type should indicate that value should be disposed
    "IDISP006": "resource",  # Implement IDisposable
    "IDISP007": "resource",  # Don't dispose injected
    "IDISP008": "resource",  # Don't mix injected and created for member
    "IDISP009": "resource",  # Add IDisposable interface
    "IDISP010": "resource",  # Call base.Dispose(disposing)
    "IDISP011": "resource",  # Don't return disposed instance
    "IDISP012": "resource",  # Property should not return created disposable
    "IDISP013": "resource",  # Await in using
    "IDISP014": "resource",  # Use a single instance of HttpClient
    "IDISP015": "resource",  # Member should not return created and cached instance
    "IDISP016": "resource",  # Don't use disposed instance
    "IDISP017": "resource",  # Prefer using

    # ==========================================================================
    # Microsoft.VisualStudio.Threading.Analyzers (P0 - L6 Engineering Quality)
    # ==========================================================================
    "VSTHRD001": "design",   # Avoid legacy thread switching APIs
    "VSTHRD002": "design",   # Avoid problematic synchronous waits
    "VSTHRD003": "design",   # Avoid awaiting foreign Tasks
    "VSTHRD004": "design",   # Await SwitchToMainThreadAsync
    "VSTHRD010": "design",   # Invoke single-threaded types on Main thread
    "VSTHRD011": "design",   # Use AsyncLazy<T>
    "VSTHRD012": "design",   # Provide JoinableTaskFactory
    "VSTHRD100": "design",   # Avoid async void methods
    "VSTHRD101": "design",   # Avoid unsupported async delegates
    "VSTHRD102": "design",   # Implement internal logic asynchronously
    "VSTHRD103": "design",   # Call async methods when in async method
    "VSTHRD104": "design",   # Offer async methods
    "VSTHRD105": "design",   # Avoid method overloads that assume TaskScheduler.Current
    "VSTHRD106": "design",   # Use InvokeAsync to raise async events
    "VSTHRD107": "design",   # Await Task within using expression
    "VSTHRD108": "design",   # Assert thread affinity unconditionally
    "VSTHRD109": "design",   # Switch instead of assert in async methods
    "VSTHRD110": "design",   # Observe result of async calls
    "VSTHRD111": "design",   # Use .ConfigureAwait(bool)
    "VSTHRD200": "design",   # Use "Async" suffix for async methods
}

# Prefix-based category mapping for analyzers with many rules (e.g., Roslynator)
DD_CATEGORY_PREFIX_MAP = {
    # ==========================================================================
    # Roslynator Analyzers (P0 - L1, L2, L6 Design/Quality)
    # ==========================================================================
    "RCS0": "design",   # Formatting rules
    "RCS1": "design",   # Analyzer rules (most common)
    "RCS9": "design",   # Refactoring rules

    # ==========================================================================
    # AsyncFixer (P1 - L2, L6 Async Anti-Patterns)
    # ==========================================================================
    "AsyncFixer": "resource",  # All AsyncFixer rules relate to async resource handling

    # ==========================================================================
    # ErrorProne.NET (P1 - L2, L6 Correctness)
    # ==========================================================================
    "EPC": "design",    # ErrorProne.NET core rules
    "ERP": "design",    # ErrorProne.NET struct rules

    # ==========================================================================
    # Meziantou.Analyzer (P1 - L1, L2, L6 Good Practices)
    # ==========================================================================
    "MA0": "design",    # All Meziantou rules (MA0xxx)

    # ==========================================================================
    # SmartAnalyzers.ExceptionAnalyzer (P1 - L2 Exception Handling)
    # ==========================================================================
    "EX0": "design",    # Exception handling rules

    # ==========================================================================
    # SonarAnalyzer.CSharp (P1 - L1, L2, L6, L7 Comprehensive)
    # ==========================================================================
    "S1": "design",     # Code smells
    "S2": "design",     # Bugs
    "S3": "design",     # Code smells
    "S4": "security",   # Vulnerabilities
    "S5": "security",   # Security hotspots
    "S6": "design",     # Code smells

    # ==========================================================================
    # IDE Analyzers (Built-in)
    # ==========================================================================
    "IDE0": "design",   # IDE rules (IDE0xxx)

    # ==========================================================================
    # StyleCop.Analyzers (P2 - L1 Code Style)
    # ==========================================================================
    "SA0": "design",    # Special rules
    "SA1": "design",    # Spacing rules
    "SA2": "design",    # Readability rules
    "SA3": "design",    # Ordering rules
    "SA4": "design",    # Maintainability rules
    "SA5": "design",    # Layout rules
    "SA6": "design",    # Documentation rules
    "SX0": "design",    # Alternative rules

    # ==========================================================================
    # xunit.analyzers (P2 - L6 Test Quality)
    # ==========================================================================
    "xUnit": "design",  # All xUnit rules

    # ==========================================================================
    # Moq.Analyzers (P2 - L6 Mock Quality)
    # ==========================================================================
    "Moq": "design",    # All Moq rules

    # ==========================================================================
    # BlowinCleanCode (P2 - L1, L2 Code Simplification)
    # ==========================================================================
    "BCC": "design",    # All BlowinCleanCode rules

    # ==========================================================================
    # DotNetProjectFile.Analyzers (P2 - L1, L6 Build Configuration)
    # ==========================================================================
    "Proj": "design",   # Project file rules
}


def get_dd_category(rule_id: str) -> str:
    """Get DD category for a rule, supporting both exact match and prefix match."""
    # First try exact match
    if rule_id in DD_CATEGORY_MAP:
        return DD_CATEGORY_MAP[rule_id]

    # Then try prefix match
    for prefix, category in DD_CATEGORY_PREFIX_MAP.items():
        if rule_id.startswith(prefix):
            return category

    return "other"


def get_documentation_url(rule_id: str) -> str:
    """Generate documentation URL for common rule prefixes.

    Provides fallback documentation URLs when SARIF helpUri is empty.
    """
    if rule_id.startswith("CA"):
        return f"https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/quality-rules/{rule_id.lower()}"
    elif rule_id.startswith("CS"):
        return f"https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/compiler-messages/{rule_id.lower()}"
    elif rule_id.startswith("IDE"):
        return f"https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/style-rules/{rule_id.lower()}"
    elif rule_id.startswith("SCS"):
        return f"https://security-code-scan.github.io/#{rule_id}"
    elif rule_id.startswith("IDISP"):
        return f"https://github.com/DotNetAnalyzers/IDisposableAnalyzers/blob/master/documentation/{rule_id}.md"
    elif rule_id.startswith("SA") or rule_id.startswith("SX"):
        return f"https://github.com/DotNetAnalyzers/StyleCopAnalyzers/blob/master/documentation/{rule_id}.md"
    elif rule_id.startswith("RCS"):
        return f"https://josefpihrt.github.io/docs/roslynator/analyzers/{rule_id}"
    elif rule_id.startswith("VSTHRD"):
        return f"https://github.com/microsoft/vs-threading/blob/main/doc/analyzers/{rule_id}.md"
    elif rule_id.startswith("MA"):
        return f"https://github.com/meziantou/Meziantou.Analyzer/blob/main/docs/Rules/{rule_id}.md"
    elif rule_id.startswith("ASYNC"):
        return f"https://github.com/semihokur/AsyncFixer/blob/main/README.md#{rule_id.lower()}"
    return ""

# Severity mapping
SEVERITY_MAP = {
    "error": "critical",
    "warning": "high",
    "info": "medium",
    "hidden": "low",
    "none": "low",
}


@dataclass
class Violation:
    """Represents a single code violation."""
    rule_id: str
    dd_category: str
    dd_severity: str
    roslyn_level: str
    file_path: str
    line_start: int
    line_end: int
    column_start: int
    column_end: int
    message: str
    code_snippet: str = ""
    fix_available: bool = False
    documentation_url: str = ""


@dataclass
class FileResult:
    """Analysis results for a single file."""
    path: str
    relative_path: str
    language: str = "csharp"
    lines_of_code: int = 0
    violations: list = field(default_factory=list)

    @property
    def violation_count(self) -> int:
        return len(self.violations)


@dataclass
class AnalysisResult:
    """Complete analysis results."""
    metadata: dict
    files: list
    summary: dict
    statistics: dict
    directory_rollup: list


def find_csproj_files(target_path: Path) -> list[Path]:
    """Find all .csproj files in the target directory."""
    return list(target_path.rglob("*.csproj"))


def run_dotnet_build(project_path: Path, sarif_path: Path, timeout: int = 900) -> tuple[bool, str]:
    """Run dotnet build with SARIF output.

    Args:
        project_path: Path to the .csproj file
        sarif_path: Path where SARIF output should be written
        timeout: Build timeout in seconds (default: 900s = 15 minutes)

    Returns:
        Tuple of (success: bool, output: str)
    """
    # CRITICAL: MSBuild requires absolute paths for ErrorLog, otherwise it
    # interprets relative paths as relative to the .csproj directory
    absolute_sarif_path = sarif_path.absolute()
    cmd = [
        "dotnet", "build",
        str(project_path.absolute()),
        "-v", "q",
        "--no-incremental",  # Force full rebuild to run all analyzers
        "/p:TreatWarningsAsErrors=false",
        f"/p:ErrorLog={absolute_sarif_path},version=2.1",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        # Clean up SARIF file - MSBuild can append non-JSON content
        if absolute_sarif_path.exists():
            try:
                with open(absolute_sarif_path, 'r') as f:
                    content = f.read()
                # Find last valid JSON closing brace and truncate any trailing content
                last_brace = content.rfind('}')
                if last_brace != -1 and last_brace < len(content) - 1:
                    with open(absolute_sarif_path, 'w') as f:
                        f.write(content[:last_brace + 1])
            except Exception:
                pass  # Continue even if cleanup fails
        return True, result.stderr or result.stdout
    except subprocess.TimeoutExpired:
        return False, f"Build timed out after {timeout} seconds"
    except Exception as e:
        return False, str(e)


def parse_sarif(sarif_path: Path) -> list[Violation]:
    """Parse SARIF file and extract violations.

    Handles both SARIF 1.0 and 2.1 formats:
    - SARIF 1.0: locations[].resultFile.uri, resultFile.region
    - SARIF 2.1: locations[].physicalLocation.artifactLocation.uri, physicalLocation.region
    """
    violations = []

    if not sarif_path.exists():
        return violations

    with open(sarif_path, "r") as f:
        content = f.read()

    try:
        sarif_data = json.loads(content)
    except json.JSONDecodeError:
        # Attempt recovery: extract valid JSON portion
        last_brace = content.rfind('}')
        if last_brace != -1:
            try:
                sarif_data = json.loads(content[:last_brace + 1])
            except json.JSONDecodeError:
                return violations  # Give up if still invalid
        else:
            return violations

    sarif_version = sarif_data.get("version", "1.0.0")
    is_sarif_v1 = sarif_version.startswith("1.")

    for run in sarif_data.get("runs", []):
        # Get tool info - different structure in v1 vs v2
        if is_sarif_v1:
            tool = run.get("tool", {})
            rules = {}  # SARIF 1.0 doesn't have rules array in tool
        else:
            tool = run.get("tool", {}).get("driver", {})
            rules = {r.get("id"): r for r in tool.get("rules", [])}

        for result in run.get("results", []):
            rule_id = result.get("ruleId", "")
            level = result.get("level", "warning")

            # Message handling - different in v1 vs v2
            message_data = result.get("message", "")
            if isinstance(message_data, dict):
                message = message_data.get("text", "")
            else:
                message = str(message_data)

            # Get rule info
            rule_info = rules.get(rule_id, {})
            help_uri = rule_info.get("helpUri", "")

            # Get location - different structure in v1 vs v2
            locations = result.get("locations", [])
            if not locations:
                continue

            location = locations[0]

            if is_sarif_v1:
                # SARIF 1.0 format
                result_file = location.get("resultFile", {})
                file_path = result_file.get("uri", "")
                region = result_file.get("region", {})
            else:
                # SARIF 2.1 format
                physical_location = location.get("physicalLocation", {})
                artifact_location = physical_location.get("artifactLocation", {})
                file_path = artifact_location.get("uri", "")
                region = physical_location.get("region", {})

            line_start = region.get("startLine", 0)
            line_end = region.get("endLine", line_start)
            col_start = region.get("startColumn", 0)
            col_end = region.get("endColumn", col_start)

            # Map to DD category
            dd_category = get_dd_category(rule_id)
            dd_severity = SEVERITY_MAP.get(level.lower(), "medium")

            violations.append(Violation(
                rule_id=rule_id,
                dd_category=dd_category,
                dd_severity=dd_severity,
                roslyn_level=level,
                file_path=file_path,
                line_start=line_start,
                line_end=line_end,
                column_start=col_start,
                column_end=col_end,
                message=message,
                documentation_url=help_uri,
            ))

    return violations


def count_lines(file_path: Path) -> int:
    """Count lines of code in a file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def group_violations_by_file(violations: list[Violation], base_path: Path) -> dict[str, FileResult]:
    """Group violations by file and create FileResult objects."""
    files: dict[str, FileResult] = {}

    for v in violations:
        # Normalize path - convert file:// URIs to filesystem paths
        file_path = v.file_path
        if file_path.startswith("file://"):
            # file:///path means /path on Unix (third / is root)
            # Strip only "file://" (7 chars) to preserve the root /
            file_path = file_path[7:]

        # Get relative path
        try:
            rel_path = Path(file_path).relative_to(base_path)
        except ValueError:
            rel_path = Path(file_path)

        key = str(rel_path)

        if key not in files:
            full_path = base_path / rel_path
            files[key] = FileResult(
                path=str(rel_path),
                relative_path=key,
                lines_of_code=count_lines(full_path) if full_path.exists() else 0,
            )

        # Convert violation to dict for storage
        # Ensure severity is populated with a default if empty
        severity = v.dd_severity or "medium"
        # Use helper function for documentation_url when SARIF helpUri is empty
        doc_url = v.documentation_url or get_documentation_url(v.rule_id)

        files[key].violations.append({
            "rule_id": v.rule_id,
            "category": v.dd_category,
            "severity": severity,
            "dd_category": v.dd_category,
            "dd_severity": severity,
            "roslyn_level": v.roslyn_level,
            "line_start": v.line_start,
            "line_end": v.line_end,
            "column_start": v.column_start,
            "column_end": v.column_end,
            "message": v.message,
            "documentation_url": doc_url,
        })

    return files


def compute_statistics(files: dict[str, FileResult], violations: list[Violation]) -> dict:
    """Compute aggregate statistics."""
    violation_counts = [f.violation_count for f in files.values()]
    total_loc = sum(f.lines_of_code for f in files.values())

    # Category distribution
    by_category: dict[str, dict] = {}
    for v in violations:
        cat = v.dd_category
        if cat not in by_category:
            by_category[cat] = {"count": 0, "severity_breakdown": {}}
        by_category[cat]["count"] += 1
        sev = v.dd_severity
        by_category[cat]["severity_breakdown"][sev] = by_category[cat]["severity_breakdown"].get(sev, 0) + 1

    # Rule distribution
    by_rule: dict[str, int] = {}
    for v in violations:
        by_rule[v.rule_id] = by_rule.get(v.rule_id, 0) + 1

    return {
        "violations_per_file": {
            "mean": sum(violation_counts) / len(violation_counts) if violation_counts else 0,
            "median": sorted(violation_counts)[len(violation_counts) // 2] if violation_counts else 0,
            "min": min(violation_counts) if violation_counts else 0,
            "max": max(violation_counts) if violation_counts else 0,
        },
        "violations_per_1000_loc": (len(violations) / total_loc * 1000) if total_loc > 0 else 0,
        "category_distribution": by_category,
        "rule_coverage": {
            "rules_triggered": len(by_rule),
            "rules_available": len(DD_CATEGORY_MAP),
            "coverage_percentage": len(by_rule) / len(DD_CATEGORY_MAP) * 100 if DD_CATEGORY_MAP else 0,
        },
        "file_coverage": {
            "files_with_violations": sum(1 for f in files.values() if f.violation_count > 0),
            "files_clean": sum(1 for f in files.values() if f.violation_count == 0),
            "violation_rate": sum(1 for f in files.values() if f.violation_count > 0) / len(files) * 100 if files else 0,
        },
    }


def compute_directory_rollup(files: dict[str, FileResult]) -> list[dict]:
    """Compute rollup statistics by directory."""
    rollup: dict[str, dict] = {}

    for path, file_result in files.items():
        directory = str(Path(path).parent)
        if directory == ".":
            directory = "root"

        if directory not in rollup:
            rollup[directory] = {
                "directory": directory,
                "total_violations": 0,
                "files_analyzed": 0,
                "by_category": {},
                "by_severity": {},
                "top_rules": {},
            }

        rollup[directory]["files_analyzed"] += 1
        rollup[directory]["total_violations"] += file_result.violation_count

        for v in file_result.violations:
            cat = v["dd_category"]
            sev = v["dd_severity"]
            rule = v["rule_id"]

            rollup[directory]["by_category"][cat] = rollup[directory]["by_category"].get(cat, 0) + 1
            rollup[directory]["by_severity"][sev] = rollup[directory]["by_severity"].get(sev, 0) + 1
            rollup[directory]["top_rules"][rule] = rollup[directory]["top_rules"].get(rule, 0) + 1

    # Sort top rules and convert to list
    for dir_data in rollup.values():
        sorted_rules = sorted(dir_data["top_rules"].items(), key=lambda x: -x[1])[:5]
        dir_data["top_rules"] = [r[0] for r in sorted_rules]

    return list(rollup.values())


def render_dashboard(result: AnalysisResult, console: Console | None = None):
    """Render analysis dashboard to terminal."""
    if not RICH_AVAILABLE or console is None:
        print_simple_summary(result)
        return

    console.print()
    console.print(Panel.fit(
        "[bold blue]Roslyn Analyzers[/bold blue] - Code Quality Analysis",
        border_style="blue"
    ))

    # Summary table
    summary_table = Table(title="Analysis Summary", show_header=True)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")

    summary_table.add_row("Files Analyzed", str(result.summary["total_files_analyzed"]))
    summary_table.add_row("Total Violations", str(result.summary["total_violations"]))
    summary_table.add_row("Files with Violations", str(result.summary["files_with_violations"]))
    summary_table.add_row("Analysis Duration", f"{result.metadata['analysis_duration_ms']}ms")

    console.print(summary_table)
    console.print()

    # Category breakdown table
    cat_table = Table(title="Violations by Category", show_header=True)
    cat_table.add_column("Category", style="cyan")
    cat_table.add_column("Count", style="yellow")
    cat_table.add_column("Percentage", style="green")

    total = result.summary["total_violations"]
    for cat, count in result.summary["violations_by_category"].items():
        pct = (count / total * 100) if total > 0 else 0
        cat_table.add_row(cat, str(count), f"{pct:.1f}%")

    console.print(cat_table)
    console.print()

    # Severity breakdown table
    sev_table = Table(title="Violations by Severity", show_header=True)
    sev_table.add_column("Severity", style="cyan")
    sev_table.add_column("Count", style="yellow")

    for sev, count in result.summary["violations_by_severity"].items():
        color = {"critical": "red", "high": "yellow", "medium": "blue", "low": "dim"}.get(sev, "white")
        sev_table.add_row(f"[{color}]{sev}[/{color}]", str(count))

    console.print(sev_table)
    console.print()

    # Top rules table
    rules_table = Table(title="Top Violated Rules", show_header=True)
    rules_table.add_column("Rule", style="cyan")
    rules_table.add_column("Count", style="yellow")
    rules_table.add_column("Category", style="green")

    for rule_info in result.summary["top_violated_rules"][:10]:
        rules_table.add_row(
            rule_info["rule_id"],
            str(rule_info["count"]),
            rule_info["category"]
        )

    console.print(rules_table)


def print_simple_summary(result: AnalysisResult):
    """Print simple text summary without rich."""
    print("\n" + "=" * 60)
    print("ROSLYN ANALYZERS - ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Files Analyzed: {result.summary['total_files_analyzed']}")
    print(f"Total Violations: {result.summary['total_violations']}")
    print(f"Duration: {result.metadata['analysis_duration_ms']}ms")
    print()
    print("By Category:")
    for cat, count in result.summary["violations_by_category"].items():
        print(f"  {cat}: {count}")
    print()
    print("By Severity:")
    for sev, count in result.summary["violations_by_severity"].items():
        print(f"  {sev}: {count}")
    print("=" * 60)


def analyze(
    target_path: Path,
    output_path: Path | None = None,
    no_color: bool = False,
    build_timeout: int = 900,
) -> AnalysisResult:
    """Main analysis function.

    Args:
        target_path: Path to project or directory containing .csproj files
        output_path: Optional path for output JSON file
        no_color: Disable colored output
        build_timeout: Build timeout in seconds (default: 900s = 15 minutes)

    Returns:
        AnalysisResult with all violations and statistics
    """
    console = Console() if RICH_AVAILABLE and not no_color else None
    start_time = time.time()

    # Find projects
    csproj_files = find_csproj_files(target_path)
    if not csproj_files:
        raise ValueError(f"No .csproj files found in {target_path}")

    if console:
        console.print(f"[cyan]Found {len(csproj_files)} project(s)[/cyan]")

    all_violations: list[Violation] = []
    # Use absolute path for SARIF directory
    sarif_dir = target_path.absolute() / "obj" / "sarif"
    sarif_dir.mkdir(parents=True, exist_ok=True)

    # Track build failures for reporting
    failed_builds: list[tuple[str, str]] = []

    # Build each project
    for i, csproj in enumerate(csproj_files):
        sarif_path = sarif_dir / f"{csproj.stem}.sarif"

        if console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(f"Building {csproj.name}...", total=None)
                success, output = run_dotnet_build(csproj, sarif_path, timeout=build_timeout)
        else:
            print(f"Building {csproj.name}...")
            success, output = run_dotnet_build(csproj, sarif_path, timeout=build_timeout)

        # Check build success and log warnings
        if not success:
            failed_builds.append((csproj.name, output))
            truncated_output = output[:500] + "..." if len(output) > 500 else output
            if console:
                console.print(f"  [yellow]Warning: Build failed for {csproj.name}[/yellow]")
                console.print(f"  [dim]{truncated_output}[/dim]")
            else:
                print(f"  Warning: Build failed for {csproj.name}")
                print(f"  {truncated_output}")

        if sarif_path.exists():
            violations = parse_sarif(sarif_path)
            all_violations.extend(violations)
            if console:
                console.print(f"  [green]Found {len(violations)} violations[/green]")
            else:
                print(f"  Found {len(violations)} violations")
        else:
            # SARIF not created - log warning with context
            reason = "build failed" if not success else "no analyzers produced output"
            if console:
                console.print(f"  [yellow]Warning: No SARIF output for {csproj.name} ({reason})[/yellow]")
            else:
                print(f"  Warning: No SARIF output for {csproj.name} ({reason})")

    # Report build failure summary
    if failed_builds:
        if console:
            console.print(f"\n[yellow]Build Summary: {len(failed_builds)}/{len(csproj_files)} projects failed to build[/yellow]")
        else:
            print(f"\nBuild Summary: {len(failed_builds)}/{len(csproj_files)} projects failed to build")

    # Group by file
    files = group_violations_by_file(all_violations, target_path)

    # Add files without violations
    for cs_file in target_path.rglob("*.cs"):
        rel_path = str(cs_file.relative_to(target_path))
        if rel_path not in files:
            files[rel_path] = FileResult(
                path=rel_path,
                relative_path=rel_path,
                lines_of_code=count_lines(cs_file),
            )

    # Compute statistics
    statistics = compute_statistics(files, all_violations)
    directory_rollup = compute_directory_rollup(files)

    # Build summary
    by_category: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    by_rule: dict[str, int] = {}

    for v in all_violations:
        by_category[v.dd_category] = by_category.get(v.dd_category, 0) + 1
        by_severity[v.dd_severity] = by_severity.get(v.dd_severity, 0) + 1
        by_rule[v.rule_id] = by_rule.get(v.rule_id, 0) + 1

    top_rules = sorted(by_rule.items(), key=lambda x: -x[1])[:10]

    duration_ms = int((time.time() - start_time) * 1000)

    result = AnalysisResult(
        metadata={
            "version": "1.0.0",
            "tool": "roslyn-analyzers",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "target_path": str(target_path.absolute()),
            "analysis_duration_ms": duration_ms,
        },
        files=[{
            "path": f.path,
            "relative_path": f.relative_path,
            "language": f.language,
            "lines_of_code": f.lines_of_code,
            "violation_count": f.violation_count,
            "violations": f.violations,
        } for f in files.values()],
        summary={
            "total_files_analyzed": len(files),
            "total_violations": len(all_violations),
            "files_with_violations": sum(1 for f in files.values() if f.violation_count > 0),
            "violations_by_severity": by_severity,
            "violations_by_category": by_category,
            "violations_by_rule": by_rule,
            "top_violated_rules": [
                {"rule_id": r[0], "count": r[1], "category": get_dd_category(r[0])}
                for r in top_rules
            ],
        },
        statistics=statistics,
        directory_rollup=directory_rollup,
    )

    # Render dashboard
    render_dashboard(result, console)

    # Save output
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump({
                "schema_version": "1.0.0",
                "generated_at": result.metadata["timestamp"],
                "repo_name": target_path.name,
                "repo_path": str(target_path.absolute()),
                "results": {
                    "tool": result.metadata["tool"],
                    "tool_version": result.metadata["version"],
                    "analysis_duration_ms": result.metadata["analysis_duration_ms"],
                    "summary": result.summary,
                    "files": result.files,
                    "statistics": result.statistics,
                    "directory_rollup": result.directory_rollup,
                },
            }, f, indent=2)
        if console:
            console.print(f"\n[green]Results saved to {output_path}[/green]")
        else:
            print(f"\nResults saved to {output_path}")

    return result


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run Roslyn Analyzers on .NET projects"
    )
    parser.add_argument(
        "target_path",
        type=Path,
        help="Path to project or directory containing .csproj files"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output JSON file path"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    parser.add_argument(
        "--build-timeout",
        type=int,
        default=900,
        help="Build timeout in seconds (default: 900 = 15 minutes)"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode (not yet implemented)"
    )

    args = parser.parse_args()

    if not args.target_path.exists():
        print(f"Error: Path does not exist: {args.target_path}")
        sys.exit(1)

    try:
        analyze(args.target_path, args.output, args.no_color, args.build_timeout)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
