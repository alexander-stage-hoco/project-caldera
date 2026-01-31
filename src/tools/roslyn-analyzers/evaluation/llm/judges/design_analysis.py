"""Design Analysis Judge for Roslyn Analyzers evaluation."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class DesignAnalysisJudge(BaseJudge):
    """Evaluates design pattern and code quality detection.

    Assesses:
    - Encapsulation violations (CA1051, CA1040, CA1034)
    - Interface design issues (CA1040, CA1033)
    - Inheritance pattern problems (CA1501, CA1502)
    - Complexity detection (CA1502, CA1505)

    Sub-scores:
    - encapsulation (25%)
    - interface_design (25%)
    - inheritance (25%)
    - complexity (25%)
    """

    @property
    def dimension_name(self) -> str:
        return "design_analysis"

    @property
    def weight(self) -> float:
        return 0.25

    def get_default_prompt(self) -> str:
        return """# Design Analysis Evaluation

You are evaluating the design pattern and code quality detection capabilities of Roslyn Analyzers.

## Evidence to Review

### Design Summary
{{ design_summary }}

### Detection by Repository
{{ detection_by_repo }}

### Sample Violations
{{ violations_sample }}

### Ground Truth Comparison
{{ ground_truth_comparison }}

## Evaluation Criteria

### Score 5 (Excellent)
- Detects encapsulation violations (public fields, accessible members)
- Identifies empty interfaces and marker interfaces
- Catches deep inheritance hierarchies
- Accurately measures cyclomatic complexity
- Coverage >95% of design ground truth

### Score 4 (Good)
- Detects most encapsulation issues
- Identifies common interface problems
- Catches most inheritance concerns
- Good complexity detection
- Coverage 85-95% of design ground truth

### Score 3 (Acceptable)
- Detects major design issues
- Some missed patterns
- Coverage 70-85% of design ground truth

### Score 2 (Poor)
- Misses many design issues
- Incomplete pattern coverage
- Coverage 50-70% of design ground truth

### Score 1 (Unacceptable)
- Fails to detect basic design violations
- Coverage <50% of design ground truth

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
        "encapsulation": <1-5>,
        "interface_design": <1-5>,
        "inheritance": <1-5>,
        "complexity": <1-5>
    }
}
```
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect design-related evidence from all analysis outputs."""
        evidence = {
            "design_summary": {
                "encapsulation": {"detected": 0, "rules": []},
                "interface_design": {"detected": 0, "rules": []},
                "inheritance": {"detected": 0, "rules": []},
                "complexity": {"detected": 0, "rules": []},
                "naming": {"detected": 0, "rules": []},
                "other_design": {"detected": 0, "rules": []},
            },
            "detection_by_repo": {},
            "violations_sample": [],
            "ground_truth_comparison": {},
        }

        # Design rule categorization
        encapsulation_rules = ["CA1051", "CA1034", "SA1401", "S1104"]
        interface_rules = ["CA1040", "CA1033", "CA1710", "CA1711"]
        inheritance_rules = ["CA1061", "CA1501", "CA1052", "S2166"]
        complexity_rules = ["CA1502", "CA1505", "CA1506"]
        naming_rules = ["CA1707", "CA1708", "CA1715", "CA1716", "CA1720"]

        # Load all analysis results
        all_results = self.load_all_analysis_results()

        for repo_name, output in all_results.items():
            results = output.get("results", output)
            summary = results.get("summary", {})
            violations_by_rule = summary.get("violations_by_rule", {})

            repo_design = {
                "encapsulation": 0,
                "interface_design": 0,
                "inheritance": 0,
                "complexity": 0,
                "naming": 0,
                "other_design": 0,
            }

            # Categorize violations
            for rule_id, count in violations_by_rule.items():
                if any(rule in rule_id for rule in encapsulation_rules):
                    evidence["design_summary"]["encapsulation"]["detected"] += count
                    evidence["design_summary"]["encapsulation"]["rules"].append(rule_id)
                    repo_design["encapsulation"] += count
                elif any(rule in rule_id for rule in interface_rules):
                    evidence["design_summary"]["interface_design"]["detected"] += count
                    evidence["design_summary"]["interface_design"]["rules"].append(rule_id)
                    repo_design["interface_design"] += count
                elif any(rule in rule_id for rule in inheritance_rules):
                    evidence["design_summary"]["inheritance"]["detected"] += count
                    evidence["design_summary"]["inheritance"]["rules"].append(rule_id)
                    repo_design["inheritance"] += count
                elif any(rule in rule_id for rule in complexity_rules):
                    evidence["design_summary"]["complexity"]["detected"] += count
                    evidence["design_summary"]["complexity"]["rules"].append(rule_id)
                    repo_design["complexity"] += count
                elif any(rule in rule_id for rule in naming_rules):
                    evidence["design_summary"]["naming"]["detected"] += count
                    evidence["design_summary"]["naming"]["rules"].append(rule_id)
                    repo_design["naming"] += count
                elif rule_id.startswith("CA10") or rule_id.startswith("CA15"):
                    evidence["design_summary"]["other_design"]["detected"] += count
                    evidence["design_summary"]["other_design"]["rules"].append(rule_id)
                    repo_design["other_design"] += count

            evidence["detection_by_repo"][repo_name] = repo_design

            # Collect sample violations
            files = results.get("files", [])
            for file_data in files:
                for violation in file_data.get("violations", [])[:3]:
                    rule_id = violation.get("rule_id", "")
                    category = violation.get("category", "")
                    if (category == "design" or
                            any(r in rule_id for r in encapsulation_rules + interface_rules + inheritance_rules + complexity_rules)):
                        evidence["violations_sample"].append({
                            "repo": repo_name,
                            "file": file_data.get("path", ""),
                            "rule_id": rule_id,
                            "message": violation.get("message", "")[:200],
                            "severity": violation.get("severity", ""),
                        })

        # Deduplicate rules
        for category in evidence["design_summary"]:
            evidence["design_summary"][category]["rules"] = list(set(evidence["design_summary"][category]["rules"]))

        # Limit sample violations
        evidence["violations_sample"] = evidence["violations_sample"][:15]

        # Load ground truth for comparison
        design_gt = self.load_ground_truth_by_name("design-violations")
        if design_gt:
            expected = design_gt.get("expected_violations", {})
            evidence["ground_truth_comparison"] = {
                "expected": expected,
                "detected": {
                    "encapsulation": evidence["design_summary"]["encapsulation"]["detected"],
                    "interface_design": evidence["design_summary"]["interface_design"]["detected"],
                    "complexity": evidence["design_summary"]["complexity"]["detected"],
                },
            }

        return evidence

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Check design detection ground truth assertions."""
        failures = []

        all_results = self.load_all_analysis_results()
        design_gt = self.load_ground_truth_by_name("design-violations")

        # Check synthetic repo for expected design findings
        if "synthetic" in all_results:
            output = all_results["synthetic"]
            results = output.get("results", output)
            summary = results.get("summary", {})
            violations_by_category = summary.get("violations_by_category", {})

            # Design category should have findings
            design_count = violations_by_category.get("design", 0)
            if design_count == 0:
                failures.append("synthetic repo should have design findings but found 0")

        # Check ground truth expectations
        if design_gt:
            expected_min = design_gt.get("minimum_expected", {})

            # Get total design detections
            total_design = sum(
                output.get("results", output).get("summary", {}).get("violations_by_category", {}).get("design", 0)
                for output in all_results.values()
            )

            min_design = expected_min.get("design_total", 0)
            if min_design > 0 and total_design < min_design:
                failures.append(
                    f"Expected at least {min_design} design violations, found {total_design}"
                )

            # Check specific patterns
            expected_encapsulation = expected_min.get("encapsulation", 0)
            if expected_encapsulation > 0:
                total_encapsulation = sum(
                    output.get("results", output).get("summary", {}).get("violations_by_rule", {}).get("CA1051", 0)
                    for output in all_results.values()
                )
                if total_encapsulation < expected_encapsulation:
                    failures.append(
                        f"Expected at least {expected_encapsulation} encapsulation violations, found {total_encapsulation}"
                    )

        return len(failures) == 0, failures

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline."""
        return super().evaluate()
