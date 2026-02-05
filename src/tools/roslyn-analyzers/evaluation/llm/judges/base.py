"""Base judge class for LLM-as-a-Judge evaluation of Roslyn Analyzers outputs.

This module re-exports the shared BaseJudge and JudgeResult classes,
and provides Roslyn Analyzers-specific extensions.
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
    """Roslyn Analyzers-specific base judge for static analysis evaluation.

    Extends the shared BaseJudge with Roslyn Analyzers-specific functionality:
    - Multiple ground truth loading methods
    - Analysis results loading by category
    - Evaluation report loading
    """

    def __init__(
        self,
        model: str = "opus-4.5",
        timeout: int = 120,
        working_dir: Path | None = None,
        output_dir: Path | None = None,
        analysis_path: Path | None = None,
        ground_truth_path: Path | None = None,
        evaluation_path: Path | None = None,
        trace_id: str | None = None,
        enable_observability: bool = True,
        evaluation_mode: str | None = None,
    ):
        """Initialize the Roslyn Analyzers judge.

        Args:
            model: Model name ("sonnet", "opus", "haiku") or full API ID
            timeout: Timeout in seconds for LLM invocation
            working_dir: Working directory for the tool
            output_dir: Directory containing analysis output files
            analysis_path: Path to the roslyn_analysis.json file
            ground_truth_path: Path to the primary ground truth file
            evaluation_path: Path to the evaluation report
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
        self.analysis_path = analysis_path or self.output_dir / "roslyn_analysis.json"
        self.ground_truth_path = ground_truth_path or self.ground_truth_dir / "csharp.json"
        self.evaluation_path = evaluation_path or self.output_dir / "evaluation_report.json"

    @property
    def prompt_file(self) -> Path:
        """Path to the prompt template file."""
        return Path(__file__).parent.parent / "prompts" / f"{self.dimension_name}.md"

    def load_analysis(self) -> dict[str, Any]:
        """Load the analysis JSON file."""
        if self.analysis_path.exists():
            return json.loads(self.analysis_path.read_text())
        return {}

    def load_ground_truth(self) -> dict[str, Any]:
        """Load the ground truth JSON file."""
        if self.ground_truth_path.exists():
            return json.loads(self.ground_truth_path.read_text())
        return {}

    def load_evaluation(self) -> dict[str, Any]:
        """Load the evaluation report JSON file."""
        if self.evaluation_path.exists():
            return json.loads(self.evaluation_path.read_text())
        return {}

    @staticmethod
    def unwrap_output(output: dict[str, Any]) -> dict[str, Any]:
        """Unwrap output from envelope format to get results/summary.

        Handles both:
        - Old format: results and summary at top level
        - New envelope format: data wrapper containing results

        Returns the unwrapped data dict that should contain summary, files, etc.
        """
        # Check for envelope format (has 'data' key)
        if "data" in output:
            return output["data"]
        # Check for results wrapper
        if "results" in output and isinstance(output["results"], dict):
            return output["results"]
        # Return as-is
        return output

    def load_all_analysis_results(self) -> dict[str, Any]:
        """Load all analysis JSON files from output_dir.

        Returns dict keyed by repo name (filename stem) -> analysis data.
        """
        results = {}

        if self.output_dir.exists() and self.output_dir.is_dir():
            for json_file in sorted(self.output_dir.glob("*.json")):
                # Skip hidden files and evaluation reports
                if json_file.name.startswith("."):
                    continue
                if "evaluation" in json_file.name.lower():
                    continue
                try:
                    data = json.loads(json_file.read_text())
                    repo_name = json_file.stem
                    results[repo_name] = data
                except json.JSONDecodeError:
                    continue

        return results

    def load_ground_truth_by_name(self, name: str) -> dict[str, Any]:
        """Load ground truth for a specific category."""
        gt_file = self.ground_truth_dir / f"{name}.json"
        if gt_file.exists():
            return json.loads(gt_file.read_text())
        return {}

    def load_all_ground_truths(self) -> dict[str, Any]:
        """Load all ground truth files."""
        results = {}

        if self.ground_truth_dir.exists():
            for gt_file in sorted(self.ground_truth_dir.glob("*.json")):
                try:
                    data = json.loads(gt_file.read_text())
                    results[gt_file.stem] = data
                except json.JSONDecodeError:
                    continue

        return results
