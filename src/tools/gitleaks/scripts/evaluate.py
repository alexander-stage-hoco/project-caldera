#!/usr/bin/env python3
"""Evaluation orchestrator for gitleaks PoC."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from scripts.checks import EvaluationReport
from scripts.checks.accuracy import run_accuracy_checks
from scripts.checks.coverage import run_coverage_checks
from scripts.checks.detection import run_detection_checks
from scripts.checks.performance import run_performance_checks
from scripts.checks.output_quality import run_output_quality_checks
from scripts.checks.integration_fit import run_integration_fit_checks
from scripts.checks.edge_cases import run_edge_case_checks
from scripts.checks.rollup import run_rollup_checks


def normalize_analysis(analysis: dict) -> dict:
    """Normalize analysis output to the evaluation shape."""
    # Handle envelope format with 'data' key
    if "data" in analysis:
        normalized = dict(analysis["data"])
        metadata = analysis.get("metadata", {})
        normalized.setdefault("schema_version", metadata.get("schema_version"))
        normalized.setdefault("timestamp", metadata.get("timestamp"))
        normalized.setdefault("repository", metadata.get("repo_id"))
        normalized.setdefault("repo_path", metadata.get("repo_id"))
        normalized["_root"] = analysis
        return normalized
    # Handle legacy format with 'results' key
    if "results" in analysis:
        normalized = dict(analysis["results"])
        normalized.setdefault("schema_version", analysis.get("schema_version"))
        normalized.setdefault("timestamp", analysis.get("generated_at"))
        normalized.setdefault("repository", analysis.get("repo_name"))
        normalized.setdefault("repo_path", analysis.get("repo_path"))
        normalized["_root"] = analysis
        return normalized
    return analysis


def evaluate_repository(
    analysis_path: Path,
    ground_truth_path: Path,
) -> EvaluationReport:
    """Evaluate a single repository against ground truth."""
    analysis_raw = json.loads(analysis_path.read_text())
    analysis = normalize_analysis(analysis_raw)
    ground_truth = json.loads(ground_truth_path.read_text())

    report = EvaluationReport(repository=analysis.get("repository", "unknown"))

    # Run all check categories
    for result in run_accuracy_checks(analysis, ground_truth):
        report.add_result(result)

    for result in run_coverage_checks(analysis, ground_truth):
        report.add_result(result)

    for result in run_detection_checks(analysis, ground_truth):
        report.add_result(result)

    for result in run_performance_checks(analysis, ground_truth):
        report.add_result(result)

    for result in run_output_quality_checks(analysis):
        report.add_result(result)

    for result in run_integration_fit_checks(analysis):
        report.add_result(result)

    for result in run_edge_case_checks(analysis, ground_truth):
        report.add_result(result)

    for result in run_rollup_checks(analysis, ground_truth):
        report.add_result(result)

    return report


def determine_decision(score: float) -> str:
    """Determine pass/fail decision based on pass rate (0-1)."""
    normalized = score * 5.0
    if normalized >= 4.0:
        return "STRONG_PASS"
    elif normalized >= 3.5:
        return "PASS"
    elif normalized >= 3.0:
        return "WEAK_PASS"
    return "FAIL"


def generate_scorecard_json(reports: list[EvaluationReport]) -> dict:
    """Generate structured scorecard JSON data from evaluation reports."""
    from datetime import datetime, timezone

    # Aggregate results across all repositories
    dimension_aggregates: dict[str, dict] = {}

    for report in reports:
        for result in report.results:
            category = result.category
            if category not in dimension_aggregates:
                dimension_aggregates[category] = {
                    "passed": 0,
                    "total": 0,
                    "checks": [],
                }
            dimension_aggregates[category]["total"] += 1
            if result.passed:
                dimension_aggregates[category]["passed"] += 1
            dimension_aggregates[category]["checks"].append({
                "check_id": result.check_id,
                "name": result.message[:50],
                "passed": result.passed,
                "message": result.message,
            })

    # Calculate overall score
    total_passed = sum(d["passed"] for d in dimension_aggregates.values())
    total_checks = sum(d["total"] for d in dimension_aggregates.values())
    overall_score = total_passed / total_checks if total_checks > 0 else 0
    normalized_score = overall_score * 5.0

    # Build dimensions data
    dimensions_data = []
    for i, (category, data) in enumerate(dimension_aggregates.items()):
        dim_score = (data["passed"] / data["total"] * 5.0) if data["total"] > 0 else 0
        dimensions_data.append({
            "id": f"D{i+1}",
            "name": category.replace("_", " ").title(),
            "weight": 1.0 / len(dimension_aggregates) if dimension_aggregates else 1.0,
            "total_checks": data["total"],
            "passed": data["passed"],
            "failed": data["total"] - data["passed"],
            "score": round(dim_score, 2),
            "weighted_score": round(dim_score / len(dimension_aggregates), 2) if dimension_aggregates else 0,
            "checks": data["checks"],
        })

    return {
        "tool": "gitleaks",
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "description": "Evaluation scorecard for gitleaks secret detection",
        "summary": {
            "total_checks": total_checks,
            "passed": total_passed,
            "failed": total_checks - total_passed,
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
            for data in dimension_aggregates.values()
            for c in data["checks"]
            if not c["passed"] and "critical" in c["check_id"].lower()
        ],
        "thresholds": {
            "STRONG_PASS": ">= 4.0 (80%+)",
            "PASS": ">= 3.5 (70%+)",
            "WEAK_PASS": ">= 3.0 (60%+)",
            "FAIL": "< 3.0 (below 60%)",
        },
        "metadata": {
            "repositories_evaluated": len(reports),
        },
    }


def print_report(report: EvaluationReport) -> None:
    """Print evaluation report to console."""
    print(f"\n{'='*60}")
    print(f"Repository: {report.repository}")
    print(f"{'='*60}")

    # Group results by category
    by_category: dict[str, list] = {}
    for result in report.results:
        if result.category not in by_category:
            by_category[result.category] = []
        by_category[result.category].append(result)

    for category, results in sorted(by_category.items()):
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        print(f"\n{category} ({passed}/{total})")
        print("-" * 40)

        for result in results:
            status = "PASS" if result.passed else "FAIL"
            print(f"  [{status}] {result.check_id}: {result.message}")

    print(f"\n{'='*60}")
    print(f"Total: {report.passed_checks}/{report.total_checks} ({report.pass_rate:.1%})")
    print(f"{'='*60}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Evaluate gitleaks analysis results")
    parser.add_argument(
        "--analysis-dir",
        type=Path,
        default=Path("output/runs"),
        help="Directory containing analysis JSON files",
    )
    parser.add_argument(
        "--ground-truth-dir",
        type=Path,
        default=Path("evaluation/ground-truth"),
        help="Directory containing ground truth JSON files",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("evaluation/results"),
        help="Output directory for evaluation reports",
    )

    args = parser.parse_args()

    print("Gitleaks PoC Evaluation")
    print("=" * 60)

    # Find all analysis files
    analysis_files = sorted(args.analysis_dir.glob("*.json"))
    if not analysis_files:
        print(f"No analysis files found in {args.analysis_dir}")
        return

    # Run evaluation for each repo
    all_reports: list[EvaluationReport] = []
    total_checks = 0
    total_passed = 0

    for analysis_path in analysis_files:
        repo_name = analysis_path.stem
        ground_truth_path = args.ground_truth_dir / f"{repo_name}.json"

        if not ground_truth_path.exists():
            print(f"Warning: No ground truth for {repo_name}, skipping")
            continue

        report = evaluate_repository(analysis_path, ground_truth_path)
        all_reports.append(report)

        print_report(report)

        total_checks += report.total_checks
        total_passed += report.passed_checks

        # Save individual report
        args.output.mkdir(parents=True, exist_ok=True)
        report_path = args.output / f"{repo_name}_eval.json"
        report_path.write_text(json.dumps(asdict(report), indent=2))

    # Print summary
    if all_reports:
        print("\n")
        print("=" * 60)
        print("OVERALL SUMMARY")
        print("=" * 60)
        print(f"Repositories evaluated: {len(all_reports)}")
        print(f"Total checks: {total_checks}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_checks - total_passed}")
        print(f"Pass rate: {total_passed/total_checks:.1%}" if total_checks > 0 else "N/A")
        print("=" * 60)

        # Generate and save scorecard.json
        scorecard_json = generate_scorecard_json(all_reports)
        scorecard_path = Path(__file__).parent.parent / "evaluation" / "scorecard.json"
        scorecard_path.parent.mkdir(parents=True, exist_ok=True)
        with open(scorecard_path, "w") as f:
            json.dump(scorecard_json, f, indent=2)
        print(f"\nScorecard saved to: {scorecard_path}")

        # List any failing repos
        failing_repos = [r for r in all_reports if r.pass_rate < 1.0]
        if failing_repos:
            print("\nRepositories with failures:")
            for r in failing_repos:
                print(f"  - {r.repository}: {r.pass_rate:.1%}")
        else:
            print("\nAll repositories passed 100%!")


if __name__ == "__main__":
    main()
