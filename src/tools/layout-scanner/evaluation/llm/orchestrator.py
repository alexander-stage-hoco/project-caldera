"""LLM Evaluation Orchestrator for Layout Scanner.

Coordinates multiple LLM judges to produce a comprehensive qualitative
evaluation of layout scanner outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from shared.evaluation import (
    LLMEvaluatorBase,
    ProgrammaticInput,
)


class LLMEvaluator(LLMEvaluatorBase):
    """Orchestrates LLM-based evaluation of layout scanner outputs.

    Coordinates multiple specialized judges, each evaluating a specific
    dimension of output quality.
    """

    def __init__(
        self,
        working_dir: Path | None = None,
        model: str = "sonnet",
        results_dir: Path | None = None,
        output_dir: Path | None = None,
    ):
        super().__init__(working_dir=working_dir, model=model, results_dir=results_dir)
        self.output_dir = output_dir or self.working_dir / "outputs"

    def register_all_judges(self) -> None:
        """Register all available judges."""
        from .judges.classification_reasoning import ClassificationReasoningJudge
        from .judges.directory_taxonomy import DirectoryTaxonomyJudge
        from .judges.hierarchy_consistency import HierarchyConsistencyJudge
        from .judges.language_detection import LanguageDetectionJudge

        judges = [
            ClassificationReasoningJudge(
                model=self.model, working_dir=self.working_dir, output_dir=self.output_dir
            ),
            DirectoryTaxonomyJudge(
                model=self.model, working_dir=self.working_dir, output_dir=self.output_dir
            ),
            HierarchyConsistencyJudge(
                model=self.model, working_dir=self.working_dir, output_dir=self.output_dir
            ),
            LanguageDetectionJudge(
                model=self.model, working_dir=self.working_dir, output_dir=self.output_dir
            ),
        ]

        for judge in judges:
            self.register_judge(judge)

    def register_focused_judges(self) -> None:
        """Register only the most important judges for quick evaluation."""
        from .judges.classification_reasoning import ClassificationReasoningJudge
        from .judges.hierarchy_consistency import HierarchyConsistencyJudge

        judges = [
            ClassificationReasoningJudge(
                model=self.model, working_dir=self.working_dir, output_dir=self.output_dir
            ),
            HierarchyConsistencyJudge(
                model=self.model, working_dir=self.working_dir, output_dir=self.output_dir
            ),
        ]

        for judge in judges:
            self.register_judge(judge)

    def save_results(self, result) -> Path:
        """Save evaluation results to file (override to also save 'latest')."""
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Save timestamped result
        output_file = self.results_dir / f"{result.run_id}.json"
        output_file.write_text(result.to_json())

        # Also save as latest
        latest_file = self.results_dir / "llm_evaluation.json"
        latest_file.write_text(result.to_json())

        return output_file


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
        "--analysis",
        type=Path,
        help="Path to analysis output file (e.g., outputs/<run-id>/output.json)",
    )

    parser.add_argument(
        "--model",
        type=str,
        default="opus-4.5",
        choices=["sonnet", "opus", "opus-4.5", "haiku"],
        help="Model to use for evaluation (default: opus-4.5)",
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
        "--programmatic-results",
        type=Path,
        help="Path to programmatic evaluation JSON (evaluation_report.json)",
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

    # Determine output_dir from --analysis if provided
    output_dir = None
    if parsed_args.analysis and parsed_args.analysis.exists():
        # If analysis points to a file, use its parent directory
        if parsed_args.analysis.is_file():
            output_dir = parsed_args.analysis.parent
        else:
            output_dir = parsed_args.analysis

    # Create evaluator
    evaluator = LLMEvaluator(
        working_dir=parsed_args.working_dir,
        model=parsed_args.model,
        output_dir=output_dir,
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

    # Load programmatic results and attach to result
    programmatic_score = parsed_args.programmatic_score
    if parsed_args.programmatic_results and parsed_args.programmatic_results.exists():
        prog_data = json.loads(parsed_args.programmatic_results.read_text())
        summary = prog_data.get("summary", {})
        result.programmatic_input = ProgrammaticInput(
            file=str(parsed_args.programmatic_results),
            decision=prog_data.get("decision", "UNKNOWN"),
            score=prog_data.get("score", 0.0),
            checks_passed=summary.get("passed", 0),
            checks_failed=summary.get("failed", 0),
        )
        # Use programmatic score from file if not explicitly provided
        if programmatic_score is None:
            programmatic_score = prog_data.get("score", 0.0) * 5.0  # Convert 0-1 to 0-5

    # Compute combined score if provided
    if programmatic_score is not None:
        result = evaluator.compute_combined_score(
            result, programmatic_score
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
        report = evaluator.generate_markdown_report(result, "LLM Evaluation Report - Layout Scanner")
        if parsed_args.output:
            report_path = parsed_args.output.with_suffix(".md")
        else:
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
    return 0 if result.decision in ("STRONG_PASS", "PASS", "WEAK_PASS") else 1


if __name__ == "__main__":
    sys.exit(main())
