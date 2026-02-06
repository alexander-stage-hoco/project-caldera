"""Programmatic evaluation script for dotcover."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any


def load_checks() -> list[tuple[str, Any]]:
    """Load all check modules from scripts/checks/."""
    checks_dir = Path(__file__).parent / "checks"
    check_modules = []

    for check_file in sorted(checks_dir.glob("*.py")):
        if check_file.name.startswith("_"):
            continue
        module_name = f"scripts.checks.{check_file.stem}"
        try:
            module = importlib.import_module(module_name)
            check_modules.append((check_file.stem, module))
        except ImportError as e:
            print(f"Warning: Could not load {module_name}: {e}", file=sys.stderr)

    return check_modules


def run_checks(output: dict, ground_truth: dict | None) -> list[dict]:
    """Run all checks and collect results."""
    results = []
    check_modules = load_checks()

    for name, module in check_modules:
        # Find all check_* functions in the module
        for attr_name in dir(module):
            if not attr_name.startswith("check_"):
                continue
            check_fn = getattr(module, attr_name)
            if not callable(check_fn):
                continue

            try:
                result = check_fn(output, ground_truth)
                if isinstance(result, dict):
                    results.append(result)
                elif isinstance(result, list):
                    results.extend(result)
            except Exception as e:
                results.append({
                    "check_id": f"{name}.{attr_name}",
                    "status": "error",
                    "message": str(e),
                })

    return results


def compute_summary(results: list[dict]) -> dict:
    """Compute summary statistics from check results."""
    total = len(results)
    passed = sum(1 for r in results if r.get("status") == "pass")
    failed = sum(1 for r in results if r.get("status") == "fail")
    warned = sum(1 for r in results if r.get("status") == "warn")
    errored = sum(1 for r in results if r.get("status") == "error")

    score = passed / total if total > 0 else 0.0

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "warned": warned,
        "errored": errored,
        "score": round(score, 4),
        "decision": "PASS" if failed == 0 and errored == 0 else "FAIL",
    }


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


def generate_scorecard_json(results: list[dict], summary: dict) -> dict:
    """Generate structured scorecard JSON data from evaluation results."""
    from datetime import datetime, timezone

    # Group checks by category
    category_data: dict[str, dict] = {}
    for check in results:
        # Extract category from check_id (e.g., "accuracy.check_foo" -> "accuracy")
        check_id = check.get("check_id", "unknown")
        category = check_id.split(".")[0] if "." in check_id else "general"

        if category not in category_data:
            category_data[category] = {
                "checks": [],
                "passed": 0,
                "failed": 0,
            }

        is_passed = check.get("status") == "pass"
        category_data[category]["checks"].append({
            "check_id": check_id,
            "name": check_id,
            "passed": is_passed,
            "message": check.get("message", ""),
        })
        if is_passed:
            category_data[category]["passed"] += 1
        else:
            category_data[category]["failed"] += 1

    # Build dimensions data
    dimensions_data = []
    num_categories = len(category_data) if category_data else 1
    for i, (category, data) in enumerate(sorted(category_data.items())):
        total = data["passed"] + data["failed"]
        score = (data["passed"] / total * 5.0) if total > 0 else 0
        dimensions_data.append({
            "id": f"D{i+1}",
            "name": category.replace("_", " ").title(),
            "weight": 1.0 / num_categories,
            "total_checks": total,
            "passed": data["passed"],
            "failed": data["failed"],
            "score": round(score, 2),
            "weighted_score": round(score / num_categories, 2),
            "checks": data["checks"],
        })

    overall_score = summary.get("score", 0)
    normalized_score = overall_score * 5.0

    return {
        "tool": "dotcover",
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "description": "Evaluation scorecard for dotCover code coverage analysis",
        "summary": {
            "total_checks": summary.get("total", 0),
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "score": round(overall_score, 4),
            "score_percent": round(overall_score * 100, 2),
            "normalized_score": round(normalized_score, 2),
            "decision": determine_decision(overall_score),
        },
        "dimensions": dimensions_data,
        "critical_failures": [
            {
                "check_id": c["check_id"],
                "name": c["name"],
                "message": c["message"],
            }
            for d in dimensions_data
            for c in d["checks"]
            if not c["passed"] and "critical" in c["check_id"].lower()
        ],
        "thresholds": {
            "STRONG_PASS": ">= 4.0 (80%+)",
            "PASS": ">= 3.5 (70%+)",
            "WEAK_PASS": ">= 3.0 (60%+)",
            "FAIL": "< 3.0 (below 60%)",
        },
        "metadata": {},
    }


def generate_scorecard_md(scorecard: dict) -> str:
    """Generate comprehensive markdown scorecard."""
    summary = scorecard.get("summary", {})
    dimensions = scorecard.get("dimensions", [])
    critical_failures = scorecard.get("critical_failures", [])
    thresholds = scorecard.get("thresholds", {})

    lines = [
        "# dotCover Evaluation Scorecard",
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
    lines.append("*Generated by dotCover evaluation framework*")

    return "\n".join(lines)


def save_scorecards(results: list[dict], summary: dict, output_dir: Path) -> None:
    """Save scorecard files (JSON and Markdown)."""
    scorecard = generate_scorecard_json(results, summary)

    # Save JSON
    json_path = output_dir / "scorecard.json"
    json_path.write_text(json.dumps(scorecard, indent=2))
    print(f"Scorecard JSON saved to: {json_path}")

    # Save Markdown
    md_path = output_dir / "scorecard.md"
    md_path.write_text(generate_scorecard_md(scorecard))
    print(f"Scorecard Markdown saved to: {md_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run programmatic evaluation")
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--ground-truth-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    # Load analysis output
    output_path = args.results_dir / "output.json"
    if not output_path.exists():
        # Try finding in subdirectories
        candidates = list(args.results_dir.glob("*/output.json"))
        if candidates:
            output_path = max(candidates, key=lambda p: p.stat().st_mtime)
        else:
            print(f"Error: No output.json found in {args.results_dir}", file=sys.stderr)
            return 1

    output = json.loads(output_path.read_text())

    # Load ground truth if available
    ground_truth = None
    gt_path = args.ground_truth_dir / "synthetic.json"
    if gt_path.exists():
        ground_truth = json.loads(gt_path.read_text())

    # Run checks
    results = run_checks(output, ground_truth)
    summary = compute_summary(results)

    # Write report with top-level decision and score for compliance
    from datetime import datetime, timezone
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "analysis_path": str(output_path),
        "ground_truth_dir": str(args.ground_truth_dir),
        "decision": determine_decision(summary["score"]),
        "score": summary["score"],
        "summary": summary,
        "checks": results,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))

    # Save scorecards
    eval_dir = Path(__file__).parent.parent / "evaluation"
    save_scorecards(results, summary, eval_dir)

    print(f"Evaluation complete. Decision: {summary['decision']}")
    print(f"Score: {summary['score']:.1%} ({summary['passed']}/{summary['total']} passed)")

    return 0 if summary["decision"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
