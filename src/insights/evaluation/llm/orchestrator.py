"""
LLM evaluation orchestrator - coordinates multiple judges.
"""

from dataclasses import dataclass, field
from typing import Any
import uuid

from .providers import LLMProvider, get_provider
from .judges import (
    BaseJudge,
    JudgeResult,
    ClarityJudge,
    ActionabilityJudge,
    AccuracyJudge,
    InsightQualityJudge,
)
from .observability import ObservableProvider
from shared.observability import get_llm_logger, get_config


@dataclass
class EvaluationResult:
    """Combined result from all LLM judges."""

    overall_score: float  # Weighted average of all judges
    judge_results: list[JudgeResult]
    combined_suggestions: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)
    trace_id: str | None = None  # Correlation ID for observability

    @property
    def pass_status(self) -> str:
        """Determine pass/fail status based on score."""
        if self.overall_score >= 4.0:
            return "STRONG_PASS"
        elif self.overall_score >= 3.5:
            return "PASS"
        elif self.overall_score >= 3.0:
            return "WEAK_PASS"
        else:
            return "FAIL"


class LLMOrchestrator:
    """Coordinates multiple LLM judges for comprehensive evaluation."""

    def __init__(
        self,
        provider: LLMProvider | None = None,
        provider_name: str = "claude_code",
        model: str | None = None,
        judges: list[BaseJudge] | None = None,
        enable_observability: bool = True,
        include_insight_quality: bool = False,
    ):
        """
        Initialize the orchestrator.

        Args:
            provider: LLM provider instance (overrides provider_name).
            provider_name: Provider name to use if provider not given.
            model: Optional model override.
            judges: Optional list of judges (defaults to all three).
            enable_observability: Whether to wrap provider with observability.
            include_insight_quality: Whether to include InsightQualityJudge for
                top 3 insight extraction and prioritization evaluation.
        """
        if provider is None:
            provider = get_provider(provider_name, model=model)

        self.provider = provider
        self.model = model
        self._enable_observability = enable_observability and get_config().enabled

        # Initialize judges with the same provider
        if judges is None:
            judges = [
                ClarityJudge(provider=provider, model=model),
                ActionabilityJudge(provider=provider, model=model),
                AccuracyJudge(provider=provider, model=model),
            ]
            # Optionally add InsightQualityJudge for top 3 extraction
            if include_insight_quality:
                judges.append(InsightQualityJudge(provider=provider, model=model))

        self.judges = judges

    def evaluate(
        self,
        report_content: str,
        context: dict[str, Any] | None = None,
        trace_id: str | None = None,
    ) -> EvaluationResult:
        """
        Run all judges on a report and combine results.

        Args:
            report_content: The report content to evaluate.
            context: Additional context for evaluation.
            trace_id: Optional trace ID for observability (generated if None).

        Returns:
            EvaluationResult with combined scores and feedback.
        """
        context = context or {}
        judge_results: list[JudgeResult] = []

        # Generate trace ID for observability correlation
        trace_id = trace_id or str(uuid.uuid4())

        # Run each judge
        for judge in self.judges:
            try:
                # Wrap provider with observability if enabled
                if self._enable_observability:
                    observable_provider = ObservableProvider(
                        provider=self.provider,
                        trace_id=trace_id,
                        judge_name=judge.name,
                    )
                    # Temporarily swap the judge's provider
                    original_provider = judge.provider
                    judge.provider = observable_provider

                result = judge.evaluate(report_content, context)

                # Update parsed results in the logger for the last interaction
                if self._enable_observability:
                    logger = get_llm_logger()
                    # Note: The interaction is already logged, but we can't update
                    # parsed results retroactively without refactoring BaseJudge.
                    # This would require BaseJudge to expose the interaction_id.
                    judge.provider = original_provider

                judge_results.append(result)
            except Exception as e:
                # Restore provider if it was swapped
                if self._enable_observability and 'original_provider' in dir():
                    judge.provider = original_provider

                # Create a failed result for this judge
                judge_results.append(JudgeResult(
                    judge_name=judge.name,
                    overall_score=1.0,
                    sub_scores={},
                    reasoning=f"Judge failed: {e}",
                    suggestions=[],
                    raw_response="",
                    metadata={"error": str(e), "trace_id": trace_id},
                ))

        # Calculate weighted overall score
        total_weight = sum(j.weight for j in self.judges)
        weighted_sum = sum(
            result.overall_score * judge.weight
            for result, judge in zip(judge_results, self.judges)
        )
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Combine suggestions (deduplicate and prioritize)
        all_suggestions = []
        for result in judge_results:
            all_suggestions.extend(result.suggestions)
        combined_suggestions = list(dict.fromkeys(all_suggestions))[:10]  # Unique, top 10

        return EvaluationResult(
            overall_score=overall_score,
            judge_results=judge_results,
            combined_suggestions=combined_suggestions,
            metadata={
                "provider": self.provider.name,
                "model": self.model or self.provider.default_model,
                "judge_count": len(self.judges),
            },
            trace_id=trace_id,
        )

    def evaluate_single_judge(
        self,
        judge_name: str,
        report_content: str,
        context: dict[str, Any] | None = None,
    ) -> JudgeResult:
        """
        Run a single judge by name.

        Args:
            judge_name: Name of the judge to run.
            report_content: The report content to evaluate.
            context: Additional context.

        Returns:
            JudgeResult from the specified judge.
        """
        for judge in self.judges:
            if judge.name == judge_name:
                return judge.evaluate(report_content, context)

        raise ValueError(f"Unknown judge: {judge_name}. Available: {[j.name for j in self.judges]}")

    def list_judges(self) -> list[dict[str, Any]]:
        """List available judges with their configuration."""
        return [
            {
                "name": judge.name,
                "weight": judge.weight,
                "sub_dimensions": judge.sub_dimensions,
            }
            for judge in self.judges
        ]
