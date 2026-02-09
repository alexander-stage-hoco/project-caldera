"""Integration Judge - Evaluates schema compatibility and SoT integration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class IntegrationJudge(BaseJudge):
    """Evaluates schema compliance and SoT integration readiness.

    Validates that:
    - Output conforms to the defined JSON schema
    - All required fields are present
    - Data types are correct
    - Output can be ingested by the SoT pipeline
    """

    @property
    def dimension_name(self) -> str:
        return "integration"

    @property
    def weight(self) -> float:
        return 0.20  # 20% of total score

    def _load_schema(self) -> dict[str, Any] | None:
        """Load the output schema for validation."""
        schema_path = self.working_dir / "schemas" / "output.schema.json"
        if not schema_path.exists():
            return None
        try:
            return json.loads(schema_path.read_text())
        except json.JSONDecodeError:
            return None

    def _validate_file_record(self, file_record: dict) -> list[str]:
        """Validate a single file record against expected structure."""
        issues = []
        required_fields = [
            "path", "total_lines", "unique_authors", "top_author",
            "top_author_pct", "last_modified", "churn_30d", "churn_90d"
        ]

        for field in required_fields:
            if field not in file_record:
                issues.append(f"Missing required field: {field}")

        # Type validations
        if "total_lines" in file_record:
            if not isinstance(file_record["total_lines"], int):
                issues.append("total_lines should be integer")

        if "unique_authors" in file_record:
            if not isinstance(file_record["unique_authors"], int):
                issues.append("unique_authors should be integer")

        if "top_author_pct" in file_record:
            pct = file_record["top_author_pct"]
            if not isinstance(pct, (int, float)):
                issues.append("top_author_pct should be numeric")

        if "churn_30d" in file_record:
            if not isinstance(file_record["churn_30d"], int):
                issues.append("churn_30d should be integer")

        if "churn_90d" in file_record:
            if not isinstance(file_record["churn_90d"], int):
                issues.append("churn_90d should be integer")

        return issues

    def _validate_author_record(self, author_record: dict) -> list[str]:
        """Validate a single author record against expected structure."""
        issues = []
        required_fields = [
            "author_email", "total_files", "total_lines",
            "exclusive_files", "avg_ownership_pct"
        ]

        for field in required_fields:
            if field not in author_record:
                issues.append(f"Missing required field: {field}")

        # Type validations
        if "total_files" in author_record:
            if not isinstance(author_record["total_files"], int):
                issues.append("total_files should be integer")

        if "total_lines" in author_record:
            if not isinstance(author_record["total_lines"], int):
                issues.append("total_lines should be integer")

        if "exclusive_files" in author_record:
            if not isinstance(author_record["exclusive_files"], int):
                issues.append("exclusive_files should be integer")

        if "avg_ownership_pct" in author_record:
            pct = author_record["avg_ownership_pct"]
            if not isinstance(pct, (int, float)):
                issues.append("avg_ownership_pct should be numeric")

        return issues

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis and assess integration readiness."""
        all_results = self.load_all_analysis_results()
        if not all_results:
            return {"error": f"No analysis files found in {self.output_dir}"}

        schema = self._load_schema()
        schema_available = schema is not None

        # Validate all outputs
        total_files = 0
        total_authors = 0
        file_issues: list[dict] = []
        author_issues: list[dict] = []
        envelope_issues: list[dict] = []

        for repo_name, repo_data in all_results.items():
            files = self.extract_files(repo_data)
            authors = self.extract_authors(repo_data)
            summary = self.extract_summary(repo_data)

            total_files += len(files)
            total_authors += len(authors)

            # Validate envelope structure
            if "files" not in repo_data and "data" not in repo_data:
                envelope_issues.append({
                    "repo": repo_name,
                    "issue": "Missing files array in output",
                })

            if not summary:
                envelope_issues.append({
                    "repo": repo_name,
                    "issue": "Missing summary object",
                })

            # Validate file records (sample)
            for i, file_record in enumerate(files[:10]):
                issues = self._validate_file_record(file_record)
                if issues:
                    file_issues.append({
                        "repo": repo_name,
                        "path": file_record.get("path", f"file_{i}"),
                        "issues": issues,
                    })

            # Validate author records (sample)
            for i, author_record in enumerate(authors[:10]):
                issues = self._validate_author_record(author_record)
                if issues:
                    author_issues.append({
                        "repo": repo_name,
                        "author": author_record.get("author_email", f"author_{i}"),
                        "issues": issues,
                    })

        # Calculate validation rates
        file_issue_count = len(file_issues)
        author_issue_count = len(author_issues)
        file_valid_rate = (
            1.0 - (file_issue_count / max(total_files, 1))
        ) if total_files > 0 else 1.0
        author_valid_rate = (
            1.0 - (author_issue_count / max(total_authors, 1))
        ) if total_authors > 0 else 1.0

        evidence = {
            "total_repos": len(all_results),
            "total_files": total_files,
            "total_authors": total_authors,
            "schema_available": schema_available,
            "file_validation_rate": round(file_valid_rate, 4),
            "author_validation_rate": round(author_valid_rate, 4),
            "file_issues": file_issues[:10],
            "author_issues": author_issues[:10],
            "envelope_issues": envelope_issues,
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
            evidence["interpretation_guidance"] = (
                "Evaluate schema compliance for SoT integration."
            )

        return evidence

    def get_default_prompt(self) -> str:
        """Return the default prompt template."""
        return """# Integration Evaluation

You are an expert in data integration evaluating git-blame-scanner's schema compliance and SoT readiness.

## Task

Evaluate whether the git-blame-scanner output is suitable for integration into the Source-of-Truth (SoT) pipeline.

## Evidence

{{ evidence }}

## Evaluation Criteria

Rate on a scale of 1-5:

1. **Schema Compliance (40%)**: Does output match the expected schema?
   - 5: All records conform to schema with correct types
   - 4: Minor issues (<5% records)
   - 3: Some issues (5-15% records)
   - 2: Significant issues (15-30% records)
   - 1: Major schema violations (>30% records)

2. **Field Completeness (30%)**: Are all required fields present?
   - 5: All required fields present in all records
   - 4: Minor missing fields (<5%)
   - 3: Some missing fields (5-15%)
   - 2: Many missing fields (15-30%)
   - 1: Critical fields missing (>30%)

3. **Data Quality (30%)**: Are values well-formed and consistent?
   - 5: All values properly typed and consistent
   - 4: Minor type/consistency issues
   - 3: Some issues
   - 2: Significant issues
   - 1: Major data quality problems

## Response Format

Respond with ONLY a JSON object (no markdown fences):

{
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "<detailed explanation>",
  "evidence_cited": ["<specific evidence points>"],
  "recommendations": ["<improvement suggestions>"],
  "sub_scores": {
    "schema_compliance": <1-5>,
    "field_completeness": <1-5>,
    "data_quality": <1-5>
  }
}
"""

    def run_heuristic_evaluation(self, evidence: dict[str, Any]) -> JudgeResult:
        """Run heuristic-based evaluation without LLM."""
        file_rate = evidence.get("file_validation_rate", 0.0)
        author_rate = evidence.get("author_validation_rate", 0.0)
        envelope_issues = evidence.get("envelope_issues", [])

        # Calculate score based on validation rates
        avg_rate = (file_rate + author_rate) / 2

        if len(envelope_issues) > 0:
            avg_rate -= 0.1 * len(envelope_issues)  # Penalize envelope issues

        if avg_rate >= 0.95:
            score = 5
        elif avg_rate >= 0.85:
            score = 4
        elif avg_rate >= 0.70:
            score = 3
        elif avg_rate >= 0.50:
            score = 2
        else:
            score = 1

        return JudgeResult(
            dimension=self.dimension_name,
            score=score,
            confidence=0.8,
            reasoning=(
                f"File validation rate: {file_rate:.1%}, "
                f"Author validation rate: {author_rate:.1%}, "
                f"Envelope issues: {len(envelope_issues)}"
            ),
            evidence_cited=[
                f"File validation rate: {file_rate:.1%}",
                f"Author validation rate: {author_rate:.1%}",
            ],
            recommendations=[],
            sub_scores={
                "schema_compliance": score,
                "field_completeness": score,
                "data_quality": score,
            },
            raw_response="",
        )

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run ground truth assertions before LLM evaluation."""
        failures = []
        all_results = self.load_all_analysis_results()

        for repo_name, repo_data in all_results.items():
            files = self.extract_files(repo_data)
            authors = self.extract_authors(repo_data)

            # Check that we have data
            if not files and not authors:
                failures.append(f"{repo_name}: No files or authors in output")
                continue

            # Validate file records
            for i, file_record in enumerate(files[:5]):
                issues = self._validate_file_record(file_record)
                if issues:
                    path = file_record.get("path", f"file_{i}")
                    failures.append(f"{repo_name}/{path}: {', '.join(issues)}")

            # Validate author records
            for i, author_record in enumerate(authors[:5]):
                issues = self._validate_author_record(author_record)
                if issues:
                    author = author_record.get("author_email", f"author_{i}")
                    failures.append(f"{repo_name}/{author}: {', '.join(issues)}")

        return len(failures) == 0, failures
