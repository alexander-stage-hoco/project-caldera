"""Base judge class for LLM-as-a-Judge evaluation of layout scanner outputs.

This module re-exports the shared BaseJudge and JudgeResult classes,
and provides layout-scanner-specific extensions.
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
    """Layout-scanner-specific base judge for file classification evaluation.

    Extends the shared BaseJudge with layout-scanner-specific functionality:
    - Output file loading
    - Ground truth file loading
    - File sampling for large repositories
    """

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
        """Initialize the layout scanner judge.

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
            output_dir=output_dir or working_dir / "outputs",
            ground_truth_dir=working_dir / "evaluation" / "ground-truth",
            trace_id=trace_id,
            enable_observability=enable_observability,
            evaluation_mode=evaluation_mode,
        )

    @property
    def prompt_file(self) -> Path:
        """Path to the prompt template file."""
        return Path(__file__).parent.parent / "prompts" / f"{self.dimension_name}.md"

    def parse_response(self, response: str) -> JudgeResult:
        """Parse the LLM response into a structured result.

        Overrides parent to add score bounds validation.
        """
        try:
            # Try to extract JSON from the response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                result = JudgeResult.from_dict(data)
                result.dimension = self.dimension_name
                if result.score < 1 or result.score > 5:
                    result.score = 3
                result.raw_response = response
                return result
        except json.JSONDecodeError:
            pass

        # Fallback: extract score from text
        score = 3  # Default to middle score
        for i in range(5, 0, -1):
            if f"score: {i}" in response.lower() or f"score:{i}" in response.lower():
                score = i
                break

        return JudgeResult(
            dimension=self.dimension_name,
            score=score,
            confidence=0.5,
            reasoning=response[:500],
            raw_response=response,
        )

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

    def _load_output_files(self) -> list[dict[str, Any]]:
        """Load all scanner output files from the output directory.

        Searches for output.json files in:
        1. Direct files in output_dir (e.g., outputs/*.json)
        2. Subdirectories (e.g., outputs/<run-id>/output.json)
        """
        outputs = []

        if not self.output_dir.exists():
            return outputs

        # First try direct JSON files in output_dir
        for path in self.output_dir.glob("*.json"):
            try:
                with open(path) as f:
                    data = json.load(f)
                    # Handle envelope format
                    if "data" in data and "files" in data.get("data", {}):
                        outputs.append(data["data"])
                    elif "files" in data:
                        outputs.append(data)
            except (json.JSONDecodeError, OSError):
                continue

        # Then try output.json in subdirectories (outputs/<run-id>/output.json)
        for path in self.output_dir.glob("*/output.json"):
            try:
                with open(path) as f:
                    data = json.load(f)
                    # Handle envelope format
                    if "data" in data and "files" in data.get("data", {}):
                        outputs.append(data["data"])
                    elif "files" in data:
                        outputs.append(data)
            except (json.JSONDecodeError, OSError):
                continue

        return outputs

    def _load_ground_truth_files(self) -> list[dict[str, Any]]:
        """Load all ground truth files."""
        gt_dir = self.working_dir / "evaluation" / "ground-truth"
        ground_truths = []

        if not gt_dir.exists():
            return ground_truths

        for path in gt_dir.glob("*.json"):
            try:
                with open(path) as f:
                    ground_truths.append(json.load(f))
            except (json.JSONDecodeError, OSError):
                continue

        return ground_truths

    def _sample_files(
        self, files: dict[str, Any], sample_size: int = 20
    ) -> list[dict[str, Any]]:
        """Sample files for evaluation to keep prompts manageable."""
        file_list = list(files.values())
        if len(file_list) <= sample_size:
            return file_list

        # Sample diverse classifications
        by_classification: dict[str, list] = {}
        for f in file_list:
            cls = f.get("classification", "other")
            by_classification.setdefault(cls, []).append(f)

        sampled = []
        per_class = max(1, sample_size // len(by_classification))

        for cls_files in by_classification.values():
            sampled.extend(cls_files[:per_class])

        return sampled[:sample_size]
