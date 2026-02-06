"""LLM judges for git-fame evaluation."""

from __future__ import annotations

from .base import BaseJudge, JudgeResult
from .authorship_quality import AuthorshipQualityJudge
from .bus_factor_accuracy import BusFactorAccuracyJudge
from .concentration_metrics import ConcentrationMetricsJudge
from .evidence_quality import EvidenceQualityJudge
from .integration_readiness import IntegrationReadinessJudge
from .output_completeness import OutputCompletenessJudge

__all__ = [
    "BaseJudge",
    "JudgeResult",
    "AuthorshipQualityJudge",
    "BusFactorAccuracyJudge",
    "ConcentrationMetricsJudge",
    "EvidenceQualityJudge",
    "IntegrationReadinessJudge",
    "OutputCompletenessJudge",
]

# Registry of all judges for orchestrator
# Format: {dimension_name: (JudgeClass, weight)}
JUDGES = {
    "authorship_quality": (AuthorshipQualityJudge, 0.25),
    "bus_factor_accuracy": (BusFactorAccuracyJudge, 0.20),
    "concentration_metrics": (ConcentrationMetricsJudge, 0.20),
    "evidence_quality": (EvidenceQualityJudge, 0.15),
    "integration_readiness": (IntegrationReadinessJudge, 0.10),
    "output_completeness": (OutputCompletenessJudge, 0.10),
}
