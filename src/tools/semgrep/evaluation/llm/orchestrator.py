"""LLM Evaluation Orchestrator for Semgrep PoC.

Coordinates multiple LLM judges to produce a comprehensive qualitative
evaluation of Semgrep outputs.
"""

from __future__ import annotations

import json
from pathlib import Path

from shared.evaluation import (
    LLMEvaluatorBase,
    DimensionResult,
    ProgrammaticInput,
    EvaluationResult,
    require_observability,
)

from .judges.base import BaseJudge, JudgeResult


class LLMEvaluator(LLMEvaluatorBase):
    """Orchestrates LLM-based evaluation of Semgrep outputs.

    Coordinates multiple specialized judges, each evaluating a specific
    dimension of output quality.
    """

    def register_all_judges(self) -> None:
        """Register all available judges."""
        from .judges.smell_accuracy import SmellAccuracyJudge
        from .judges.rule_coverage import RuleCoverageJudge
        from .judges.false_positive_rate import FalsePositiveRateJudge
        from .judges.actionability import ActionabilityJudge

        judges = [
            SmellAccuracyJudge(model=self.model, working_dir=self.working_dir),
            RuleCoverageJudge(model=self.model, working_dir=self.working_dir),
            FalsePositiveRateJudge(model=self.model, working_dir=self.working_dir),
            ActionabilityJudge(model=self.model, working_dir=self.working_dir),
        ]

        for judge in judges:
            self.register_judge(judge)

    def register_focused_judges(self) -> None:
        """Register only the most important judges for quick evaluation."""
        from .judges.smell_accuracy import SmellAccuracyJudge
        from .judges.rule_coverage import RuleCoverageJudge

        judges = [
            SmellAccuracyJudge(model=self.model, working_dir=self.working_dir),
            RuleCoverageJudge(model=self.model, working_dir=self.working_dir),
        ]

        for judge in judges:
            self.register_judge(judge)


def main():
    """Main entry point for LLM evaluation."""
    import argparse

    parser = argparse.ArgumentParser(description="Run LLM evaluation for poc-semgrep")
    parser.add_argument(
        "--model",
        default="opus-4.5",
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

    args = parser.parse_args()

    working_dir = args.working_dir or Path(__file__).parent.parent.parent

    print("LLM Evaluation for poc-semgrep")
    print(f"Model: {args.model}")
    print(f"Working directory: {working_dir}")
    print("=" * 60)
    print()

    evaluator = LLMEvaluator(working_dir=working_dir, model=args.model)
    evaluator.register_all_judges()

    print(f"Running {len(evaluator._judges)} judges...")
    print()

    result = evaluator.evaluate()

    # Load programmatic results and attach to result
    if args.programmatic_results and args.programmatic_results.exists():
        prog_data = json.loads(args.programmatic_results.read_text())
        summary = prog_data.get("summary", {})
        result.programmatic_input = ProgrammaticInput(
            file=str(args.programmatic_results),
            decision=prog_data.get("decision", "UNKNOWN"),
            score=prog_data.get("score", 0.0),
            checks_passed=summary.get("passed", 0),
            checks_failed=summary.get("failed", 0),
        )
        # Compute combined score if programmatic results available
        prog_score = prog_data.get("score", 0.0) * 5.0  # Convert 0-1 to 0-5
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
        md_report = evaluator.generate_markdown_report(result, "Semgrep LLM Evaluation Report")
        md_path = output_path.with_suffix(".md")
        md_path.write_text(md_report)
        print(f"Markdown report saved to: {md_path}")


if __name__ == "__main__":
    main()
