"""Base judge class for LLM-as-a-Judge evaluation of scancode outputs.

This module inherits from the shared BaseJudge and provides scancode-specific
functionality like loading ground truth fixtures.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Import shared base judge (reuses LLMClient, observability, etc.)
from shared.evaluation import BaseJudge as SharedBaseJudge, JudgeResult


# Re-export JudgeResult for backwards compatibility
__all__ = ["BaseJudge", "JudgeResult"]


class BaseJudge(SharedBaseJudge):
    """Scancode-specific base judge class.

    Extends the shared BaseJudge with scancode-specific functionality:
    - Analysis result loading from scancode output directory structure
    - Ground truth fixture loading from evaluation directory
    - Backward-compatible analysis_path parameter
    """

    def __init__(
        self,
        model: str = "opus-4.5",
        timeout: int = 120,
        working_dir: Path | None = None,
        analysis_path: Path | None = None,
        output_dir: Path | None = None,
        evaluation_mode: str | None = None,
    ):
        """Initialize the scancode judge.

        Args:
            model: Model name ("sonnet", "opus", "opus-4.5", "haiku")
            timeout: Timeout in seconds for LLM invocation
            working_dir: Working directory for the tool
            analysis_path: Path to scancode analysis JSON (deprecated, use output_dir)
            output_dir: Directory containing analysis output files
            evaluation_mode: Evaluation mode ("synthetic", "real_world", or None for auto-detect)
        """
        working_dir = working_dir or Path.cwd()
        output_dir = output_dir or working_dir / "outputs"

        # Store analysis_path for backward compatibility
        self._analysis_path = analysis_path or output_dir / "output.json"

        # Call shared base class
        super().__init__(
            model=model,
            timeout=timeout,
            working_dir=working_dir,
            output_dir=output_dir,
            ground_truth_dir=working_dir / "evaluation" / "ground-truth",
            use_llm=True,
            evaluation_mode=evaluation_mode,
        )

    @property
    def analysis_path(self) -> Path:
        """Path to the scancode analysis JSON file (deprecated)."""
        return self._analysis_path

    @property
    def prompt_file(self) -> Path:
        """Path to the prompt template file."""
        return Path(__file__).parent.parent / "prompts" / f"{self.dimension_name}.md"

    def load_all_analysis_results(self) -> dict[str, Any]:
        """Load all analysis JSON files from output_dir (including subdirectories).

        Returns:
            Dictionary keyed by run ID or filename to analysis data.
        """
        results: dict[str, Any] = {}

        if self.output_dir.exists() and self.output_dir.is_dir():
            # Look for output.json in run subdirectories (outputs/<run-id>/output.json)
            for json_file in sorted(self.output_dir.glob("*/output.json")):
                try:
                    data = json.loads(json_file.read_text())
                    run_id = json_file.parent.name
                    results[run_id] = data
                except json.JSONDecodeError:
                    continue

            # Also check for direct JSON files
            for json_file in sorted(self.output_dir.glob("*.json")):
                if json_file.name.startswith("."):
                    continue
                try:
                    data = json.loads(json_file.read_text())
                    results[json_file.stem] = data
                except json.JSONDecodeError:
                    continue

        if not results and self._analysis_path.exists():
            try:
                data = json.loads(self._analysis_path.read_text())
                results["default"] = data
            except json.JSONDecodeError:
                pass

        return results

    def load_ground_truth(self) -> dict[str, Any]:
        """Load ground truth JSON fixtures for comparison.

        Returns:
            Dictionary keyed by fixture name to ground truth data.
        """
        results: dict[str, Any] = {}
        if not self.ground_truth_dir.exists():
            return results

        for json_file in sorted(self.ground_truth_dir.glob("*.json")):
            if json_file.name.startswith("."):
                continue
            try:
                data = json.loads(json_file.read_text())
                results[json_file.stem] = data
            except json.JSONDecodeError:
                continue

        return results

    def build_prompt(self, evidence: dict[str, Any]) -> str:
        """Build the complete prompt with evidence.

        Supports template placeholders like {{ key_name }}.

        Args:
            evidence: Evidence dictionary from collect_evidence()

        Returns:
            Complete prompt string ready for LLM invocation
        """
        template = self.load_prompt_template()
        prompt = template
        for key, value in evidence.items():
            placeholder = f"{{{{ {key} }}}}"
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, indent=2)
            else:
                value_str = str(value)
            prompt = prompt.replace(placeholder, value_str)
        return prompt
