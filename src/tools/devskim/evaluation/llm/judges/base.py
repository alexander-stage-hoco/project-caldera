"""Base judge class for LLM-as-a-Judge evaluation of DevSkim security linting.

This module inherits from the shared BaseJudge and provides DevSkim-specific
functionality like unwrapping envelope format and loading analysis results.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Add shared src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[6]))

# Import shared base judge (reuses LLMClient, observability, etc.)
from shared.evaluation import BaseJudge as SharedBaseJudge, JudgeResult


# Re-export JudgeResult for backwards compatibility
__all__ = ["BaseJudge", "JudgeResult"]


class BaseJudge(SharedBaseJudge):
    """DevSkim-specific base judge class.

    Extends the shared BaseJudge with DevSkim-specific functionality:
    - Envelope unwrapping for DevSkim output format
    - Analysis result loading from DevSkim output directory structure
    - Backward-compatible analysis_path parameter

    Each judge evaluates a specific dimension of DevSkim security
    analysis quality. Judges invoke Claude in headless mode with
    specialized prompts.
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
        """Initialize the DevSkim judge.

        Args:
            model: Model name ("sonnet", "opus", "opus-4.5", "haiku")
            timeout: Timeout in seconds for LLM invocation
            working_dir: Working directory for the tool
            analysis_path: Path to DevSkim analysis JSON (deprecated, use output_dir)
            output_dir: Directory containing analysis output files
            evaluation_mode: Evaluation mode ("synthetic", "real_world", or None for auto-detect)
        """
        working_dir = working_dir or Path.cwd()
        output_dir = output_dir or working_dir / "outputs"

        # Store analysis_path for backward compatibility
        self._analysis_path = analysis_path or output_dir / "devskim_analysis.json"

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
        """Path to the DevSkim analysis JSON file (deprecated)."""
        return self._analysis_path

    @property
    def prompt_file(self) -> Path:
        """Path to the prompt template file."""
        return Path(__file__).parent.parent / "prompts" / f"{self.dimension_name}.md"

    def _unwrap_envelope(self, data: dict[str, Any]) -> dict[str, Any]:
        """Unwrap envelope structure if present.

        Tool outputs use envelope: {"metadata": {...}, "data": {...}}
        This extracts the inner "data" content for judge processing.

        Args:
            data: Raw analysis data that may be wrapped in envelope

        Returns:
            Unwrapped data dictionary
        """
        if "data" in data and isinstance(data["data"], dict):
            # Preserve metadata alongside unwrapped data
            inner = data["data"].copy()
            if "metadata" in data:
                inner["_metadata"] = data["metadata"]
            return inner
        return data

    def load_all_analysis_results(self) -> dict[str, Any]:
        """Load all analysis JSON files from output_dir.

        Handles two directory structures:
        1. Nested: outputs/<run-id>/output.json (preferred)
        2. Flat: outputs/*.json (backwards compatibility)

        Automatically unwraps envelope structure (metadata + data).

        Returns:
            Dictionary keyed by repo name to analysis data.
        """
        results = {}

        if self.output_dir.exists() and self.output_dir.is_dir():
            # Check for nested structure: outputs/<run-id>/output.json
            for subdir in sorted(self.output_dir.iterdir()):
                if subdir.is_dir():
                    output_file = subdir / "output.json"
                    if output_file.exists():
                        try:
                            raw_data = json.loads(output_file.read_text())
                            repo_name = raw_data.get("metadata", {}).get("repo_name", subdir.name)
                            results[repo_name] = self._unwrap_envelope(raw_data)
                        except json.JSONDecodeError:
                            continue

            # Also check for flat structure: outputs/*.json (backwards compat)
            for json_file in sorted(self.output_dir.glob("*.json")):
                if json_file.name.startswith("."):
                    continue
                try:
                    raw_data = json.loads(json_file.read_text())
                    repo_name = json_file.stem
                    if repo_name not in results:
                        results[repo_name] = self._unwrap_envelope(raw_data)
                except json.JSONDecodeError:
                    continue

        # Fallback to single analysis_path
        if not results and self._analysis_path.exists():
            try:
                raw_data = json.loads(self._analysis_path.read_text())
                results["default"] = self._unwrap_envelope(raw_data)
            except json.JSONDecodeError:
                pass

        return results
