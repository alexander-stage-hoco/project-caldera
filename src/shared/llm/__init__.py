"""Shared LLM invocation utilities for Project Caldera tools."""

from __future__ import annotations

from .client import (
    LLMClient,
    MODEL_MAP,
    CLI_MODEL_MAP,
    HAS_ANTHROPIC_SDK,
    validate_claude_cli,
)
from .prompt_guard import (
    DEFAULT_MAX_PROMPT_CHARS,
    check_prompt_size,
    estimate_tokens,
    guard_prompt,
)
from .tiered_detail import (
    DEFAULT_MAX_DATA_CHARS,
    fit_to_budget,
)

__all__ = [
    "LLMClient",
    "MODEL_MAP",
    "CLI_MODEL_MAP",
    "HAS_ANTHROPIC_SDK",
    "validate_claude_cli",
    "DEFAULT_MAX_PROMPT_CHARS",
    "check_prompt_size",
    "estimate_tokens",
    "guard_prompt",
    "DEFAULT_MAX_DATA_CHARS",
    "fit_to_budget",
]
