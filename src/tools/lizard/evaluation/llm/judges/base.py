"""Base judge class for LLM-as-a-Judge evaluation of Lizard outputs.

This module re-exports the shared BaseJudge and JudgeResult classes,
and provides Lizard-specific extensions.
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
    """Lizard-specific base judge with analysis path resolution.

    Extends the shared BaseJudge with Lizard-specific functionality:
    - analysis_path parameter for specifying the analysis JSON file
    - Automatic analysis path resolution
    - Analysis loading with envelope unwrapping
    """

    def __init__(
        self,
        model: str = "opus-4.5",
        timeout: int = 120,
        working_dir: Path | None = None,
        analysis_path: Path | None = None,
        trace_id: str | None = None,
        enable_observability: bool = True,
        evaluation_mode: str | None = None,
    ):
        """Initialize the Lizard judge.

        Args:
            model: Model name ("sonnet", "opus", "haiku") or full API ID
            timeout: Timeout in seconds for LLM invocation
            working_dir: Working directory for the tool
            analysis_path: Path to the lizard analysis JSON file
            trace_id: Correlation ID for linking all judges in one evaluation run
            enable_observability: Whether to log LLM interactions (default True)
            evaluation_mode: Evaluation mode ("synthetic", "real_world", or None for auto-detect)
        """
        super().__init__(
            model=model,
            timeout=timeout,
            working_dir=working_dir,
            trace_id=trace_id,
            enable_observability=enable_observability,
            evaluation_mode=evaluation_mode,
        )
        self.analysis_path = analysis_path or self._resolve_analysis_path()

    @property
    def prompt_file(self) -> Path:
        """Path to the prompt template file."""
        return Path(__file__).parent.parent / "prompts" / f"{self.dimension_name}.md"

    def _resolve_analysis_path(self) -> Path:
        """Resolve default analysis path for evaluation."""
        evaluation_path = self.working_dir / "evaluation" / "results" / "output.json"
        if evaluation_path.exists():
            return evaluation_path

        outputs_root = self.working_dir / "outputs"
        if outputs_root.exists():
            candidates = [
                p for p in outputs_root.iterdir()
                if p.is_dir() and (p / "output.json").exists()
            ]
            if candidates:
                return max(candidates, key=lambda p: p.stat().st_mtime) / "output.json"

        return self.working_dir / "output" / "output.json"

    def _load_analysis(self) -> dict[str, Any]:
        """Load analysis JSON, handling envelope payloads."""
        analysis = json.loads(self.analysis_path.read_text())
        if isinstance(analysis, dict) and "data" in analysis:
            return analysis.get("data") or {}
        return analysis

    def build_prompt(self, evidence: dict[str, Any]) -> str:
        """Build the complete prompt with evidence.

        Overrides parent to support per-key placeholder replacement.
        """
        template = self.load_prompt_template()

        # Replace placeholders in template
        prompt = template
        for key, value in evidence.items():
            placeholder = f"{{{{ {key} }}}}"
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, indent=2)
            else:
                value_str = str(value)
            prompt = prompt.replace(placeholder, value_str)

        if "{{" in prompt or "}}" in prompt:
            raise ValueError("Unresolved prompt placeholders detected")
        if "Respond with ONLY a JSON object" not in prompt:
            prompt = (
                prompt
                + "\n\nRespond with ONLY a JSON object. Do not use markdown fences or extra text."
            )

        return prompt
