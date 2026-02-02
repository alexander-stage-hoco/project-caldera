"""Judge for evaluating severity classification accuracy."""

from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class SeverityAccuracyJudge(BaseJudge):
    """Evaluates accuracy of severity classification (Critical/High/Medium/Low)."""

    @property
    def dimension_name(self) -> str:
        return "severity_accuracy"

    @property
    def weight(self) -> float:
        return 0.20  # 20% of overall score

    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence about severity classification accuracy."""
        results = self.load_analysis_results()
        ground_truth = self.load_ground_truth()

        evidence = {
            "severity_distribution": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "unknown": 0,
            },
            "cvss_alignment": [],
            "per_repo_severity": [],
            "ground_truth_comparison": [],
        }

        for repo_name, data in results.items():
            summary = data.get("summary", {})
            vulns = data.get("vulnerabilities", [])

            # Aggregate severity counts
            evidence["severity_distribution"]["critical"] += summary.get(
                "critical_count", 0
            )
            evidence["severity_distribution"]["high"] += summary.get("high_count", 0)
            evidence["severity_distribution"]["medium"] += summary.get("medium_count", 0)
            evidence["severity_distribution"]["low"] += summary.get("low_count", 0)
            evidence["severity_distribution"]["unknown"] += summary.get(
                "unknown_count", 0
            )

            # Per-repo severity breakdown
            evidence["per_repo_severity"].append(
                {
                    "repo": repo_name,
                    "critical": summary.get("critical_count", 0),
                    "high": summary.get("high_count", 0),
                    "medium": summary.get("medium_count", 0),
                    "low": summary.get("low_count", 0),
                }
            )

            # Check CVSS score alignment with severity
            for vuln in vulns[:10]:  # Sample first 10
                cvss = vuln.get("cvss_score")
                severity = vuln.get("severity", "UNKNOWN")

                # Expected severity based on CVSS 3.x ranges
                # Handle None cvss_score (not all vulnerabilities have CVSS scores)
                if cvss is None:
                    expected = "UNKNOWN"
                elif cvss >= 9.0:
                    expected = "CRITICAL"
                elif cvss >= 7.0:
                    expected = "HIGH"
                elif cvss >= 4.0:
                    expected = "MEDIUM"
                elif cvss > 0:
                    expected = "LOW"
                else:
                    expected = "UNKNOWN"

                evidence["cvss_alignment"].append(
                    {
                        "cve_id": vuln.get("id"),
                        "cvss_score": cvss,
                        "reported_severity": severity,
                        "expected_severity": expected,
                        "aligned": severity == expected,
                    }
                )

            # Compare with ground truth
            if repo_name in ground_truth:
                gt = ground_truth[repo_name]
                comparison = {
                    "repo": repo_name,
                    "expected_critical": gt.get("expected_critical", {}),
                    "expected_high": gt.get("expected_high", {}),
                    "actual_critical": summary.get("critical_count", 0),
                    "actual_high": summary.get("high_count", 0),
                }

                # Check if within expected ranges
                exp_crit = gt.get("expected_critical", {})
                if isinstance(exp_crit, dict):
                    comparison["critical_in_range"] = (
                        exp_crit.get("min", 0)
                        <= summary.get("critical_count", 0)
                        <= exp_crit.get("max", 999)
                    )
                elif isinstance(exp_crit, int):
                    comparison["critical_in_range"] = (
                        summary.get("critical_count", 0) == exp_crit
                    )

                exp_high = gt.get("expected_high", {})
                if isinstance(exp_high, dict):
                    comparison["high_in_range"] = (
                        exp_high.get("min", 0)
                        <= summary.get("high_count", 0)
                        <= exp_high.get("max", 999)
                    )

                evidence["ground_truth_comparison"].append(comparison)

        # Calculate alignment statistics
        if evidence["cvss_alignment"]:
            aligned = sum(1 for a in evidence["cvss_alignment"] if a["aligned"])
            total = len(evidence["cvss_alignment"])
            evidence["alignment_rate"] = round(aligned / total * 100, 1)
        else:
            evidence["alignment_rate"] = 0

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
