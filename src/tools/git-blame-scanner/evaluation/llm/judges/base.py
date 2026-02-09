"""Base judge class for git-blame-scanner.

This module provides a tool-specific BaseJudge that extends the shared
BaseJudge implementation with git-blame-scanner-specific helpers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shared.evaluation.base_judge import BaseJudge as SharedBaseJudge
from shared.evaluation.base_judge import JudgeResult
from shared.output_management import unwrap_envelope


class BaseJudge(SharedBaseJudge):
    """Base class for git-blame-scanner LLM judges.

    Provides git-blame-scanner-specific helper methods for extracting
    and validating file-level authorship data.
    """

    # Add synthetic patterns specific to git-blame-scanner
    SYNTHETIC_PATTERNS = SharedBaseJudge.SYNTHETIC_PATTERNS | {
        "single-author", "balanced", "concentrated", "high-churn",
    }

    def __init__(
        self,
        model: str = "opus-4.5",
        timeout: int = 120,
        working_dir: Path | None = None,
        output_dir: Path | None = None,
        ground_truth_dir: Path | None = None,
        use_llm: bool = True,
        trace_id: str | None = None,
        enable_observability: bool = True,
        evaluation_mode: str | None = None,
    ):
        """Initialize the git-blame-scanner judge.

        Args:
            model: Model name ("sonnet", "opus", "opus-4.5", "haiku")
            timeout: Timeout in seconds for LLM invocation
            working_dir: Working directory for the tool
            output_dir: Directory containing analysis output files
            ground_truth_dir: Directory containing ground truth files
            use_llm: Whether to use LLM evaluation (False for heuristic-only)
            trace_id: Correlation ID for linking all judges in one evaluation run
            enable_observability: Whether to log LLM interactions
            evaluation_mode: Evaluation mode ("synthetic", "real_world", or None)
        """
        if working_dir is None:
            working_dir = Path(__file__).parent.parent.parent.parent

        if ground_truth_dir is None:
            ground_truth_dir = working_dir / "evaluation" / "ground-truth"

        super().__init__(
            model=model,
            timeout=timeout,
            working_dir=working_dir,
            output_dir=output_dir,
            ground_truth_dir=ground_truth_dir,
            use_llm=use_llm,
            trace_id=trace_id,
            enable_observability=enable_observability,
            evaluation_mode=evaluation_mode,
        )

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
        # Use shared unwrap_envelope helper
        inner = unwrap_envelope(analysis)
        if "files" in inner:
            return inner["files"]
        if "results" in inner and isinstance(inner["results"], dict):
            return inner["results"].get("files", [])
        return []

    @staticmethod
    def extract_authors(analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract authors list from analysis data.

        Args:
            analysis: Analysis data dictionary

        Returns:
            List of author dictionaries
        """
        # Use shared unwrap_envelope helper
        inner = unwrap_envelope(analysis)
        if "authors" in inner:
            return inner["authors"]
        if "results" in inner and isinstance(inner["results"], dict):
            return inner["results"].get("authors", [])
        return []

    @staticmethod
    def extract_summary(analysis: dict[str, Any]) -> dict[str, Any]:
        """Extract summary dict from analysis data.

        Args:
            analysis: Analysis data dictionary

        Returns:
            Summary dictionary
        """
        # Use shared unwrap_envelope helper
        inner = unwrap_envelope(analysis)
        if "summary" in inner:
            return inner["summary"]
        if "results" in inner and isinstance(inner["results"], dict):
            return inner["results"].get("summary", {})
        return {}


__all__ = ["BaseJudge", "JudgeResult"]
