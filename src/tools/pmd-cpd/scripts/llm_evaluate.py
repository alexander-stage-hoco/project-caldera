#!/usr/bin/env python3
"""
LLM-based evaluation for PMD CPD analysis.

Runs 4 LLM judges to evaluate duplication detection quality:
- Duplication Accuracy (35%): Are detected clones genuine?
- Semantic Detection (25%): Does semantic mode work?
- Cross-File Detection (20%): Are cross-file clones found?
- Actionability (20%): Are reports useful for refactoring?

Usage:
    python llm_evaluate.py --analysis output/runs/synthetic.json --model opus
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.llm.judges import (
    JudgeResult,
    DuplicationAccuracyJudge,
    SemanticDetectionJudge,
    CrossFileDetectionJudge,
    ActionabilityJudge,
)


def calculate_combined_score(
    programmatic_score: float,  # 0.0-1.0 or 1.0-5.0
    llm_score: float,  # 1-5
    programmatic_weight: float = 0.60,
    llm_weight: float = 0.40,
) -> dict[str, Any]:
    """Calculate combined score from programmatic and LLM evaluations.

    Returns dict with:
    - combined_score: 1-5 scale
    - programmatic_contribution: weighted contribution
    - llm_contribution: weighted contribution
    - decision: STRONG_PASS, PASS, WEAK_PASS, FAIL
    """
    # Score may be on 0-1 or 1-5 scale; normalize to 1-5
    if programmatic_score <= 1.0:
        programmatic_normalized = programmatic_score * 4 + 1  # 0.0 -> 1, 1.0 -> 5
    else:
        programmatic_normalized = programmatic_score  # Already on 1-5 scale

    combined = (
        programmatic_normalized * programmatic_weight +
        llm_score * llm_weight
    )

    if combined >= 4.0:
        decision = "STRONG_PASS"
    elif combined >= 3.5:
        decision = "PASS"
    elif combined >= 3.0:
        decision = "WEAK_PASS"
    else:
        decision = "FAIL"

    return {
        "combined_score": round(combined, 2),
        "programmatic_contribution": round(programmatic_normalized * programmatic_weight, 2),
        "llm_contribution": round(llm_score * llm_weight, 2),
        "programmatic_normalized": round(programmatic_normalized, 2),
        "llm_score": round(llm_score, 2),
        "decision": decision,
    }


def run_llm_evaluation(
    analysis_path: str,
    model: str = "opus",
    skip_judges: list[str] | None = None,
) -> dict[str, Any]:
    """Run all LLM judges and return combined results."""
    working_dir = Path(__file__).parent.parent
    output_dir = Path(analysis_path).parent

    skip_judges = skip_judges or []

    # Initialize judges
    judges = [
        DuplicationAccuracyJudge(
            model=model,
            working_dir=working_dir,
            analysis_path=Path(analysis_path),
            output_dir=output_dir,
        ),
        SemanticDetectionJudge(
            model=model,
            working_dir=working_dir,
            analysis_path=Path(analysis_path),
            output_dir=output_dir,
        ),
        CrossFileDetectionJudge(
            model=model,
            working_dir=working_dir,
            analysis_path=Path(analysis_path),
            output_dir=output_dir,
        ),
        ActionabilityJudge(
            model=model,
            working_dir=working_dir,
            analysis_path=Path(analysis_path),
            output_dir=output_dir,
        ),
    ]

    # Filter out skipped judges
    judges = [j for j in judges if j.dimension_name not in skip_judges]

    # Run evaluations
    results = []
    for judge in judges:
        print(f"Running {judge.dimension_name} judge...")
        try:
            result = judge.evaluate()
            results.append({
                "dimension": result.dimension,
                "weight": judge.weight,
                "score": result.score,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "evidence_cited": result.evidence_cited,
                "recommendations": result.recommendations,
                "sub_scores": result.sub_scores,
            })
            print(f"  Score: {result.score}/5 (confidence: {result.confidence:.2f})")
        except Exception as e:
            print(f"  Error: {e}")
            results.append({
                "dimension": judge.dimension_name,
                "weight": judge.weight,
                "score": 0,
                "confidence": 0.0,
                "reasoning": f"Error running judge: {e}",
                "evidence_cited": [],
                "recommendations": [],
                "sub_scores": {},
            })

    # Calculate weighted score
    total_weight = sum(r["weight"] for r in results)
    weighted_score = (
        sum(r["score"] * r["weight"] for r in results) / total_weight
        if total_weight > 0
        else 0
    )

    return {
        "timestamp": datetime.now().isoformat(),
        "analysis_path": analysis_path,
        "model": model,
        "summary": {
            "weighted_score": round(weighted_score, 2),
            "weighted_score_pct": round(weighted_score / 5 * 100, 1),
            "judge_count": len(results),
        },
        "judges": results,
    }


def print_report(report: dict[str, Any]):
    """Print the LLM evaluation report."""
    print()
    print("=" * 70)
    print("PMD CPD LLM EVALUATION REPORT")
    print("=" * 70)
    print()
    print(f"Analysis: {report['analysis_path']}")
    print(f"Model: {report['model']}")
    print(f"Timestamp: {report['timestamp']}")
    print()

    # Summary
    summary = report["summary"]
    print("-" * 70)
    print("SUMMARY")
    print("-" * 70)
    print(f"Weighted Score: {summary['weighted_score']}/5.0 ({summary['weighted_score_pct']}%)")
    print(f"Judges Run: {summary['judge_count']}")
    print()

    # Individual judge results
    print("-" * 70)
    print("JUDGE RESULTS")
    print("-" * 70)

    for result in report["judges"]:
        print(f"\n{result['dimension'].upper()} (weight: {result['weight']:.0%})")
        print(f"  Score: {result['score']}/5 (confidence: {result['confidence']:.2f})")
        print(f"  Reasoning: {result['reasoning'][:200]}...")

        if result["sub_scores"]:
            print("  Sub-scores:")
            for name, score in result["sub_scores"].items():
                print(f"    - {name}: {score}/5")

        if result["recommendations"]:
            print("  Recommendations:")
            for rec in result["recommendations"][:3]:
                print(f"    - {rec}")

    print()
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="PMD CPD LLM Evaluation"
    )
    parser.add_argument(
        "--analysis",
        "-a",
        required=True,
        help="Path to analysis JSON file",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output JSON file path",
    )
    parser.add_argument(
        "--model",
        "-m",
        default="opus",
        choices=["opus", "sonnet", "haiku", "opus-4.5"],
        help="Claude model to use (default: opus)",
    )
    parser.add_argument(
        "--skip-judge",
        action="append",
        dest="skip_judges",
        default=[],
        help="Skip specific judges (can be repeated)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON only",
    )
    parser.add_argument(
        "--programmatic-score",
        type=float,
        help="Programmatic evaluation score (0.0-1.0) for combined scoring",
    )
    parser.add_argument(
        "--programmatic-results",
        type=Path,
        help="Path to programmatic evaluation JSON (evaluation_report.json)",
    )

    args = parser.parse_args()

    # Validate inputs
    if not Path(args.analysis).exists():
        print(f"Error: Analysis file not found: {args.analysis}")
        sys.exit(1)

    # Run evaluation
    report = run_llm_evaluation(
        args.analysis,
        model=args.model,
        skip_judges=args.skip_judges,
    )

    # Get weighted score for decision
    weighted_score = report["summary"]["weighted_score"]

    # Determine decision based on weighted score
    if weighted_score >= 4.0:
        decision = "STRONG_PASS"
    elif weighted_score >= 3.5:
        decision = "PASS"
    elif weighted_score >= 3.0:
        decision = "WEAK_PASS"
    else:
        decision = "FAIL"

    # Add compliance-required root-level fields
    report["model"] = args.model
    report["score"] = round(weighted_score, 2)
    report["decision"] = decision

    # Load programmatic evaluation results if path provided
    if args.programmatic_results and args.programmatic_results.exists():
        try:
            prog_data = json.loads(args.programmatic_results.read_text())
            summary = prog_data.get("summary", {})
            # Support both 'score' and 'total_score' field names
            prog_score = prog_data.get("score") or prog_data.get("total_score") or summary.get("score", 0.0)
            report["programmatic_input"] = {
                "file": str(args.programmatic_results),
                "decision": prog_data.get("decision", summary.get("decision", "UNKNOWN")),
                "score": prog_score,
                "passed": summary.get("passed", 0),
                "failed": summary.get("failed", 0),
                "total": summary.get("total", 0),
            }
            # Compute combined score from loaded results
            combined = calculate_combined_score(
                programmatic_score=prog_score,
                llm_score=weighted_score,
            )
            report["combined"] = combined
        except Exception:
            pass  # Continue without programmatic input

    # Add combined scoring if programmatic score provided
    if args.programmatic_score is not None:
        combined = calculate_combined_score(
            programmatic_score=args.programmatic_score,
            llm_score=weighted_score,
        )
        report["combined"] = combined

    # Print or output
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        if not args.json:
            print(f"\nReport saved to: {args.output}")

    # Exit with appropriate code
    if weighted_score < 3.0:
        sys.exit(1)


if __name__ == "__main__":
    main()
