"""Judge for evaluating IaC misconfiguration detection quality."""

from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class IaCQualityJudge(BaseJudge):
    """Evaluates quality of IaC (Dockerfile/Terraform) misconfiguration detection."""

    @property
    def dimension_name(self) -> str:
        return "iac_quality"

    @property
    def weight(self) -> float:
        return 0.25  # 25% of overall score

    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence about IaC misconfiguration detection quality."""
        results = self.load_analysis_results()
        ground_truth = self.load_ground_truth()

        evidence = {
            "iac_summary": {
                "repos_with_iac_issues": 0,
                "repos_without_iac_issues": 0,
                "total_misconfigurations": 0,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
            },
            "per_repo_iac": [],
            "sample_misconfigurations": [],
            "detection_by_type": {"dockerfile": 0, "terraform": 0, "other": 0},
        }

        for repo_name, data in results.items():
            iac = data.get("iac_misconfigurations", {})
            misconfigs = iac.get("misconfigurations", [])

            total = iac.get("total_count", 0)
            critical = iac.get("critical_count", 0)
            high = iac.get("high_count", 0)

            if total > 0:
                evidence["iac_summary"]["repos_with_iac_issues"] += 1
            else:
                evidence["iac_summary"]["repos_without_iac_issues"] += 1

            evidence["iac_summary"]["total_misconfigurations"] += total
            evidence["iac_summary"]["critical_count"] += critical
            evidence["iac_summary"]["high_count"] += high

            # Count by severity
            for mc in misconfigs:
                severity = mc.get("severity", "UNKNOWN").upper()
                if severity == "MEDIUM":
                    evidence["iac_summary"]["medium_count"] += 1
                elif severity == "LOW":
                    evidence["iac_summary"]["low_count"] += 1

                # Count by target type
                target = mc.get("target", "").lower()
                if "dockerfile" in target:
                    evidence["detection_by_type"]["dockerfile"] += 1
                elif target.endswith(".tf"):
                    evidence["detection_by_type"]["terraform"] += 1
                else:
                    evidence["detection_by_type"]["other"] += 1

            # Per-repo IaC summary
            evidence["per_repo_iac"].append(
                {
                    "repo": repo_name,
                    "total_issues": total,
                    "critical": critical,
                    "high": high,
                    "issue_types": list(set(mc.get("id", "unknown") for mc in misconfigs)),
                }
            )

            # Sample misconfigurations for review
            for mc in misconfigs[:5]:
                evidence["sample_misconfigurations"].append(
                    {
                        "id": mc.get("id"),
                        "severity": mc.get("severity"),
                        "title": mc.get("title"),
                        "target": mc.get("target"),
                        "target_type": mc.get("target_type"),
                        "resolution": mc.get("resolution", "")[:200],
                        "start_line": mc.get("start_line"),
                    }
                )

        # Check for expected IaC detection in iac-misconfigs repo
        if "iac-misconfigs" in results:
            iac_data = results["iac-misconfigs"].get("iac_misconfigurations", {})
            evidence["iac_misconfigs_repo"] = {
                "total_detected": iac_data.get("total_count", 0),
                "critical_detected": iac_data.get("critical_count", 0),
                "high_detected": iac_data.get("high_count", 0),
                "expectation": "Should detect multiple IaC issues in this test repo",
            }

        # Assess actionability of findings
        actionable_count = sum(
            1
            for mc in evidence["sample_misconfigurations"]
            if mc.get("resolution") and len(mc.get("resolution", "")) > 10
        )
        evidence["actionability_rate"] = (
            round(actionable_count / len(evidence["sample_misconfigurations"]) * 100, 1)
            if evidence["sample_misconfigurations"]
            else 0
        )

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
