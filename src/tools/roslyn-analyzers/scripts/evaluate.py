#!/usr/bin/env python3
"""
Programmatic Evaluation Orchestrator for Roslyn Analyzers PoC.

Runs all 28 programmatic checks (AC-1 to AC-10, CV-1 to CV-8,
EC-1 to EC-8, PF-1 to PF-4) and generates evaluation report.

Usage:
    python scripts/evaluate.py \
        --analysis output/runs/roslyn_analysis.json \
        --ground-truth evaluation/ground-truth \
        --output output/runs/evaluation_report.json
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from checks import (
    CheckResult,
    EvaluationReport,
    load_analysis_results,
    load_ground_truth,
)
from checks.accuracy import run_all_accuracy_checks
from checks.coverage import run_all_coverage_checks
from checks.edge_cases import run_all_edge_case_checks
from checks.performance import run_all_performance_checks


# Category weights for overall score
CATEGORY_WEIGHTS = {
    "accuracy": 0.40,
    "coverage": 0.25,
    "edge_cases": 0.20,
    "performance": 0.15,
}


def compute_category_scores(checks: list[CheckResult]) -> dict:
    """Compute weighted scores by category."""
    category_results: dict[str, list[CheckResult]] = {}

    for check in checks:
        cat = check.category
        if cat not in category_results:
            category_results[cat] = []
        category_results[cat].append(check)

    scores = {}
    for cat, results in category_results.items():
        weight = CATEGORY_WEIGHTS.get(cat, 0.0)
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        score = passed / total if total > 0 else 0

        scores[cat] = {
            "weight": weight,
            "checks_total": total,
            "checks_passed": passed,
            "score": score,
            "weighted_score": score * weight,
        }

    return scores


def compute_overall_score(category_scores: dict) -> float:
    """Compute overall weighted score."""
    return sum(cs["weighted_score"] for cs in category_scores.values())


def determine_decision(overall_score: float, category_scores: dict) -> tuple[str, str]:
    """Determine pass/fail decision based on score and category minimums."""
    # Check category minimums (all must be >= 70%)
    category_failures = []
    for cat, cs in category_scores.items():
        if cs["score"] < 0.70:
            category_failures.append(f"{cat} ({cs['score']*100:.1f}%)")

    if category_failures:
        return "FAIL", f"Category minimum not met: {', '.join(category_failures)}"

    # Check overall thresholds
    if overall_score >= 0.80:
        return "STRONG_PASS", f"Score {overall_score:.3f} >= 0.80 (STRONG_PASS threshold)"
    elif overall_score >= 0.70:
        return "PASS", f"Score {overall_score:.3f} >= 0.70 (PASS threshold)"
    elif overall_score >= 0.60:
        return "WEAK_PASS", f"Score {overall_score:.3f} >= 0.60 (WEAK_PASS threshold)"
    else:
        return "FAIL", f"Score {overall_score:.3f} < 0.60 (below minimum threshold)"


def generate_scorecard_json(report: EvaluationReport) -> dict:
    """Generate structured scorecard JSON data from evaluation report."""
    dimensions_data = []
    for i, (category, cs) in enumerate(report.category_scores.items()):
        category_checks = [c for c in report.checks if c["category"] == category]
        dimensions_data.append({
            "id": f"D{i+1}",
            "name": category.replace("_", " ").title(),
            "weight": cs["weight"],
            "total_checks": cs["checks_total"],
            "passed": cs["checks_passed"],
            "failed": cs["checks_total"] - cs["checks_passed"],
            "score": round(cs["score"] * 5.0, 2),
            "weighted_score": round(cs["weighted_score"] * 5.0, 2),
            "checks": [
                {
                    "check_id": c["check_id"],
                    "name": c["name"],
                    "passed": c["passed"],
                    "message": c["message"],
                }
                for c in category_checks
            ],
        })

    overall_score = report.summary["overall_score"]
    normalized_score = overall_score * 5.0

    return {
        "tool": "roslyn-analyzers",
        "version": "1.0.0",
        "generated_at": report.timestamp,
        "description": "Evaluation scorecard for Roslyn Analyzers C# analysis",
        "summary": {
            "total_checks": report.summary["total_checks"],
            "passed": report.summary["passed"],
            "failed": report.summary["failed"],
            "score": round(overall_score, 4),
            "score_percent": round(overall_score * 100, 2),
            "normalized_score": round(normalized_score, 2),
            "decision": report.decision,
        },
        "dimensions": dimensions_data,
        "critical_failures": [
            {
                "check_id": c["check_id"],
                "name": c["name"],
                "message": c["message"],
            }
            for c in report.checks
            if not c["passed"] and "critical" in c["check_id"].lower()
        ],
        "thresholds": {
            "STRONG_PASS": ">= 4.0 (80%+)",
            "PASS": ">= 3.5 (70%+)",
            "WEAK_PASS": ">= 3.0 (60%+)",
            "FAIL": "< 3.0 (below 60%)",
        },
        "metadata": {
            "analysis_file": report.analysis_file,
        },
    }


def generate_scorecard_md(scorecard: dict) -> str:
    """Generate comprehensive markdown scorecard."""
    summary = scorecard.get("summary", {})
    dimensions = scorecard.get("dimensions", [])
    critical_failures = scorecard.get("critical_failures", [])
    thresholds = scorecard.get("thresholds", {})

    lines = [
        "# Roslyn Analyzers Evaluation Scorecard",
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
    if metadata.get("analysis_file"):
        lines.append(f"*Analysis: `{metadata.get('analysis_file')}`*")

    return "\n".join(lines)


def render_report(report: EvaluationReport, console: Console | None = None):
    """Render evaluation report to terminal."""
    if not RICH_AVAILABLE or console is None:
        print_simple_report(report)
        return

    console.print()
    console.print(Panel.fit(
        "[bold blue]Roslyn Analyzers[/bold blue] - Programmatic Evaluation",
        border_style="blue"
    ))

    # Summary table
    summary = report.summary
    summary_table = Table(title="Evaluation Summary", show_header=True)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")

    summary_table.add_row("Total Checks", str(summary["total_checks"]))
    summary_table.add_row("Passed", f"[green]{summary['passed']}[/green]")
    summary_table.add_row("Failed", f"[red]{summary['failed']}[/red]")
    summary_table.add_row("Pass Rate", f"{summary['pass_rate_pct']:.1f}%")
    summary_table.add_row("Overall Score", f"{summary['overall_score']:.3f}")

    decision_color = {
        "STRONG_PASS": "bold green",
        "PASS": "green",
        "WEAK_PASS": "yellow",
        "FAIL": "red",
    }.get(report.decision, "white")
    summary_table.add_row("Decision", f"[{decision_color}]{report.decision}[/{decision_color}]")

    console.print(summary_table)
    console.print()

    # Category breakdown table
    cat_table = Table(title="Category Scores", show_header=True)
    cat_table.add_column("Category", style="cyan")
    cat_table.add_column("Passed/Total", style="yellow")
    cat_table.add_column("Score", style="green")
    cat_table.add_column("Weight", style="dim")
    cat_table.add_column("Weighted", style="blue")

    for cat, cs in report.category_scores.items():
        score_color = "green" if cs["score"] >= 0.70 else "red"
        cat_table.add_row(
            cat.replace("_", " ").title(),
            f"{cs['checks_passed']}/{cs['checks_total']}",
            f"[{score_color}]{cs['score']*100:.1f}%[/{score_color}]",
            f"{cs['weight']*100:.0f}%",
            f"{cs['weighted_score']:.3f}",
        )

    console.print(cat_table)
    console.print()

    # Individual checks table
    checks_table = Table(title="Check Results", show_header=True)
    checks_table.add_column("ID", style="cyan", width=6)
    checks_table.add_column("Name", style="white", width=30)
    checks_table.add_column("Status", style="white", width=8)
    checks_table.add_column("Score", style="white", width=8)
    checks_table.add_column("Message", style="dim", width=40)

    for check in report.checks:
        status = "[green]PASS[/green]" if check["passed"] else "[red]FAIL[/red]"
        score_color = "green" if check["score"] >= 0.80 else ("yellow" if check["score"] >= 0.50 else "red")
        msg = check["message"]
        checks_table.add_row(
            check["check_id"],
            check["name"],
            status,
            f"[{score_color}]{check['score']:.2f}[/{score_color}]",
            msg[:40] + "..." if len(msg) > 40 else msg,
        )

    console.print(checks_table)
    console.print()

    # Decision
    console.print(Panel(
        f"[{decision_color}]{report.decision}[/{decision_color}]: {report.decision_reason}",
        title="Final Decision",
        border_style=decision_color.replace("bold ", ""),
    ))


def print_simple_report(report: EvaluationReport):
    """Print simple text report without rich."""
    print("\n" + "=" * 70)
    print("ROSLYN ANALYZERS - PROGRAMMATIC EVALUATION")
    print("=" * 70)

    summary = report.summary
    print(f"Total Checks: {summary['total_checks']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Pass Rate: {summary['pass_rate_pct']:.1f}%")
    print(f"Overall Score: {summary['overall_score']:.3f}")
    print(f"Decision: {report.decision}")
    print()

    print("Category Scores:")
    for cat, cs in report.category_scores.items():
        print(f"  {cat}: {cs['checks_passed']}/{cs['checks_total']} ({cs['score']*100:.1f}%)")
    print()

    print("Check Results:")
    for check in report.checks:
        status = "PASS" if check["passed"] else "FAIL"
        msg = check["message"][:50]
        print(f"  [{check['check_id']}] {status}: {check['name']} - {msg}")

    print()
    print(f"Decision: {report.decision}")
    print(f"Reason: {report.decision_reason}")
    print("=" * 70)


def run_evaluation(
    analysis_path: str,
    ground_truth_path: str,
    output_path: str | None = None,
    json_only: bool = False,
    quick: bool = False,
) -> EvaluationReport:
    """Run full programmatic evaluation."""
    console = Console() if RICH_AVAILABLE and not json_only else None

    # Load data
    if console:
        console.print("[cyan]Loading analysis results...[/cyan]")
    analysis = load_analysis_results(analysis_path)

    if console:
        console.print("[cyan]Loading ground truth...[/cyan]")
    ground_truth = load_ground_truth(ground_truth_path)

    # Run all checks
    all_checks: list[CheckResult] = []

    if console:
        console.print("[cyan]Running accuracy checks (AC-1 to AC-10)...[/cyan]")
    all_checks.extend(run_all_accuracy_checks(analysis, ground_truth))

    if console:
        console.print("[cyan]Running coverage checks (CV-1 to CV-8)...[/cyan]")
    all_checks.extend(run_all_coverage_checks(analysis, ground_truth))

    if console:
        console.print("[cyan]Running edge case checks (EC-1 to EC-8)...[/cyan]")
    all_checks.extend(run_all_edge_case_checks(analysis, ground_truth))

    if not quick:
        if console:
            console.print("[cyan]Running performance checks (PF-1 to PF-4)...[/cyan]")
        all_checks.extend(run_all_performance_checks(analysis, ground_truth))

    # Compute scores
    category_scores = compute_category_scores(all_checks)
    overall_score = compute_overall_score(category_scores)
    decision, reason = determine_decision(overall_score, category_scores)

    # Build summary
    passed_count = sum(1 for c in all_checks if c.passed)
    failed_count = len(all_checks) - passed_count

    summary = {
        "total_checks": len(all_checks),
        "passed": passed_count,
        "failed": failed_count,
        "skipped": 0,
        "pass_rate_pct": (passed_count / len(all_checks) * 100) if all_checks else 0,
        "overall_score": overall_score,
    }

    # Create report
    report = EvaluationReport(
        evaluation_id=f"eval-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        analysis_file=analysis_path,
        summary=summary,
        category_scores=category_scores,
        checks=[asdict(c) for c in all_checks],
        decision=decision,
        decision_reason=reason,
    )

    # Render report
    if not json_only:
        render_report(report, console)

    # Save output
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump({
                "evaluation_id": report.evaluation_id,
                "timestamp": report.timestamp,
                "analysis_file": report.analysis_file,
                "summary": report.summary,
                "category_scores": report.category_scores,
                "checks": report.checks,
                "decision": report.decision,
                "decision_reason": report.decision_reason,
            }, f, indent=2)

        if console:
            console.print(f"\n[green]Report saved to {output_path}[/green]")
        elif not json_only:
            print(f"\nReport saved to {output_path}")

    # JSON-only output
    if json_only:
        print(json.dumps({
            "evaluation_id": report.evaluation_id,
            "timestamp": report.timestamp,
            "summary": report.summary,
            "decision": report.decision,
        }, indent=2))

    # Generate and save scorecard files
    scorecard_json = generate_scorecard_json(report)
    if output_path:
        out_dir = Path(output_path).parent if Path(output_path).suffix else Path(output_path)
    else:
        out_dir = Path(__file__).parent.parent / "evaluation" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Output uniform evaluation_report.json for compliance
    evaluation_report_path = out_dir / "evaluation_report.json"
    evaluation_report = {
        "timestamp": report.timestamp,
        "tool": "roslyn-analyzers",
        "decision": report.decision,
        "score": round(report.summary["overall_score"], 4),
        "checks": [
            {
                "name": c["check_id"],
                "status": "PASS" if c["passed"] else "FAIL",
                "message": c["message"],
            }
            for c in report.checks
        ],
        "summary": {
            "total": report.summary["total_checks"],
            "passed": report.summary["passed"],
            "failed": report.summary["failed"],
        },
    }
    with open(evaluation_report_path, "w") as f:
        json.dump(evaluation_report, f, indent=2)

    scorecard_json_path = out_dir / "scorecard.json"
    scorecard_md_path = out_dir / "scorecard.md"
    with open(scorecard_json_path, "w") as f:
        json.dump(scorecard_json, f, indent=2)
    scorecard_md_path.write_text(generate_scorecard_md(scorecard_json))
    if console:
        console.print(f"[green]Evaluation report saved to {evaluation_report_path}[/green]")
        console.print(f"[green]Scorecard saved to {scorecard_md_path}[/green]")
    elif not json_only:
        print(f"Evaluation report saved to {evaluation_report_path}")
        print(f"Scorecard saved to {scorecard_md_path}")

    return report


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run programmatic evaluation for Roslyn Analyzers PoC"
    )
    parser.add_argument(
        "--analysis", "-a",
        required=True,
        help="Path to analysis results JSON file"
    )
    parser.add_argument(
        "--ground-truth", "-g",
        required=True,
        help="Path to ground truth directory or JSON file"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output report JSON file path"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON only (no terminal formatting)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Skip performance checks for faster evaluation"
    )

    args = parser.parse_args()

    try:
        report = run_evaluation(
            args.analysis,
            args.ground_truth,
            args.output,
            args.json,
            args.quick,
        )

        # Exit with appropriate code
        if report.decision in ["STRONG_PASS", "PASS"]:
            sys.exit(0)
        elif report.decision == "WEAK_PASS":
            sys.exit(0)  # Still a pass
        else:
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
