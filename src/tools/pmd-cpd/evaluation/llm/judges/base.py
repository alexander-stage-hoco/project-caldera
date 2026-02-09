"""Base judge class for LLM-as-a-Judge evaluation of PMD CPD outputs.

This module re-exports the shared BaseJudge and JudgeResult classes,
and provides PMD CPD-specific extensions.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

# Import from shared module - eliminates duplicate code
from shared.evaluation import BaseJudge as SharedBaseJudge, JudgeResult

# Re-export JudgeResult for backwards compatibility
__all__ = ["BaseJudge", "JudgeResult"]


class BaseJudge(SharedBaseJudge):
    """PMD CPD-specific base judge with output resolution.

    Extends the shared BaseJudge with PMD CPD-specific functionality:
    - Automatic output directory resolution
    - Tool output loading with envelope unwrapping
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
        """Initialize the PMD CPD judge.

        Args:
            model: Model name ("sonnet", "opus", "haiku") or full API ID
            timeout: Timeout in seconds for LLM invocation
            working_dir: Working directory for the tool
            output_dir: Directory containing analysis output files
            ground_truth_dir: Directory containing ground truth files
            use_llm: Whether to use LLM evaluation (False for heuristic-only)
            trace_id: Correlation ID for linking all judges in one evaluation run
            enable_observability: Whether to log LLM interactions (default True)
            evaluation_mode: Evaluation mode ("synthetic", "real_world", or None for auto-detect)
        """
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
        """Path to the prompt template file."""
        return Path(__file__).parent.parent / "prompts" / f"{self.dimension_name}.md"

    def _load_tool_output(self, output_path: Path) -> dict[str, Any]:
        """Load output JSON, unwrapping envelope data when present."""
        payload = json.loads(output_path.read_text())
        if isinstance(payload, dict) and "data" in payload:
            return payload.get("data") or {}
        return payload

    def _resolve_output_dir(self) -> Path:
        """Resolve the most recent output directory."""
        evaluation_dir = self.working_dir / "evaluation" / "results"
        if (evaluation_dir / "output.json").exists():
            return evaluation_dir

        outputs_root = self.working_dir / "outputs"
        if outputs_root.exists():
            candidates = [
                p for p in outputs_root.iterdir()
                if p.is_dir() and (p / "output.json").exists()
            ]
            if candidates:
                return max(candidates, key=lambda p: p.stat().st_mtime)

        return self.working_dir / "output"

    def invoke_claude(self, prompt: str) -> str:
        """Invoke Claude, with test mode support.

        Overrides parent to add PMD_CPD_TEST_MODE support for testing.
        """
        # Skip real invocation in test mode
        if os.getenv("PMD_CPD_TEST_MODE"):
            return json.dumps({
                "dimension": self.dimension_name,
                "score": 4,
                "confidence": 0.85,
                "reasoning": "Mock response for testing",
                "evidence_cited": [],
                "recommendations": [],
                "sub_scores": {}
            })

        return super().invoke_claude(prompt)
