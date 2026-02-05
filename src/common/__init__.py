"""Shared utilities."""

from .cli_parser import (
    CommonArgs,
    CommitResolutionConfig,
    ValidationError,
    add_common_args,
    validate_common_args,
    validate_common_args_raising,
)
from .ecosystem_detector import (
    ECOSYSTEM_PATTERNS,
    DependencyFile,
    DependencyFileType,
    EcosystemDetectionResult,
    EcosystemPattern,
    EcosystemStatus,
    classify_dependency_file,
    detect_ecosystems,
    detect_ecosystems_from_directory,
    format_ecosystem_completeness,
    get_ecosystem_summary,
)
from .envelope_formatter import (
    create_envelope,
    get_current_timestamp,
)
from .git_utilities import (
    FALLBACK_COMMIT,
    commit_exists,
    fallback_commit_hash,
    git_head,
    git_run,
    is_fallback_commit,
    resolve_commit,
)

__all__ = [
    # CLI parser
    "CommonArgs",
    "CommitResolutionConfig",
    "ValidationError",
    "add_common_args",
    "validate_common_args",
    "validate_common_args_raising",
    # Ecosystem detector
    "ECOSYSTEM_PATTERNS",
    "DependencyFile",
    "DependencyFileType",
    "EcosystemDetectionResult",
    "EcosystemPattern",
    "EcosystemStatus",
    "classify_dependency_file",
    "detect_ecosystems",
    "detect_ecosystems_from_directory",
    "format_ecosystem_completeness",
    "get_ecosystem_summary",
    # Envelope formatter
    "create_envelope",
    "get_current_timestamp",
    # Git utilities
    "FALLBACK_COMMIT",
    "commit_exists",
    "fallback_commit_hash",
    "git_head",
    "git_run",
    "is_fallback_commit",
    "resolve_commit",
]
