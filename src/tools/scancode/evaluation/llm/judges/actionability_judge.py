"""LLM judge for actionability and clarity of license risk output."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class ActionabilityJudge(BaseJudge):
    """Judge whether outputs provide clear, actionable license insights."""

    @property
    def dimension_name(self) -> str:
        return "actionability"

    @property
    def weight(self) -> float:
        return 0.20

    def get_default_prompt(self) -> str:
        return (
            "You are evaluating actionability of license analysis outputs.\n"
            "Check if outputs clearly explain risk, list concrete license findings, "
            "and are usable for compliance decisions.\n"
            "Return JSON with: dimension, score, confidence, reasoning, "
            "evidence_cited, recommendations, sub_scores.\n"
            "Evidence:\n"
            "{{ analysis_results }}\n"
        )

    def collect_evidence(self) -> dict[str, Any]:
        return {
            "analysis_results": self.load_all_analysis_results(),
        }

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        failures: list[str] = []
        if not self.load_all_analysis_results():
            failures.append("No analysis results found in output/runs.")
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
