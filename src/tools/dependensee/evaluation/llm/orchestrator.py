"""LLM Evaluation Orchestrator for DependenSee.

Coordinates multiple LLM judges to produce a comprehensive qualitative
evaluation of DependenSee dependency analysis outputs.
"""

from __future__ import annotations

import json
from pathlib import Path

from shared.evaluation import (
    LLMEvaluatorBase,
    ProgrammaticInput,
    require_observability,
)

from .judges import (
    ProjectDetectionJudge,
    DependencyAccuracyJudge,
    GraphQualityJudge,
    CircularDetectionJudge,
)


class LLMEvaluator(LLMEvaluatorBase):
    """Orchestrates LLM-based evaluation of DependenSee outputs.

    Coordinates four specialized judges, each evaluating a specific
    dimension of dependency analysis quality:
    - project_detection (30%): All .NET projects discovered
    - dependency_accuracy (30%): References correctly captured
    - graph_quality (20%): Graph structure is complete and consistent
    - circular_detection (20%): Circular dependencies identified
    """

    def __init__(
        self,
        working_dir: Path | None = None,
        model: str = "opus-4.5",
        results_dir: Path | None = None,
        output_dir: Path | None = None,
    ):
        """Initialize the evaluator.

        Args:
            working_dir: Working directory containing analysis outputs.
            model: Claude model to use for evaluation.
            results_dir: Directory to save evaluation results.
            output_dir: Directory containing analysis output files.
        """
        super().__init__(working_dir=working_dir, model=model, results_dir=results_dir)
        self.output_dir = output_dir or self.working_dir / "outputs"

    def register_all_judges(self) -> None:
        """Register all available judges for comprehensive evaluation."""
        judges = [
            ProjectDetectionJudge(
                model=self.model,
                working_dir=self.working_dir,
                output_dir=self.output_dir,
            ),
            DependencyAccuracyJudge(
                model=self.model,
                working_dir=self.working_dir,
                output_dir=self.output_dir,
            ),
            GraphQualityJudge(
                model=self.model,
                working_dir=self.working_dir,
                output_dir=self.output_dir,
            ),
            CircularDetectionJudge(
                model=self.model,
                working_dir=self.working_dir,
                output_dir=self.output_dir,
            ),
        ]

        for judge in judges:
            self.register_judge(judge)

    def register_focused_judges(self) -> None:
        """Register only the most important judges for quick evaluation.

        Focuses on project detection and dependency accuracy (60% of total weight).
        """
        judges = [
            ProjectDetectionJudge(
                model=self.model,
                working_dir=self.working_dir,
                output_dir=self.output_dir,
            ),
            DependencyAccuracyJudge(
                model=self.model,
                working_dir=self.working_dir,
                output_dir=self.output_dir,
            ),
        ]

        for judge in judges:
            self.register_judge(judge)


def main():
    """Main entry point for LLM evaluation."""
    require_observability()
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Run LLM evaluation for dependensee")
    parser.add_argument(
        "results_dir",
        type=Path,
        nargs="?",
        default=None,
        help="Directory containing analysis outputs (default: working_dir/outputs)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file for results (default: evaluation/llm/results/<run-id>.json)",
    )
    parser.add_argument(
        "--model",
        default="opus-4.5",
        choices=["opus", "opus-4.5", "sonnet", "haiku"],
        help="Model to use for evaluation (default: opus-4.5)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds for LLM invocation (default: 300)",
    )
    parser.add_argument(
        "--focused",
        action="store_true",
        help="Run focused evaluation (2 judges instead of 4)",
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
        help="Working directory (default: tool directory)",
    )
    parser.add_argument(
        "--programmatic-results",
        type=Path,
        help="Path to programmatic evaluation JSON (evaluation_report.json)",
    )

    args = parser.parse_args()

    # Determine working directory
    working_dir = args.working_dir or Path(__file__).parent.parent.parent
    output_dir = args.results_dir or working_dir / "outputs"

    print("LLM Evaluation for dependensee")
    print(f"Model: {args.model}")
    print(f"Working directory: {working_dir}")
    print(f"Output directory: {output_dir}")
    print("=" * 60)
    print()

    # Create evaluator
    evaluator = LLMEvaluator(
        working_dir=working_dir,
        model=args.model,
        output_dir=output_dir,
    )

    # Register judges
    if args.focused:
        print("Running focused evaluation (2 judges)...")
        evaluator.register_focused_judges()
    else:
        print("Running full evaluation (4 judges)...")
        evaluator.register_all_judges()

    print(f"Registered {len(evaluator._judges)} judges")
    print()

    # Run evaluation
    result = evaluator.evaluate()

    # Load programmatic results if provided
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
        # Compute combined score (programmatic is 0-1, convert to 0-5)
        prog_score = prog_data.get("score", 0.0) * 5.0
        result = evaluator.compute_combined_score(result, prog_score)
    else:
        # Try to find programmatic results automatically
        default_prog_path = working_dir / "evaluation" / "results" / "evaluation_report.json"
        if default_prog_path.exists():
            prog_data = json.loads(default_prog_path.read_text())
            summary = prog_data.get("summary", {})
            result.programmatic_input = ProgrammaticInput(
                file=str(default_prog_path),
                decision=prog_data.get("decision", "UNKNOWN"),
                score=prog_data.get("score", 0.0),
                checks_passed=summary.get("passed", 0),
                checks_failed=summary.get("failed", 0),
            )
            prog_score = prog_data.get("score", 0.0) * 5.0
            result = evaluator.compute_combined_score(result, prog_score)

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total Score: {result.total_score:.2f}/5.0")
    print(f"Average Confidence: {result.average_confidence:.2f}")
    if result.combined_score is not None:
        print(f"Combined Score: {result.combined_score:.2f}/5.0")
    print(f"Decision: {result.decision}")
    print()

    # Save results
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result.to_json())
        output_path = args.output
    else:
        output_path = evaluator.save_results(result)

    print(f"Results saved to: {output_path}")

    # Generate markdown report if requested
    if args.markdown:
        md_report = evaluator.generate_markdown_report(result, "DependenSee LLM Evaluation Report")
        md_path = output_path.with_suffix(".md")
        md_path.write_text(md_report)
        print(f"Markdown report saved to: {md_path}")

    # Return exit code based on decision
    if result.decision in ("STRONG_PASS", "PASS"):
        return 0
    elif result.decision == "WEAK_PASS":
        return 0  # Still passing
    else:
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
