"""LLM Evaluation Orchestrator for symbol-scanner outputs.

Coordinates multiple LLM judges to produce a comprehensive qualitative
evaluation of symbol-scanner analysis outputs.
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
    require_observability,
)

from .judges.base import BaseJudge, JudgeResult


class LLMEvaluator(LLMEvaluatorBase):
    """Orchestrates LLM-based evaluation of symbol-scanner outputs.

    Coordinates four specialized judges, each evaluating a specific
    dimension of output quality:
    - Symbol Accuracy (30%): Correctness of symbol extraction
    - Call Relationship (30%): Accuracy of function/method call relationships
    - Import Completeness (20%): Completeness of import extraction
    - Integration (20%): Overall data consistency and metadata quality
    """

    def __init__(
        self,
        working_dir: Path | None = None,
        model: str = "opus-4.5",
        results_dir: Path | None = None,
        timeout: int = 120,
    ):
        """Initialize the evaluator.

        Args:
            working_dir: Working directory containing analysis outputs.
            model: Claude model to use for evaluation.
            results_dir: Directory to save evaluation results.
            timeout: Timeout in seconds for each judge's LLM invocation.
        """
        super().__init__(working_dir=working_dir, model=model, results_dir=results_dir)
        self.timeout = timeout

    def _default_results_dir(self) -> Path:
        """Override to use 'results' instead of 'llm/results'."""
        return self.working_dir / "evaluation" / "results"

    def register_all_judges(self) -> None:
        """Register all 4 judges for comprehensive evaluation."""
        from .judges.symbol_accuracy import SymbolAccuracyJudge
        from .judges.call_relationship import CallRelationshipJudge
        from .judges.import_completeness import ImportCompletenessJudge
        from .judges.integration import IntegrationJudge

        judges = [
            SymbolAccuracyJudge(
                model=self.model,
                working_dir=self.working_dir,
                timeout=self.timeout,
            ),
            CallRelationshipJudge(
                model=self.model,
                working_dir=self.working_dir,
                timeout=self.timeout,
            ),
            ImportCompletenessJudge(
                model=self.model,
                working_dir=self.working_dir,
                timeout=self.timeout,
            ),
            IntegrationJudge(
                model=self.model,
                working_dir=self.working_dir,
                timeout=self.timeout,
            ),
        ]

        for judge in judges:
            self.register_judge(judge)

    def register_focused_judges(self) -> None:
        """Register top 2 judges for quick evaluation.

        Uses Symbol Accuracy and Call Relationship judges, which together
        represent 60% of the total weight and cover the core functionality.
        """
        from .judges.symbol_accuracy import SymbolAccuracyJudge
        from .judges.call_relationship import CallRelationshipJudge

        judges = [
            SymbolAccuracyJudge(
                model=self.model,
                working_dir=self.working_dir,
                timeout=self.timeout,
            ),
            CallRelationshipJudge(
                model=self.model,
                working_dir=self.working_dir,
                timeout=self.timeout,
            ),
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
    """CLI entry point for LLM evaluation."""
    require_observability()
    parser = argparse.ArgumentParser(
        description="Run LLM evaluation on symbol-scanner analysis output."
    )
    parser.add_argument(
        "--analysis",
        default=os.environ.get("ANALYSIS_PATH"),
        help="Path to symbol-scanner analysis output JSON (required)",
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
        help="Path to programmatic evaluation JSON for combined scoring",
    )
    parser.add_argument(
        "--focused",
        action="store_true",
        help="Use focused judges (2 instead of 4) for quick evaluation",
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
            print(
                f"Error: Programmatic results file does not exist: {programmatic_results}",
                file=sys.stderr,
            )
            sys.exit(1)

    focused = args.focused

    # Determine working directory from analysis path
    # Typical path: src/tools/symbol-scanner/outputs/<run-id>/output.json
    working_dir = analysis.parent.parent.parent

    # Create evaluator
    evaluator = LLMEvaluator(
        working_dir=working_dir,
        model=model,
        results_dir=output.parent,
    )

    # Register judges based on mode
    if focused:
        evaluator.register_focused_judges()
        print("Using focused evaluation (2 judges)")
    else:
        evaluator.register_all_judges()
        print("Using full evaluation (4 judges)")

    # Run evaluation
    result = evaluator.evaluate()

    # Load programmatic input if provided
    if programmatic_results:
        prog_data = json.loads(programmatic_results.read_text())
        summary = prog_data.get("summary", {})
        prog_decision = (
            prog_data.get("decision")
            or prog_data.get("classification")
            or "UNKNOWN"
        )
        prog_score_raw = (
            prog_data.get("score")
            or prog_data.get("overall_score")
            or 0.0
        )

        # Scale programmatic score from 0-1 to 1-5 scale if needed
        # (score <= 1.0 indicates 0-1 scale, otherwise assume already on 5-point scale)
        if prog_score_raw <= 1.0:
            prog_score = 1.0 + prog_score_raw * 4.0  # Maps 0->1, 1->5
        else:
            prog_score = prog_score_raw

        result.programmatic_input = ProgrammaticInput(
            file=str(programmatic_results),
            decision=prog_decision,
            score=prog_score,  # Store scaled score
            checks_passed=summary.get("passed", 0),
            checks_failed=summary.get("failed", 0),
        )

        # Compute combined score (now both on 5-point scale)
        evaluator.compute_combined_score(result, prog_score)

    # Save results
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result.to_json())

    # Print summary
    print(f"\nLLM evaluation complete: {output}")
    print(f"Decision: {result.decision}")
    print(f"Score: {result.total_score:.2f}/5.0")

    if result.combined_score is not None:
        print(f"Combined Score: {result.combined_score:.2f}/5.0")


if __name__ == "__main__":
    main()
