"""LLM Evaluation Orchestrator for scancode license analysis."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
    programmatic_score: float | None = None
    combined_score: float | None = None
    programmatic_input: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "model": self.model,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "score": self.total_score,  # compliance expects 'score' not 'total_score'
            "total_score": self.total_score,
            "average_confidence": self.average_confidence,
            "decision": self.decision,
            "programmatic_score": self.programmatic_score,
            "combined_score": self.combined_score,
            "programmatic_input": self.programmatic_input or {},
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class LLMEvaluator:
    """Orchestrates LLM-based evaluation of scancode outputs."""

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
        from .judges.accuracy_judge import LicenseAccuracyJudge
        from .judges.actionability_judge import ActionabilityJudge
        from .judges.coverage_judge import LicenseCoverageJudge
        from .judges.risk_classification_judge import RiskClassificationJudge

        judges = [
            LicenseAccuracyJudge(model=self.model, working_dir=self.working_dir),
            LicenseCoverageJudge(model=self.model, working_dir=self.working_dir),
            ActionabilityJudge(model=self.model, working_dir=self.working_dir),
            RiskClassificationJudge(model=self.model, working_dir=self.working_dir),
        ]

        for judge in judges:
            self.register_judge(judge)

    def _load_programmatic_input(self) -> dict[str, Any]:
        """Load programmatic evaluation results for inclusion in LLM evaluation."""
        prog_path = self.working_dir / "evaluation" / "results" / "evaluation_report.json"
        if prog_path.exists():
            try:
                data = json.loads(prog_path.read_text())
                # Add file field for compliance
                data["file"] = str(prog_path.relative_to(self.working_dir))
                return data
            except (json.JSONDecodeError, OSError):
                pass
        return {"file": "evaluation/results/evaluation_report.json", "decision": "UNKNOWN", "score": 0.0}

    def evaluate(self, run_assertions: bool = True) -> EvaluationResult:
        """Run evaluation with all registered judges."""
        run_id = f"llm-eval-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        timestamp = datetime.now(timezone.utc).isoformat()

        # Load programmatic evaluation for inclusion
        programmatic_input = self._load_programmatic_input()

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

        total_score = weighted_sum / total_weight if total_weight else 0.0
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
            programmatic_input=programmatic_input,
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
        return llm_result

    def save_results(self, result: EvaluationResult) -> Path:
        """Save evaluation results to JSON file."""
        self.results_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.results_dir / f"{result.run_id}.json"
        output_path.write_text(result.to_json())
        return output_path

    def generate_markdown_report(self, result: EvaluationResult) -> str:
        """Generate a markdown summary report."""
        lines = [
            "# LLM Evaluation Report",
            "",
            f"- Run ID: {result.run_id}",
            f"- Timestamp: {result.timestamp}",
            f"- Model: {result.model}",
            f"- Total Score: {result.total_score:.2f}",
            f"- Decision: {result.decision}",
            "",
            "## Dimension Scores",
            "",
        ]

        for dim in result.dimensions:
            lines.extend(
                [
                    f"### {dim.name}",
                    "",
                    f"- Score: {dim.score}/5",
                    f"- Confidence: {dim.confidence:.2f}",
                    f"- Weight: {dim.weight:.2f}",
                    "",
                    f"Reasoning: {dim.reasoning}",
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


def main() -> None:
    """Main entry point for LLM evaluation."""
    import argparse

    parser = argparse.ArgumentParser(description="Run LLM evaluation for scancode")
    parser.add_argument(
        "--model",
        default="opus",
        choices=["opus", "sonnet", "haiku"],
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

    args = parser.parse_args()

    working_dir = args.working_dir or Path(__file__).parent.parent.parent

    print("LLM Evaluation for scancode")
    print(f"Model: {args.model}")
    print(f"Working directory: {working_dir}")
    print("=" * 60)
    print()

    evaluator = LLMEvaluator(working_dir=working_dir, model=args.model)
    evaluator.register_all_judges()

    print(f"Running {len(evaluator._judges)} judges...")
    print()

    result = evaluator.evaluate()

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total Score: {result.total_score:.2f}")
    print(f"Decision: {result.decision}")
    print()

    output_path = evaluator.save_results(result)
    print(f"Results saved to: {output_path}")

    if args.markdown:
        md_report = evaluator.generate_markdown_report(result)
        md_path = output_path.with_suffix(".md")
        md_path.write_text(md_report)
        print(f"Markdown report saved to: {md_path}")


if __name__ == "__main__":
    main()
