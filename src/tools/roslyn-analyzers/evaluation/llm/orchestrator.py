"""LLM Evaluation Orchestrator for Roslyn Analyzers PoC.

Coordinates multiple LLM judges to produce a comprehensive qualitative
evaluation of Roslyn Analyzers static analysis outputs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from shared.evaluation import (
    LLMEvaluatorBase,
    ProgrammaticInput,
    require_observability,
)

from .judges.base import BaseJudge, JudgeResult


class LLMEvaluator(LLMEvaluatorBase):
    """Orchestrates LLM-based evaluation of Roslyn Analyzers outputs.

    Coordinates multiple specialized judges, each evaluating a specific
    dimension of .NET static analysis quality.
    """

    def __init__(
        self,
        working_dir: Path | None = None,
        model: str = "opus-4.5",
        results_dir: Path | None = None,
        analysis_path: Path | None = None,
    ):
        super().__init__(working_dir=working_dir, model=model, results_dir=results_dir)
        self.analysis_path = analysis_path or self.working_dir / "output" / "runs" / "roslyn_analysis.json"

    def register_all_judges(self) -> None:
        """Register all 5 Roslyn Analyzers judges."""
        from .judges.security_detection import SecurityDetectionJudge
        from .judges.design_analysis import DesignAnalysisJudge
        from .judges.resource_management import ResourceManagementJudge
        from .judges.overall_quality import OverallQualityJudge
        from .judges.integration_fit import IntegrationFitJudge

        judges = [
            SecurityDetectionJudge(model=self.model, working_dir=self.working_dir, analysis_path=self.analysis_path),
            DesignAnalysisJudge(model=self.model, working_dir=self.working_dir, analysis_path=self.analysis_path),
            ResourceManagementJudge(model=self.model, working_dir=self.working_dir, analysis_path=self.analysis_path),
            OverallQualityJudge(model=self.model, working_dir=self.working_dir, analysis_path=self.analysis_path),
            IntegrationFitJudge(model=self.model, working_dir=self.working_dir, analysis_path=self.analysis_path),
        ]

        for judge in judges:
            self.register_judge(judge)

    def register_focused_judges(self) -> None:
        """Register only the most critical judges for quick evaluation."""
        from .judges.security_detection import SecurityDetectionJudge
        from .judges.overall_quality import OverallQualityJudge

        judges = [
            SecurityDetectionJudge(model=self.model, working_dir=self.working_dir, analysis_path=self.analysis_path),
            OverallQualityJudge(model=self.model, working_dir=self.working_dir, analysis_path=self.analysis_path),
        ]

        for judge in judges:
            self.register_judge(judge)

    def register_judges_by_name(self, names: list[str]) -> None:
        """Register judges by their dimension names."""
        from .judges.security_detection import SecurityDetectionJudge
        from .judges.design_analysis import DesignAnalysisJudge
        from .judges.resource_management import ResourceManagementJudge
        from .judges.overall_quality import OverallQualityJudge
        from .judges.integration_fit import IntegrationFitJudge

        judge_map = {
            "security_detection": SecurityDetectionJudge,
            "design_analysis": DesignAnalysisJudge,
            "resource_management": ResourceManagementJudge,
            "overall_quality": OverallQualityJudge,
            "integration_fit": IntegrationFitJudge,
        }

        for name in names:
            name = name.strip()
            if name in judge_map:
                judge = judge_map[name](
                    model=self.model,
                    working_dir=self.working_dir,
                    analysis_path=self.analysis_path,
                )
                self.register_judge(judge)
            else:
                print(f"Warning: Unknown judge '{name}'. Available: {', '.join(judge_map.keys())}")

    def compute_combined_score(self, llm_result, programmatic_score: float):
        """Override to normalize programmatic score from 0-1 to 1-5 scale."""
        # Normalize programmatic score from 0-1 to 1-5 scale
        prog_normalized = 1 + (programmatic_score * 4)
        return super().compute_combined_score(llm_result, prog_normalized)


def main():
    """CLI entry point for LLM evaluation."""
    require_observability()
    parser = argparse.ArgumentParser(
        description="Run LLM evaluation on Roslyn Analyzers outputs"
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
        help="Path to the roslyn_analysis.json file",
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
        help="Run only focused judges (security + overall quality)",
    )
    parser.add_argument(
        "--judges",
        type=str,
        help="Comma-separated list of judge names to run",
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
        help="Path to programmatic evaluation JSON to extract score from",
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
        analysis_path = args.working_dir / "output" / "runs" / "roslyn_analysis.json"

    # Create evaluator
    evaluator = LLMEvaluator(
        working_dir=args.working_dir,
        model=args.model,
        analysis_path=analysis_path,
    )

    # Load programmatic score from results file if provided
    programmatic_score = args.programmatic_score
    programmatic_input = None
    if args.programmatic_results and args.programmatic_results.exists():
        prog_data = json.loads(args.programmatic_results.read_text())
        summary = prog_data.get("summary", {})
        programmatic_input = ProgrammaticInput(
            file=str(args.programmatic_results),
            decision=prog_data.get("decision", "UNKNOWN"),
            score=prog_data.get("score", 0.0),
            checks_passed=summary.get("passed", 0),
            checks_failed=summary.get("failed", 0),
        )
        # Extract score from programmatic evaluation format
        programmatic_score = prog_data.get("score", programmatic_score)
        if programmatic_score is None:
            programmatic_score = prog_data.get("overall_score")
        if programmatic_score is None and "summary" in prog_data:
            programmatic_score = prog_data["summary"].get("overall_score")

    # Register judges
    if args.judges:
        evaluator.register_judges_by_name(args.judges.split(","))
    elif args.focused:
        evaluator.register_focused_judges()
    else:
        evaluator.register_all_judges()

    # Run evaluation
    print(f"\n{'='*60}")
    print("LLM Evaluation - Roslyn Analyzers Static Analysis")
    print(f"{'='*60}\n")

    result = evaluator.evaluate(run_assertions=not args.no_assertions)

    # Attach programmatic input to result
    if programmatic_input is not None:
        result.programmatic_input = programmatic_input

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
    output_path = None
    if args.output:
        args.output.write_text(result.to_json())
        output_path = args.output
        print(f"Results saved to: {args.output}")
    else:
        output_file = evaluator.save_results(result)
        output_path = output_file
        print(f"Results saved to: {output_file}")

    # Generate and save markdown report
    report = evaluator.generate_markdown_report(result, "LLM Evaluation Report - Roslyn Analyzers")
    report_file = output_path.with_suffix(".md") if output_path else evaluator.results_dir / f"{result.run_id}.md"
    report_file.write_text(report)
    print(f"Report saved to: {report_file}")


if __name__ == "__main__":
    main()
