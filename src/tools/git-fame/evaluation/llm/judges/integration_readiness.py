"""Integration Readiness Judge - Evaluates readiness for SoT Engine integration."""

from __future__ import annotations

from typing import Any

from .base import BaseJudge, JudgeResult


class IntegrationReadinessJudge(BaseJudge):
    """Evaluates readiness for integration with the SoT Engine.

    Validates that:
    - Output schema is compatible with Caldera persistence layer
    - Required envelope fields are present
    - Data types are correct for DuckDB storage
    """

    @property
    def dimension_name(self) -> str:
        return "integration_readiness"

    @property
    def weight(self) -> float:
        return 0.10  # 10% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis and assess integration readiness."""
        all_results = self.load_all_analysis_results()
        if not all_results:
            return {"error": f"No analysis files found in {self.output_dir}"}

        integration_analysis: list[dict] = []

        # Required Caldera envelope fields (new format with metadata/data)
        metadata_fields = ["tool_name", "tool_version", "run_id", "repo_id", "branch", "commit", "timestamp", "schema_version"]
        data_fields = ["tool", "tool_version", "repo_name", "summary", "authors"]
        summary_fields = ["author_count", "total_loc", "hhi_index", "bus_factor", "top_author_pct"]

        for repo_name, repo_data in all_results.items():
            # Check metadata fields (new Caldera envelope format)
            metadata = repo_data.get("metadata", {})
            metadata_present = [f for f in metadata_fields if f in metadata]
            metadata_missing = [f for f in metadata_fields if f not in metadata]

            # Check data fields (new Caldera envelope format)
            data_section = repo_data.get("data", {})
            data_present = [f for f in data_fields if f in data_section]
            data_missing = [f for f in data_fields if f not in data_section]

            # Check summary fields
            summary = data_section.get("summary", {})
            summary_present = [f for f in summary_fields if f in summary]
            summary_missing = [f for f in summary_fields if f not in summary]

            # Validate data types
            type_issues: list[str] = []

            # Check schema_version format (now in metadata)
            schema_version = metadata.get("schema_version", "")
            if schema_version and not self._is_valid_semver(schema_version):
                type_issues.append(f"schema_version '{schema_version}' is not valid semver")

            # Check timestamp is ISO timestamp (now in metadata)
            timestamp = metadata.get("timestamp", "")
            if timestamp and not self._is_valid_timestamp(timestamp):
                type_issues.append(f"timestamp '{timestamp}' is not valid ISO timestamp")

            # Check numeric fields
            if summary:
                if not isinstance(summary.get("author_count", 0), int):
                    type_issues.append("author_count should be integer")
                if not isinstance(summary.get("total_loc", 0), int):
                    type_issues.append("total_loc should be integer")
                if not isinstance(summary.get("bus_factor", 0), int):
                    type_issues.append("bus_factor should be integer")

            # Calculate completeness scores
            metadata_score = len(metadata_present) / len(metadata_fields) * 100 if metadata_fields else 0
            data_score = len(data_present) / len(data_fields) * 100 if data_fields else 0
            summary_score = len(summary_present) / len(summary_fields) * 100 if summary_fields else 0

            integration_analysis.append({
                "repo": repo_name,
                "metadata": {
                    "present": metadata_present,
                    "missing": metadata_missing,
                    "score_pct": round(metadata_score, 1),
                },
                "data": {
                    "present": data_present,
                    "missing": data_missing,
                    "score_pct": round(data_score, 1),
                },
                "summary": {
                    "present": summary_present,
                    "missing": summary_missing,
                    "score_pct": round(summary_score, 1),
                },
                "type_issues": type_issues,
                "overall_score_pct": round((metadata_score + data_score + summary_score) / 3, 1),
            })

        # Calculate overall metrics
        total_repos = len(integration_analysis)
        avg_score = (
            sum(a["overall_score_pct"] for a in integration_analysis) / total_repos
            if total_repos > 0 else 0
        )
        repos_with_type_issues = sum(1 for a in integration_analysis if a["type_issues"])

        evidence = {
            "total_repos": total_repos,
            "avg_integration_score_pct": round(avg_score, 1),
            "repos_with_type_issues": repos_with_type_issues,
            "type_issue_rate_pct": round(repos_with_type_issues / total_repos * 100, 1) if total_repos > 0 else 0,
            "integration_analysis": integration_analysis,
            "required_metadata_fields": metadata_fields,
            "required_data_fields": data_fields,
            "required_summary_fields": summary_fields,
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
            evidence["interpretation_guidance"] = "Evaluate integration readiness."

        return evidence

    def _is_valid_semver(self, version: str) -> bool:
        """Check if version string is valid semver format."""
        import re
        return bool(re.match(r"^\d+\.\d+\.\d+", version))

    def _is_valid_timestamp(self, timestamp: str) -> bool:
        """Check if timestamp is valid ISO format."""
        import re
        # Basic ISO 8601 pattern
        return bool(re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", timestamp))

    def get_default_prompt(self) -> str:
        """Return the default prompt template if file doesn't exist."""
        return """# Integration Readiness Evaluation

You are evaluating git-fame output readiness for integration with the Caldera SoT Engine.

## Background

The SoT Engine requires:
- **Caldera Envelope Format**: Standard wrapper with metadata section (tool_name, tool_version, run_id, schema_version, timestamp) and data section
- **Data Structure**: Tool-specific data with tool, tool_version, repo_name, summary, authors
- **Summary Metrics**: Aggregate metrics (author_count, total_loc, hhi_index, bus_factor, top_author_pct)
- **Type Correctness**: Proper data types for DuckDB persistence

## Task

Evaluate how well git-fame output conforms to SoT Engine integration requirements.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

1. **Schema Completeness (40%)**: Are all required fields present?
   - 5: 100% of required fields present in all repos
   - 4: >95% field coverage
   - 3: 85-95% coverage
   - 2: 70-85% coverage
   - 1: <70% coverage

2. **Type Correctness (30%)**: Are data types correct?
   - 5: No type issues in any repo
   - 4: Minor type issues in <5% of repos
   - 3: Type issues in 5-15% of repos
   - 2: Type issues in 15-30% of repos
   - 1: Widespread type issues (>30%)

3. **Format Consistency (30%)**: Is output format consistent?
   - 5: All repos follow identical structure
   - 4: Minor structural variations
   - 3: Some structural inconsistencies
   - 2: Significant inconsistencies
   - 1: Highly inconsistent output

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific evidence points>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "schema_completeness": <1-5>,
    "type_correctness": <1-5>,
    "format_consistency": <1-5>
  }
}
"""

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run ground truth assertions before LLM evaluation."""
        failures = []
        all_results = self.load_all_analysis_results()

        # Required fields for valid Caldera envelope output
        required_metadata = ["tool_name", "schema_version", "timestamp"]
        required_data = ["summary", "authors"]

        for repo_name, repo_data in all_results.items():
            # Check metadata section
            metadata = repo_data.get("metadata", {})
            missing_metadata = [f for f in required_metadata if f not in metadata]
            if missing_metadata:
                failures.append(
                    f"{repo_name}: missing required metadata fields: {missing_metadata}"
                )

            # Check data section structure
            data_section = repo_data.get("data", {})
            if not data_section:
                failures.append(f"{repo_name}: missing data section")
            else:
                if "summary" not in data_section:
                    failures.append(f"{repo_name}: missing data.summary")
                if "authors" not in data_section:
                    failures.append(f"{repo_name}: missing data.authors")

        return len(failures) == 0, failures
