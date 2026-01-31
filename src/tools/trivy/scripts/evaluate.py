#!/usr/bin/env python3
"""Evaluation runner for Trivy analysis outputs."""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

import click
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class CheckResult:
    """Result of a single evaluation check."""
    
    check_id: str
    name: str
    category: str
    severity: str
    passed: bool
    score: float
    message: str
    evidence: dict


def generate_scorecard_md(summary: dict) -> str:
    """Generate a minimal markdown scorecard for compliance."""
    overall = summary.get("overall", {})
    lines = [
        "# Trivy Evaluation Scorecard",
        "",
        f"**Generated:** {summary.get('evaluated_at', '')}",
        f"**Decision:** {summary.get('decision', '')}",
        f"**Score:** {summary.get('score_percent', 0)}%",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total Checks | {overall.get('total', 0)} |",
        f"| Passed | {overall.get('passed', 0)} |",
        f"| Failed | {overall.get('total', 0) - overall.get('passed', 0)} |",
        f"| Pass Rate | {overall.get('pass_rate', 0):.2%} |",
        "",
    ]
    return "\n".join(lines)


def generate_scorecard_json(summary: dict) -> dict:
    """Generate a minimal scorecard JSON."""
    overall = summary.get("overall", {})
    score = overall.get("pass_rate", 0)
    normalized_score = score * 5.0
    decision = (
        "STRONG_PASS" if normalized_score >= 4.0 else
        "PASS" if normalized_score >= 3.5 else
        "WEAK_PASS" if normalized_score >= 3.0 else
        "FAIL"
    )
    return {
        "tool": "trivy",
        "version": "1.0.0",
        "generated_at": summary.get("evaluated_at", ""),
        "summary": {
            "total_checks": overall.get("total", 0),
            "passed": overall.get("passed", 0),
            "failed": overall.get("total", 0) - overall.get("passed", 0),
            "score_percent": round(score * 100, 2),
            "normalized_score": round(normalized_score, 2),
            "decision": decision,
        },
    }


def load_ground_truth(gt_path: Path) -> dict | None:
    """Load ground truth file if it exists."""
    if gt_path.exists():
        return json.loads(gt_path.read_text())
    return None


def _get_results_section(data: dict) -> dict:
    """Get the results section, handling both envelope and legacy formats.

    Envelope format: {"metadata": {...}, "data": {...}}
    Legacy format: {"results": {...}}
    """
    # Try envelope format first (metadata + data)
    if "metadata" in data and "data" in data:
        return data.get("data", {})
    # Fall back to legacy format (results)
    return data.get("results", {})


def check_vulnerability_count(data: dict, ground_truth: dict | None) -> CheckResult:
    """TR-AC-1: Check vulnerability count accuracy."""
    results = _get_results_section(data)
    vulns = results.get("vulnerabilities", [])
    actual = len(vulns)
    
    if ground_truth:
        expected = ground_truth.get("expected_vulnerabilities", {})
        min_val = expected.get("min", 0)
        max_val = expected.get("max", float("inf"))
        passed = min_val <= actual <= max_val
    else:
        passed = True  # No ground truth, assume pass
        min_val, max_val = 0, float("inf")
    
    return CheckResult(
        check_id="TR-AC-1",
        name="Vulnerability count accuracy",
        category="accuracy",
        severity="critical",
        passed=passed,
        score=1.0 if passed else 0.0,
        message=f"Found {actual} vulnerabilities (expected {min_val}-{max_val})",
        evidence={"actual": actual, "expected_min": min_val, "expected_max": max_val},
    )


def check_critical_count(data: dict, ground_truth: dict | None) -> CheckResult:
    """TR-AC-2: Check critical vulnerability count."""
    results = _get_results_section(data)
    # Handle both envelope format (findings_summary.by_severity) and legacy (summary)
    summary = results.get("findings_summary", results.get("summary", {}))
    by_severity = summary.get("by_severity", {})
    # Legacy format uses critical_count directly
    actual = by_severity.get("CRITICAL", summary.get("critical_count", 0))
    
    if ground_truth:
        expected = ground_truth.get("expected_critical", {})
        min_val = expected.get("min", 0)
        max_val = expected.get("max", float("inf"))
        passed = min_val <= actual <= max_val
    else:
        passed = True
        min_val, max_val = 0, float("inf")
    
    return CheckResult(
        check_id="TR-AC-2",
        name="Critical count accuracy",
        category="accuracy",
        severity="critical",
        passed=passed,
        score=1.0 if passed else 0.0,
        message=f"Found {actual} critical vulnerabilities (expected {min_val}-{max_val})",
        evidence={"actual": actual, "expected_min": min_val, "expected_max": max_val},
    )


def check_required_fields(data: dict, ground_truth: dict | None) -> CheckResult:
    """TR-CM-4: Check required vulnerability fields are present."""
    results = _get_results_section(data)
    vulns = results.get("vulnerabilities", [])
    required_fields = ["id", "package", "severity"]
    
    missing = []
    for i, vuln in enumerate(vulns):
        for field in required_fields:
            if not vuln.get(field):
                missing.append(f"vulnerability[{i}].{field}")
    
    passed = len(missing) == 0
    score = 1.0 - (len(missing) / max(len(vulns) * len(required_fields), 1))
    
    return CheckResult(
        check_id="TR-CM-4",
        name="Vulnerability required fields",
        category="completeness",
        severity="high",
        passed=passed,
        score=max(0, score),
        message=f"Required fields present" if passed else f"Missing {len(missing)} required fields",
        evidence={"missing": missing[:10]},  # Limit evidence size
    )


def check_target_coverage(data: dict, ground_truth: dict | None) -> CheckResult:
    """TR-CV-1: Check all expected targets are detected."""
    results = _get_results_section(data)
    targets = results.get("targets", [])
    # If targets not explicitly listed, extract unique targets from vulnerabilities
    if not targets:
        vulns = results.get("vulnerabilities", [])
        unique_targets = {v.get("target", "") for v in vulns if v.get("target")}
        target_paths = list(unique_targets)
    else:
        target_paths = [t.get("path", "") for t in targets]
    
    if ground_truth:
        expected_targets = ground_truth.get("expected_targets", [])
        missing = [t for t in expected_targets if t not in target_paths]
        passed = len(missing) == 0
    else:
        passed = len(targets) > 0
        missing = []
    
    return CheckResult(
        check_id="TR-CV-1",
        name="Target coverage",
        category="coverage",
        severity="high",
        passed=passed,
        score=1.0 if passed else 0.0,
        message=f"Found {len(targets)} targets" if passed else f"Missing targets: {missing}",
        evidence={"found": target_paths, "missing": missing},
    )


def check_metadata_consistency(data: dict, ground_truth: dict | None) -> CheckResult:
    """Check metadata consistency.

    Handles both envelope format (metadata at root) and legacy format
    (metadata fields in results or at root level).
    """
    # Check for envelope format first
    if "metadata" in data and "data" in data:
        metadata = data.get("metadata", {})
        is_envelope = True
    else:
        # Legacy format - check root level and results
        metadata = {
            "schema_version": data.get("schema_version"),
            "tool_name": data.get("results", {}).get("tool", "trivy"),
            "run_id": data.get("run_id"),
            "repo_id": data.get("repo_id"),
            "branch": data.get("branch"),
            "commit": data.get("commit"),
            "timestamp": data.get("generated_at"),
        }
        is_envelope = False

    issues = []

    # Check schema version
    schema_version = metadata.get("schema_version")
    if schema_version and schema_version != "1.0.0":
        issues.append(f"schema_version is {schema_version}, expected 1.0.0")
    elif not schema_version and is_envelope:
        issues.append("schema_version missing")

    # Check tool name (only for envelope format)
    tool_name = metadata.get("tool_name")
    if is_envelope and tool_name != "trivy":
        issues.append(f"tool_name is {tool_name}, expected trivy")

    # Check required fields (only for envelope format, legacy format is lenient)
    if is_envelope:
        required = ["run_id", "repo_id", "branch", "commit", "timestamp"]
        for field in required:
            if not metadata.get(field):
                issues.append(f"missing {field}")

    passed = len(issues) == 0

    return CheckResult(
        check_id="TR-CM-3",
        name="Metadata consistency",
        category="completeness",
        severity="medium",
        passed=passed,
        score=1.0 if passed else 0.5,
        message="Metadata consistent" if passed else f"Issues: {issues}",
        evidence={"issues": issues, "format": "envelope" if is_envelope else "legacy"},
    )


def run_all_checks(data: dict, ground_truth: dict | None) -> list[CheckResult]:
    """Run all evaluation checks."""
    checks = [
        check_vulnerability_count,
        check_critical_count,
        check_required_fields,
        check_target_coverage,
        check_metadata_consistency,
    ]
    
    results = []
    for check_fn in checks:
        try:
            result = check_fn(data, ground_truth)
            results.append(result)
        except Exception as e:
            logger.error(f"Check {check_fn.__name__} failed", error=str(e))
    
    return results


def compute_scores(results: list[CheckResult]) -> dict:
    """Compute aggregate scores from check results."""
    by_category = {}
    for result in results:
        cat = result.category
        if cat not in by_category:
            by_category[cat] = {"passed": 0, "total": 0, "scores": []}
        by_category[cat]["total"] += 1
        if result.passed:
            by_category[cat]["passed"] += 1
        by_category[cat]["scores"].append(result.score)
    
    category_scores = {}
    for cat, data in by_category.items():
        category_scores[cat] = {
            "passed": data["passed"],
            "total": data["total"],
            "pass_rate": data["passed"] / data["total"] if data["total"] > 0 else 0,
            "avg_score": sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0,
        }
    
    overall_passed = sum(1 for r in results if r.passed)
    overall_total = len(results)
    
    return {
        "overall": {
            "passed": overall_passed,
            "total": overall_total,
            "pass_rate": overall_passed / overall_total if overall_total > 0 else 0,
        },
        "by_category": category_scores,
    }


def aggregate_scores(evaluations: list[dict]) -> dict:
    """Aggregate overall scores from multiple evaluations."""
    total = sum(e["scores"]["overall"]["total"] for e in evaluations)
    passed = sum(e["scores"]["overall"]["passed"] for e in evaluations)
    return {
        "overall": {
            "passed": passed,
            "total": total,
            "pass_rate": passed / total if total > 0 else 0,
        }
    }


def evaluate_repository(
    analysis_path: Path,
    ground_truth_path: Path | None = None,
) -> dict:
    """Evaluate a repository's analysis output.

    This function provides a programmatic interface for evaluation,
    used by integration tests and other tools.

    Args:
        analysis_path: Path to the analysis JSON file
        ground_truth_path: Optional path to ground truth file

    Returns:
        Dictionary containing evaluation results with scores and check details
    """
    data = json.loads(analysis_path.read_text())
    ground_truth = load_ground_truth(ground_truth_path) if ground_truth_path else None

    results = run_all_checks(data, ground_truth)
    scores = compute_scores(results)

    return {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "input_file": str(analysis_path),
        "ground_truth_file": str(ground_truth_path) if ground_truth_path else None,
        "scores": scores,
        "checks": [asdict(r) for r in results],
    }


@click.command()
@click.option(
    "--input",
    "input_path",
    type=click.Path(exists=True, path_type=Path),
    help="Single input file to evaluate",
)
@click.option(
    "--ground-truth",
    "gt_path",
    type=click.Path(path_type=Path),
    help="Ground truth file",
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(path_type=Path),
    required=True,
    help="Output directory or file",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
def main(
    input_path: Path | None,
    gt_path: Path | None,
    output_path: Path,
    verbose: bool,
):
    """Run evaluation on Trivy analysis outputs."""
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
    
    if input_path and input_path.exists():
        # Single file evaluation
        data = json.loads(input_path.read_text())
        ground_truth = load_ground_truth(gt_path) if gt_path else None
        
        results = run_all_checks(data, ground_truth)
        scores = compute_scores(results)
        
        evaluation = {
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "input_file": str(input_path),
            "ground_truth_file": str(gt_path) if gt_path else None,
            "scores": scores,
            "checks": [asdict(r) for r in results],
        }
        
        # Determine output file
        if output_path.suffix == ".json":
            out_file = output_path
        else:
            output_path.mkdir(parents=True, exist_ok=True)
            out_file = output_path / f"{input_path.stem}-eval.json"
        
        out_file.write_text(json.dumps(evaluation, indent=2))
        
        # Print summary
        click.echo(f"Evaluation complete: {out_file}")
        click.echo(f"Pass rate: {scores['overall']['pass_rate']:.1%}")
        click.echo(f"Passed: {scores['overall']['passed']}/{scores['overall']['total']}")

        # Compliance artifacts
        out_dir = out_file.parent
        summary = {
            "evaluated_at": evaluation["evaluated_at"],
            "overall": scores["overall"],
        }
        checks_path = out_dir / "checks.json"
        scorecard_json_path = out_dir / "scorecard.json"
        scorecard_md_path = out_dir / "scorecard.md"
        checks_path.write_text(json.dumps(evaluation, indent=2))
        scorecard_json = generate_scorecard_json(summary)
        scorecard_json_path.write_text(json.dumps(scorecard_json, indent=2))
        scorecard_md_path.write_text(generate_scorecard_md(summary))
    else:
        # Batch evaluation - find all output files
        output_dir = Path("output/runs")
        gt_dir = Path("evaluation/ground-truth")
        
        all_evaluations = []
        for output_file in output_dir.glob("*.json"):
            data = json.loads(output_file.read_text())
            gt_file = gt_dir / f"{output_file.stem}.json"
            ground_truth = load_ground_truth(gt_file)
            
            results = run_all_checks(data, ground_truth)
            scores = compute_scores(results)
            
            all_evaluations.append({
                "input_file": str(output_file),
                "scores": scores,
                "check_count": len(results),
            })
        
        # Write summary
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        summary = {
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "evaluations": all_evaluations,
        }
        
        (output_path / "summary.json").write_text(json.dumps(summary, indent=2))
        click.echo(f"Evaluated {len(all_evaluations)} files")

        # Compliance artifacts
        checks_path = output_path / "checks.json"
        scorecard_json_path = output_path / "scorecard.json"
        scorecard_md_path = output_path / "scorecard.md"
        checks_path.write_text(json.dumps(summary, indent=2))
        scorecard_json = generate_scorecard_json({
            "evaluated_at": summary["evaluated_at"],
            "overall": aggregate_scores(all_evaluations),
        })
        scorecard_json_path.write_text(json.dumps(scorecard_json, indent=2))
        scorecard_md_path.write_text(generate_scorecard_md({
            "evaluated_at": summary["evaluated_at"],
            "overall": aggregate_scores(all_evaluations)["overall"],
        }))


if __name__ == "__main__":
    main()
