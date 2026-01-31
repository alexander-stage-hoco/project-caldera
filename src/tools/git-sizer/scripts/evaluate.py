#!/usr/bin/env python3
"""
Programmatic evaluation for git-sizer repository analysis.

Runs 28 checks across 4 categories:
- Accuracy (AC-1 to AC-8): Size detection accuracy
- Coverage (CV-1 to CV-8): Metric coverage
- Edge Cases (EC-1 to EC-8): Edge case handling
- Performance (PF-1 to PF-4): Speed thresholds

Usage:
    python -m scripts.evaluate --results-dir evaluation/results --ground-truth-dir evaluation/ground-truth
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .checks import (
    EvaluationReport,
    load_all_results,
    run_accuracy_checks,
    run_coverage_checks,
    run_edge_case_checks,
    run_performance_checks,
)


def run_all_checks(
    analysis: dict,
    ground_truth_dir: str,
    skip_long_checks: bool = False,
) -> list:
    """Run all evaluation checks and return results."""
    results = []

    # Accuracy checks (AC-1 to AC-8)
    results.extend(run_accuracy_checks(analysis, ground_truth_dir))

    # Coverage checks (CV-1 to CV-8)
    results.extend(run_coverage_checks(analysis))

    # Edge case checks (EC-1 to EC-8)
    results.extend(run_edge_case_checks(analysis))

    # Performance checks (PF-1 to PF-4)
    results.extend(run_performance_checks(analysis, skip_long_checks))

    return results


def create_report(
    analysis_path: str,
    ground_truth_dir: str,
    analysis: dict,
    checks: list,
) -> EvaluationReport:
    """Create evaluation report from check results."""
    return EvaluationReport(
        timestamp=datetime.now().isoformat(),
        analysis_path=analysis_path,
        ground_truth_dir=ground_truth_dir,
        checks=checks,
    )


def determine_decision(score: float) -> str:
    """Determine pass/fail decision based on score (0-1)."""
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
            "score": round(score * 5.0, 2),
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

    normalized_score = report.score * 5.0

    return {
        "tool": "git-sizer",
        "version": "1.0.0",
        "generated_at": report.timestamp,
        "description": "Evaluation scorecard for git-sizer repository health analysis",
        "summary": {
            "total_checks": report.total,
            "passed": report.passed,
            "failed": report.failed,
            "score": round(report.score, 4),
            "score_percent": round(report.score * 100, 2),
            "normalized_score": round(normalized_score, 2),
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


def generate_scorecard_md(scorecard: dict) -> str:
    """Generate a minimal markdown scorecard for compliance."""
    summary = scorecard.get("summary", {})
    lines = [
        "# Git-Sizer Evaluation Scorecard",
        "",
        f"**Generated:** {scorecard.get('generated_at', '')}",
        f"**Decision:** {summary.get('decision', '')}",
        f"**Score:** {summary.get('score_percent', 0)}%",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total Checks | {summary.get('total_checks', 0)} |",
        f"| Passed | {summary.get('passed', 0)} |",
        f"| Failed | {summary.get('failed', 0)} |",
        f"| Normalized Score | {summary.get('normalized_score', 0)}/5.0 |",
        "",
    ]
    return "\n".join(lines)


def print_report(report: EvaluationReport) -> None:
    """Print evaluation report to console."""
    print("\n" + "=" * 70)
    print("GIT-SIZER EVALUATION REPORT")
    print("=" * 70)

    print(f"\nTimestamp: {report.timestamp}")
    print(f"Analysis:  {report.analysis_path}")

    # Overall summary
    print("\n" + "-" * 70)
    print("OVERALL SUMMARY")
    print("-" * 70)
    print(f"  Total Checks: {report.total}")
    print(f"  Passed:       {report.passed} ({report.passed/report.total*100:.1f}%)")
    print(f"  Failed:       {report.failed} ({report.failed/report.total*100:.1f}%)")
    print(f"  Overall Score: {report.score:.2f}/1.00")
    print(f"  Decision:      {determine_decision(report.score)}")

    # Category breakdown
    print("\n" + "-" * 70)
    print("CATEGORY BREAKDOWN")
    print("-" * 70)

    for category, (passed, total) in report.passed_by_category.items():
        score = report.score_by_category.get(category, 0.0)
        pct = passed / total * 100 if total > 0 else 0
        status = "PASS" if pct >= 75 else "FAIL"
        print(f"  {category.upper():15} {passed:2}/{total:2} ({pct:5.1f}%)  Score: {score:.2f}  [{status}]")

    # Detailed results
    print("\n" + "-" * 70)
    print("DETAILED RESULTS")
    print("-" * 70)

    current_category = None
    for check in report.checks:
        if check.category.value != current_category:
            current_category = check.category.value
            print(f"\n  [{current_category.upper()}]")

        status = "PASS" if check.passed else "FAIL"
        score_str = f"{check.score:.2f}"
        print(f"    {check.check_id:6} {status:4} ({score_str}) - {check.name}")
        if not check.passed:
            print(f"           {check.message}")

    # Final verdict
    print("\n" + "=" * 70)
    overall_status = "PASS" if report.score >= 0.75 else "FAIL"
    print(f"FINAL VERDICT: {overall_status} ({report.score:.2f}/1.00)")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate git-sizer analysis results"
    )
    parser.add_argument(
        "--results-dir",
        required=True,
        help="Path to results directory (containing repo subdirs with output.json)",
    )
    parser.add_argument(
        "--ground-truth-dir",
        default="evaluation/ground-truth",
        help="Path to ground truth directory",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output path for evaluation results JSON",
    )
    parser.add_argument(
        "--skip-long-checks",
        action="store_true",
        help="Skip long-running checks",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON only (no console output)",
    )

    args = parser.parse_args()

    # Validate paths
    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        print(f"Error: Results directory not found: {results_dir}", file=sys.stderr)
        sys.exit(1)

    ground_truth_dir = Path(args.ground_truth_dir)
    if not ground_truth_dir.exists():
        ground_truth_dir.mkdir(parents=True, exist_ok=True)

    # Load all analysis results
    analysis = load_all_results(results_dir)

    if not analysis.get("repositories"):
        print(f"Error: No analysis results found in {results_dir}", file=sys.stderr)
        sys.exit(1)

    # Run all checks
    checks = run_all_checks(
        analysis,
        str(ground_truth_dir),
        args.skip_long_checks,
    )

    # Create report
    report = create_report(
        str(results_dir),
        str(ground_truth_dir),
        analysis,
        checks,
    )

    # Output
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print_report(report)

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report.to_dict(), indent=2, fp=f)
        if not args.json:
            print(f"Results saved to: {output_path}")

    # Generate and save scorecard
    scorecard_json = generate_scorecard_json(report)
    if args.output:
        out_dir = Path(args.output).parent if Path(args.output).suffix else Path(args.output)
        out_dir.mkdir(parents=True, exist_ok=True)
        checks_path = out_dir / "checks.json"
        scorecard_json_path = out_dir / "scorecard.json"
        scorecard_md_path = out_dir / "scorecard.md"
        with open(checks_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        with open(scorecard_json_path, "w") as f:
            json.dump(scorecard_json, f, indent=2)
        scorecard_md_path.write_text(generate_scorecard_md(scorecard_json))
        if not args.json:
            print(f"Scorecard saved to: {scorecard_md_path}")
    else:
        scorecard_path = Path(__file__).parent.parent / "evaluation" / "scorecard.json"
        scorecard_path.parent.mkdir(parents=True, exist_ok=True)
        with open(scorecard_path, "w") as f:
            json.dump(scorecard_json, f, indent=2)
        if not args.json:
            print(f"Scorecard saved to: {scorecard_path}")

    # Exit with appropriate code
    sys.exit(0 if report.score >= 0.75 else 1)


if __name__ == "__main__":
    main()
