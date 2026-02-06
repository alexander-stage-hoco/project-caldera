"""Evaluation checks for git-fame."""

from __future__ import annotations

from .output_quality import OutputQualityChecks
from .authorship_accuracy import AuthorshipAccuracyChecks
from .reliability import ReliabilityChecks
from .performance import PerformanceChecks
from .integration_fit import IntegrationFitChecks
from .installation import InstallationChecks

__all__ = [
    "OutputQualityChecks",
    "AuthorshipAccuracyChecks",
    "ReliabilityChecks",
    "PerformanceChecks",
    "IntegrationFitChecks",
    "InstallationChecks",
]
