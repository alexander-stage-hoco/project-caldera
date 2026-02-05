"""Accuracy Judge for dotCover evaluation.

Evaluates the correctness of coverage percentages and statement counts.
"""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class AccuracyJudge(BaseJudge):
    """Evaluates coverage percentage correctness.

    Assesses:
    - Statement count accuracy
    - Coverage percentage calculation
    - Assembly/Type/Method totals consistency
    - Ground truth comparison

    Sub-scores:
    - statement_counts (25%)
    - percentage_accuracy (25%)
    - hierarchy_consistency (25%)
    - ground_truth_match (25%)
    """

    @property
    def dimension_name(self) -> str:
        return "accuracy"

    @property
    def weight(self) -> float:
        return 0.35

    def get_default_prompt(self) -> str:
        return """# Coverage Accuracy Evaluation

You are evaluating the accuracy of dotCover code coverage measurements.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

**Important**: When evaluation_mode is "real_world":
- Judge output quality: schema compliance, coverage calculations
- Verify that covered_statements <= total_statements invariant holds
- Check that percentages are correctly calculated (covered/total * 100)

## Evidence to Review

### Coverage Summary
{{ coverage_summary }}

### Assembly Coverage
{{ assembly_coverage }}

### Type Coverage Sample
{{ type_coverage_sample }}

### Method Coverage Sample
{{ method_coverage_sample }}

### Ground Truth Comparison
{{ ground_truth_comparison }}

## Evaluation Criteria

### For Synthetic Repos (with ground truth):

#### Score 5 (Excellent)
- All coverage percentages match ground truth within 1%
- Statement counts are exact matches
- No invariant violations (covered <= total)
- Hierarchy totals sum correctly

#### Score 4 (Good)
- Coverage percentages within 5% of ground truth
- Minor statement count discrepancies
- No invariant violations

#### Score 3 (Acceptable)
- Coverage percentages within 10% of ground truth
- Some count discrepancies
- No critical invariant violations

#### Score 2 (Poor)
- Large percentage deviations (>10%)
- Multiple count discrepancies
- Some invariant violations

#### Score 1 (Unacceptable)
- Completely incorrect coverage data
- Major invariant violations
- Data appears corrupted or unusable

### For Real-World Repos:

#### Score 5 (Excellent)
- All invariants hold (covered <= total, 0 <= pct <= 100)
- Percentages correctly calculated
- Complete schema compliance

#### Score 4 (Good)
- Minor calculation rounding issues
- All data structurally correct

#### Score 3 (Acceptable)
- Some schema issues but data usable

#### Score 2 (Poor)
- Multiple schema or calculation issues

#### Score 1 (Failing)
- Broken output, invalid data

## Response Format

Respond with JSON:
```json
{
    "score": <1-5>,
    "confidence": <0.0-1.0>,
    "reasoning": "<detailed explanation>",
    "evidence_cited": ["<specific findings>"],
    "recommendations": ["<improvements>"],
    "sub_scores": {
        "statement_counts": <1-5>,
        "percentage_accuracy": <1-5>,
        "hierarchy_consistency": <1-5>,
        "ground_truth_match": <1-5>
    }
}
```
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect accuracy-related evidence from analysis outputs."""
        evidence: dict[str, Any] = {
            "evaluation_mode": self.evaluation_mode,
            "coverage_summary": {},
            "assembly_coverage": [],
            "type_coverage_sample": [],
            "method_coverage_sample": [],
            "ground_truth_comparison": {},
        }

        # Load all analysis results
        all_results = self.load_all_analysis_results()

        for run_id, output in all_results.items():
            data = self.unwrap_output(output)
            summary = data.get("summary", {})
            evidence["coverage_summary"][run_id] = summary

            # Collect assembly data
            assemblies = data.get("assemblies", [])
            for asm in assemblies[:5]:
                evidence["assembly_coverage"].append({
                    "run_id": run_id,
                    "name": asm.get("name"),
                    "covered": asm.get("covered_statements"),
                    "total": asm.get("total_statements"),
                    "pct": asm.get("statement_coverage_pct"),
                })

            # Collect type samples
            types = data.get("types", [])
            for t in types[:10]:
                evidence["type_coverage_sample"].append({
                    "run_id": run_id,
                    "name": t.get("name"),
                    "assembly": t.get("assembly"),
                    "covered": t.get("covered_statements"),
                    "total": t.get("total_statements"),
                    "pct": t.get("statement_coverage_pct"),
                })

            # Collect method samples
            methods = data.get("methods", [])
            for m in methods[:15]:
                evidence["method_coverage_sample"].append({
                    "run_id": run_id,
                    "type": m.get("type_name"),
                    "name": m.get("name"),
                    "covered": m.get("covered_statements"),
                    "total": m.get("total_statements"),
                    "pct": m.get("statement_coverage_pct"),
                })

        # Load ground truth for comparison
        ground_truth = self.load_ground_truth()
        if ground_truth:
            evidence["ground_truth_comparison"] = {
                "expected_coverage": ground_truth.get("expected_coverage", {}),
                "expected_assemblies": ground_truth.get("expected_assemblies", []),
            }

        # Inject synthetic baseline context for real-world evaluation
        if self.evaluation_mode == "real_world":
            synthetic_context = self.load_synthetic_evaluation_context()
            if synthetic_context:
                evidence["synthetic_baseline"] = synthetic_context
                evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                    synthetic_context
                )
            else:
                evidence["synthetic_baseline"] = "No synthetic baseline available"
                evidence["interpretation_guidance"] = "Evaluate based on data integrity only"
        else:
            evidence["synthetic_baseline"] = "N/A - synthetic mode uses direct ground truth"
            evidence["interpretation_guidance"] = "Strict ground truth evaluation"

        return evidence

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Check accuracy-related ground truth assertions."""
        failures = []

        all_results = self.load_all_analysis_results()
        ground_truth = self.load_ground_truth()

        for run_id, output in all_results.items():
            data = self.unwrap_output(output)
            summary = data.get("summary", {})

            # Check invariants
            covered = summary.get("covered_statements", 0)
            total = summary.get("total_statements", 0)
            pct = summary.get("statement_coverage_pct", 0)

            if covered > total:
                failures.append(f"{run_id}: covered_statements ({covered}) > total_statements ({total})")

            if pct < 0 or pct > 100:
                failures.append(f"{run_id}: statement_coverage_pct ({pct}) out of range [0, 100]")

            # Check percentage calculation
            if total > 0:
                expected_pct = (covered / total) * 100
                if abs(pct - expected_pct) > 0.1:
                    failures.append(f"{run_id}: percentage mismatch - expected {expected_pct:.1f}, got {pct}")

        # Check ground truth expectations
        if ground_truth:
            expected = ground_truth.get("expected_coverage", {})
            for run_id, expected_pct in expected.items():
                if run_id in all_results:
                    actual_data = self.unwrap_output(all_results[run_id])
                    actual_pct = actual_data.get("summary", {}).get("statement_coverage_pct", 0)
                    if abs(actual_pct - expected_pct) > 5:
                        failures.append(
                            f"{run_id}: expected coverage ~{expected_pct}%, got {actual_pct}%"
                        )

        return len(failures) == 0, failures

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline."""
        return super().evaluate()
