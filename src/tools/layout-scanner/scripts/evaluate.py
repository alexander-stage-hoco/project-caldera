#!/usr/bin/env python3
"""
Evaluation Orchestrator for Layout Scanner.

Runs all evaluation checks against scanner output and produces
a comprehensive evaluation report.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .checks import (
    CheckCategory,
    CheckResult,
    DimensionResult,
    calculate_overall_score,
    get_decision,
    score_from_table,
)
from .checks.accuracy import run_accuracy_checks
from .checks.classification import run_classification_checks
from .checks.content_metadata import run_content_metadata_checks
from .checks.edge_cases import run_edge_case_checks
from .checks.git_metadata import run_git_metadata_checks
from .checks.output_quality import run_output_quality_checks
from .checks.performance import run_performance_checks
from .report_formatter import EvaluationResult, ReportFormatter


def generate_scorecard_json(summary: Dict[str, Any], results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate structured scorecard JSON data from evaluation results."""
    from datetime import datetime, timezone

    # Group checks by dimension/category
    dimension_data: Dict[str, Dict] = {}
    for repo_result in results:
        for dim in repo_result.get("dimensions", []):
            cat_name = dim.get("category", "unknown")
            if cat_name not in dimension_data:
                dimension_data[cat_name] = {
                    "checks": [],
                    "passed": 0,
                    "failed": 0,
                    "scores": [],
                }
            for check in dim.get("checks", []):
                dimension_data[cat_name]["checks"].append({
                    "check_id": check.get("check_id", ""),
                    "name": check.get("name", check.get("check_id", "")),
                    "passed": check.get("passed", False),
                    "message": check.get("message", ""),
                })
                if check.get("passed"):
                    dimension_data[cat_name]["passed"] += 1
                else:
                    dimension_data[cat_name]["failed"] += 1
            dimension_data[cat_name]["scores"].append(dim.get("score", 0))

    # Build dimensions array
    dimensions = []
    num_categories = len(dimension_data) if dimension_data else 1
    for i, (cat_name, data) in enumerate(sorted(dimension_data.items())):
        total = data["passed"] + data["failed"]
        avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
        dimensions.append({
            "id": f"D{i+1}",
            "name": cat_name.replace("_", " ").title(),
            "weight": 1.0 / num_categories,
            "total_checks": total,
            "passed": data["passed"],
            "failed": data["failed"],
            "score": round(avg_score, 2),
            "weighted_score": round(avg_score / num_categories, 2),
            "checks": data["checks"],
        })

    avg_score = summary.get("average_score", 0)
    score_normalized = avg_score  # Already on 0-5 scale

    return {
        "tool": "layout-scanner",
        "version": "1.0.0",
        "generated_at": summary.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "description": "Evaluation scorecard for Layout Scanner repository analysis",
        "summary": {
            "total_checks": sum(d["total_checks"] for d in dimensions),
            "passed": sum(d["passed"] for d in dimensions),
            "failed": sum(d["failed"] for d in dimensions),
            "score": round(avg_score / 5.0, 4) if avg_score else 0,
            "score_percent": round(avg_score / 5.0 * 100, 2) if avg_score else 0,
            "normalized_score": round(score_normalized, 2),
            "decision": summary.get("decision", "FAIL"),
        },
        "dimensions": dimensions,
        "critical_failures": [
            {
                "check_id": c["check_id"],
                "name": c["name"],
                "message": c["message"],
            }
            for d in dimensions
            for c in d["checks"]
            if not c["passed"] and "critical" in c["check_id"].lower()
        ],
        "thresholds": {
            "STRONG_PASS": ">= 4.0 (80%+)",
            "PASS": ">= 3.5 (70%+)",
            "WEAK_PASS": ">= 3.0 (60%+)",
            "FAIL": "< 3.0 (below 60%)",
        },
        "metadata": {
            "evaluated_count": summary.get("evaluated_count", 0),
        },
    }


def generate_scorecard_md(scorecard: Dict[str, Any]) -> str:
    """Generate comprehensive markdown scorecard."""
    summary = scorecard.get("summary", {})
    dimensions = scorecard.get("dimensions", [])
    critical_failures = scorecard.get("critical_failures", [])
    thresholds = scorecard.get("thresholds", {})

    lines = [
        "# Layout Scanner Evaluation Scorecard",
        "",
        f"**Generated:** {scorecard.get('generated_at', '')}",
        f"**Decision:** {summary.get('decision', '')}",
        f"**Score:** {summary.get('normalized_score', 0)}/5.0",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Evaluated Outputs | {scorecard.get('metadata', {}).get('evaluated_count', 0)} |",
        f"| Total Checks | {summary.get('total_checks', 0)} |",
        f"| Passed | {summary.get('passed', 0)} |",
        f"| Failed | {summary.get('failed', 0)} |",
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
    lines.append("*Generated by Layout Scanner evaluation framework*")

    return "\n".join(lines)


def load_output(path: Path) -> Dict[str, Any]:
    """Load scanner output from JSON file."""
    with open(path) as f:
        payload = json.load(f)
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            return {}
    if isinstance(payload, dict) and "metadata" in payload and "data" in payload:
        data = payload["data"]
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}
        payload = data if isinstance(data, dict) else {}

    if not isinstance(payload, dict):
        return {}

    # Normalize files/directories if they are lists
    files = payload.get("files")
    if isinstance(files, list):
        normalized = {}
        for item in files:
            if isinstance(item, dict):
                key = item.get("path") or item.get("name") or str(len(normalized))
                normalized[key] = item
            elif isinstance(item, str):
                normalized[item] = {"path": item, "name": Path(item).name}
        payload["files"] = normalized
    elif isinstance(files, dict):
        normalized = {}
        for key, item in files.items():
            if isinstance(item, dict):
                normalized[key] = item
            elif isinstance(item, str):
                normalized[key] = {"path": item, "name": Path(item).name}
        payload["files"] = normalized
    elif files is not None:
        payload["files"] = {}

    directories = payload.get("directories")
    if isinstance(directories, list):
        normalized = {}
        for item in directories:
            if isinstance(item, dict):
                key = item.get("path") or item.get("name") or str(len(normalized))
                normalized[key] = item
            elif isinstance(item, str):
                normalized[item] = {"path": item, "name": Path(item).name}
        payload["directories"] = normalized
    elif isinstance(directories, dict):
        normalized = {}
        for key, item in directories.items():
            if isinstance(item, dict):
                normalized[key] = item
            elif isinstance(item, str):
                normalized[key] = {"path": item, "name": Path(item).name}
        payload["directories"] = normalized
    elif directories is not None:
        payload["directories"] = {}

    return payload


def load_ground_truth(name: str, ground_truth_dir: Path) -> Optional[Dict[str, Any]]:
    """Load ground truth for a repository."""
    path = ground_truth_dir / f"{name}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def run_all_checks(
    output: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]] = None,
    schema_path: Optional[Path] = None,
) -> Dict[CheckCategory, List[CheckResult]]:
    """
    Run all evaluation checks.

    Returns dict of category -> list of check results.
    """
    results: Dict[CheckCategory, List[CheckResult]] = {}

    # Output Quality checks
    results[CheckCategory.OUTPUT_QUALITY] = run_output_quality_checks(
        output, schema_path
    )

    # Accuracy checks
    results[CheckCategory.ACCURACY] = run_accuracy_checks(output, ground_truth)

    # Classification checks
    results[CheckCategory.CLASSIFICATION] = run_classification_checks(
        output, ground_truth
    )

    # Performance checks
    results[CheckCategory.PERFORMANCE] = run_performance_checks(output, ground_truth)

    # Edge case checks
    results[CheckCategory.EDGE_CASES] = run_edge_case_checks(output, ground_truth)

    # Git metadata checks (optional - only if git pass completed)
    passes = output.get("passes_completed", [])
    if "git" in passes:
        results[CheckCategory.GIT_METADATA] = run_git_metadata_checks(output)

    # Content metadata checks (optional - only if content pass completed)
    if "content" in passes:
        results[CheckCategory.CONTENT_METADATA] = run_content_metadata_checks(output)

    return results


def compute_dimension_results(
    check_results: Dict[CheckCategory, List[CheckResult]]
) -> List[DimensionResult]:
    """Compute dimension-level results from check results."""
    dimensions = []

    for category, checks in check_results.items():
        passed_count = sum(1 for c in checks if c.passed)
        score = score_from_table(category, passed_count)

        dimension = DimensionResult(
            category=category,
            checks=checks,
            passed_count=passed_count,
            total_count=len(checks),
            score=score,
        )
        dimensions.append(dimension)

    return dimensions


def evaluate_output(
    output_path: Path,
    ground_truth_dir: Optional[Path] = None,
    schema_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Evaluate a single scanner output file.

    Returns evaluation result dict.
    """
    output = load_output(output_path)
    if not isinstance(output, dict):
        output = {}

    # Load ground truth if available
    repo_name = output.get("repository", output_path.stem)
    ground_truth = None

    if ground_truth_dir:
        ground_truth = load_ground_truth(repo_name, ground_truth_dir)

    # Run all checks
    check_results = run_all_checks(output, ground_truth, schema_path)

    # Compute dimension results
    dimension_results = compute_dimension_results(check_results)

    # Calculate overall score
    overall_score = calculate_overall_score(dimension_results)
    decision = get_decision(overall_score)

    # Build result
    total_checks = sum(len(checks) for checks in check_results.values())
    passed_checks = sum(
        sum(1 for c in checks if c.passed) for checks in check_results.values()
    )

    return {
        "repository": repo_name,
        "output_file": str(output_path),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "overall_score": overall_score,
        "decision": decision,
        "summary": {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "pass_rate": round(passed_checks / total_checks * 100, 1) if total_checks > 0 else 0,
        },
        "dimensions": [d.to_dict() for d in dimension_results],
    }


def evaluate_all(
    output_dir: Path,
    ground_truth_dir: Path,
    results_dir: Path,
    schema_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Evaluate all scanner outputs in a directory.

    Returns summary of all evaluations.
    """
    output_files = list(output_dir.glob("*.json"))

    if not output_files:
        print(f"No output files found in {output_dir}")
        return {"error": "No output files found"}

    results = []
    overall_scores = []

    for output_path in sorted(output_files):
        print(f"Evaluating {output_path.name}...")

        try:
            result = evaluate_output(output_path, ground_truth_dir, schema_path)
            results.append(result)
            overall_scores.append(result["overall_score"])

            # Print summary
            print(f"  Score: {result['overall_score']}/5.0 - {result['decision']}")
            print(f"  Checks: {result['summary']['passed_checks']}/{result['summary']['total_checks']} passed")

        except Exception as e:
            print(f"  Error: {e}")
            results.append({
                "repository": output_path.stem,
                "output_file": str(output_path),
                "error": str(e),
            })

    # Compute aggregate
    avg_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0
    aggregate_decision = get_decision(avg_score)

    # Aggregate check totals across all repos
    total_checks = sum(r["summary"]["total_checks"] for r in results if "summary" in r)
    passed_checks = sum(r["summary"]["passed_checks"] for r in results if "summary" in r)

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "evaluated_count": len(results),
        "average_score": round(avg_score, 2),
        "decision": aggregate_decision,
        "score": round(avg_score / 5.0, 4),
        "summary": {
            "total": total_checks,
            "passed": passed_checks,
            "failed": total_checks - passed_checks,
        },
        "checks": [],
        "repositories": results,
    }

    # Save results
    results_dir.mkdir(parents=True, exist_ok=True)
    results_path = results_dir / "evaluation_report.json"

    with open(results_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Generate and save scorecards
    scorecard = generate_scorecard_json(summary, results)

    scorecard_json_path = results_dir / "scorecard.json"
    with open(scorecard_json_path, "w") as f:
        json.dump(scorecard, f, indent=2)

    scorecard_md_path = results_dir / "scorecard.md"
    scorecard_md_path.write_text(generate_scorecard_md(scorecard))

    print(f"\nResults saved to {results_path}")
    print(f"Scorecard saved to {scorecard_md_path}")
    print(f"\nAggregate: {avg_score:.2f}/5.0 - {aggregate_decision}")

    return summary


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate Layout Scanner output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "output" / "runs",
        help="Directory containing scanner outputs",
    )

    parser.add_argument(
        "--ground-truth-dir",
        type=Path,
        default=Path(__file__).parent.parent / "evaluation" / "ground-truth",
        help="Directory containing ground truth files",
    )

    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path(__file__).parent.parent / "evaluation" / "results",
        help="Directory to write evaluation results",
    )

    parser.add_argument(
        "--schema",
        type=Path,
        default=Path(__file__).parent.parent / "schemas" / "layout.json",
        help="Path to JSON schema",
    )

    parser.add_argument(
        "--single",
        type=Path,
        help="Evaluate a single output file",
    )

    parser.add_argument(
        "--category", "-c",
        type=str,
        choices=[
            "output_quality", "accuracy", "classification",
            "performance", "edge_cases", "git_metadata", "content_metadata"
        ],
        help="Filter to specific category",
    )

    parser.add_argument(
        "--format", "-f",
        type=str,
        choices=["table", "json", "markdown", "summary"],
        default="table",
        help="Output format (default: table)",
    )

    parser.add_argument(
        "--status",
        type=str,
        choices=["passed", "failed", "all"],
        default="all",
        help="Filter by check status",
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed evidence for failed checks",
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )

    parsed_args = parser.parse_args(args)

    env_output_dir = os.environ.get("OUTPUT_DIR")
    env_eval_output_dir = os.environ.get("EVAL_OUTPUT_DIR")

    if env_output_dir:
        parsed_args.output_dir = Path(env_output_dir)
    if env_eval_output_dir:
        parsed_args.results_dir = Path(env_eval_output_dir)

    if parsed_args.single:
        # Evaluate single file
        result = evaluate_output(
            parsed_args.single,
            parsed_args.ground_truth_dir,
            parsed_args.schema,
        )

        # Format output using ReportFormatter
        formatter = ReportFormatter(use_color=not parsed_args.no_color)
        eval_result = EvaluationResult.from_dict(result)

        output = formatter.format(
            eval_result,
            format_type=parsed_args.format,
            category_filter=parsed_args.category,
            status_filter=parsed_args.status,
            verbose=parsed_args.verbose,
        )

        print(output)

        return 0 if result["decision"] in ["STRONG_PASS", "PASS"] else 1

    else:
        # Evaluate all
        summary = evaluate_all(
            parsed_args.output_dir,
            parsed_args.ground_truth_dir,
            parsed_args.results_dir,
            parsed_args.schema,
        )

        return 0 if summary.get("decision") in ["STRONG_PASS", "PASS"] else 1


if __name__ == "__main__":
    sys.exit(main())
