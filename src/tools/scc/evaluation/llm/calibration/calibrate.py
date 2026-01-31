#!/usr/bin/env python3
"""Calibration script for LLM-as-Judge evaluation.

Computes agreement between LLM judge scores and expert-labeled examples.

Usage:
    python calibrate.py
    python calibrate.py --dimension directory_analysis
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from evaluation.llm.judges.base import BaseJudge


def load_calibration_dataset(path: Path | None = None) -> list[dict]:
    """Load calibration dataset."""
    if path is None:
        path = Path(__file__).parent / "calibration_dataset.json"

    data = json.loads(path.read_text())
    return data.get("examples", [])


def run_judge_on_example(
    judge: BaseJudge,
    example: dict,
) -> tuple[int, float]:
    """Run a judge on a calibration example.

    Returns:
        Tuple of (predicted_score, confidence)
    """
    # Build prompt with example evidence
    evidence = example.get("evidence", {})
    prompt = judge.build_prompt(evidence)

    # Invoke LLM
    response = judge.invoke_claude(prompt)

    # Parse response
    result = judge.parse_response(response)

    return result.score, result.confidence


def compute_agreement_metrics(
    predictions: list[int],
    labels: list[int],
) -> dict[str, float]:
    """Compute agreement metrics between predictions and labels."""
    n = len(predictions)
    if n == 0:
        return {"exact_match": 0.0, "within_1": 0.0, "mae": 0.0}

    exact_matches = sum(1 for p, l in zip(predictions, labels) if p == l)
    within_1 = sum(1 for p, l in zip(predictions, labels) if abs(p - l) <= 1)
    mae = sum(abs(p - l) for p, l in zip(predictions, labels)) / n

    return {
        "exact_match": exact_matches / n,
        "within_1": within_1 / n,
        "mae": mae,
    }


def get_judge_for_dimension(dimension: str, working_dir: Path) -> BaseJudge | None:
    """Get the appropriate judge for a dimension."""
    from evaluation.llm.judges.directory_analysis import DirectoryAnalysisJudge
    from evaluation.llm.judges.statistics import StatisticsJudge
    from evaluation.llm.judges.integration_fit import IntegrationFitJudge
    from evaluation.llm.judges.api_design import APIDesignJudge
    from evaluation.llm.judges.edge_cases import EdgeCasesJudge
    from evaluation.llm.judges.risk import RiskJudge

    judges = {
        "directory_analysis": DirectoryAnalysisJudge,
        "statistics": StatisticsJudge,
        "integration_fit": IntegrationFitJudge,
        "api_design": APIDesignJudge,
        "edge_cases": EdgeCasesJudge,
        "risk": RiskJudge,
    }

    judge_class = judges.get(dimension)
    if judge_class:
        return judge_class(working_dir=working_dir)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run calibration for LLM-as-Judge evaluation"
    )
    parser.add_argument(
        "--dimension",
        help="Only run calibration for specific dimension",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        help="Path to calibration dataset",
    )
    parser.add_argument(
        "--working-dir",
        type=Path,
        default=Path(__file__).parent.parent.parent.parent,
        help="Working directory",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show what would be run, don't invoke LLM",
    )

    args = parser.parse_args()

    # Load calibration dataset
    examples = load_calibration_dataset(args.dataset)

    if args.dimension:
        examples = [e for e in examples if e.get("dimension") == args.dimension]

    if not examples:
        print("No calibration examples found")
        return 1

    print("=" * 60)
    print("LLM Judge Calibration")
    print("=" * 60)
    print(f"Examples: {len(examples)}")
    print(f"Working Directory: {args.working_dir}")
    print()

    # Group by dimension
    by_dimension: dict[str, list[dict]] = {}
    for ex in examples:
        dim = ex.get("dimension", "unknown")
        if dim not in by_dimension:
            by_dimension[dim] = []
        by_dimension[dim].append(ex)

    all_results = []

    for dimension, dim_examples in by_dimension.items():
        print(f"\n## {dimension} ({len(dim_examples)} examples)")
        print("-" * 40)

        judge = get_judge_for_dimension(dimension, args.working_dir)
        if judge is None:
            print(f"  No judge available for {dimension}")
            continue

        predictions = []
        labels = []

        for ex in dim_examples:
            print(f"  [{ex['id']}] {ex['scenario']}")
            expected = ex.get("expected_score", 3)
            labels.append(expected)

            if args.dry_run:
                print(f"    Expected: {expected} (dry run - not invoking LLM)")
                predictions.append(expected)  # Use expected for dry run
            else:
                try:
                    predicted, confidence = run_judge_on_example(judge, ex)
                    predictions.append(predicted)
                    match = "✓" if predicted == expected else "✗"
                    print(f"    Expected: {expected}, Predicted: {predicted} [{match}] (conf: {confidence:.2f})")
                except Exception as e:
                    print(f"    Error: {e}")
                    predictions.append(3)  # Default score on error

        # Compute metrics
        if predictions:
            metrics = compute_agreement_metrics(predictions, labels)
            print()
            print(f"  Exact Match: {metrics['exact_match']:.1%}")
            print(f"  Within 1: {metrics['within_1']:.1%}")
            print(f"  MAE: {metrics['mae']:.2f}")

            all_results.append({
                "dimension": dimension,
                "examples": len(dim_examples),
                "metrics": metrics,
            })

    # Summary
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    if all_results:
        total_exact = sum(r["metrics"]["exact_match"] * r["examples"] for r in all_results)
        total_within_1 = sum(r["metrics"]["within_1"] * r["examples"] for r in all_results)
        total_examples = sum(r["examples"] for r in all_results)

        print(f"Total Examples: {total_examples}")
        print(f"Overall Exact Match: {total_exact / total_examples:.1%}")
        print(f"Overall Within 1: {total_within_1 / total_examples:.1%}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
