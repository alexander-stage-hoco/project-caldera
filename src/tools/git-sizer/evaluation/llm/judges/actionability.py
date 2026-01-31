"""Actionability Judge - Evaluates clarity and usefulness of recommendations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class ActionabilityJudge(BaseJudge):
    """Evaluates actionability of repository health reports.

    Validates that:
    - LFS candidates are clearly identified
    - Violation messages are clear and actionable
    - Health grades help prioritization
    - Recommendations can be acted upon
    """

    @property
    def dimension_name(self) -> str:
        return "actionability"

    @property
    def weight(self) -> float:
        return 0.20  # 20% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Load analysis and evaluate actionability."""
        analysis = self.load_analysis()
        if "error" in analysis:
            return analysis

        repositories = analysis.get("repositories", [])

        # Extract LFS candidates
        lfs_candidates_summary = []
        total_lfs_candidates = 0
        for repo in repositories:
            candidates = repo.get("lfs_candidates", [])
            total_lfs_candidates += len(candidates)
            if candidates:
                lfs_candidates_summary.append({
                    "repository": repo.get("repository", "unknown"),
                    "candidate_count": len(candidates),
                    "candidates": candidates[:10],  # First 10
                })

        # Analyze violation messages
        violation_messages = []
        for repo in repositories:
            for violation in repo.get("violations", []):
                violation_messages.append({
                    "repository": repo.get("repository", ""),
                    "metric": violation.get("metric", ""),
                    "value": violation.get("value", ""),
                    "level": violation.get("level", 0),
                    "raw_value": violation.get("raw_value", 0),
                    "object_ref": violation.get("object_ref", ""),
                    "has_metric": bool(violation.get("metric")),
                    "has_value": bool(violation.get("value")),
                    "has_object_ref": bool(violation.get("object_ref")),
                })

        # Evaluate message quality
        message_quality = {
            "total_violations": len(violation_messages),
            "with_object_ref": sum(1 for v in violation_messages if v["has_object_ref"]),
            "with_metric": sum(1 for v in violation_messages if v["has_metric"]),
            "with_value": sum(1 for v in violation_messages if v["has_value"]),
        }

        # Health grade coverage
        grade_coverage = []
        for repo in repositories:
            grade = repo.get("health_grade", "")
            violations = len(repo.get("violations", []))
            lfs = len(repo.get("lfs_candidates", []))
            grade_coverage.append({
                "repository": repo.get("repository", ""),
                "health_grade": grade,
                "has_grade": bool(grade),
                "violation_count": violations,
                "lfs_candidate_count": lfs,
            })

        # Calculate actionability metrics
        repos_with_grades = sum(1 for g in grade_coverage if g["has_grade"])
        grade_coverage_pct = (repos_with_grades / len(repositories) * 100) if repositories else 0

        # Check for actionable information
        actionable_info = {
            "lfs_recommendations": total_lfs_candidates > 0,
            "threshold_warnings": message_quality["total_violations"] > 0,
            "all_repos_graded": repos_with_grades == len(repositories),
        }

        summary = analysis.get("summary", {})

        return {
            "lfs_candidates_summary": lfs_candidates_summary,
            "total_lfs_candidates": total_lfs_candidates,
            "violation_messages": violation_messages,
            "message_quality": message_quality,
            "grade_coverage": grade_coverage,
            "grade_coverage_pct": round(grade_coverage_pct, 1),
            "actionable_info": actionable_info,
            "total_repositories": len(repositories),
            "total_violations": summary.get("total_violations", 0),
        }

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Validate actionability requirements."""
        failures = []

        analysis = self.load_analysis()
        if "error" in analysis:
            failures.append(analysis["error"])
            return False, failures

        # Check all repos have health grades
        for repo in analysis.get("repositories", []):
            if not repo.get("health_grade"):
                failures.append(
                    f"Repository {repo.get('repository')} missing health grade"
                )

        # Check violations have required fields
        for repo in analysis.get("repositories", []):
            for violation in repo.get("violations", []):
                if not violation.get("metric"):
                    failures.append(
                        f"Violation in {repo.get('repository')} missing metric"
                    )
                if not violation.get("level"):
                    failures.append(
                        f"Violation in {repo.get('repository')} missing level"
                    )

        # Check bloated repo has LFS candidates
        for repo in analysis.get("repositories", []):
            name = repo.get("repository", "")
            if "bloated" in name.lower():
                candidates = repo.get("lfs_candidates", [])
                if len(candidates) == 0:
                    failures.append(
                        f"Bloated repo should have LFS candidates identified"
                    )

        return len(failures) == 0, failures

    def get_default_prompt(self) -> str:
        return '''# Actionability Judge

You are evaluating the **actionability** of git-sizer's repository health reports.

## Evaluation Dimension
**Actionability (20% weight)**: Can developers easily understand and act on the findings?

## Background
Actionable reports should:
- Clearly identify files that should use Git LFS
- Explain what threshold violations mean
- Provide health grades for quick prioritization
- Enable teams to make informed decisions

Good actionability examples:
- "5 files over 1 MiB identified as LFS candidates"
- "max_blob_size: 10.2 MiB exceeds threshold (level: 3)"
- "Health Grade: C+ - Large binary files detected"

Poor actionability:
- "Repository has issues"
- "Size: large"

## Scoring Rubric
| Score | Criteria |
|-------|----------|
| 5 | Clear LFS recommendations, detailed violations, actionable grades |
| 4 | Good recommendations, clear messages, useful grades |
| 3 | Adequate information, some gaps in clarity |
| 2 | Vague messages, limited actionable information |
| 1 | Unclear findings, no actionable recommendations |

## Sub-Dimensions
1. **LFS Recommendations (40%)**: Clear identification of LFS candidates
2. **Violation Clarity (30%)**: Messages explain issues clearly
3. **Prioritization Support (30%)**: Grades enable quick assessment

## Evidence to Evaluate

### LFS Candidates Summary
```json
{{ lfs_candidates_summary }}
```
- Total LFS candidates identified: {{ total_lfs_candidates }}

### Violation Messages
```json
{{ violation_messages }}
```

### Message Quality Metrics
```json
{{ message_quality }}
```

### Grade Coverage
```json
{{ grade_coverage }}
```
- Repositories with grades: {{ grade_coverage_pct }}%

### Actionable Information
```json
{{ actionable_info }}
```

## Evaluation Questions
1. Are LFS candidates clearly identified with file names/paths?
2. Do violation messages explain what the metric means?
3. Are threshold values and current values both shown?
4. Do health grades help quickly identify problematic repos?

## Required Output Format
Respond with ONLY a JSON object:
```json
{
  "dimension": "actionability",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of actionability assessment",
  "evidence_cited": ["specific actionable elements examined"],
  "recommendations": ["improvements for actionability"],
  "sub_scores": {
    "lfs_recommendations": <1-5>,
    "violation_clarity": <1-5>,
    "prioritization_support": <1-5>
  }
}
```
'''

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline."""
        return super().evaluate()
