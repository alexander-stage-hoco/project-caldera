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
        repos_with_cycles = []
        repos_without_cycles = []

        for repo_name, repo_analysis in all_results.items():
            data = repo_analysis.get("data", repo_analysis)
            cycles = data.get("circular_dependencies", [])

            if cycles:
                total_cycles += len(cycles)
                repos_with_cycles.append(repo_name)
                for cycle in cycles:
                    all_cycles.append({
                        "repo": repo_name,
                        "cycle": cycle,
                        "length": len(cycle) if isinstance(cycle, list) else 0,
                    })
            else:
                repos_without_cycles.append(repo_name)

        # Get summary stats if available
        summary_counts = {}
        for repo_name, repo_analysis in all_results.items():
            data = repo_analysis.get("data", repo_analysis)
            if "summary" in data:
                summary_counts[repo_name] = data["summary"].get("circular_dependency_count", 0)

        # Check consistency between actual cycles and summary
        consistency_issues = []
        for repo_name, summary_count in summary_counts.items():
            actual_count = sum(1 for c in all_cycles if c["repo"] == repo_name)
            if actual_count != summary_count:
                consistency_issues.append({
                    "repo": repo_name,
                    "summary_reports": summary_count,
                    "actual_found": actual_count,
                })

        evidence = {
            "total_cycles": total_cycles,
            "repos_with_cycles": repos_with_cycles,
            "repos_without_cycles": repos_without_cycles,
            "cycles": all_cycles[:10],  # Sample up to 10 cycles
            "summary_counts": summary_counts,
            "consistency_issues": consistency_issues,
            "is_consistent": len(consistency_issues) == 0,
            "evaluation_mode": self.evaluation_mode,
        }

        # Load ground truth for comparison if available
        ground_truth = self.load_ground_truth()
        if ground_truth:
            gt_comparison = []
            for repo_name, gt in ground_truth.items():
                expected = gt.get("expected", {})
                expected_cycles = expected.get("circular_dependency_count", 0)

                actual_count = sum(1 for c in all_cycles if c["repo"] == repo_name)

                gt_comparison.append({
                    "repo": repo_name,
                    "expected": expected_cycles,
                    "actual": actual_count,
                    "match": expected_cycles == actual_count,
                })
            evidence["ground_truth_comparison"] = gt_comparison

        # Inject synthetic context for real-world evaluation
        if self.evaluation_mode == "real_world":
            synthetic_context = self.load_synthetic_evaluation_context()
            if synthetic_context:
                evidence["synthetic_baseline"] = synthetic_context
                evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                    synthetic_context
                )

        return evidence

    def get_default_prompt(self) -> str:
        """Return the default prompt template if file doesn't exist."""
        return """# Circular Dependency Detection Evaluation

You are an expert .NET architect evaluating DependenSee's ability to detect circular dependencies.

## Task

Evaluate the accuracy and completeness of circular dependency detection.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

1. **Detection Accuracy** (40%): Are circular dependencies correctly identified?
   - 5: All cycles detected with no false positives
   - 4: Most cycles detected (>90%), minimal false positives
   - 3: Majority detected (70-90%), some false positives
   - 2: Some cycles missed (50-70%) or many false positives
   - 1: Many cycles missed (<50%) or unreliable results

2. **Path Completeness** (30%): Are full cycle paths reported?
   - 5: All cycles include complete path (A -> B -> C -> A)
   - 4: Most paths complete (>90%)
   - 3: Majority complete (70-90%)
   - 2: Some paths incomplete (50-70%)
   - 1: Paths are missing or incomplete (<50%)

3. **Internal Consistency** (30%): Is the data internally consistent?
   - 5: Summary counts match actual cycle counts exactly
   - 4: Minor discrepancies (<5%)
   - 3: Some discrepancies (5-15%)
   - 2: Significant discrepancies (15-30%)
   - 1: Major inconsistencies (>30%)

## Special Case: No Cycles

If no circular dependencies are found AND ground truth confirms zero cycles expected:
- Score 5 if output is well-formed and consistent
- This is a valid and correct result

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific evidence points>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "detection_accuracy": <1-5>,
    "path_completeness": <1-5>,
    "internal_consistency": <1-5>
  }
}
"""

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run ground truth assertions before LLM evaluation.

        Checks that cycle counts match expected values from ground truth.
        """
        failures = []
        all_results = self.load_all_analysis_results()
        ground_truth = self.load_ground_truth()

        if not ground_truth:
            return True, []

        for repo_name, gt in ground_truth.items():
            if repo_name not in all_results:
                continue

            expected = gt.get("expected", {})
            expected_cycles = expected.get("circular_dependency_count", 0)

            data = all_results[repo_name].get("data", all_results[repo_name])
            actual_cycles = len(data.get("circular_dependencies", []))

            if actual_cycles != expected_cycles:
                failures.append(
                    f"{repo_name}: expected {expected_cycles} cycles, found {actual_cycles}"
                )

        return len(failures) == 0, failures
