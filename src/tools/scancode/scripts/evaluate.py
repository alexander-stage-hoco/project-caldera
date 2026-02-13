#!/usr/bin/env python3
"""Evaluation orchestrator for license analysis PoC."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from checks import EvaluationReport
from checks.accuracy import run_accuracy_checks
from checks.coverage import run_coverage_checks
from checks.detection import run_detection_checks
from checks.performance import run_performance_checks


SCRIPT_DIR = Path(__file__).parent


# =============================================================================
# Scorecard Generation
# =============================================================================


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


def generate_scorecard_json(
    all_reports: list[EvaluationReport],
    total_checks: int,
    total_passed: int,
) -> dict:
    """Generate structured scorecard JSON data from evaluation reports."""
    from datetime import datetime, timezone

    # Aggregate checks by category
    category_data = {}

    for report in all_reports:
        for result in report.results:
            category = getattr(result, "category", "unknown")
            if category not in category_data:
                category_data[category] = {
                    "checks": [],
                    "passed": 0,
                    "failed": 0,
                }

            category_data[category]["checks"].append({
                "check_id": result.check_id,
                "name": getattr(result, "name", result.check_id),
                "passed": result.passed,
                "message": result.message,
            })
            if result.passed:
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

    overall_score = total_passed / total_checks if total_checks > 0 else 0

    return {
        "tool": "scancode",
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "description": "Evaluation scorecard for ScanCode license analysis",
        "summary": {
            "total_checks": total_checks,
            "passed": total_passed,
            "failed": total_checks - total_passed,
            "score": round(overall_score, 4),
            "score_percent": round(overall_score * 100, 2),
            "normalized_score": round(overall_score * 5.0, 2),
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
        "metadata": {
            "repositories_evaluated": len(all_reports),
        },
    }


def generate_scorecard_md(scorecard_json: dict, output_path: Path) -> None:
    """Generate markdown scorecard from JSON data."""
    summary = scorecard_json.get("summary", {})
    dimensions = scorecard_json.get("dimensions", [])

    md_lines = [
        "# Scancode License Analysis Evaluation Scorecard",
        "",
        "## Overview",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| **Tool** | scancode |",
        f"| **Last Evaluated** | {scorecard_json.get('generated_at', 'N/A')[:10]} |",
        f"| **Overall Score** | {summary.get('normalized_score', 0)}/5.0 |",
        f"| **Decision** | {summary.get('decision', 'N/A')} |",
        "",
        "## Summary",
        "",
        "| Category | Passed | Total | Pass Rate |",
        "|----------|--------|-------|-----------|",
    ]

    for dim in dimensions:
        total = dim.get("total_checks", 0)
        passed = dim.get("passed", 0)
        rate = (passed / total * 100) if total > 0 else 0
        md_lines.append(f"| {dim['name']} | {passed} | {total} | {rate:.0f}% |")

    total_checks = summary.get("total_checks", 0)
    total_passed = summary.get("passed", 0)
    overall_rate = summary.get("score_percent", 0)
    md_lines.append(f"| **Overall** | {total_passed} | {total_checks} | {overall_rate:.0f}% |")

    md_lines.extend([
        "",
        "## Dimensions",
        "",
    ])

    for dim in dimensions:
        md_lines.extend([
            f"### {dim['name']}",
            "",
            f"- **Score**: {dim.get('score', 0)}/5.0",
            f"- **Weight**: {dim.get('weight', 0):.0%}",
            f"- **Checks**: {dim.get('passed', 0)}/{dim.get('total_checks', 0)} passed",
            "",
        ])

    critical_failures = scorecard_json.get("critical_failures", [])
    if critical_failures:
        md_lines.extend([
            "## Critical Failures",
            "",
        ])
        for failure in critical_failures:
            md_lines.append(f"- **{failure.get('check_id', 'unknown')}**: {failure.get('message', 'No message')}")
        md_lines.append("")

    md_lines.extend([
        "## Thresholds",
        "",
        "| Decision | Criteria |",
        "|----------|----------|",
    ])
    for decision, criteria in scorecard_json.get("thresholds", {}).items():
        md_lines.append(f"| {decision} | {criteria} |")

    output_path.write_text("\n".join(md_lines) + "\n")


def load_json(path: Path) -> dict:
    """Load JSON file."""
    return json.loads(path.read_text())


def normalize_analysis(analysis: dict) -> dict:
    """Normalize analysis output to the legacy evaluation shape.

    Handles both:
    - Caldera envelope format: {"metadata": {...}, "data": {...}}
    - Legacy Vulcan format: {"results": {...}}
    """
    # Caldera envelope format (with metadata/data)
    if "data" in analysis and "metadata" in analysis:
        metadata = analysis.get("metadata", {})
        data = analysis.get("data", {})
        normalized = dict(data)
        normalized.setdefault("schema_version", metadata.get("schema_version"))
        normalized.setdefault("repository", metadata.get("repo_name", ""))
        normalized.setdefault("repo_path", metadata.get("repo_path", ""))
        normalized.setdefault("timestamp", metadata.get("timestamp"))
        normalized.setdefault("tool", metadata.get("tool_name"))
        normalized.setdefault("tool_version", metadata.get("tool_version"))
        return normalized
    # Legacy Vulcan format (with results wrapper)
    if "results" in analysis:
        normalized = dict(analysis.get("results", {}))
        normalized.setdefault("schema_version", analysis.get("schema_version"))
        normalized.setdefault("repository", analysis.get("repo_name"))
        normalized.setdefault("repo_path", analysis.get("repo_path"))
        normalized.setdefault("timestamp", analysis.get("generated_at"))
        normalized.setdefault("tool", normalized.get("tool"))
        normalized.setdefault("tool_version", normalized.get("tool_version"))
        return normalized
    # Already normalized or unknown format
    return analysis


def evaluate_repository(
    analysis_path: Path, ground_truth_path: Path
) -> EvaluationReport:
    """Run all checks for a single repository."""
    analysis = normalize_analysis(load_json(analysis_path))
    ground_truth = load_json(ground_truth_path)

    repo_name = analysis.get("repository", analysis_path.stem)
    report = EvaluationReport(repository=repo_name)

    # Run all check categories
    for result in run_accuracy_checks(analysis, ground_truth):
        report.add_result(result)

    for result in run_coverage_checks(analysis, ground_truth):
        report.add_result(result)

    for result in run_detection_checks(analysis, ground_truth):
        report.add_result(result)

    for result in run_performance_checks(analysis, ground_truth):
        report.add_result(result)

    return report


def find_analysis_files(analysis_dir: Path, ground_truth_dir: Path) -> list[tuple[Path, Path]]:
    """Find analysis files that have matching ground truth.

    Returns list of (analysis_path, ground_truth_path) tuples.
    """
    pairs = []

    # Pattern 1: Direct JSON files in analysis_dir (e.g., mit-only.json)
    for analysis_path in analysis_dir.glob("*.json"):
        repo_name = analysis_path.stem
        ground_truth_path = ground_truth_dir / f"{repo_name}.json"
        if ground_truth_path.exists():
            pairs.append((analysis_path, ground_truth_path))

    # Pattern 2: Subdirectories with output.json (e.g., outputs/<run-id>/output.json)
    # Try to match against ground truth by looking at the output content
    for subdir in analysis_dir.iterdir():
        if not subdir.is_dir():
            continue
        output_path = subdir / "output.json"
        if not output_path.exists():
            continue

        # Try to extract repo name from the output
        try:
            with open(output_path) as f:
                data = json.load(f)
            # Check envelope format metadata
            if "metadata" in data:
                repo_path = data.get("metadata", {}).get("repo_path", "")
                repo_name = Path(repo_path).name if repo_path else subdir.name
            else:
                repo_name = data.get("repo_name", subdir.name)

            ground_truth_path = ground_truth_dir / f"{repo_name}.json"
            if ground_truth_path.exists():
                pairs.append((output_path, ground_truth_path))
        except (json.JSONDecodeError, OSError):
            continue

    return pairs


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Evaluate license analysis results")
    parser.add_argument(
        "--analysis-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory containing analysis results",
    )
    parser.add_argument(
        "--ground-truth-dir",
        type=Path,
        default=Path("evaluation/ground-truth"),
        help="Directory containing ground truth files",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("evaluation/results/evaluation_report.json"),
        help="Output file for evaluation report",
    )

    args = parser.parse_args()

    print("License Analysis Evaluation")
    print("=" * 60)
    print()

    all_reports = []
    total_checks = 0
    total_passed = 0

    # Find all analysis files with matching ground truth
    analysis_pairs = find_analysis_files(args.analysis_dir, args.ground_truth_dir)
    if not analysis_pairs:
        print(f"No analysis files found in {args.analysis_dir}")
        print("Results saved to evaluation/results/")
        return

    for analysis_path, ground_truth_path in analysis_pairs:
        repo_name = ground_truth_path.stem

        report = evaluate_repository(analysis_path, ground_truth_path)
        all_reports.append(report)

        total_checks += report.total_checks
        total_passed += report.passed_checks

        # Print report
        status = "PASS" if report.pass_rate == 1.0 else "FAIL"
        print(f"{repo_name}: {report.passed_checks}/{report.total_checks} ({status})")

        # Show failed checks
        failed = [r for r in report.results if not r.passed]
        for result in failed:
            print(f"  FAIL {result.check_id}: {result.message}")

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Repositories evaluated: {len(all_reports)}")
    print(f"Total checks: {total_checks}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_checks - total_passed}")
    pass_rate = total_passed / total_checks if total_checks > 0 else 0
    print(f"Overall pass rate: {pass_rate:.1%}")

    # Generate and save scorecard.json
    scorecard_json = generate_scorecard_json(all_reports, total_checks, total_passed)
    scorecard_path = SCRIPT_DIR.parent / "evaluation" / "scorecard.json"
    scorecard_path.parent.mkdir(parents=True, exist_ok=True)
    with open(scorecard_path, "w") as f:
        json.dump(scorecard_json, f, indent=2)
    print(f"\nScorecard saved to: {scorecard_path}")

    # Generate scorecard.md
    scorecard_md_path = SCRIPT_DIR.parent / "evaluation" / "scorecard.md"
    generate_scorecard_md(scorecard_json, scorecard_md_path)
    print(f"Markdown scorecard saved to: {scorecard_md_path}")

    # Save output with compliance-required fields
    from datetime import datetime, timezone

    # Flatten checks from all reports for compliance
    all_checks = []
    for report in all_reports:
        for result in report.results:
            all_checks.append({
                "check_id": result.check_id,
                "name": getattr(result, "name", result.check_id),
                "passed": result.passed,
                "message": result.message,
                "repository": report.repository,
                "category": getattr(result, "category", "unknown"),
            })

    output_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": "scancode",
        "version": "1.0.0",
        "decision": determine_decision(pass_rate),
        "score": round(pass_rate * 5.0, 2),
        "summary": {
            "passed": total_passed,
            "failed": total_checks - total_passed,
            "total": total_checks,
            "pass_rate": round(pass_rate, 4),
        },
        "checks": all_checks,
        "total_repositories": len(all_reports),
        "reports": [asdict(r) for r in all_reports],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output_data, indent=2))
    print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
