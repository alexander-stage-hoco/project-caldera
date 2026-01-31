"""False positive rate judge for Trivy evaluation.

This judge evaluates the false positive rate of vulnerability detection by:
- Checking clean/no-vulnerability repos for spurious detections
- Evaluating test/dev dependency classification
- Assessing overall precision of the detection
"""

from typing import Any

from .base import BaseJudge, JudgeResult


class FalsePositiveRateJudge(BaseJudge):
    """Judge for evaluating false positive rate in vulnerability detection.

    For security tools, false positive rate is critical - a tool that floods
    developers with noise becomes shelfware. This judge specifically evaluates:
    - Zero findings on known-clean repositories
    - Correct classification of test/dev dependencies
    - Overall precision of vulnerability detection
    """

    @property
    def dimension_name(self) -> str:
        return "false_positive_rate"

    @property
    def weight(self) -> float:
        return 0.15  # 15% of overall score

    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence about false positive rates."""
        results = self.load_analysis_results()
        ground_truth = self.load_ground_truth()

        evidence = {
            "summary": {
                "repos_analyzed": len(results),
                "clean_repos_tested": 0,
                "clean_repos_with_findings": 0,
                "total_false_positives": 0,
                "false_positive_rate": 0.0,
                "precision": 100.0,
            },
            "clean_repo_results": [],
            "dev_dependency_issues": [],
            "potential_false_positives": [],
            "severity_distribution": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
        }

        total_findings = 0
        false_positives = 0

        for repo_name, data in results.items():
            vulns = data.get("vulnerabilities", [])
            summary = data.get("summary", {})
            total_findings += len(vulns)

            # Aggregate severity distribution
            evidence["severity_distribution"]["critical"] += summary.get(
                "critical_count", 0
            )
            evidence["severity_distribution"]["high"] += summary.get("high_count", 0)
            evidence["severity_distribution"]["medium"] += summary.get(
                "medium_count", 0
            )
            evidence["severity_distribution"]["low"] += summary.get("low_count", 0)

            # Find matching ground truth
            gt = ground_truth.get(repo_name)
            if not gt:
                continue

            # Check if this is a "clean" repository (should have 0 vulnerabilities)
            expected_vulns = gt.get("expected_vulnerabilities", {})
            is_clean_repo = False

            if isinstance(expected_vulns, dict):
                is_clean_repo = (
                    expected_vulns.get("min", 0) == 0
                    and expected_vulns.get("max", 0) == 0
                )
            elif isinstance(expected_vulns, int):
                is_clean_repo = expected_vulns == 0

            # Also check for explicit "no vulnerabilities" indicator
            if gt.get("id") == "no-vulnerabilities" or "clean" in gt.get(
                "description", ""
            ).lower():
                is_clean_repo = True

            if is_clean_repo:
                evidence["summary"]["clean_repos_tested"] += 1
                findings_count = len(vulns)

                clean_result = {
                    "repo": repo_name,
                    "expected_findings": 0,
                    "actual_findings": findings_count,
                    "passed": findings_count == 0,
                }

                if findings_count > 0:
                    evidence["summary"]["clean_repos_with_findings"] += 1
                    false_positives += findings_count

                    # Sample some false positives for review
                    for vuln in vulns[:5]:
                        evidence["potential_false_positives"].append(
                            {
                                "repo": repo_name,
                                "cve_id": vuln.get("id"),
                                "package": vuln.get("package"),
                                "severity": vuln.get("severity"),
                                "reason": "Found in clean repository expected to have 0 vulnerabilities",
                            }
                        )

                evidence["clean_repo_results"].append(clean_result)

            # Check for dev/test dependency misclassification
            # These are common sources of false positives in production assessments
            excluded_packages = gt.get("excluded_packages", [])
            test_packages = gt.get("test_packages", [])
            dev_packages = gt.get("dev_packages", [])

            all_excluded = set(excluded_packages + test_packages + dev_packages)
            if all_excluded:
                for vuln in vulns:
                    pkg = vuln.get("package", "")
                    if pkg in all_excluded:
                        false_positives += 1
                        evidence["dev_dependency_issues"].append(
                            {
                                "repo": repo_name,
                                "package": pkg,
                                "cve_id": vuln.get("id"),
                                "severity": vuln.get("severity"),
                                "category": (
                                    "test"
                                    if pkg in test_packages
                                    else "dev" if pkg in dev_packages else "excluded"
                                ),
                                "note": "Vulnerability in non-production dependency",
                            }
                        )

        # Calculate summary statistics
        evidence["summary"]["total_false_positives"] = false_positives

        if total_findings > 0:
            evidence["summary"]["false_positive_rate"] = round(
                false_positives / total_findings * 100, 1
            )
            evidence["summary"]["precision"] = round(
                (total_findings - false_positives) / total_findings * 100, 1
            )
        elif evidence["summary"]["clean_repos_tested"] > 0:
            # Only clean repos tested, calculate based on those
            clean_with_findings = evidence["summary"]["clean_repos_with_findings"]
            if clean_with_findings > 0:
                evidence["summary"]["false_positive_rate"] = 100.0
                evidence["summary"]["precision"] = 0.0

        return evidence

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run ground truth assertions for false positive rate.

        Key assertions:
        1. Clean repositories should have zero findings
        2. False positive rate should be below 5% threshold

        Returns:
            Tuple of (all_passed, list of failure messages)
        """
        failures = []

        evidence = self.collect_evidence()

        # Assertion 1: Clean repos should have no findings
        clean_tested = evidence["summary"]["clean_repos_tested"]
        clean_with_findings = evidence["summary"]["clean_repos_with_findings"]

        if clean_tested > 0 and clean_with_findings > 0:
            failures.append(
                f"{clean_with_findings}/{clean_tested} clean repositories "
                f"have unexpected findings (should be 0)"
            )

        # Assertion 2: False positive rate should be acceptable (<5%)
        fp_rate = evidence["summary"]["false_positive_rate"]
        if fp_rate > 5.0:
            failures.append(
                f"False positive rate is {fp_rate}% (threshold: <5%)"
            )

        return len(failures) == 0, failures

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline with ground truth assertions.

        1. Collects evidence about false positive rates
        2. Runs ground truth assertions (caps score at 2 if failed)
        3. Builds prompt from template
        4. Invokes Claude for evaluation
        5. Parses response into JudgeResult
        """
        # Run ground truth assertions first
        gt_passed, gt_failures = self.run_ground_truth_assertions()

        # Collect evidence
        evidence = self.collect_evidence()

        # Add assertion results to evidence
        evidence["ground_truth_assertions"] = {
            "passed": gt_passed,
            "failures": gt_failures,
        }

        # Build prompt
        prompt = self.build_prompt(evidence)

        # Invoke Claude
        response = self.invoke_claude(prompt)

        # Parse response
        result = self.parse_response(response)

        # Cap score if ground truth assertions failed
        if not gt_passed:
            original_score = result.score
            result.score = min(result.score, 2)
            if result.score != original_score:
                result.reasoning = (
                    f"[Score capped from {original_score} to {result.score} due to "
                    f"ground truth assertion failures: {gt_failures}] "
                    + result.reasoning
                )

        return result
