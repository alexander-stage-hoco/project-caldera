"""Semantic detection judge for PMD CPD evaluation."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class SemanticDetectionJudge(BaseJudge):
    """Judge that evaluates semantic duplication detection.

    Weight: 25%

    Evaluates:
    - Does --ignore-identifiers mode detect renamed variable clones?
    - Does --ignore-literals mode detect constant-changed clones?
    - Are Type 2 clones (near duplicates) properly identified?
    """

    @property
    def dimension_name(self) -> str:
        return "semantic_detection"

    @property
    def weight(self) -> float:
        return 0.25

    def get_default_prompt(self) -> str:
        return """You are an expert code quality evaluator assessing PMD CPD's semantic duplication detection capabilities.

## Task
Evaluate how well CPD detects semantic duplicates - code that has the same logic but different variable names or literal values. Score from 1-5 where:
- 5: Excellent - Accurately detects Type 2 clones with renamed vars/different literals
- 4: Good - Detects most semantic duplicates
- 3: Acceptable - Some semantic detection capability
- 2: Poor - Limited semantic detection
- 1: Very Poor - Only detects exact matches

## Evidence
{{ evidence }}

## Instructions
1. Check if semantic mode flags (ignore_identifiers, ignore_literals) are enabled
2. Review if files named "semantic_dup_*" show expected clones
3. Compare standard vs semantic mode results if available

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
    "identifier_detection": <1-5>,
    "literal_detection": <1-5>,
    "type2_clone_detection": <1-5>
  }
}
```"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence for evaluation."""
        results = self.load_all_analysis_results()

        evidence = {
            "semantic_mode_enabled": False,
            "ignore_identifiers": False,
            "ignore_literals": False,
            "semantic_files_detected": [],
            "standard_vs_semantic": {},
        }

        for repo_name, data in results.items():
            metadata = data.get("metadata", {})
            evidence["ignore_identifiers"] = metadata.get("ignore_identifiers", False)
            evidence["ignore_literals"] = metadata.get("ignore_literals", False)
            evidence["semantic_mode_enabled"] = (
                evidence["ignore_identifiers"] or evidence["ignore_literals"]
            )

            # Find semantic test files
            for f in data.get("files", []):
                path = f.get("path", "")
                if "semantic" in path.lower():
                    evidence["semantic_files_detected"].append({
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
