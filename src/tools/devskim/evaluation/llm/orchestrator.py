"""LLM Evaluation Orchestrator for DevSkim PoC.

Coordinates multiple LLM judges to produce a comprehensive qualitative
evaluation of DevSkim security scanning outputs.
"""

from __future__ import annotations

import json
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
class EvaluationResult:
    """Complete LLM evaluation result."""

    run_id: str
    timestamp: str
    model: str
    dimensions: list[DimensionResult]
    total_score: float
    average_confidence: float
    decision: str
    programmatic_input: dict[str, Any] | None = None
    combined_score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "model": self.model,
            # Include 'score' at root level for compliance scanner compatibility
            "score": self.total_score,
            "decision": self.decision,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "total_score": self.total_score,
            "average_confidence": self.average_confidence,
            "combined_score": self.combined_score,
        }
        # Include programmatic_input for compliance scanner
        if self.programmatic_input:
            result["programmatic_input"] = self.programmatic_input
        return result

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class LLMEvaluator:
    """Orchestrates LLM-based evaluation of DevSkim outputs.

    Coordinates multiple specialized judges, each evaluating a specific
    dimension of security scanning quality.
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
    ):
        self.working_dir = working_dir or Path.cwd()
        self.model = model
        self.results_dir = results_dir or self.working_dir / "evaluation" / "llm" / "results"
        self._judges: list[BaseJudge] = []

    def register_judge(self, judge: BaseJudge) -> None:
        """Register a judge for evaluation."""
        self._judges.append(judge)

    def register_all_judges(self) -> None:
        """Register all available judges."""
        from .judges.detection_accuracy import DetectionAccuracyJudge
        from .judges.severity_calibration import SeverityCalibrationJudge
        from .judges.rule_coverage import RuleCoverageJudge
        from .judges.security_focus import SecurityFocusJudge

        judges = [
            DetectionAccuracyJudge(model=self.model, working_dir=self.working_dir),
            SeverityCalibrationJudge(model=self.model, working_dir=self.working_dir),
            RuleCoverageJudge(model=self.model, working_dir=self.working_dir),
            SecurityFocusJudge(model=self.model, working_dir=self.working_dir),
        ]

        for judge in judges:
            self.register_judge(judge)

    def register_focused_judges(self) -> None:
        """Register only the most important judges for quick evaluation."""
        from .judges.detection_accuracy import DetectionAccuracyJudge
        from .judges.rule_coverage import RuleCoverageJudge

        judges = [
            DetectionAccuracyJudge(model=self.model, working_dir=self.working_dir),
            RuleCoverageJudge(model=self.model, working_dir=self.working_dir),
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

            gt_passed = True
            gt_failures: list[str] = []
            if run_assertions:
                gt_passed, gt_failures = judge.run_ground_truth_assertions()
                if not gt_passed:
                    print(f"  Ground truth assertions failed: {len(gt_failures)} failures")

            result = judge.evaluate()

            if not gt_passed:
                result.score = min(result.score, 2)

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

        if total_weight > 0:
            total_score = weighted_sum / total_weight
        else:
            total_score = 0.0

        avg_confidence = confidence_sum / len(self._judges) if self._judges else 0.0

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
        programmatic_input: dict[str, Any],
    ) -> EvaluationResult:
        """Compute combined score from LLM and programmatic evaluations."""
        programmatic_score = programmatic_input.get("score", 0.0)
        # Normalize programmatic score to 0-5 scale if needed
        if programmatic_score <= 1.0:
            programmatic_score = programmatic_score * 5.0

        combined = (
            programmatic_score * self.PROGRAMMATIC_WEIGHT
            + llm_result.total_score * self.LLM_WEIGHT
        )

        llm_result.programmatic_input = programmatic_input
        llm_result.combined_score = combined

        if combined >= self.STRONG_PASS_THRESHOLD:
            llm_result.decision = "STRONG_PASS"
        elif combined >= self.PASS_THRESHOLD:
            llm_result.decision = "PASS"
        elif combined >= self.WEAK_PASS_THRESHOLD:
            llm_result.decision = "WEAK_PASS"
        else:
            llm_result.decision = "FAIL"

        return llm_result

    def save_results(self, result: EvaluationResult, use_standard_path: bool = False) -> Path:
        """Save evaluation results to file.

        Args:
            result: The evaluation result to save.
            use_standard_path: If True, save to evaluation/results/llm_evaluation.json
                for compliance scanner compatibility.
        """
        if use_standard_path:
            # Save to standardized path for compliance scanner
            output_file = self.working_dir / "evaluation" / "results" / "llm_evaluation.json"
        else:
            output_file = self.results_dir / f"{result.run_id}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(result.to_json())
        return output_file

    def generate_markdown_report(self, result: EvaluationResult) -> str:
        """Generate a markdown report from evaluation results."""
        lines = [
            "# DevSkim LLM Evaluation Report",
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


def load_programmatic_results(working_dir: Path) -> dict[str, Any] | None:
    """Load programmatic evaluation results."""
    prog_path = working_dir / "evaluation" / "results" / "evaluation_report.json"
    if not prog_path.exists():
        return None
    try:
        data = json.loads(prog_path.read_text())
        return {
            "file": str(prog_path),
            "decision": data.get("decision", data.get("summary", {}).get("decision")),
            "score": data.get("score", data.get("summary", {}).get("score", 0.0)),
            "passed": data.get("summary", {}).get("passed", 0),
            "failed": data.get("summary", {}).get("failed", 0),
            "total": data.get("summary", {}).get("total", 0),
        }
    except (json.JSONDecodeError, KeyError):
        return None


def main():
    """Main entry point for LLM evaluation."""
    require_observability()
    import argparse

    parser = argparse.ArgumentParser(description="Run LLM evaluation for DevSkim")
    parser.add_argument(
        "--model",
        default="opus",
        choices=["opus", "sonnet", "haiku", "opus-4.5"],
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
        "--focused",
        action="store_true",
        help="Run focused evaluation (fewer judges, faster)",
    )

    args = parser.parse_args()

    working_dir = args.working_dir or Path(__file__).parent.parent.parent

    print("LLM Evaluation for DevSkim")
    print(f"Model: {args.model}")
    print(f"Working directory: {working_dir}")
    print("=" * 60)
    print()

    # Load programmatic results
    programmatic_input = load_programmatic_results(working_dir)
    if programmatic_input:
        print(f"Loaded programmatic results: {programmatic_input['decision']} ({programmatic_input['score']:.4f})")
    else:
        print("Warning: No programmatic evaluation results found")
    print()

    evaluator = LLMEvaluator(working_dir=working_dir, model=args.model)

    if args.focused:
        evaluator.register_focused_judges()
    else:
        evaluator.register_all_judges()

    print(f"Running {len(evaluator._judges)} judges...")
    print()

    result = evaluator.evaluate()

    # Compute combined score if programmatic results available
    if programmatic_input:
        result = evaluator.compute_combined_score(result, programmatic_input)
        print()
        print("=" * 60)
        print("COMBINED RESULTS")
        print("=" * 60)
        print(f"LLM Score: {result.total_score:.2f}")
        print(f"Programmatic Score: {programmatic_input['score']:.4f}")
        print(f"Combined Score: {result.combined_score:.2f}")
        print(f"Decision: {result.decision}")
    else:
        print()
        print("=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(f"Total Score: {result.total_score:.2f}")
        print(f"Decision: {result.decision}")
    print()

    # Save to both run-specific path and standard path
    run_output_path = evaluator.save_results(result, use_standard_path=False)
    print(f"Results saved to: {run_output_path}")

    std_output_path = evaluator.save_results(result, use_standard_path=True)
    print(f"Compliance-compatible results saved to: {std_output_path}")

    if args.markdown:
        md_report = evaluator.generate_markdown_report(result)
        md_path = run_output_path.with_suffix(".md")
        md_path.write_text(md_report)
        print(f"Markdown report saved to: {md_path}")


if __name__ == "__main__":
    main()
