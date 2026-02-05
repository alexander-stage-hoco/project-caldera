"""Statistics Judge - Evaluates distribution metrics validity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class StatisticsJudge(BaseJudge):
    """Evaluates validity of statistical metrics.

    Assesses whether distribution statistics (percentiles, Gini, skewness)
    are mathematically valid and meaningful.
    """

    @property
    def dimension_name(self) -> str:
        return "statistics"

    @property
    def weight(self) -> float:
        return 0.20  # 20% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Collect statistical evidence."""
        # Handle missing analysis file with default values for all placeholders
        if not self.analysis_path.exists():
            evidence: dict[str, Any] = {
                "error": f"Analysis file not found: {self.analysis_path}",
                "ccn_distribution": {},
                "nloc_distribution": {},
                "params_distribution": {},
                "total_functions": 0,
                "total_files": 0,
                "directory_statistics": [],
                "structure": {},
                "evaluation_mode": self.evaluation_mode,
            }
            # Inject synthetic context even when analysis is missing
            if self.evaluation_mode == "real_world":
                synthetic_context = self.load_synthetic_evaluation_context()
                if synthetic_context:
                    evidence["synthetic_baseline"] = synthetic_context
                    evidence["interpretation_guidance"] = self.get_interpretation_guidance(
                        synthetic_context
                    )
                else:
                    evidence["synthetic_baseline"] = "No synthetic baseline available"
                    evidence["interpretation_guidance"] = (
                        "Evaluate based on ground truth comparison only"
                    )
            else:
                evidence["synthetic_baseline"] = (
                    "N/A - synthetic mode uses direct ground truth comparison"
                )
                evidence["interpretation_guidance"] = "Strict ground truth evaluation"
            return evidence

        analysis = self._load_analysis()

        summary = analysis.get("summary", {})

        # Collect distribution data
        ccn_dist = summary.get("ccn_distribution", {})
        nloc_dist = summary.get("nloc_distribution", {})
        params_dist = summary.get("params_distribution", {})

        # Sample directory-level statistics
        directory_stats = []
        for dir_info in analysis.get("directories", [])[:5]:
            dir_stat = {
                "path": dir_info.get("path", ""),
                "name": dir_info.get("name", ""),
                "recursive_ccn_dist": dir_info.get("recursive", {}).get("ccn_distribution", {}),
                "direct_ccn_dist": dir_info.get("direct", {}).get("ccn_distribution", {}),
            }
            directory_stats.append(dir_stat)

        return {
            "ccn_distribution": ccn_dist,
            "nloc_distribution": nloc_dist,
            "params_distribution": params_dist,
            "total_functions": summary.get("total_functions", 0),
            "total_files": summary.get("total_files", 0),
            "directory_statistics": directory_stats,
            "structure": summary.get("structure", {}),
        }

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Validate statistical properties."""
        failures = []

        if not self.analysis_path.exists():
            failures.append(f"Analysis file not found: {self.analysis_path}")
            return False, failures

        try:
            analysis = self._load_analysis()
        except json.JSONDecodeError as e:
            failures.append(f"Invalid JSON: {e}")
            return False, failures

        summary = analysis.get("summary", {})

        # Check CCN distribution
        ccn_dist = summary.get("ccn_distribution", {})
        if ccn_dist:
            failures.extend(self._validate_distribution(ccn_dist, "CCN"))

        # Check NLOC distribution
        nloc_dist = summary.get("nloc_distribution", {})
        if nloc_dist:
            failures.extend(self._validate_distribution(nloc_dist, "NLOC"))

        # Check directory-level statistics
        for dir_info in analysis.get("directories", []):
            path = dir_info.get("path", "unknown")
            rec_dist = dir_info.get("recursive", {}).get("ccn_distribution", {})
            if rec_dist:
                dir_failures = self._validate_distribution(rec_dist, f"Dir {path}")
                failures.extend(dir_failures[:2])  # Limit directory errors

        return len(failures) == 0, failures

    def _validate_distribution(self, dist: dict, name: str) -> list[str]:
        """Validate a distribution's statistical properties."""
        failures = []

        # Check basic stats exist
        required = ["min", "max", "mean", "median"]
        missing = [f for f in required if f not in dist]
        if missing:
            failures.append(f"{name}: missing required fields: {missing}")
            return failures

        min_val = dist.get("min", 0)
        max_val = dist.get("max", 0)
        mean = dist.get("mean", 0)
        median = dist.get("median", 0)

        # Check min <= median <= max
        if min_val > median:
            failures.append(f"{name}: min ({min_val}) > median ({median})")
        if median > max_val:
            failures.append(f"{name}: median ({median}) > max ({max_val})")
        if min_val > max_val:
            failures.append(f"{name}: min ({min_val}) > max ({max_val})")

        # Check mean is between min and max
        if mean < min_val or mean > max_val:
            failures.append(f"{name}: mean ({mean}) outside [min, max] range")

        # Check percentiles are monotonic
        percentiles = ["p25", "p50", "p75", "p90", "p95", "p99"]
        prev_val = min_val
        for p in percentiles:
            if p in dist:
                val = dist[p]
                if val < prev_val:
                    failures.append(f"{name}: {p} ({val}) < previous percentile ({prev_val})")
                if val > max_val:
                    failures.append(f"{name}: {p} ({val}) > max ({max_val})")
                prev_val = val

        # Check Gini is in [0, 1]
        gini = dist.get("gini")
        if gini is not None and (gini < 0 or gini > 1):
            failures.append(f"{name}: Gini ({gini}) not in [0, 1]")

        # Check stddev is non-negative
        stddev = dist.get("stddev")
        if stddev is not None and stddev < 0:
            failures.append(f"{name}: stddev ({stddev}) is negative")

        # Check CV is non-negative
        cv = dist.get("cv")
        if cv is not None and cv < 0:
            failures.append(f"{name}: CV ({cv}) is negative")

        return failures

    def get_default_prompt(self) -> str:
        return '''# Statistics Judge

You are evaluating the **statistical validity** of metrics computed by Lizard function analysis.

## Evaluation Dimension
**Statistics (20% weight)**: Are distribution statistics mathematically valid and meaningful?

## Background
The analysis computes comprehensive distribution statistics:
- Basic stats: min, max, mean, median, stddev
- Percentiles: p25, p50, p75, p90, p95, p99
- Shape metrics: skewness, kurtosis, CV (coefficient of variation)
- Inequality metrics: Gini coefficient, Theil index

## Statistical Validity Rules
1. min <= p25 <= p50 <= p75 <= p90 <= p95 <= p99 <= max
2. mean must be between min and max
3. stddev >= 0
4. Gini coefficient must be in [0, 1]
5. CV = stddev / mean (when mean > 0)

## Scoring Rubric
| Score | Criteria |
|-------|----------|
| 5 | All statistics valid, comprehensive metrics |
| 4 | Minor issues (1-2 missing/invalid fields) |
| 3 | Basic stats valid, advanced metrics questionable |
| 2 | Multiple statistical errors or inconsistencies |
| 1 | Statistics are unreliable or invalid |

## Sub-Dimensions
1. **Basic Statistics (40%)**: min, max, mean, median, stddev
2. **Percentiles (30%)**: Monotonicity and validity
3. **Advanced Metrics (30%)**: Gini, skewness, kurtosis

## Evidence to Evaluate

### Summary-Level CCN Distribution
```json
{{ ccn_distribution }}
```

### Summary-Level NLOC Distribution
```json
{{ nloc_distribution }}
```

### Parameter Count Distribution
```json
{{ params_distribution }}
```

### Directory-Level Statistics Sample
```json
{{ directory_statistics }}
```

### Overall Counts
- Total functions: {{ total_functions }}
- Total files: {{ total_files }}
- Structure: {{ structure }}

## Evaluation Questions
1. Are percentiles monotonically increasing?
2. Is the mean within the [min, max] range?
3. Are inequality metrics (Gini) in valid ranges?
4. Are directory-level statistics consistent with file-level?

## Required Output Format
Respond with ONLY a JSON object:
```json
{
  "dimension": "statistics",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of statistical validity",
  "evidence_cited": ["specific metrics examined"],
  "recommendations": ["improvements"],
  "sub_scores": {
    "basic_statistics": <1-5>,
    "percentiles": <1-5>,
    "advanced_metrics": <1-5>
  }
}
```
'''

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline.

        Delegates to base class implementation which:
        1. Collects evidence via collect_evidence()
        2. Builds prompt from template
        3. Invokes Claude for evaluation
        4. Parses response into JudgeResult
        """
        return super().evaluate()
