"""NarrativeEnricher — shared LLM wrapper for report narrative generation.

Reuses the existing LLM provider infrastructure from the evaluation layer.
Returns ``None`` on any failure so callers always fall back to rule-based output.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
import warnings
from typing import Any

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a senior software architect writing concise, factual narrative "
    "sections for a code analysis report. Be specific: reference exact file "
    "names, metric values, and CVE IDs from the data provided. Do not invent "
    "metrics. Respond with only the narrative text."
)

DEFAULT_MODEL = "claude-sonnet-4"


class NarrativeEnricher:
    """LLM-powered narrative enrichment for report sections.

    Provider selection:
    - If ``ANTHROPIC_API_KEY`` is set → ``AnthropicAPIProvider``
    - Otherwise → ``ClaudeCodeHeadlessProvider``

    The provider is wrapped in ``ObservableProvider`` for correlated logging.
    """

    def __init__(self, trace_id: str | None = None) -> None:
        self._trace_id = trace_id or str(uuid.uuid4())
        self._provider = self._create_provider()

    def _create_provider(self) -> Any:
        """Create and wrap the LLM provider."""
        from ..evaluation.llm.providers import LLMProvider
        from ..evaluation.llm.observability.observable_provider import ObservableProvider

        provider: LLMProvider
        if os.environ.get("ANTHROPIC_API_KEY"):
            from ..evaluation.llm.providers.anthropic import AnthropicAPIProvider

            provider = AnthropicAPIProvider(model=DEFAULT_MODEL)
        else:
            from ..evaluation.llm.providers.claude_code import ClaudeCodeHeadlessProvider

            provider = ClaudeCodeHeadlessProvider(model=DEFAULT_MODEL)

        return ObservableProvider(
            provider=provider,
            trace_id=self._trace_id,
            judge_name="NarrativeEnricher",
        )

    @property
    def trace_id(self) -> str:
        """Trace ID shared across all enrichment calls."""
        return self._trace_id

    def enrich(
        self,
        task: str,
        data: dict[str, Any],
        max_tokens: int = 512,
    ) -> str | None:
        """Generate a narrative enrichment from structured data.

        Args:
            task: Description of what narrative to produce.
            data: Structured data to feed the LLM.
            max_tokens: Maximum tokens for the response.

        Returns:
            Narrative text on success, ``None`` on any failure.
        """
        prompt = f"{task}\n\nData:\n{json.dumps(data, indent=2, default=str)}"

        try:
            response = self._provider.complete(
                prompt=prompt,
                system=SYSTEM_PROMPT,
                model=DEFAULT_MODEL,
                temperature=0.3,
                max_tokens=max_tokens,
            )
            content = response.content.strip()
            if not content:
                return None
            return content
        except Exception as exc:
            warnings.warn(
                f"[NarrativeEnricher] LLM call failed: {exc}",
                stacklevel=2,
            )
            logger.debug("NarrativeEnricher failure details", exc_info=True)
            return None
