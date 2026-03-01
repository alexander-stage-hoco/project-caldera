"""Prompt size estimation and truncation guard rails.

Prevents oversized prompts from exceeding context limits, wasting tokens,
or causing silent quality degradation when analyzing large repositories.
"""

from __future__ import annotations

import warnings

DEFAULT_MAX_PROMPT_CHARS = 100_000  # ~28k tokens, safe for Claude's 200k context
CHARS_PER_TOKEN = 3.5  # conservative estimate for JSON-heavy text


def estimate_tokens(text: str) -> int:
    """Estimate token count from character length.

    Uses a conservative chars-per-token ratio tuned for JSON-heavy text
    (which tokenizes less efficiently than natural language).

    Args:
        text: The text to estimate tokens for.

    Returns:
        Estimated token count.
    """
    return int(len(text) / CHARS_PER_TOKEN)


def check_prompt_size(
    prompt: str,
    max_chars: int = DEFAULT_MAX_PROMPT_CHARS,
) -> tuple[str, bool]:
    """Check prompt size and truncate if it exceeds the limit.

    Args:
        prompt: The prompt text to check.
        max_chars: Maximum allowed character count.

    Returns:
        Tuple of (possibly truncated prompt, was_truncated).
        If truncated, a marker is appended indicating the truncation.
    """
    if len(prompt) <= max_chars:
        return prompt, False

    truncated = prompt[:max_chars]
    truncated += f"\n\n[INPUT TRUNCATED — exceeded {max_chars} chars]"
    return truncated, True


def guard_prompt(
    prompt: str,
    max_chars: int | None = None,
    context: str = "",
) -> str:
    """Check prompt size, truncate if needed, and emit a warning.

    Convenience wrapper around ``check_prompt_size`` that also emits
    a ``warnings.warn`` when truncation occurs.

    Args:
        prompt: The prompt text to guard.
        max_chars: Maximum allowed character count (None = default).
        context: Optional context string for the warning message.

    Returns:
        The (possibly truncated) prompt.
    """
    effective_max = max_chars if max_chars is not None else DEFAULT_MAX_PROMPT_CHARS
    result, was_truncated = check_prompt_size(prompt, effective_max)
    if was_truncated:
        label = f" [{context}]" if context else ""
        warnings.warn(
            f"Prompt truncated{label}: {len(prompt)} → {effective_max} chars "
            f"(~{estimate_tokens(prompt)} → ~{estimate_tokens(result)} tokens)",
            stacklevel=3,
        )
    return result
