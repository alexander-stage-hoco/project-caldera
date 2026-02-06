#!/usr/bin/env python3
"""
Programmatic evaluation for Semgrep smell analysis.

Runs 28 checks across 4 categories:
- Accuracy (AC-1 to AC-8): Detection accuracy
- Coverage (CV-1 to CV-8): Language and category coverage
- Edge Cases (EC-1 to EC-8): Edge case handling
- Performance (PF-1 to PF-4): Speed and efficiency
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from checks import (
    CheckResult,
    CheckCategory,
    EvaluationReport,
    load_analysis,
    run_accuracy_checks,
    run_coverage_checks,
    run_edge_case_checks,
    run_output_quality_checks,
    run_performance_checks,
    run_integration_fit_checks,
)


# =============================================================================
# Terminal Colors
# =============================================================================

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"


_use_color = True


def c(text: str, *codes: str) -> str:
    if not _use_color:
        return str(text)
    prefix = "".join(codes)
    return f"{prefix}{text}{Colors.RESET}"


def set_color_enabled(enabled: bool):
    global _use_color
    _use_color = enabled


# =============================================================================
# Scorecard Generation
# =============================================================================


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
        "tool": "semgrep",
        "version": "1.0.0",
        "generated_at": report.timestamp,
        "description": "Evaluation scorecard for Semgrep static analysis",
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


def generate_scorecard_md(scorecard: dict) -> str:
    """Generate comprehensive markdown scorecard."""
    summary = scorecard.get("summary", {})
    dimensions = scorecard.get("dimensions", [])
    critical_failures = scorecard.get("critical_failures", [])
    thresholds = scorecard.get("thresholds", {})

    lines = [
        "# Semgrep Evaluation Scorecard",
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
        f"| Raw Score | {summary.get('score', 0):.3f} |",
        f"| Normalized Score | {summary.get('normalized_score', 0):.2f}/5.0 |",
        "",
    ]

    # Dimensions table
    if dimensions:
        lines.append("## Dimensions")
        lines.append("")
        lines.append("| Dimension | Checks | Passed | Score |")
        lines.append("|-----------|--------|--------|-------|")
        for dim in dimensions:
            score_pct = dim.get("score", 0) / 5.0 * 100 if dim.get("score") else 0
            lines.append(
                f"| {dim.get('name', '')} | {dim.get('total_checks', 0)} | "
                f"{dim.get('passed', 0)}/{dim.get('total_checks', 0)} | {score_pct:.1f}% |"
            )
        lines.append("")

    # Critical failures
    if critical_failures:
        lines.append("## Critical Failures")
        lines.append("")
        for failure in critical_failures:
            lines.append(f"- **{failure.get('check_id', '')}** - {failure.get('name', '')}: {failure.get('message', '')}")
        lines.append("")

    # Detailed results by category
    if dimensions:
        lines.append("## Detailed Results")
        lines.append("")
        for dim in dimensions:
            lines.append(f"### {dim.get('name', '')}")
            lines.append("")
            lines.append("| Check | Status | Message |")
            lines.append("|-------|--------|---------|")
            for check in dim.get("checks", []):
                status = "PASS" if check.get("passed") else "FAIL"
                msg = check.get("message", "")
                msg = msg[:50] + "..." if len(msg) > 50 else msg
                lines.append(f"| {check.get('check_id', '')} | {status} | {msg} |")
            lines.append("")

    # Decision thresholds
    if thresholds:
        lines.append("## Decision Thresholds")
        lines.append("")
        lines.append("| Decision | Criteria |")
        lines.append("|----------|----------|")
        for decision, criteria in thresholds.items():
            lines.append(f"| {decision} | {criteria} |")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    metadata = scorecard.get("metadata", {})
    if metadata.get("analysis_path"):
        lines.append(f"*Analysis: `{metadata.get('analysis_path')}`*")
    if metadata.get("ground_truth_dir"):
        lines.append(f"*Ground Truth: `{metadata.get('ground_truth_dir')}`*")

    return "\n".join(lines)


# =============================================================================
# Evaluation Runner
# =============================================================================

def run_evaluation(
    analysis_path: str,
    ground_truth_dir: str,
    skip_performance: bool = False,
) -> EvaluationReport:
    """Run all evaluation checks and return report."""
    analysis = load_analysis(analysis_path)

    all_checks: list[CheckResult] = []

    # Run accuracy checks
    accuracy_checks = run_accuracy_checks(analysis, ground_truth_dir)
    all_checks.extend(accuracy_checks)

    # Run coverage checks
    coverage_checks = run_coverage_checks(analysis)
    all_checks.extend(coverage_checks)

    # Run edge case checks
    edge_case_checks = run_edge_case_checks(analysis)
    all_checks.extend(edge_case_checks)

    # Run output quality checks
    output_quality_checks = run_output_quality_checks(analysis)
    all_checks.extend(output_quality_checks)

    # Run integration fit checks
    integration_checks = run_integration_fit_checks(analysis)
    all_checks.extend(integration_checks)

    # Run performance checks
    if not skip_performance:
        performance_checks = run_performance_checks(analysis)
        all_checks.extend(performance_checks)

    return EvaluationReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        analysis_path=analysis_path,
        ground_truth_dir=ground_truth_dir,
        checks=all_checks,
    )


def print_report(report: EvaluationReport):
    """Print evaluation report to console."""
    print()
    print(c("=" * 70, Colors.CYAN))
    print(c("  SEMGREP EVALUATION REPORT", Colors.CYAN, Colors.BOLD))
    print(c("=" * 70, Colors.CYAN))
    print()

    # Summary
    print(c("SUMMARY", Colors.BLUE, Colors.BOLD))
    print(c("-" * 40, Colors.BLUE))
    print(f"  Total Checks:  {report.total}")
    print(f"  Passed:        {c(str(report.passed), Colors.GREEN)}")
    print(f"  Failed:        {c(str(report.failed), Colors.RED if report.failed > 0 else Colors.GREEN)}")
    score_color = Colors.GREEN if report.score >= 0.8 else (Colors.YELLOW if report.score >= 0.6 else Colors.RED)
    print(f"  Overall Score: {c(f'{report.score:.1%}', score_color, Colors.BOLD)}")
    print()

    # Score by category
    print(c("SCORE BY CATEGORY", Colors.BLUE, Colors.BOLD))
    print(c("-" * 40, Colors.BLUE))
    for category, score in sorted(report.score_by_category.items()):
        passed, total = report.passed_by_category.get(category, (0, 0))
        score_color = Colors.GREEN if score >= 0.8 else (Colors.YELLOW if score >= 0.6 else Colors.RED)
        print(f"  {category:15} {c(f'{score:.1%}', score_color):>8}  ({passed}/{total} passed)")
    print()

    # Detailed results
    print(c("DETAILED RESULTS", Colors.BLUE, Colors.BOLD))
    print(c("-" * 40, Colors.BLUE))

    current_category = None
    for check in sorted(report.checks, key=lambda x: (x.category.value, x.check_id)):
        if check.category != current_category:
            current_category = check.category
            print()
            print(c(f"  [{current_category.value.upper()}]", Colors.CYAN, Colors.BOLD))

        status = c("PASS", Colors.GREEN) if check.passed else c("FAIL", Colors.RED)
        score_str = f"{check.score:.0%}"
        print(f"    {check.check_id:5} {status} {score_str:>5}  {check.name}")
        if not check.passed:
            print(f"           {c(check.message, Colors.DIM)}")

    print()

    # Final decision
    if report.score >= 0.8:
        decision = c("STRONG PASS", Colors.GREEN, Colors.BOLD)
    elif report.score >= 0.6:
        decision = c("PASS", Colors.GREEN)
    elif report.score >= 0.5:
        decision = c("WEAK PASS", Colors.YELLOW)
    else:
        decision = c("FAIL", Colors.RED, Colors.BOLD)

    print(c("=" * 70, Colors.CYAN))
    print(f"  DECISION: {decision}  (Score: {report.score:.1%})")
    print(c("=" * 70, Colors.CYAN))
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate Semgrep smell analysis against ground truth"
    )
    parser.add_argument(
        "--analysis", "-a",
        required=True,
        help="Path to analysis JSON file",
    )
    parser.add_argument(
        "--ground-truth", "-g",
        required=True,
        help="Path to ground truth directory",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file path",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON only (no console report)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Skip performance checks",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )

    args = parser.parse_args()

    if args.no_color:
        set_color_enabled(False)

    # Validate paths
    if not Path(args.analysis).exists():
        print(f"Error: Analysis file not found: {args.analysis}", file=sys.stderr)
        sys.exit(1)

    if not Path(args.ground_truth).is_dir():
        print(f"Error: Ground truth directory not found: {args.ground_truth}", file=sys.stderr)
        sys.exit(1)

    # Run evaluation
    report = run_evaluation(
        analysis_path=args.analysis,
        ground_truth_dir=args.ground_truth,
        skip_performance=args.quick,
    )

    # Output results
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print_report(report)

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        if not args.json:
            print(f"  Results saved to: {args.output}")
            print()

    # Generate and save scorecard files
    scorecard_json = generate_scorecard_json(report)
    if args.output:
        out_dir = Path(args.output).parent if Path(args.output).suffix else Path(args.output)
    else:
        out_dir = Path(__file__).parent.parent / "evaluation" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Output uniform evaluation_report.json for compliance
    evaluation_report_path = out_dir / "evaluation_report.json"
    evaluation_report = {
        "timestamp": report.timestamp,
        "tool": "semgrep",
        "decision": determine_decision(report.score),
        "score": round(report.score, 4),
        "checks": [
            {
                "name": c.check_id,
                "status": "PASS" if c.passed else "FAIL",
                "message": c.message,
            }
            for c in report.checks
        ],
        "summary": {
            "total": report.total,
            "passed": report.passed,
            "failed": report.failed,
        },
    }
    with open(evaluation_report_path, "w") as f:
        json.dump(evaluation_report, f, indent=2)

    scorecard_json_path = out_dir / "scorecard.json"
    scorecard_md_path = out_dir / "scorecard.md"
    with open(scorecard_json_path, "w") as f:
        json.dump(scorecard_json, f, indent=2)
    scorecard_md_path.write_text(generate_scorecard_md(scorecard_json))
    if not args.json:
        print(f"  Evaluation report saved to: {evaluation_report_path}")
        print(f"  Scorecard saved to: {scorecard_md_path}")
        print()

    # Exit with appropriate code
    sys.exit(0 if report.score >= 0.5 else 1)


if __name__ == "__main__":
    main()
