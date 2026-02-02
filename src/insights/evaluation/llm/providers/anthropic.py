"""
Anthropic API provider for direct API access.
"""

import os
from typing import Any

from . import LLMProvider, LLMResponse


class AnthropicAPIProvider(LLMProvider):
    """Uses Anthropic API directly."""

    SUPPORTED_MODELS = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-latest",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ]

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-latest",
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        """
        Initialize Anthropic API provider.

        Args:
            model: Model to use.
            api_key: Anthropic API key (or ANTHROPIC_API_KEY env var).
            base_url: Optional custom base URL.
        """
        self._model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.base_url = base_url
        self._client: Any = None

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def default_model(self) -> str:
        return "claude-3-5-sonnet-latest"

    def supports_model(self, model: str) -> bool:
        return model in self.SUPPORTED_MODELS or model.startswith("claude-")

    def _get_client(self) -> Any:
        """Lazy-initialize the Anthropic client."""
        if self._client is None:
            try:
                import anthropic
            except ImportError:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")

            if not self.api_key:
                raise ValueError("Anthropic API key not provided. Set ANTHROPIC_API_KEY env var or pass api_key.")

            kwargs: dict[str, Any] = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url

            self._client = anthropic.Anthropic(**kwargs)

        return self._client

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send a completion request to Anthropic API."""
        client = self._get_client()
        effective_model = model or self._model

        kwargs: dict[str, Any] = {
            "model": effective_model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system:
            kwargs["system"] = system

        if temperature > 0:
            kwargs["temperature"] = temperature

        response = client.messages.create(**kwargs)

        content = ""
        if response.content:
            content = response.content[0].text if hasattr(response.content[0], "text") else str(response.content[0])

        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            }

        return LLMResponse(
            content=content,
            model=effective_model,
            usage=usage,
            metadata={
                "provider": "anthropic",
                "stop_reason": response.stop_reason,
            },
        )
