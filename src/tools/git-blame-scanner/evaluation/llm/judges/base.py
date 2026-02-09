"""Base judge class for git-blame-scanner.

This module provides a tool-specific BaseJudge that extends the shared
BaseJudge implementation with git-blame-scanner-specific helpers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shared.evaluation.base_judge import BaseJudge as SharedBaseJudge
from shared.evaluation.base_judge import JudgeResult


class BaseJudge(SharedBaseJudge):
    """Base class for git-blame-scanner LLM judges.

    Provides git-blame-scanner-specific helper methods for extracting
    and validating file-level authorship data.
    """

    # Add synthetic patterns specific to git-blame-scanner
    SYNTHETIC_PATTERNS = SharedBaseJudge.SYNTHETIC_PATTERNS | {
        "single-author", "balanced", "concentrated", "high-churn",
    }

    def load_all_analysis_results(self) -> dict[str, Any]:
        """Load all analysis results, handling git-blame-scanner's output format.

        Returns:
            Dictionary keyed by repo name to analysis data.
        """
        return self.load_analysis_results()

    @staticmethod
    def extract_files(analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract files list from analysis data.

        Args:
            analysis: Analysis data dictionary

        Returns:
            List of file dictionaries
        """
        # Try various formats
        if "files" in analysis:
            return analysis["files"]
        if "results" in analysis and isinstance(analysis["results"], dict):
            return analysis["results"].get("files", [])
        if "data" in analysis and isinstance(analysis["data"], dict):
            return analysis["data"].get("files", [])
        return []

    @staticmethod
    def extract_authors(analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract authors list from analysis data.

        Args:
            analysis: Analysis data dictionary

        Returns:
            List of author dictionaries
        """
        # Try various formats
        if "authors" in analysis:
            return analysis["authors"]
        if "results" in analysis and isinstance(analysis["results"], dict):
            return analysis["results"].get("authors", [])
        if "data" in analysis and isinstance(analysis["data"], dict):
            return analysis["data"].get("authors", [])
        return []

    @staticmethod
    def extract_summary(analysis: dict[str, Any]) -> dict[str, Any]:
        """Extract summary dict from analysis data.

        Args:
            analysis: Analysis data dictionary

        Returns:
            Summary dictionary
        """
        # Try various formats
        if "summary" in analysis:
            return analysis["summary"]
        if "results" in analysis and isinstance(analysis["results"], dict):
            return analysis["results"].get("summary", {})
        if "data" in analysis and isinstance(analysis["data"], dict):
            return analysis["data"].get("summary", {})
        return {}


__all__ = ["BaseJudge", "JudgeResult"]
