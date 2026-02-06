"""Concentration Metrics Judge - Evaluates ownership concentration calculations."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult
from .utils import calculate_concentration_metrics


class ConcentrationMetricsJudge(BaseJudge):
    """Evaluates accuracy of ownership concentration metrics.

    Validates that:
    - HHI (Herfindahl-Hirschman Index) is correctly calculated
    - Top-N author percentages are accurate
    - Concentration metrics are consistent with each other
    """

    @property
    def dimension_name(self) -> str:
        return "concentration_metrics"

    @property
    def weight(self) -> float:
        return 0.20  # 20% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis and assess concentration metrics accuracy."""
        all_results = self.load_all_analysis_results()
        if not all_results:
            return {"error": f"No analysis files found in {self.output_dir}"}

        concentration_analysis: list[dict] = []

        for repo_name, repo_data in all_results.items():
            authors = self.extract_authors(repo_data)
            summary = self.extract_summary(repo_data)

            # Get reported values
            reported_hhi = summary.get("hhi_index", 0)
            reported_top_pct = summary.get("top_author_pct", 0)
            reported_top_two = summary.get("top_two_pct", 0)

            # Calculate expected values
            calculated = calculate_concentration_metrics(authors)

            # Compare reported vs calculated
            hhi_diff = abs(reported_hhi - calculated["hhi"])
            top1_diff = abs(reported_top_pct - calculated["top_1_pct"])

            # Determine if values match (within tolerance)
            hhi_match = hhi_diff < 0.01  # 1% tolerance for HHI
            top1_match = top1_diff < 1.0  # 1 percentage point tolerance

            concentration_analysis.append({
                "repo": repo_name,
                "author_count": len(authors),
                "reported": {
                    "hhi_index": reported_hhi,
                    "top_author_pct": reported_top_pct,
                    "top_two_pct": reported_top_two,
                },
                "calculated": {
                    "hhi": calculated["hhi"],
                    "gini": calculated["gini"],
                    "top_1_pct": calculated["top_1_pct"],
                    "top_3_pct": calculated["top_3_pct"],
                    "top_5_pct": calculated["top_5_pct"],
                },
                "validation": {
                    "hhi_match": hhi_match,
                    "hhi_diff": round(hhi_diff, 4),
                    "top1_match": top1_match,
                    "top1_diff": round(top1_diff, 2),
                },
                "concentration_level": self._classify_concentration(calculated["hhi"]),
            })

        # Calculate overall accuracy
        hhi_matches = sum(1 for a in concentration_analysis if a["validation"]["hhi_match"])
        top1_matches = sum(1 for a in concentration_analysis if a["validation"]["top1_match"])
        total = len(concentration_analysis)

        evidence = {
            "total_repos": total,
            "hhi_accuracy_pct": round(hhi_matches / total * 100, 1) if total > 0 else 0,
            "top_author_accuracy_pct": round(top1_matches / total * 100, 1) if total > 0 else 0,
            "concentration_analysis": concentration_analysis,
            "evaluation_mode": self.evaluation_mode,
        }

        # Load ground truth for comparison if available
        ground_truth = self.load_ground_truth()
        if ground_truth:
            gt_comparison = []
            for analysis in concentration_analysis:
                repo_name = analysis["repo"]
                if repo_name in ground_truth:
                    expected = ground_truth[repo_name].get("expected", {})
                    expected_hhi = expected.get("hhi_index")
                    if expected_hhi is not None:
                        actual_hhi = analysis["reported"]["hhi_index"]
                        gt_comparison.append({
                            "repo": repo_name,
                            "expected_hhi": expected_hhi,
                            "actual_hhi": actual_hhi,
                            "match": abs(expected_hhi - actual_hhi) < 0.01,
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
            evidence["interpretation_guidance"] = "Evaluate concentration metric accuracy."

        return evidence

    def _classify_concentration(self, hhi: float) -> str:
        """Classify concentration level based on HHI.

        Args:
            hhi: Herfindahl-Hirschman Index value (0-1)

        Returns:
            Classification string
        """
        if hhi >= 0.50:
            return "highly_concentrated"
        elif hhi >= 0.25:
            return "moderately_concentrated"
        elif hhi >= 0.15:
            return "unconcentrated"
        else:
            return "highly_distributed"

    def get_default_prompt(self) -> str:
        """Return the default prompt template if file doesn't exist."""
        return """# Concentration Metrics Evaluation

You are evaluating git-fame's accuracy in calculating ownership concentration metrics.

## Background

- **HHI (Herfindahl-Hirschman Index)**: Sum of squared ownership fractions (0=equal, 1=monopoly)
  - >0.50: Highly concentrated
  - 0.25-0.50: Moderately concentrated
  - 0.15-0.25: Unconcentrated
  - <0.15: Highly distributed

- **Top Author Percentage**: Ownership percentage of the highest contributor
- **Top Two Percentage**: Combined ownership of top two contributors

## Task

Evaluate the accuracy of concentration metric calculations in the git-fame output.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

1. **HHI Accuracy (40%)**: Is HHI correctly calculated?
   - 5: All HHI values match recalculated values (within 1% tolerance)
   - 4: Minor discrepancies in edge cases only
   - 3: Some repos have incorrect values (>80% correct)
   - 2: Many repos have incorrect values (50-80% correct)
   - 1: Systematic calculation errors (<50% correct)

2. **Top-N Accuracy (35%)**: Are top author percentages correct?
   - 5: All top-N values match exactly
   - 4: Minor rounding differences only
   - 3: Some values off by >1 percentage point
   - 2: Many values incorrect
   - 1: Top-N calculations unreliable

3. **Internal Consistency (25%)**: Are metrics consistent with each other?
   - 5: All metrics are mutually consistent
   - 4: Minor inconsistencies
   - 3: Some inconsistencies
   - 2: Significant inconsistencies
   - 1: Metrics contradict each other

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific evidence points>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "hhi_accuracy": <1-5>,
    "top_n_accuracy": <1-5>,
    "internal_consistency": <1-5>
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
            summary = self.extract_summary(all_results[repo_name])

            # Check HHI
            expected_hhi = expected.get("hhi_index")
            if expected_hhi is not None:
                actual_hhi = summary.get("hhi_index", 0)
                if abs(actual_hhi - expected_hhi) > 0.02:  # 2% tolerance
                    failures.append(
                        f"{repo_name}: expected hhi_index={expected_hhi}, got {actual_hhi}"
                    )

            # Check top author percentage
            expected_top = expected.get("top_author_pct")
            if expected_top is not None:
                actual_top = summary.get("top_author_pct", 0)
                if abs(actual_top - expected_top) > 2.0:  # 2 percentage point tolerance
                    failures.append(
                        f"{repo_name}: expected top_author_pct={expected_top}, got {actual_top}"
                    )

        return len(failures) == 0, failures
