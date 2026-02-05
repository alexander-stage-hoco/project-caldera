#!/usr/bin/env python3
"""Smell analysis using Semgrep.

Detects code smells and quality issues using Semgrep static analysis.
Includes 16-section dashboard visualization.
"""

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
# DD Smell Mapping
# =============================================================================

# Map Semgrep rule patterns to DD smell IDs
# Custom DD rules use DD-XX-NAME format which maps directly via dd_smell_id metadata
RULE_TO_SMELL_MAP = {
    # Error Handling (from auto rules)
    "empty-catch": "D1_EMPTY_CATCH",
    "bare-except": "D1_EMPTY_CATCH",
    "pass-in-except": "D1_EMPTY_CATCH",
    "generic-exception-caught": "D2_CATCH_ALL",
    "catch-broad-exception": "D2_CATCH_ALL",
    "throw-ex": "D4_INCORRECT_RETHROW",
    "raise-from-none": "D4_INCORRECT_RETHROW",

    # Async/Concurrency (from auto rules)
    "async-void": "E2_ASYNC_VOID",
    "task-wait": "E1_SYNC_OVER_ASYNC",
    "task-result": "E1_SYNC_OVER_ASYNC",

    # Resource Management (from auto rules)
    "httpclient-new": "F3_HTTPCLIENT_NEW",
    "new-httpclient": "F3_HTTPCLIENT_NEW",

    # Security (from auto rules and p/security-code-scan)
    "sql-injection": "SQL_INJECTION",
    "formatted-sql": "SQL_INJECTION",
    "string-concat-sql": "SQL_INJECTION",
    "sqli": "SQL_INJECTION",
    "sqlinjection": "SQL_INJECTION",
    "raw-sql-query": "SQL_INJECTION",
    "xss": "XSS_VULNERABILITY",
    "cross-site-scripting": "XSS_VULNERABILITY",
    "html-injection": "XSS_VULNERABILITY",
    "path-traversal": "PATH_TRAVERSAL",
    "directory-traversal": "PATH_TRAVERSAL",
    "lfi": "PATH_TRAVERSAL",
    "xxe": "XXE_VULNERABILITY",
    "xml-external-entity": "XXE_VULNERABILITY",
    "xml-parser": "XXE_VULNERABILITY",
    "deserialization": "UNSAFE_DESERIALIZATION",
    "insecure-deserialization": "UNSAFE_DESERIALIZATION",
    "binaryformatter": "UNSAFE_DESERIALIZATION",
    "hardcoded-secret": "HARDCODED_SECRET",
    "hardcoded-password": "HARDCODED_SECRET",
    "hardcoded-credential": "HARDCODED_SECRET",
    "hardcoded-key": "HARDCODED_SECRET",
    "password-in-string": "HARDCODED_SECRET",
    "weak-crypto": "INSECURE_CRYPTO",
    "weak-cipher": "INSECURE_CRYPTO",
    "md5": "INSECURE_CRYPTO",
    "sha1": "INSECURE_CRYPTO",
    "des": "INSECURE_CRYPTO",
    "insecure-random": "INSECURE_CRYPTO",
    "command-injection": "COMMAND_INJECTION",
    "os-command-injection": "COMMAND_INJECTION",
    "process-start": "COMMAND_INJECTION",
    "ldap-injection": "LDAP_INJECTION",
    "xpath-injection": "XPATH_INJECTION",
    "csrf": "CSRF_VULNERABILITY",
    "open-redirect": "OPEN_REDIRECT",
    "ssrf": "SSRF_VULNERABILITY",
    "server-side-request-forgery": "SSRF_VULNERABILITY",
    "missing-authorization": "BROKEN_ACCESS_CONTROL",
    "broken-authorization": "BROKEN_ACCESS_CONTROL",
    "authorization": "BROKEN_ACCESS_CONTROL",
    "jwt-token": "HARDCODED_SECRET",
    "detected-jwt": "HARDCODED_SECRET",
    "deprecated-cipher": "INSECURE_CRYPTO",
    "deprecated_cipher_algorithm": "INSECURE_CRYPTO",
    "use_deprecated_cipher": "INSECURE_CRYPTO",
    "weak-random": "INSECURE_CRYPTO",
    # Security Code Scan rules (SCS0xxx pattern)
    "SCS0002": "SQL_INJECTION",  # SQL Injection
    "SCS0005": "INSECURE_CRYPTO",  # Weak Random Number Generator
    "SCS0006": "INSECURE_CRYPTO",  # Weak Hashing Algorithm (MD5)
    "SCS0007": "XXE_VULNERABILITY",  # XML External Entity Injection
    "SCS0010": "INSECURE_CRYPTO",  # Weak Cipher Mode (DES, TripleDES, RC2)
    "SCS0011": "INSECURE_CRYPTO",  # Weak CBC Mode Cipher
    "SCS0013": "PATH_TRAVERSAL",  # Potential Path Traversal
    "SCS0018": "PATH_TRAVERSAL",  # Potential Path Injection
    "SCS0015": "HARDCODED_SECRET",  # Hardcoded Password
    "SCS0016": "CSRF_VULNERABILITY",  # CSRF Token Missing
    "SCS0019": "LDAP_INJECTION",  # LDAP Injection
    "SCS0020": "OPEN_REDIRECT",  # Open Redirect
    "SCS0026": "COMMAND_INJECTION",  # OS Command Injection
    "SCS0028": "UNSAFE_DESERIALIZATION",  # Insecure Deserialization
    "SCS0029": "XSS_VULNERABILITY",  # Cross-Site Scripting

    # OWASP Top 10 patterns (from p/owasp-top-ten ruleset)
    "A01": "BROKEN_ACCESS_CONTROL",  # A01:2021 Broken Access Control
    "A02": "INSECURE_CRYPTO",  # A02:2021 Cryptographic Failures
    "A03": "SQL_INJECTION",  # A03:2021 Injection
    "A05": "SECURITY_MISCONFIGURATION",  # A05:2021 Security Misconfiguration
    "A07": "XSS_VULNERABILITY",  # A07:2021 Cross-Site Scripting
    "A08": "UNSAFE_DESERIALIZATION",  # A08:2021 Software and Data Integrity Failures

    # CWE Top 25 patterns (from p/cwe-top-25 ruleset)
    "CWE-79": "XSS_VULNERABILITY",  # Cross-site Scripting
    "CWE-89": "SQL_INJECTION",  # SQL Injection
    "CWE-94": "CODE_INJECTION",  # Code Injection
    "CWE-502": "UNSAFE_DESERIALIZATION",  # Deserialization of Untrusted Data
    "CWE-611": "XXE_VULNERABILITY",  # XML External Entity
    "CWE-798": "HARDCODED_SECRET",  # Use of Hard-coded Credentials
    "CWE-22": "PATH_TRAVERSAL",  # Path Traversal
    "CWE-78": "COMMAND_INJECTION",  # OS Command Injection
    "CWE-352": "CSRF_VULNERABILITY",  # Cross-Site Request Forgery
    "CWE-918": "SSRF_VULNERABILITY",  # Server-Side Request Forgery
    "CWE-327": "INSECURE_CRYPTO",  # Use of a Broken or Risky Cryptographic Algorithm
    "CWE-330": "INSECURE_CRYPTO",  # Use of Insufficiently Random Values
    "CWE-601": "OPEN_REDIRECT",  # URL Redirection to Untrusted Site

    # Microsoft CA rule patterns (from community-rules/csharp)
    # Deserialization (CA2300-CA2330)
    "CA2300": "UNSAFE_DESERIALIZATION",  # BinaryFormatter deserialization
    "CA2301": "UNSAFE_DESERIALIZATION",  # BinaryFormatter without binder
    "CA2302": "UNSAFE_DESERIALIZATION",  # NetDataContractSerializer
    "CA2305": "UNSAFE_DESERIALIZATION",  # LosFormatter deserialization
    "CA2310": "UNSAFE_DESERIALIZATION",  # NetDataContractSerializer
    "CA2311": "UNSAFE_DESERIALIZATION",  # NetDataContractSerializer without binder
    "CA2312": "UNSAFE_DESERIALIZATION",  # NetDataContractSerializer without binder
    "CA2315": "UNSAFE_DESERIALIZATION",  # ObjectStateFormatter deserialization
    "CA2321": "UNSAFE_DESERIALIZATION",  # JavaScriptSerializer deserialization
    "CA2322": "UNSAFE_DESERIALIZATION",  # JavaScriptSerializer with SimpleTypeResolver
    "CA2326": "UNSAFE_DESERIALIZATION",  # TypeNameHandling not None
    "CA2327": "UNSAFE_DESERIALIZATION",  # JsonSerializer with unsafe settings
    "CA2328": "UNSAFE_DESERIALIZATION",  # JsonSerializerSettings unsafe
    "CA2329": "UNSAFE_DESERIALIZATION",  # JsonSerializer without binder
    "CA2330": "UNSAFE_DESERIALIZATION",  # JsonSerializerSettings unsafe
    "CA2350": "UNSAFE_DESERIALIZATION",  # DataTable.ReadXml
    "CA2351": "UNSAFE_DESERIALIZATION",  # DataSet.ReadXml
    "CA2356": "UNSAFE_DESERIALIZATION",  # DataSet/DataTable in web deserialization

    # Security (CA3xxx - Injection)
    "CA3001": "SQL_INJECTION",  # SQL Injection
    "CA3002": "XSS_VULNERABILITY",  # XSS
    "CA3003": "PATH_TRAVERSAL",  # File Path Injection
    "CA3004": "INFORMATION_DISCLOSURE",  # Information Disclosure
    "CA3005": "LDAP_INJECTION",  # LDAP Injection
    "CA3006": "COMMAND_INJECTION",  # Process Command Injection
    "CA3007": "OPEN_REDIRECT",  # Open Redirect
    "CA3008": "XPATH_INJECTION",  # XPath Injection
    "CA3009": "CODE_INJECTION",  # XML Injection
    "CA3010": "CODE_INJECTION",  # XAML Injection
    "CA3011": "CODE_INJECTION",  # DLL Injection
    "CA3012": "CODE_INJECTION",  # Regex Injection

    # Cryptography (CA5350-CA5405)
    "CA5350": "INSECURE_CRYPTO",  # Weak Cryptographic Algorithm (DES, TripleDES)
    "CA5351": "INSECURE_CRYPTO",  # Broken Cryptographic Algorithm (MD5, SHA1)
    "CA5358": "INSECURE_CRYPTO",  # Unsafe Cipher Mode
    "CA5359": "INSECURE_CRYPTO",  # Do Not Disable Certificate Validation
    "CA5360": "INSECURE_CRYPTO",  # Do Not Call Dangerous Methods
    "CA5361": "INSECURE_CRYPTO",  # Disable SChannel Use of Strong Crypto
    "CA5362": "UNSAFE_DESERIALIZATION",  # Potential Reference Cycle in Deserialize
    "CA5363": "SECURITY_MISCONFIGURATION",  # Do Not Disable Request Validation
    "CA5364": "INSECURE_CRYPTO",  # Do Not Use Deprecated Security Protocols
    "CA5365": "SECURITY_MISCONFIGURATION",  # Do Not Disable HTTP Header Checking
    "CA5366": "XXE_VULNERABILITY",  # Use XmlReader for DataSet Read XML
    "CA5367": "UNSAFE_DESERIALIZATION",  # Do Not Serialize Types With Pointer Fields
    "CA5368": "SECURITY_MISCONFIGURATION",  # Set ViewStateUserKey for Page
    "CA5369": "XXE_VULNERABILITY",  # Use XmlReader for Deserialize
    "CA5370": "XXE_VULNERABILITY",  # Use XmlReader for Validating Reader
    "CA5371": "XXE_VULNERABILITY",  # Use XmlReader for Schema Read
    "CA5372": "XXE_VULNERABILITY",  # Use XmlReader for XPathDocument
    "CA5373": "INSECURE_CRYPTO",  # Do Not Use Obsolete Key Derivation Function
    "CA5374": "INSECURE_CRYPTO",  # Do Not Use XslTransform
    "CA5375": "HARDCODED_SECRET",  # Do Not Use Account Shared Access Signature
    "CA5376": "SECURITY_MISCONFIGURATION",  # Use SharedAccessProtocol HttpsOnly
    "CA5377": "SECURITY_MISCONFIGURATION",  # Use Container Level Access Policy
    "CA5378": "SECURITY_MISCONFIGURATION",  # ServicePointManagerSecurityProtocols
    "CA5379": "INSECURE_CRYPTO",  # Weak Key Derivation Function Algorithm
    "CA5380": "INSECURE_CRYPTO",  # Do Not Add Certificates To Root Store
    "CA5381": "INSECURE_CRYPTO",  # Ensure Certificates Not Added To Root
    "CA5382": "SECURITY_MISCONFIGURATION",  # Use Secure Cookies In ASP.NET Core
    "CA5383": "SECURITY_MISCONFIGURATION",  # Ensure Use Secure Cookies
    "CA5384": "INSECURE_CRYPTO",  # Do Not Use Digital Signature Algorithm
    "CA5385": "INSECURE_CRYPTO",  # Use RSA with Sufficient Key Size
    "CA5386": "HARDCODED_SECRET",  # Avoid Hardcoding SecurityProtocolType
    "CA5387": "INSECURE_CRYPTO",  # Weak Key Derivation Function Iteration Count
    "CA5388": "INSECURE_CRYPTO",  # Ensure Sufficient Iteration Count
    "CA5389": "PATH_TRAVERSAL",  # Do Not Add Archive Item's Path To Target
    "CA5390": "INSECURE_CRYPTO",  # Do Not Hard-code Encryption Key
    "CA5391": "CSRF_VULNERABILITY",  # Use Antiforgery Tokens In ASP.NET Core
    "CA5392": "BROKEN_ACCESS_CONTROL",  # Use DefaultDllImportSearchPaths
    "CA5393": "SECURITY_MISCONFIGURATION",  # Do Not Use Unsafe DllImportSearchPath
    "CA5394": "INSECURE_CRYPTO",  # Do Not Use Insecure Randomness
    "CA5395": "BROKEN_ACCESS_CONTROL",  # Miss HttpVerb Attribute For Action Methods
    "CA5396": "SECURITY_MISCONFIGURATION",  # Set HttpOnly To True For HttpCookie
    "CA5397": "SECURITY_MISCONFIGURATION",  # Do Not Use Deprecated SslProtocols
    "CA5398": "SECURITY_MISCONFIGURATION",  # Avoid Hardcoded SslProtocols
    "CA5399": "SECURITY_MISCONFIGURATION",  # Disable HttpClient Certificate Check
    "CA5400": "SECURITY_MISCONFIGURATION",  # Ensure HttpClient Certificate Check
    "CA5401": "INSECURE_CRYPTO",  # Do Not Use CreateEncryptor With Non-Default IV
    "CA5402": "INSECURE_CRYPTO",  # Use CreateEncryptor With Default IV
    "CA5403": "HARDCODED_SECRET",  # Do Not Hard-code Certificate
    "CA5404": "SECURITY_MISCONFIGURATION",  # Do Not Disable Token Validation Checks
    "CA5405": "SECURITY_MISCONFIGURATION",  # Do Not Always Skip Token Validation

    # Custom DD rules (direct mappings for DD-prefixed rule IDs)
    # Error Handling (D1-D7)
    "DD-D1-EMPTY-CATCH": "D1_EMPTY_CATCH",
    "DD-D2-CATCH-ALL": "D2_CATCH_ALL",
    "DD-D3-LOG-AND-SWALLOW": "D3_LOG_AND_CONTINUE",
    "DD-D4-INCORRECT-RETHROW": "D4_INCORRECT_RETHROW",
    "DD-D5-GENERIC-EXCEPTION": "D5_GENERIC_EXCEPTION",
    "DD-D7-CATCH-RETURN": "D7_CATCH_RETURN_DEFAULT",
    # Async/Concurrency (E1-E7)
    "DD-E1-SYNC-OVER-ASYNC": "E1_SYNC_OVER_ASYNC",
    "DD-E2-ASYNC-VOID": "E2_ASYNC_VOID",
    "DD-E3-MISSING-CONFIGURE-AWAIT": "E3_MISSING_CONFIGURE_AWAIT",
    "DD-E4-MISSING-CANCELLATION": "E4_MISSING_CANCELLATION",
    "DD-E5-UNSAFE-LOCK": "E5_UNSAFE_LOCK",
    "DD-E7-ASYNC-WITHOUT-AWAIT": "E7_ASYNC_WITHOUT_AWAIT",
    # Resource Management (F2-F6)
    "DD-F2-MISSING-USING": "F2_MISSING_USING",
    "DD-F3-HTTPCLIENT-NEW": "F3_HTTPCLIENT_NEW",
    "DD-F4-STRING-CONCAT": "F4_EXCESSIVE_ALLOCATION",
    "DD-F4-STRING-PLUSEQUALS": "F4_EXCESSIVE_ALLOCATION",
    "DD-F5-DISPOSABLE-FIELD": "F5_DISPOSABLE_FIELD",
    "DD-F6-EVENT": "F6_EVENT_HANDLER_LEAK",
    "DD-F6-LISTENER": "F6_EVENT_HANDLER_LEAK",
    # Nullability (G1-G3)
    "DD-G1-NULLABLE-DISABLED": "G1_NULLABLE_DISABLED",
    "DD-G2-NULL-FORGIVING": "G2_NULL_FORGIVING",
    "DD-G3-NULLABLE-RESTORE": "G3_INCONSISTENT_NULLABLE",
    # API Design (H1-H8)
    "DD-H1-MUTABLE-DTO": "H1_MUTABLE_DTO",
    "DD-H2-LONG-PARAM-LIST": "H2_LONG_PARAM_LIST",
    "DD-H3-BOOLEAN-BLINDNESS": "H3_BOOLEAN_BLINDNESS",
    "DD-H4-BOOLEAN-BLINDNESS": "H4_BOOLEAN_BLINDNESS",
    "DD-H4-COMPLEX-CONDITIONAL": "H4_COMPLEX_CONDITIONALS",
    "DD-H5-PUBLIC-MUTABLE-COLLECTION": "H5_PUBLIC_MUTABLE_COLLECTION",
    "DD-H5-HIDDEN-DEPENDENCY": "H5_HIDDEN_DEPENDENCIES",
    "DD-H6-STATIC-MUTABLE": "H6_STATIC_MUTABLE_STATE",
    "DD-H6-PUBLIC-STATIC": "H6_STATIC_MUTABLE_STATE",
    "DD-H8-DYNAMIC": "H8_DYNAMIC_USAGE",
    # Dead Code (I1-I5)
    "DD-I1-UNUSED-IMPORT": "I1_UNUSED_IMPORT",
    "DD-I3-UNREACHABLE": "I2_UNREACHABLE_CODE",
    "DD-I3-PRAGMA": "I3_TOO_MANY_SUPPRESSIONS",
    "DD-I3-SUPPRESS": "I3_TOO_MANY_SUPPRESSIONS",
    "DD-I3-NOQA": "I3_TOO_MANY_SUPPRESSIONS",
    "DD-I3-ESLINT": "I3_TOO_MANY_SUPPRESSIONS",
    "DD-I4-COMMENTED-CODE": "I4_COMMENTED_CODE",
    "DD-I5-EMPTY-METHOD": "I5_EMPTY_METHOD",
    "DD-I2-UNREACHABLE": "I2_UNREACHABLE_CODE",
    # Refactoring (B2, B6-B8)
    "DD-B2-LONG-PARAM-LIST": "B2_LONG_PARAMETER_LIST",
    "DD-B2-LONG-CTOR-PARAMS": "B2_LONG_PARAMETER_LIST",
    "DD-B6-MESSAGE-CHAIN": "B6_MESSAGE_CHAINS",
    "DD-B8-SWITCH-ON-TYPE": "B8_SWITCH_STATEMENTS",
    "DD-B8-TYPE-CHECK": "B8_SWITCH_STATEMENTS",
    "DD-B8-INSTANCEOF": "B8_SWITCH_STATEMENTS",
    "DD-B8-ISINSTANCE": "B8_SWITCH_STATEMENTS",
    # Dependency (C4)
    "DD-C4-SERVICE-LOCATOR": "C4_INAPPROPRIATE_INTIMACY",
    "DD-C4-TIGHT-COUPLING": "C4_INAPPROPRIATE_INTIMACY",

    # ==========================================================================
    # Code Quality Rules (Phase 3: r2c-best-practices, r2c-ci)
    # ==========================================================================
    # r2c-best-practices patterns
    "mutable-default-argument": "H5_HIDDEN_DEPENDENCIES",
    "mutable-default": "H5_HIDDEN_DEPENDENCIES",
    "useless-comparison": "I2_UNREACHABLE_CODE",
    "useless-assignment": "I2_UNREACHABLE_CODE",
    "unreachable-code": "I2_UNREACHABLE_CODE",
    "dead-code": "I2_UNREACHABLE_CODE",
    "unused-variable": "I1_UNUSED_IMPORT",
    "unused-import": "I1_UNUSED_IMPORT",
    "redundant-return": "I2_UNREACHABLE_CODE",
    "redundant-expression": "I2_UNREACHABLE_CODE",
    "always-true": "I2_UNREACHABLE_CODE",
    "always-false": "I2_UNREACHABLE_CODE",
    "tautology": "I2_UNREACHABLE_CODE",
    "comparison-to-itself": "I2_UNREACHABLE_CODE",
    "self-comparison": "I2_UNREACHABLE_CODE",

    # Correctness patterns (r2c-ci)
    "correctness": "CORRECTNESS_ISSUE",
    "logic-error": "CORRECTNESS_ISSUE",
    "incorrect": "CORRECTNESS_ISSUE",
    "off-by-one": "CORRECTNESS_ISSUE",
    "boundary": "CORRECTNESS_ISSUE",
    "type-mismatch": "CORRECTNESS_ISSUE",
    "null-pointer": "CORRECTNESS_ISSUE",
    "null-deference": "CORRECTNESS_ISSUE",
    "divide-by-zero": "CORRECTNESS_ISSUE",
    "infinite-loop": "CORRECTNESS_ISSUE",
    "race-condition": "E5_UNSAFE_LOCK",

    # Best practice patterns
    "best-practice": "BEST_PRACTICE_VIOLATION",
    "anti-pattern": "BEST_PRACTICE_VIOLATION",
    "code-smell": "BEST_PRACTICE_VIOLATION",
    "maintainability": "BEST_PRACTICE_VIOLATION",
    "deprecated-api": "BEST_PRACTICE_VIOLATION",
    "deprecated-function": "BEST_PRACTICE_VIOLATION",
    "performance": "PERFORMANCE_ISSUE",
    "inefficient": "PERFORMANCE_ISSUE",
    "complexity": "A2_HIGH_CYCLOMATIC",

    # ==========================================================================
    # Multi-Language Registry Rulesets (SEMGREP_USE_MULTI_LANG=1)
    # Patterns from p/javascript, p/typescript, p/python, p/java, p/go
    # ==========================================================================

    # JavaScript/TypeScript security patterns (p/javascript, p/typescript)
    "react-dangerouslysetinnerhtml": "XSS_VULNERABILITY",
    "react-raw-html": "XSS_VULNERABILITY",
    "dom-xss": "XSS_VULNERABILITY",
    "document-write": "XSS_VULNERABILITY",
    "innerhtml": "XSS_VULNERABILITY",
    "eval": "CODE_INJECTION",
    "new-function": "CODE_INJECTION",
    "settimeout-string": "CODE_INJECTION",
    "setinterval-string": "CODE_INJECTION",
    "child-process-exec": "COMMAND_INJECTION",
    "spawn-shell": "COMMAND_INJECTION",
    "nosql-injection": "SQL_INJECTION",
    "mongodb-injection": "SQL_INJECTION",
    "sequelize-injection": "SQL_INJECTION",
    "knex-raw": "SQL_INJECTION",
    "prototype-pollution": "SECURITY_MISCONFIGURATION",
    "express-open-redirect": "OPEN_REDIRECT",
    "express-ssrf": "SSRF_VULNERABILITY",
    "jwt-hardcoded": "HARDCODED_SECRET",
    "jwt-none-algorithm": "INSECURE_CRYPTO",
    "weak-ssl": "INSECURE_CRYPTO",
    "insecure-cookie": "SECURITY_MISCONFIGURATION",
    "cors-misconfiguration": "SECURITY_MISCONFIGURATION",
    "unsafe-regex": "PERFORMANCE_ISSUE",
    "regex-dos": "PERFORMANCE_ISSUE",

    # Python security patterns (p/python)
    "flask-app-debug": "SECURITY_MISCONFIGURATION",
    "flask-send-file": "PATH_TRAVERSAL",
    "django-raw-sql": "SQL_INJECTION",
    "django-orm-injection": "SQL_INJECTION",
    "subprocess-shell": "COMMAND_INJECTION",
    "os-system": "COMMAND_INJECTION",
    "popen-shell": "COMMAND_INJECTION",
    "yaml-load": "UNSAFE_DESERIALIZATION",
    "pickle-load": "UNSAFE_DESERIALIZATION",
    "marshal-loads": "UNSAFE_DESERIALIZATION",
    "shelve-open": "UNSAFE_DESERIALIZATION",
    "jinja2-autoescape": "XSS_VULNERABILITY",
    "django-safestring": "XSS_VULNERABILITY",
    "request-verify-false": "INSECURE_CRYPTO",
    "weak-ssl-version": "INSECURE_CRYPTO",
    "hashlib-md5": "INSECURE_CRYPTO",
    "hashlib-sha1": "INSECURE_CRYPTO",
    "pycrypto-weak": "INSECURE_CRYPTO",
    "assert-debug": "BEST_PRACTICE_VIOLATION",
    "hardcoded-binding": "SECURITY_MISCONFIGURATION",

    # Java security patterns (p/java)
    "spring-sqli": "SQL_INJECTION",
    "jdbc-sqli": "SQL_INJECTION",
    "hibernate-sqli": "SQL_INJECTION",
    "jpa-sqli": "SQL_INJECTION",
    "mybatis-sqli": "SQL_INJECTION",
    "spring-xss": "XSS_VULNERABILITY",
    "jsp-xss": "XSS_VULNERABILITY",
    "freemarker-xss": "XSS_VULNERABILITY",
    "velocity-xss": "XSS_VULNERABILITY",
    "runtime-exec": "COMMAND_INJECTION",
    "processbuilder-injection": "COMMAND_INJECTION",
    "java-deserialization": "UNSAFE_DESERIALIZATION",
    "objectinputstream": "UNSAFE_DESERIALIZATION",
    "xmldecoder": "UNSAFE_DESERIALIZATION",
    "snakeyaml-unsafe": "UNSAFE_DESERIALIZATION",
    "xxe-documentbuilder": "XXE_VULNERABILITY",
    "xxe-saxparser": "XXE_VULNERABILITY",
    "xxe-xmlreader": "XXE_VULNERABILITY",
    "spring-csrf": "CSRF_VULNERABILITY",
    "spring-open-redirect": "OPEN_REDIRECT",
    "spring-ssrf": "SSRF_VULNERABILITY",
    "java-ldap-injection": "LDAP_INJECTION",
    "java-xpath-injection": "XPATH_INJECTION",
    "weak-random": "INSECURE_CRYPTO",
    "ecb-mode": "INSECURE_CRYPTO",
    "static-iv": "INSECURE_CRYPTO",
    "hardcoded-iv": "INSECURE_CRYPTO",

    # Go security patterns (p/go)
    "go-sqli": "SQL_INJECTION",
    "gorm-sqli": "SQL_INJECTION",
    "sqlx-injection": "SQL_INJECTION",
    "template-injection": "XSS_VULNERABILITY",
    "html-template-xss": "XSS_VULNERABILITY",
    "exec-injection": "COMMAND_INJECTION",
    "os-exec-injection": "COMMAND_INJECTION",
    "yaml-unmarshal": "UNSAFE_DESERIALIZATION",
    "json-unmarshal-interface": "UNSAFE_DESERIALIZATION",
    "ssrf-http-request": "SSRF_VULNERABILITY",
    "path-traversal-join": "PATH_TRAVERSAL",
    "filepath-join-traversal": "PATH_TRAVERSAL",
    "tls-insecure-skip": "INSECURE_CRYPTO",
    "weak-tls": "INSECURE_CRYPTO",
    "rand-crypto": "INSECURE_CRYPTO",
    "defer-in-loop": "RESOURCE_LEAK",
    "goroutine-leak": "RESOURCE_LEAK",

    # ==========================================================================
    # Elttam Audit Rules (SEMGREP_USE_ELTTAM=1)
    # Entrypoint discovery and code audit patterns
    # ==========================================================================

    # ASP.NET/C# entrypoints
    "aspnet-controller": "ENTRYPOINT_DISCOVERY",
    "aspnet-apicontroller": "ENTRYPOINT_DISCOVERY",
    "aspnet-route": "ENTRYPOINT_DISCOVERY",
    "aspnet-httpget": "ENTRYPOINT_DISCOVERY",
    "aspnet-httppost": "ENTRYPOINT_DISCOVERY",
    "aspnet-httpput": "ENTRYPOINT_DISCOVERY",
    "aspnet-httpdelete": "ENTRYPOINT_DISCOVERY",
    "aspnet-action": "ENTRYPOINT_DISCOVERY",
    "webapi-controller": "ENTRYPOINT_DISCOVERY",
    "mvc-controller": "ENTRYPOINT_DISCOVERY",
    "razor-page": "ENTRYPOINT_DISCOVERY",
    "minimal-api": "ENTRYPOINT_DISCOVERY",
    "grpc-service": "ENTRYPOINT_DISCOVERY",
    "signalr-hub": "ENTRYPOINT_DISCOVERY",

    # Python web framework entrypoints
    "flask-route": "ENTRYPOINT_DISCOVERY",
    "flask-endpoint": "ENTRYPOINT_DISCOVERY",
    "django-view": "ENTRYPOINT_DISCOVERY",
    "django-urlpattern": "ENTRYPOINT_DISCOVERY",
    "django-rest-viewset": "ENTRYPOINT_DISCOVERY",
    "django-rest-apiview": "ENTRYPOINT_DISCOVERY",
    "fastapi-route": "ENTRYPOINT_DISCOVERY",
    "fastapi-endpoint": "ENTRYPOINT_DISCOVERY",
    "tornado-handler": "ENTRYPOINT_DISCOVERY",
    "aiohttp-route": "ENTRYPOINT_DISCOVERY",

    # JavaScript/TypeScript web framework entrypoints
    "express-route": "ENTRYPOINT_DISCOVERY",
    "express-router": "ENTRYPOINT_DISCOVERY",
    "express-middleware": "ENTRYPOINT_DISCOVERY",
    "koa-route": "ENTRYPOINT_DISCOVERY",
    "fastify-route": "ENTRYPOINT_DISCOVERY",
    "hapi-route": "ENTRYPOINT_DISCOVERY",
    "nestjs-controller": "ENTRYPOINT_DISCOVERY",
    "nestjs-route": "ENTRYPOINT_DISCOVERY",

    # Java web framework entrypoints
    "spring-requestmapping": "ENTRYPOINT_DISCOVERY",
    "spring-getmapping": "ENTRYPOINT_DISCOVERY",
    "spring-postmapping": "ENTRYPOINT_DISCOVERY",
    "spring-putmapping": "ENTRYPOINT_DISCOVERY",
    "spring-deletemapping": "ENTRYPOINT_DISCOVERY",
    "spring-controller": "ENTRYPOINT_DISCOVERY",
    "spring-restcontroller": "ENTRYPOINT_DISCOVERY",
    "jaxrs-path": "ENTRYPOINT_DISCOVERY",
    "jaxrs-resource": "ENTRYPOINT_DISCOVERY",
    "servlet-mapping": "ENTRYPOINT_DISCOVERY",
    "struts-action": "ENTRYPOINT_DISCOVERY",

    # Go web framework entrypoints
    "http-handlefunc": "ENTRYPOINT_DISCOVERY",
    "http-handler": "ENTRYPOINT_DISCOVERY",
    "gin-route": "ENTRYPOINT_DISCOVERY",
    "gin-handler": "ENTRYPOINT_DISCOVERY",
    "echo-route": "ENTRYPOINT_DISCOVERY",
    "fiber-route": "ENTRYPOINT_DISCOVERY",
    "chi-route": "ENTRYPOINT_DISCOVERY",
    "gorilla-route": "ENTRYPOINT_DISCOVERY",

    # Rust web framework entrypoints
    "actix-route": "ENTRYPOINT_DISCOVERY",
    "actix-handler": "ENTRYPOINT_DISCOVERY",
    "rocket-route": "ENTRYPOINT_DISCOVERY",
    "axum-route": "ENTRYPOINT_DISCOVERY",
    "warp-route": "ENTRYPOINT_DISCOVERY",

    # Audit-specific patterns (from Elttam rules-audit)
    "user-input-sink": "AUDIT_INPUT_SINK",
    "sensitive-data-flow": "AUDIT_DATA_FLOW",
    "authentication-bypass": "AUDIT_AUTH_BYPASS",
    "authorization-check": "AUDIT_AUTH_CHECK",
    "session-management": "AUDIT_SESSION",
    "file-upload": "AUDIT_FILE_UPLOAD",
    "output-encoding": "AUDIT_OUTPUT_ENCODING",
    "crypto-usage": "AUDIT_CRYPTO_USAGE",
    "logging-sensitive": "AUDIT_LOGGING",
    "error-disclosure": "AUDIT_ERROR_DISCLOSURE",
}

# DD Smell Categories
SMELL_CATEGORIES = {
    # Error Handling (D1-D7)
    "D1_EMPTY_CATCH": "error_handling",
    "D2_CATCH_ALL": "error_handling",
    "D3_LOG_AND_CONTINUE": "error_handling",
    "D4_INCORRECT_RETHROW": "error_handling",
    "D5_GENERIC_EXCEPTION": "error_handling",
    "D7_CATCH_RETURN_DEFAULT": "error_handling",
    # Async/Concurrency (E1-E7)
    "E1_SYNC_OVER_ASYNC": "async_concurrency",
    "E2_ASYNC_VOID": "async_concurrency",
    "E3_MISSING_CONFIGURE_AWAIT": "async_concurrency",
    "E4_MISSING_CANCELLATION": "async_concurrency",
    "E5_UNSAFE_LOCK": "async_concurrency",
    "E7_ASYNC_WITHOUT_AWAIT": "async_concurrency",
    # Resource Management (F2-F6)
    "F2_MISSING_USING": "resource_management",
    "F3_HTTPCLIENT_NEW": "resource_management",
    "F4_EXCESSIVE_ALLOCATION": "resource_management",
    "F5_DISPOSABLE_FIELD": "resource_management",
    "F6_EVENT_HANDLER_LEAK": "resource_management",
    # Nullability (G1-G3)
    "G1_NULLABLE_DISABLED": "nullability",
    "G2_NULL_FORGIVING": "nullability",
    "G3_INCONSISTENT_NULLABLE": "nullability",
    # API Design (H1-H8)
    "H1_MUTABLE_DTO": "api_design",
    "H2_LONG_PARAM_LIST": "api_design",
    "H3_BOOLEAN_BLINDNESS": "api_design",
    "H4_BOOLEAN_BLINDNESS": "api_design",
    "H4_COMPLEX_CONDITIONALS": "api_design",
    "H5_PUBLIC_MUTABLE_COLLECTION": "api_design",
    "H5_HIDDEN_DEPENDENCIES": "api_design",
    "H6_STATIC_MUTABLE_STATE": "api_design",
    "H8_DYNAMIC_USAGE": "api_design",
    # Dead Code (I1-I5)
    "I1_UNUSED_IMPORT": "dead_code",
    "I3_UNREACHABLE_CODE": "dead_code",
    "I3_TOO_MANY_SUPPRESSIONS": "dead_code",
    "I4_COMMENTED_CODE": "dead_code",
    "I5_EMPTY_METHOD": "dead_code",
    "I2_UNREACHABLE_CODE": "dead_code",
    # Refactoring (B2, B6-B8)
    "B2_LONG_PARAMETER_LIST": "refactoring",
    "B6_MESSAGE_CHAINS": "refactoring",
    "B8_SWITCH_STATEMENTS": "refactoring",
    # Dependency (C3-C4)
    "C3_GOD_CLASS": "dependency",
    "C4_INAPPROPRIATE_INTIMACY": "dependency",
    # Security (SQL injection, XSS, path traversal, XXE, etc.)
    "SQL_INJECTION": "security",
    "XSS_VULNERABILITY": "security",
    "PATH_TRAVERSAL": "security",
    "XXE_VULNERABILITY": "security",
    "UNSAFE_DESERIALIZATION": "security",
    "HARDCODED_SECRET": "security",
    "INSECURE_CRYPTO": "security",
    "COMMAND_INJECTION": "security",
    "LDAP_INJECTION": "security",
    "XPATH_INJECTION": "security",
    "CSRF_VULNERABILITY": "security",
    "OPEN_REDIRECT": "security",
    "SSRF_VULNERABILITY": "security",
    "BROKEN_ACCESS_CONTROL": "security",
    # Additional security categories (from OWASP/CWE/CA rules)
    "CODE_INJECTION": "security",
    "SECURITY_MISCONFIGURATION": "security",
    "INFORMATION_DISCLOSURE": "security",
    # Size/Complexity (legacy)
    "A2_HIGH_CYCLOMATIC": "size_complexity",
    "A3_DEEP_NESTING": "size_complexity",
    # Code Quality (Phase 3: r2c-best-practices, r2c-ci)
    "CORRECTNESS_ISSUE": "correctness",
    "BEST_PRACTICE_VIOLATION": "best_practice",
    "PERFORMANCE_ISSUE": "performance",
    # Resource leaks (multi-language patterns)
    "RESOURCE_LEAK": "resource_management",
    # Entrypoint Discovery (Elttam audit rules)
    "ENTRYPOINT_DISCOVERY": "entrypoint_discovery",
    # Audit-specific categories (Elttam audit rules)
    "AUDIT_INPUT_SINK": "audit",
    "AUDIT_DATA_FLOW": "audit",
    "AUDIT_AUTH_BYPASS": "audit",
    "AUDIT_AUTH_CHECK": "audit",
    "AUDIT_SESSION": "audit",
    "AUDIT_FILE_UPLOAD": "audit",
    "AUDIT_OUTPUT_ENCODING": "audit",
    "AUDIT_CRYPTO_USAGE": "audit",
    "AUDIT_LOGGING": "audit",
    "AUDIT_ERROR_DISCLOSURE": "audit",
}

# Severity mapping
SEVERITY_MAP = {
    "ERROR": "CRITICAL",
    "WARNING": "HIGH",
    "INFO": "MEDIUM",
}


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class SmellInstance:
    """A single smell detection."""
    rule_id: str
    dd_smell_id: str
    dd_category: str
    file_path: str
    line_start: int
    line_end: int
    column_start: int
    column_end: int
    severity: str
    message: str
    code_snippet: str = ""


@dataclass
class FileStats:
    """Statistics for a single file."""
    path: str
    language: str
    lines: int  # Renamed from lines for consistency with scc pattern
    smell_count: int
    smell_density: float
    by_category: dict[str, int] = field(default_factory=dict)
    by_severity: dict[str, int] = field(default_factory=dict)
    by_smell_type: dict[str, int] = field(default_factory=dict)
    smells: list[SmellInstance] = field(default_factory=list)


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


def compute_theil(values: list[float]) -> float:
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


def compute_hoover(values: list[float]) -> float:
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


def compute_palma(values: list[float]) -> float:
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


def compute_top_share(values: list[float], top_pct: float) -> float:
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


def compute_bottom_share(values: list[float], bottom_pct: float) -> float:
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


# =============================================================================
# Distribution Dataclass (22 metrics)
# =============================================================================

@dataclass
class Distribution:
    """Statistical distribution with 22 metrics.

    Matches the scc pattern for comprehensive distribution analysis:
    - Basic: min, max, mean, median, stddev
    - Percentiles: p25, p50, p75, p90, p95, p99
    - Shape: skewness, kurtosis, cv, iqr
    - Inequality: gini, theil, hoover, palma
    - Shares: top_10_pct_share, top_20_pct_share, bottom_50_pct_share
    """
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
    cv: float = 0.0  # Coefficient of variation (stddev/mean)
    iqr: float = 0.0  # Interquartile range (p75 - p25)
    # Inequality metrics
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
            # Inequality metrics
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
    smell_count: int = 0
    categories_covered: set = field(default_factory=set)


@dataclass
class DirectoryStats:
    """Aggregated statistics for a directory (direct or recursive).

    Used to compare direct (files in this dir only) vs recursive (all files in subtree).
    """
    file_count: int = 0
    lines_code: int = 0
    smell_count: int = 0
    by_category: dict[str, int] = field(default_factory=dict)
    by_severity: dict[str, int] = field(default_factory=dict)
    by_smell_type: dict[str, int] = field(default_factory=dict)
    smell_density: float = 0.0  # smells per 100 LOC
    smell_distribution: Distribution | None = None


@dataclass
class DirectoryEntry:
    """Complete directory entry with direct vs recursive rollups.

    Matches the scc pattern for dual-tier aggregation:
    - direct: Stats for files directly in this directory
    - recursive: Stats for files in this directory + all subdirectories
    """
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
    """Full analysis result with directory rollups (v2.0 schema, aligned with TOOL_REQUIREMENTS.md)."""
    # Root-level fields per TOOL_REQUIREMENTS.md
    schema_version: str = "2.0.0"
    generated_at: str = ""
    repo_name: str = ""
    repo_path: str = ""
    # Tool-specific metadata
    run_id: str = ""
    timestamp: str = ""
    root_path: str = ""
    semgrep_version: str = ""
    rules_used: list[str] = field(default_factory=list)
    analysis_duration_ms: int = 0
    # Directory-level data (new in v2.0)
    directories: list[DirectoryEntry] = field(default_factory=list)
    # File-level data
    files: list[FileStats] = field(default_factory=list)
    smells: list[SmellInstance] = field(default_factory=list)
    # Aggregations
    by_language: dict[str, LanguageStats] = field(default_factory=dict)
    by_category: dict[str, int] = field(default_factory=dict)
    by_smell_type: dict[str, int] = field(default_factory=dict)
    by_severity: dict[str, int] = field(default_factory=dict)
    smell_distribution: Distribution | None = None


# =============================================================================
# Semgrep Runner
# =============================================================================

def get_semgrep_cmd() -> str:
    """Get the semgrep command, preferring venv version."""
    # Check for venv semgrep first
    script_dir = Path(__file__).parent.parent
    venv_semgrep = script_dir / ".venv" / "bin" / "semgrep"
    if venv_semgrep.exists():
        return str(venv_semgrep)
    # Fall back to system semgrep
    return "semgrep"


def _build_semgrep_env() -> dict[str, str]:
    """Build a semgrep environment that stays within the tool workspace."""
    script_dir = Path(__file__).parent.parent
    data_dir = script_dir / ".semgrep"
    cache_dir = data_dir / "cache"
    data_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.setdefault("SEMGREP_SEND_METRICS", "off")
    env.setdefault("SEMGREP_METRICS", "off")
    env.setdefault("SEMGREP_DISABLE_VERSION_CHECK", "1")
    env.setdefault("SEMGREP_LOG_FILE", str(data_dir / "semgrep.log"))
    env.setdefault("SEMGREP_SETTINGS_FILE", str(data_dir / "settings.yml"))
    env.setdefault("SEMGREP_VERSION_CACHE_PATH", str(cache_dir / "semgrep_version"))
    env.setdefault("XDG_CONFIG_HOME", str(data_dir))
    env.setdefault("XDG_CACHE_HOME", str(cache_dir))
    try:
        import certifi
        cert_path = certifi.where()
        env.setdefault("SSL_CERT_FILE", cert_path)
        env.setdefault("REQUESTS_CA_BUNDLE", cert_path)
        env.setdefault("CURL_CA_BUNDLE", cert_path)
    except Exception:
        pass
    return env


def get_semgrep_version() -> str:
    """Get Semgrep version string."""
    try:
        result = subprocess.run(
            [get_semgrep_cmd(), "--version"],
            capture_output=True,
            text=True,
            env=_build_semgrep_env(),
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return "unknown"
    except Exception:
        return "unknown"


def run_semgrep(
    target_path: str,
    rules: list[str] | None = None,
    baseline_commit: str | None = None,
    include_files: list[str] | None = None,
) -> dict:
    """Run Semgrep analysis on target path.

    Uses both the built-in 'auto' rules for security detection
    and custom DD rules for smell detection.

    Args:
        target_path: Path to analyze
        rules: Optional list of additional rule configs
        baseline_commit: Optional git commit hash to compare against (only shows new findings)
        include_files: Optional list of specific files to analyze (for incremental analysis)
    """
    # Find custom rules directory relative to this script
    script_dir = Path(__file__).parent.parent
    rules_dir = script_dir / "rules"

    jobs = str(max(1, min(8, os.cpu_count() or 1)))
    use_registry = os.environ.get("SEMGREP_USE_REGISTRY", "0") == "1"
    use_community = os.environ.get("SEMGREP_USE_COMMUNITY", "0") == "1"
    use_multi_lang = os.environ.get("SEMGREP_USE_MULTI_LANG", "0") == "1"
    use_elttam = os.environ.get("SEMGREP_USE_ELTTAM", "0") == "1"

    # Elttam audit rules directory (external submodule)
    elttam_rules_dir = script_dir / "external-rules" / "elttam"
    elttam_audit_rules = elttam_rules_dir / "rules-audit"

    if use_registry:
        cmd = [
            get_semgrep_cmd(),
            "--json",
            "--metrics=off",
            "--disable-version-check",
            "--jobs",
            jobs,
            "--config", "p/csharp",  # Official C# rules for patterns and best practices
            "--config", "p/security-code-scan",  # .NET security rules (OWASP SCS0xxx)
            # Additional official rulesets for comprehensive coverage
            "--config", "p/owasp-top-ten",  # OWASP Top 10 vulnerabilities
            "--config", "p/cwe-top-25",  # CWE Top 25 weaknesses
            "--config", "p/secrets",  # Hardcoded secrets detection
            "--config", "p/security-audit",  # Comprehensive security audit
            "--config", "p/default",  # Default balanced ruleset
            "--config", "p/gitlab",  # GitLab SAST rules
            # Code quality rulesets (Phase 3)
            "--config", "p/r2c-best-practices",  # Best practices: mutable defaults, anti-patterns
            "--config", "p/r2c-ci",  # CI-safe correctness rules with low false-positives
        ]
        # Multi-language rulesets for polyglot repository analysis
        if use_multi_lang:
            cmd.extend([
                "--config", "p/javascript",  # JavaScript security rules
                "--config", "p/typescript",  # TypeScript security rules
                "--config", "p/python",  # Python security rules
                "--config", "p/java",  # Java security rules
                "--config", "p/go",  # Go security rules
            ])
        cmd.extend(["--max-target-bytes", "1000000"])
    else:
        cmd = [
            get_semgrep_cmd(),
            "--json",
            "--metrics=off",
            "--disable-version-check",
            "--jobs",
            jobs,
            "--max-target-bytes",
            "1000000",
        ]

    # Add baseline commit comparison (only shows new findings since that commit)
    if baseline_commit:
        cmd.extend(["--baseline-commit", baseline_commit])

    # Add custom DD rules directory if it exists and has rules
    if rules_dir.exists() and list(rules_dir.glob("*.yaml")):
        cmd.extend(["--config", str(rules_dir)])

    # Add community rules for C# (Microsoft .NET Security Guidelines CA2300-CA5405)
    # Note: Community rules may have validation errors; they are added conditionally
    community_rules = script_dir / "community-rules" / "csharp"
    use_community_rules = use_community and community_rules.exists()

    # Add Elttam audit rules if enabled and available
    # These provide entrypoint discovery and code audit helpers
    use_elttam_rules = use_elttam and elttam_audit_rules.exists()
    if use_elttam_rules:
        cmd.extend(["--config", str(elttam_audit_rules)])

    # Add specific rulesets if provided
    if rules:
        for rule in rules:
            cmd.extend(["--config", rule])

    # Add include patterns for incremental analysis
    if include_files:
        for file_path in include_files:
            cmd.extend(["--include", file_path])

    cmd.append(target_path)

    def _run_command(command: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(command, capture_output=True, text=True, env=_build_semgrep_env())

    def _is_cert_error(stderr: str) -> bool:
        lowered = stderr.lower()
        return "ca-certs" in lowered or "trust anchors" in lowered or "x509" in lowered

    def _is_registry_error(stderr: str) -> bool:
        lowered = stderr.lower()
        return (
            "semgrep.dev" in lowered
            or "connectionerror" in lowered
            or "failed to resolve" in lowered
            or "name resolution" in lowered
            or "max retries exceeded" in lowered
        )

    def _build_local_command(include_community: bool = True, include_elttam: bool = True) -> list[str]:
        local_cmd = [
            get_semgrep_cmd(),
            "--json",
            "--metrics=off",
            "--disable-version-check",
            "--jobs",
            jobs,
            "--max-target-bytes",
            "1000000",
        ]
        if rules_dir.exists() and list(rules_dir.glob("*.yaml")):
            local_cmd.extend(["--config", str(rules_dir)])
        if include_community and use_community_rules:
            local_cmd.extend(["--config", str(community_rules)])
        if include_elttam and use_elttam_rules:
            local_cmd.extend(["--config", str(elttam_audit_rules)])
        if rules:
            for rule in rules:
                local_cmd.extend(["--config", rule])
        if include_files:
            for file_path in include_files:
                local_cmd.extend(["--include", file_path])
        local_cmd.append(target_path)
        return local_cmd

    # Try with community rules first if they exist
    if use_community_rules:
        cmd_with_community = cmd.copy()
        cmd_with_community.insert(-1, "--config")
        cmd_with_community.insert(-1, str(community_rules))

        result = _run_command(cmd_with_community)

        # If community rules cause errors (return code 7), fall back to without them
        if result.returncode not in (0, 1):
            print(f"  Community rules had errors, running without them", file=sys.stderr)
            result = _run_command(cmd)
    else:
        result = _run_command(cmd)

    if result.returncode not in (0, 1) and (_is_cert_error(result.stderr) or _is_registry_error(result.stderr)):
        print("Semgrep registry fetch failed; retrying with local rules only.", file=sys.stderr)
        local_cmd = _build_local_command(include_community=True)
        result = _run_command(local_cmd)
        if result.returncode not in (0, 1) and use_community_rules:
            print("  Community rules had errors, running without them", file=sys.stderr)
            local_cmd = _build_local_command(include_community=False)
            result = _run_command(local_cmd)

    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        if result.returncode not in (0, 1):  # 1 means findings were found
            print(f"Semgrep error: {result.stderr}", file=sys.stderr)
        return {"results": [], "errors": []}
    if result.returncode not in (0, 1) and parsed.get("errors"):
        print(f"Semgrep error: {result.stderr}", file=sys.stderr)
    return parsed


def map_rule_to_smell(rule_id: str, metadata: dict | None = None) -> tuple[str, str]:
    """Map a Semgrep rule ID to DD smell ID and category.

    Args:
        rule_id: The Semgrep rule ID (e.g., "DD-D1-EMPTY-CATCH-python")
        metadata: Optional rule metadata containing dd_smell_id and dd_category

    Returns:
        Tuple of (smell_id, category)
    """
    # Check for DD metadata in custom rules first
    if metadata:
        dd_smell_id = metadata.get("dd_smell_id")
        dd_category = metadata.get("dd_category")
        if dd_smell_id and dd_category:
            return dd_smell_id, dd_category

    rule_lower = rule_id.lower()

    # Check direct mappings (handles DD-prefixed rules)
    for pattern, smell_id in RULE_TO_SMELL_MAP.items():
        if pattern.lower() in rule_lower:
            category = SMELL_CATEGORIES.get(smell_id, "unknown")
            return smell_id, category

    # Parse DD-prefixed rule ID format: DD-XX-NAME-language
    if rule_id.startswith("DD-"):
        parts = rule_id.split("-")
        if len(parts) >= 3:
            # Extract code like D1, E2, H4, etc.
            code = parts[1]
            # Build smell_id like D1_EMPTY_CATCH
            name_parts = parts[2:-1] if len(parts) > 3 else [parts[2]]
            smell_id = f"{code}_{'_'.join(name_parts)}".upper()
            category = SMELL_CATEGORIES.get(smell_id, "unknown")
            if category != "unknown":
                return smell_id, category

    # Default mapping based on rule characteristics
    if "exception" in rule_lower or "catch" in rule_lower or "try" in rule_lower:
        return "D1_EMPTY_CATCH", "error_handling"
    if "async" in rule_lower:
        return "E2_ASYNC_VOID", "async_concurrency"
    if "sql" in rule_lower or "injection" in rule_lower:
        return "SQL_INJECTION", "security"

    return rule_id, "unknown"


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

def compute_directory_smell_stats(files: list[FileStats]) -> DirectoryStats:
    """Compute aggregated smell statistics for a set of files.

    Args:
        files: List of FileStats for files in this directory scope

    Returns:
        DirectoryStats with aggregated smell metrics
    """
    if not files:
        return DirectoryStats()

    file_count = len(files)
    lines_code = sum(f.lines for f in files)
    smell_count = sum(f.smell_count for f in files)

    # Aggregate by category
    by_category: dict[str, int] = defaultdict(int)
    by_severity: dict[str, int] = defaultdict(int)
    by_smell_type: dict[str, int] = defaultdict(int)

    for f in files:
        for cat, count in f.by_category.items():
            by_category[cat] += count
        for sev, count in f.by_severity.items():
            by_severity[sev] += count
        for smell_type, count in f.by_smell_type.items():
            by_smell_type[smell_type] += count

    # Smell density (smells per 100 LOC)
    smell_density = (smell_count / lines_code * 100) if lines_code > 0 else 0.0

    # Distribution of smell counts per file
    smell_counts = [float(f.smell_count) for f in files]
    smell_distribution = compute_distribution(smell_counts) if len(files) >= 3 else None

    return DirectoryStats(
        file_count=file_count,
        lines_code=lines_code,
        smell_count=smell_count,
        by_category=dict(by_category),
        by_severity=dict(by_severity),
        by_smell_type=dict(by_smell_type),
        smell_density=round(smell_density, 4),
        smell_distribution=smell_distribution,
    )


def build_directory_entries(files: list[FileStats], root_path: str) -> list[DirectoryEntry]:
    """Build directory tree with direct vs recursive rollups.

    Matches the scc pattern for dual-tier aggregation:
    - Groups files by parent directory
    - For each directory, computes direct (this dir only) vs recursive (subtree) stats

    Args:
        files: List of all FileStats from analysis
        root_path: Root path of the analysis

    Returns:
        List of DirectoryEntry objects sorted by path
    """
    if not files:
        return []

    # Build directory structure
    dir_files: dict[str, list[FileStats]] = defaultdict(list)  # path -> [files directly in this dir]
    all_dirs: set[str] = set()

    for f in files:
        path = Path(f.path)
        parent = str(path.parent)
        # Normalize "." to root representation
        if parent == ".":
            parent = "."
        dir_files[parent].append(f)
        all_dirs.add(parent)

        # Track all ancestor directories (for nested paths)
        for i in range(1, len(path.parts)):
            ancestor = "/".join(path.parts[:i])
            if ancestor:
                all_dirs.add(ancestor)

    all_dirs_sorted = sorted(all_dirs)

    # Compute root depth for relative depth calculation
    # "." has depth 0, otherwise count slashes
    non_root_dirs = [d for d in all_dirs_sorted if d != "."]
    root_depth = min(d.count("/") for d in non_root_dirs) if non_root_dirs else 0

    # Compute stats for each directory
    directories = []

    for dir_path in all_dirs_sorted:
        # Direct files (only in this directory)
        direct_files = dir_files.get(dir_path, [])

        # Recursive files (this directory + all subdirectories)
        recursive_files = []
        for other_path, other_files in dir_files.items():
            if dir_path == ".":
                # Root captures all files
                recursive_files.extend(other_files)
            elif other_path == dir_path or other_path.startswith(dir_path + "/"):
                recursive_files.extend(other_files)

        # Compute stats
        direct_stats = compute_directory_smell_stats(direct_files)
        recursive_stats = compute_directory_smell_stats(recursive_files)

        # Immediate subdirectories
        if dir_path == ".":
            # For root, immediate subdirs are top-level dirs (those without "/" except root)
            subdirs = [d for d in all_dirs_sorted if d != "." and "/" not in d]
        else:
            subdirs = [
                d for d in all_dirs_sorted
                if d.startswith(dir_path + "/") and d.count("/") == dir_path.count("/") + 1
            ]

        # Structural metrics
        is_leaf = len(subdirs) == 0 and len(direct_files) > 0
        child_count = len(subdirs)
        depth = 0 if dir_path == "." else dir_path.count("/") - root_depth + 1

        # Name for display
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

    # Sort by path for output (root first)
    directories.sort(key=lambda d: ("" if d.path == "." else d.path))

    return directories


# =============================================================================
# Analysis
# =============================================================================

def analyze_with_semgrep(
    target_path: str,
    rules: list[str] | None = None,
    baseline_commit: str | None = None,
) -> AnalysisResult:
    """Run full Semgrep analysis and return structured results.

    Args:
        target_path: Path to analyze
        rules: Optional list of additional rule configs
        baseline_commit: Optional git commit to compare against (only shows new findings)
    """
    start_time = datetime.now()

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
            # No changed files, return empty result
            print("  Incremental mode: no changed files to analyze")
            return AnalysisResult(
                run_id=start_time.strftime("%Y%m%d-%H%M%S"),
                timestamp=start_time.isoformat(),
                root_path=os.path.abspath(target_path),
                semgrep_version=get_semgrep_version(),
            )

    # Run Semgrep
    semgrep_output = run_semgrep(target_path, rules, baseline_commit, include_files)

    # Initialize result
    # Get repo_name from environment or derive from path
    repo_name = os.environ.get("REPO_NAME", "") or os.path.basename(os.path.abspath(target_path))
    abs_root_path = os.path.abspath(target_path)

    result = AnalysisResult(
        # Root-level fields per TOOL_REQUIREMENTS.md
        generated_at=start_time.isoformat(),
        repo_name=repo_name,
        repo_path=abs_root_path,
        # Tool-specific metadata
        run_id=start_time.strftime("%Y%m%d-%H%M%S"),
        timestamp=start_time.isoformat(),
        root_path=abs_root_path,
        semgrep_version=get_semgrep_version(),
    )

    # Process findings
    file_smells: dict[str, list[SmellInstance]] = defaultdict(list)
    rel_target = target_path.rstrip("/")

    for finding in semgrep_output.get("results", []):
        rule_id = finding.get("check_id", "unknown")
        raw_file_path = finding.get("path", "")
        # Normalize to relative path from target
        # Semgrep returns paths like 'eval-repos/synthetic/python/file.py'
        # We want 'python/file.py' (relative to target)
        if os.path.isabs(raw_file_path):
            file_path = os.path.relpath(raw_file_path, abs_root_path)
        elif raw_file_path.startswith(rel_target + "/"):
            file_path = raw_file_path[len(rel_target) + 1:]
        else:
            file_path = raw_file_path
        start = finding.get("start", {})
        end = finding.get("end", {})

        # Extract metadata from custom DD rules
        extra = finding.get("extra", {})
        metadata = extra.get("metadata", {})

        dd_smell_id, dd_category = map_rule_to_smell(rule_id, metadata)
        severity = SEVERITY_MAP.get(
            extra.get("severity", "WARNING"),
            "MEDIUM"
        )

        smell = SmellInstance(
            rule_id=rule_id,
            dd_smell_id=dd_smell_id,
            dd_category=dd_category,
            file_path=file_path,
            line_start=start.get("line", 0),
            line_end=end.get("line", 0),
            column_start=start.get("col", 0),
            column_end=end.get("col", 0),
            severity=severity,
            message=finding.get("extra", {}).get("message", ""),
            code_snippet=finding.get("extra", {}).get("lines", ""),
        )

        result.smells.append(smell)
        file_smells[file_path].append(smell)

        # Update counts
        result.by_category[dd_category] = result.by_category.get(dd_category, 0) + 1
        result.by_smell_type[dd_smell_id] = result.by_smell_type.get(dd_smell_id, 0) + 1
        result.by_severity[severity] = result.by_severity.get(severity, 0) + 1

    # Collect rules used
    result.rules_used = list(set(s.rule_id for s in result.smells))

    # Build file stats
    all_files = set()
    for root, _, files in os.walk(target_path):
        for f in files:
            if f.endswith(('.py', '.js', '.ts', '.cs', '.java', '.go', '.rs')):
                rel_path = os.path.relpath(os.path.join(root, f), target_path)
                # In incremental mode, only include changed files
                if incremental_mode and changed_files_set:
                    if rel_path not in changed_files_set:
                        continue
                all_files.add(rel_path)

    smell_counts = []
    for file_path in all_files:
        full_path = os.path.join(target_path, file_path)
        loc = count_lines(full_path)
        lang = detect_language(file_path)
        smells = file_smells.get(file_path, [])
        smell_count = len(smells)
        smell_density = smell_count / loc * 100 if loc > 0 else 0

        # Compute per-file aggregations for directory rollups
        file_by_category: dict[str, int] = defaultdict(int)
        file_by_severity: dict[str, int] = defaultdict(int)
        file_by_smell_type: dict[str, int] = defaultdict(int)
        for smell in smells:
            file_by_category[smell.dd_category] += 1
            file_by_severity[smell.severity] += 1
            file_by_smell_type[smell.dd_smell_id] += 1

        file_stat = FileStats(
            path=file_path,
            language=lang,
            lines=loc,
            smell_count=smell_count,
            smell_density=smell_density,
            by_category=dict(file_by_category),
            by_severity=dict(file_by_severity),
            by_smell_type=dict(file_by_smell_type),
            smells=smells,
        )
        result.files.append(file_stat)
        smell_counts.append(smell_count)

        # Update language stats
        if lang not in result.by_language:
            result.by_language[lang] = LanguageStats()
        result.by_language[lang].files += 1
        result.by_language[lang].lines += loc
        result.by_language[lang].smell_count += smell_count
        for smell in smells:
            result.by_language[lang].categories_covered.add(smell.dd_category)

    # Compute distribution
    if smell_counts:
        result.smell_distribution = compute_distribution([float(x) for x in smell_counts])

    # Build directory tree with direct vs recursive rollups (v2.0 feature)
    result.directories = build_directory_entries(result.files, target_path)

    # Calculate duration
    end_time = datetime.now()
    result.analysis_duration_ms = int((end_time - start_time).total_seconds() * 1000)

    return result


# =============================================================================
# Dashboard Display
# =============================================================================

def display_dashboard(result: AnalysisResult, width: int = 100):
    """Display the 18-section analysis dashboard."""

    # Section 1: Header
    print()
    print_header("SEMGREP SMELL ANALYSIS", width)

    # Section 2: Run Metadata
    print_section("1. Run Metadata", width)
    print_row("Run ID:", result.run_id, "Timestamp:", result.timestamp[:19], width)
    print_row("Target:", truncate_path_middle(result.root_path, 40),
              "Semgrep:", result.semgrep_version, width)
    print_row("Duration:", f"{result.analysis_duration_ms}ms",
              "Rules Used:", str(len(result.rules_used)), width)
    print_section_end(width)

    # Section 3: Overall Summary
    print_section("2. Overall Summary", width)
    total_files = len(result.files)
    files_with_smells = sum(1 for f in result.files if f.smell_count > 0)
    total_smells = len(result.smells)
    total_lines = sum(f.lines for f in result.files)

    print_row("Total Files:", format_number(total_files),
              "Files with Smells:", format_number(files_with_smells), width)
    print_row("Total Smells:", c(format_number(total_smells), Colors.YELLOW if total_smells > 0 else Colors.GREEN),
              "Total Lines:", format_number(total_lines), width)
    smell_rate = files_with_smells / total_files * 100 if total_files > 0 else 0
    density = total_smells / total_lines * 1000 if total_lines > 0 else 0
    print_row("Smell Rate:", format_percent(smell_rate),
              "Smells/KLOC:", f"{density:.2f}", width)
    print_section_end(width)

    # Section 4: Smells by Category
    print_section("3. Smells by DD Category", width)
    categories = [
        "error_handling", "async_concurrency", "resource_management",
        "nullability", "api_design", "dead_code", "refactoring",
        "dependency", "security", "size_complexity",
        # Code quality categories (Phase 3)
        "correctness", "best_practice", "performance",
        "unknown"
    ]
    for cat in categories:
        count = result.by_category.get(cat, 0)
        if count > 0:
            color = Colors.RED if count > 5 else (Colors.YELLOW if count > 0 else Colors.GREEN)
            print_row(f"  {cat}:", c(str(count), color), "", "", width)
    if not any(result.by_category.get(cat, 0) > 0 for cat in categories):
        print_row("  No smells detected", c("CLEAN", Colors.GREEN), "", "", width)
    print_section_end(width)

    # Section 5: Smells by Severity
    print_section("4. Smells by Severity", width)
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        count = result.by_severity.get(sev, 0)
        if count > 0:
            color = Colors.RED if sev == "CRITICAL" else (
                Colors.YELLOW if sev == "HIGH" else Colors.CYAN
            )
            print_row(f"  {sev}:", c(str(count), color), "", "", width)
    print_section_end(width)

    # Section 6: Top Smell Types
    print_section("5. Top Smell Types", width)
    sorted_types = sorted(result.by_smell_type.items(), key=lambda x: x[1], reverse=True)[:5]
    for smell_type, count in sorted_types:
        print_row(f"  {smell_type}:", str(count), "", "", width)
    if not sorted_types:
        print_row("  No smells detected", "", "", "", width)
    print_section_end(width)

    # Section 7: Language Coverage
    print_section("6. Language Coverage", width)
    for lang, stats in sorted(result.by_language.items(), key=lambda x: x[1].files, reverse=True):
        cats_str = ", ".join(sorted(stats.categories_covered)[:3]) if stats.categories_covered else "none"
        print_row(f"  {lang}:",
                  f"{stats.files} files, {stats.smell_count} smells",
                  "Categories:", cats_str, width)
    print_section_end(width)

    # Section 8: Files with Most Smells
    print_section("7. Files with Most Smells (Top 10)", width)
    sorted_files = sorted(result.files, key=lambda x: x.smell_count, reverse=True)[:10]
    for f in sorted_files:
        if f.smell_count > 0:
            color = Colors.RED if f.smell_count > 5 else (Colors.YELLOW if f.smell_count > 2 else Colors.WHITE)
            print_row(f"  {truncate_path_middle(f.path, 50)}:",
                      c(f"{f.smell_count} smells", color),
                      "Density:", f"{f.smell_density:.1f}/100 LOC", width)
    if not any(f.smell_count > 0 for f in sorted_files):
        print_row("  All files are clean!", "", "", "", width)
    print_section_end(width)

    # Section 9: Clean Files
    print_section("8. Clean Files Summary", width)
    clean_files = [f for f in result.files if f.smell_count == 0]
    print_row("Clean Files:", c(format_number(len(clean_files)), Colors.GREEN),
              "Percentage:", c(format_percent(len(clean_files) / total_files * 100 if total_files > 0 else 0), Colors.GREEN), width)
    print_section_end(width)

    # Section 10: Distribution Statistics
    if result.smell_distribution and result.smell_distribution.count > 0:
        print_section("9. Smell Distribution Statistics", width)
        dist = result.smell_distribution
        print_row("Min:", str(int(dist.min)), "Max:", str(int(dist.max)), width)
        print_row("Mean:", f"{dist.mean:.2f}", "Median:", f"{dist.median:.2f}", width)
        print_row("Std Dev:", f"{dist.stddev:.2f}", "P90:", f"{dist.p90:.1f}", width)
        print_section_end(width)

    # Section 11: Sample Findings
    print_section("10. Sample Findings (First 5)", width)
    for smell in result.smells[:5]:
        location = f"{truncate_path_middle(smell.file_path, 30)}:{smell.line_start}"
        print_row(f"  {smell.dd_smell_id}:", location, "Severity:", smell.severity, width)
    if not result.smells:
        print_row("  No findings to display", "", "", "", width)
    print_section_end(width)

    # Section 12: Directory Tree View
    if result.directories:
        print_section("11. Directory Tree", width)
        for d in result.directories[:10]:
            indent = "  " * d.depth
            name = d.name if d.name != "(root)" else "(root)"
            smells_str = f"{d.recursive.smell_count} smells" if d.recursive.smell_count > 0 else "clean"
            color = Colors.RED if d.recursive.smell_count > 10 else (
                Colors.YELLOW if d.recursive.smell_count > 0 else Colors.GREEN
            )
            print_row(f"  {indent}{name}/:", c(smells_str, color),
                      "Files:", str(d.recursive.file_count), width)
        print_section_end(width)

    # Section 13: Top Directories by Recursive Smells
    if result.directories:
        print_section("12. Top Directories (Recursive Smells)", width)
        top_dirs = sorted(result.directories, key=lambda x: x.recursive.smell_count, reverse=True)[:5]
        for d in top_dirs:
            if d.recursive.smell_count > 0:
                density = f"{d.recursive.smell_density:.2f}/KLOC"
                print_row(f"  {truncate_path_middle(d.path, 35)}:",
                          f"{d.recursive.smell_count} smells ({d.recursive.file_count} files)",
                          "Density:", density, width)
        print_section_end(width)

    # Section 14: Smell Concentration Analysis (Gini, Palma)
    if result.smell_distribution and result.smell_distribution.count > 0:
        print_section("13. Smell Concentration (Inequality)", width)
        dist = result.smell_distribution
        gini_color = Colors.RED if dist.gini > 0.7 else (Colors.YELLOW if dist.gini > 0.5 else Colors.GREEN)
        print_row("Gini:", c(f"{dist.gini:.3f}", gini_color),
                  "Theil:", f"{dist.theil:.3f}", width)
        print_row("Hoover:", f"{dist.hoover:.3f}",
                  "Palma:", f"{dist.palma:.2f}x", width)
        print_row("Top 10% Share:", f"{dist.top_10_pct_share:.1%}",
                  "Bottom 50% Share:", f"{dist.bottom_50_pct_share:.1%}", width)
        print_section_end(width)

    # Section 15: Per-Language Distribution Analysis
    if len(result.by_language) > 0:
        print_section("14. Per-Language Analysis", width)
        for lang, stats in sorted(result.by_language.items(), key=lambda x: x[1].smell_count, reverse=True)[:3]:
            lang_density = stats.smell_count / stats.files if stats.files > 0 else 0
            top_cats = ", ".join(sorted(stats.categories_covered)[:2]) if stats.categories_covered else "none"
            print_row(f"  {lang}:", f"{stats.smell_count} smells / {stats.files} files",
                      "Top:", top_cats, width)
        print_section_end(width)

    # Section 16: Enhanced Distribution Statistics (22 metrics summary)
    if result.smell_distribution and result.smell_distribution.count > 0:
        print_section("15. Distribution Shape", width)
        dist = result.smell_distribution
        skew_label = "right-skewed" if dist.skewness > 1 else ("symmetric" if abs(dist.skewness) < 0.5 else "left-skewed")
        kurt_label = "heavy-tailed" if dist.kurtosis > 2 else ("normal" if abs(dist.kurtosis) < 1 else "light-tailed")
        print_row("Skewness:", f"{dist.skewness:.2f} ({skew_label})",
                  "Kurtosis:", f"{dist.kurtosis:.2f} ({kurt_label})", width)
        print_row("IQR:", f"{dist.iqr:.1f}",
                  "CV:", f"{dist.cv:.2f}", width)
        print_section_end(width)

    # Section 17: Key Findings Summary
    print_section("16. Key Findings", width)
    findings = []
    if total_smells == 0:
        findings.append(("No smells detected", Colors.GREEN))
    else:
        # Critical concentration
        if result.by_severity.get("CRITICAL", 0) > 0:
            findings.append((f"{result.by_severity['CRITICAL']} CRITICAL severity issues", Colors.RED))
        # High Gini indicates concentration
        if result.smell_distribution and result.smell_distribution.gini > 0.6:
            findings.append(("Smells concentrated in few files (Gini > 0.6)", Colors.YELLOW))
        # Categories affected
        active_cats = len([c for c in result.by_category.values() if c > 0])
        if active_cats >= 3:
            findings.append((f"Issues across {active_cats} categories", Colors.YELLOW))
        # Top file concentration
        top_file = max(result.files, key=lambda x: x.smell_count, default=None)
        if top_file and top_file.smell_count > 5:
            findings.append((f"Hotspot: {top_file.path} ({top_file.smell_count} smells)", Colors.RED))

    for finding, color in findings[:5]:
        print_row("  •", c(finding, color), "", "", width)
    if not findings:
        print_row("  •", "Analysis complete, no significant findings", "", "", width)
    print_section_end(width)

    # Section 18: Recommendations
    print_section("17. Recommendations", width)
    recommendations = []
    if result.by_severity.get("CRITICAL", 0) > 0:
        recommendations.append("Priority: Address CRITICAL severity issues first")
    if result.by_category.get("error_handling", 0) > 3:
        recommendations.append("Fix error handling: empty catch blocks, catch-all patterns")
    if result.by_category.get("async_concurrency", 0) > 0:
        recommendations.append("Review async patterns: avoid .Result/.Wait(), async void")
    if result.by_category.get("resource_management", 0) > 0:
        recommendations.append("Add using/Dispose: ensure proper resource cleanup")
    if result.by_category.get("security", 0) > 0:
        recommendations.append("Security audit: SQL injection, hardcoded credentials")
    # Code quality recommendations (Phase 3)
    if result.by_category.get("correctness", 0) > 0:
        recommendations.append("Fix correctness issues: logic errors, null dereferences")
    if result.by_category.get("best_practice", 0) > 0:
        recommendations.append("Review best practices: anti-patterns, deprecated APIs")
    if result.by_category.get("performance", 0) > 0:
        recommendations.append("Address performance: inefficient patterns, complexity")
    if result.smell_distribution and result.smell_distribution.gini > 0.7:
        recommendations.append("Refactor hotspots: smells highly concentrated")

    for rec in recommendations[:4]:
        print_row("  →", rec, "", "", width)
    if not recommendations:
        print_row("  →", "Keep up the good work!", "", "", width)
    print_section_end(width)

    # Final summary
    print()
    if total_smells == 0:
        print(c("  ANALYSIS COMPLETE: No smells detected!", Colors.GREEN, Colors.BOLD))
    else:
        print(c(f"  ANALYSIS COMPLETE: {total_smells} smells found across {files_with_smells} files",
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
        # Basic stats
        "min": d.min,
        "max": d.max,
        "mean": round(d.mean, 4),
        "median": round(d.median, 4),
        "stddev": round(d.stddev, 4),
        # Percentiles
        "p25": d.p25,
        "p50": round(d.p50, 4),
        "p75": d.p75,
        "p90": round(d.p90, 4),
        "p95": round(d.p95, 4),
        "p99": round(d.p99, 4),
        # Shape
        "skewness": round(d.skewness, 4),
        "kurtosis": round(d.kurtosis, 4),
        "cv": round(d.cv, 4),
        "iqr": round(d.iqr, 4),
        # Inequality
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
        "smell_count": stats.smell_count,
        "by_category": stats.by_category,
        "by_severity": stats.by_severity,
        "by_smell_type": stats.by_smell_type,
        "smell_density": round(stats.smell_density, 4),
        "smell_distribution": distribution_to_dict(stats.smell_distribution),
    }


def result_to_dict(result: AnalysisResult) -> dict:
    """Convert AnalysisResult to JSON-serializable dict (v2.0 schema).

    Creates the standard output structure per TOOL_REQUIREMENTS.md:
    {
        "schema_version": "2.0.0",
        "generated_at": "...",
        "repo_name": "...",
        "repo_path": "...",
        "results": {
            // All tool-specific data
        }
    }
    """
    # Serialize files
    files = []
    for f in result.files:
        smells = []
        for s in f.smells:
            smells.append({
                "rule_id": s.rule_id,
                "dd_smell_id": s.dd_smell_id,
                "dd_category": s.dd_category,
                "line_start": s.line_start,
                "line_end": s.line_end,
                "column_start": s.column_start,
                "column_end": s.column_end,
                "severity": s.severity,
                "message": s.message,
                "code_snippet": s.code_snippet,
            })
        files.append({
            "path": f.path,
            "language": f.language,
            "lines": f.lines,
            "smell_count": f.smell_count,
            "smell_density": round(f.smell_density, 4),
            "by_category": f.by_category,
            "by_severity": f.by_severity,
            "by_smell_type": f.by_smell_type,
            "smells": smells,
        })

    # Serialize directories (v2.0 feature)
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
            "smell_count": stats.smell_count,
            "categories_covered": list(stats.categories_covered),
        }

    return {
        # Root-level fields per TOOL_REQUIREMENTS.md
        "schema_version": result.schema_version,
        "generated_at": result.generated_at,
        "repo_name": result.repo_name,
        "repo_path": result.repo_path,
        # All tool-specific data in results wrapper
        "results": {
            "tool": "semgrep",
            "tool_version": result.semgrep_version,
            "metadata": {
                "schema_version": result.schema_version,
                "run_id": result.run_id,
                "timestamp": result.timestamp,
                "root_path": result.root_path,
                "semgrep_version": result.semgrep_version,
                "rules_used": result.rules_used,
                "analysis_duration_ms": result.analysis_duration_ms,
            },
            "summary": {
                "total_files": len(result.files),
                "total_directories": len(result.directories),
                "files_with_smells": sum(1 for f in result.files if f.smell_count > 0),
                "total_smells": len(result.smells),
                "total_lines": sum(f.lines for f in result.files),
                "smells_by_category": result.by_category,
                "smells_by_type": result.by_smell_type,
                "smells_by_severity": result.by_severity,
            },
            "directories": directories,
            "files": files,
            "by_language": by_language,
            "statistics": {
                "smell_distribution": distribution_to_dict(result.smell_distribution),
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
        description="Analyze code smells using Semgrep"
    )
    parser.add_argument(
        "target",
        help="Target directory to analyze",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file path",
        default="output/smell_analysis.json",
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
        "--rules", "-r",
        nargs="+",
        help="Additional Semgrep rule configs to use",
    )
    parser.add_argument(
        "--baseline-commit",
        type=str,
        default=None,
        help="Git commit hash to compare against (only shows new findings since that commit)",
    )

    args = parser.parse_args()

    if args.no_color:
        set_color_enabled(False)

    # Validate target
    if not os.path.exists(args.target):
        print(f"Error: Target path does not exist: {args.target}", file=sys.stderr)
        sys.exit(1)

    # Run analysis
    result = analyze_with_semgrep(args.target, args.rules, args.baseline_commit)

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
