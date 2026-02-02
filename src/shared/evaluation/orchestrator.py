"""Shared LLM Evaluation Orchestrator.

Provides common dataclasses and base evaluator class that all tool-specific
orchestrators can inherit from to reduce code duplication.
"""

from __future__ import annotations

import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .base_judge import BaseJudge, JudgeResult
from .observability_check import require_observability


@dataclass
class DimensionResult:
    """Result for a single evaluation dimension."""

    name: str
    score: int  # 1-5
    weight: float
    weighted_score: float
    confidence: float
    reasoning: str
    evidence_cited: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    sub_scores: dict[str, int] = field(default_factory=dict)
    ground_truth_passed: bool = True
    ground_truth_failures: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ProgrammaticInput:
    """Reference to programmatic evaluation results."""

    file: str
    decision: str
    score: float
    checks_passed: int
    checks_failed: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class EvaluationResult:
    """Complete LLM evaluation result."""

    run_id: str
    timestamp: str
    model: str
    dimensions: list[DimensionResult]
    total_score: float
    average_confidence: float
    decision: str
    programmatic_score: float | None = None
    combined_score: float | None = None
    programmatic_input: ProgrammaticInput | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "model": self.model,
            "decision": self.decision,
            "score": self.total_score,
            "programmatic_input": self.programmatic_input.to_dict() if self.programmatic_input else None,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "summary": {
                "weighted_score": self.total_score,
                "avg_confidence": self.average_confidence,
            },
            # Legacy fields for backward compatibility
            "run_id": self.run_id,
            "total_score": self.total_score,
            "average_confidence": self.average_confidence,
            "programmatic_score": self.programmatic_score,
            "combined_score": self.combined_score,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class LLMEvaluatorBase(ABC):
    """Base class for LLM-based evaluation orchestrators.

    Coordinates multiple specialized judges, each evaluating a specific
    dimension of output quality. Subclasses must implement judge registration.
    """

    # Decision thresholds (on 5-point scale)
    STRONG_PASS_THRESHOLD = 4.0
    PASS_THRESHOLD = 3.5
    WEAK_PASS_THRESHOLD = 3.0

    # Combined scoring weights
    PROGRAMMATIC_WEIGHT = 0.60
    LLM_WEIGHT = 0.40

    def __init__(
        self,
        working_dir: Path | None = None,
        model: str = "opus-4.5",
        results_dir: Path | None = None,
    ):
        """Initialize the evaluator.

        Args:
            working_dir: Working directory containing analysis outputs.
            model: Claude model to use for evaluation.
            results_dir: Directory to save evaluation results.
        """
        self.working_dir = working_dir or Path.cwd()
        self.model = model
        self.results_dir = results_dir or self._default_results_dir()
        self._judges: list[BaseJudge] = []

    def _default_results_dir(self) -> Path:
        """Return the default results directory. Can be overridden by subclasses."""
        return self.working_dir / "evaluation" / "llm" / "results"

    def register_judge(self, judge: BaseJudge) -> None:
        """Register a judge for evaluation."""
        self._judges.append(judge)

    @abstractmethod
    def register_all_judges(self) -> None:
        """Register all available judges for this tool. Must be implemented by subclasses."""
        ...

    @abstractmethod
    def register_focused_judges(self) -> None:
        """Register a subset of judges for quick evaluation. Must be implemented by subclasses."""
        ...

    def evaluate(self, run_assertions: bool = True) -> EvaluationResult:
        """Run evaluation with all registered judges.

        Args:
            run_assertions: Whether to run ground truth assertions.

        Returns:
            EvaluationResult with all dimension scores and overall decision.
        """
        # Enforce observability - fail fast if disabled
        require_observability()

        run_id = f"llm-eval-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        timestamp = datetime.now(timezone.utc).isoformat()

        # Generate trace ID to correlate all judge interactions
        trace_id = str(uuid.uuid4())

        dimension_results: list[DimensionResult] = []
        total_weight = 0.0
        weighted_sum = 0.0
        confidence_sum = 0.0

        for judge in self._judges:
            # Propagate trace_id to judge if it supports it
            if hasattr(judge, "_trace_id"):
                judge._trace_id = trace_id

            print(f"Running {judge.dimension_name} evaluation...")

            # Run ground truth assertions first
            gt_passed = True
            gt_failures: list[str] = []
            if run_assertions:
                gt_passed, gt_failures = judge.run_ground_truth_assertions()
                if not gt_passed:
                    print(f"  Ground truth assertions failed: {len(gt_failures)} failures")

            # Run LLM evaluation
            result = judge.evaluate()

            # Apply ground truth penalty if assertions failed
            if not gt_passed:
                result.score = min(result.score, 2)  # Cap at 2 if assertions fail

            weighted_score = result.score * judge.weight

            dim_result = DimensionResult(
                name=judge.dimension_name,
                score=result.score,
                weight=judge.weight,
                weighted_score=weighted_score,
                confidence=result.confidence,
                reasoning=result.reasoning,
                evidence_cited=result.evidence_cited,
                recommendations=result.recommendations,
                sub_scores=result.sub_scores,
                ground_truth_passed=gt_passed,
                ground_truth_failures=gt_failures,
            )

            dimension_results.append(dim_result)
            weighted_sum += weighted_score
            total_weight += judge.weight
            confidence_sum += result.confidence

            print(f"  Score: {result.score}/5 (confidence: {result.confidence:.2f})")

        # Calculate totals
        if total_weight > 0:
            total_score = weighted_sum / total_weight
        else:
            total_score = 0.0

        avg_confidence = confidence_sum / len(self._judges) if self._judges else 0.0

        # Determine decision
        decision = self._determine_decision(total_score)

        return EvaluationResult(
            run_id=run_id,
            timestamp=timestamp,
            model=self.model,
            dimensions=dimension_results,
            total_score=total_score,
            average_confidence=avg_confidence,
            decision=decision,
        )

    def _determine_decision(self, score: float) -> str:
        """Determine pass/fail decision based on score."""
        if score >= self.STRONG_PASS_THRESHOLD:
            return "STRONG_PASS"
        elif score >= self.PASS_THRESHOLD:
            return "PASS"
        elif score >= self.WEAK_PASS_THRESHOLD:
            return "WEAK_PASS"
        else:
            return "FAIL"

    def compute_combined_score(
        self,
        llm_result: EvaluationResult,
        programmatic_score: float,
    ) -> EvaluationResult:
        """Compute combined score from LLM and programmatic evaluations.

        Args:
            llm_result: The LLM evaluation result.
            programmatic_score: The programmatic evaluation score (expected on same scale as LLM).

        Returns:
            Updated EvaluationResult with combined score.
        """
        combined = (
            programmatic_score * self.PROGRAMMATIC_WEIGHT
            + llm_result.total_score * self.LLM_WEIGHT
        )

        llm_result.programmatic_score = programmatic_score
        llm_result.combined_score = combined

        # Update decision based on combined score
        llm_result.decision = self._determine_decision(combined)

        return llm_result

    def save_results(self, result: EvaluationResult) -> Path:
        """Save evaluation results to file.

        Args:
            result: The evaluation result to save.

        Returns:
            Path to the saved results file.
        """
        self.results_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.results_dir / f"{result.run_id}.json"
        output_file.write_text(result.to_json())
        return output_file

    def generate_markdown_report(self, result: EvaluationResult, title: str | None = None) -> str:
        """Generate a markdown report from evaluation results.

        Args:
            result: The evaluation result to report on.
            title: Optional custom title for the report.

        Returns:
            Markdown formatted report string.
        """
        title = title or "LLM Evaluation Report"
        lines = [
            f"# {title}",
            "",
            f"**Run ID:** {result.run_id}",
            f"**Timestamp:** {result.timestamp}",
            f"**Model:** {result.model}",
            "",
            "---",
            "",
            "## Summary",
            "",
            f"**LLM Score:** {result.total_score:.2f}/5.0",
            f"**Average Confidence:** {result.average_confidence:.2f}",
        ]

        if result.programmatic_score is not None:
            lines.append(f"**Programmatic Score:** {result.programmatic_score:.2f}/5.0")

        if result.combined_score is not None:
            lines.append(f"**Combined Score:** {result.combined_score:.2f}/5.0")

        lines.extend([
            f"**Decision:** {result.decision}",
            "",
            "---",
            "",
            "## Dimension Scores",
            "",
            "| Dimension | Score | Weight | Weighted | Confidence |",
            "|-----------|-------|--------|----------|------------|",
        ])

        for dim in result.dimensions:
            lines.append(
                f"| {dim.name} | {dim.score}/5 | {dim.weight:.0%} | "
                f"{dim.weighted_score:.2f} | {dim.confidence:.2f} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## Detailed Results",
            "",
        ])

        for dim in result.dimensions:
            lines.extend([
                f"### {dim.name}",
                "",
                f"**Score:** {dim.score}/5",
                f"**Weight:** {dim.weight:.0%}",
                f"**Confidence:** {dim.confidence:.2f}",
                "",
            ])

            if not dim.ground_truth_passed:
                lines.extend([
                    "**Ground Truth Assertions Failed:**",
                    "",
                ])
                for failure in dim.ground_truth_failures:
                    lines.append(f"- {failure}")
                lines.append("")

            if dim.sub_scores:
                lines.extend([
                    "**Sub-Scores:**",
                    "",
                ])
                for sub, score in dim.sub_scores.items():
                    lines.append(f"- {sub}: {score}/5")
                lines.append("")

            lines.extend([
                "**Reasoning:**",
                "",
                dim.reasoning,
                "",
            ])

            if dim.evidence_cited:
                lines.extend([
                    "**Evidence Cited:**",
                    "",
                ])
                for ev in dim.evidence_cited:
                    lines.append(f"- {ev}")
                lines.append("")

            if dim.recommendations:
                lines.extend([
                    "**Recommendations:**",
                    "",
                ])
                for rec in dim.recommendations:
                    lines.append(f"- {rec}")
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)
