"""
LLM judges for evaluating Insights reports.

Four judges with different focuses:
- ClarityJudge: Report clarity and presentation (30% weight)
- ActionabilityJudge: Actionability of findings (40% weight)
- AccuracyJudge: Content accuracy and consistency (30% weight)
- InsightQualityJudge: Top insight extraction and prioritization (50% weight, optional)
"""

from .base import BaseJudge, JudgeResult
from .clarity import ClarityJudge
from .actionability import ActionabilityJudge
from .accuracy import AccuracyJudge
from .insight_quality import InsightQualityJudge, InsightQualityResult

__all__ = [
    "BaseJudge",
    "JudgeResult",
    "ClarityJudge",
    "ActionabilityJudge",
    "AccuracyJudge",
    "InsightQualityJudge",
    "InsightQualityResult",
]
