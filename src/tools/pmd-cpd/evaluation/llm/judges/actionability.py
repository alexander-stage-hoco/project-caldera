"""Actionability judge for PMD CPD evaluation."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class ActionabilityJudge(BaseJudge):
    """Judge that evaluates the actionability of duplication reports.

    Weight: 20%

    Evaluates:
    - Are the reports useful for developers to take action?
    - Is there enough context to understand what to refactor?
    - Are the metrics and summaries helpful?
    """

    @property
    def dimension_name(self) -> str:
        return "actionability"

    @property
    def weight(self) -> float:
        return 0.20

    def get_default_prompt(self) -> str:
        return """You are an expert code quality evaluator assessing the actionability of PMD CPD's duplication reports.

## Task
Evaluate how useful the CPD reports are for developers to take action on code duplication. Score from 1-5 where:
- 5: Excellent - Reports clearly guide refactoring with specific locations and context
- 4: Good - Reports are useful with good location info
- 3: Acceptable - Basic actionable information
- 2: Poor - Hard to act on the reports
- 1: Very Poor - Reports are not actionable

## Evidence
{{ evidence }}

## Instructions
1. Review the report structure and information provided
2. Check if line numbers and file paths are clear
3. Evaluate if the code fragments help understand the duplication
4. Assess if the summaries help prioritize which duplicates to fix

## Response Format
Respond with a JSON object:
```json
{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "Your detailed reasoning",
  "evidence_cited": ["list of evidence you used"],
  "recommendations": ["list of recommendations"],
  "sub_scores": {
    "location_clarity": <1-5>,
    "context_provided": <1-5>,
    "prioritization_support": <1-5>
  }
}
```"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence for evaluation."""
        results = self.load_all_analysis_results()

        evidence = {
            "report_structure": {},
            "sample_clone_details": [],
            "summary_quality": {},
            "metadata_available": {},
        }

        for repo_name, data in results.items():
            # Report structure
            evidence["report_structure"] = {
                "has_metadata": "metadata" in data,
                "has_summary": "summary" in data,
                "has_files": "files" in data,
                "has_duplications": "duplications" in data,
                "has_statistics": "statistics" in data,
            }

            # Metadata
            metadata = data.get("metadata", {})
            evidence["metadata_available"] = {
                "version": "version" in metadata,
                "cpd_version": "cpd_version" in metadata,
                "min_tokens": "min_tokens" in metadata,
                "analyzed_at": "analyzed_at" in metadata,
                "elapsed_seconds": "elapsed_seconds" in metadata,
            }

            # Summary quality
            summary = data.get("summary", {})
            evidence["summary_quality"] = {
                "has_total_files": "total_files" in summary,
                "has_total_clones": "total_clones" in summary,
                "has_duplication_percentage": "duplication_percentage" in summary,
                "has_cross_file_clones": "cross_file_clones" in summary,
            }

            # Sample clone details (check what info is provided)
            duplications = data.get("duplications", [])[:3]
            for dup in duplications:
                clone_detail = {
                    "has_clone_id": "clone_id" in dup,
                    "has_lines": "lines" in dup,
                    "has_tokens": "tokens" in dup,
                    "has_code_fragment": bool(dup.get("code_fragment")),
                    "occurrence_fields": [],
                }

                for occ in dup.get("occurrences", [])[:1]:
                    clone_detail["occurrence_fields"] = list(occ.keys())

                evidence["sample_clone_details"].append(clone_detail)

        return evidence
    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline.

        Delegates to base class implementation which:
        1. Collects evidence via collect_evidence()
        2. Builds prompt from template
        3. Invokes Claude for evaluation
        4. Parses response into JudgeResult
        """
        return super().evaluate()
