#!/usr/bin/env python3
"""Run programmatic evaluation for git-fame.

Evaluates git-fame output across multiple dimensions:
- Output Quality (20%)
- Authorship Accuracy (20%)
- Reliability (15%)
- Performance (15%)
- Integration Fit (15%)
- Installation (15%)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from checks import (
    OutputQualityChecks,
    AuthorshipAccuracyChecks,
    ReliabilityChecks,
    PerformanceChecks,
    IntegrationFitChecks,
    InstallationChecks,
)


def calculate_dimension_score(results: list[dict[str, Any]]) -> float:
    """Calculate score for a dimension (0-5 scale)."""
    if not results:
        return 0.0
    passed = sum(1 for r in results if r.get("passed", False))
    return round(passed / len(results) * 5.0, 2)


def classify_score(score: float) -> str:
    """Classify score into pass/fail category."""
    if score >= 4.5:
        return "STRONG_PASS"
    elif score >= 4.0:
        return "PASS"
    elif score >= 3.5:
        return "MARGINAL_PASS"
    elif score >= 3.0:
        return "MARGINAL_FAIL"
    else:
        return "FAIL"


def find_output_dir(base_dir: Path) -> Path:
    """Find the most recent output directory.

    Follows Caldera convention of outputs/<RUN_ID>/ structure.
    Falls back to legacy output/ directory.
    """
    outputs_dir = base_dir / "outputs"
    if outputs_dir.exists():
        # Find the most recent run directory (by modification time)
        run_dirs = [d for d in outputs_dir.iterdir() if d.is_dir()]
        if run_dirs:
            latest = max(run_dirs, key=lambda d: d.stat().st_mtime)
            return latest

    # Fall back to legacy output directory
    return base_dir / "output"


def run_evaluation(base_dir: Path) -> dict[str, Any]:
    """Run complete evaluation and return results."""
    output_dir = find_output_dir(base_dir)
    eval_repos_dir = base_dir / "eval-repos"
    ground_truth_file = base_dir / "evaluation" / "ground-truth" / "synthetic.json"

    print(f"Using output directory: {output_dir}")

    # Run all check categories
    print("Running evaluation checks...")
    print()

    # 1. Output Quality (20%)
    print("1. Output Quality checks...")
    oq_checker = OutputQualityChecks(output_dir)
    oq_results = oq_checker.run_all()
    oq_score = calculate_dimension_score(oq_results)
    print(f"   Score: {oq_score}/5.0 ({sum(1 for r in oq_results if r['passed'])}/{len(oq_results)} passed)")

    # 2. Authorship Accuracy (20%)
    print("2. Authorship Accuracy checks...")
    aa_checker = AuthorshipAccuracyChecks(output_dir, ground_truth_file)
    aa_results = aa_checker.run_all()
    aa_score = calculate_dimension_score(aa_results)
    print(f"   Score: {aa_score}/5.0 ({sum(1 for r in aa_results if r['passed'])}/{len(aa_results)} passed)")

    # 3. Reliability (15%)
    print("3. Reliability checks...")
    rel_checker = ReliabilityChecks(output_dir, eval_repos_dir)
    rel_results = rel_checker.run_all()
    rel_score = calculate_dimension_score(rel_results)
    print(f"   Score: {rel_score}/5.0 ({sum(1 for r in rel_results if r['passed'])}/{len(rel_results)} passed)")

    # 4. Performance (15%)
    print("4. Performance checks...")
    perf_checker = PerformanceChecks(output_dir, eval_repos_dir)
    perf_results = perf_checker.run_all()
    perf_score = calculate_dimension_score(perf_results)
    print(f"   Score: {perf_score}/5.0 ({sum(1 for r in perf_results if r['passed'])}/{len(perf_results)} passed)")

    # 5. Integration Fit (15%)
    print("5. Integration Fit checks...")
    int_checker = IntegrationFitChecks(output_dir)
    int_results = int_checker.run_all()
    int_score = calculate_dimension_score(int_results)
    print(f"   Score: {int_score}/5.0 ({sum(1 for r in int_results if r['passed'])}/{len(int_results)} passed)")

    # 6. Installation (15%)
    print("6. Installation checks...")
    inst_checker = InstallationChecks()
    inst_results = inst_checker.run_all()
    inst_score = calculate_dimension_score(inst_results)
    print(f"   Score: {inst_score}/5.0 ({sum(1 for r in inst_results if r['passed'])}/{len(inst_results)} passed)")

    print()

    # Calculate weighted overall score
    weights = {
        "output_quality": 0.20,
        "authorship_accuracy": 0.20,
        "reliability": 0.15,
        "performance": 0.15,
        "integration_fit": 0.15,
        "installation": 0.15,
    }

    weighted_score = (
        oq_score * weights["output_quality"]
        + aa_score * weights["authorship_accuracy"]
        + rel_score * weights["reliability"]
        + perf_score * weights["performance"]
        + int_score * weights["integration_fit"]
        + inst_score * weights["installation"]
    )
    weighted_score = round(weighted_score, 2)

    classification = classify_score(weighted_score)

    # Calculate totals for summary
    all_checks = oq_results + aa_results + rel_results + perf_results + int_results + inst_results
    total_checks = len(all_checks)
    passed_checks = sum(1 for c in all_checks if c.get("passed", False))

    # Compile results
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": "git-fame",
        "version": "3.1.1",
        "overall_score": weighted_score,
        "classification": classification,
        "summary": {
            "total_checks": total_checks,
            "passed": passed_checks,
            "failed": total_checks - passed_checks,
            "score": round(weighted_score / 5.0, 4),
            "score_percent": round(weighted_score / 5.0 * 100, 2),
            "decision": classification,
        },
        "dimensions": {
            "output_quality": {
                "weight": weights["output_quality"],
                "score": oq_score,
                "checks": oq_results,
            },
            "authorship_accuracy": {
                "weight": weights["authorship_accuracy"],
                "score": aa_score,
                "checks": aa_results,
            },
            "reliability": {
                "weight": weights["reliability"],
                "score": rel_score,
                "checks": rel_results,
            },
            "performance": {
                "weight": weights["performance"],
                "score": perf_score,
                "checks": perf_results,
            },
            "integration_fit": {
                "weight": weights["integration_fit"],
                "score": int_score,
                "checks": int_results,
            },
            "installation": {
                "weight": weights["installation"],
                "score": inst_score,
                "checks": inst_results,
            },
        },
    }

    return results


def determine_decision(score: float) -> str:
    """Determine pass/fail decision based on normalized score (0-5)."""
    if score >= 4.0:
        return "STRONG_PASS"
    elif score >= 3.5:
        return "PASS"
    elif score >= 3.0:
        return "WEAK_PASS"
    return "FAIL"


def generate_scorecard_json(results: dict[str, Any]) -> dict:
    """Generate structured scorecard JSON data."""
    dimensions_data = []
    for i, (dim_name, dim_data) in enumerate(results["dimensions"].items()):
        passed = sum(1 for c in dim_data["checks"] if c.get("passed", False))
        dimensions_data.append({
            "id": f"D{i+1}",
            "name": dim_name.replace("_", " ").title(),
            "weight": dim_data["weight"],
            "total_checks": len(dim_data["checks"]),
            "passed": passed,
            "failed": len(dim_data["checks"]) - passed,
            "score": dim_data["score"],
            "weighted_score": round(dim_data["score"] * dim_data["weight"], 2),
            "checks": [
                {
                    "check_id": c.get("check", f"C{j+1}"),
                    "name": c.get("check", ""),
                    "passed": c.get("passed", False),
                    "message": c.get("message", ""),
                }
                for j, c in enumerate(dim_data["checks"])
            ],
        })

    total_checks = sum(len(d["checks"]) for d in results["dimensions"].values())
    passed_checks = sum(
        sum(1 for c in d["checks"] if c.get("passed")) for d in results["dimensions"].values()
    )

    return {
        "tool": results["tool"],
        "version": results.get("version", "1.0.0"),
        "generated_at": results["timestamp"],
        "description": f"Evaluation scorecard for {results['tool']} git analytics",
        "summary": {
            "total_checks": total_checks,
            "passed": passed_checks,
            "failed": total_checks - passed_checks,
            "score": round(results["overall_score"] / 5.0, 4),
            "score_percent": round(results["overall_score"] / 5.0 * 100, 2),
            "normalized_score": round(results["overall_score"], 2),
            "decision": determine_decision(results["overall_score"]),
        },
        "dimensions": dimensions_data,
        "critical_failures": [],
        "thresholds": {
            "STRONG_PASS": ">= 4.0 (80%+)",
            "PASS": ">= 3.5 (70%+)",
            "WEAK_PASS": ">= 3.0 (60%+)",
            "FAIL": "< 3.0 (below 60%)",
        },
    }


def generate_scorecard(results: dict[str, Any], output_path: Path) -> None:
    """Generate markdown scorecard."""
    lines = [
        "# git-fame Evaluation Scorecard",
        "",
        f"**Generated**: {results['timestamp']}",
        f"**Tool**: {results['tool']} v{results['version']}",
        "",
        "## Overall Score",
        "",
        f"**Score**: {results['overall_score']}/5.0",
        f"**Classification**: {results['classification']}",
        "",
        "## Dimension Scores",
        "",
        "| Dimension | Weight | Score | Status |",
        "|-----------|--------|-------|--------|",
    ]

    for dim_name, dim_data in results["dimensions"].items():
        weight_pct = int(dim_data["weight"] * 100)
        score = dim_data["score"]
        status = "PASS" if score >= 4.0 else ("MARGINAL" if score >= 3.0 else "FAIL")
        lines.append(f"| {dim_name.replace('_', ' ').title()} | {weight_pct}% | {score}/5.0 | {status} |")

    lines.extend(["", "## Detailed Results", ""])

    for dim_name, dim_data in results["dimensions"].items():
        lines.append(f"### {dim_name.replace('_', ' ').title()}")
        lines.append("")
        lines.append("| Check | Status | Message |")
        lines.append("|-------|--------|---------|")

        for check in dim_data["checks"]:
            status = "PASS" if check["passed"] else "FAIL"
            message = check["message"][:60] + "..." if len(check["message"]) > 60 else check["message"]
            lines.append(f"| {check['check']} | {status} | {message} |")

        lines.append("")

    output_path.write_text("\n".join(lines))


def main():
    """Main entry point."""
    base_dir = Path(__file__).parent.parent

    print("=" * 60)
    print("git-fame Programmatic Evaluation")
    print("=" * 60)
    print()

    results = run_evaluation(base_dir)

    # Save JSON results
    results_dir = base_dir / "evaluation" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    json_file = results_dir / "evaluation_report.json"
    json_file.write_text(json.dumps(results, indent=2))
    print(f"JSON results: {json_file}")

    # Generate markdown scorecard
    scorecard_file = base_dir / "evaluation" / "scorecard.md"
    generate_scorecard(results, scorecard_file)
    print(f"Scorecard: {scorecard_file}")

    # Generate JSON scorecard
    scorecard_json = generate_scorecard_json(results)
    scorecard_json_file = base_dir / "evaluation" / "scorecard.json"
    with open(scorecard_json_file, "w") as f:
        json.dump(scorecard_json, f, indent=2)
    print(f"Scorecard JSON: {scorecard_json_file}")

    print()
    print("=" * 60)
    print(f"OVERALL: {results['overall_score']}/5.0 - {results['classification']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
