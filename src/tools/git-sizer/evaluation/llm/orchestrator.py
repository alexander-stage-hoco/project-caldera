#!/usr/bin/env python3
"""
Run LLM judges for git-sizer evaluation.

Usage:
    python -m evaluation.llm.run_judges output/output.json
    python -m evaluation.llm.run_judges output/output.json --output evaluation/llm/results.json
    python -m evaluation.llm.run_judges output/output.json --judge size_accuracy
"""

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shared.evaluation import require_observability, ProgrammaticInput

from .judges import (
    JUDGES,
    SizeAccuracyJudge,
    ThresholdQualityJudge,
    ActionabilityJudge,
    IntegrationFitJudge,
)


def run_all_judges(
    analysis_path: Path,
    model: str = "sonnet",
    timeout: int = 120,
    specific_judge: str | None = None,
    programmatic_input: ProgrammaticInput | None = None,
    working_dir: Path | None = None,
) -> dict:
    """Run all judges and return combined results."""
    # Enforce observability - fail fast if disabled
    require_observability()

    # Derive working_dir from this file's location (evaluation/llm/orchestrator.py)
    # Go up 2 levels to reach the git-sizer tool directory
    if working_dir is None:
        working_dir = Path(__file__).parent.parent.parent

    # Generate trace ID to correlate all judge interactions
    trace_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    results = {
        "timestamp": timestamp,
        "analysis_path": str(analysis_path),
        "model": model,
        "trace_id": trace_id,
        "judges": {},
        "summary": {},
        "programmatic_input": programmatic_input.to_dict() if programmatic_input else None,
    }

    judge_classes = {
        "size_accuracy": SizeAccuracyJudge,
        "threshold_quality": ThresholdQualityJudge,
        "actionability": ActionabilityJudge,
        "integration_fit": IntegrationFitJudge,
    }

    # Filter to specific judge if requested
    if specific_judge:
        if specific_judge not in judge_classes:
            print(f"Error: Unknown judge '{specific_judge}'", file=sys.stderr)
            print(f"Available: {list(judge_classes.keys())}", file=sys.stderr)
            sys.exit(1)
        judge_classes = {specific_judge: judge_classes[specific_judge]}

    total_weighted_score = 0.0
    total_weight = 0.0

    for name, judge_class in judge_classes.items():
        print(f"Running {name} judge...", file=sys.stderr)

        judge = judge_class(
            model=model,
            timeout=timeout,
            analysis_path=analysis_path,
            working_dir=working_dir,
        )

        # Run ground truth assertions first
        assertions_passed, failures = judge.run_ground_truth_assertions()
        if not assertions_passed:
            print(f"  Ground truth assertions failed:", file=sys.stderr)
            for failure in failures[:5]:
                print(f"    - {failure}", file=sys.stderr)

        # Run LLM evaluation
        result = judge.evaluate()
        weight = JUDGES[name][1]

        results["judges"][name] = {
            "score": result.score,
            "confidence": result.confidence,
            "weight": weight,
            "weighted_score": result.score * weight,
            "reasoning": result.reasoning,
            "evidence_cited": result.evidence_cited,
            "recommendations": result.recommendations,
            "sub_scores": result.sub_scores,
            "assertions_passed": assertions_passed,
            "assertion_failures": failures if not assertions_passed else [],
        }

        total_weighted_score += result.score * weight
        total_weight += weight

        print(f"  Score: {result.score}/5 (weight: {weight:.0%})", file=sys.stderr)

    # Calculate final score
    final_score = total_weighted_score / total_weight if total_weight > 0 else 0
    final_score_5 = final_score  # Already on 1-5 scale

    if final_score_5 >= 4.0:
        verdict = "STRONG_PASS"
    elif final_score_5 >= 3.5:
        verdict = "PASS"
    elif final_score_5 >= 3.0:
        verdict = "WEAK_PASS"
    else:
        verdict = "FAIL"

    results["summary"] = {
        "total_judges": len(results["judges"]),
        "weighted_score": round(final_score_5, 2),
        "normalized_score": round(final_score_5 / 5.0, 2),  # 0-1 scale
        "grade": get_grade(final_score_5),
        "verdict": verdict,
        "avg_confidence": sum(j["confidence"] for j in results["judges"].values()) / len(results["judges"]) if results["judges"] else 0.0,
    }

    # Add uniform schema fields
    results["decision"] = verdict
    results["score"] = round(final_score_5, 2)
    results["dimensions"] = results["judges"]  # Alias for uniform schema

    return results


def get_grade(score: float) -> str:
    """Convert score to letter grade."""
    if score >= 4.5:
        return "A"
    elif score >= 4.0:
        return "A-"
    elif score >= 3.5:
        return "B+"
    elif score >= 3.0:
        return "B"
    elif score >= 2.5:
        return "B-"
    elif score >= 2.0:
        return "C"
    elif score >= 1.5:
        return "D"
    else:
        return "F"


def print_report(results: dict) -> None:
    """Print evaluation report to console."""
    print("\n" + "=" * 70)
    print("GIT-SIZER LLM EVALUATION REPORT")
    print("=" * 70)

    print(f"\nTimestamp: {results['timestamp']}")
    print(f"Analysis:  {results['analysis_path']}")
    print(f"Model:     {results['model']}")

    # Summary
    summary = results["summary"]
    print("\n" + "-" * 70)
    print("SUMMARY")
    print("-" * 70)
    print(f"  Weighted Score: {summary['weighted_score']}/5.0")
    print(f"  Grade:          {summary['grade']}")
    print(f"  Verdict:        {summary['verdict']}")

    # Individual judges
    print("\n" + "-" * 70)
    print("JUDGE RESULTS")
    print("-" * 70)

    for name, result in results["judges"].items():
        status = "PASS" if result["assertions_passed"] else "FAIL"
        print(f"\n  {name.upper()} (weight: {result['weight']:.0%})")
        print(f"    Score:      {result['score']}/5 (weighted: {result['weighted_score']:.2f})")
        print(f"    Confidence: {result['confidence']:.1%}")
        print(f"    Assertions: {status}")

        if result.get("sub_scores"):
            print(f"    Sub-scores:")
            for sub_name, sub_score in result["sub_scores"].items():
                print(f"      - {sub_name}: {sub_score}/5")

        if result.get("reasoning"):
            reasoning = result["reasoning"][:200]
            if len(result["reasoning"]) > 200:
                reasoning += "..."
            print(f"    Reasoning: {reasoning}")

    # Final verdict
    print("\n" + "=" * 70)
    print(f"FINAL VERDICT: {summary['verdict']} ({summary['weighted_score']}/5.0, Grade: {summary['grade']})")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Run LLM judges for git-sizer evaluation"
    )
    parser.add_argument(
        "analysis_path",
        help="Path to analysis JSON file (or directory containing output.json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output path for results JSON",
    )
    parser.add_argument(
        "--model",
        default="opus-4.5",
        choices=["opus", "opus-4.5", "sonnet", "haiku"],
        help="Claude model to use (default: opus-4.5)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout per judge in seconds (default: 120)",
    )
    parser.add_argument(
        "--judge",
        help="Run specific judge only",
        choices=["size_accuracy", "threshold_quality", "actionability", "integration_fit"],
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON only (no console output)",
    )
    parser.add_argument(
        "--programmatic-results",
        type=Path,
        help="Path to programmatic evaluation JSON (evaluation_report.json)",
    )

    args = parser.parse_args()

    # Validate paths
    analysis_path = Path(args.analysis_path)

    # If directory given, keep as directory (load_analysis will aggregate subdirectories)
    # Only check for output.json if it's a file path that doesn't exist
    if not analysis_path.exists():
        print(f"Error: Analysis path not found: {analysis_path}", file=sys.stderr)
        sys.exit(1)

    # Load programmatic results if provided
    programmatic_input = None
    if args.programmatic_results and args.programmatic_results.exists():
        prog_data = json.loads(args.programmatic_results.read_text())
        summary = prog_data.get("summary", {})
        programmatic_input = ProgrammaticInput(
            file=str(args.programmatic_results),
            decision=prog_data.get("decision", "UNKNOWN"),
            score=prog_data.get("score", 0.0),
            checks_passed=summary.get("passed", 0),
            checks_failed=summary.get("failed", 0),
        )

    # Run judges
    results = run_all_judges(
        analysis_path=analysis_path,
        model=args.model,
        timeout=args.timeout,
        specific_judge=args.judge,
        programmatic_input=programmatic_input,
    )

    # Output
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_report(results)

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(results, indent=2, fp=f)
        if not args.json:
            print(f"Results saved to: {output_path}")

    # Exit with appropriate code
    verdict = results["summary"]["verdict"]
    sys.exit(0 if verdict in ("STRONG_PASS", "PASS", "WEAK_PASS") else 1)


if __name__ == "__main__":
    main()
