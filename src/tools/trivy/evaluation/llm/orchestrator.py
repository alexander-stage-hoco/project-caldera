"""LLM Evaluation Orchestrator for Trivy vulnerability scanning outputs.

Coordinates multiple LLM judges to produce a comprehensive qualitative
evaluation of Trivy analysis outputs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from shared.evaluation import (
    LLMEvaluatorBase,
    ProgrammaticInput,
)

from .judges.base import BaseJudge, JudgeResult


class LLMEvaluator(LLMEvaluatorBase):
    """Orchestrates LLM-based evaluation of Trivy outputs.

    Coordinates multiple specialized judges, each evaluating a specific
    dimension of output quality.
    """

    def __init__(
        self,
        working_dir: Path | None = None,
        model: str = "opus-4.5",
        results_dir: Path | None = None,
        timeout: int = 120,
        output_dir: Path | None = None,
    ):
        super().__init__(working_dir=working_dir, model=model, results_dir=results_dir)
        self.timeout = timeout
        self.output_dir = output_dir or self.working_dir / "outputs"

    def _default_results_dir(self) -> Path:
        """Override to use 'results' instead of 'llm/results'."""
        return self.working_dir / "evaluation" / "results"

    def register_all_judges(self) -> None:
        """Register all available judges for comprehensive evaluation."""
        from .judges.vulnerability_accuracy import VulnerabilityAccuracyJudge
        from .judges.severity_accuracy import SeverityAccuracyJudge
        from .judges.sbom_completeness import SBOMCompletenessJudge
        from .judges.iac_quality import IaCQualityJudge
        from .judges.false_positive_rate import FalsePositiveRateJudge
        from .judges.freshness_quality import FreshnessQualityJudge
        from .judges.vulnerability_detection import VulnerabilityDetectionJudge

        judges = [
            VulnerabilityAccuracyJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout, output_dir=self.output_dir),
            SeverityAccuracyJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout, output_dir=self.output_dir),
            SBOMCompletenessJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout, output_dir=self.output_dir),
            IaCQualityJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout, output_dir=self.output_dir),
            FalsePositiveRateJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout, output_dir=self.output_dir),
            FreshnessQualityJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout, output_dir=self.output_dir),
            VulnerabilityDetectionJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout, output_dir=self.output_dir),
        ]

        for judge in judges:
            self.register_judge(judge)

    def register_focused_judges(self) -> None:
        """Register only the most important judges for quick evaluation."""
        from .judges.vulnerability_accuracy import VulnerabilityAccuracyJudge
        from .judges.severity_accuracy import SeverityAccuracyJudge
        from .judges.iac_quality import IaCQualityJudge

        judges = [
            VulnerabilityAccuracyJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout, output_dir=self.output_dir),
            SeverityAccuracyJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout, output_dir=self.output_dir),
            IaCQualityJudge(model=self.model, working_dir=self.working_dir, timeout=self.timeout, output_dir=self.output_dir),
        ]

        for judge in judges:
            self.register_judge(judge)

    def save_results(self, result) -> Path:
        """Save evaluation results to file."""
        self.results_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.results_dir / "llm_evaluation.json"
        output_file.write_text(result.to_json())
        return output_file


def main() -> None:
    """Run LLM evaluation on Trivy analysis output."""
    parser = argparse.ArgumentParser(
        description="Run LLM evaluation on Trivy analysis output."
    )
    parser.add_argument(
        "--analysis",
        default=os.environ.get("ANALYSIS_PATH"),
        help="Path to Trivy analysis output JSON (required)",
    )
    parser.add_argument(
        "--output",
        default=os.environ.get("OUTPUT_PATH"),
        help="Path to write evaluation results (required)",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("LLM_MODEL", "opus-4.5"),
        help="LLM model to use (default: opus-4.5)",
    )
    parser.add_argument(
        "--programmatic-results",
        default=os.environ.get("PROGRAMMATIC_RESULTS_PATH"),
        help="Path to programmatic evaluation JSON",
    )
    parser.add_argument(
        "--focused",
        action="store_true",
        help="Use focused judges for quick evaluation",
    )
    args = parser.parse_args()

    # Validate required arguments
    if not args.analysis:
        print("Error: --analysis is required", file=sys.stderr)
        sys.exit(1)
    if not args.output:
        print("Error: --output is required", file=sys.stderr)
        sys.exit(1)

    # Convert to Path objects and validate
    analysis = Path(args.analysis)
    if not analysis.exists():
        print(f"Error: Analysis file does not exist: {analysis}", file=sys.stderr)
        sys.exit(1)

    output = Path(args.output)
    model = args.model

    programmatic_results: Path | None = None
    if args.programmatic_results:
        programmatic_results = Path(args.programmatic_results)
        if not programmatic_results.exists():
            print(f"Error: Programmatic results file does not exist: {programmatic_results}", file=sys.stderr)
            sys.exit(1)

    focused = args.focused

    # Determine working directory from analysis path
    working_dir = analysis.parent.parent.parent  # outputs/<run-id>/output.json -> tool root

    # Determine output_dir from analysis path (parent of the analysis file)
    output_dir = analysis.parent

    # Create evaluator
    evaluator = LLMEvaluator(
        working_dir=working_dir,
        model=model,
        results_dir=output.parent,
        output_dir=output_dir,
    )

    # Register judges
    if focused:
        evaluator.register_focused_judges()
    else:
        evaluator.register_all_judges()

    # Run evaluation
    result = evaluator.evaluate()

    # Load programmatic input if provided
    if programmatic_results:
        prog_data = json.loads(programmatic_results.read_text())
        summary = prog_data.get("summary", {})
        prog_decision = prog_data.get("decision") or prog_data.get("classification") or "UNKNOWN"
        prog_score = prog_data.get("score") or prog_data.get("overall_score") or 0.0

        result.programmatic_input = ProgrammaticInput(
            file=str(programmatic_results),
            decision=prog_decision,
            score=prog_score,
            checks_passed=summary.get("passed", 0),
            checks_failed=summary.get("failed", 0),
        )

        # Compute combined score
        evaluator.compute_combined_score(result, prog_score)

    # Save results
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result.to_json())
    print(f"LLM evaluation complete: {output}")


if __name__ == "__main__":
    main()
