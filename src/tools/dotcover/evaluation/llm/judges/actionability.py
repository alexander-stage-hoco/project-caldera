"""Actionability Judge for dotCover evaluation.

Evaluates how actionable the coverage data is for improving test coverage.
"""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class ActionabilityJudge(BaseJudge):
    """Evaluates actionability of coverage data for test improvement.

    Assesses:
    - Low-coverage method identification
    - Uncovered code detection
    - Priority ranking usefulness
    - Improvement recommendations

    Sub-scores:
    - low_coverage_identification (25%)
    - uncovered_detection (25%)
    - priority_ranking (25%)
    - improvement_guidance (25%)
    """

    @property
    def dimension_name(self) -> str:
        return "actionability"

    @property
    def weight(self) -> float:
        return 0.25

    def get_default_prompt(self) -> str:
        return """# Coverage Actionability Evaluation

You are evaluating how actionable the dotCover coverage output is for improving test coverage.

## Evaluation Context

{{ interpretation_guidance }}

### Evaluation Mode
{{ evaluation_mode }}

**Focus**: Does the output help developers identify WHERE to add tests?

## Evidence to Review

### Coverage Summary
{{ coverage_summary }}

### Low Coverage Methods (< 50%)
{{ low_coverage_methods }}

### Uncovered Types
{{ uncovered_types }}

### Coverage Distribution
{{ coverage_distribution }}

### Ground Truth Expected Findings
{{ ground_truth_findings }}

## Evaluation Criteria

### Score 5 (Excellent)
- Clearly identifies all methods with < 50% coverage
- Provides specific type/method names for targeting
- Coverage data enables prioritization by impact
- Easy to identify "quick wins" for coverage improvement

### Score 4 (Good)
- Identifies most low-coverage areas
- Type/method granularity allows targeted testing
- Coverage percentages enable comparison

### Score 3 (Acceptable)
- Basic identification of uncovered areas
- Some granularity for test targeting
- Percentages present but limited context

### Score 2 (Poor)
- Limited identification of problem areas
- Too coarse-grained for actionable testing
- Missing key coverage gaps

### Score 1 (Unacceptable)
- No useful information for test improvement
- Cannot identify where tests are needed
- Data too aggregated or missing

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
        "low_coverage_identification": <1-5>,
        "uncovered_detection": <1-5>,
        "priority_ranking": <1-5>,
        "improvement_guidance": <1-5>
    }
}
```
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect actionability-related evidence from analysis outputs."""
        evidence: dict[str, Any] = {
            "evaluation_mode": self.evaluation_mode,
            "coverage_summary": {},
            "low_coverage_methods": [],
            "uncovered_types": [],
            "coverage_distribution": {
                "0-25%": 0,
                "25-50%": 0,
                "50-75%": 0,
                "75-100%": 0,
            },
            "ground_truth_findings": {},
        }

        # Load all analysis results
        all_results = self.load_all_analysis_results()

        for run_id, output in all_results.items():
            data = self.unwrap_output(output)
            summary = data.get("summary", {})
            evidence["coverage_summary"][run_id] = summary

            # Find low coverage methods (< 50%)
            methods = data.get("methods", [])
            for m in methods:
                pct = m.get("statement_coverage_pct", 0)
                total = m.get("total_statements", 0)

                # Categorize by coverage range
                if pct < 25:
                    evidence["coverage_distribution"]["0-25%"] += 1
                elif pct < 50:
                    evidence["coverage_distribution"]["25-50%"] += 1
                elif pct < 75:
                    evidence["coverage_distribution"]["50-75%"] += 1
                else:
                    evidence["coverage_distribution"]["75-100%"] += 1

                # Collect low coverage methods
                if pct < 50 and total > 0:
                    evidence["low_coverage_methods"].append({
                        "run_id": run_id,
                        "type": m.get("type_name"),
                        "method": m.get("name"),
                        "coverage_pct": pct,
                        "total_statements": total,
                        "uncovered_statements": total - m.get("covered_statements", 0),
                    })

            # Find uncovered types (0% coverage)
            types = data.get("types", [])
            for t in types:
                if t.get("statement_coverage_pct", 0) == 0 and t.get("total_statements", 0) > 0:
                    evidence["uncovered_types"].append({
                        "run_id": run_id,
                        "assembly": t.get("assembly"),
                        "namespace": t.get("namespace"),
                        "type": t.get("name"),
                        "total_statements": t.get("total_statements"),
                    })

        # Sort by impact (uncovered statements)
        evidence["low_coverage_methods"].sort(
            key=lambda x: x.get("uncovered_statements", 0),
            reverse=True
        )
        evidence["low_coverage_methods"] = evidence["low_coverage_methods"][:20]

        evidence["uncovered_types"].sort(
            key=lambda x: x.get("total_statements", 0),
            reverse=True
        )
        evidence["uncovered_types"] = evidence["uncovered_types"][:10]

        # Load ground truth for expected findings
        ground_truth = self.load_ground_truth()
        if ground_truth:
            evidence["ground_truth_findings"] = {
                "expected_low_coverage": ground_truth.get("expected_low_coverage_methods", []),
                "expected_uncovered": ground_truth.get("expected_uncovered_types", []),
            }

        # Add interpretation guidance
        if self.evaluation_mode == "real_world":
            synthetic_context = self.load_synthetic_evaluation_context()
            if synthetic_context:
                evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                    synthetic_context
                )
            else:
                evidence["interpretation_guidance"] = "Evaluate based on data utility"
        else:
            evidence["interpretation_guidance"] = "Strict ground truth evaluation"

        return evidence

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Check actionability-related ground truth assertions."""
        failures = []

        all_results = self.load_all_analysis_results()
        ground_truth = self.load_ground_truth()

        if not ground_truth:
            return True, []

        # Check expected low coverage methods were identified
        expected_low = ground_truth.get("expected_low_coverage_methods", [])
        for expected in expected_low:
            found = False
            for run_id, output in all_results.items():
                data = self.unwrap_output(output)
                methods = data.get("methods", [])
                for m in methods:
                    if (m.get("name") == expected.get("name") and
                        m.get("type_name") == expected.get("type")):
                        if m.get("statement_coverage_pct", 100) < 50:
                            found = True
                            break
                if found:
                    break
            if not found and expected_low:
                failures.append(
                    f"Expected low-coverage method not identified: {expected.get('type')}.{expected.get('name')}"
                )

        # Check expected uncovered types
        expected_uncovered = ground_truth.get("expected_uncovered_types", [])
        for expected in expected_uncovered:
            found = False
            for run_id, output in all_results.items():
                data = self.unwrap_output(output)
                types = data.get("types", [])
                for t in types:
                    if t.get("name") == expected.get("name"):
                        if t.get("statement_coverage_pct", 100) == 0:
                            found = True
                            break
                if found:
                    break
            if not found and expected_uncovered:
                failures.append(
                    f"Expected uncovered type not identified: {expected.get('name')}"
                )

        return len(failures) == 0, failures

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline."""
        return super().evaluate()
