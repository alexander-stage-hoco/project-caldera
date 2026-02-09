"""LLM judges for coverage-ingest evaluation."""

from .base import BaseJudge, JudgeResult
from .risk_tier_quality import RiskTierQualityJudge
from .gap_actionability import GapActionabilityJudge
from .cross_format_consistency import CrossFormatConsistencyJudge

__all__ = [
    "BaseJudge",
    "JudgeResult",
    "RiskTierQualityJudge",
    "GapActionabilityJudge",
    "CrossFormatConsistencyJudge",
]

# Judge registry with weights
JUDGES = {
    "risk_tier_quality": (RiskTierQualityJudge, 0.35),
    "gap_actionability": (GapActionabilityJudge, 0.35),
    "cross_format_consistency": (CrossFormatConsistencyJudge, 0.30),
}
