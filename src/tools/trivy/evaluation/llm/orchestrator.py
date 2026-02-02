"""LLM Evaluation Orchestrator for Trivy vulnerability scanning outputs.

Coordinates multiple LLM judges to produce a comprehensive qualitative
evaluation of Trivy analysis outputs.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click

from shared.evaluation import require_observability

from .judges.base import BaseJudge, JudgeResult


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
    trace_id: str | None = None

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
            "trace_id": self.trace_id,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class LLMEvaluator:
    """Orchestrates LLM-based evaluation of Trivy outputs.

    Coordinates multiple specialized judges, each evaluating a specific
    dimension of output quality.
    """

    # Decision thresholds
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
        timeout: int = 120,
        output_dir: Path | None = None,
    ):
        self.working_dir = working_dir or Path.cwd()
        self.model = model
        self.results_dir = results_dir or self.working_dir / "evaluation" / "results"
        self.timeout = timeout
        self.output_dir = output_dir or self.working_dir / "outputs"
        self._judges: list[BaseJudge] = []

    def register_judge(self, judge: BaseJudge) -> None:
        """Register a judge for evaluation."""
        self._judges.append(judge)

    def register_all_judges(self) -> None:
        """Register all available judges for comprehensive evaluation."""
        from .judges.vulnerability_accuracy import VulnerabilityAccuracyJudge
        from .judges.severity_accuracy import SeverityAccuracyJudge
        from .judges.sbom_completeness import SBOMCompletenessJudge
        from .judges.iac_quality import IaCQualityJudge
        from .judges.false_positive_rate import FalsePositiveRateJudge
        from .judges.freshness_quality import FreshnessQualityJudge
        from .judges.vulnerability_detection import VulnerabilityDetectionJudge

        judges = [
            VulnerabilityAccuracyJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout, output_dir=self.output_dir),
            SeverityAccuracyJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout, output_dir=self.output_dir),
            SBOMCompletenessJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout, output_dir=self.output_dir),
            IaCQualityJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout, output_dir=self.output_dir),
            FalsePositiveRateJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout, output_dir=self.output_dir),
            FreshnessQualityJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout, output_dir=self.output_dir),
            VulnerabilityDetectionJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout, output_dir=self.output_dir),
        ]

        for judge in judges:
            self.register_judge(judge)

    def register_focused_judges(self) -> None:
        """Register only the most important judges for quick evaluation."""
        from .judges.vulnerability_accuracy import VulnerabilityAccuracyJudge
        from .judges.severity_accuracy import SeverityAccuracyJudge
        from .judges.iac_quality import IaCQualityJudge

        judges = [
            VulnerabilityAccuracyJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout, output_dir=self.output_dir),
            SeverityAccuracyJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout, output_dir=self.output_dir),
            IaCQualityJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout, output_dir=self.output_dir),
        ]

        for judge in judges:
            self.register_judge(judge)

    def evaluate(self, run_assertions: bool = True) -> EvaluationResult:
        """Run evaluation with all registered judges."""
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
            # Propagate trace_id to judge
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
            # Normalize to 5-point scale
            total_score = weighted_sum / total_weight
        else:
            total_score = 0.0

        avg_confidence = confidence_sum / len(self._judges) if self._judges else 0.0

        # Determine decision
        if total_score >= self.STRONG_PASS_THRESHOLD:
            decision = "STRONG_PASS"
        elif total_score >= self.PASS_THRESHOLD:
            decision = "PASS"
        elif total_score >= self.WEAK_PASS_THRESHOLD:
            decision = "WEAK_PASS"
        else:
            decision = "FAIL"

        return EvaluationResult(
            run_id=run_id,
            timestamp=timestamp,
            model=self.model,
            dimensions=dimension_results,
            total_score=total_score,
            average_confidence=avg_confidence,
            decision=decision,
            trace_id=trace_id,
        )

    def compute_combined_score(
        self,
        llm_result: EvaluationResult,
        programmatic_score: float,
    ) -> EvaluationResult:
        """Compute combined score from LLM and programmatic evaluations."""
        combined = (
            programmatic_score * self.PROGRAMMATIC_WEIGHT +
            llm_result.total_score * self.LLM_WEIGHT
        )

        llm_result.programmatic_score = programmatic_score
        llm_result.combined_score = combined

        # Update decision based on combined score
        if combined >= self.STRONG_PASS_THRESHOLD:
            llm_result.decision = "STRONG_PASS"
        elif combined >= self.PASS_THRESHOLD:
            llm_result.decision = "PASS"
        elif combined >= self.WEAK_PASS_THRESHOLD:
            llm_result.decision = "WEAK_PASS"
        else:
            llm_result.decision = "FAIL"

        return llm_result

    def save_results(self, result: EvaluationResult) -> Path:
        """Save evaluation results to file."""
        self.results_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.results_dir / "llm_evaluation.json"
        output_file.write_text(result.to_json())
        return output_file


@click.command()
@click.option("--analysis", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--output", type=click.Path(path_type=Path), required=True)
@click.option("--model", default="opus-4.5", help="LLM model to use")
@click.option("--programmatic-results", type=click.Path(exists=True, path_type=Path), help="Path to programmatic evaluation JSON")
@click.option("--focused", is_flag=True, help="Use focused judges for quick evaluation")
def main(analysis: Path, output: Path, model: str, programmatic_results: Path | None, focused: bool):
    """Run LLM evaluation on Trivy analysis output."""
    # Determine working directory from analysis path
    working_dir = analysis.parent.parent.parent  # outputs/<run-id>/output.json -> tool root

    # Determine output_dir from analysis path (parent of the analysis file)
    output_dir = analysis.parent

    # Create evaluator
    evaluator = LLMEvaluator(
        working_dir=working_dir,
        model=model,
        results_dir=output.parent,
        output_dir=output_dir,
    )

    # Register judges
    if focused:
        evaluator.register_focused_judges()
    else:
        evaluator.register_all_judges()

    # Run evaluation
    result = evaluator.evaluate()

    # Load programmatic input if provided
    if programmatic_results:
        prog_data = json.loads(programmatic_results.read_text())
        summary = prog_data.get("summary", {})
        prog_decision = prog_data.get("decision") or prog_data.get("classification") or "UNKNOWN"
        prog_score = prog_data.get("score") or prog_data.get("overall_score") or 0.0

        result.programmatic_input = ProgrammaticInput(
            file=str(programmatic_results),
            decision=prog_decision,
            score=prog_score,
            checks_passed=summary.get("passed", 0),
            checks_failed=summary.get("failed", 0),
        )

        # Compute combined score
        evaluator.compute_combined_score(result, prog_score)

    # Save results
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result.to_json())
    click.echo(f"LLM evaluation complete: {output}")


if __name__ == "__main__":
    main()
