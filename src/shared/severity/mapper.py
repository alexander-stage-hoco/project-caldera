"""Severity mapping and normalization utilities.

This module provides standardized severity handling across all Project Caldera
analysis tools. It consolidates severity mapping patterns from gitleaks,
roslyn-analyzers, semgrep, trivy, and other tools.
"""

from __future__ import annotations

from enum import Enum


class SeverityLevel(str, Enum):
    """Standard severity levels used across Project Caldera.

    Values are uppercase strings for consistency with common security
    tool conventions (SARIF, CVSS, etc.).
    """

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:
        return self.value


# Severity ordering for comparison (higher index = more severe)
SEVERITY_ORDER: dict[str, int] = {
    "UNKNOWN": 0,
    "INFO": 1,
    "LOW": 2,
    "MEDIUM": 3,
    "HIGH": 4,
    "CRITICAL": 5,
}

# Reverse mapping for escalation
_SEVERITY_BY_ORDER: dict[int, str] = {v: k for k, v in SEVERITY_ORDER.items()}

# File path patterns that indicate production context (elevated severity)
PRODUCTION_PATH_PATTERNS: list[str] = [
    ".env.production",
    ".env.prod",
    "prod/",
    "production/",
    ".aws/credentials",
    "config/prod",
    "deploy/prod",
    "k8s/prod",
    "kubernetes/prod",
    "terraform/prod",
    "infra/prod",
]

# Common severity aliases from various tools
_SEVERITY_ALIASES: dict[str, str] = {
    # Lowercase versions
    "critical": "CRITICAL",
    "high": "HIGH",
    "medium": "MEDIUM",
    "low": "LOW",
    "info": "INFO",
    "informational": "INFO",
    "information": "INFO",
    "unknown": "UNKNOWN",
    "none": "INFO",
    # CVSS-style
    "error": "HIGH",
    "warning": "MEDIUM",
    "note": "LOW",
    "hint": "INFO",
    # Numeric strings
    "1": "LOW",
    "2": "MEDIUM",
    "3": "HIGH",
    "4": "CRITICAL",
    # SonarQube-style
    "blocker": "CRITICAL",
    "major": "HIGH",
    "minor": "MEDIUM",
    # Trivy-style
    "negligible": "INFO",
}


def normalize_severity(raw: str | None, default: str = "MEDIUM") -> str:
    """Normalize a raw severity string to a standard SeverityLevel value.

    Handles various formats from different tools:
    - Lowercase/mixed case: "high" -> "HIGH"
    - Aliases: "warning" -> "MEDIUM", "blocker" -> "CRITICAL"
    - Already normalized: "HIGH" -> "HIGH"

    Args:
        raw: Raw severity string from a tool (may be None or empty)
        default: Default severity if raw is None/empty/unrecognized

    Returns:
        Normalized severity string (one of SeverityLevel values)

    Example:
        >>> normalize_severity("high")
        "HIGH"
        >>> normalize_severity("warning")
        "MEDIUM"
        >>> normalize_severity(None)
        "MEDIUM"
    """
    if not raw:
        return default

    # Try direct match (already uppercase)
    upper = raw.upper()
    if upper in SEVERITY_ORDER:
        return upper

    # Try alias lookup (case-insensitive)
    lower = raw.lower().strip()
    if lower in _SEVERITY_ALIASES:
        return _SEVERITY_ALIASES[lower]

    # Return default for unrecognized values
    return default


def is_valid_severity(value: str | None) -> bool:
    """Check if a value is a valid severity level.

    Args:
        value: Value to check

    Returns:
        True if value is a recognized severity level

    Example:
        >>> is_valid_severity("HIGH")
        True
        >>> is_valid_severity("INVALID")
        False
    """
    if not value:
        return False
    return value.upper() in SEVERITY_ORDER


def compare_severity(a: str, b: str) -> int:
    """Compare two severity levels.

    Args:
        a: First severity level
        b: Second severity level

    Returns:
        -1 if a < b, 0 if a == b, 1 if a > b

    Example:
        >>> compare_severity("HIGH", "LOW")
        1
        >>> compare_severity("MEDIUM", "MEDIUM")
        0
        >>> compare_severity("INFO", "CRITICAL")
        -1
    """
    order_a = SEVERITY_ORDER.get(normalize_severity(a), 0)
    order_b = SEVERITY_ORDER.get(normalize_severity(b), 0)

    if order_a < order_b:
        return -1
    elif order_a > order_b:
        return 1
    return 0


def escalate_for_production_path(
    base_severity: str,
    file_path: str,
    patterns: list[str] | None = None,
) -> str:
    """Escalate severity if the file path indicates a production context.

    Production paths (credentials, prod configs, etc.) warrant higher
    severity because issues in these files have greater blast radius.

    Args:
        base_severity: The initial severity level
        file_path: Path to check for production patterns
        patterns: Optional custom patterns (defaults to PRODUCTION_PATH_PATTERNS)

    Returns:
        Escalated severity (one level higher) or original severity

    Example:
        >>> escalate_for_production_path("MEDIUM", ".env.production")
        "HIGH"
        >>> escalate_for_production_path("HIGH", "config/prod/db.yaml")
        "CRITICAL"
        >>> escalate_for_production_path("MEDIUM", "src/utils.py")
        "MEDIUM"
    """
    if not file_path:
        return base_severity

    check_patterns = patterns if patterns is not None else PRODUCTION_PATH_PATTERNS
    file_path_lower = file_path.lower()

    # Check if path matches any production pattern
    is_production = any(pattern in file_path_lower for pattern in check_patterns)

    if not is_production:
        return base_severity

    # Escalate by one level (capped at CRITICAL)
    normalized = normalize_severity(base_severity)
    current_order = SEVERITY_ORDER.get(normalized, 3)  # Default to MEDIUM level
    escalated_order = min(current_order + 1, SEVERITY_ORDER["CRITICAL"])

    return _SEVERITY_BY_ORDER.get(escalated_order, normalized)
