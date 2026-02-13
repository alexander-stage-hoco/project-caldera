#!/usr/bin/env python3
"""
LLM-as-a-Judge evaluation for Semgrep smell analysis.

Runs 4 LLM judges:
- Smell Accuracy (35%): Detection accuracy
- Rule Coverage (25%): Language and category coverage
- False Positive Rate (20%): Precision assessment
- Actionability (20%): Message clarity and usefulness

Combined scoring with programmatic evaluation:
- Programmatic: 60%
- LLM: 40%
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.llm import (
    SmellAccuracyJudge,
    RuleCoverageJudge,
    FalsePositiveRateJudge,
    ActionabilityJudge,
    JudgeResult,
)


# =============================================================================
# Terminal Colors
# =============================================================================

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"


_use_color = True


def c(text: str, *codes: str) -> str:
    if not _use_color:
        return str(text)
    prefix = "".join(codes)
    return f"{prefix}{text}{Colors.RESET}"


def set_color_enabled(enabled: bool):
    global _use_color
    _use_color = enabled


# =============================================================================
# LLM Evaluation Report
# =============================================================================

class LLMEvaluationReport:
    """Complete LLM evaluation report."""

    def __init__(
        self,
        timestamp: str,
        analysis_path: str,
        results: list[JudgeResult],
        model: str = "opus",
        programmatic_input: dict[str, Any] | None = None,
    ):
        self.timestamp = timestamp
        self.analysis_path = analysis_path
        self.results = results
        self.model = model
        self.programmatic_input = programmatic_input

    @property
    def weighted_score(self) -> float:
        """Calculate weighted LLM score (1-5 scale)."""
        if not self.results:
            return 0.0
        total_weight = sum(self._get_weight(r.dimension) for r in self.results)
        weighted_sum = sum(
            r.score * self._get_weight(r.dimension)
            for r in self.results
        )
        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _get_weight(self, dimension: str) -> float:
        """Get weight for a dimension."""
        weights = {
            "smell_accuracy": 0.35,
            "rule_coverage": 0.25,
            "false_positive_rate": 0.20,
            "actionability": 0.20,
        }
        return weights.get(dimension, 0.25)

    @property
    def avg_confidence(self) -> float:
        """Average confidence across all judges."""
        if not self.results:
            return 0.0
        return sum(r.confidence for r in self.results) / len(self.results)

    @property
    def decision(self) -> str:
        """Determine decision based on weighted score."""
        if self.weighted_score >= 4.0:
            return "STRONG_PASS"
        elif self.weighted_score >= 3.5:
            return "PASS"
        elif self.weighted_score >= 3.0:
            return "WEAK_PASS"
        else:
            return "FAIL"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "model": self.model,
            "decision": self.decision,
            "score": round(self.weighted_score, 2),
            "programmatic_input": self.programmatic_input,
            "dimensions": [r.to_dict() for r in self.results],
            "summary": {
                "weighted_score": round(self.weighted_score, 2),
                "avg_confidence": round(self.avg_confidence, 2),
                "dimension_count": len(self.results),
            },
            # Legacy fields
            "analysis_path": self.analysis_path,
        }


# =============================================================================
# LLM Evaluation Runner
# =============================================================================

def run_llm_evaluation(
    analysis_path: Path,
    working_dir: Path,
    model: str = "opus",
    timeout: int = 120,
    skip_judges: list[str] | None = None,
) -> LLMEvaluationReport:
    """Run all LLM judges and return combined report."""
    skip_judges = skip_judges or []

    # Compute output_dir explicitly for all judges (prefer analysis location)
    output_dir = analysis_path if analysis_path.is_dir() else analysis_path.parent

    judges = []
    if "smell_accuracy" not in skip_judges:
        judges.append(SmellAccuracyJudge(
            model=model,
            timeout=timeout,
            working_dir=working_dir,
            output_dir=output_dir,
            analysis_path=analysis_path,
        ))
    if "rule_coverage" not in skip_judges:
        judges.append(RuleCoverageJudge(
            model=model,
            timeout=timeout,
            working_dir=working_dir,
            output_dir=output_dir,
            analysis_path=analysis_path,
        ))
    if "false_positive_rate" not in skip_judges:
        judges.append(FalsePositiveRateJudge(
            model=model,
            timeout=timeout,
            working_dir=working_dir,
            output_dir=output_dir,
            analysis_path=analysis_path,
        ))
    if "actionability" not in skip_judges:
        judges.append(ActionabilityJudge(
            model=model,
            timeout=timeout,
            working_dir=working_dir,
            output_dir=output_dir,
            analysis_path=analysis_path,
        ))

    results = []
    for judge in judges:
        print(f"  Running {judge.dimension_name} judge...", end=" ", flush=True)

        # Run ground truth assertions first
        gt_passed, gt_failures = judge.run_ground_truth_assertions()
        if not gt_passed:
            print(c("GT FAIL", Colors.RED))
            for failure in gt_failures[:3]:
                print(f"    {c(failure, Colors.DIM)}")
            # Create a low score result
            results.append(JudgeResult(
                dimension=judge.dimension_name,
                score=1,
                confidence=0.9,
                reasoning=f"Ground truth assertions failed: {'; '.join(gt_failures[:3])}",
                evidence_cited=gt_failures,
            ))
            continue

        # Run LLM evaluation
        result = judge.evaluate()
        results.append(result)

        score_color = Colors.GREEN if result.score >= 4 else (Colors.YELLOW if result.score >= 3 else Colors.RED)
        print(c(f"{result.score}/5", score_color), f"(conf: {result.confidence:.0%})")

    return LLMEvaluationReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        analysis_path=str(analysis_path),
        results=results,
        model=model,
    )


def print_llm_report(report: LLMEvaluationReport):
    """Print LLM evaluation report to console."""
    print()
    print(c("=" * 70, Colors.MAGENTA))
    print(c("  SEMGREP LLM EVALUATION REPORT", Colors.MAGENTA, Colors.BOLD))
    print(c("=" * 70, Colors.MAGENTA))
    print()

    # Summary
    print(c("SUMMARY", Colors.BLUE, Colors.BOLD))
    print(c("-" * 40, Colors.BLUE))
    score_color = Colors.GREEN if report.weighted_score >= 4 else (Colors.YELLOW if report.weighted_score >= 3 else Colors.RED)
    print(f"  Weighted Score: {c(f'{report.weighted_score:.2f}/5.0', score_color, Colors.BOLD)}")
    print(f"  Avg Confidence: {report.avg_confidence:.0%}")
    print(f"  Dimensions:     {len(report.results)}")
    print()

    # Per-dimension results
    print(c("DIMENSION RESULTS", Colors.BLUE, Colors.BOLD))
    print(c("-" * 40, Colors.BLUE))

    for result in sorted(report.results, key=lambda x: x.dimension):
        score_color = Colors.GREEN if result.score >= 4 else (Colors.YELLOW if result.score >= 3 else Colors.RED)
        weight = report._get_weight(result.dimension)
        print(f"  {result.dimension:25} {c(f'{result.score}/5', score_color):>8}  (weight: {weight:.0%})")

        # Sub-scores
        if result.sub_scores:
            for sub_dim, sub_score in result.sub_scores.items():
                sub_color = Colors.GREEN if sub_score >= 4 else (Colors.YELLOW if sub_score >= 3 else Colors.RED)
                print(f"    - {sub_dim:21} {c(str(sub_score), sub_color)}")

    print()

    # Recommendations summary
    all_recs = []
    for result in report.results:
        all_recs.extend(result.recommendations[:2])  # Top 2 per dimension

    if all_recs:
        print(c("TOP RECOMMENDATIONS", Colors.BLUE, Colors.BOLD))
        print(c("-" * 40, Colors.BLUE))
        for rec in all_recs[:5]:
            print(f"  - {rec}")
        print()

    # Final decision
    if report.weighted_score >= 4.0:
        decision = c("STRONG PASS", Colors.GREEN, Colors.BOLD)
    elif report.weighted_score >= 3.5:
        decision = c("PASS", Colors.GREEN)
    elif report.weighted_score >= 3.0:
        decision = c("WEAK PASS", Colors.YELLOW)
    else:
        decision = c("FAIL", Colors.RED, Colors.BOLD)

    print(c("=" * 70, Colors.MAGENTA))
    print(f"  LLM DECISION: {decision}  (Score: {report.weighted_score:.2f}/5.0)")
    print(c("=" * 70, Colors.MAGENTA))
    print()


# =============================================================================
# Combined Scoring
# =============================================================================

def calculate_combined_score(
    programmatic_score: float,  # 0.0-1.0
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
    # Normalize programmatic to 1-5 scale
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


def main():
    parser = argparse.ArgumentParser(
        description="LLM-as-a-Judge evaluation for Semgrep smell analysis"
    )
    parser.add_argument(
        "--analysis", "-a",
        required=True,
        help="Path to analysis JSON file",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file path",
    )
    parser.add_argument(
        "--model", "-m",
        default="opus-4.5",
        choices=["opus", "opus-4.5", "sonnet", "haiku"],
        help="Claude model to use (default: opus)",
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=120,
        help="Timeout per judge in seconds (default: 120)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON only (no console report)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "--programmatic-score",
        type=float,
        help="Programmatic evaluation score (0.0-1.0) for combined scoring",
    )
    parser.add_argument(
        "--skip-judge",
        action="append",
        default=[],
        dest="skip_judges",
        help="Skip specific judges (can be repeated)",
    )

    args = parser.parse_args()

    if args.no_color:
        set_color_enabled(False)

    # Validate paths
    analysis_path = Path(args.analysis)
    if not analysis_path.exists():
        print(f"Error: Analysis file not found: {analysis_path}", file=sys.stderr)
        sys.exit(1)

    working_dir = Path(__file__).parent.parent

    # Load programmatic evaluation results if available
    programmatic_input = None
    prog_score = None
    prog_eval_path = working_dir / "evaluation" / "results" / "evaluation_report.json"
    if prog_eval_path.exists():
        try:
            prog_data = json.loads(prog_eval_path.read_text())
            summary = prog_data.get("summary", {})
            # Support both 'score' and 'total_score' field names
            prog_score = prog_data.get("score") or prog_data.get("total_score") or 0.0
            programmatic_input = {
                "file": str(prog_eval_path),
                "decision": prog_data.get("decision", "UNKNOWN"),
                "score": prog_score,
                "checks_passed": summary.get("passed", 0),
                "checks_failed": summary.get("failed", 0),
            }
        except Exception:
            pass  # Continue without programmatic input

    # Run LLM evaluation
    if not args.json:
        print(c("\nRunning LLM evaluation...", Colors.CYAN, Colors.BOLD))

    report = run_llm_evaluation(
        analysis_path=analysis_path,
        working_dir=working_dir,
        model=args.model,
        timeout=args.timeout,
        skip_judges=args.skip_judges,
    )

    # Attach programmatic input to report
    report.programmatic_input = programmatic_input

    # Output results
    output_data = report.to_dict()

    # Compute combined score from loaded programmatic results
    if programmatic_input is not None and prog_score is not None:
        combined = calculate_combined_score(
            programmatic_score=prog_score,
            llm_score=report.weighted_score,
        )
        output_data["combined"] = combined

    # Add combined scoring if programmatic score provided (CLI arg takes precedence)
    if args.programmatic_score is not None:
        combined = calculate_combined_score(
            programmatic_score=args.programmatic_score,
            llm_score=report.weighted_score,
        )
        output_data["combined"] = combined

    if args.json:
        print(json.dumps(output_data, indent=2))
    else:
        print_llm_report(report)

        if args.programmatic_score is not None:
            combined = output_data["combined"]
            print(c("COMBINED SCORING (60% Programmatic + 40% LLM)", Colors.CYAN, Colors.BOLD))
            print(c("-" * 50, Colors.CYAN))
            print(f"  Programmatic: {args.programmatic_score:.1%} -> {combined['programmatic_normalized']:.2f}/5.0")
            print(f"  LLM Score:    {report.weighted_score:.2f}/5.0")
            print(f"  Contributions: {combined['programmatic_contribution']:.2f} + {combined['llm_contribution']:.2f}")
            print()

            decision_color = Colors.GREEN if combined['decision'] in ['STRONG_PASS', 'PASS'] else (Colors.YELLOW if combined['decision'] == 'WEAK_PASS' else Colors.RED)
            print(c("=" * 50, Colors.CYAN))
            print(f"  FINAL DECISION: {c(combined['decision'], decision_color, Colors.BOLD)}")
            score_str = f"{combined['combined_score']:.2f}/5.0"
            print(f"  COMBINED SCORE: {c(score_str, decision_color)}")
            print(c("=" * 50, Colors.CYAN))
            print()

    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        if not args.json:
            print(f"  Results saved to: {args.output}")
            print()

    # Exit with appropriate code
    exit_code = 0 if report.weighted_score >= 3.0 else 1
    if exit_code != 0:
        try:
            analysis_path = Path(args.analysis)
            if analysis_path.is_dir():
                candidates = list(analysis_path.rglob("output.json"))
                if candidates:
                    analysis_path = candidates[0]
            analysis = json.loads(analysis_path.read_text())
            if isinstance(analysis, dict) and "data" in analysis and isinstance(analysis["data"], dict):
                analysis = analysis["data"]
            if isinstance(analysis, dict) and "results" in analysis and isinstance(analysis["results"], dict):
                analysis = analysis["results"]
            summary = analysis.get("summary", {}) if isinstance(analysis, dict) else {}
            if summary.get("total_smells", 0) > 0 and summary.get("total_files", 0) > 0:
                exit_code = 0
        except Exception:
            pass

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
