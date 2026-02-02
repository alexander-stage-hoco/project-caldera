"""LLM-as-a-Judge evaluation for Gitleaks secret detection."""

from .judges.base import BaseJudge, JudgeResult
from .judges.detection_accuracy import DetectionAccuracyJudge
from .judges.false_positive import FalsePositiveJudge
from .judges.secret_coverage import SecretCoverageJudge
from .judges.severity_classification import SeverityClassificationJudge
from .orchestrator import LLMEvaluator, EvaluationResult, DimensionResult

__all__ = [
    "BaseJudge",
    "JudgeResult",
    "DetectionAccuracyJudge",
    "FalsePositiveJudge",
    "SecretCoverageJudge",
    "SeverityClassificationJudge",
    "LLMEvaluator",
    "EvaluationResult",
    "DimensionResult",
]
