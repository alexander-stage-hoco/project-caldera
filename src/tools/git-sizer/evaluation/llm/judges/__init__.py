"""LLM judges for git-sizer evaluation."""

from .base import BaseJudge, JudgeResult
from .size_accuracy import SizeAccuracyJudge
from .threshold_quality import ThresholdQualityJudge
from .actionability import ActionabilityJudge
from .integration_fit import IntegrationFitJudge

__all__ = [
    "BaseJudge",
    "JudgeResult",
    "SizeAccuracyJudge",
    "ThresholdQualityJudge",
    "ActionabilityJudge",
    "IntegrationFitJudge",
]

# Judge registry with weights
JUDGES = {
    "size_accuracy": (SizeAccuracyJudge, 0.35),
    "threshold_quality": (ThresholdQualityJudge, 0.25),
    "actionability": (ActionabilityJudge, 0.20),
    "integration_fit": (IntegrationFitJudge, 0.20),
}
