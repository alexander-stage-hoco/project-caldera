#!/usr/bin/env python3
"""Main evaluation script for Lizard function analysis.

This script runs all programmatic checks against analysis results and
ground truth data, producing a comprehensive evaluation report.

Usage:
    python scripts/evaluate.py --analysis evaluation/results/output.json
    python scripts/evaluate.py --analysis evaluation/results/output.json --ground-truth evaluation/ground-truth
    python scripts/evaluate.py --analysis evaluation/results/output.json --output evaluation/results/evaluation_report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.checks import (
    CheckCategory,
    CheckResult,
    CheckSeverity,
    EvaluationReport,
)
from scripts.checks.accuracy import run_accuracy_checks
from scripts.checks.coverage import run_coverage_checks
from scripts.checks.edge_cases import run_edge_case_checks
from scripts.checks.exclusion import run_exclusion_checks
from scripts.checks.performance import run_performance_checks


def load_json(path: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with open(path) as f:
        return json.load(f)


def load_ground_truth_for_language(
    ground_truth_dir: Path, language: str
) -> Dict[str, Any] | None:
    """Load ground truth for a specific language."""
    gt_path = ground_truth_dir / f"{language}.json"
    if gt_path.exists():
        return load_json(gt_path)
    return None


def load_all_ground_truth(ground_truth_dir: Path) -> Dict[str, Dict[str, Any]]:
    """Load ground truth for all languages.

    Returns dict mapping language name to ground truth data.
    """
    ground_truth = {}
    for gt_file in ground_truth_dir.glob("*.json"):
        language = gt_file.stem
        ground_truth[language] = load_json(gt_file)
    return ground_truth


def merge_ground_truth(ground_truth_by_lang: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Merge ground truth from multiple languages into unified format.

    This allows accuracy checks to work across all languages at once.
    """
    merged = {
        "languages": list(ground_truth_by_lang.keys()),
        "files": {},
        "total_functions": 0,
        "total_ccn": 0,
    }

    for lang, gt_data in ground_truth_by_lang.items():
        for filename, file_data in gt_data.get("files", {}).items():
            # Prefix with language for uniqueness
            full_path = f"{lang}/{filename}"
            merged["files"][full_path] = file_data
            merged["total_functions"] += file_data.get("expected_functions", 0)
            merged["total_ccn"] += file_data.get("total_ccn", 0)

    return merged


def _normalize_analysis(raw_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize analysis JSON to expected format for checks.

    The function_analyzer outputs data under 'results' key, but checks
    expect data at the top level. This function extracts and normalizes.
    """
    # Envelope schema: extract data payload
    if "data" in raw_analysis and isinstance(raw_analysis.get("data"), dict):
        return raw_analysis["data"]

    # If data is already in the expected format (has 'files' at top level)
    if "files" in raw_analysis and isinstance(raw_analysis.get("files"), list):
        return raw_analysis

    # Extract from 'results' if present (new analyzer format)
    if "results" in raw_analysis:
        results = raw_analysis["results"]
        return {
            "files": results.get("files", []),
            "summary": results.get("summary", {}),
            "by_language": results.get("by_language", {}),
            "directories": results.get("directories", []),
            "run_id": results.get("run_id"),
            "timestamp": results.get("timestamp"),
            "root_path": results.get("root_path"),
            "lizard_version": results.get("lizard_version"),
            # Keep original metadata
            "schema_version": raw_analysis.get("schema_version"),
            "repo_name": raw_analysis.get("repo_name"),
            "repo_path": raw_analysis.get("repo_path"),
        }

    # Return as-is if unknown format
    return raw_analysis


def run_evaluation(
    analysis_path: Path,
    ground_truth_dir: Path,
    eval_repos_path: Path | None = None,
) -> EvaluationReport:
    """Run all evaluation checks and return report.

    Args:
        analysis_path: Path to output.json
        ground_truth_dir: Path to ground-truth directory
        eval_repos_path: Optional path to eval-repos for performance checks

    Returns:
        EvaluationReport with all check results
    """
    # Load and normalize analysis
    raw_analysis = load_json(analysis_path)
    analysis = _normalize_analysis(raw_analysis)

    # Load and merge ground truth
    ground_truth_by_lang = load_all_ground_truth(ground_truth_dir)
    merged_ground_truth = merge_ground_truth(ground_truth_by_lang)

    # Run all checks
    all_checks: List[CheckResult] = []

    # Accuracy checks (per-language)
    for lang, gt_data in ground_truth_by_lang.items():
        checks = run_accuracy_checks(analysis, gt_data)
        # Tag checks with language in evidence
        for check in checks:
            check.evidence["language"] = lang
        all_checks.extend(checks)

    # Coverage checks
    all_checks.extend(run_coverage_checks(analysis))

    # Exclusion checks
    all_checks.extend(run_exclusion_checks(analysis, merged_ground_truth))

    # Edge case checks (merged ground truth)
    all_checks.extend(run_edge_case_checks(analysis, merged_ground_truth))

    # Performance checks
    all_checks.extend(run_performance_checks(analysis, eval_repos_path))

    # Create report
    return EvaluationReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        analysis_path=str(analysis_path),
        ground_truth_path=str(ground_truth_dir),
        checks=all_checks,
    )


def print_report(report: EvaluationReport, verbose: bool = False) -> None:
    """Print evaluation report to console."""
    print("\n" + "=" * 80)
    print("  LIZARD EVALUATION REPORT")
    print("=" * 80)
    print(f"\n  Timestamp: {report.timestamp}")
    print(f"  Analysis:  {report.analysis_path}")
    print(f"  Ground Truth: {report.ground_truth_path}")

    # Summary
    print("\n" + "-" * 80)
    print("  SUMMARY")
    print("-" * 80)
    print(f"\n  Total Checks:  {report.total_checks}")
    print(f"  Passed:        {report.passed_checks} ({100 * report.passed_checks / report.total_checks:.1f}%)")
    print(f"  Failed:        {report.failed_checks}")
    print(f"  Overall Score: {report.overall_score:.3f}")

    # Critical failures
    if report.critical_failures:
        print("\n" + "-" * 80)
        print("  CRITICAL FAILURES")
        print("-" * 80)
        for check in report.critical_failures:
            print(f"\n  [{check.check_id}] {check.name}")
            print(f"     Message: {check.message}")

    # Results by category
    for category in CheckCategory:
        category_checks = report.by_category(category)
        if not category_checks:
            continue

        print("\n" + "-" * 80)
        print(f"  {category.value.upper()} CHECKS")
        print("-" * 80)

        for check in category_checks:
            status = "PASS" if check.passed else "FAIL"
            severity_icon = {
                CheckSeverity.CRITICAL: "",
                CheckSeverity.HIGH: "",
                CheckSeverity.MEDIUM: "",
                CheckSeverity.LOW: "",
            }.get(check.severity, "")

            print(f"\n  [{check.check_id}] {check.name}")
            print(f"     Status:   {status} {severity_icon}")
            print(f"     Score:    {check.score:.3f}")
            print(f"     Severity: {check.severity.value}")
            print(f"     Message:  {check.message}")

            if verbose and check.evidence:
                print(f"     Evidence: {json.dumps(check.evidence, indent=2)[:500]}...")

    print("\n" + "=" * 80)
    print("  END OF REPORT")
    print("=" * 80 + "\n")


def generate_scorecard_json(report: EvaluationReport) -> Dict[str, Any]:
    """Generate structured scorecard JSON data.

    Returns comprehensive scorecard with dimensions, scores, and details.
    """
    # Calculate scores by category/dimension
    dimensions = []
    for category in CheckCategory:
        category_checks = report.by_category(category)
        if not category_checks:
            continue

        # Calculate category score
        category_score = sum(c.score for c in category_checks) / len(category_checks)
        passed = sum(1 for c in category_checks if c.passed)

        # Get severity breakdown
        by_severity = {}
        for severity in CheckSeverity:
            sev_checks = [c for c in category_checks if c.severity == severity]
            if sev_checks:
                by_severity[severity.value] = {
                    "count": len(sev_checks),
                    "passed": sum(1 for c in sev_checks if c.passed),
                    "score": sum(c.score for c in sev_checks) / len(sev_checks),
                }

        dimensions.append({
            "id": f"D{len(dimensions) + 1}",
            "name": category.value.replace("_", " ").title(),
            "category": category.value,
            "total_checks": len(category_checks),
            "passed": passed,
            "failed": len(category_checks) - passed,
            "score": round(category_score, 3),
            "by_severity": by_severity,
            "check_ids": [c.check_id for c in category_checks],
        })

    # Determine decision based on score
    normalized_score = 1 + (report.overall_score * 4)  # 0-1 -> 1-5
    if normalized_score >= 4.0:
        decision = "STRONG_PASS"
    elif normalized_score >= 3.5:
        decision = "PASS"
    elif normalized_score >= 3.0:
        decision = "WEAK_PASS"
    else:
        decision = "FAIL"

    return {
        "tool": "lizard",
        "version": "1.0.0",
        "generated_at": report.timestamp,
        "description": "Evaluation scorecard for Lizard function-level complexity analysis",
        "summary": {
            "total_checks": report.total_checks,
            "passed": report.passed_checks,
            "failed": report.failed_checks,
            "score": round(report.overall_score, 3),
            "score_percent": round(report.overall_score * 100, 1),
            "normalized_score": round(normalized_score, 2),
            "decision": decision,
        },
        "dimensions": dimensions,
        "critical_failures": [
            {
                "check_id": c.check_id,
                "name": c.name,
                "message": c.message,
            }
            for c in report.critical_failures
        ],
        "thresholds": {
            "STRONG_PASS": ">= 4.0 normalized (>= 75% raw)",
            "PASS": ">= 3.5 normalized (>= 62.5% raw)",
            "WEAK_PASS": ">= 3.0 normalized (>= 50% raw)",
            "FAIL": "< 3.0 normalized (< 50% raw)",
        },
        "metadata": {
            "tool_type": "complexity_analysis",
            "primary_purpose": "function_level_ccn_analysis",
            "languages_covered": 7,
            "ground_truth_functions": 524,
            "analysis_path": report.analysis_path,
            "ground_truth_path": report.ground_truth_path,
        },
    }


def generate_scorecard_md(report: EvaluationReport, scorecard: Dict[str, Any]) -> str:
    """Generate markdown scorecard report.

    Args:
        report: EvaluationReport with check results
        scorecard: Scorecard JSON data

    Returns:
        Formatted markdown string
    """
    lines = []

    # Header
    lines.append("# Lizard Evaluation Scorecard")
    lines.append("")
    lines.append(f"**Generated:** {scorecard['generated_at']}")
    lines.append(f"**Decision:** {scorecard['summary']['decision']}")
    lines.append(f"**Score:** {scorecard['summary']['score_percent']}%")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Checks | {scorecard['summary']['total_checks']} |")
    lines.append(f"| Passed | {scorecard['summary']['passed']} |")
    lines.append(f"| Failed | {scorecard['summary']['failed']} |")
    lines.append(f"| Raw Score | {scorecard['summary']['score']:.3f} |")
    lines.append(f"| Normalized Score | {scorecard['summary']['normalized_score']:.2f}/5.0 |")
    lines.append("")

    # Dimensions table
    lines.append("## Dimensions")
    lines.append("")
    lines.append("| Dimension | Checks | Passed | Score |")
    lines.append("|-----------|--------|--------|-------|")
    for dim in scorecard["dimensions"]:
        lines.append(
            f"| {dim['name']} | {dim['total_checks']} | {dim['passed']}/{dim['total_checks']} | {dim['score']*100:.1f}% |"
        )
    lines.append("")

    # Critical failures
    if scorecard["critical_failures"]:
        lines.append("## Critical Failures")
        lines.append("")
        for failure in scorecard["critical_failures"]:
            lines.append(f"- **{failure['check_id']}** - {failure['name']}: {failure['message']}")
        lines.append("")

    # Detailed results by category
    lines.append("## Detailed Results")
    lines.append("")

    for category in CheckCategory:
        category_checks = report.by_category(category)
        if not category_checks:
            continue

        lines.append(f"### {category.value.replace('_', ' ').title()}")
        lines.append("")
        lines.append("| Check | Status | Score | Severity | Message |")
        lines.append("|-------|--------|-------|----------|---------|")

        for check in category_checks:
            status = "PASS" if check.passed else "FAIL"
            msg = check.message[:50] + "..." if len(check.message) > 50 else check.message
            lines.append(
                f"| {check.check_id} | {status} | {check.score:.2f} | {check.severity.value} | {msg} |"
            )
        lines.append("")

    # Decision thresholds
    lines.append("## Decision Thresholds")
    lines.append("")
    lines.append("| Decision | Criteria |")
    lines.append("|----------|----------|")
    for decision, criteria in scorecard["thresholds"].items():
        lines.append(f"| {decision} | {criteria} |")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append(f"*Analysis: `{scorecard['metadata']['analysis_path']}`*")
    lines.append(f"*Ground Truth: `{scorecard['metadata']['ground_truth_path']}`*")

    return "\n".join(lines)


def save_scorecards(
    report: EvaluationReport,
    output_dir: Path,
) -> None:
    """Save scorecard files (JSON and Markdown).

    Args:
        report: EvaluationReport with check results
        output_dir: Directory to save scorecards
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate scorecard data
    scorecard = generate_scorecard_json(report)

    # Save JSON
    json_path = output_dir / "scorecard.json"
    with open(json_path, "w") as f:
        json.dump(scorecard, f, indent=2)
    print(f"Scorecard JSON saved to: {json_path}")

    # Save Markdown
    md_path = output_dir / "scorecard.md"
    md_content = generate_scorecard_md(report, scorecard)
    with open(md_path, "w") as f:
        f.write(md_content)
    print(f"Scorecard Markdown saved to: {md_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate Lizard function analysis against ground truth"
    )
    parser.add_argument(
        "--analysis",
        type=Path,
        required=True,
        help="Path to output.json file",
    )
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=Path(__file__).parent.parent / "evaluation" / "ground-truth",
        help="Path to ground-truth directory",
    )
    parser.add_argument(
        "--eval-repos",
        type=Path,
        default=None,
        help="Path to eval-repos directory (for performance checks)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to write JSON report (optional)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed evidence for each check",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON only (no console report)",
    )
    parser.add_argument(
        "--scorecard",
        type=Path,
        default=None,
        help="Directory to write scorecard files (scorecard.json and scorecard.md)",
    )

    args = parser.parse_args()

    # Validate paths
    if not args.analysis.exists():
        print(f"Error: Analysis file not found: {args.analysis}", file=sys.stderr)
        sys.exit(1)

    if not args.ground_truth.exists():
        print(f"Error: Ground truth directory not found: {args.ground_truth}", file=sys.stderr)
        sys.exit(1)

    # Run evaluation
    report = run_evaluation(
        analysis_path=args.analysis,
        ground_truth_dir=args.ground_truth,
        eval_repos_path=args.eval_repos,
    )

    # Output
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print_report(report, verbose=args.verbose)

    # Save JSON if requested
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"\nReport saved to: {args.output}")

    # Save scorecards if requested
    if args.scorecard:
        save_scorecards(report, args.scorecard)

    # Exit with appropriate code
    if report.critical_failures:
        sys.exit(2)  # Critical failures
    elif report.failed_checks > 0:
        sys.exit(1)  # Some failures
    else:
        sys.exit(0)  # All passed


if __name__ == "__main__":
    main()
