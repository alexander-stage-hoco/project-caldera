"""LLM Evaluation Orchestrator for SonarQube.

Coordinates multiple LLM judges to produce a comprehensive qualitative
evaluation of SonarQube static analysis outputs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from shared.evaluation import (
    LLMEvaluatorBase,
    ProgrammaticInput,
)

from .judges.base import BaseJudge, JudgeResult


class LLMEvaluator(LLMEvaluatorBase):
    """Orchestrates LLM-based evaluation of SonarQube outputs.

    Coordinates multiple specialized judges, each evaluating a specific
    dimension of static analysis quality.
    """

    def __init__(
        self,
        working_dir: Path | None = None,
        model: str = "opus-4.5",
        results_dir: Path | None = None,
        analysis_path: Path | None = None,
    ):
        super().__init__(working_dir=working_dir, model=model, results_dir=results_dir)
        self.analysis_path = analysis_path or self.working_dir / "output" / "runs" / "sonarqube_analysis.json"

    def register_all_judges(self) -> None:
        """Register all SonarQube judges."""
        from .judges.issue_accuracy import IssueAccuracyJudge
        from .judges.coverage_completeness import CoverageCompletenessJudge
        from .judges.actionability import ActionabilityJudge

        judges = [
            IssueAccuracyJudge(model=self.model, working_dir=self.working_dir, analysis_path=self.analysis_path),
            CoverageCompletenessJudge(model=self.model, working_dir=self.working_dir, analysis_path=self.analysis_path),
            ActionabilityJudge(model=self.model, working_dir=self.working_dir, analysis_path=self.analysis_path),
        ]

        for judge in judges:
            self.register_judge(judge)

    def register_focused_judges(self) -> None:
        """Register only the most critical judges for quick evaluation."""
        from .judges.issue_accuracy import IssueAccuracyJudge

        judges = [
            IssueAccuracyJudge(model=self.model, working_dir=self.working_dir, analysis_path=self.analysis_path),
        ]

        for judge in judges:
            self.register_judge(judge)

    def compute_combined_score(self, llm_result, programmatic_score: float):
        """Override to normalize programmatic score from 0-1 to 1-5 scale."""
        prog_normalized = 1 + (programmatic_score * 4)
        return super().compute_combined_score(llm_result, prog_normalized)


def main():
    """CLI entry point for LLM evaluation."""
    parser = argparse.ArgumentParser(
        description="Run LLM evaluation on SonarQube outputs"
    )
    parser.add_argument(
        "--working-dir",
        type=Path,
        default=Path.cwd(),
        help="Working directory containing analysis outputs",
    )
    parser.add_argument(
        "--analysis",
        type=Path,
        help="Path to the sonarqube_analysis.json file",
    )
    parser.add_argument(
        "--model",
        default="opus-4.5",
        choices=["opus", "opus-4.5", "sonnet", "haiku"],
        help="Claude model to use for evaluation",
    )
    parser.add_argument(
        "--focused",
        action="store_true",
        help="Run only focused judges (issue accuracy)",
    )
    parser.add_argument(
        "--no-assertions",
        action="store_true",
        help="Skip ground truth assertions",
    )
    parser.add_argument(
        "--programmatic-score",
        type=float,
        help="Programmatic score (0-1) to combine with LLM score",
    )
    parser.add_argument(
        "--programmatic-results",
        type=Path,
        help="Path to programmatic evaluation JSON (evaluation_report.json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for results JSON",
    )

    args = parser.parse_args()

    # Determine analysis path
    analysis_path = args.analysis
    if analysis_path is None:
        analysis_path = args.working_dir / "output" / "runs" / "sonarqube_analysis.json"

    # Create evaluator
    evaluator = LLMEvaluator(
        working_dir=args.working_dir,
        model=args.model,
        analysis_path=analysis_path,
    )

    # Register judges
    if args.focused:
        evaluator.register_focused_judges()
    else:
        evaluator.register_all_judges()

    # Run evaluation
    print(f"\n{'='*60}")
    print("LLM Evaluation - SonarQube Static Analysis")
    print(f"{'='*60}\n")

    result = evaluator.evaluate(run_assertions=not args.no_assertions)

    # Load programmatic results and attach to result
    programmatic_score = args.programmatic_score
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
        # Use programmatic score from file if not explicitly provided
        if programmatic_score is None:
            programmatic_score = prog_data.get("score", 0.0)

    # Combine with programmatic score if provided
    if programmatic_score is not None:
        result = evaluator.compute_combined_score(result, programmatic_score)

    # Print summary
    print(f"\n{'='*60}")
    print("EVALUATION SUMMARY")
    print(f"{'='*60}\n")
    print(f"Total LLM Score: {result.total_score:.2f}/5.0")
    print(f"Average Confidence: {result.average_confidence:.2f}")
    if result.combined_score:
        print(f"Combined Score: {result.combined_score:.2f}/5.0")
    print(f"Decision: {result.decision}")
    print()

    # Save results
    if args.output:
        args.output.write_text(result.to_json())
        print(f"Results saved to: {args.output}")
    else:
        output_file = evaluator.save_results(result)
        print(f"Results saved to: {output_file}")

    # Generate and save markdown report
    report = evaluator.generate_markdown_report(result, "LLM Evaluation Report - SonarQube")
    report_file = evaluator.results_dir / f"{result.run_id}.md"
    report_file.write_text(report)
    print(f"Report saved to: {report_file}")


if __name__ == "__main__":
    main()
