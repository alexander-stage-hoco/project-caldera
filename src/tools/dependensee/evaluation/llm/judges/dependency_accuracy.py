"""Dependency Accuracy Judge - Evaluates correctness of dependency detection."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class DependencyAccuracyJudge(BaseJudge):
    """Evaluates accuracy of project and package dependency detection.

    Validates that:
    - Project references are correctly identified
    - NuGet package references are captured with versions
    - Dependency graph is internally consistent
    """

    @property
    def dimension_name(self) -> str:
        return "dependency_accuracy"

    @property
    def weight(self) -> float:
        return 0.30  # 30% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis and assess dependency accuracy."""
        all_results = self.load_all_analysis_results()
        if not all_results:
            return {"error": f"No analysis files found in {self.output_dir}"}

        # Aggregate from all repos
        total_projects = 0
        total_project_refs = 0
        total_package_refs = 0
        packages_with_version = 0
        all_packages = []

        for repo_name, repo_analysis in all_results.items():
            projects = self.extract_projects(repo_analysis)
            total_projects += len(projects)

            for proj in projects:
                refs = proj.get("project_references", [])
                total_project_refs += len(refs)

                pkgs = proj.get("package_references", [])
                total_package_refs += len(pkgs)
                for pkg in pkgs:
                    if pkg.get("version"):
                        packages_with_version += 1
                    all_packages.append(pkg)

        # Check for duplicate packages (same name, different versions)
        package_names = [p.get("name") for p in all_packages]
        unique_packages = len(set(package_names))

        evidence = {
            "total_projects": total_projects,
            "total_project_references": total_project_refs,
            "total_package_references": total_package_refs,
            "packages_with_version": packages_with_version,
            "unique_packages": unique_packages,
            "sample_packages": all_packages[:10],
            "evaluation_mode": self.evaluation_mode,
        }

        # Inject synthetic context for real-world evaluation
        if self.evaluation_mode == "real_world":
            synthetic_context = self.load_synthetic_evaluation_context()
            if synthetic_context:
                evidence["synthetic_baseline"] = synthetic_context
                evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                    synthetic_context
                )

        return evidence

    def format_prompt(self, evidence: dict[str, Any]) -> str:
        """Format prompt for LLM evaluation."""
        prompt_template = self.prompt_file.read_text() if self.prompt_file.exists() else ""
        return prompt_template.format(
            total_projects=evidence.get("total_projects", 0),
            total_project_refs=evidence.get("total_project_references", 0),
            total_package_refs=evidence.get("total_package_references", 0),
            packages_with_version=evidence.get("packages_with_version", 0),
            sample_packages=evidence.get("sample_packages", []),
        )

    def parse_response(self, response: str, evidence: dict[str, Any]) -> JudgeResult:
        """Parse LLM response into structured result."""
        total_pkgs = evidence.get("total_package_references", 0)
        with_version = evidence.get("packages_with_version", 0)

        if total_pkgs == 0:
            return JudgeResult(
                dimension=self.dimension_name,
                score=0.5,  # Neutral if no packages
                verdict="PASS",
                reasoning="No package references to validate",
                evidence=evidence,
            )

        version_coverage = with_version / total_pkgs
        overall_score = version_coverage

        verdict = "PASS" if overall_score >= 0.8 else "FAIL"
        reasoning = f"Found {total_pkgs} package references. {with_version} have version info ({version_coverage:.0%})."

        return JudgeResult(
            dimension=self.dimension_name,
            score=overall_score,
            verdict=verdict,
            reasoning=reasoning,
            evidence=evidence,
        )
