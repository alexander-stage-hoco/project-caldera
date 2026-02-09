"""LLM judges for coverage-ingest evaluation."""

from .base import BaseJudge, JudgeResult
from .risk_tier_quality import RiskTierQualityJudge
from .gap_actionability import GapActionabilityJudge
from .cross_format_consistency import CrossFormatConsistencyJudge
from .parser_accuracy import ParserAccuracyJudge

__all__ = [
    "BaseJudge",
    "JudgeResult",
    "RiskTierQualityJudge",
    "GapActionabilityJudge",
    "CrossFormatConsistencyJudge",
    "ParserAccuracyJudge",
]

# Judge registry with weights
JUDGES = {
    "risk_tier_quality": (RiskTierQualityJudge, 0.25),
    "gap_actionability": (GapActionabilityJudge, 0.25),
    "cross_format_consistency": (CrossFormatConsistencyJudge, 0.25),
    "parser_accuracy": (ParserAccuracyJudge, 0.25),
}
