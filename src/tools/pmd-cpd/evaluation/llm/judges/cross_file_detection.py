"""Cross-file detection judge for PMD CPD evaluation."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class CrossFileDetectionJudge(BaseJudge):
    """Judge that evaluates cross-file duplication detection.

    Weight: 20%

    Evaluates:
    - Are duplicates spanning multiple files detected?
    - Are the file relationships properly linked?
    - Is the cross-file reporting clear and useful?
    """

    @property
    def dimension_name(self) -> str:
        return "cross_file_detection"

    @property
    def weight(self) -> float:
        return 0.20

    def get_default_prompt(self) -> str:
        return """You are an expert code quality evaluator assessing PMD CPD's cross-file duplication detection.

## Task
Evaluate how well CPD detects and reports duplicates that span multiple files. Score from 1-5 where:
- 5: Excellent - All cross-file clones detected with clear file relationships
- 4: Good - Most cross-file clones detected
- 3: Acceptable - Basic cross-file detection works
- 2: Poor - Misses many cross-file duplicates
- 1: Very Poor - Fails to detect cross-file clones

## Evidence
{{ evidence }}

## Instructions
1. Review the cross-file clone statistics
2. Check if cross_file_a/cross_file_b test files show expected clones
3. Verify occurrences show multiple distinct files

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
    "detection_rate": <1-5>,
    "file_linking": <1-5>,
    "reporting_clarity": <1-5>
  }
}
```"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence for evaluation."""
        results = self.load_all_analysis_results()

        evidence = {
            "cross_file_clone_count": 0,
            "total_clone_count": 0,
            "cross_file_clones": [],
            "cross_file_test_files": [],
        }

        for repo_name, data in results.items():
            duplications = data.get("duplications", [])
            evidence["total_clone_count"] = len(duplications)

            for dup in duplications:
                occurrences = dup.get("occurrences", [])
                files = set(occ.get("file", "") for occ in occurrences)

                if len(files) > 1:
                    evidence["cross_file_clone_count"] += 1
                    if len(evidence["cross_file_clones"]) < 5:
                        evidence["cross_file_clones"].append({
                            "clone_id": dup.get("clone_id"),
                            "lines": dup.get("lines"),
                            "files_involved": list(files),
                            "occurrence_count": len(occurrences),
                        })

            # Find cross-file test files
            for f in data.get("files", []):
                path = f.get("path", "")
                if "cross_file" in path.lower():
                    evidence["cross_file_test_files"].append({
                        "path": path,
                        "duplicate_blocks": f.get("duplicate_blocks", 0),
                        "duplication_percentage": f.get("duplication_percentage", 0),
                    })

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
