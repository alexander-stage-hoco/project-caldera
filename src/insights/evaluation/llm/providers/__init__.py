"""
LLM provider abstraction for evaluation judges.

Supports multiple LLM backends:
- Claude Code Headless (default, Opus 4.5)
- OpenAI API (gpt-4o, gpt-4-turbo)
- Codex Headless
- Anthropic API direct
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    content: str
    model: str
    usage: dict[str, int] | None = None
    metadata: dict[str, Any] | None = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging/identification."""
        ...

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model to use."""
        ...

    @abstractmethod
    def complete(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """
        Send a completion request.

        Args:
            prompt: The user prompt.
            system: Optional system prompt.
            model: Optional model override.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            LLMResponse with the completion.
        """
        ...

    def supports_model(self, model: str) -> bool:
        """Check if this provider supports a given model."""
        return True  # Default: assume support


def get_provider(name: str, **kwargs: Any) -> LLMProvider:
    """
    Get an LLM provider by name.

    Args:
        name: Provider name ('claude_code', 'openai', 'codex', 'anthropic').
        **kwargs: Provider-specific configuration.

    Returns:
        Configured LLMProvider instance.
    """
    from .claude_code import ClaudeCodeHeadlessProvider
    from .openai import OpenAIProvider
    from .codex import CodexHeadlessProvider
    from .anthropic import AnthropicAPIProvider

    providers = {
        "claude_code": ClaudeCodeHeadlessProvider,
        "openai": OpenAIProvider,
        "codex": CodexHeadlessProvider,
        "anthropic": AnthropicAPIProvider,
    }

    if name not in providers:
        raise ValueError(f"Unknown provider: {name}. Available: {list(providers.keys())}")

    return providers[name](**kwargs)


__all__ = [
    "LLMProvider",
    "LLMResponse",
    "get_provider",
]


# Re-export ObservableProvider for convenience
def get_observable_provider(name: str, trace_id: str | None = None, **kwargs: Any) -> "LLMProvider":
    """
    Get an observable LLM provider by name.

    Combines get_provider with ObservableProvider wrapping.

    Args:
        name: Provider name ('claude_code', 'openai', 'codex', 'anthropic').
        trace_id: Optional trace ID for observability.
        **kwargs: Provider-specific configuration.

    Returns:
        ObservableProvider wrapping the requested provider.
    """
    from ..observability import ObservableProvider

    provider = get_provider(name, **kwargs)
    return ObservableProvider(provider, trace_id=trace_id)
