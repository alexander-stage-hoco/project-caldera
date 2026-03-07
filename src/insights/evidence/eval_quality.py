"""Programmatic quality checks for LLM judge evaluation output.

Mirrors the ``check_warning_budget()`` pattern from ``collector.py``:
YAML-driven thresholds with hardcoded fallbacks, frozen dataclass results,
called in ``builder.py`` after ``evaluate_all()`` returns.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .entities import EvaluationScore, EvidenceRegistry


# ---------------------------------------------------------------------------
# Result entities
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvalQualityFlag:
    """Result of a single quality check."""

    check: str
    passed: bool
    metric: float
    threshold: float
    message: str


@dataclass(frozen=True)
class EvalQualityReport:
    """Aggregate result of all quality checks."""

    passed: bool
    flags: tuple[EvalQualityFlag, ...]
    summary: dict[str, Any]


# ---------------------------------------------------------------------------
# Threshold loading (mirrors _load_warning_budget)
# ---------------------------------------------------------------------------

_DEFAULT_THRESHOLDS: dict[str, float] = {
    "coverage": 0.7,
    "uniformity": 0.8,
    "reasoning_presence": 0.8,
    "contradictions": 0,
    "confidence_calibration": 0.6,
    "avg_score_min": 2.0,
    "avg_score_max": 4.5,
}


def _load_thresholds() -> dict[str, float]:
    """Load quality thresholds from ``eval_quality_thresholds.yml``."""
    path = Path(__file__).resolve().parent.parent / "eval_quality_thresholds.yml"
    try:
        import yaml

        data = yaml.safe_load(path.read_text())
        return {**_DEFAULT_THRESHOLDS, **data.get("thresholds", {})}
    except Exception:
        return dict(_DEFAULT_THRESHOLDS)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def _check_coverage(
    scores: list[EvaluationScore],
    registry: EvidenceRegistry,
    threshold: float,
) -> EvalQualityFlag:
    """Check that enough expected entities received scores."""
    # Expected: non-empty evidence categories + total claims + total risks
    categories_with_evidence = {
        e.category for e in registry.evidence
    }
    expected = len(categories_with_evidence) + len(registry.claims) + len(registry.risks)
    actual = len(scores)
    metric = actual / expected if expected > 0 else 1.0
    passed = metric >= threshold
    return EvalQualityFlag(
        check="coverage",
        passed=passed,
        metric=round(metric, 3),
        threshold=threshold,
        message=(
            f"Coverage {metric:.0%} ({actual}/{expected} entities evaluated)"
            if passed
            else f"Low coverage: only {metric:.0%} ({actual}/{expected}) entities evaluated (need >= {threshold:.0%})"
        ),
    )


def _check_uniformity(
    scores: list[EvaluationScore],
    threshold: float,
) -> EvalQualityFlag:
    """Flag if too many scores share the same value (rubber-stamping)."""
    if not scores:
        return EvalQualityFlag(
            check="uniformity", passed=True, metric=0.0, threshold=threshold,
            message="No scores to check",
        )
    counts = Counter(s.score for s in scores)
    most_common_count = counts.most_common(1)[0][1]
    metric = most_common_count / len(scores)
    passed = metric <= threshold
    return EvalQualityFlag(
        check="uniformity",
        passed=passed,
        metric=round(metric, 3),
        threshold=threshold,
        message=(
            f"Score uniformity {metric:.0%} (within tolerance)"
            if passed
            else f"Rubber-stamping detected: {metric:.0%} of scores share the same value (max {threshold:.0%})"
        ),
    )


def _check_reasoning_presence(
    scores: list[EvaluationScore],
    threshold: float,
) -> EvalQualityFlag:
    """Check that enough scores include non-empty reasoning."""
    if not scores:
        return EvalQualityFlag(
            check="reasoning_presence", passed=True, metric=1.0, threshold=threshold,
            message="No scores to check",
        )
    with_reasoning = sum(1 for s in scores if s.reasoning and s.reasoning.strip())
    metric = with_reasoning / len(scores)
    passed = metric >= threshold
    return EvalQualityFlag(
        check="reasoning_presence",
        passed=passed,
        metric=round(metric, 3),
        threshold=threshold,
        message=(
            f"Reasoning present in {metric:.0%} of scores"
            if passed
            else f"Missing reasoning: only {metric:.0%} have reasoning (need >= {threshold:.0%})"
        ),
    )


def _check_score_severity_contradictions(
    registry: EvidenceRegistry,
    threshold: float,
) -> EvalQualityFlag:
    """Flag critical/high risks scored 5/5 (incoherent) or low risks scored 1/5 (suspicious)."""
    contradictions = 0
    for risk in registry.risks:
        evaluation = registry.evaluation_for(risk.risk_id)
        if not evaluation:
            continue
        if risk.severity in ("critical", "high") and evaluation.score == 1:
            contradictions += 1
        if risk.severity == "low" and evaluation.score == 5:
            contradictions += 1
    passed = contradictions <= threshold
    return EvalQualityFlag(
        check="contradictions",
        passed=passed,
        metric=float(contradictions),
        threshold=threshold,
        message=(
            "No score-severity contradictions"
            if passed
            else f"{contradictions} score-severity contradiction(s) found (max {int(threshold)})"
        ),
    )


def _check_confidence_calibration(
    scores: list[EvaluationScore],
    threshold: float,
) -> EvalQualityFlag:
    """Extreme scores (1 or 5) should have confidence >= threshold."""
    extreme = [s for s in scores if s.score in (1, 5)]
    if not extreme:
        return EvalQualityFlag(
            check="confidence_calibration", passed=True, metric=1.0,
            threshold=threshold, message="No extreme scores to check",
        )
    well_calibrated = sum(1 for s in extreme if s.confidence >= threshold)
    metric = well_calibrated / len(extreme)
    pass_rate = 0.8
    passed = metric >= pass_rate
    return EvalQualityFlag(
        check="confidence_calibration",
        passed=passed,
        metric=round(metric, 3),
        threshold=threshold,
        message=(
            f"Confidence calibration OK ({metric:.0%} of extreme scores >= {threshold})"
            if passed
            else f"Poor calibration: only {metric:.0%} of extreme scores have confidence >= {threshold}"
        ),
    )


def _check_avg_score_range(
    scores: list[EvaluationScore],
    min_avg: float,
    max_avg: float,
) -> EvalQualityFlag:
    """Average score should fall within a reasonable range."""
    if not scores:
        return EvalQualityFlag(
            check="avg_score_range", passed=True, metric=0.0,
            threshold=min_avg, message="No scores to check",
        )
    avg = sum(s.score for s in scores) / len(scores)
    passed = min_avg <= avg <= max_avg
    return EvalQualityFlag(
        check="avg_score_range",
        passed=passed,
        metric=round(avg, 3),
        threshold=min_avg,  # report the lower bound as the threshold
        message=(
            f"Average score {avg:.2f} (within {min_avg}-{max_avg})"
            if passed
            else f"Average score {avg:.2f} outside acceptable range [{min_avg}, {max_avg}]"
        ),
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def check_evaluation_quality(
    scores: list[EvaluationScore],
    registry: EvidenceRegistry,
) -> EvalQualityReport:
    """Run all quality checks on evaluation scores and return a report."""
    thresholds = _load_thresholds()

    flags: list[EvalQualityFlag] = [
        _check_coverage(scores, registry, thresholds["coverage"]),
        _check_uniformity(scores, thresholds["uniformity"]),
        _check_reasoning_presence(scores, thresholds["reasoning_presence"]),
        _check_score_severity_contradictions(registry, thresholds["contradictions"]),
        _check_confidence_calibration(scores, thresholds["confidence_calibration"]),
        _check_avg_score_range(scores, thresholds["avg_score_min"], thresholds["avg_score_max"]),
    ]

    summary = {f.check: f.metric for f in flags}
    all_passed = all(f.passed for f in flags)

    return EvalQualityReport(
        passed=all_passed,
        flags=tuple(flags),
        summary=summary,
    )
