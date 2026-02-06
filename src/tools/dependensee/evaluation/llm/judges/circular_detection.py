"""Circular Dependency Detection Judge - Evaluates circular dependency analysis."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class CircularDetectionJudge(BaseJudge):
    """Evaluates circular dependency detection capabilities.

    Validates that:
    - Circular dependencies are correctly identified
    - Cycles are reported with full path information
    - No false positives are generated
    """

    @property
    def dimension_name(self) -> str:
        return "circular_detection"

    @property
    def weight(self) -> float:
        return 0.20  # 20% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis and assess circular dependency detection."""
        all_results = self.load_all_analysis_results()
        if not all_results:
            return {"error": f"No analysis files found in {self.output_dir}"}

        # Aggregate from all repos
        total_cycles = 0
        all_cycles = []

        for repo_name, repo_analysis in all_results.items():
            data = repo_analysis.get("data", repo_analysis)
            cycles = data.get("circular_dependencies", [])
            total_cycles += len(cycles)
            for cycle in cycles:
                all_cycles.append({
                    "repo": repo_name,
                    "cycle": cycle,
                    "length": len(cycle),
                })

        # Get summary stats if available
        summary = {}
        for repo_name, repo_analysis in all_results.items():
            data = repo_analysis.get("data", repo_analysis)
            if "summary" in data:
                summary = data["summary"]
                break

        return {
            "total_cycles": total_cycles,
            "cycles": all_cycles[:10],  # Sample up to 10 cycles
            "summary_count": summary.get("circular_dependency_count", total_cycles),
            "evaluation_mode": self.evaluation_mode,
        }

    def format_prompt(self, evidence: dict[str, Any]) -> str:
        """Format prompt for LLM evaluation."""
        prompt_template = self.prompt_file.read_text() if self.prompt_file.exists() else ""
        return prompt_template.format(
            total_cycles=evidence.get("total_cycles", 0),
            cycles=evidence.get("cycles", []),
        )

    def parse_response(self, response: str, evidence: dict[str, Any]) -> JudgeResult:
        """Parse LLM response into structured result."""
        total_cycles = evidence.get("total_cycles", 0)
        summary_count = evidence.get("summary_count", 0)

        # Check consistency between actual cycles and summary
        consistent = (total_cycles == summary_count)

        if consistent:
            overall_score = 1.0
            verdict = "PASS"
            reasoning = f"Circular dependency detection is consistent. Found {total_cycles} cycles."
        else:
            overall_score = 0.5
            verdict = "FAIL"
            reasoning = f"Inconsistency: summary reports {summary_count} cycles but {total_cycles} were found."

        return JudgeResult(
            dimension=self.dimension_name,
            score=overall_score,
            verdict=verdict,
            reasoning=reasoning,
            evidence=evidence,
        )
