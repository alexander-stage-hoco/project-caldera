"""LLM judge for risk classification accuracy."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class RiskClassificationJudge(BaseJudge):
    """Judge whether the overall risk classification is appropriate."""

    @property
    def dimension_name(self) -> str:
        return "risk_classification"

    @property
    def weight(self) -> float:
        return 0.25

    def get_default_prompt(self) -> str:
        return (
            "You are evaluating risk classification accuracy.\n"
            "Assess whether overall_risk, risk_reasons, and category flags are correct.\n"
            "Return JSON with: dimension, score, confidence, reasoning, "
            "evidence_cited, recommendations, sub_scores.\n"
            "Evidence:\n"
            "{{ analysis_results }}\n"
            "{{ ground_truth }}\n"
        )

    def collect_evidence(self) -> dict[str, Any]:
        return {
            "analysis_results": self.load_all_analysis_results(),
            "ground_truth": self.load_ground_truth(),
        }

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        failures: list[str] = []
        analysis = self.load_all_analysis_results()
        ground_truth = self.load_ground_truth()

        if not analysis:
            failures.append("No analysis results found in output/runs.")
        if not ground_truth:
            failures.append("No ground truth fixtures found in evaluation/ground-truth.")

        # Check that analysis contains risk classification fields
        for name, result in analysis.items():
            data = result.get("data", result)
            if "overall_risk" not in data:
                failures.append(f"Analysis '{name}' missing overall_risk field.")

        return (len(failures) == 0, failures)

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline.

        Delegates to base class implementation which:
        1. Collects evidence via collect_evidence()
        2. Builds prompt from template
        3. Invokes Claude for evaluation
        4. Parses response into JudgeResult
        """
        return super().evaluate()
