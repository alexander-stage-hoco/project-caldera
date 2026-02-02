"""
LLM Logger with structlog integration.

Provides structured logging for LLM interactions with support for
both console output and file persistence.
"""

from datetime import datetime
from typing import Any
import uuid

# structlog is optional - only needed for console logging
try:
    import structlog
    HAS_STRUCTLOG = True
except ImportError:
    structlog = None  # type: ignore
    HAS_STRUCTLOG = False

from .schemas import LLMInteraction
from .config import ObservabilityConfig, get_config
from .storage import FileStore


class LLMLogger:
    """
    Logger for LLM interactions.

    Coordinates between structlog for console output and FileStore for persistence.
    Builds LLMInteraction objects from request/response pairs.
    """

    def __init__(
        self,
        config: ObservabilityConfig | None = None,
        store: FileStore | None = None,
    ):
        """
        Initialize the LLM logger.

        Args:
            config: Observability configuration (uses global config if None)
            store: File store for persistence (creates new one if None)
        """
        self.config = config or get_config()
        self.store = store or FileStore(base_dir=self.config.log_dir)

        # Configure structlog for console output (if available)
        if HAS_STRUCTLOG:
            self._logger = structlog.get_logger("llm_observability")
        else:
            self._logger = None

        # Track in-flight interactions for building complete records
        self._pending: dict[str, dict[str, Any]] = {}

    def start_interaction(
        self,
        interaction_id: str | None = None,
        trace_id: str | None = None,
        provider_name: str = "",
        judge_name: str | None = None,
        model: str = "",
        system_prompt: str | None = None,
        user_prompt: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Log the start of an LLM interaction.

        Args:
            interaction_id: Unique ID for this interaction (generated if None)
            trace_id: Correlation ID for related interactions
            provider_name: Name of the LLM provider
            judge_name: Name of the judge making the call (if applicable)
            model: Model being used
            system_prompt: System prompt text
            user_prompt: User prompt text
            metadata: Additional metadata

        Returns:
            The interaction_id (generated or provided)
        """
        if not self.config.enabled:
            return interaction_id or str(uuid.uuid4())

        interaction_id = interaction_id or str(uuid.uuid4())
        trace_id = trace_id or str(uuid.uuid4())

        # Truncate prompts if configured
        if self.config.max_prompt_length:
            if system_prompt and len(system_prompt) > self.config.max_prompt_length:
                system_prompt = system_prompt[: self.config.max_prompt_length] + "...[truncated]"
            if len(user_prompt) > self.config.max_prompt_length:
                user_prompt = user_prompt[: self.config.max_prompt_length] + "...[truncated]"

        # Store pending interaction data
        self._pending[interaction_id] = {
            "interaction_id": interaction_id,
            "trace_id": trace_id,
            "timestamp_start": datetime.now(),
            "provider_name": provider_name,
            "judge_name": judge_name,
            "model": model,
            "system_prompt": system_prompt if self.config.include_prompts else None,
            "user_prompt": user_prompt if self.config.include_prompts else "[redacted]",
            "metadata": metadata or {},
        }

        # Log to console if enabled and structlog available
        if self.config.log_to_console and self._logger is not None:
            self._logger.info(
                "llm_request_started",
                interaction_id=interaction_id,
                trace_id=trace_id,
                provider=provider_name,
                judge=judge_name,
                model=model,
                prompt_length=len(user_prompt),
            )

        return interaction_id

    def complete_interaction(
        self,
        interaction_id: str,
        response_content: str = "",
        usage: dict[str, int] | None = None,
        status: str = "success",
        error_message: str | None = None,
        parsed_score: float | None = None,
        parsed_reasoning: str | None = None,
        parsed_sub_scores: dict[str, float] | None = None,
    ) -> LLMInteraction | None:
        """
        Complete a pending interaction and persist it.

        Args:
            interaction_id: ID from start_interaction
            response_content: LLM response text
            usage: Token usage dict (prompt_tokens, completion_tokens, total_tokens)
            status: "success", "error", or "timeout"
            error_message: Error message if status != "success"
            parsed_score: Parsed score from response (if applicable)
            parsed_reasoning: Parsed reasoning from response (if applicable)
            parsed_sub_scores: Parsed sub-dimension scores (if applicable)

        Returns:
            The completed LLMInteraction, or None if not found/disabled
        """
        if not self.config.enabled:
            return None

        pending = self._pending.pop(interaction_id, None)
        if not pending:
            if self._logger is not None:
                self._logger.warning(
                    "llm_interaction_not_found",
                    interaction_id=interaction_id,
                )
            return None

        timestamp_end = datetime.now()
        duration_ms = int((timestamp_end - pending["timestamp_start"]).total_seconds() * 1000)

        # Truncate response if configured
        if self.config.max_response_length and len(response_content) > self.config.max_response_length:
            response_content = response_content[: self.config.max_response_length] + "...[truncated]"

        # Build the interaction record
        interaction = LLMInteraction(
            interaction_id=interaction_id,
            trace_id=pending["trace_id"],
            timestamp_start=pending["timestamp_start"],
            timestamp_end=timestamp_end,
            duration_ms=duration_ms,
            provider_name=pending["provider_name"],
            judge_name=pending["judge_name"],
            model=pending["model"],
            system_prompt=pending["system_prompt"],
            user_prompt=pending["user_prompt"],
            prompt_tokens=usage.get("prompt_tokens") if usage else None,
            response_content=response_content if self.config.include_responses else "[redacted]",
            completion_tokens=usage.get("completion_tokens") if usage else None,
            total_tokens=usage.get("total_tokens") if usage else None,
            status=status,
            error_message=error_message,
            parsed_score=parsed_score if self.config.capture_parsed_results else None,
            parsed_reasoning=parsed_reasoning if self.config.capture_parsed_results else None,
            parsed_sub_scores=parsed_sub_scores if self.config.capture_parsed_results else None,
            metadata=pending["metadata"],
        )

        # Persist to file
        if self.config.log_to_file:
            self.store.append(interaction)

        # Log to console if enabled and structlog available
        if self.config.log_to_console and self._logger is not None:
            log_method = self._logger.info if status == "success" else self._logger.error
            log_method(
                "llm_request_completed",
                interaction_id=interaction_id,
                trace_id=pending["trace_id"],
                provider=pending["provider_name"],
                judge=pending["judge_name"],
                status=status,
                duration_ms=duration_ms,
                response_length=len(response_content),
                parsed_score=parsed_score,
            )

        return interaction

    def log_error(
        self,
        interaction_id: str,
        error: Exception,
    ) -> LLMInteraction | None:
        """
        Log an error for an in-flight interaction.

        Convenience method that calls complete_interaction with error status.
        """
        return self.complete_interaction(
            interaction_id=interaction_id,
            response_content="",
            status="error",
            error_message=str(error),
        )

    def log_timeout(
        self,
        interaction_id: str,
        timeout_seconds: int,
    ) -> LLMInteraction | None:
        """
        Log a timeout for an in-flight interaction.

        Convenience method that calls complete_interaction with timeout status.
        """
        return self.complete_interaction(
            interaction_id=interaction_id,
            response_content="",
            status="timeout",
            error_message=f"Request timed out after {timeout_seconds} seconds",
        )

    def get_pending_count(self) -> int:
        """Get the number of pending (in-flight) interactions."""
        return len(self._pending)


# Global logger instance (lazy-loaded)
_global_logger: LLMLogger | None = None


def get_llm_logger() -> LLMLogger:
    """
    Get the global LLM logger instance.

    Creates a new logger with global config on first call.
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = LLMLogger()
    return _global_logger


def reset_llm_logger() -> None:
    """Reset the global logger (for testing)."""
    global _global_logger
    _global_logger = None
