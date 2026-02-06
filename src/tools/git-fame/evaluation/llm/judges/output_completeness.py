"""Output Completeness Judge - Evaluates overall output completeness."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class OutputCompletenessJudge(BaseJudge):
    """Evaluates the overall completeness of git-fame output.

    Validates that:
    - All expected sections are present
    - Author list is complete and non-empty
    - Summary metrics are all populated
    - No critical data is missing
    """

    @property
    def dimension_name(self) -> str:
        return "output_completeness"

    @property
    def weight(self) -> float:
        return 0.10  # 10% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis and assess output completeness."""
        all_results = self.load_all_analysis_results()
        if not all_results:
            return {"error": f"No analysis files found in {self.output_dir}"}

        completeness_analysis: list[dict] = []

        for repo_name, repo_data in all_results.items():
            results = self.extract_results(repo_data)
            authors = self.extract_authors(repo_data)
            summary = self.extract_summary(repo_data)

            # Check sections present
            sections = {
                "summary": bool(summary),
                "authors": bool(authors),
                "provenance": bool(results.get("provenance")),
            }

            # Check author list quality
            author_quality = {
                "count": len(authors),
                "has_names": all(a.get("name") for a in authors),
                "has_loc": all(a.get("surviving_loc") is not None for a in authors),
                "has_ownership": all(a.get("ownership_pct") is not None for a in authors),
                "has_commits": all(a.get("commit_count") is not None for a in authors),
            }

            # Check summary quality
            summary_quality = {
                "has_author_count": "author_count" in summary,
                "has_total_loc": "total_loc" in summary,
                "has_hhi": "hhi_index" in summary,
                "has_bus_factor": "bus_factor" in summary,
                "has_top_author_pct": "top_author_pct" in summary,
            }

            # Check for error conditions
            has_error = "error" in results
            error_message = results.get("error", "")

            # Calculate completeness scores
            section_score = sum(sections.values()) / len(sections) * 100 if sections else 0
            author_score = sum(author_quality.values()) / len(author_quality) * 100 if author_quality else 0
            summary_score = sum(summary_quality.values()) / len(summary_quality) * 100 if summary_quality else 0

            # Overall score (weighted)
            overall_score = (
                section_score * 0.2 +
                author_score * 0.5 +
                summary_score * 0.3
            )

            completeness_analysis.append({
                "repo": repo_name,
                "sections": sections,
                "author_quality": author_quality,
                "summary_quality": summary_quality,
                "has_error": has_error,
                "error_message": error_message if has_error else None,
                "scores": {
                    "section_score_pct": round(section_score, 1),
                    "author_score_pct": round(author_score, 1),
                    "summary_score_pct": round(summary_score, 1),
                    "overall_score_pct": round(overall_score, 1),
                },
            })

        # Calculate overall metrics
        total_repos = len(completeness_analysis)
        repos_with_errors = sum(1 for a in completeness_analysis if a["has_error"])
        avg_score = (
            sum(a["scores"]["overall_score_pct"] for a in completeness_analysis) / total_repos
            if total_repos > 0 else 0
        )
        fully_complete = sum(
            1 for a in completeness_analysis
            if a["scores"]["overall_score_pct"] >= 95
        )

        evidence = {
            "total_repos": total_repos,
            "repos_with_errors": repos_with_errors,
            "error_rate_pct": round(repos_with_errors / total_repos * 100, 1) if total_repos > 0 else 0,
            "avg_completeness_score_pct": round(avg_score, 1),
            "fully_complete_repos": fully_complete,
            "full_completeness_rate_pct": round(fully_complete / total_repos * 100, 1) if total_repos > 0 else 0,
            "completeness_analysis": completeness_analysis,
            "evaluation_mode": self.evaluation_mode,
        }

        # Load ground truth for comparison if available
        ground_truth = self.load_ground_truth()
        if ground_truth:
            gt_comparison = []
            for analysis in completeness_analysis:
                repo_name = analysis["repo"]
                if repo_name in ground_truth:
                    expected = ground_truth[repo_name].get("expected", {})
                    expected_author_count = expected.get("author_count")
                    actual_author_count = analysis["author_quality"]["count"]

                    if expected_author_count is not None:
                        gt_comparison.append({
                            "repo": repo_name,
                            "expected_author_count": expected_author_count,
                            "actual_author_count": actual_author_count,
                            "match": expected_author_count == actual_author_count,
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
            evidence["interpretation_guidance"] = "Evaluate output completeness."

        return evidence

    def get_default_prompt(self) -> str:
        """Return the default prompt template if file doesn't exist."""
        return """# Output Completeness Evaluation

You are evaluating the overall completeness of git-fame analysis output.

## Background

Complete git-fame output should include:
- **Summary Section**: Aggregate metrics (author_count, total_loc, hhi_index, bus_factor)
- **Authors Section**: List of all authors with their metrics
- **Provenance Section**: Tool information and command used
- **No Errors**: Clean execution without error conditions

## Task

Evaluate the completeness of git-fame output across all analyzed repositories.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

1. **Section Presence (25%)**: Are all sections present?
   - 5: All sections present in all repos
   - 4: Minor sections missing in <5% of repos
   - 3: Some sections missing (5-15%)
   - 2: Many sections missing (15-30%)
   - 1: Critical sections missing (>30%)

2. **Author Data Quality (40%)**: Is author data complete?
   - 5: All authors have all required fields
   - 4: >95% of authors complete
   - 3: 85-95% complete
   - 2: 70-85% complete
   - 1: <70% complete

3. **Summary Data Quality (25%)**: Are summary metrics present?
   - 5: All summary metrics present and valid
   - 4: >95% of metrics present
   - 3: 85-95% present
   - 2: 70-85% present
   - 1: <70% present

4. **Error Rate (10%)**: Are there analysis errors?
   - 5: No errors in any repo
   - 4: Errors in <5% of repos
   - 3: Errors in 5-15% of repos
   - 2: Errors in 15-30% of repos
   - 1: Errors in >30% of repos

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific evidence points>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "section_presence": <1-5>,
    "author_data_quality": <1-5>,
    "summary_data_quality": <1-5>,
    "error_rate": <1-5>
  }
}
"""

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run ground truth assertions before LLM evaluation."""
        failures = []
        all_results = self.load_all_analysis_results()

        for repo_name, repo_data in all_results.items():
            results = self.extract_results(repo_data)
            authors = self.extract_authors(repo_data)
            summary = self.extract_summary(repo_data)

            # Check for errors
            if "error" in results:
                failures.append(f"{repo_name}: has error - {results['error']}")

            # Check authors present
            if not authors:
                failures.append(f"{repo_name}: no authors found")

            # Check summary present
            if not summary:
                failures.append(f"{repo_name}: no summary found")

        return len(failures) == 0, failures
