"""Integration Fit Judge - evaluates DD Platform architecture fit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class IntegrationFitJudge(BaseJudge):
    """Evaluates how well SonarQube output maps to DD Platform schema."""

    def _summarize_tool_output(self, tool_output: dict[str, Any]) -> dict[str, Any]:
        """Reduce envelope payload to a concise summary for prompt size control."""
        if not isinstance(tool_output, dict):
            return {}

        metadata = tool_output.get("metadata", {}) if isinstance(tool_output.get("metadata"), dict) else {}
        data = tool_output.get("data", {}) if isinstance(tool_output.get("data"), dict) else {}

        # Extract issues summary
        issues = data.get("issues", {})
        issues_summary = issues.get("summary", {}) if isinstance(issues, dict) else {}

        # Extract metrics summary
        metrics = data.get("metrics", {})
        metrics_summary = metrics.get("summary", {}) if isinstance(metrics, dict) else {}

        return {
            "metadata": metadata,
            "data": {
                "tool": data.get("tool"),
                "tool_version": data.get("tool_version"),
                "issues_summary": issues_summary,
                "metrics_summary": metrics_summary,
                "has_rollups": "rollups" in issues or "rollups" in data,
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

Evaluate how well SonarQube output maps to DD Platform evidence schema. Score 1-5:
- 5: Perfect fit, no transformation loss
- 4: Minor transformations needed
- 3: Some manual mapping required
- 2: Significant transformation needed
- 1: Incompatible

Respond with JSON: {"score": <1-5>, "confidence": <0-1>, "reasoning": "..."}
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect SonarQube output and envelope output."""
        # Load analysis data
        tool_output = {}
        tool_output_summary = {}
        if self.analysis_path and self.analysis_path.exists():
            tool_output = json.loads(self.analysis_path.read_text())
            tool_output_summary = self._summarize_tool_output(tool_output)

        return {
            "tool_output": tool_output,
            "tool_output_summary": tool_output_summary,
        }

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Verify basic integration requirements."""
        failures = []

        # Check analysis path exists and is valid JSON
        if self.analysis_path is None:
            failures.append("analysis_path not set")
        elif not self.analysis_path.exists():
            failures.append(f"analysis file not found: {self.analysis_path}")
        else:
            try:
                data = json.loads(self.analysis_path.read_text())
                if "metadata" not in data:
                    failures.append("Missing 'metadata' field in output")
                if "data" not in data:
                    failures.append("Missing 'data' field in output")
            except json.JSONDecodeError as e:
                failures.append(f"Invalid JSON in output: {e}")

        return len(failures) == 0, failures

    def evaluate(self) -> JudgeResult:
        """Evaluate integration fit.

        This method performs a heuristic evaluation without invoking the LLM,
        checking structural requirements for DD Platform integration.
        """
        # Run ground truth assertions first
        gt_passed, gt_failures = self.run_ground_truth_assertions()

        if not gt_passed:
            return self._create_result(
                score=1,
                confidence=0.9,
                reasoning=f"Ground truth assertions failed: {', '.join(gt_failures)}",
                recommendations=["Ensure output follows Caldera envelope format"],
            )

        # Analyze integration fit
        data = self.analysis_data
        issues = []
        score = 5

        # Check for Caldera envelope format
        if "metadata" not in data or "data" not in data:
            issues.append("Not using Caldera envelope format")
            score = min(score, 2)
        else:
            metadata = data["metadata"]
            inner_data = data["data"]

            # Check required metadata fields
            required_metadata = ["tool_name", "run_id", "repo_id", "timestamp"]
            missing_metadata = [f for f in required_metadata if f not in metadata]
            if missing_metadata:
                issues.append(f"Missing metadata fields: {missing_metadata}")
                score = min(score, 4)

            # Check for issues structure
            if "issues" not in inner_data:
                issues.append("Missing 'issues' section in data")
                score = min(score, 3)
            else:
                issues_data = inner_data["issues"]
                if "items" not in issues_data:
                    issues.append("Missing 'items' in issues section")
                    score = min(score, 3)
                if "rollups" not in issues_data:
                    issues.append("Missing 'rollups' for directory aggregation")
                    score = min(score, 4)

            # Check for metrics structure
            if "metrics" in inner_data:
                metrics_data = inner_data["metrics"]
                if "summary" not in metrics_data:
                    issues.append("Missing 'summary' in metrics section")
                    score = min(score, 4)

        reasoning = (
            f"Integration fit analysis completed. "
            f"Score: {score}/5. "
            f"Issues found: {len(issues)}. "
            + (f"Details: {'; '.join(issues)}" if issues else "Output follows DD Platform schema.")
        )

        return self._create_result(
            score=score,
            confidence=0.85,
            reasoning=reasoning,
            evidence=[
                f"Envelope format: {'yes' if 'metadata' in data and 'data' in data else 'no'}",
                f"Issues found: {len(issues)}",
            ],
            recommendations=[
                "Ensure all metadata fields are populated",
                "Include rollups for directory-level aggregation",
            ] if issues else [],
        )
