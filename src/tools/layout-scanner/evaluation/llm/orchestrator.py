"""LLM Evaluation Orchestrator for Layout Scanner.

Coordinates multiple LLM judges to produce a comprehensive qualitative
evaluation of layout scanner outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "model": self.model,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "total_score": self.total_score,
            "average_confidence": self.average_confidence,
            "decision": self.decision,
            "programmatic_score": self.programmatic_score,
            "combined_score": self.combined_score,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class LLMEvaluator:
    """Orchestrates LLM-based evaluation of layout scanner outputs.

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
        model: str = "sonnet",
        results_dir: Path | None = None,
    ):
        self.working_dir = working_dir or Path.cwd()
        self.model = model
        self.results_dir = (
            results_dir or self.working_dir / "evaluation" / "llm" / "results"
        )
        self._judges: list = []

    def register_judge(self, judge) -> None:
        """Register a judge for evaluation."""
        self._judges.append(judge)

    def register_all_judges(self) -> None:
        """Register all available judges."""
        from .judges.classification_reasoning import ClassificationReasoningJudge
        from .judges.directory_taxonomy import DirectoryTaxonomyJudge
        from .judges.hierarchy_consistency import HierarchyConsistencyJudge
        from .judges.language_detection import LanguageDetectionJudge

        judges = [
            ClassificationReasoningJudge(
                model=self.model, working_dir=self.working_dir
            ),
            DirectoryTaxonomyJudge(model=self.model, working_dir=self.working_dir),
            HierarchyConsistencyJudge(model=self.model, working_dir=self.working_dir),
            LanguageDetectionJudge(model=self.model, working_dir=self.working_dir),
        ]

        for judge in judges:
            self.register_judge(judge)

    def register_focused_judges(self) -> None:
        """Register only the most important judges for quick evaluation."""
        from .judges.classification_reasoning import ClassificationReasoningJudge
        from .judges.hierarchy_consistency import HierarchyConsistencyJudge

        judges = [
            ClassificationReasoningJudge(
                model=self.model, working_dir=self.working_dir
            ),
            HierarchyConsistencyJudge(model=self.model, working_dir=self.working_dir),
        ]

        for judge in judges:
            self.register_judge(judge)

    def evaluate(self, run_assertions: bool = True) -> EvaluationResult:
        """Run evaluation with all registered judges."""
        run_id = f"llm-eval-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        timestamp = datetime.now(timezone.utc).isoformat()

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
                    print(
                        f"  Ground truth assertions failed: {len(gt_failures)} failures"
                    )
                    for failure in gt_failures[:3]:
                        print(f"    - {failure}")

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
            total_score=round(total_score, 2),
            average_confidence=round(avg_confidence, 2),
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
        llm_result.combined_score = round(combined, 2)

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

        # Save timestamped result
        output_file = self.results_dir / f"{result.run_id}.json"
        output_file.write_text(result.to_json())

        # Also save as latest
        latest_file = self.results_dir / "llm_evaluation.json"
        latest_file.write_text(result.to_json())

        return output_file

    def generate_markdown_report(self, result: EvaluationResult) -> str:
        """Generate a markdown report from evaluation results."""
        lines = [
            "# LLM Evaluation Report - Layout Scanner",
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
            lines.append(
                f"**Programmatic Score:** {result.programmatic_score:.2f}/5.0"
            )

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
                "| Dimension | Score | Weight | Weighted | Confidence | GT Passed |",
                "|-----------|-------|--------|----------|------------|-----------|",
            ]
        )

        for dim in result.dimensions:
            gt_status = "Yes" if dim.ground_truth_passed else "No"
            lines.append(
                f"| {dim.name} | {dim.score}/5 | {dim.weight:.0%} | "
                f"{dim.weighted_score:.2f} | {dim.confidence:.2f} | {gt_status} |"
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
                for failure in dim.ground_truth_failures[:5]:
                    lines.append(f"- {failure}")
                if len(dim.ground_truth_failures) > 5:
                    lines.append(
                        f"- ... and {len(dim.ground_truth_failures) - 5} more"
                    )
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
                    dim.reasoning[:500] + ("..." if len(dim.reasoning) > 500 else ""),
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
                for ev in dim.evidence_cited[:5]:
                    lines.append(f"- {ev}")
                lines.append("")

            if dim.recommendations:
                lines.extend(
                    [
                        "**Recommendations:**",
                        "",
                    ]
                )
                for rec in dim.recommendations[:5]:
                    lines.append(f"- {rec}")
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)


def main(args: list[str] | None = None) -> int:
    """Main entry point for LLM evaluation."""
    parser = argparse.ArgumentParser(
        description="Run LLM evaluation for Layout Scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--working-dir",
        type=Path,
        default=Path.cwd(),
        help="Working directory (default: current directory)",
    )

    parser.add_argument(
        "--model",
        type=str,
        default="sonnet",
        choices=["sonnet", "opus", "haiku"],
        help="Model to use for evaluation (default: sonnet)",
    )

    parser.add_argument(
        "--focused",
        action="store_true",
        help="Run focused evaluation (fewer judges, faster)",
    )

    parser.add_argument(
        "--no-assertions",
        action="store_true",
        help="Skip ground truth assertions",
    )

    parser.add_argument(
        "--programmatic-score",
        type=float,
        help="Programmatic score to combine with LLM score",
    )

    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output file for results (default: evaluation/llm/results/)",
    )

    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "markdown", "both"],
        default="both",
        help="Output format (default: both)",
    )

    parsed_args = parser.parse_args(args)

    # Create evaluator
    evaluator = LLMEvaluator(
        working_dir=parsed_args.working_dir,
        model=parsed_args.model,
    )

    # Register judges
    if parsed_args.focused:
        print("Running focused evaluation (2 judges)...")
        evaluator.register_focused_judges()
    else:
        print("Running full evaluation (4 judges)...")
        evaluator.register_all_judges()

    # Run evaluation
    result = evaluator.evaluate(run_assertions=not parsed_args.no_assertions)

    # Compute combined score if provided
    if parsed_args.programmatic_score is not None:
        result = evaluator.compute_combined_score(
            result, parsed_args.programmatic_score
        )

    # Save results
    if parsed_args.output:
        output_path = parsed_args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_path = evaluator.save_results(result)
        print(f"\nResults saved to {output_path}")

    # Output based on format
    if parsed_args.format in ("json", "both"):
        if parsed_args.output:
            parsed_args.output.write_text(result.to_json())
        print("\n" + "=" * 60)
        print("JSON Result:")
        print("=" * 60)
        print(result.to_json())

    if parsed_args.format in ("markdown", "both"):
        report = evaluator.generate_markdown_report(result)
        report_path = evaluator.results_dir / "llm_evaluation_report.md"
        report_path.write_text(report)
        print(f"\nMarkdown report saved to {report_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("Evaluation Summary")
    print("=" * 60)
    print(f"Total Score: {result.total_score:.2f}/5.0")
    print(f"Decision: {result.decision}")
    print(f"Average Confidence: {result.average_confidence:.2f}")

    if result.combined_score is not None:
        print(f"Combined Score: {result.combined_score:.2f}/5.0")

    # Return exit code based on decision
    return 0 if result.decision in ("STRONG_PASS", "PASS") else 1


if __name__ == "__main__":
    sys.exit(main())
