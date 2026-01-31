"""Integration Fit Judge - Evaluates compatibility with Caldera Platform."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class IntegrationFitJudge(BaseJudge):
    """Evaluates how well git-sizer fits Caldera Platform integration.

    Validates that:
    - Output structure is compatible with Caldera storage
    - Metrics map to Caldera SoT schema
    - Performance is acceptable for pipeline
    - No overlap with existing Caldera collectors
    """

    @property
    def dimension_name(self) -> str:
        return "integration_fit"

    @property
    def weight(self) -> float:
        return 0.20  # 20% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Analyze output structure for Caldera Platform compatibility."""
        analysis = self.load_analysis()
        if "error" in analysis:
            return analysis

        # Schema compatibility check
        required_fields = ["timestamp", "target_path", "repositories", "summary"]
        repo_required_fields = ["repository", "health_grade", "metrics", "violations"]
        metric_fields = [
            "blob_count", "blob_total_size", "max_blob_size",
            "tree_count", "max_tree_entries", "commit_count",
            "max_path_depth", "max_path_length",
        ]

        schema_check = {
            "top_level_fields": {
                field: field in analysis for field in required_fields
            },
            "top_level_complete": all(field in analysis for field in required_fields),
        }

        # Check repo structure
        repos = analysis.get("repositories", [])
        if repos:
            sample_repo = repos[0]
            schema_check["repo_fields"] = {
                field: field in sample_repo for field in repo_required_fields
            }
            schema_check["repo_complete"] = all(
                field in sample_repo for field in repo_required_fields
            )

            # Check metrics coverage
            sample_metrics = sample_repo.get("metrics", {})
            schema_check["metric_fields"] = {
                field: field in sample_metrics for field in metric_fields
            }
            schema_check["metric_coverage"] = sum(
                1 for f in metric_fields if f in sample_metrics
            ) / len(metric_fields) * 100

        # Caldera Platform integration mapping
        caldera_mapping = {
            "repository_level": {
                "health_grade": "lz_git_sizer_metrics.health_grade",
                "blob_total_size": "lz_git_sizer_metrics.blob_total_size",
                "max_blob_size": "lz_git_sizer_metrics.max_blob_size",
                "commit_count": "lz_git_sizer_metrics.commit_count",
                "lfs_candidates": "lz_git_sizer_lfs_candidates[]",
                "violations": "lz_git_sizer_violations[]",
            },
            "gap_analysis": {
                "fills_gap": True,
                "gaps_addressed": [
                    "Repository-level health scoring",
                    "Blob size analysis (LFS candidates)",
                    "Object count and efficiency",
                    "Path depth analysis",
                ],
                "overlaps": [
                    "commit_count (can be derived from git history)",
                ],
                "unique_metrics": [
                    "health_grade",
                    "blob_total_size",
                    "max_blob_size",
                    "max_tree_entries",
                    "max_path_depth",
                    "lfs_candidates",
                ],
            },
        }

        # Performance assessment
        summary = analysis.get("summary", {})
        total_duration_ms = summary.get("total_duration_ms", 0)
        repo_count = len(repos)
        avg_duration = total_duration_ms / repo_count if repo_count > 0 else 0

        performance = {
            "total_duration_ms": total_duration_ms,
            "repo_count": repo_count,
            "avg_duration_per_repo_ms": round(avg_duration, 1),
            "meets_threshold": total_duration_ms < 10000,  # < 10s for all repos
            "fast_enough_for_pipeline": avg_duration < 2000,  # < 2s per repo
        }

        # Output format assessment
        output_format = {
            "json_valid": True,  # If we got here, JSON is valid
            "raw_output_preserved": all(
                repo.get("raw_output") is not None for repo in repos
            ),
            "nested_structures": bool(repos and repos[0].get("metrics")),
            "array_fields": ["repositories", "violations", "lfs_candidates"],
        }

        return {
            "schema_check": schema_check,
            "caldera_mapping": caldera_mapping,
            "performance": performance,
            "output_format": output_format,
            "total_repositories": repo_count,
            "existing_caldera_tools": [
                "scc (file-level LOC)",
                "lizard (function-level CCN)",
                "semgrep (code smells)",
                "trivy (vulnerabilities)",
                "sonarqube (quality analysis)",
            ],
            "git_sizer_adds": [
                "repository-level health grade",
                "LFS candidate identification",
                "threshold violation detection",
                "blob/tree/path analysis",
            ],
        }

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Validate integration fit requirements."""
        failures = []

        analysis = self.load_analysis()
        if "error" in analysis:
            failures.append(analysis["error"])
            return False, failures

        # Check required top-level fields (may be normalized from envelope)
        required_fields = ["timestamp", "target_path", "repositories", "summary"]
        for field in required_fields:
            if field not in analysis:
                failures.append(f"Missing required field: {field}")

        # Check repository structure
        for repo in analysis.get("repositories", []):
            if not repo.get("repository"):
                failures.append("Repository missing 'repository' field")
            if not repo.get("health_grade"):
                failures.append(f"Repository {repo.get('repository')} missing health_grade")
            if not repo.get("metrics"):
                failures.append(f"Repository {repo.get('repository')} missing metrics")

        # Check performance
        summary = analysis.get("summary", {})
        duration = summary.get("total_duration_ms", 0)
        if duration > 60000:  # 60 seconds max
            failures.append(f"Performance too slow: {duration}ms > 60000ms")

        return len(failures) == 0, failures

    def get_default_prompt(self) -> str:
        return '''# Integration Fit Judge

You are evaluating the **integration fit** of git-sizer for the Caldera Platform.

## Evaluation Dimension
**Integration Fit (20% weight)**: How well does git-sizer integrate with Caldera Platform?

## Background
The Caldera Platform is a code analysis system with:
- Envelope format output (metadata + data)
- DuckDB storage via landing zone tables
- Existing tools: scc (LOC), lizard (CCN), semgrep (smells), trivy (vulns), sonarqube
- File-level and function-level metrics already covered

git-sizer should:
- Fill gaps (not duplicate existing metrics)
- Use compatible output formats (envelope)
- Meet performance requirements
- Add unique repository-level insights

## Scoring Rubric
| Score | Criteria |
|-------|----------|
| 5 | Perfect fit - fills clear gap, compatible schema, fast performance |
| 4 | Good fit - minor schema adjustments needed, performs well |
| 3 | Acceptable fit - some gaps remain, moderate adjustments needed |
| 2 | Poor fit - significant overlap or incompatibilities |
| 1 | Does not fit - major conflicts with existing architecture |

## Sub-Dimensions
1. **Gap Coverage (40%)**: Fills gaps in existing Caldera capabilities
2. **Schema Compatibility (30%)**: Output maps to Caldera storage schema
3. **Performance (30%)**: Fast enough for pipeline integration

## Evidence to Evaluate

### Schema Compatibility Check
```json
{{ schema_check }}
```

### Caldera Platform Mapping
```json
{{ caldera_mapping }}
```

### Performance Assessment
```json
{{ performance }}
```

### Output Format
```json
{{ output_format }}
```

### Existing Caldera Tools
```json
{{ existing_caldera_tools }}
```

### What git-sizer Adds
```json
{{ git_sizer_adds }}
```

## Evaluation Questions
1. Does git-sizer fill a clear gap in Caldera Platform capabilities?
2. Can the output schema map directly to Caldera storage tables?
3. Is performance acceptable for pipeline integration?
4. Is there minimal overlap with existing collectors?

## Required Output Format
Respond with ONLY a JSON object:
```json
{
  "dimension": "integration_fit",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of integration fit assessment",
  "evidence_cited": ["specific compatibility factors examined"],
  "recommendations": ["integration improvements"],
  "sub_scores": {
    "gap_coverage": <1-5>,
    "schema_compatibility": <1-5>,
    "performance": <1-5>
  }
}
```
'''

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline."""
        return super().evaluate()
