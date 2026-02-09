"""Actionability Judge - Evaluates whether findings are actionable."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult
from .utils import calculate_knowledge_risk_metrics


class ActionabilityJudge(BaseJudge):
    """Evaluates whether git-blame-scanner findings are actionable.

    Validates that:
    - Knowledge silos are clearly identified
    - High-risk files are surfaced appropriately
    - Recommendations can drive concrete actions (e.g., code review, pairing)
    """

    @property
    def dimension_name(self) -> str:
        return "actionability"

    @property
    def weight(self) -> float:
        return 0.25  # 25% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis and assess actionability."""
        all_results = self.load_all_analysis_results()
        if not all_results:
            return {"error": f"No analysis files found in {self.output_dir}"}

        # Aggregate risk data from all repos
        total_files = 0
        knowledge_silos: list[dict] = []
        high_concentration_files: list[dict] = []
        stale_files: list[dict] = []
        repo_summaries: list[dict] = []

        for repo_name, repo_data in all_results.items():
            files = self.extract_files(repo_data)
            summary = self.extract_summary(repo_data)
            authors = self.extract_authors(repo_data)

            total_files += len(files)

            # Calculate risk metrics
            risk_metrics = calculate_knowledge_risk_metrics(files)

            # Collect knowledge silos
            for f in files:
                if (
                    f.get("unique_authors", 0) == 1
                    and f.get("total_lines", 0) > 100
                ):
                    knowledge_silos.append({
                        "repo": repo_name,
                        "path": f.get("path", ""),
                        "total_lines": f.get("total_lines", 0),
                        "top_author": f.get("top_author", ""),
                    })

            # Collect high concentration files
            for f in files:
                if f.get("top_author_pct", 0) >= 80:
                    high_concentration_files.append({
                        "repo": repo_name,
                        "path": f.get("path", ""),
                        "top_author_pct": f.get("top_author_pct", 0),
                        "unique_authors": f.get("unique_authors", 0),
                    })

            # Collect stale files
            for f in files:
                if f.get("churn_90d", 0) == 0:
                    stale_files.append({
                        "repo": repo_name,
                        "path": f.get("path", ""),
                        "last_modified": f.get("last_modified", ""),
                        "total_lines": f.get("total_lines", 0),
                    })

            # Author exclusive files for bus factor analysis
            exclusive_authors = [
                a for a in authors if a.get("exclusive_files", 0) > 0
            ]

            repo_summaries.append({
                "repo": repo_name,
                "file_count": len(files),
                "knowledge_silo_count": risk_metrics["knowledge_silo_count"],
                "high_concentration_count": risk_metrics["high_concentration_count"],
                "stale_file_count": risk_metrics["stale_file_count"],
                "authors_with_exclusive_files": len(exclusive_authors),
                "single_author_pct": summary.get("single_author_pct", 0),
            })

        # Sort by severity for sampling
        knowledge_silos.sort(key=lambda x: x.get("total_lines", 0), reverse=True)
        high_concentration_files.sort(
            key=lambda x: x.get("top_author_pct", 0), reverse=True
        )

        evidence = {
            "total_repos": len(all_results),
            "total_files": total_files,
            "knowledge_silos_sample": knowledge_silos[:15],
            "high_concentration_sample": high_concentration_files[:15],
            "stale_files_sample": stale_files[:10],
            "repo_summaries": repo_summaries,
            "total_knowledge_silos": len(knowledge_silos),
            "total_high_concentration": len(high_concentration_files),
            "total_stale": len(stale_files),
            "evaluation_mode": self.evaluation_mode,
        }

        # Add synthetic context if available
        synthetic_context = self.load_synthetic_evaluation_context()
        if synthetic_context:
            evidence["synthetic_baseline"] = synthetic_context
            evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                synthetic_context
            )
        else:
            evidence["synthetic_baseline"] = "Not available"
            evidence["interpretation_guidance"] = (
                "Evaluate whether findings enable concrete team actions."
            )

        return evidence

    def get_default_prompt(self) -> str:
        """Return the default prompt template."""
        return """# Actionability Evaluation

You are an expert in code quality and team dynamics evaluating git-blame-scanner's actionability.

## Task

Evaluate whether the git-blame-scanner output provides actionable insights for reducing knowledge risk and improving team collaboration.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

1. **Knowledge Silo Identification (35%)**: Are knowledge silos clearly identified?
   - 5: All silos identified with file paths, authors, and line counts
   - 4: Most silos identified with key details
   - 3: Silos identified but missing some context
   - 2: Partial identification, missing key details
   - 1: Silos not effectively identified

2. **Risk Prioritization (35%)**: Are high-risk files surfaced appropriately?
   - 5: Clear prioritization by risk (size, concentration, staleness)
   - 4: Good prioritization with minor gaps
   - 3: Moderate prioritization
   - 2: Weak prioritization
   - 1: No effective prioritization

3. **Action Enablement (30%)**: Can findings drive concrete actions?
   - 5: Findings directly enable actions (pairing, reviews, documentation)
   - 4: Most findings are actionable
   - 3: Some actionable findings
   - 2: Limited actionability
   - 1: Findings not actionable

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific evidence points>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "silo_identification": <1-5>,
    "risk_prioritization": <1-5>,
    "action_enablement": <1-5>
  }
}
"""

    def run_heuristic_evaluation(self, evidence: dict[str, Any]) -> JudgeResult:
        """Run heuristic-based evaluation without LLM."""
        score = 3
        reasoning_parts = []

        # Check if knowledge silos are identified
        silos = evidence.get("total_knowledge_silos", 0)
        silo_sample = evidence.get("knowledge_silos_sample", [])

        if silos > 0 and len(silo_sample) > 0:
            # Check if samples have required fields
            has_details = all(
                s.get("path") and s.get("top_author") and s.get("total_lines")
                for s in silo_sample[:5]
            )
            if has_details:
                score += 1
                reasoning_parts.append("Knowledge silos well-documented with details")
        else:
            reasoning_parts.append("No knowledge silos to evaluate")

        # Check if high concentration files are identified
        high_conc = evidence.get("total_high_concentration", 0)
        if high_conc > 0:
            score += 0.5
            reasoning_parts.append(
                f"High concentration files identified ({high_conc})"
            )

        # Check repo summaries for risk metrics
        summaries = evidence.get("repo_summaries", [])
        if summaries:
            has_metrics = all(
                "single_author_pct" in s for s in summaries
            )
            if has_metrics:
                score += 0.5
                reasoning_parts.append("Risk metrics available per repository")

        return JudgeResult(
            dimension=self.dimension_name,
            score=min(5, round(score)),
            confidence=0.7,
            reasoning="; ".join(reasoning_parts) if reasoning_parts else "Heuristic evaluation",
            evidence_cited=[
                f"Total knowledge silos: {silos}",
                f"Total high concentration files: {high_conc}",
            ],
            recommendations=["Run with LLM for detailed evaluation"],
            raw_response="",
        )
