"""Judge for evaluating SBOM/package inventory completeness."""

from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class SBOMCompletenessJudge(BaseJudge):
    """Evaluates completeness of SBOM/package inventory."""

    @property
    def dimension_name(self) -> str:
        return "sbom_completeness"

    @property
    def weight(self) -> float:
        return 0.15  # 15% of overall score

    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence about SBOM/package inventory quality."""
        results = self.load_analysis_results()

        evidence = {
            "sbom_summary": {
                "repos_with_sbom": 0,
                "repos_without_sbom": 0,
                "total_packages": 0,
                "total_vulnerable": 0,
                "total_clean": 0,
            },
            "per_repo_sbom": [],
            "package_inventory_quality": [],
        }

        for repo_name, data in results.items():
            sbom = data.get("sbom", {})
            summary = data.get("summary", {})

            if sbom and sbom.get("total_packages", 0) > 0:
                evidence["sbom_summary"]["repos_with_sbom"] += 1
            else:
                evidence["sbom_summary"]["repos_without_sbom"] += 1

            total_pkgs = sbom.get("total_packages", 0)
            vulnerable_pkgs = sbom.get("vulnerable_packages", 0)
            clean_pkgs = sbom.get("clean_packages", 0)

            evidence["sbom_summary"]["total_packages"] += total_pkgs
            evidence["sbom_summary"]["total_vulnerable"] += vulnerable_pkgs
            evidence["sbom_summary"]["total_clean"] += clean_pkgs

            repo_sbom = {
                "repo": repo_name,
                "sbom_present": bool(sbom),
                "format": sbom.get("format", "none"),
                "total_packages": total_pkgs,
                "vulnerable_packages": vulnerable_pkgs,
                "clean_packages": clean_pkgs,
                "vulnerability_ratio": (
                    round(vulnerable_pkgs / total_pkgs * 100, 1)
                    if total_pkgs > 0
                    else 0
                ),
            }
            evidence["per_repo_sbom"].append(repo_sbom)

            # Assess inventory quality
            quality = {
                "repo": repo_name,
                "has_dependency_count": summary.get("dependency_count", 0) > 0,
                "dependency_count": summary.get("dependency_count", 0),
                "has_targets": summary.get("targets_scanned", 0) > 0,
                "targets_scanned": summary.get("targets_scanned", 0),
                "counts_consistent": (
                    total_pkgs == 0
                    or vulnerable_pkgs + clean_pkgs <= total_pkgs + 5  # Allow small variance
                ),
            }

            # Check target types identified
            targets = data.get("targets", [])
            quality["target_types"] = list(set(t.get("type", "unknown") for t in targets))

            evidence["package_inventory_quality"].append(quality)

        # Calculate overall SBOM coverage rate
        total_repos = (
            evidence["sbom_summary"]["repos_with_sbom"]
            + evidence["sbom_summary"]["repos_without_sbom"]
        )
        evidence["sbom_coverage_rate"] = (
            round(evidence["sbom_summary"]["repos_with_sbom"] / total_repos * 100, 1)
            if total_repos > 0
            else 0
        )

        # Calculate overall vulnerability ratio
        total_pkgs = evidence["sbom_summary"]["total_packages"]
        vuln_pkgs = evidence["sbom_summary"]["total_vulnerable"]
        evidence["overall_vulnerability_ratio"] = (
            round(vuln_pkgs / total_pkgs * 100, 1) if total_pkgs > 0 else 0
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
