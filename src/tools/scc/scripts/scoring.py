"""Scoring module for scc PoC evaluation."""

from typing import List, Dict
from scripts.checks import CheckResult, DimensionResult


# Scoring tables: maps number of passed checks to score (1-5)
SCORING_TABLES: Dict[str, Dict[int, int]] = {
    "output_quality": {8: 5, 7: 4, 5: 3, 3: 2, 0: 1},
    "integration_fit": {6: 5, 5: 4, 4: 3, 2: 2, 0: 1},
    "reliability": {8: 5, 7: 4, 5: 3, 3: 2, 0: 1},
    "performance": {4: 5, 3: 4, 2: 3, 1: 2, 0: 1},
    "installation": {4: 5, 3: 4, 2: 3, 1: 2, 0: 1},
    "coverage": {9: 5, 8: 4, 6: 3, 4: 2, 0: 1},
    "license": {3: 5, 2: 4, 1: 3, 0: 2},
    # New dimensions for extended analysis
    "per_file": {6: 5, 5: 4, 4: 3, 2: 2, 0: 1},
    "directory_analysis": {5: 5, 4: 4, 3: 3, 2: 2, 0: 1},
    "cocomo": {3: 5, 2: 4, 1: 3, 0: 2},
}

# Dimension weights (core evaluation = 70%, extended = 30%)
DIMENSION_WEIGHTS: Dict[str, float] = {
    # Core dimensions (70%)
    "output_quality": 0.20,
    "integration_fit": 0.15,
    "reliability": 0.10,
    "performance": 0.10,
    "installation": 0.05,
    "coverage": 0.05,
    "license": 0.05,
    # Extended analysis dimensions (30%)
    "per_file": 0.10,
    "directory_analysis": 0.10,
    "cocomo": 0.10,
}

# Decision thresholds
DECISION_THRESHOLDS = {
    "STRONG_PASS": 4.0,
    "PASS": 3.5,
    "WEAK_PASS": 3.0,
    "FAIL": 0.0
}


def compute_dimension_score(checks: List[CheckResult], dimension: str) -> int:
    """Compute 1-5 score from check results using dimension-specific scoring table."""
    passed_count = sum(1 for c in checks if c.passed)
    scoring_table = SCORING_TABLES.get(dimension, {0: 1})

    # Find the highest threshold that the passed_count meets
    for threshold in sorted(scoring_table.keys(), reverse=True):
        if passed_count >= threshold:
            return scoring_table[threshold]

    return 1  # Default minimum score


def compute_dimension_result(checks: List[CheckResult], dimension: str) -> DimensionResult:
    """Compute full dimension result including score and weighted score."""
    weight = DIMENSION_WEIGHTS.get(dimension, 0.0)
    score = compute_dimension_score(checks, dimension)
    weighted_score = score * weight

    return DimensionResult(
        dimension=dimension,
        weight=weight,
        checks=checks,
        score=score,
        weighted_score=weighted_score
    )


def compute_total_score(dimensions: List[DimensionResult]) -> float:
    """Compute weighted total score."""
    return sum(d.weighted_score for d in dimensions)


def determine_decision(total_score: float) -> str:
    """Determine pass/fail decision based on total score."""
    if total_score >= DECISION_THRESHOLDS["STRONG_PASS"]:
        return "STRONG_PASS"
    elif total_score >= DECISION_THRESHOLDS["PASS"]:
        return "PASS"
    elif total_score >= DECISION_THRESHOLDS["WEAK_PASS"]:
        return "WEAK_PASS"
    else:
        return "FAIL"


def format_score_summary(dimensions: List[DimensionResult], total_score: float, decision: str) -> str:
    """Format a summary of the scoring results."""
    lines = [
        "## Scoring Summary",
        "",
        "| Dimension | Weight | Passed | Total | Score | Weighted |",
        "|-----------|--------|--------|-------|-------|----------|"
    ]

    for d in dimensions:
        lines.append(
            f"| {d.dimension.replace('_', ' ').title()} | {d.weight:.0%} | "
            f"{d.checks_passed} | {d.checks_total} | {d.score}/5 | {d.weighted_score:.2f} |"
        )

    lines.extend([
        f"| **TOTAL** | **100%** | | | | **{total_score:.2f}** |",
        "",
        f"**Decision: {decision}** ({total_score:.2f}/5.0)",
        ""
    ])

    return "\n".join(lines)
