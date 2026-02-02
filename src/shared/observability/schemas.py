"""
Data schemas for LLM observability.

Defines the core data structures for logging and tracing LLM interactions.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any
import json


@dataclass
class LLMInteraction:
    """
    Represents a single LLM request/response interaction.

    This captures everything needed to debug and analyze LLM calls:
    - Timing information (start, end, duration)
    - Source identification (provider, judge, model)
    - Full input (system prompt, user prompt)
    - Full output (response, tokens, status)
    - Parsed results (score, reasoning)
    """

    # Identification
    interaction_id: str  # UUID for this specific interaction
    trace_id: str  # Correlation ID for related interactions (e.g., all judges in one eval)

    # Timing
    timestamp_start: datetime
    timestamp_end: datetime
    duration_ms: int

    # Source
    provider_name: str  # "claude_code", "anthropic", "openai"
    judge_name: str | None  # "clarity", "actionability", "accuracy", or None for raw calls
    model: str  # "claude-opus-4-5-20251101"

    # Input
    system_prompt: str | None
    user_prompt: str
    prompt_tokens: int | None = None

    # Output
    response_content: str = ""
    completion_tokens: int | None = None
    total_tokens: int | None = None
    status: str = "success"  # "success", "error", "timeout"
    error_message: str | None = None

    # Parsed result (populated after response parsing)
    parsed_score: float | None = None
    parsed_reasoning: str | None = None
    parsed_sub_scores: dict[str, float] | None = None

    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        data["timestamp_start"] = self.timestamp_start.isoformat()
        data["timestamp_end"] = self.timestamp_end.isoformat()
        return data

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LLMInteraction":
        """Create from dictionary (e.g., loaded from JSON)."""
        # Convert ISO format strings back to datetime
        if isinstance(data.get("timestamp_start"), str):
            data["timestamp_start"] = datetime.fromisoformat(data["timestamp_start"])
        if isinstance(data.get("timestamp_end"), str):
            data["timestamp_end"] = datetime.fromisoformat(data["timestamp_end"])
        return cls(**data)


@dataclass
class EvaluationSpan:
    """
    Represents a complete evaluation span containing multiple judge interactions.

    This is useful for analyzing an entire evaluation run that includes
    multiple judges (clarity, actionability, accuracy).
    """

    trace_id: str  # Shared trace ID for all interactions in this span
    timestamp_start: datetime
    timestamp_end: datetime
    total_duration_ms: int

    # Evaluation context
    report_format: str | None = None  # "html", "json", etc.
    run_pk: int | None = None

    # Aggregated results
    judge_count: int = 0
    successful_judges: int = 0
    failed_judges: int = 0

    # Overall evaluation result
    overall_score: float | None = None
    pass_status: str | None = None

    # Individual interactions (populated on demand)
    interactions: list[LLMInteraction] = field(default_factory=list)

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = {
            "trace_id": self.trace_id,
            "timestamp_start": self.timestamp_start.isoformat(),
            "timestamp_end": self.timestamp_end.isoformat(),
            "total_duration_ms": self.total_duration_ms,
            "report_format": self.report_format,
            "run_pk": self.run_pk,
            "judge_count": self.judge_count,
            "successful_judges": self.successful_judges,
            "failed_judges": self.failed_judges,
            "overall_score": self.overall_score,
            "pass_status": self.pass_status,
            "interactions": [i.to_dict() for i in self.interactions],
            "metadata": self.metadata,
        }
        return data

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_interactions(
        cls,
        trace_id: str,
        interactions: list[LLMInteraction],
        overall_score: float | None = None,
        pass_status: str | None = None,
        **kwargs: Any,
    ) -> "EvaluationSpan":
        """Create an EvaluationSpan from a list of interactions."""
        if not interactions:
            now = datetime.now()
            return cls(
                trace_id=trace_id,
                timestamp_start=now,
                timestamp_end=now,
                total_duration_ms=0,
                interactions=[],
                overall_score=overall_score,
                pass_status=pass_status,
                **kwargs,
            )

        start = min(i.timestamp_start for i in interactions)
        end = max(i.timestamp_end for i in interactions)
        total_duration = int((end - start).total_seconds() * 1000)

        successful = sum(1 for i in interactions if i.status == "success")
        failed = sum(1 for i in interactions if i.status != "success")

        return cls(
            trace_id=trace_id,
            timestamp_start=start,
            timestamp_end=end,
            total_duration_ms=total_duration,
            judge_count=len(interactions),
            successful_judges=successful,
            failed_judges=failed,
            overall_score=overall_score,
            pass_status=pass_status,
            interactions=interactions,
            **kwargs,
        )
