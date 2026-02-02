"""Security Detection Judge for Roslyn Analyzers evaluation."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class SecurityDetectionJudge(BaseJudge):
    """Evaluates security vulnerability detection quality.

    Assesses:
    - SQL injection detection (CA2100, CA3001)
    - Cryptography analysis (CA5xxx rules)
    - Deserialization security (CA2300-CA2315)
    - XSS and other OWASP patterns

    Sub-scores:
    - sql_injection (25%)
    - cryptography (25%)
    - deserialization (25%)
    - overall_coverage (25%)
    """

    @property
    def dimension_name(self) -> str:
        return "security_detection"

    @property
    def weight(self) -> float:
        return 0.30

    def get_default_prompt(self) -> str:
        return """# Security Detection Evaluation

You are evaluating the security vulnerability detection capabilities of Roslyn Analyzers.

## Evaluation Context

{{ interpretation_guidance }}

### Synthetic Repo Validation Results
{{ synthetic_baseline }}

### Evaluation Mode
{{ evaluation_mode }}

**Important**: When evaluation_mode is "real_world":
- Low security finding counts are NOT automatically failures
- Judge output quality: schema compliance, rule categorization, severity mapping
- Judge detection quality: Are the security issues that WERE detected accurate and properly classified?
- Consider: A tool that finds 0 security issues in a secure codebase deserves a high score

## Evidence to Review

### Security Summary
{{ security_summary }}

### Detection by Rule Category
{{ detection_by_category }}

### Sample Violations
{{ violations_sample }}

### Ground Truth Comparison
{{ ground_truth_comparison }}

## Evaluation Criteria

### For Synthetic Repos (with ground truth):

#### Score 5 (Excellent)
- Detects all expected SQL injection patterns (CA2100, CA3001, CA3002)
- Identifies weak cryptography usage (CA5350, CA5351, CA5xxx)
- Catches unsafe deserialization (CA2300-CA2315)
- Zero false negatives on security-critical files
- Coverage >95% of security ground truth

#### Score 4 (Good)
- Detects most SQL injection patterns
- Identifies common cryptography issues
- Catches most deserialization problems
- Coverage 85-95% of security ground truth

#### Score 3 (Acceptable)
- Detects common security issues
- Some missed patterns
- Coverage 70-85% of security ground truth

#### Score 2 (Poor)
- Misses many security issues
- Incomplete pattern coverage
- Coverage 50-70% of security ground truth

#### Score 1 (Unacceptable)
- Fails to detect critical vulnerabilities
- Coverage <50% of security ground truth

### For Real-World Repos (when synthetic_baseline shows validated tool):

#### Score 5 (Excellent)
- Output schema compliant, any findings accurately classified, complete metadata

#### Score 4 (Good)
- Minor schema issues but findings accurate, good rule categorization

#### Score 3 (Acceptable)
- Schema issues OR questionable security classification

#### Score 2 (Poor)
- Multiple schema issues AND questionable classifications

#### Score 1 (Failing)
- Broken output, missing required fields, obvious false positives

**Key principle**: Do NOT penalize for low finding counts on real-world repos when the tool is validated (synthetic_score >= 0.9).

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
        "sql_injection": <1-5>,
        "cryptography": <1-5>,
        "deserialization": <1-5>,
        "overall_coverage": <1-5>
    }
}
```
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect security-related evidence from all analysis outputs.

        For real-world evaluation mode, also injects synthetic evaluation
        context to help the LLM understand tool baseline capability.
        """
        evidence: dict[str, Any] = {
            "evaluation_mode": self.evaluation_mode,
            "security_summary": {
                "sql_injection": {"detected": 0, "rules": []},
                "cryptography": {"detected": 0, "rules": []},
                "deserialization": {"detected": 0, "rules": []},
                "xss": {"detected": 0, "rules": []},
                "other_security": {"detected": 0, "rules": []},
            },
            "detection_by_category": {},
            "violations_sample": [],
            "ground_truth_comparison": {},
        }

        # Security rule categorization
        sql_injection_rules = ["CA2100", "CA3001", "CA3002"]
        crypto_rules = ["CA5350", "CA5351", "CA5358", "CA5359", "CA5385", "CA5390", "CA5397", "CA5401", "CA5402"]
        deserialization_rules = ["CA2300", "CA2301", "CA2305", "CA2311", "CA2315", "CA2321", "CA2322"]
        xss_rules = ["CA3147"]

        # Load all analysis results
        all_results = self.load_all_analysis_results()

        for repo_name, output in all_results.items():
            results = output.get("results", output)
            summary = results.get("summary", {})
            violations_by_rule = summary.get("violations_by_rule", {})

            repo_security = {
                "sql_injection": 0,
                "cryptography": 0,
                "deserialization": 0,
                "xss": 0,
                "other_security": 0,
            }

            # Categorize violations
            for rule_id, count in violations_by_rule.items():
                if any(rule in rule_id for rule in sql_injection_rules):
                    evidence["security_summary"]["sql_injection"]["detected"] += count
                    evidence["security_summary"]["sql_injection"]["rules"].append(rule_id)
                    repo_security["sql_injection"] += count
                elif any(rule in rule_id for rule in crypto_rules):
                    evidence["security_summary"]["cryptography"]["detected"] += count
                    evidence["security_summary"]["cryptography"]["rules"].append(rule_id)
                    repo_security["cryptography"] += count
                elif any(rule in rule_id for rule in deserialization_rules):
                    evidence["security_summary"]["deserialization"]["detected"] += count
                    evidence["security_summary"]["deserialization"]["rules"].append(rule_id)
                    repo_security["deserialization"] += count
                elif any(rule in rule_id for rule in xss_rules):
                    evidence["security_summary"]["xss"]["detected"] += count
                    evidence["security_summary"]["xss"]["rules"].append(rule_id)
                    repo_security["xss"] += count
                elif rule_id.startswith("CA5") or rule_id.startswith("CA3"):
                    evidence["security_summary"]["other_security"]["detected"] += count
                    evidence["security_summary"]["other_security"]["rules"].append(rule_id)
                    repo_security["other_security"] += count

            evidence["detection_by_category"][repo_name] = repo_security

            # Collect sample violations
            files = results.get("files", [])
            for file_data in files:
                for violation in file_data.get("violations", [])[:3]:
                    rule_id = violation.get("rule_id", "")
                    if (any(r in rule_id for r in sql_injection_rules + crypto_rules + deserialization_rules + xss_rules)
                            or rule_id.startswith("CA5") or rule_id.startswith("CA3")):
                        evidence["violations_sample"].append({
                            "repo": repo_name,
                            "file": file_data.get("path", ""),
                            "rule_id": rule_id,
                            "message": violation.get("message", "")[:200],
                            "severity": violation.get("severity", ""),
                        })

        # Deduplicate rules
        for category in evidence["security_summary"]:
            evidence["security_summary"][category]["rules"] = list(set(evidence["security_summary"][category]["rules"]))

        # Limit sample violations
        evidence["violations_sample"] = evidence["violations_sample"][:15]

        # Load ground truth for comparison
        security_gt = self.load_ground_truth_by_name("security-issues")
        if security_gt:
            expected = security_gt.get("expected_violations", {})
            evidence["ground_truth_comparison"] = {
                "expected": expected,
                "detected": {
                    "sql_injection": evidence["security_summary"]["sql_injection"]["detected"],
                    "cryptography": evidence["security_summary"]["cryptography"]["detected"],
                    "deserialization": evidence["security_summary"]["deserialization"]["detected"],
                },
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
                evidence["interpretation_guidance"] = (
                    "Evaluate based on ground truth comparison only"
                )
        else:
            evidence["synthetic_baseline"] = (
                "N/A - synthetic mode uses direct ground truth comparison"
            )
            evidence["interpretation_guidance"] = "Strict ground truth evaluation"

        return evidence

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Check security detection ground truth assertions."""
        failures = []

        all_results = self.load_all_analysis_results()
        security_gt = self.load_ground_truth_by_name("security-issues")

        # Check synthetic repo for expected security findings
        if "synthetic" in all_results:
            output = all_results["synthetic"]
            results = output.get("results", output)
            summary = results.get("summary", {})
            violations_by_category = summary.get("violations_by_category", {})

            # Security category should have findings
            security_count = violations_by_category.get("security", 0)
            if security_count == 0:
                failures.append("synthetic repo should have security findings but found 0")

        # Check ground truth expectations
        if security_gt:
            expected_min = security_gt.get("minimum_expected", {})

            # Get total security detections
            total_security = sum(
                output.get("results", output).get("summary", {}).get("violations_by_category", {}).get("security", 0)
                for output in all_results.values()
            )

            min_security = expected_min.get("security_total", 0)
            if min_security > 0 and total_security < min_security:
                failures.append(
                    f"Expected at least {min_security} security violations, found {total_security}"
                )

        # Check clean-code ground truth for false positives
        clean_gt = self.load_ground_truth_by_name("clean-code")
        if clean_gt:
            expected_clean = clean_gt.get("expected_clean_files", [])
            # Check if any analysis output has violations on clean files
            for repo_name, output in all_results.items():
                results = output.get("results", output)
                files = results.get("files", [])
                for file_data in files:
                    file_path = file_data.get("path", "")
                    if any(clean_file in file_path for clean_file in expected_clean):
                        security_violations = [
                            v for v in file_data.get("violations", [])
                            if v.get("category") == "security"
                        ]
                        if security_violations:
                            failures.append(
                                f"Clean file {file_path} has {len(security_violations)} false positive security findings"
                            )

        return len(failures) == 0, failures

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline."""
        return super().evaluate()
