"""
LLM Observability Module.

Provides comprehensive logging and tracing for LLM judge interactions.

Usage:
    from shared.observability import (
        get_llm_logger,
        LLMInteraction,
        FileStore,
    )

    # Get the global logger
    logger = get_llm_logger()

    # Query logged interactions
    store = FileStore()
    interactions = store.query_by_trace("my-trace")
"""

from .schemas import LLMInteraction, EvaluationSpan
from .config import ObservabilityConfig, get_config, set_config, reset_config
from .logger import LLMLogger, get_llm_logger, reset_llm_logger
from .storage import FileStore

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
]
