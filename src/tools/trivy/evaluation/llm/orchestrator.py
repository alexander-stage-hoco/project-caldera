"""LLM Evaluation Orchestrator for Trivy vulnerability scanning outputs.

Coordinates multiple LLM judges to produce a comprehensive qualitative
evaluation of Trivy analysis outputs.
"""

from __future__ import annotations

import json
from pathlib import Path

import click

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


@click.command()
@click.option("--analysis", type=click.Path(exists=True, path_type=Path), required=True)
@click.option("--output", type=click.Path(path_type=Path), required=True)
@click.option("--model", default="opus-4.5", help="LLM model to use")
@click.option("--programmatic-results", type=click.Path(exists=True, path_type=Path), help="Path to programmatic evaluation JSON")
@click.option("--focused", is_flag=True, help="Use focused judges for quick evaluation")
def main(analysis: Path, output: Path, model: str, programmatic_results: Path | None, focused: bool):
    """Run LLM evaluation on Trivy analysis output."""
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
    click.echo(f"LLM evaluation complete: {output}")


if __name__ == "__main__":
    main()
