"""Shared severity mapping utilities for Project Caldera tools."""

from __future__ import annotations

from .mapper import (
    SeverityLevel,
    SEVERITY_ORDER,
    PRODUCTION_PATH_PATTERNS,
    normalize_severity,
    compare_severity,
    is_valid_severity,
    escalate_for_production_path,
)

__all__ = [
    "SeverityLevel",
    "SEVERITY_ORDER",
    "PRODUCTION_PATH_PATTERNS",
    "normalize_severity",
    "compare_severity",
    "is_valid_severity",
    "escalate_for_production_path",
]
