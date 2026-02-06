"""Authorship Quality Judge - Evaluates accuracy of author attribution."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult
from .utils import compare_authors, validate_ownership_percentages


class AuthorshipQualityJudge(BaseJudge):
    """Evaluates the quality and accuracy of author attribution.

    Validates that:
    - Authors are correctly identified from git history
    - Ownership percentages are accurate and sum to 100%
    - Author metrics (LOC, commits, files) are reasonable
    """

    @property
    def dimension_name(self) -> str:
        return "authorship_quality"

    @property
    def weight(self) -> float:
        return 0.25  # 25% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis and assess authorship quality."""
        all_results = self.load_all_analysis_results()
        if not all_results:
            return {"error": f"No analysis files found in {self.output_dir}"}

        # Aggregate authorship data from all repos
        total_authors = 0
        total_loc = 0
        all_author_data: list[dict] = []
        validation_issues: list[str] = []
        repo_summaries: list[dict] = []

        for repo_name, repo_data in all_results.items():
            authors = self.extract_authors(repo_data)
            summary = self.extract_summary(repo_data)

            total_authors += len(authors)
            total_loc += summary.get("total_loc", 0)

            # Validate ownership percentages
            validation = validate_ownership_percentages(authors)
            if not validation["valid"]:
                validation_issues.extend(
                    [f"{repo_name}: {issue}" for issue in validation["issues"]]
                )

            # Sample top authors for evidence
            sorted_authors = sorted(
                authors,
                key=lambda a: a.get("ownership_pct", 0),
                reverse=True
            )
            all_author_data.extend(sorted_authors[:5])

            repo_summaries.append({
                "repo": repo_name,
                "author_count": len(authors),
                "total_loc": summary.get("total_loc", 0),
                "top_author_pct": summary.get("top_author_pct", 0),
                "ownership_valid": validation["valid"],
            })

        evidence = {
            "total_repos": len(all_results),
            "total_authors": total_authors,
            "total_loc": total_loc,
            "sample_authors": all_author_data[:15],  # Top 15 authors across all repos
            "repo_summaries": repo_summaries,
            "validation_issues": validation_issues,
            "evaluation_mode": self.evaluation_mode,
        }

        # Load ground truth for comparison if available
        ground_truth = self.load_ground_truth()
        if ground_truth:
            gt_comparison = []
            for repo_name, gt in ground_truth.items():
                if repo_name not in all_results:
                    continue

                expected_authors = gt.get("expected", {}).get("authors", [])
                actual_authors = self.extract_authors(all_results[repo_name])

                comparison = compare_authors(actual_authors, expected_authors)
                gt_comparison.append({
                    "repo": repo_name,
                    "accuracy": comparison["accuracy"],
                    "matches": len(comparison["matches"]),
                    "mismatches": len(comparison["mismatches"]),
                    "missing": len(comparison["missing"]),
                })
            evidence["ground_truth_comparison"] = gt_comparison

        # Add synthetic context if available
        synthetic_context = self.load_synthetic_evaluation_context()
        if synthetic_context:
            evidence["synthetic_baseline"] = synthetic_context
            evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                synthetic_context
            )
        else:
            evidence["synthetic_baseline"] = "Not available (synthetic evaluation mode)"
            evidence["interpretation_guidance"] = "Evaluate against ground truth expectations."

        return evidence

    def get_default_prompt(self) -> str:
        """Return the default prompt template if file doesn't exist."""
        return """# Authorship Quality Evaluation

You are an expert in code analysis evaluating git-fame's accuracy in author attribution.

## Task

Evaluate the quality and accuracy of author attribution in the git-fame output.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

1. **Author Identification (40%)**: Are authors correctly identified?
   - 5: All authors captured with correct names
   - 4: Most authors correct (>95%)
   - 3: Majority correct (85-95%)
   - 2: Some issues (70-85%)
   - 1: Many authors missing or incorrect (<70%)

2. **Ownership Accuracy (35%)**: Are ownership percentages accurate?
   - 5: All percentages sum to 100%, values are reasonable
   - 4: Minor discrepancies (<1% total deviation)
   - 3: Some issues (1-5% deviation)
   - 2: Significant issues (5-10% deviation)
   - 1: Major data integrity issues (>10% deviation)

3. **Metric Completeness (25%)**: Are author metrics complete?
   - 5: LOC, commits, files all present and valid
   - 4: Minor metrics missing (<5%)
   - 3: Some metrics missing (5-15%)
   - 2: Many metrics missing (15-30%)
   - 1: Critical data missing (>30%)

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific evidence points>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "author_identification": <1-5>,
    "ownership_accuracy": <1-5>,
    "metric_completeness": <1-5>
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
            authors = self.extract_authors(all_results[repo_name])

            # Validate ownership sums to 100%
            validation = validate_ownership_percentages(authors)
            if not validation["valid"]:
                failures.extend(validation["issues"])

            # Check expected author count
            expected_count = expected.get("author_count")
            if expected_count is not None:
                actual_count = len(authors)
                if actual_count != expected_count:
                    failures.append(
                        f"{repo_name}: expected {expected_count} authors, found {actual_count}"
                    )

        return len(failures) == 0, failures
