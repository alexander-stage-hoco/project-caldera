#!/usr/bin/env python3
"""Generate combined scorecard from programmatic and LLM evaluations.

Usage:
    python scripts/generate_combined_report.py
    python scripts/generate_combined_report.py --programmatic-file evaluation/results/eval-xxx.json
    python scripts/generate_combined_report.py --llm-file evaluation/results/llm_evaluation.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def load_latest_file(pattern: str, directory: Path) -> Path | None:
    """Load the most recent file matching pattern."""
    files = sorted(directory.glob(pattern))
    return files[-1] if files else None


def load_programmatic_results(file_path: Path | None, results_dir: Path) -> dict:
    """Load programmatic evaluation results."""
    if file_path is None:
        static_path = results_dir / "checks.json"
        file_path = static_path if static_path.exists() else load_latest_file("eval-*_checks.json", results_dir)

    if file_path is None or not file_path.exists():
        return {"error": "Programmatic results not found"}

    data = json.loads(file_path.read_text())
    dimensions = data.get("dimensions", [])
    total_checks = sum(d.get("checks_total", 0) for d in dimensions if isinstance(d, dict))
    passed_checks = sum(d.get("checks_passed", 0) for d in dimensions if isinstance(d, dict))
    return {
        "file": str(file_path),
        "run_id": data.get("run_id", "unknown"),
        "total_score": data.get("total_score", 0),
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "decision": data.get("decision", "UNKNOWN"),
        "dimensions": dimensions,
    }


def load_llm_results(file_path: Path | None, results_dir: Path) -> dict:
    """Load LLM evaluation results."""
    if file_path is None:
        static_path = results_dir / "llm_evaluation.json"
        file_path = static_path if static_path.exists() else load_latest_file("llm-eval-*.json", results_dir)

    if file_path is None or not file_path.exists():
        return {"error": "LLM results not found"}

    data = json.loads(file_path.read_text())
    return {
        "file": str(file_path),
        "run_id": data.get("run_id", "unknown"),
        "total_score": data.get("total_score", 0),
        "average_confidence": data.get("average_confidence", 0),
        "decision": data.get("decision", "UNKNOWN"),
        "dimensions": data.get("dimensions", []),
    }


def compute_combined_score(
    prog_score: float,
    llm_score: float,
    prog_weight: float = 0.60,
    llm_weight: float = 0.40,
) -> tuple[float, str]:
    """Compute combined score and decision."""
    combined = prog_score * prog_weight + llm_score * llm_weight

    if combined >= 4.0:
        decision = "STRONG_PASS"
    elif combined >= 3.5:
        decision = "PASS"
    elif combined >= 3.0:
        decision = "WEAK_PASS"
    else:
        decision = "FAIL"

    return combined, decision


def generate_combined_scorecard(
    prog_results: dict,
    llm_results: dict,
    output_file: Path,
) -> str:
    """Generate combined scorecard markdown."""
    timestamp = datetime.now(timezone.utc).isoformat()

    prog_score = prog_results.get("total_score", 0)
    llm_score = llm_results.get("total_score", 0)

    combined_score, decision = compute_combined_score(prog_score, llm_score)

    lines = [
        "# scc Evaluation Scorecard (Combined)",
        "",
        f"**Generated:** {timestamp}",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"| Evaluation Type | Score | Weight | Weighted |",
        f"|-----------------|-------|--------|----------|",
        f"| Programmatic | {prog_score:.2f}/5.0 | 60% | {prog_score * 0.60:.2f} |",
        f"| LLM-as-Judge | {llm_score:.2f}/5.0 | 40% | {llm_score * 0.40:.2f} |",
        f"| **Combined** | **{combined_score:.2f}/5.0** | 100% | **{combined_score:.2f}** |",
        "",
        f"## Decision: **{decision}**",
        "",
        "---",
        "",
        "## Programmatic Evaluation",
        "",
    ]

    if "error" in prog_results:
        lines.append(f"**Error:** {prog_results['error']}")
    else:
        lines.extend([
            f"**Run ID:** {prog_results['run_id']}",
            f"**Checks:** {prog_results['passed_checks']}/{prog_results['total_checks']}",
            f"**Score:** {prog_results['total_score']:.2f}/5.0",
            "",
            "| Dimension | Passed | Total | Score |",
            "|-----------|--------|-------|-------|",
        ])
        for dim in prog_results.get("dimensions", []):
            if not isinstance(dim, dict):
                continue
            passed = dim.get("checks_passed", 0)
            total = dim.get("checks_total", 0)
            score = dim.get("score", 0)
            lines.append(f"| {dim.get('dimension', 'Unknown')} | {passed} | {total} | {score}/5 |")

    lines.extend([
        "",
        "---",
        "",
        "## LLM-as-Judge Evaluation",
        "",
    ])

    if "error" in llm_results:
        lines.append(f"**Error:** {llm_results['error']}")
    else:
        lines.extend([
            f"**Run ID:** {llm_results['run_id']}",
            f"**Average Confidence:** {llm_results['average_confidence']:.2f}",
            f"**Score:** {llm_results['total_score']:.2f}/5.0",
            "",
            "| Dimension | Score | Weight | Confidence |",
            "|-----------|-------|--------|------------|",
        ])
        for dim in llm_results.get("dimensions", []):
            score = dim.get("score", 0)
            weight = dim.get("weight", 0)
            conf = dim.get("confidence", 0)
            lines.append(f"| {dim.get('name', 'Unknown')} | {score}/5 | {weight:.0%} | {conf:.2f} |")

    lines.extend([
        "",
        "---",
        "",
        "## Decision Thresholds",
        "",
        "| Decision | Threshold |",
        "|----------|-----------|",
        "| STRONG_PASS | >= 4.0 |",
        "| PASS | >= 3.5 |",
        "| WEAK_PASS | >= 3.0 |",
        "| FAIL | < 3.0 |",
        "",
        "---",
        "",
        f"*Combined score calculated as: (Programmatic × 60%) + (LLM × 40%)*",
    ])

    content = "\n".join(lines)

    # Write to file
    output_file.write_text(content)

    return content


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate combined scorecard from programmatic and LLM evaluations"
    )
    parser.add_argument(
        "--programmatic-file",
        type=Path,
        help="Programmatic evaluation results file",
    )
    parser.add_argument(
        "--llm-file",
        type=Path,
        help="LLM evaluation results file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent.parent / "evaluation" / "results" / "combined_scorecard.md",
        help="Output file path",
    )
    parser.add_argument(
        "--working-dir",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Working directory",
    )

    args = parser.parse_args()

    prog_results_dir = args.working_dir / "evaluation" / "results"
    llm_results_dir = prog_results_dir

    print("Loading programmatic results...")
    prog_results = load_programmatic_results(args.programmatic_file, prog_results_dir)

    print("Loading LLM results...")
    llm_results = load_llm_results(args.llm_file, llm_results_dir)

    print("Generating combined scorecard...")
    content = generate_combined_scorecard(prog_results, llm_results, args.output)

    print()
    print("=" * 60)
    print(content)
    print("=" * 60)
    print()
    print(f"Saved to: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
