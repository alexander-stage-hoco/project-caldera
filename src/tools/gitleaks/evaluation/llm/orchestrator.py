"""LLM Evaluation Orchestrator for Gitleaks PoC.

Coordinates multiple LLM judges to produce a comprehensive qualitative
evaluation of Gitleaks secret detection outputs.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
        return {
            "file": self.file,
            "decision": self.decision,
            "score": self.score,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
        }


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


class LLMEvaluator:
    """Orchestrates LLM-based evaluation of Gitleaks outputs.

    Coordinates multiple specialized judges, each evaluating a specific
    dimension of secret detection quality.
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
        model: str = "opus",
        results_dir: Path | None = None,
        evaluation_mode: str | None = None,
    ):
        self.working_dir = working_dir or Path.cwd()
        self.model = model
        self.results_dir = results_dir or self.working_dir / "evaluation" / "llm" / "results"
        self.evaluation_mode = evaluation_mode  # "synthetic", "real_world", or None for auto
        self._judges: list[BaseJudge] = []

    def register_judge(self, judge: BaseJudge) -> None:
        """Register a judge for evaluation."""
        self._judges.append(judge)

    def register_all_judges(self) -> None:
        """Register all available judges."""
        from .judges.detection_accuracy import DetectionAccuracyJudge
        from .judges.false_positive import FalsePositiveJudge
        from .judges.secret_coverage import SecretCoverageJudge
        from .judges.severity_classification import SeverityClassificationJudge

        judges = [
            DetectionAccuracyJudge(
                model=self.model,
                working_dir=self.working_dir,
                evaluation_mode=self.evaluation_mode,
            ),
            FalsePositiveJudge(
                model=self.model,
                working_dir=self.working_dir,
                evaluation_mode=self.evaluation_mode,
            ),
            SecretCoverageJudge(
                model=self.model,
                working_dir=self.working_dir,
                evaluation_mode=self.evaluation_mode,
            ),
            SeverityClassificationJudge(
                model=self.model,
                working_dir=self.working_dir,
                evaluation_mode=self.evaluation_mode,
            ),
        ]

        for judge in judges:
            self.register_judge(judge)

    def register_focused_judges(self) -> None:
        """Register only the most important judges for quick evaluation."""
        from .judges.detection_accuracy import DetectionAccuracyJudge
        from .judges.false_positive import FalsePositiveJudge

        judges = [
            DetectionAccuracyJudge(
                model=self.model,
                working_dir=self.working_dir,
                evaluation_mode=self.evaluation_mode,
            ),
            FalsePositiveJudge(
                model=self.model,
                working_dir=self.working_dir,
                evaluation_mode=self.evaluation_mode,
            ),
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
        )

    def compute_combined_score(
        self,
        llm_result: EvaluationResult,
        programmatic_score: float,
    ) -> EvaluationResult:
        """Compute combined score from LLM and programmatic evaluations."""
        combined = (
            programmatic_score * self.PROGRAMMATIC_WEIGHT
            + llm_result.total_score * self.LLM_WEIGHT
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
        output_file = self.results_dir / f"{result.run_id}.json"
        output_file.write_text(result.to_json())
        return output_file

    def generate_markdown_report(self, result: EvaluationResult) -> str:
        """Generate a markdown report from evaluation results."""
        lines = [
            "# Gitleaks LLM Evaluation Report",
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

        lines.extend(
            [
                f"**Decision:** {result.decision}",
                "",
                "---",
                "",
                "## Dimension Scores",
                "",
                "| Dimension | Score | Weight | Weighted | Confidence |",
                "|-----------|-------|--------|----------|------------|",
            ]
        )

        for dim in result.dimensions:
            lines.append(
                f"| {dim.name} | {dim.score}/5 | {dim.weight:.0%} | "
                f"{dim.weighted_score:.2f} | {dim.confidence:.2f} |"
            )

        lines.extend(
            [
                "",
                "---",
                "",
                "## Detailed Results",
                "",
            ]
        )

        for dim in result.dimensions:
            lines.extend(
                [
                    f"### {dim.name}",
                    "",
                    f"**Score:** {dim.score}/5",
                    f"**Weight:** {dim.weight:.0%}",
                    f"**Confidence:** {dim.confidence:.2f}",
                    "",
                ]
            )

            if not dim.ground_truth_passed:
                lines.extend(
                    [
                        "**Ground Truth Assertions Failed:**",
                        "",
                    ]
                )
                for failure in dim.ground_truth_failures:
                    lines.append(f"- {failure}")
                lines.append("")

            if dim.sub_scores:
                lines.extend(
                    [
                        "**Sub-Scores:**",
                        "",
                    ]
                )
                for sub, score in dim.sub_scores.items():
                    lines.append(f"- {sub}: {score}/5")
                lines.append("")

            lines.extend(
                [
                    "**Reasoning:**",
                    "",
                    dim.reasoning,
                    "",
                ]
            )

            if dim.evidence_cited:
                lines.extend(
                    [
                        "**Evidence Cited:**",
                        "",
                    ]
                )
                for ev in dim.evidence_cited:
                    lines.append(f"- {ev}")
                lines.append("")

            if dim.recommendations:
                lines.extend(
                    [
                        "**Recommendations:**",
                        "",
                    ]
                )
                for rec in dim.recommendations:
                    lines.append(f"- {rec}")
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)


def main():
    """Main entry point for LLM evaluation."""
    import argparse

    parser = argparse.ArgumentParser(description="Run LLM evaluation for poc-gitleaks")
    parser.add_argument(
        "--model",
        default="opus",
        choices=["opus", "opus-4.5", "sonnet", "haiku"],
        help="Model to use for evaluation (default: opus)",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Generate markdown report",
    )
    parser.add_argument(
        "--working-dir",
        type=Path,
        default=None,
        help="Working directory (default: current)",
    )
    parser.add_argument(
        "--programmatic-results",
        type=Path,
        help="Path to programmatic evaluation JSON (evaluation_report.json)",
    )
    parser.add_argument(
        "--evaluation-mode",
        choices=["synthetic", "real_world", "auto"],
        default="auto",
        help="Evaluation mode: 'synthetic' for ground-truth repos, 'real_world' for production repos, 'auto' for auto-detect (default: auto)",
    )

    args = parser.parse_args()

    working_dir = args.working_dir or Path(__file__).parent.parent.parent

    # Handle evaluation mode
    evaluation_mode = None if args.evaluation_mode == "auto" else args.evaluation_mode

    print("LLM Evaluation for poc-gitleaks")
    print(f"Model: {args.model}")
    print(f"Working directory: {working_dir}")
    print(f"Evaluation mode: {args.evaluation_mode}")
    print("=" * 60)
    print()

    evaluator = LLMEvaluator(
        working_dir=working_dir,
        model=args.model,
        evaluation_mode=evaluation_mode,
    )
    evaluator.register_all_judges()

    print(f"Running {len(evaluator._judges)} judges...")
    print()

    result = evaluator.evaluate()

    # Load programmatic results and attach to result
    if args.programmatic_results and args.programmatic_results.exists():
        prog_data = json.loads(args.programmatic_results.read_text())
        summary = prog_data.get("summary", {})
        # Score may be at root level or in summary section
        prog_score_raw = prog_data.get("score") or summary.get("score", 0.0)
        prog_decision = prog_data.get("decision") or summary.get("decision", "UNKNOWN")
        result.programmatic_input = ProgrammaticInput(
            file=str(args.programmatic_results),
            decision=prog_decision,
            score=prog_score_raw,
            checks_passed=summary.get("passed", 0),
            checks_failed=summary.get("failed", 0),
        )
        # Compute combined score if programmatic results available
        prog_score = prog_score_raw * 5.0  # Convert 0-1 to 0-5
        result = evaluator.compute_combined_score(result, prog_score)

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total Score: {result.total_score:.2f}")
    print(f"Decision: {result.decision}")
    print()

    # Save results
    output_path = evaluator.save_results(result)
    print(f"Results saved to: {output_path}")

    if args.markdown:
        md_report = evaluator.generate_markdown_report(result)
        md_path = output_path.with_suffix(".md")
        md_path.write_text(md_report)
        print(f"Markdown report saved to: {md_path}")


if __name__ == "__main__":
    main()
