"""
LLM Observability Module.

DEPRECATED: Import from shared.observability instead.
This module re-exports from shared.observability for backwards compatibility.

Provides comprehensive logging and tracing for LLM judge interactions.

Usage:
    # Preferred (new):
    from shared.observability import (
        get_llm_logger,
        LLMInteraction,
        FileStore,
    )

    # Deprecated (backwards compatible):
    from insights.evaluation.llm.observability import (
        get_llm_logger,
        LLMInteraction,
        ObservableProvider,
        FileStore,
    )
"""

import warnings

# Re-export everything from shared.observability
from shared.observability import (
    LLMInteraction,
    EvaluationSpan,
    ObservabilityConfig,
    get_config,
    set_config,
    reset_config,
    LLMLogger,
    get_llm_logger,
    reset_llm_logger,
    FileStore,
)

# Keep ObservableProvider here since it depends on insights.evaluation.llm.providers
from .observable_provider import ObservableProvider

__all__ = [
    # Schemas
    "LLMInteraction",
    "EvaluationSpan",
    # Config
    "ObservabilityConfig",
    "get_config",
    "set_config",
    "reset_config",
    # Logger
    "LLMLogger",
    "get_llm_logger",
    "reset_llm_logger",
    # Storage
    "FileStore",
    # Provider wrapper (insights-specific)
    "ObservableProvider",
]


def __getattr__(name: str):
    """Emit deprecation warning when this module is accessed."""
    warnings.warn(
        f"Importing '{name}' from 'insights.evaluation.llm.observability' is deprecated. "
        f"Import from 'shared.observability' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    raise AttributeError(f"module 'insights.evaluation.llm.observability' has no attribute '{name}'")
