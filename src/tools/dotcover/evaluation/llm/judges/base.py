"""Base judge class for LLM-as-a-Judge evaluation of dotCover outputs.

This module re-exports the shared BaseJudge and JudgeResult classes,
and provides dotCover-specific extensions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Import from shared module - eliminates duplicate code
from shared.evaluation import BaseJudge as SharedBaseJudge, JudgeResult
from shared.output_management import unwrap_envelope

# Re-export JudgeResult for backwards compatibility
__all__ = ["BaseJudge", "JudgeResult"]


class BaseJudge(SharedBaseJudge):
    """dotCover-specific base judge for code coverage evaluation.

    Extends the shared BaseJudge with dotCover-specific functionality:
    - Coverage data loading methods
    - Assembly/Type/Method hierarchy handling
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
        """Initialize the dotCover judge.

        Args:
            model: Model name ("sonnet", "opus", "haiku") or full API ID
            timeout: Timeout in seconds for LLM invocation
            working_dir: Working directory for the tool
            output_dir: Directory containing analysis output files
            analysis_path: Path to the coverage output.json file
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
            output_dir=output_dir or working_dir / "outputs",
            ground_truth_dir=working_dir / "evaluation" / "ground-truth",
            trace_id=trace_id,
            enable_observability=enable_observability,
            evaluation_mode=evaluation_mode,
        )
        self.analysis_path = analysis_path or self.output_dir / "output.json"
        self.ground_truth_path = ground_truth_path or self.ground_truth_dir / "synthetic.json"
        self.evaluation_path = evaluation_path or self.working_dir / "evaluation" / "results" / "evaluation_report.json"

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
        """Unwrap output from envelope format to get data.

        Handles both:
        - Envelope format: data wrapper containing coverage info
        - Legacy format: direct coverage data

        Returns the unwrapped data dict that should contain summary, assemblies, etc.
        """
        # Use shared unwrap_envelope helper
        return unwrap_envelope(output)

    def load_all_analysis_results(self) -> dict[str, Any]:
        """Load all analysis JSON files from output_dir.

        Returns dict keyed by run_id (from filename or directory) -> analysis data.
        """
        results = {}

        if self.output_dir.exists() and self.output_dir.is_dir():
            # Check for JSON files in output dir or subdirs
            for json_file in sorted(self.output_dir.glob("**/output.json")):
                try:
                    data = json.loads(json_file.read_text())
                    # Use parent directory name as key
                    run_id = json_file.parent.name if json_file.parent != self.output_dir else "default"
                    results[run_id] = data
                except json.JSONDecodeError:
                    continue

        return results

    def extract_coverage_summary(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """Extract coverage summary from analysis data.

        Args:
            analysis: Analysis data dictionary (potentially wrapped in envelope)

        Returns:
            Summary dictionary with coverage metrics
        """
        data = self.unwrap_output(analysis)
        return data.get("summary", {})

    def extract_assemblies(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract assemblies list from analysis data.

        Args:
            analysis: Analysis data dictionary

        Returns:
            List of assembly coverage dictionaries
        """
        data = self.unwrap_output(analysis)
        return data.get("assemblies", [])

    def extract_types(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract types list from analysis data.

        Args:
            analysis: Analysis data dictionary

        Returns:
            List of type coverage dictionaries
        """
        data = self.unwrap_output(analysis)
        return data.get("types", [])

    def extract_methods(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract methods list from analysis data.

        Args:
            analysis: Analysis data dictionary

        Returns:
            List of method coverage dictionaries
        """
        data = self.unwrap_output(analysis)
        return data.get("methods", [])
