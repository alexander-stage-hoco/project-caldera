"""Project Detection Judge - Evaluates completeness of .NET project discovery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class ProjectDetectionJudge(BaseJudge):
    """Evaluates project detection accuracy and completeness.

    Validates that:
    - All .NET projects (.csproj, .fsproj, .vbproj) are discovered
    - Project paths are correctly normalized (repo-relative)
    - Target frameworks are identified
    """

    @property
    def dimension_name(self) -> str:
        return "project_detection"

    @property
    def weight(self) -> float:
        return 0.30  # 30% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis and assess project detection."""
        all_results = self.load_all_analysis_results()
        if not all_results:
            return {"error": f"No analysis files found in {self.output_dir}"}

        # Aggregate projects from all repos
        all_projects = []
        repos_analyzed = []

        for repo_name, repo_analysis in all_results.items():
            repos_analyzed.append(repo_name)
            for proj in self.extract_projects(repo_analysis):
                proj_copy = dict(proj)
                proj_copy["_repo"] = repo_name
                all_projects.append(proj_copy)

        # Analyze project detection metrics
        total_projects = len(all_projects)
        projects_with_framework = sum(1 for p in all_projects if p.get("target_framework"))
        projects_with_path = sum(1 for p in all_projects if p.get("path"))

        # Check path quality
        absolute_paths = sum(1 for p in all_projects if p.get("path", "").startswith("/"))
        dotdot_paths = sum(1 for p in all_projects if ".." in p.get("path", ""))
        relative_paths = total_projects - absolute_paths - dotdot_paths

        # Count project types
        csproj_count = sum(1 for p in all_projects if p.get("path", "").endswith(".csproj"))
        fsproj_count = sum(1 for p in all_projects if p.get("path", "").endswith(".fsproj"))
        vbproj_count = sum(1 for p in all_projects if p.get("path", "").endswith(".vbproj"))

        evidence = {
            "repos_analyzed": repos_analyzed,
            "total_projects": total_projects,
            "projects_with_framework": projects_with_framework,
            "projects_with_path": projects_with_path,
            "path_quality": {
                "absolute_paths": absolute_paths,
                "paths_with_dotdot": dotdot_paths,
                "relative_paths": relative_paths,
            },
            "project_types": {
                "csproj": csproj_count,
                "fsproj": fsproj_count,
                "vbproj": vbproj_count,
            },
            "sample_projects": all_projects[:5],
            "evaluation_mode": self.evaluation_mode,
        }

        # Load ground truth for comparison if available
        ground_truth = self.load_ground_truth()
        if ground_truth:
            gt_comparison = []
            for repo_name, gt in ground_truth.items():
                expected_count = gt.get("expected", {}).get("project_count", 0)
                actual_count = sum(1 for p in all_projects if p.get("_repo") == repo_name)
                gt_comparison.append({
                    "repo": repo_name,
                    "expected": expected_count,
                    "actual": actual_count,
                    "match": expected_count == actual_count,
                })
            evidence["ground_truth_comparison"] = gt_comparison

        # Inject synthetic context for real-world evaluation
        if self.evaluation_mode == "real_world":
            synthetic_context = self.load_synthetic_evaluation_context()
            if synthetic_context:
                evidence["synthetic_baseline"] = synthetic_context
                evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                    synthetic_context
                )

        return evidence

    def get_default_prompt(self) -> str:
        """Return the default prompt template if file doesn't exist."""
        return """# Project Detection Evaluation

You are an expert .NET architect evaluating DependenSee's ability to detect and analyze .NET projects.

## Task

Evaluate the completeness and accuracy of project detection in the analysis output.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

1. **Completeness** (40%): Are all .NET project files detected?
   - 5: All .csproj, .fsproj, .vbproj files found
   - 4: Most projects found (>90%)
   - 3: Majority found (70-90%)
   - 2: Some projects missing (50-70%)
   - 1: Many projects missing (<50%)

2. **Path Quality** (30%): Are paths correctly normalized?
   - 5: All paths are repo-relative, no ".." or absolute paths
   - 4: Minor path issues (<5%)
   - 3: Some path issues (5-15%)
   - 2: Significant path issues (15-30%)
   - 1: Paths are mostly absolute or contain ".."

3. **Framework Detection** (30%): Are target frameworks identified?
   - 5: All projects have target framework
   - 4: Most have framework (>90%)
   - 3: Majority have framework (70-90%)
   - 2: Some missing (50-70%)
   - 1: Framework missing from most (<50%)

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific evidence points>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "completeness": <1-5>,
    "path_quality": <1-5>,
    "framework_detection": <1-5>
  }
}
"""

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run ground truth assertions before LLM evaluation.

        Checks that project counts match expected values from ground truth files.
        """
        failures = []
        all_results = self.load_all_analysis_results()
        ground_truth = self.load_ground_truth()

        if not ground_truth:
            # No ground truth = no assertions to run
            return True, []

        for repo_name, gt in ground_truth.items():
            expected_count = gt.get("expected", {}).get("project_count", 0)

            # Find matching analysis results
            if repo_name in all_results:
                projects = self.extract_projects(all_results[repo_name])
                actual_count = len(projects)

                if actual_count != expected_count:
                    failures.append(
                        f"{repo_name}: expected {expected_count} projects, found {actual_count}"
                    )

        return len(failures) == 0, failures
