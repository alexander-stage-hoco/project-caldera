"""Scoring logic for architecture review dimensions.

Converts lists of findings into dimension scores and overall advisory status.
"""

from __future__ import annotations

from models import DimensionResult, Finding


def score_dimension(findings: list[Finding]) -> int:
    """Score a dimension based on finding counts.

    Returns:
        Score 1-5 based on severity distribution:
        - 5 = 0 findings
        - 4 = 1-3 info, 0 warnings, 0 errors
        - 3 = 4+ info OR 1-3 warnings, 0 errors
        - 2 = 4+ warnings OR 1-2 errors
        - 1 = 3+ errors
    """
    errors = sum(1 for f in findings if f.severity == "error")
    warnings = sum(1 for f in findings if f.severity == "warning")
    infos = sum(1 for f in findings if f.severity == "info")

    if errors >= 3:
        return 1
    if errors >= 1 or warnings >= 4:
        return 2
    if warnings >= 1 or infos >= 4:
        return 3
    if infos >= 1:
        return 4
    return 5


def status_from_score(score: int) -> str:
    """Derive dimension status from score.

    Returns:
        'pass' for score >= 4, 'warn' for 3, 'fail' for <= 2.
    """
    if score >= 4:
        return "pass"
    if score == 3:
        return "warn"
    return "fail"


def compute_overall(dimensions: list[DimensionResult]) -> tuple[float, str]:
    """Compute weighted overall score and advisory status.

    Returns:
        Tuple of (weighted_score, advisory_status).
    """
    if not dimensions:
        return 5.0, "STRONG_PASS"

    total_weight = sum(d.weight for d in dimensions)
    if total_weight == 0:
        total_weight = 1.0

    weighted_sum = sum(d.score * d.weight for d in dimensions)
    score = round(weighted_sum / total_weight, 2)

    return score, advisory_status(score)


def advisory_status(score: float) -> str:
    """Map a numeric score to an advisory status.

    Returns:
        STRONG_PASS (>= 4.0), PASS (>= 3.5), WEAK_PASS (>= 3.0), NEEDS_WORK (< 3.0).
    """
    if score >= 4.0:
        return "STRONG_PASS"
    if score >= 3.5:
        return "PASS"
    if score >= 3.0:
        return "WEAK_PASS"
    return "NEEDS_WORK"
