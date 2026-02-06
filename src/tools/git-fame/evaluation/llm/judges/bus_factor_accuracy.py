"""Bus Factor Accuracy Judge - Evaluates correctness of bus factor calculation."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class BusFactorAccuracyJudge(BaseJudge):
    """Evaluates accuracy of bus factor calculation.

    Validates that:
    - Bus factor is correctly calculated (minimum authors for 50% coverage)
    - Bus factor aligns with ownership distribution
    - Risk assessment based on bus factor is appropriate
    """

    @property
    def dimension_name(self) -> str:
        return "bus_factor_accuracy"

    @property
    def weight(self) -> float:
        return 0.20  # 20% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis and assess bus factor accuracy."""
        all_results = self.load_all_analysis_results()
        if not all_results:
            return {"error": f"No analysis files found in {self.output_dir}"}

        bus_factor_analysis: list[dict] = []

        for repo_name, repo_data in all_results.items():
            authors = self.extract_authors(repo_data)
            summary = self.extract_summary(repo_data)

            reported_bus_factor = summary.get("bus_factor", 0)
            calculated_bus_factor = self.calculate_bus_factor(authors)

            # Calculate cumulative ownership for top N authors
            sorted_authors = sorted(
                authors,
                key=lambda a: a.get("ownership_pct", 0),
                reverse=True
            )

            cumulative_coverage: list[dict] = []
            cumsum = 0.0
            for i, author in enumerate(sorted_authors[:10], 1):
                cumsum += author.get("ownership_pct", 0)
                cumulative_coverage.append({
                    "rank": i,
                    "author": author.get("name", ""),
                    "ownership_pct": author.get("ownership_pct", 0),
                    "cumulative_pct": round(cumsum, 2),
                })

            # Determine risk level based on bus factor
            author_count = len(authors)
            if author_count == 0:
                risk_level = "unknown"
            elif reported_bus_factor == 1:
                risk_level = "critical"
            elif reported_bus_factor <= 2:
                risk_level = "high"
            elif reported_bus_factor <= 4:
                risk_level = "moderate"
            else:
                risk_level = "low"

            bus_factor_analysis.append({
                "repo": repo_name,
                "reported_bus_factor": reported_bus_factor,
                "calculated_bus_factor": calculated_bus_factor,
                "match": reported_bus_factor == calculated_bus_factor,
                "author_count": author_count,
                "top_author_pct": summary.get("top_author_pct", 0),
                "cumulative_coverage": cumulative_coverage[:5],
                "risk_level": risk_level,
            })

        # Count matches and mismatches
        matches = sum(1 for a in bus_factor_analysis if a["match"])
        mismatches = len(bus_factor_analysis) - matches

        evidence = {
            "total_repos": len(all_results),
            "bus_factor_matches": matches,
            "bus_factor_mismatches": mismatches,
            "accuracy_pct": round(matches / len(bus_factor_analysis) * 100, 1) if bus_factor_analysis else 0,
            "bus_factor_analysis": bus_factor_analysis,
            "evaluation_mode": self.evaluation_mode,
        }

        # Load ground truth for comparison if available
        ground_truth = self.load_ground_truth()
        if ground_truth:
            gt_comparison = []
            for analysis in bus_factor_analysis:
                repo_name = analysis["repo"]
                if repo_name in ground_truth:
                    expected_bf = ground_truth[repo_name].get("expected", {}).get("bus_factor")
                    if expected_bf is not None:
                        gt_comparison.append({
                            "repo": repo_name,
                            "expected": expected_bf,
                            "actual": analysis["reported_bus_factor"],
                            "match": expected_bf == analysis["reported_bus_factor"],
                        })
            if gt_comparison:
                evidence["ground_truth_comparison"] = gt_comparison

        # Add synthetic context if available
        synthetic_context = self.load_synthetic_evaluation_context()
        if synthetic_context:
            evidence["synthetic_baseline"] = synthetic_context
            evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                synthetic_context
            )
        else:
            evidence["synthetic_baseline"] = "Not available"
            evidence["interpretation_guidance"] = "Evaluate bus factor calculation accuracy."

        return evidence

    def get_default_prompt(self) -> str:
        """Return the default prompt template if file doesn't exist."""
        return """# Bus Factor Accuracy Evaluation

You are evaluating git-fame's accuracy in calculating the bus factor metric.

## Background

Bus factor = minimum number of authors whose combined ownership reaches 50% of the codebase.
A low bus factor (1-2) indicates high key-person risk.

## Task

Evaluate the accuracy of bus factor calculation in the git-fame output.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

1. **Calculation Accuracy (50%)**: Is bus factor correctly calculated?
   - 5: All bus factors match recalculated values exactly
   - 4: Minor discrepancies in edge cases only
   - 3: Some repos have incorrect values (>80% correct)
   - 2: Many repos have incorrect values (50-80% correct)
   - 1: Systematic calculation errors (<50% correct)

2. **Consistency with Distribution (30%)**: Does bus factor align with ownership?
   - 5: Bus factor perfectly reflects ownership concentration
   - 4: Minor inconsistencies
   - 3: Some inconsistencies
   - 2: Significant inconsistencies
   - 1: Bus factor contradicts ownership data

3. **Risk Assessment Validity (20%)**: Is risk classification appropriate?
   - 5: Risk levels accurately reflect bus factor implications
   - 4: Minor misclassifications
   - 3: Some misclassifications
   - 2: Many misclassifications
   - 1: Risk assessment is unreliable

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific evidence points>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "calculation_accuracy": <1-5>,
    "distribution_consistency": <1-5>,
    "risk_assessment": <1-5>
  }
}
"""

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run ground truth assertions before LLM evaluation."""
        failures = []
        all_results = self.load_all_analysis_results()
        ground_truth = self.load_ground_truth()

        if not ground_truth:
            return True, []

        for repo_name, gt in ground_truth.items():
            if repo_name not in all_results:
                continue

            expected = gt.get("expected", {})
            expected_bf = expected.get("bus_factor")
            if expected_bf is None:
                continue

            summary = self.extract_summary(all_results[repo_name])
            actual_bf = summary.get("bus_factor", 0)

            if actual_bf != expected_bf:
                failures.append(
                    f"{repo_name}: expected bus_factor={expected_bf}, got {actual_bf}"
                )

        return len(failures) == 0, failures
