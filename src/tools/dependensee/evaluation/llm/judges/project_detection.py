"""Project Detection Judge - Evaluates completeness of .NET project discovery."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class ProjectDetectionJudge(BaseJudge):
    """Evaluates project detection accuracy and completeness.

    Validates that:
    - All .NET projects (.csproj, .fsproj, .vbproj) are discovered
    - Project paths are correctly normalized
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
        for repo_name, repo_analysis in all_results.items():
            for proj in self.extract_projects(repo_analysis):
                proj["_repo"] = repo_name
                all_projects.append(proj)

        # Analyze project detection metrics
        total_projects = len(all_projects)
        projects_with_framework = sum(1 for p in all_projects if p.get("target_framework"))
        projects_with_path = sum(1 for p in all_projects if p.get("path"))

        # Check path quality
        absolute_paths = sum(1 for p in all_projects if p.get("path", "").startswith("/"))
        dotdot_paths = sum(1 for p in all_projects if ".." in p.get("path", ""))

        return {
            "total_projects": total_projects,
            "projects_with_framework": projects_with_framework,
            "projects_with_path": projects_with_path,
            "path_quality": {
                "absolute_paths": absolute_paths,
                "paths_with_dotdot": dotdot_paths,
                "relative_paths": total_projects - absolute_paths - dotdot_paths,
            },
            "sample_projects": all_projects[:5],
            "evaluation_mode": self.evaluation_mode,
        }

    def format_prompt(self, evidence: dict[str, Any]) -> str:
        """Format prompt for LLM evaluation."""
        prompt_template = self.prompt_file.read_text() if self.prompt_file.exists() else ""
        return prompt_template.format(
            total_projects=evidence.get("total_projects", 0),
            projects_with_framework=evidence.get("projects_with_framework", 0),
            path_quality=evidence.get("path_quality", {}),
            sample_projects=evidence.get("sample_projects", []),
        )

    def parse_response(self, response: str, evidence: dict[str, Any]) -> JudgeResult:
        """Parse LLM response into structured result."""
        # Simple heuristic scoring based on evidence
        total = evidence.get("total_projects", 0)
        if total == 0:
            return JudgeResult(
                dimension=self.dimension_name,
                score=0.0,
                verdict="FAIL",
                reasoning="No projects detected",
                evidence=evidence,
            )

        with_framework = evidence.get("projects_with_framework", 0)
        path_quality = evidence.get("path_quality", {})
        good_paths = path_quality.get("relative_paths", 0)

        framework_score = with_framework / total if total > 0 else 0
        path_score = good_paths / total if total > 0 else 0
        overall_score = (framework_score * 0.4 + path_score * 0.6)

        verdict = "PASS" if overall_score >= 0.7 else "FAIL"
        reasoning = f"Detected {total} projects. {with_framework} have target frameworks. {good_paths} have properly normalized paths."

        return JudgeResult(
            dimension=self.dimension_name,
            score=overall_score,
            verdict=verdict,
            reasoning=reasoning,
            evidence=evidence,
        )
