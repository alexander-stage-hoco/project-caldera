"""Base judge class for LLM-as-a-Judge evaluation of SonarQube analysis.

This module re-exports the shared BaseJudge and JudgeResult classes,
and provides SonarQube-specific extensions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Import from shared module - eliminates duplicate code
from shared.evaluation import BaseJudge as SharedBaseJudge, JudgeResult

# Re-export JudgeResult for backwards compatibility
__all__ = ["BaseJudge", "JudgeResult"]


class BaseJudge(SharedBaseJudge):
    """SonarQube-specific base judge with analysis data handling.

    Extends the shared BaseJudge with SonarQube-specific functionality:
    - analysis_path parameter for specifying the analysis JSON file
    - analysis_data property for lazy-loading the analysis
    - analysis_results property for unwrapping Caldera envelope format
    """

    def __init__(
        self,
        model: str = "opus-4.5",
        timeout: int = 120,
        working_dir: Path | None = None,
        analysis_path: Path | None = None,
        output_dir: Path | None = None,
        trace_id: str | None = None,
        enable_observability: bool = True,
        evaluation_mode: str | None = None,
    ):
        """Initialize the SonarQube judge.

        Args:
            model: Model name ("sonnet", "opus", "haiku") or full API ID
            timeout: Timeout in seconds for LLM invocation
            working_dir: Working directory for the tool
            analysis_path: Path to the sonarqube analysis JSON file
            output_dir: Directory containing analysis output files
            trace_id: Correlation ID for linking all judges in one evaluation run
            enable_observability: Whether to log LLM interactions (default True)
            evaluation_mode: Evaluation mode ("synthetic", "real_world", or None for auto-detect)
        """
        super().__init__(
            model=model,
            timeout=timeout,
            working_dir=working_dir,
            output_dir=output_dir or (working_dir or Path.cwd()) / "evaluation" / "llm" / "results",
            trace_id=trace_id,
            enable_observability=enable_observability,
            evaluation_mode=evaluation_mode,
        )
        self.analysis_path = analysis_path
        self._analysis_data: dict | None = None

    @property
    def analysis_data(self) -> dict:
        """Load and cache analysis data."""
        if self._analysis_data is None:
            if self.analysis_path is None:
                raise ValueError("analysis_path not set")
            with open(self.analysis_path) as f:
                self._analysis_data = json.load(f)
        return self._analysis_data

    @property
    def analysis_results(self) -> dict:
        """Return the normalized results payload.

        Handles both Caldera envelope format and legacy flat format.
        """
        data = self.analysis_data
        # Handle Caldera envelope format
        if "data" in data and "metadata" in data:
            inner = data["data"]
            return inner.get("results", inner)
        return data.get("results", data)

    @property
    def prompt_file(self) -> Path:
        """Path to the prompt template file."""
        return Path(__file__).parent.parent / "prompts" / f"{self.dimension_name.replace(' ', '_').lower()}.md"

    def _create_result(
        self,
        score: int,
        confidence: float,
        reasoning: str,
        evidence: list[str] | None = None,
        recommendations: list[str] | None = None,
        sub_scores: dict[str, int] | None = None,
    ) -> JudgeResult:
        """Create a JudgeResult with common fields."""
        return JudgeResult(
            dimension=self.dimension_name,
            score=score,
            confidence=confidence,
            reasoning=reasoning,
            evidence_cited=evidence or [],
            recommendations=recommendations or [],
            sub_scores=sub_scores or {},
        )
