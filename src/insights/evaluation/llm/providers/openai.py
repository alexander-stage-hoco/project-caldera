"""
OpenAI API provider for LLM evaluation.
"""

import os
from typing import Any

from . import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """Uses OpenAI API (gpt-4o, gpt-4-turbo, etc.)."""

    SUPPORTED_MODELS = [
        "gpt-4o",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-4o-mini",
        "gpt-3.5-turbo",
    ]

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str | None = None,
        organization: str | None = None,
        base_url: str | None = None,
    ):
        """
        Initialize OpenAI provider.

        Args:
            model: Model to use (default: gpt-4o).
            api_key: OpenAI API key (or OPENAI_API_KEY env var).
            organization: Optional organization ID.
            base_url: Optional custom base URL.
        """
        self._model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.organization = organization
        self.base_url = base_url
        self._client: Any = None

    @property
    def name(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return "gpt-4o"

    def supports_model(self, model: str) -> bool:
        return model in self.SUPPORTED_MODELS

    def _get_client(self) -> Any:
        """Lazy-initialize the OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError("openai package not installed. Run: pip install openai")

            if not self.api_key:
                raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY env var or pass api_key.")

            kwargs: dict[str, Any] = {"api_key": self.api_key}
            if self.organization:
                kwargs["organization"] = self.organization
            if self.base_url:
                kwargs["base_url"] = self.base_url

            self._client = OpenAI(**kwargs)

        return self._client

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send a completion request to OpenAI API."""
        client = self._get_client()
        effective_model = model or self._model

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=effective_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        choice = response.choices[0]
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return LLMResponse(
            content=choice.message.content or "",
            model=effective_model,
            usage=usage,
            metadata={
                "provider": "openai",
                "finish_reason": choice.finish_reason,
            },
        )
