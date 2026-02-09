"""Shared utilities for Project Caldera tools.

This package provides common infrastructure for all Project Caldera
analysis tools, including:

- LLM invocation (SDK and CLI)
- Severity mapping and normalization
- Path utilities
- Evaluation framework (BaseJudge, observability)

Example usage:
    from shared.llm import LLMClient
    from shared.severity import normalize_severity, SeverityLevel
    from shared.path_utils import normalize_file_path
    from shared.evaluation import BaseJudge, JudgeResult
"""

from __future__ import annotations

# LLM client exports
from .llm import (
    LLMClient,
    MODEL_MAP,
    CLI_MODEL_MAP,
    HAS_ANTHROPIC_SDK,
)

# Severity mapping exports
from .severity import (
    SeverityLevel,
    SEVERITY_ORDER,
    PRODUCTION_PATH_PATTERNS,
    normalize_severity,
    compare_severity,
    is_valid_severity,
    escalate_for_production_path,
)

# Path utilities exports
from .path_utils import (
    normalize_file_path,
    normalize_dir_path,
    is_repo_relative_path,
    validate_paths_consistent,
    detect_path_root_pattern,
)

__all__ = [
    # LLM
    "LLMClient",
    "MODEL_MAP",
    "CLI_MODEL_MAP",
    "HAS_ANTHROPIC_SDK",
    # Severity
    "SeverityLevel",
    "SEVERITY_ORDER",
    "PRODUCTION_PATH_PATTERNS",
    "normalize_severity",
    "compare_severity",
    "is_valid_severity",
    "escalate_for_production_path",
    # Path utilities
    "normalize_file_path",
    "normalize_dir_path",
    "is_repo_relative_path",
    "validate_paths_consistent",
    "detect_path_root_pattern",
]
