"""Duplication accuracy judge for PMD CPD evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class DuplicationAccuracyJudge(BaseJudge):
    """Judge that evaluates the accuracy of duplication detection.

    Weight: 35%

    Evaluates:
    - Are the detected clones genuine duplicates?
    - Are important duplicates being missed?
    - Are the line counts and locations accurate?
    """

    @property
    def dimension_name(self) -> str:
        return "duplication_accuracy"

    @property
    def weight(self) -> float:
        return 0.35

    def get_default_prompt(self) -> str:
        return """You are an expert code quality evaluator assessing the accuracy of PMD CPD's code duplication detection.

## Task
Evaluate the accuracy of code clone detection results. Score from 1-5 where:
- 5: Excellent - All detected clones are genuine, no false positives
- 4: Good - Most clones are genuine with minor issues
- 3: Acceptable - Some false positives or missed duplicates
- 2: Poor - Significant accuracy issues
- 1: Very Poor - Mostly incorrect results

## Evidence
{{ evidence }}

## Instructions
1. Review the detected duplications
2. Assess if the clones appear to be genuine code duplicates
3. Check if clone line counts seem reasonable
4. Look for obvious false positives or misses

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
    "genuine_clones": <1-5>,
    "false_positive_rate": <1-5>,
    "location_accuracy": <1-5>
  }
}
```"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence for evaluation."""
        results = self.load_all_analysis_results()

        evidence: dict[str, Any] = {
            "analysis_summary": {},
            "sample_duplications": [],
            "file_metrics": [],
            "evaluation_mode": self.evaluation_mode,
        }

        for repo_name, data in results.items():
            # Add summary
            evidence["analysis_summary"] = {
                "total_files": data.get("summary", {}).get("total_files", 0),
                "total_clones": data.get("summary", {}).get("total_clones", 0),
                "duplication_percentage": data.get("summary", {}).get("duplication_percentage", 0),
            }

            # Sample duplications (limit to 5)
            duplications = data.get("duplications", [])[:5]
            for dup in duplications:
                evidence["sample_duplications"].append({
                    "clone_id": dup.get("clone_id"),
                    "lines": dup.get("lines"),
                    "tokens": dup.get("tokens"),
                    "occurrences": len(dup.get("occurrences", [])),
                    "code_fragment": dup.get("code_fragment", "")[:200],
                })

            # Sample file metrics (limit to 10)
            files = data.get("files", [])[:10]
            for f in files:
                evidence["file_metrics"].append({
                    "path": f.get("path"),
                    "total_lines": f.get("total_lines"),
                    "duplicate_lines": f.get("duplicate_lines"),
                    "duplication_percentage": f.get("duplication_percentage"),
                })

        # Add synthetic baseline context for real-world evaluation
        if self.evaluation_mode == "real_world":
            synthetic_context = self.load_synthetic_evaluation_context()
            if synthetic_context:
                evidence["synthetic_baseline"] = synthetic_context
                evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                    synthetic_context
                )
            else:
                evidence["synthetic_baseline"] = "No synthetic baseline available"
                evidence["interpretation_guidance"] = (
                    "Evaluate based on ground truth comparison only"
                )
        else:
            evidence["synthetic_baseline"] = (
                "N/A - synthetic mode uses direct ground truth comparison"
            )
            evidence["interpretation_guidance"] = "Strict ground truth evaluation"

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
