"""LLM judge for license coverage and completeness."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class LicenseCoverageJudge(BaseJudge):
    """Judge whether the output covers expected license categories and files."""

    @property
    def dimension_name(self) -> str:
        return "coverage"

    @property
    def weight(self) -> float:
        return 0.25

    def get_default_prompt(self) -> str:
        return (
            "You are evaluating coverage of license detection.\n"
            "Assess whether expected license categories and files are represented.\n"
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
        if not self.load_all_analysis_results():
            failures.append("No analysis results found in output/runs.")
        if not self.load_ground_truth():
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
