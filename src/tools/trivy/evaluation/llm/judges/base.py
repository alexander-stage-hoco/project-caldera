"""Base judge class for Trivy LLM evaluation.

This module re-exports the shared BaseJudge and JudgeResult classes,
and provides Trivy-specific extensions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Import from shared module - eliminates duplicate code
from shared.evaluation import BaseJudge as SharedBaseJudge, JudgeResult
from shared.output_management import load_analysis_results, load_ground_truth

# Re-export JudgeResult for backwards compatibility
__all__ = ["BaseJudge", "JudgeResult"]


class BaseJudge(SharedBaseJudge):
    """Trivy-specific base judge for vulnerability detection evaluation.

    Extends the shared BaseJudge with Trivy-specific functionality:
    - Trivy-specific directory defaults
    - Custom prompt loading with string formatting
    """

    # Class-level attributes for legacy compatibility
    name: str = "base"

    def __init__(
        self,
        model: str = "opus-4.5",
        timeout: int = 120,
        working_dir: Path | None = None,
        output_dir: Path | None = None,
        trace_id: str | None = None,
        enable_observability: bool = True,
        evaluation_mode: str | None = None,
    ):
        """Initialize the Trivy judge.

        Args:
            model: Model name ("sonnet", "opus", "haiku") or full API ID
            timeout: Timeout in seconds for LLM invocation
            working_dir: Working directory for the tool
            output_dir: Directory containing analysis output files
            trace_id: Correlation ID for linking all judges in one evaluation run
            enable_observability: Whether to log LLM interactions (default True)
            evaluation_mode: Evaluation mode ("synthetic", "real_world", or None for auto-detect)
        """
        working_dir = working_dir or Path(__file__).parent.parent.parent.parent
        super().__init__(
            model=model,
            timeout=timeout,
            working_dir=working_dir,
            output_dir=output_dir or working_dir / "output" / "runs",
            ground_truth_dir=working_dir / "evaluation" / "ground-truth",
            trace_id=trace_id,
            enable_observability=enable_observability,
            evaluation_mode=evaluation_mode,
        )
        self._prompts_dir = Path(__file__).parent.parent / "prompts"

    @property
    def prompt_file(self) -> Path:
        """Path to the prompt template file."""
        return self._prompts_dir / f"{self.dimension_name}.md"

    def load_prompt(self, filename: str, **kwargs) -> str:
        """Load and format a prompt template."""
        prompt_path = self._prompts_dir / filename
        if prompt_path.exists():
            template = prompt_path.read_text()
            return template.format(**kwargs)
        return ""

    # load_analysis_results() and get_prompt() are inherited from SharedBaseJudge
