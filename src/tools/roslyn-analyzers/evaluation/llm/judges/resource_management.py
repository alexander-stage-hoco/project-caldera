"""Resource Management Judge for Roslyn Analyzers evaluation."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class ResourceManagementJudge(BaseJudge):
    """Evaluates resource management and disposal detection.

    Assesses:
    - IDisposable implementation (CA1063, CA1816)
    - Undisposed object detection (IDISP rules)
    - Async pattern analysis (CA2000, CA2007)
    - Resource leak prevention (CA2213)

    Sub-scores:
    - idisposable_impl (25%)
    - undisposed_detection (25%)
    - async_patterns (25%)
    - leak_prevention (25%)
    """

    @property
    def dimension_name(self) -> str:
        return "resource_management"

    @property
    def weight(self) -> float:
        return 0.25

    def get_default_prompt(self) -> str:
        return """# Resource Management Evaluation

You are evaluating the resource management detection capabilities of Roslyn Analyzers.

## Evidence to Review

### Resource Summary
{{ resource_summary }}

### Detection by Repository
{{ detection_by_repo }}

### Sample Violations
{{ violations_sample }}

### Ground Truth Comparison
{{ ground_truth_comparison }}

## Evaluation Criteria

### Score 5 (Excellent)
- Detects all IDisposable implementation issues (CA1063, CA1816)
- Identifies undisposed objects (IDISP006, IDISP014)
- Catches async pattern issues (CA2000, CA2007)
- Finds resource leaks (CA2213)
- Coverage >95% of resource ground truth

### Score 4 (Good)
- Detects most IDisposable issues
- Identifies common undisposed objects
- Catches most async issues
- Good leak detection
- Coverage 85-95% of resource ground truth

### Score 3 (Acceptable)
- Detects major resource issues
- Some missed patterns
- Coverage 70-85% of resource ground truth

### Score 2 (Poor)
- Misses many resource issues
- Incomplete pattern coverage
- Coverage 50-70% of resource ground truth

### Score 1 (Unacceptable)
- Fails to detect basic resource problems
- Coverage <50% of resource ground truth

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
        "idisposable_impl": <1-5>,
        "undisposed_detection": <1-5>,
        "async_patterns": <1-5>,
        "leak_prevention": <1-5>
    }
}
```
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect resource-related evidence from all analysis outputs."""
        evidence = {
            "resource_summary": {
                "idisposable_impl": {"detected": 0, "rules": []},
                "undisposed": {"detected": 0, "rules": []},
                "async_patterns": {"detected": 0, "rules": []},
                "leaks": {"detected": 0, "rules": []},
                "other_resource": {"detected": 0, "rules": []},
            },
            "detection_by_repo": {},
            "violations_sample": [],
            "ground_truth_comparison": {},
        }

        # Resource rule categorization
        idisposable_rules = ["CA1063", "CA1816", "CA1821"]
        undisposed_rules = ["IDISP006", "IDISP014", "CA2000"]
        async_rules = ["ASYNC0001", "ASYNC0002", "CA2007", "CA2008", "CA2012", "VSTHRD110", "VSTHRD111"]
        leak_rules = ["CA2213", "CA2215", "IDISP001", "IDISP004"]

        # Load all analysis results
        all_results = self.load_all_analysis_results()

        for repo_name, output in all_results.items():
            results = output.get("results", output)
            summary = results.get("summary", {})
            violations_by_rule = summary.get("violations_by_rule", {})

            repo_resource = {
                "idisposable_impl": 0,
                "undisposed": 0,
                "async_patterns": 0,
                "leaks": 0,
                "other_resource": 0,
            }

            # Categorize violations
            for rule_id, count in violations_by_rule.items():
                if any(rule in rule_id for rule in idisposable_rules):
                    evidence["resource_summary"]["idisposable_impl"]["detected"] += count
                    evidence["resource_summary"]["idisposable_impl"]["rules"].append(rule_id)
                    repo_resource["idisposable_impl"] += count
                elif any(rule in rule_id for rule in undisposed_rules):
                    evidence["resource_summary"]["undisposed"]["detected"] += count
                    evidence["resource_summary"]["undisposed"]["rules"].append(rule_id)
                    repo_resource["undisposed"] += count
                elif any(rule in rule_id for rule in async_rules):
                    evidence["resource_summary"]["async_patterns"]["detected"] += count
                    evidence["resource_summary"]["async_patterns"]["rules"].append(rule_id)
                    repo_resource["async_patterns"] += count
                elif any(rule in rule_id for rule in leak_rules):
                    evidence["resource_summary"]["leaks"]["detected"] += count
                    evidence["resource_summary"]["leaks"]["rules"].append(rule_id)
                    repo_resource["leaks"] += count
                elif rule_id.startswith("IDISP") or "Dispose" in rule_id:
                    evidence["resource_summary"]["other_resource"]["detected"] += count
                    evidence["resource_summary"]["other_resource"]["rules"].append(rule_id)
                    repo_resource["other_resource"] += count

            evidence["detection_by_repo"][repo_name] = repo_resource

            # Collect sample violations
            files = results.get("files", [])
            for file_data in files:
                for violation in file_data.get("violations", [])[:3]:
                    rule_id = violation.get("rule_id", "")
                    category = violation.get("category", "")
                    if (category == "resource" or
                            any(r in rule_id for r in idisposable_rules + undisposed_rules + async_rules + leak_rules) or
                            rule_id.startswith("IDISP")):
                        evidence["violations_sample"].append({
                            "repo": repo_name,
                            "file": file_data.get("path", ""),
                            "rule_id": rule_id,
                            "message": violation.get("message", "")[:200],
                            "severity": violation.get("severity", ""),
                        })

        # Deduplicate rules
        for category in evidence["resource_summary"]:
            evidence["resource_summary"][category]["rules"] = list(set(evidence["resource_summary"][category]["rules"]))

        # Limit sample violations
        evidence["violations_sample"] = evidence["violations_sample"][:15]

        # Load ground truth for comparison
        resource_gt = self.load_ground_truth_by_name("resource-management")
        if resource_gt:
            expected = resource_gt.get("expected_violations", {})
            evidence["ground_truth_comparison"] = {
                "expected": expected,
                "detected": {
                    "idisposable_impl": evidence["resource_summary"]["idisposable_impl"]["detected"],
                    "undisposed": evidence["resource_summary"]["undisposed"]["detected"],
                    "async_patterns": evidence["resource_summary"]["async_patterns"]["detected"],
                    "leaks": evidence["resource_summary"]["leaks"]["detected"],
                },
            }

        return evidence

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Check resource detection ground truth assertions."""
        failures = []

        all_results = self.load_all_analysis_results()
        resource_gt = self.load_ground_truth_by_name("resource-management")

        # Check synthetic repo for expected resource findings
        if "synthetic" in all_results:
            output = all_results["synthetic"]
            results = output.get("results", output)
            summary = results.get("summary", {})
            violations_by_category = summary.get("violations_by_category", {})

            # Resource category should have findings
            resource_count = violations_by_category.get("resource", 0)
            if resource_count == 0:
                failures.append("synthetic repo should have resource findings but found 0")

        # Check ground truth expectations
        if resource_gt:
            expected_min = resource_gt.get("minimum_expected", {})

            # Get total resource detections
            total_resource = sum(
                output.get("results", output).get("summary", {}).get("violations_by_category", {}).get("resource", 0)
                for output in all_results.values()
            )

            min_resource = expected_min.get("resource_total", 0)
            if min_resource > 0 and total_resource < min_resource:
                failures.append(
                    f"Expected at least {min_resource} resource violations, found {total_resource}"
                )

            # Check specific IDISP rules
            expected_idisp = expected_min.get("idisp_rules", 0)
            if expected_idisp > 0:
                total_idisp = 0
                for output in all_results.values():
                    violations_by_rule = output.get("results", output).get("summary", {}).get("violations_by_rule", {})
                    total_idisp += sum(count for rule, count in violations_by_rule.items() if "IDISP" in rule)

                if total_idisp < expected_idisp:
                    failures.append(
                        f"Expected at least {expected_idisp} IDISP violations, found {total_idisp}"
                    )

        return len(failures) == 0, failures

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline."""
        return super().evaluate()
