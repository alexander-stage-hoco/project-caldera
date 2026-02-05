#!/usr/bin/env python3
"""CLI runner for LLM-as-a-Judge evaluation of scc.

Usage:
    python scripts/run_llm_eval.py --mode focused
    python scripts/run_llm_eval.py --mode full
    python scripts/run_llm_eval.py --mode full --model opus-4.5
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.llm import LLMEvaluator
from evaluation.llm.orchestrator import ProgrammaticInput


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run LLM-as-a-Judge evaluation on scc outputs"
    )
    parser.add_argument(
        "--mode",
        choices=["focused", "full"],
        default="focused",
        help="Evaluation mode: 'focused' (4 key dimensions) or 'full' (all 10)",
    )
    parser.add_argument(
        "--model",
        default="opus-4.5",
        choices=["opus", "opus-4.5", "sonnet", "haiku"],
        help="Claude model to use (default: opus)",
    )
    parser.add_argument(
        "--working-dir",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Working directory (default: poc-scc root)",
    )
    parser.add_argument(
        "--skip-assertions",
        action="store_true",
        help="Skip ground truth assertions before LLM evaluation",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for results (default: auto-generated in results/)",
    )
    parser.add_argument(
        "--programmatic-score",
        type=float,
        help="Programmatic score (0-5) to include in combined scorecard",
    )
    parser.add_argument(
        "--programmatic-results",
        type=Path,
        help="Path to programmatic evaluation JSON (evaluation_report.json)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("LLM-as-a-Judge Evaluation")
    print("=" * 60)
    print(f"Mode: {args.mode}")
    print(f"Model: {args.model}")
    print(f"Working Directory: {args.working_dir}")
    print("=" * 60)
    print()

    timeout = int(os.environ.get("LLM_TIMEOUT", "120"))

    # Create evaluator
    evaluator = LLMEvaluator(
        working_dir=args.working_dir,
        model=args.model,
        timeout=timeout,
    )

    # Register judges based on mode
    if args.mode == "focused":
        print("Registering focused judges (4 dimensions)...")
        evaluator.register_focused_judges()
    else:
        print("Registering all judges (10 dimensions)...")
        evaluator.register_all_judges()

    print()

    # Run evaluation
    result = evaluator.evaluate(run_assertions=not args.skip_assertions)

    # Load programmatic results and attach to result
    if args.programmatic_results and args.programmatic_results.exists():
        prog_data = json.loads(args.programmatic_results.read_text())
        summary = prog_data.get("summary", {})
        # Support both 'score' and 'total_score' field names
        prog_score = prog_data.get("score") or prog_data.get("total_score") or 0.0
        result.programmatic_input = ProgrammaticInput(
            file=str(args.programmatic_results),
            decision=prog_data.get("decision", "UNKNOWN"),
            score=prog_score,
            checks_passed=summary.get("passed", 0),
            checks_failed=summary.get("failed", 0),
        )
        # Use programmatic score for combined calculation if not explicitly provided
        if args.programmatic_score is None:
            # Score may be on 0-1 or 0-5 scale; normalize to 0-5
            if prog_score <= 1.0:
                args.programmatic_score = prog_score * 5.0
            else:
                args.programmatic_score = prog_score

    # Compute combined score if programmatic score provided
    if args.programmatic_score is not None:
        result = evaluator.compute_combined_score(result, args.programmatic_score)

    # Save results
    output_path = args.output or evaluator.save_results(result)
    if args.output:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result.to_json())
    print()
    print("=" * 60)
    print("Results Summary")
    print("=" * 60)
    print(f"Run ID: {result.run_id}")
    print(f"LLM Score: {result.total_score:.2f}/5.0")
    print(f"Average Confidence: {result.average_confidence:.2f}")

    if result.programmatic_score is not None:
        print(f"Programmatic Score: {result.programmatic_score:.2f}/5.0")

    if result.combined_score is not None:
        print(f"Combined Score: {result.combined_score:.2f}/5.0")

    print(f"Decision: {result.decision}")
    print()
    print("Dimension Scores:")
    for dim in result.dimensions:
        gt_status = "✓" if dim.ground_truth_passed else "✗"
        print(f"  [{gt_status}] {dim.name}: {dim.score}/5 ({dim.weight:.0%})")
        if not dim.ground_truth_passed:
            for failure in dim.ground_truth_failures[:3]:
                print(f"      - {failure}")

    print()
    print(f"Results saved to: {output_path}")

    # Generate markdown report
    report = evaluator.generate_markdown_report(result)
    report_path = output_path.with_suffix(".md")
    report_path.write_text(report)
    print(f"Report saved to: {report_path}")

    return 0 if result.decision in ("STRONG_PASS", "PASS", "WEAK_PASS") else 1


if __name__ == "__main__":
    sys.exit(main())
