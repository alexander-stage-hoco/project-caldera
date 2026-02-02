"""Base judge class for LLM-as-a-Judge evaluation of Gitleaks secret detection.

This module re-exports the shared BaseJudge and JudgeResult classes,
and provides Gitleaks-specific extensions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Import from shared module - eliminates duplicate code
from shared.evaluation import BaseJudge as SharedBaseJudge, JudgeResult

# Re-export JudgeResult for backwards compatibility
__all__ = ["BaseJudge", "JudgeResult"]


class BaseJudge(SharedBaseJudge):
    """Gitleaks-specific base judge for secret detection evaluation.

    Extends the shared BaseJudge with Gitleaks-specific functionality:
    - Multi-file analysis results loading
    - Legacy single file fallback support
    - Ground truth loading from evaluation/ground-truth directory

    Each judge evaluates a specific dimension of Gitleaks secret detection
    quality. Judges invoke Claude Code in headless mode with specialized prompts.
    """

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
        """Initialize the gitleaks judge.

        Args:
            model: Model name ("sonnet", "opus", "opus-4.5", "haiku")
            timeout: Timeout in seconds for LLM invocation
            working_dir: Working directory for the tool
            output_dir: Directory containing analysis output files
            ground_truth_dir: Directory containing ground truth files
            use_llm: Whether to use LLM evaluation (False for heuristic-only)
            trace_id: Correlation ID for linking all judges in one evaluation run
            enable_observability: Whether to log LLM interactions
            evaluation_mode: Evaluation mode ("synthetic", "real_world", or None for auto)
        """
        # Set gitleaks-specific defaults
        if working_dir is None:
            working_dir = Path(__file__).parent.parent.parent.parent
        if output_dir is None:
            output_dir = working_dir / "outputs" / "runs"
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

    @property
    def prompt_file(self) -> Path:
        """Path to the prompt template file.

        Overrides parent to use gitleaks-specific prompt location.
        """
        return Path(__file__).parent.parent / "prompts" / f"{self.dimension_name}.md"

    def load_all_analysis_results(self) -> dict[str, Any]:
        """Load all analysis JSON files from output_dir.

        Returns dict keyed by repo name (filename stem) -> analysis data.
        This method handles the gitleaks-specific envelope format.
        """
        return self.load_analysis_results()

    def load_all_ground_truth(self) -> dict[str, Any]:
        """Load all ground truth files from ground_truth_dir.

        Returns dict keyed by repo name -> ground truth data.
        Aggregates evidence from multiple scenarios.
        """
        return self.load_ground_truth()
