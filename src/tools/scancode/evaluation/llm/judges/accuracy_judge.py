"""LLM judge for license detection accuracy."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class LicenseAccuracyJudge(BaseJudge):
    """Judge whether detected licenses match expected ground truth."""

    @property
    def dimension_name(self) -> str:
        return "accuracy"

    @property
    def weight(self) -> float:
        return 0.30

    def get_default_prompt(self) -> str:
        return (
            "You are evaluating license detection accuracy.\n"
            "Compare analysis_results to ground_truth and score accuracy 1-5.\n"
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
