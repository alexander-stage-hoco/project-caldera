#!/usr/bin/env python3
"""Architecture reviewer CLI — programmatic (heuristic) checker.

Runs deterministic architecture conformance checks against Project Caldera tool
implementations and produces JSON results matching review_result.schema.json.

Usage:
    python reviewer.py --target scc
    python reviewer.py --target pmd-cpd --review-type tool_implementation
    python reviewer.py --target cross-tool --review-type cross_tool
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure this module's directory is on sys.path for local imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from checks.d1_entity_persistence import check_d1
from checks.d1_entity_persistence import DIMENSION as D1_DIM, WEIGHT as D1_WEIGHT
from checks.d2_output_schema import check_d2
from checks.d2_output_schema import DIMENSION as D2_DIM, WEIGHT as D2_WEIGHT
from checks.d3_code_conventions import check_d3
from checks.d3_code_conventions import DIMENSION as D3_DIM, WEIGHT as D3_WEIGHT
from checks.d4_evaluation_infra import check_d4
from checks.d4_evaluation_infra import DIMENSION as D4_DIM, WEIGHT as D4_WEIGHT
from checks.d5_cross_tool import check_d5
from checks.d5_cross_tool import DIMENSION as D5_DIM, WEIGHT as D5_WEIGHT
from checks.d6_blueprint import check_d6
from checks.d6_blueprint import DIMENSION as D6_DIM, WEIGHT as D6_WEIGHT
from discovery import discover_tool_files
from models import DimensionResult, Finding, ReviewResult, ReviewSummary
from scoring import compute_overall, score_dimension, status_from_score

# Review type → dimensions to run
REVIEW_TYPE_DIMENSIONS = {
    "tool_implementation": ["D1", "D2", "D3", "D4", "D6"],
    "cross_tool": ["D5"],
    "blueprint_alignment": ["D6"],
}


def _find_project_root() -> Path:
    """Auto-detect project root by walking up from this file to find CLAUDE.md."""
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / "CLAUDE.md").exists():
            return p
        p = p.parent
    return Path.cwd()


def _run_dimension(
    dim_id: str, target: str, project_root: Path,
) -> DimensionResult:
    """Run a single dimension's checks and return a scored result."""
    if dim_id == "D1":
        tf = discover_tool_files(target, project_root)
        findings = check_d1(tf, project_root)
        dim_name, weight = D1_DIM, D1_WEIGHT
    elif dim_id == "D2":
        tf = discover_tool_files(target, project_root)
        findings = check_d2(tf)
        dim_name, weight = D2_DIM, D2_WEIGHT
    elif dim_id == "D3":
        tf = discover_tool_files(target, project_root)
        findings = check_d3(tf)
        dim_name, weight = D3_DIM, D3_WEIGHT
    elif dim_id == "D4":
        tf = discover_tool_files(target, project_root)
        findings = check_d4(tf)
        dim_name, weight = D4_DIM, D4_WEIGHT
    elif dim_id == "D5":
        findings = check_d5(project_root)
        dim_name, weight = D5_DIM, D5_WEIGHT
    elif dim_id == "D6":
        tf = discover_tool_files(target, project_root)
        findings = check_d6(tf)
        dim_name, weight = D6_DIM, D6_WEIGHT
    else:
        raise ValueError(f"Unknown dimension: {dim_id}")

    score = score_dimension(findings)
    status = status_from_score(score)
    return DimensionResult(
        dimension=dim_name,
        weight=weight,
        status=status,
        score=score,
        findings=findings,
    )


def run_review(
    target: str,
    review_type: str,
    project_root: Path,
    output_dir: Path | None = None,
) -> ReviewResult:
    """Run a full architecture review.

    Args:
        target: Tool name or 'cross-tool'.
        review_type: One of tool_implementation, cross_tool, blueprint_alignment.
        project_root: Path to project root.
        output_dir: Directory for output JSON (default: src/architecture-review/results).

    Returns:
        The ReviewResult.
    """
    dim_ids = REVIEW_TYPE_DIMENSIONS.get(review_type, [])
    dimensions: list[DimensionResult] = []

    for dim_id in dim_ids:
        dim_result = _run_dimension(dim_id, target, project_root)
        dimensions.append(dim_result)

    # Compute summary
    all_findings: list[Finding] = []
    for d in dimensions:
        all_findings.extend(d.findings)

    overall_score, overall_status = compute_overall(dimensions)
    by_severity = {
        "error": sum(1 for f in all_findings if f.severity == "error"),
        "warning": sum(1 for f in all_findings if f.severity == "warning"),
        "info": sum(1 for f in all_findings if f.severity == "info"),
    }

    summary = ReviewSummary(
        total_findings=len(all_findings),
        by_severity=by_severity,
        overall_status=overall_status,
        overall_score=overall_score,
        dimensions_reviewed=len(dimensions),
    )

    result = ReviewResult(
        review_id=ReviewResult.create_id(),
        timestamp=ReviewResult.create_timestamp(),
        target=target,
        review_type=review_type,
        dimensions=dimensions,
        summary=summary,
    )

    # Write output
    if output_dir is None:
        output_dir = Path(__file__).resolve().parent / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{target}-programmatic-{result.timestamp[:19].replace(':', '')}.json"
    output_path = output_dir / filename
    output_path.write_text(json.dumps(result.to_dict(), indent=2) + "\n")

    return result


def _print_summary(result: ReviewResult) -> None:
    """Print a human-readable summary to stdout."""
    s = result.summary
    print(f"\nArchitecture Review: {result.target} ({result.review_type})")
    print(f"{'=' * 60}")
    print(f"Overall: {s.overall_status} (score: {s.overall_score})")
    print(f"Findings: {s.total_findings} "
          f"(errors: {s.by_severity['error']}, "
          f"warnings: {s.by_severity['warning']}, "
          f"info: {s.by_severity['info']})")
    print()
    for d in result.dimensions:
        print(f"  {d.dimension}: {d.status} (score: {d.score}, "
              f"findings: {len(d.findings)})")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Architecture reviewer — programmatic (heuristic) checker"
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Tool name to review (e.g., 'scc', 'lizard') or 'cross-tool'",
    )
    parser.add_argument(
        "--review-type",
        default="tool_implementation",
        choices=["tool_implementation", "cross_tool", "blueprint_alignment"],
        help="Type of review to perform (default: tool_implementation)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for results JSON (default: src/architecture-review/results)",
    )
    parser.add_argument(
        "--project-root",
        default=None,
        help="Project root directory (default: auto-detect from git root)",
    )

    args = parser.parse_args()

    project_root = Path(args.project_root) if args.project_root else _find_project_root()
    output_dir = Path(args.output_dir) if args.output_dir else None

    result = run_review(
        target=args.target,
        review_type=args.review_type,
        project_root=project_root,
        output_dir=output_dir,
    )

    _print_summary(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
