#!/usr/bin/env python3
"""
Programmatic evaluation for PMD CPD analysis.

Runs 28 checks across 4 categories to validate CPD output against ground truth:
- Accuracy (AC-1 to AC-8): Clone detection accuracy
- Coverage (CV-1 to CV-8): Language and file coverage
- Edge Cases (EC-1 to EC-8): Edge case handling
- Performance (PF-1 to PF-4): Speed and resource checks

Usage:
    python evaluate.py --analysis output/runs/synthetic.json --ground-truth evaluation/ground-truth
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from checks import (
    EvaluationReport,
    load_analysis,
    run_accuracy_checks,
    run_coverage_checks,
    run_edge_case_checks,
    run_performance_checks,
)


# =============================================================================
# Scorecard Generation
# =============================================================================

SCRIPT_DIR = Path(__file__).parent


def determine_decision(score: float) -> str:
    """Determine pass/fail decision based on score (0-1)."""
    # Convert to 0-5 scale
    normalized = score * 5.0
    if normalized >= 4.0:
        return "STRONG_PASS"
    elif normalized >= 3.5:
        return "PASS"
    elif normalized >= 3.0:
        return "WEAK_PASS"
    return "FAIL"


def generate_scorecard_json(report: EvaluationReport) -> dict:
    """Generate structured scorecard JSON data from evaluation report."""
    # Build dimensions data from category scores
    dimensions_data = []
    for i, (category, score) in enumerate(sorted(report.score_by_category.items())):
        passed, total = report.passed_by_category.get(category, (0, 0))
        category_checks = [c for c in report.checks if c.category.value == category]
        dimensions_data.append({
            "id": f"D{i+1}",
            "name": category.replace("_", " ").title(),
            "weight": 1.0 / len(report.score_by_category) if report.score_by_category else 1.0,
            "total_checks": total,
            "passed": passed,
            "failed": total - passed,
            "score": round(score * 5.0, 2),  # Convert to 0-5 scale
            "weighted_score": round(score * 5.0 / len(report.score_by_category), 2) if report.score_by_category else 0,
            "checks": [
                {
                    "check_id": c.check_id,
                    "name": c.name,
                    "passed": c.passed,
                    "message": c.message,
                }
                for c in category_checks
            ],
        })

    normalized_score = report.score * 5.0  # Convert to 0-5 scale

    return {
        "tool": "pmd-cpd",
        "version": "1.0.0",
        "generated_at": report.timestamp,
        "description": "Evaluation scorecard for PMD CPD duplication analysis",
        "summary": {
            "total_checks": report.total,
            "passed": report.passed,
            "failed": report.failed,
            "score": round(report.score, 4),  # 0-1 normalized
            "score_percent": round(report.score * 100, 2),
            "normalized_score": round(normalized_score, 2),  # 0-5 scale
            "decision": determine_decision(report.score),
        },
        "dimensions": dimensions_data,
        "critical_failures": [
            {
                "check_id": c.check_id,
                "name": c.name,
                "message": c.message,
            }
            for c in report.checks
            if not c.passed and "critical" in c.check_id.lower()
        ],
        "thresholds": {
            "STRONG_PASS": ">= 4.0 (80%+)",
            "PASS": ">= 3.5 (70%+)",
            "WEAK_PASS": ">= 3.0 (60%+)",
            "FAIL": "< 3.0 (below 60%)",
        },
        "metadata": {
            "analysis_path": report.analysis_path,
            "ground_truth_dir": report.ground_truth_dir,
        },
    }


def run_evaluation(
    analysis_path: str,
    ground_truth_dir: str,
    quick: bool = False,
) -> EvaluationReport:
    """Run all evaluation checks and return a report."""
    # Load analysis
    analysis = load_analysis(analysis_path)

    # Run all checks
    all_checks = []

    # Accuracy checks (8)
    all_checks.extend(run_accuracy_checks(analysis, ground_truth_dir))

    # Coverage checks (8)
    all_checks.extend(run_coverage_checks(analysis, ground_truth_dir))

    # Edge case checks (8)
    all_checks.extend(run_edge_case_checks(analysis, ground_truth_dir))

    # Performance checks (4) - skip in quick mode
    if not quick:
        all_checks.extend(run_performance_checks(analysis, ground_truth_dir))

    return EvaluationReport(
        timestamp=datetime.now().isoformat(),
        analysis_path=analysis_path,
        ground_truth_dir=ground_truth_dir,
        checks=all_checks,
    )


def print_report(report: EvaluationReport, json_output: bool = False):
    """Print the evaluation report."""
    if json_output:
        print(json.dumps(report.to_dict(), indent=2))
        return

    print("=" * 70)
    print("PMD CPD EVALUATION REPORT")
    print("=" * 70)
    print()
    print(f"Analysis: {report.analysis_path}")
    print(f"Ground Truth: {report.ground_truth_dir}")
    print(f"Timestamp: {report.timestamp}")
    print()

    # Summary
    print("-" * 70)
    print("SUMMARY")
    print("-" * 70)
    print(f"Total Checks: {report.total}")
    print(f"Passed: {report.passed}")
    print(f"Failed: {report.failed}")
    print(f"Overall Score: {report.score:.2%}")
    print()

    # Score by category
    print("Score by Category:")
    for cat, score in report.score_by_category.items():
        passed, total = report.passed_by_category[cat]
        print(f"  {cat.upper()}: {score:.2%} ({passed}/{total} passed)")
    print()

    # Individual checks
    print("-" * 70)
    print("CHECK RESULTS")
    print("-" * 70)

    # Group by category
    by_category = {}
    for check in report.checks:
        cat = check.category.value
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(check)

    for cat in ["accuracy", "coverage", "edge_cases", "performance"]:
        if cat not in by_category:
            continue

        print(f"\n{cat.upper().replace('_', ' ')}:")
        for check in by_category[cat]:
            status = "PASS" if check.passed else "FAIL"
            print(f"  [{status}] {check.check_id}: {check.name}")
            print(f"         {check.message}")

    print()
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="PMD CPD Programmatic Evaluation"
    )
    parser.add_argument(
        "--analysis",
        "-a",
        required=True,
        help="Path to analysis JSON file",
    )
    parser.add_argument(
        "--ground-truth",
        "-g",
        required=True,
        help="Path to ground truth directory",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output JSON file path",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON only",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode (skip performance checks)",
    )

    args = parser.parse_args()

    # Validate inputs
    if not Path(args.analysis).exists():
        print(f"Error: Analysis file not found: {args.analysis}")
        sys.exit(1)

    if not Path(args.ground_truth).exists():
        print(f"Error: Ground truth directory not found: {args.ground_truth}")
        sys.exit(1)

    # Run evaluation
    report = run_evaluation(
        args.analysis,
        args.ground_truth,
        quick=args.quick,
    )

    # Print report
    print_report(report, json_output=args.json)

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        if not args.json:
            print(f"\nReport saved to: {args.output}")

    # Generate and save scorecard.json
    scorecard_json = generate_scorecard_json(report)
    scorecard_path = SCRIPT_DIR.parent / "evaluation" / "scorecard.json"
    scorecard_path.parent.mkdir(parents=True, exist_ok=True)
    with open(scorecard_path, "w") as f:
        json.dump(scorecard_json, f, indent=2)
    if not args.json:
        print(f"\nScorecard saved to: {scorecard_path}")

    # Exit with appropriate code
    if report.score < 0.7:
        sys.exit(1)


if __name__ == "__main__":
    main()
