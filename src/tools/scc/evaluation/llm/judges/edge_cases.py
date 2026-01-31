"""Edge Cases Judge - evaluates handling of unusual files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class EdgeCasesJudge(BaseJudge):
    """Evaluates how scc handles edge cases."""

    @property
    def dimension_name(self) -> str:
        return "edge_cases"

    @property
    def weight(self) -> float:
        return 0.10  # 10%

    def get_default_prompt(self) -> str:
        return """# Edge Cases Judge

Evaluate scc edge case handling. Score 1-5:
- 5: All edge cases handled gracefully
- 4: Most edge cases work
- 3: Common edge cases work
- 2: Frequent failures
- 1: Cannot process many valid files

Respond with JSON: {"score": <1-5>, "confidence": <0-1>, "reasoning": "..."}
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect edge case test results."""
        results_dir = self.working_dir / "evaluation" / "results"

        # Load evaluation results
        edge_case_results = {}
        latest_results = sorted(results_dir.glob("eval-*.json"))
        if latest_results:
            data = json.loads(latest_results[-1].read_text())
            # Extract reliability checks
            for dim in data.get("dimensions", []):
                if dim.get("dimension") == "reliability" or dim.get("name") == "reliability":
                    edge_case_results = dim.get("checks", [])
                    break

        return {
            "edge_case_results": edge_case_results,
            "error_output": "",  # No errors in current tests
        }

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Verify edge cases were tested."""
        failures = []
        results_dir = self.working_dir / "evaluation" / "results"

        # Check that evaluation was run
        results_files = list(results_dir.glob("eval-*.json"))
        if not results_files:
            failures.append("No evaluation results found")
            return False, failures

        # Load latest results
        data = json.loads(results_files[-1].read_text())

        # Check reliability dimension exists
        reliability_found = False
        for dim in data.get("dimensions", []):
            if dim.get("dimension") == "reliability" or dim.get("name") == "reliability":
                reliability_found = True
                # Check specific edge cases
                checks = {c.get("check_id", c.get("id")): c for c in dim.get("checks", [])}

                if "RL-1" not in checks:
                    failures.append("Empty file handling not tested")
                if "RL-2" not in checks:
                    failures.append("Comments-only handling not tested")
                if "RL-4" not in checks:
                    failures.append("Unicode handling not tested")

        if not reliability_found:
            failures.append("Reliability dimension not found")

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
