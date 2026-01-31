"""Judge for evaluating dependency freshness detection accuracy."""

from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class FreshnessQualityJudge(BaseJudge):
    """Evaluates accuracy of dependency freshness/outdatedness detection."""

    @property
    def dimension_name(self) -> str:
        return "freshness_quality"

    @property
    def weight(self) -> float:
        return 0.15  # 15% of overall score

    def collect_evidence(self) -> dict[str, Any]:
        """Collect evidence about freshness detection accuracy."""
        results = self.load_analysis_results()
        ground_truth = self.load_ground_truth()

        evidence = {
            "summary": {
                "repos_with_freshness": 0,
                "repos_without_freshness": 0,
                "total_packages_checked": 0,
                "total_outdated": 0,
                "overall_outdated_pct": 0.0,
            },
            "per_repo_results": [],
            "ground_truth_comparison": [],
            "registry_coverage": {
                "pip": 0,
                "npm": 0,
                "nuget": 0,
                "maven": 0,
                "go": 0,
            },
            "version_delta_samples": [],
        }

        total_packages = 0
        total_outdated = 0

        for repo_name, data in results.items():
            freshness = data.get("freshness", {})

            if not freshness.get("checked", False):
                evidence["summary"]["repos_without_freshness"] += 1
                evidence["per_repo_results"].append({
                    "repo": repo_name,
                    "freshness_checked": False,
                    "packages": 0,
                    "outdated": 0,
                    "outdated_pct": None,
                })
                continue

            evidence["summary"]["repos_with_freshness"] += 1

            packages = freshness.get("packages", [])
            outdated_count = freshness.get("outdated_count", 0)
            total_packages_repo = freshness.get("total_packages", len(packages))
            outdated_pct = freshness.get("outdated_pct", 0.0)

            total_packages += total_packages_repo
            total_outdated += outdated_count

            repo_result = {
                "repo": repo_name,
                "freshness_checked": True,
                "packages": total_packages_repo,
                "outdated": outdated_count,
                "outdated_pct": outdated_pct,
                "major_versions_behind_total": freshness.get("major_versions_behind_total", 0),
                "avg_days_behind": freshness.get("avg_days_behind", 0),
            }

            # Count registry types
            registry_types = set()
            for pkg in packages:
                pkg_type = pkg.get("package_type", "").lower()
                if pkg_type:
                    registry_types.add(pkg_type)
                    if pkg_type in evidence["registry_coverage"]:
                        evidence["registry_coverage"][pkg_type] += 1

            repo_result["registry_types"] = list(registry_types)
            evidence["per_repo_results"].append(repo_result)

            # Compare with ground truth
            if repo_name in ground_truth:
                gt = ground_truth[repo_name]

                if gt.get("freshness_expected", False):
                    expected_outdated = gt.get("expected_outdated_count", {})
                    expected_pct = gt.get("expected_outdated_pct", {})

                    comparison = {
                        "repo": repo_name,
                        "outdated_count": outdated_count,
                        "expected_outdated_min": expected_outdated.get("min", 0),
                        "expected_outdated_max": expected_outdated.get("max", 999),
                        "outdated_in_range": (
                            expected_outdated.get("min", 0)
                            <= outdated_count
                            <= expected_outdated.get("max", 999)
                        ),
                        "outdated_pct": outdated_pct,
                        "expected_pct_min": expected_pct.get("min", 0),
                        "expected_pct_max": expected_pct.get("max", 100),
                        "pct_in_range": (
                            expected_pct.get("min", 0)
                            <= outdated_pct
                            <= expected_pct.get("max", 100)
                        ),
                    }
                    evidence["ground_truth_comparison"].append(comparison)

            # Sample version deltas (up to 3 per repo)
            for pkg in packages[:3]:
                if pkg.get("is_outdated", False):
                    evidence["version_delta_samples"].append({
                        "repo": repo_name,
                        "package": pkg.get("package"),
                        "package_type": pkg.get("package_type"),
                        "installed": pkg.get("installed_version"),
                        "latest": pkg.get("latest_version"),
                        "major_behind": pkg.get("major_versions_behind", 0),
                        "minor_behind": pkg.get("minor_versions_behind", 0),
                        "patch_behind": pkg.get("patch_versions_behind", 0),
                        "days_since_latest": pkg.get("days_since_latest", 0),
                        "has_vulnerability": pkg.get("has_vulnerability", False),
                    })

        # Compute overall percentages
        evidence["summary"]["total_packages_checked"] = total_packages
        evidence["summary"]["total_outdated"] = total_outdated
        if total_packages > 0:
            evidence["summary"]["overall_outdated_pct"] = round(
                (total_outdated / total_packages) * 100, 1
            )

        # Limit version delta samples to 10 total
        evidence["version_delta_samples"] = evidence["version_delta_samples"][:10]

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
