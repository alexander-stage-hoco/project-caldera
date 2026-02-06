"""LLM judges for DependenSee evaluation."""

from __future__ import annotations

from .base import BaseJudge, JudgeResult
from .project_detection import ProjectDetectionJudge
from .dependency_accuracy import DependencyAccuracyJudge
from .graph_quality import GraphQualityJudge
from .circular_detection import CircularDetectionJudge

__all__ = [
    "BaseJudge",
    "JudgeResult",
    "ProjectDetectionJudge",
    "DependencyAccuracyJudge",
    "GraphQualityJudge",
    "CircularDetectionJudge",
]

# Registry of all judges for orchestrator
JUDGES = [
    ProjectDetectionJudge,
    DependencyAccuracyJudge,
    GraphQualityJudge,
    CircularDetectionJudge,
]
