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
        all_project_refs = []

        for repo_name, repo_analysis in all_results.items():
            projects = self.extract_projects(repo_analysis)
            total_projects += len(projects)

            for proj in projects:
                refs = proj.get("project_references", [])
                total_project_refs += len(refs)
                for ref in refs:
                    all_project_refs.append({
                        "from": proj.get("name", "unknown"),
                        "to": ref,
                        "repo": repo_name,
                    })

                pkgs = proj.get("package_references", [])
                total_package_refs += len(pkgs)
                for pkg in pkgs:
                    if pkg.get("version"):
                        packages_with_version += 1
                    all_packages.append({
                        "name": pkg.get("name"),
                        "version": pkg.get("version"),
                        "project": proj.get("name"),
                        "repo": repo_name,
                    })

        # Check for duplicate packages (same name, different versions)
        package_names = [p.get("name") for p in all_packages if p.get("name")]
        unique_packages = len(set(package_names))
        duplicate_packages = len(package_names) - unique_packages

        # Calculate version coverage percentage
        version_coverage_pct = (
            (packages_with_version / total_package_refs * 100)
            if total_package_refs > 0
            else 100.0
        )

        evidence = {
            "total_projects": total_projects,
            "total_project_references": total_project_refs,
            "total_package_references": total_package_refs,
            "packages_with_version": packages_with_version,
            "version_coverage_pct": round(version_coverage_pct, 1),
            "unique_packages": unique_packages,
            "duplicate_package_count": duplicate_packages,
            "sample_packages": all_packages[:10],
            "sample_project_refs": all_project_refs[:10],
            "evaluation_mode": self.evaluation_mode,
        }

        # Load ground truth for comparison if available
        ground_truth = self.load_ground_truth()
        if ground_truth:
            gt_comparison = []
            for repo_name, gt in ground_truth.items():
                expected = gt.get("expected", {})
                expected_refs = expected.get("reference_count", 0)
                expected_pkgs = expected.get("package_count", 0)

                actual_refs = sum(
                    1 for r in all_project_refs if r.get("repo") == repo_name
                )
                actual_pkgs = sum(
                    1 for p in all_packages if p.get("repo") == repo_name
                )

                gt_comparison.append({
                    "repo": repo_name,
                    "expected_refs": expected_refs,
                    "actual_refs": actual_refs,
                    "refs_match": expected_refs == actual_refs,
                    "expected_pkgs": expected_pkgs,
                    "actual_pkgs": actual_pkgs,
                    "pkgs_match": expected_pkgs == actual_pkgs,
                })
            evidence["ground_truth_comparison"] = gt_comparison

        # Add synthetic context (empty for synthetic mode, populated for real_world)
        synthetic_context = self.load_synthetic_evaluation_context()
        if synthetic_context:
            evidence["synthetic_baseline"] = synthetic_context
            evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                synthetic_context
            )
        else:
            evidence["synthetic_baseline"] = "Not available (synthetic evaluation mode)"
            evidence["interpretation_guidance"] = "Evaluate against ground truth expectations."

        return evidence

    def get_default_prompt(self) -> str:
        """Return the default prompt template if file doesn't exist."""
        return """# Dependency Accuracy Evaluation

You are an expert .NET architect evaluating DependenSee's accuracy in detecting project and package dependencies.

## Task

Evaluate the accuracy and completeness of dependency detection in the analysis output.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

1. **Project Reference Accuracy** (40%): Are project references correctly identified?
   - 5: All project references captured with correct paths
   - 4: Most references correct (>90%)
   - 3: Majority correct (70-90%)
   - 2: Some issues (50-70%)
   - 1: Many references missing or incorrect (<50%)

2. **Package Reference Accuracy** (35%): Are NuGet packages correctly identified?
   - 5: All packages with correct names and versions
   - 4: Most packages correct (>90%)
   - 3: Majority correct (70-90%)
   - 2: Some packages missing versions (50-70%)
   - 1: Many packages missing or incorrect (<50%)

3. **Internal Consistency** (25%): Is the dependency data internally consistent?
   - 5: No orphan references, all targets exist
   - 4: Minor inconsistencies (<5%)
   - 3: Some inconsistencies (5-15%)
   - 2: Significant inconsistencies (15-30%)
   - 1: Major data integrity issues (>30%)

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific evidence points>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "project_ref_accuracy": <1-5>,
    "package_ref_accuracy": <1-5>,
    "internal_consistency": <1-5>
  }
}
"""

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run ground truth assertions before LLM evaluation.

        Checks that reference and package counts match expected values.
        """
        failures = []
        all_results = self.load_all_analysis_results()
        ground_truth = self.load_ground_truth()

        if not ground_truth:
            return True, []

        for repo_name, gt in ground_truth.items():
            if repo_name not in all_results:
                continue

            expected = gt.get("expected", {})
            projects = self.extract_projects(all_results[repo_name])

            # Count actual references and packages
            actual_refs = sum(len(p.get("project_references", [])) for p in projects)
            actual_pkgs = sum(len(p.get("package_references", [])) for p in projects)

            expected_refs = expected.get("reference_count", 0)
            expected_pkgs = expected.get("package_count", 0)

            if actual_refs != expected_refs:
                failures.append(
                    f"{repo_name}: expected {expected_refs} project refs, found {actual_refs}"
                )

            if actual_pkgs != expected_pkgs:
                failures.append(
                    f"{repo_name}: expected {expected_pkgs} packages, found {actual_pkgs}"
                )

        return len(failures) == 0, failures
