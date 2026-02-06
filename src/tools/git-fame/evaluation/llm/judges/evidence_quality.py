"""Evidence Quality Judge - Evaluates completeness of supporting data."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class EvidenceQualityJudge(BaseJudge):
    """Evaluates the quality and completeness of evidence in git-fame output.

    Validates that:
    - All required metrics are present for each author
    - Data provenance is properly tracked
    - Supporting evidence (commits, files touched) is available
    """

    @property
    def dimension_name(self) -> str:
        return "evidence_quality"

    @property
    def weight(self) -> float:
        return 0.15  # 15% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis and assess evidence quality."""
        all_results = self.load_all_analysis_results()
        if not all_results:
            return {"error": f"No analysis files found in {self.output_dir}"}

        evidence_analysis: list[dict] = []
        required_fields = ["name", "surviving_loc", "commit_count", "ownership_pct"]
        optional_fields = ["insertions_total", "deletions_total", "files_touched"]

        for repo_name, repo_data in all_results.items():
            results = self.extract_results(repo_data)
            authors = self.extract_authors(repo_data)
            summary = self.extract_summary(repo_data)

            # Check required summary fields
            required_summary_fields = ["author_count", "total_loc", "bus_factor", "hhi_index"]
            summary_missing = [f for f in required_summary_fields if f not in summary]

            # Check author field completeness
            authors_with_all_required = 0
            authors_with_all_optional = 0
            field_coverage: dict[str, int] = {}

            for author in authors:
                # Check required fields
                has_required = all(f in author for f in required_fields)
                if has_required:
                    authors_with_all_required += 1

                # Check optional fields
                has_optional = all(f in author for f in optional_fields)
                if has_optional:
                    authors_with_all_optional += 1

                # Track field coverage
                for field in required_fields + optional_fields:
                    if field in author:
                        field_coverage[field] = field_coverage.get(field, 0) + 1

            author_count = len(authors)
            required_coverage = (
                authors_with_all_required / author_count * 100
                if author_count > 0 else 0
            )
            optional_coverage = (
                authors_with_all_optional / author_count * 100
                if author_count > 0 else 0
            )

            # Check provenance
            provenance = results.get("provenance", {})
            has_provenance = bool(provenance.get("tool") and provenance.get("commands"))

            evidence_analysis.append({
                "repo": repo_name,
                "author_count": author_count,
                "summary_missing_fields": summary_missing,
                "required_field_coverage_pct": round(required_coverage, 1),
                "optional_field_coverage_pct": round(optional_coverage, 1),
                "field_coverage": {
                    k: round(v / author_count * 100, 1) if author_count > 0 else 0
                    for k, v in field_coverage.items()
                },
                "has_provenance": has_provenance,
                "provenance": provenance,
            })

        # Calculate overall metrics
        total_repos = len(evidence_analysis)
        avg_required = (
            sum(a["required_field_coverage_pct"] for a in evidence_analysis) / total_repos
            if total_repos > 0 else 0
        )
        avg_optional = (
            sum(a["optional_field_coverage_pct"] for a in evidence_analysis) / total_repos
            if total_repos > 0 else 0
        )
        repos_with_provenance = sum(1 for a in evidence_analysis if a["has_provenance"])

        evidence = {
            "total_repos": total_repos,
            "avg_required_field_coverage_pct": round(avg_required, 1),
            "avg_optional_field_coverage_pct": round(avg_optional, 1),
            "repos_with_provenance": repos_with_provenance,
            "provenance_coverage_pct": round(repos_with_provenance / total_repos * 100, 1) if total_repos > 0 else 0,
            "evidence_analysis": evidence_analysis,
            "required_fields": required_fields,
            "optional_fields": optional_fields,
            "evaluation_mode": self.evaluation_mode,
        }

        # Add synthetic context if available
        synthetic_context = self.load_synthetic_evaluation_context()
        if synthetic_context:
            evidence["synthetic_baseline"] = synthetic_context
            evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                synthetic_context
            )
        else:
            evidence["synthetic_baseline"] = "Not available"
            evidence["interpretation_guidance"] = "Evaluate evidence completeness."

        return evidence

    def get_default_prompt(self) -> str:
        """Return the default prompt template if file doesn't exist."""
        return """# Evidence Quality Evaluation

You are evaluating the quality and completeness of evidence in git-fame output.

## Background

Good evidence quality means:
- All required metrics are present for every author
- Optional metrics (insertions, deletions, files touched) provide additional context
- Provenance information (tool, command) enables reproducibility
- Data is consistent and non-contradictory

## Task

Evaluate the completeness and quality of evidence in the git-fame output.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

1. **Required Field Coverage (40%)**: Are required fields present?
   - 5: 100% of authors have all required fields
   - 4: >95% coverage
   - 3: 85-95% coverage
   - 2: 70-85% coverage
   - 1: <70% coverage

2. **Optional Field Coverage (30%)**: Are optional metrics available?
   - 5: >90% of authors have all optional fields
   - 4: 70-90% coverage
   - 3: 50-70% coverage
   - 2: 30-50% coverage
   - 1: <30% coverage

3. **Provenance Quality (30%)**: Is provenance properly tracked?
   - 5: All repos have complete provenance (tool, command, version)
   - 4: Most repos have provenance (>90%)
   - 3: Some repos have provenance (70-90%)
   - 2: Few repos have provenance (50-70%)
   - 1: Provenance rarely present (<50%)

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific evidence points>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "required_field_coverage": <1-5>,
    "optional_field_coverage": <1-5>,
    "provenance_quality": <1-5>
  }
}
"""

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run ground truth assertions before LLM evaluation."""
        failures = []
        all_results = self.load_all_analysis_results()

        for repo_name, repo_data in all_results.items():
            authors = self.extract_authors(repo_data)

            # Check that all authors have required fields
            required_fields = ["name", "surviving_loc", "commit_count", "ownership_pct"]
            for i, author in enumerate(authors):
                missing = [f for f in required_fields if f not in author]
                if missing:
                    failures.append(
                        f"{repo_name}: author[{i}] missing required fields: {missing}"
                    )

        return len(failures) == 0, failures
