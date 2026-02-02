"""
Observable provider wrapper for LLM providers.

Wraps any LLMProvider with logging and tracing capabilities.
"""

from typing import Any
import uuid

from ..providers import LLMProvider, LLMResponse
from shared.observability import LLMLogger, get_llm_logger


class ObservableProvider(LLMProvider):
    """
    Wraps an LLMProvider with observability logging.

    This wrapper intercepts all calls to complete() and logs:
    - Request start (prompt, model, etc.)
    - Response (content, tokens, duration)
    - Errors and timeouts

    All interactions share a trace_id for correlation.

    Usage:
        provider = ClaudeCodeHeadlessProvider()
        observable = ObservableProvider(provider, trace_id="eval-123")

        # All calls are now logged
        response = observable.complete("Hello")
    """

    def __init__(
        self,
        provider: LLMProvider,
        logger: LLMLogger | None = None,
        trace_id: str | None = None,
        judge_name: str | None = None,
    ):
        """
        Initialize the observable provider.

        Args:
            provider: The underlying LLM provider to wrap
            logger: LLM logger instance (uses global if None)
            trace_id: Correlation ID for all interactions (generated if None)
            judge_name: Name of the judge using this provider (for tagging)
        """
        self._provider = provider
        self._logger = logger or get_llm_logger()
        self._trace_id = trace_id or str(uuid.uuid4())
        self._judge_name = judge_name

    @property
    def name(self) -> str:
        """Provider name (from wrapped provider)."""
        return self._provider.name

    @property
    def default_model(self) -> str:
        """Default model (from wrapped provider)."""
        return self._provider.default_model

    @property
    def trace_id(self) -> str:
        """Get the trace ID for this provider."""
        return self._trace_id

    @property
    def judge_name(self) -> str | None:
        """Get the judge name for this provider."""
        return self._judge_name

    @judge_name.setter
    def judge_name(self, value: str | None) -> None:
        """Set the judge name for subsequent calls."""
        self._judge_name = value

    def supports_model(self, model: str) -> bool:
        """Check if model is supported (delegates to wrapped provider)."""
        return self._provider.supports_model(model)

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """
        Send a completion request with observability logging.

        Args:
            prompt: The user prompt
            system: Optional system prompt
            model: Optional model override
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse from the wrapped provider
        """
        model = model or self._provider.default_model

        # Start interaction logging
        interaction_id = self._logger.start_interaction(
            trace_id=self._trace_id,
            provider_name=self._provider.name,
            judge_name=self._judge_name,
            model=model,
            system_prompt=system,
            user_prompt=prompt,
            metadata={
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )

        try:
            # Call the wrapped provider
            response = self._provider.complete(
                prompt=prompt,
                system=system,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Log successful completion
            self._logger.complete_interaction(
                interaction_id=interaction_id,
                response_content=response.content,
                usage=response.usage,
                status="success",
            )

            return response

        except TimeoutError as e:
            # Log timeout
            self._logger.log_timeout(interaction_id, timeout_seconds=120)
            raise

        except Exception as e:
            # Log error
            self._logger.log_error(interaction_id, e)
            raise

    def with_judge(self, judge_name: str) -> "ObservableProvider":
        """
        Create a new observable provider for a specific judge.

        Returns a new instance with the same trace_id but tagged with
        the judge name. Useful when passing the provider to different judges.

        Args:
            judge_name: Name of the judge

        Returns:
            New ObservableProvider instance
        """
        return ObservableProvider(
            provider=self._provider,
            logger=self._logger,
            trace_id=self._trace_id,
            judge_name=judge_name,
        )


def wrap_provider(
    provider: LLMProvider,
    trace_id: str | None = None,
    judge_name: str | None = None,
) -> ObservableProvider:
    """
    Convenience function to wrap a provider with observability.

    If the provider is already an ObservableProvider, returns it unchanged
    (or creates a new one with updated trace_id if provided).

    Args:
        provider: The LLM provider to wrap
        trace_id: Optional trace ID (generated if None)
        judge_name: Optional judge name for tagging

    Returns:
        ObservableProvider wrapping the given provider
    """
    if isinstance(provider, ObservableProvider):
        if trace_id is None and judge_name is None:
            return provider
        # Create new wrapper with updated trace_id or judge_name
        return ObservableProvider(
            provider=provider._provider,
            logger=provider._logger,
            trace_id=trace_id or provider._trace_id,
            judge_name=judge_name or provider._judge_name,
        )

    return ObservableProvider(
        provider=provider,
        trace_id=trace_id,
        judge_name=judge_name,
    )
