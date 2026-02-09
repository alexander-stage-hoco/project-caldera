"""Re-export path normalization utilities from common module.

This module provides a clean `shared.path_utils` interface while
maintaining backward compatibility with existing `common.path_normalization`
imports.

Usage:
    from shared.path_utils import normalize_file_path, is_repo_relative_path
"""

from __future__ import annotations

from common.path_normalization import (
    normalize_file_path,
    normalize_dir_path,
    is_repo_relative_path,
    validate_paths_consistent,
    detect_path_root_pattern,
)

__all__ = [
    "normalize_file_path",
    "normalize_dir_path",
    "is_repo_relative_path",
    "validate_paths_consistent",
    "detect_path_root_pattern",
]
