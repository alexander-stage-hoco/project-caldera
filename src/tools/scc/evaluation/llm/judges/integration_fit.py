"""Integration Fit Judge - evaluates DD Platform architecture fit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class IntegrationFitJudge(BaseJudge):
    """Evaluates how well scc output maps to DD Platform schema."""

    def _summarize_tool_output(self, tool_output: dict[str, Any]) -> dict[str, Any]:
        """Reduce envelope payload to a concise summary for prompt size control."""
        if not isinstance(tool_output, dict):
            return {}

        metadata = tool_output.get("metadata", {}) if isinstance(tool_output.get("metadata"), dict) else {}
        data = tool_output.get("data", {}) if isinstance(tool_output.get("data"), dict) else {}

        languages = data.get("languages")
        languages_sample = None
        if isinstance(languages, list):
            languages_sample = languages[:5]

        return {
            "metadata": metadata,
            "data": {
                "tool": data.get("tool"),
                "tool_version": data.get("tool_version"),
                "summary": data.get("summary"),
                "languages_sample": languages_sample,
                "language_count": len(languages) if isinstance(languages, list) else None,
            },
        }

    @property
    def dimension_name(self) -> str:
        return "integration_fit"

    @property
    def weight(self) -> float:
        return 0.10  # 10%

    def get_default_prompt(self) -> str:
        return """# Integration Fit Judge

Evaluate how well scc maps to DD Platform evidence schema. Score 1-5:
- 5: Perfect fit, no transformation loss
- 4: Minor transformations needed
- 3: Some manual mapping required
- 2: Significant transformation needed
- 1: Incompatible

Respond with JSON: {"score": <1-5>, "confidence": <0-1>, "reasoning": "..."}
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect scc output and envelope output."""
        output_dir = self._resolve_output_dir()

        # Load raw scc output
        scc_output = {}
        raw_file = output_dir / "raw_scc_output.json"
        if raw_file.exists():
            scc_output = json.loads(raw_file.read_text())

        # Load envelope output
        tool_output = {}
        tool_data = {}
        tool_output_summary = {}
        output_file = output_dir / "output.json"
        if output_file.exists():
            tool_output = json.loads(output_file.read_text())
            tool_data = self._load_tool_output(output_file)
            tool_output_summary = self._summarize_tool_output(tool_output)

        return {
            "scc_output": scc_output,
            "tool_output": tool_output,
            "tool_data": tool_data,
            "tool_output_summary": tool_output_summary,
        }

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Verify basic integration requirements."""
        failures = []
        output_dir = self.working_dir / "output"

        # Check output file exists and is valid JSON
        output_file = output_dir / "output.json"
        if not output_file.exists():
            failures.append("output.json not found")
        else:
            try:
                data = json.loads(output_file.read_text())
                if "metadata" not in data:
                    failures.append("Missing 'metadata' field in output")
                if "data" not in data:
                    failures.append("Missing 'data' field in output")
            except json.JSONDecodeError as e:
                failures.append(f"Invalid JSON in output: {e}")

        return len(failures) == 0, failures

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline.

        Delegates to base class implementation which:
        1. Collects evidence via collect_evidence()
        2. Builds prompt from template
        3. Invokes Claude for evaluation
        4. Parses response into JudgeResult
        """
        return super().evaluate()
