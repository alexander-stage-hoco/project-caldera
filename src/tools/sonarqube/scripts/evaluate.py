#!/usr/bin/env python3
"""
Evaluation orchestrator for SonarQube analysis outputs.

Runs programmatic checks against analysis outputs and generates scorecards.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.checks import (
    CheckResult,
    EvaluationReport,
    load_analysis,
    load_ground_truth,
)
from scripts.checks.accuracy import run_accuracy_checks
from scripts.checks.coverage import run_coverage_checks
from scripts.checks.completeness import run_completeness_checks
from scripts.checks.edge_cases import run_edge_case_checks
from scripts.checks.performance import run_performance_checks


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
    MAGENTA = "\033[35m"


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
# Evaluation Functions
# =============================================================================

def run_all_checks(
    data: dict,
    ground_truth: dict | None,
    skip_performance: bool = False,
) -> list[CheckResult]:
    """Run all evaluation checks on analysis data."""
    checks = []

    # Run checks by category
    checks.extend(run_accuracy_checks(data, ground_truth))
    checks.extend(run_coverage_checks(data, ground_truth))
    checks.extend(run_completeness_checks(data, ground_truth))
    checks.extend(run_edge_case_checks(data, ground_truth))

    if not skip_performance:
        checks.extend(run_performance_checks(data, ground_truth))

    return checks


def determine_decision(score: float) -> str:
    """Determine pass/fail decision based on score (0-1)."""
    normalized = score * 5  # Convert to 0-5 scale
    if normalized >= 4.0:
        return "STRONG_PASS"
    elif normalized >= 3.5:
        return "PASS"
    elif normalized >= 3.0:
        return "WEAK_PASS"
    return "FAIL"


def generate_scorecard(report: EvaluationReport) -> dict[str, Any]:
    """Generate structured scorecard JSON from evaluation report."""
    # Group checks by category
    category_data: dict[str, dict] = {}
    for check in report.checks:
        cat = check.category.value
        if cat not in category_data:
            category_data[cat] = {
                "passed": 0,
                "total": 0,
                "score_sum": 0.0,
                "checks": [],
            }
        category_data[cat]["total"] += 1
        category_data[cat]["score_sum"] += check.score
        if check.passed:
            category_data[cat]["passed"] += 1
        category_data[cat]["checks"].append({
            "check_id": check.check_id,
            "name": check.name,
            "passed": check.passed,
            "score": round(check.score, 4),
            "message": check.message,
        })

    # Build dimensions data
    dimensions = []
    for i, (cat_name, data) in enumerate(category_data.items()):
        cat_score = data["score_sum"] / data["total"] if data["total"] > 0 else 0
        dimensions.append({
            "id": f"D{i+1}",
            "name": cat_name.replace("_", " ").title(),
            "weight": 1.0 / len(category_data) if category_data else 1.0,
            "total_checks": data["total"],
            "passed": data["passed"],
            "failed": data["total"] - data["passed"],
            "score": round(cat_score, 4),
            "weighted_score": round(cat_score / len(category_data), 4) if category_data else 0,
            "checks": data["checks"],
        })

    return {
        "tool": "sonarqube",
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "description": "Evaluation scorecard for SonarQube static analysis",
        "summary": {
            "total_checks": report.total,
            "passed": report.passed,
            "failed": report.failed,
            "score": round(report.score, 4),
            "score_percent": round(report.score * 100, 2),
            "normalized_score": round(report.score * 5, 2),  # 0-5 scale
            "decision": determine_decision(report.score),
        },
        "dimensions": dimensions,
        "score_by_category": {k: round(v, 4) for k, v in report.score_by_category.items()},
        "thresholds": {
            "STRONG_PASS": ">= 4.0 (80%+)",
            "PASS": ">= 3.5 (70%+)",
            "WEAK_PASS": ">= 3.0 (60%+)",
            "FAIL": "< 3.0 (below 60%)",
        },
    }


def generate_scorecard_md(scorecard: dict) -> str:
    """Generate comprehensive markdown scorecard."""
    summary = scorecard.get("summary", {})
    dimensions = scorecard.get("dimensions", [])
    thresholds = scorecard.get("thresholds", {})

    lines = [
        "# SonarQube Evaluation Scorecard",
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
            score_pct = dim.get("score", 0) * 100
            lines.append(
                f"| {dim.get('name', '')} | {dim.get('total_checks', 0)} | "
                f"{dim.get('passed', 0)}/{dim.get('total_checks', 0)} | {score_pct:.1f}% |"
            )
        lines.append("")

    # Critical failures (checks with passed=False and severity=critical)
    critical_failures = [
        check
        for dim in dimensions
        for check in dim.get("checks", [])
        if not check.get("passed") and "critical" in check.get("check_id", "").lower()
    ]
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
            lines.append("| Check | Status | Score | Message |")
            lines.append("|-------|--------|-------|---------|")
            for check in dim.get("checks", []):
                status = "PASS" if check.get("passed") else "FAIL"
                score = check.get("score", 0)
                msg = check.get("message", "")
                msg = msg[:50] + "..." if len(msg) > 50 else msg
                lines.append(f"| {check.get('check_id', '')} | {status} | {score:.2f} | {msg} |")
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
    lines.append("*Generated by SonarQube evaluation framework*")

    return "\n".join(lines)


def print_report(report: EvaluationReport):
    """Print evaluation report to console."""
    print()
    print(c("=" * 70, Colors.MAGENTA))
    print(c("  SONARQUBE EVALUATION REPORT", Colors.MAGENTA, Colors.BOLD))
    print(c("=" * 70, Colors.MAGENTA))
    print()

    # Summary
    print(c("SUMMARY", Colors.BLUE, Colors.BOLD))
    print(c("-" * 40, Colors.BLUE))
    score_color = Colors.GREEN if report.score >= 0.8 else (Colors.YELLOW if report.score >= 0.6 else Colors.RED)
    print(f"  Score: {c(f'{report.score:.1%}', score_color, Colors.BOLD)} ({report.passed}/{report.total} checks passed)")
    print(f"  Decision: {c(determine_decision(report.score), score_color)}")
    print()

    # Per-category results
    print(c("CATEGORY RESULTS", Colors.BLUE, Colors.BOLD))
    print(c("-" * 40, Colors.BLUE))

    for cat, cat_score in sorted(report.score_by_category.items()):
        passed, total = report.passed_by_category.get(cat, (0, 0))
        score_color = Colors.GREEN if cat_score >= 0.8 else (Colors.YELLOW if cat_score >= 0.6 else Colors.RED)
        print(f"  {cat:20} {c(f'{cat_score:.1%}', score_color):>8}  ({passed}/{total})")

    print()

    # Failed checks
    failed_checks = [c for c in report.checks if not c.passed]
    if failed_checks:
        print(c("FAILED CHECKS", Colors.RED, Colors.BOLD))
        print(c("-" * 40, Colors.RED))
        for check in failed_checks:
            print(f"  {c('✗', Colors.RED)} [{check.check_id}] {check.name}")
            print(f"      {check.message}")
        print()

    # Final decision
    decision = determine_decision(report.score)
    if decision in ["STRONG_PASS", "PASS"]:
        decision_str = c(decision, Colors.GREEN, Colors.BOLD)
    elif decision == "WEAK_PASS":
        decision_str = c(decision, Colors.YELLOW)
    else:
        decision_str = c(decision, Colors.RED, Colors.BOLD)

    print(c("=" * 70, Colors.MAGENTA))
    print(f"  DECISION: {decision_str}  (Score: {report.score:.1%})")
    print(c("=" * 70, Colors.MAGENTA))
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate SonarQube analysis outputs"
    )
    parser.add_argument(
        "--analysis", "-a",
        required=True,
        help="Path to analysis JSON file",
    )
    parser.add_argument(
        "--ground-truth", "-g",
        help="Path to ground truth directory or file",
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

    # Load analysis data
    analysis_path = Path(args.analysis)
    if not analysis_path.exists():
        print(f"Error: Analysis file not found: {analysis_path}", file=sys.stderr)
        sys.exit(1)

    data = load_analysis(analysis_path)

    # Load ground truth if provided
    ground_truth = None
    ground_truth_dir = args.ground_truth
    if ground_truth_dir:
        gt_path = Path(ground_truth_dir)
        if gt_path.is_file():
            with open(gt_path) as f:
                ground_truth = json.load(f)
        elif gt_path.is_dir():
            # Try to find matching ground truth by repo name
            repo_name = analysis_path.stem
            if repo_name == "output":
                # Try parent directory name
                repo_name = analysis_path.parent.name
            ground_truth = load_ground_truth(gt_path, repo_name)

    # Run evaluation
    if not args.json:
        print(c("\nRunning programmatic evaluation...", Colors.CYAN, Colors.BOLD))

    checks = run_all_checks(data, ground_truth, skip_performance=args.quick)

    report = EvaluationReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        analysis_path=str(analysis_path),
        ground_truth_dir=str(args.ground_truth) if args.ground_truth else "",
        checks=checks,
    )

    # Generate outputs
    if args.json:
        output_data = report.to_dict()
        print(json.dumps(output_data, indent=2))
    else:
        print_report(report)

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        if not args.json:
            print(f"  Results saved to: {output_path}")

    # Generate compliance artifacts
    eval_output_dir = os.environ.get("EVAL_OUTPUT_DIR")
    if eval_output_dir:
        out_dir = Path(eval_output_dir)
    elif args.output:
        out_dir = Path(args.output).parent if Path(args.output).suffix else Path(args.output)
    else:
        out_dir = Path(__file__).parent.parent / "evaluation" / "results"

    out_dir.mkdir(parents=True, exist_ok=True)
    scorecard = generate_scorecard(report)
    # Output uniform evaluation_report.json for compliance
    evaluation_report_path = out_dir / "evaluation_report.json"
    evaluation_report = {
        "timestamp": report.timestamp,
        "tool": "sonarqube",
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
        json.dump(scorecard, f, indent=2)
    scorecard_md_path.write_text(generate_scorecard_md(scorecard))
    if not args.json:
        print(f"  Scorecard saved to: {scorecard_md_path}")
        print()

    # Exit with appropriate code
    sys.exit(0 if report.score >= 0.6 else 1)


if __name__ == "__main__":
    main()
