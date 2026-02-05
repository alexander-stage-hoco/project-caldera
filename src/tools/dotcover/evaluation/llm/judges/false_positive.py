"""False Positive Judge for dotCover evaluation.

Evaluates the accuracy of uncovered code detection (avoiding false positives).
"""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class FalsePositiveJudge(BaseJudge):
    """Evaluates false positive rate in coverage detection.

    Assesses:
    - Uncovered line verification
    - Coverage attribution accuracy
    - Edge case handling
    - Instrumentation reliability

    Sub-scores:
    - uncovered_line_accuracy (25%)
    - coverage_attribution (25%)
    - edge_case_handling (25%)
    - instrumentation_reliability (25%)
    """

    @property
    def dimension_name(self) -> str:
        return "false_positive"

    @property
    def weight(self) -> float:
        return 0.20

    def get_default_prompt(self) -> str:
        return """# False Positive Evaluation

You are evaluating the false positive rate in dotCover's coverage detection.

## Evaluation Context

{{ interpretation_guidance }}

### Evaluation Mode
{{ evaluation_mode }}

**Focus**: Are "uncovered" lines truly uncovered? Are "covered" lines truly covered?

## Evidence to Review

### Coverage Summary
{{ coverage_summary }}

### Known Covered Code (Ground Truth)
{{ known_covered_code }}

### Reported Coverage Status
{{ reported_coverage }}

### Edge Cases
{{ edge_cases }}

### Anomalies Detected
{{ anomalies }}

## Evaluation Criteria

### Score 5 (Excellent)
- No false positives on verified covered code
- Accurate coverage attribution for all scenarios
- Handles edge cases correctly (generics, async, lambdas)
- Consistent instrumentation results

### Score 4 (Good)
- Rare false positives (< 2% error rate)
- Minor edge case handling issues
- Overall reliable coverage data

### Score 3 (Acceptable)
- Some false positives present (2-5% error rate)
- Known edge case limitations
- Usable but requires verification

### Score 2 (Poor)
- Significant false positives (5-10% error rate)
- Multiple edge case failures
- Coverage data requires manual verification

### Score 1 (Unacceptable)
- Unreliable coverage detection (> 10% error rate)
- Systematic false positives
- Coverage data cannot be trusted

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
        "uncovered_line_accuracy": <1-5>,
        "coverage_attribution": <1-5>,
        "edge_case_handling": <1-5>,
        "instrumentation_reliability": <1-5>
    }
}
```
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect false positive-related evidence from analysis outputs."""
        evidence: dict[str, Any] = {
            "evaluation_mode": self.evaluation_mode,
            "coverage_summary": {},
            "known_covered_code": [],
            "reported_coverage": [],
            "edge_cases": [],
            "anomalies": [],
        }

        # Load all analysis results
        all_results = self.load_all_analysis_results()
        ground_truth = self.load_ground_truth()

        for run_id, output in all_results.items():
            data = self.unwrap_output(output)
            summary = data.get("summary", {})
            evidence["coverage_summary"][run_id] = summary

            # Check for coverage anomalies
            methods = data.get("methods", [])
            for m in methods:
                covered = m.get("covered_statements", 0)
                total = m.get("total_statements", 0)
                pct = m.get("statement_coverage_pct", 0)

                # Anomaly: 100% coverage but covered != total
                if pct == 100 and covered != total and total > 0:
                    evidence["anomalies"].append({
                        "run_id": run_id,
                        "type": "percentage_mismatch",
                        "method": m.get("name"),
                        "covered": covered,
                        "total": total,
                        "pct": pct,
                    })

                # Anomaly: 0% coverage but covered > 0
                if pct == 0 and covered > 0:
                    evidence["anomalies"].append({
                        "run_id": run_id,
                        "type": "zero_pct_with_coverage",
                        "method": m.get("name"),
                        "covered": covered,
                        "total": total,
                    })

            # Check types for edge cases (generics, nested classes)
            types = data.get("types", [])
            for t in types:
                type_name = t.get("name", "")
                # Generic types
                if "<" in type_name or "`" in type_name:
                    evidence["edge_cases"].append({
                        "run_id": run_id,
                        "type": "generic",
                        "name": type_name,
                        "coverage_pct": t.get("statement_coverage_pct"),
                    })
                # Nested classes
                if "+" in type_name or "/" in type_name:
                    evidence["edge_cases"].append({
                        "run_id": run_id,
                        "type": "nested",
                        "name": type_name,
                        "coverage_pct": t.get("statement_coverage_pct"),
                    })

            # Sample reported coverage for verification
            for m in methods[:10]:
                evidence["reported_coverage"].append({
                    "run_id": run_id,
                    "type": m.get("type_name"),
                    "method": m.get("name"),
                    "covered": m.get("covered_statements"),
                    "total": m.get("total_statements"),
                })

        # Load ground truth for known covered code
        if ground_truth:
            known_covered = ground_truth.get("known_covered_methods", [])
            for item in known_covered:
                evidence["known_covered_code"].append(item)

        # Limit collections
        evidence["edge_cases"] = evidence["edge_cases"][:15]
        evidence["anomalies"] = evidence["anomalies"][:10]

        # Add interpretation guidance
        if self.evaluation_mode == "real_world":
            synthetic_context = self.load_synthetic_evaluation_context()
            if synthetic_context:
                evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                    synthetic_context
                )
            else:
                evidence["interpretation_guidance"] = "Evaluate based on data consistency"
        else:
            evidence["interpretation_guidance"] = "Strict ground truth evaluation"

        return evidence

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Check false positive-related ground truth assertions."""
        failures = []

        all_results = self.load_all_analysis_results()
        ground_truth = self.load_ground_truth()

        # Check for known coverage anomalies
        for run_id, output in all_results.items():
            data = self.unwrap_output(output)
            methods = data.get("methods", [])

            for m in methods:
                covered = m.get("covered_statements", 0)
                total = m.get("total_statements", 0)
                pct = m.get("statement_coverage_pct", 0)

                # Critical: covered > total is always a false positive
                if covered > total:
                    failures.append(
                        f"{run_id}: False positive - {m.get('name')} has covered ({covered}) > total ({total})"
                    )

                # Critical: percentage doesn't match counts
                if total > 0:
                    expected_pct = (covered / total) * 100
                    if abs(pct - expected_pct) > 1:
                        failures.append(
                            f"{run_id}: Calculation error - {m.get('name')} pct={pct} but expected={expected_pct:.1f}"
                        )

        # Check ground truth known covered code
        if ground_truth:
            known_covered = ground_truth.get("known_covered_methods", [])
            for expected in known_covered:
                # Verify these are reported as covered
                for run_id, output in all_results.items():
                    data = self.unwrap_output(output)
                    methods = data.get("methods", [])
                    for m in methods:
                        if (m.get("name") == expected.get("name") and
                            m.get("type_name") == expected.get("type")):
                            if m.get("covered_statements", 0) == 0:
                                failures.append(
                                    f"False positive: {expected.get('type')}.{expected.get('name')} "
                                    f"is known covered but reported as uncovered"
                                )

        return len(failures) == 0, failures

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline."""
        return super().evaluate()
