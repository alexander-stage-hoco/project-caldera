"""LLM Evaluation Orchestrator for Gitleaks PoC.

Coordinates multiple LLM judges to produce a comprehensive qualitative
evaluation of Gitleaks secret detection outputs.
"""

from __future__ import annotations

import json
from pathlib import Path

from shared.evaluation import (
    LLMEvaluatorBase,
    ProgrammaticInput,
)

from .judges.base import BaseJudge, JudgeResult


class LLMEvaluator(LLMEvaluatorBase):
    """Orchestrates LLM-based evaluation of Gitleaks outputs.

    Coordinates multiple specialized judges, each evaluating a specific
    dimension of secret detection quality.
    """

    def __init__(
        self,
        working_dir: Path | None = None,
        model: str = "opus",
        results_dir: Path | None = None,
        evaluation_mode: str | None = None,
    ):
        super().__init__(working_dir=working_dir, model=model, results_dir=results_dir)
        self.evaluation_mode = evaluation_mode  # "synthetic", "real_world", or None for auto

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
        md_report = evaluator.generate_markdown_report(result, "Gitleaks LLM Evaluation Report")
        md_path = output_path.with_suffix(".md")
        md_path.write_text(md_report)
        print(f"Markdown report saved to: {md_path}")


if __name__ == "__main__":
    main()
