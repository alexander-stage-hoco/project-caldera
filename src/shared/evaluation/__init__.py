"""Shared evaluation utilities for Project Caldera tools."""

from .base_judge import BaseJudge, JudgeResult
from .observability_check import (
    ObservabilityDisabledError,
    is_observability_enabled,
    require_observability,
    verify_interactions_logged,
    get_observability_summary,
    get_recent_interactions,
)
from .orchestrator import (
    DimensionResult,
    ProgrammaticInput,
    EvaluationResult,
    LLMEvaluatorBase,
)

__all__ = [
    "BaseJudge",
    "JudgeResult",
    # Orchestrator components
    "DimensionResult",
    "ProgrammaticInput",
    "EvaluationResult",
    "LLMEvaluatorBase",
    # Observability enforcement
    "ObservabilityDisabledError",
    "is_observability_enabled",
    "require_observability",
    "verify_interactions_logged",
    "get_observability_summary",
    "get_recent_interactions",
]

# Re-export HAS_OBSERVABILITY flag for tools to check
try:
    from .base_judge import HAS_OBSERVABILITY
    __all__.append("HAS_OBSERVABILITY")
except ImportError:
    HAS_OBSERVABILITY = False
