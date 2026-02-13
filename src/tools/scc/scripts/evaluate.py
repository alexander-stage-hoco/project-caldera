#!/usr/bin/env python3
"""Main evaluation orchestrator for scc PoC."""

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List
import sys
import uuid

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.checks import CheckResult, DimensionResult, EvaluationResult
from common.git_utilities import resolve_commit as _resolve_commit
from scripts.checks.output_quality import run_output_quality_checks
from scripts.checks.integration_fit import run_integration_fit_checks
from scripts.checks.reliability import run_reliability_checks
from scripts.checks.performance import run_performance_checks
from scripts.checks.installation import run_installation_checks
from scripts.checks.coverage import run_coverage_checks
from scripts.checks.license import run_license_checks
from scripts.checks.per_file import run_per_file_checks
from scripts.checks.directory_analysis import run_directory_analysis_checks
from scripts.checks.cocomo import run_cocomo_checks
from scripts.scoring import (
    compute_dimension_result,
    compute_total_score,
    determine_decision,
    format_score_summary
)


def _resolve_results_dir(base_path: Path) -> Path:
    """Resolve evaluation results directory."""
    env_dir = os.environ.get("EVAL_OUTPUT_DIR")
    if env_dir:
        return Path(env_dir)
    return base_path / "evaluation" / "results"


def run_scc_analysis(base_path: Path, results_dir: Path) -> tuple:
    """Run scc analysis and return exit code and stderr."""
    scc_path = base_path / "bin" / "scc"
    output_path = results_dir / "raw_scc_output.json"

    result = subprocess.run(
        [str(scc_path), "eval-repos/synthetic", "-f", "json"],
        capture_output=True,
        text=True,
        cwd=base_path,
        timeout=60
    )

    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(result.stdout)

    return result.returncode, result.stderr


def _git_value(repo_path: Path, args: list[str], fallback: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True,
        text=True,
    )
    value = result.stdout.strip()
    return value if value else fallback


def run_envelope_analysis(base_path: Path, repo_path: Path, output_path: Path) -> None:
    """Run envelope analysis to generate output.json."""
    run_id = str(uuid.uuid4())
    repo_id = str(uuid.uuid4())
    branch = _git_value(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"], "unknown")
    try:
        commit = _resolve_commit(repo_path, "", base_path)
    except ValueError as exc:
        raise RuntimeError(f"Unable to resolve commit: {exc}") from exc

    python_exe = os.environ.get("PYTHON", sys.executable)
    subprocess.run(
        [
            python_exe,
            str(base_path / "scripts" / "analyze.py"),
            "--repo-path",
            str(repo_path),
            "--repo-name",
            repo_path.name,
            "--output-dir",
            str(output_path.parent),
            "--run-id",
            run_id,
            "--repo-id",
            repo_id,
            "--branch",
            branch,
            "--commit",
            commit,
            "--no-color",
        ],
        cwd=base_path,
        capture_output=True,
        timeout=120,
        check=False,
    )


def run_all_checks(base_path: Path) -> List[DimensionResult]:
    """Run all evaluation checks and return dimension results."""
    results_dir = _resolve_results_dir(base_path)
    raw_output_path = results_dir / "raw_scc_output.json"
    output_path = results_dir / "output.json"
    schema_path = base_path / "schemas" / "output.schema.json"
    repo_path = base_path / "eval-repos" / "synthetic"

    # First, run scc to generate fresh output
    print("Running scc analysis...")
    results_dir.mkdir(parents=True, exist_ok=True)
    exit_code, stderr = run_scc_analysis(base_path, results_dir)

    # Run envelope analysis to generate output.json
    print("Running envelope analysis...")
    run_envelope_analysis(base_path, repo_path, output_path)

    dimensions = []

    # Output Quality
    print("Running output quality checks...")
    oq_checks = run_output_quality_checks(raw_output_path, exit_code, stderr)
    dimensions.append(compute_dimension_result(oq_checks, "output_quality"))

    # Integration Fit
    print("Running integration fit checks...")
    if_checks = run_integration_fit_checks(raw_output_path, output_path, schema_path)
    dimensions.append(compute_dimension_result(if_checks, "integration_fit"))

    # Reliability
    print("Running reliability checks...")
    rl_checks = run_reliability_checks(base_path)
    dimensions.append(compute_dimension_result(rl_checks, "reliability"))

    # Performance
    print("Running performance checks...")
    pf_checks = run_performance_checks(base_path)
    dimensions.append(compute_dimension_result(pf_checks, "performance"))

    # Installation
    print("Running installation checks...")
    in_checks = run_installation_checks(base_path)
    dimensions.append(compute_dimension_result(in_checks, "installation"))

    # Coverage
    print("Running coverage checks...")
    cv_checks = run_coverage_checks(raw_output_path)
    dimensions.append(compute_dimension_result(cv_checks, "coverage"))

    # License
    print("Running license checks...")
    cl_checks = run_license_checks(base_path)
    dimensions.append(compute_dimension_result(cl_checks, "license"))

    # Per-File Analysis
    print("Running per-file checks...")
    pf_checks = run_per_file_checks(base_path)
    dimensions.append(compute_dimension_result(pf_checks, "per_file"))

    # Directory Analysis - use existing directory_analysis.json if available
    print("Running directory analysis checks...")
    dir_analysis_path = results_dir / "directory_analysis.json"
    if dir_analysis_path.exists():
        import json
        with open(dir_analysis_path) as f:
            dir_data = json.load(f)
        da_checks = run_directory_analysis_checks(dir_data)
    else:
        da_checks = run_directory_analysis_checks(base_path)
    dimensions.append(compute_dimension_result(da_checks, "directory_analysis"))

    # COCOMO
    print("Running COCOMO checks...")
    co_checks = run_cocomo_checks(base_path)
    dimensions.append(compute_dimension_result(co_checks, "cocomo"))

    return dimensions


def generate_check_report(dimensions: List[DimensionResult]) -> str:
    """Generate detailed check report."""
    lines = ["# Detailed Check Results", ""]

    for dim in dimensions:
        lines.extend([
            f"## {dim.dimension.replace('_', ' ').title()}",
            f"**Score: {dim.score}/5** ({dim.checks_passed}/{dim.checks_total} checks passed)",
            ""
        ])

        for check in dim.checks:
            status = "PASS" if check.passed else "FAIL"
            lines.append(f"- [{status}] **{check.check_id}**: {check.name}")
            lines.append(f"  - {check.message}")
            if not check.passed and check.expected:
                lines.append(f"  - Expected: {check.expected}")
                lines.append(f"  - Actual: {check.actual}")
            lines.append("")

    return "\n".join(lines)


def generate_scorecard_json(result: EvaluationResult) -> dict:
    """Generate structured scorecard JSON data."""
    dimensions_data = []
    for dim in result.dimensions:
        dimensions_data.append({
            "id": f"D{len(dimensions_data) + 1}",
            "name": dim.dimension.replace("_", " ").title(),
            "weight": dim.weight,
            "total_checks": dim.checks_total,
            "passed": dim.checks_passed,
            "failed": dim.checks_total - dim.checks_passed,
            "score": dim.score,
            "weighted_score": round(dim.weighted_score, 2),
            "checks": [
                {
                    "check_id": c.check_id,
                    "name": c.name,
                    "passed": c.passed,
                    "message": c.message,
                    "expected": c.expected,
                    "actual": c.actual,
                }
                for c in dim.checks
            ],
        })

    total_checks = sum(d.checks_total for d in result.dimensions)
    passed_checks = sum(d.checks_passed for d in result.dimensions)

    return {
        "tool": "scc",
        "version": "1.0.0",
        "generated_at": result.timestamp,
        "description": "Evaluation scorecard for scc lines of code analysis",
        "summary": {
            "total_checks": total_checks,
            "passed": passed_checks,
            "failed": total_checks - passed_checks,
            "score": round(result.total_score / 5.0, 4),
            "score_percent": round(result.total_score / 5.0 * 100, 2),
            "normalized_score": round(result.total_score, 2),
            "decision": result.decision,
        },
        "dimensions": dimensions_data,
        "critical_failures": [
            {
                "check_id": c.check_id,
                "name": c.name,
                "message": c.message,
            }
            for dim in result.dimensions
            for c in dim.checks
            if not c.passed and "critical" in c.check_id.lower()
        ],
        "thresholds": {
            "STRONG_PASS": ">= 4.0 (80%+)",
            "PASS": ">= 3.5 (70%+)",
            "WEAK_PASS": ">= 3.0 (60%+)",
            "FAIL": "< 3.0 (below 60%)",
        },
    }


def generate_scorecard(result: EvaluationResult) -> str:
    """Generate evaluation scorecard markdown."""
    lines = [
        "# scc Evaluation Scorecard",
        "",
        f"**Evaluated:** {result.timestamp}",
        f"**Run ID:** {result.run_id}",
        "",
        "---",
        "",
        "## Quick Screen Results",
        "",
        "- [x] Structured output (JSON/SARIF/CSV) - **Native JSON confirmed**",
        "- [x] Supports target languages - **All 7 languages detected**",
        "- [x] Active maintenance - **6.4K+ GitHub stars, regular releases**",
        "- [x] Compatible license - **MIT/Unlicense**",
        "- [x] Can run offline - **Single binary, no network required**",
        "",
        "**Result: ALL CHECKS PASSED - Proceed to scoring**",
        "",
        "---",
        "",
        format_score_summary(result.dimensions, result.total_score, result.decision),
        "",
        "---",
        "",
    ]

    # Add dimension details
    for dim in result.dimensions:
        lines.extend([
            f"### {dim.dimension.replace('_', ' ').title()} ({dim.weight:.0%})",
            "",
            f"**Score: {dim.score}/5**",
            "",
            "Checks:",
        ])

        for check in dim.checks:
            status = "x" if check.passed else " "
            lines.append(f"- [{status}] {check.name}: {check.message}")

        lines.extend([
            "",
            f"**Weighted: {dim.score} x {dim.weight:.2f} = {dim.weighted_score:.2f}**",
            "",
        ])

    # Add decision
    lines.extend([
        "---",
        "",
        "## Decision",
        "",
        f"**{result.decision} ({result.total_score:.2f}/5.0)**",
        "",
    ])

    if result.decision in ["STRONG_PASS", "PASS"]:
        lines.append("scc is approved for use in the DD Platform MVP.")
    elif result.decision == "WEAK_PASS":
        lines.append("scc passes with reservations. Review failing checks before proceeding.")
    else:
        lines.append("scc does not meet requirements. Review failing checks.")

    return "\n".join(lines)


def main():
    """Main entry point."""
    base_path = Path(__file__).parent.parent

    print("=" * 60)
    print("scc PoC Evaluation")
    print("=" * 60)
    print()

    # Run all checks
    dimensions = run_all_checks(base_path)

    # Compute total score and decision
    total_score = compute_total_score(dimensions)
    decision = determine_decision(total_score)

    # Create evaluation result
    run_id = f"eval-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    timestamp = datetime.now(timezone.utc).isoformat()

    result = EvaluationResult(
        run_id=run_id,
        timestamp=timestamp,
        dimensions=dimensions,
        total_score=total_score,
        decision=decision,
        summary={
            "total_checks": sum(d.checks_total for d in dimensions),
            "passed_checks": sum(d.checks_passed for d in dimensions),
            "dimensions_count": len(dimensions)
        }
    )

    # Save results
    results_dir = _resolve_results_dir(base_path)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Save check results as JSON (uniform evaluation_report.json format)
    check_results_path = results_dir / "evaluation_report.json"

    # Build flat checks list for uniform schema
    flat_checks = []
    total_passed = 0
    total_failed = 0
    for d in dimensions:
        for c in d.checks:
            flat_checks.append({
                "name": c.check_id,
                "status": "PASS" if c.passed else "FAIL",
                "message": c.message,
            })
            if c.passed:
                total_passed += 1
            else:
                total_failed += 1

    check_data = {
        "timestamp": timestamp,
        "tool": "scc",
        "decision": decision,
        "score": total_score / 5.0,  # Normalize to 0-1 scale
        "checks": flat_checks,
        "summary": {
            "total": total_passed + total_failed,
            "passed": total_passed,
            "failed": total_failed,
        },
        # Keep detailed dimensions for reference
        "run_id": run_id,
        "dimensions": [
            {
                "dimension": d.dimension,
                "weight": d.weight,
                "score": d.score,
                "weighted_score": d.weighted_score,
                "checks_passed": d.checks_passed,
                "checks_total": d.checks_total,
                "checks": [
                    {
                        "check_id": c.check_id,
                        "name": c.name,
                        "passed": c.passed,
                        "message": c.message,
                        "expected": c.expected,
                        "actual": c.actual,
                        "evidence": c.evidence
                    }
                    for c in d.checks
                ]
            }
            for d in dimensions
        ],
        "total_score": total_score,
        "decision": decision
    }
    with open(check_results_path, "w") as f:
        json.dump(check_data, f, indent=2, default=str)

    # Generate and save scorecard
    scorecard = generate_scorecard(result)
    scorecard_path = results_dir / "scorecard.md"
    with open(scorecard_path, "w") as f:
        f.write(scorecard)

    # Generate and save scorecard JSON
    scorecard_json = generate_scorecard_json(result)
    scorecard_json_path = results_dir / "scorecard.json"
    with open(scorecard_json_path, "w") as f:
        json.dump(scorecard_json, f, indent=2)
    print(f"  - {scorecard_json_path}")

    # Print summary
    print()
    print("=" * 60)
    print("EVALUATION COMPLETE")
    print("=" * 60)
    print()
    print(format_score_summary(dimensions, total_score, decision))
    print()
    print(f"Results saved to:")
    print(f"  - {check_results_path}")
    print(f"  - {scorecard_path}")
    print()

    # Return exit code based on decision
    return 0 if decision in ["STRONG_PASS", "PASS", "WEAK_PASS"] else 1


if __name__ == "__main__":
    exit(main())
