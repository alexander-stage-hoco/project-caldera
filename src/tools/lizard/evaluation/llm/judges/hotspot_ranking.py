"""Hotspot Ranking Judge - Evaluates hotspot identification quality."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


class HotspotRankingJudge(BaseJudge):
    """Evaluates quality of hotspot identification.

    Assesses whether high-complexity functions are correctly identified
    and ranked as potential refactoring targets.
    """

    @property
    def dimension_name(self) -> str:
        return "hotspot_ranking"

    @property
    def weight(self) -> float:
        return 0.20  # 20% of total score

    def collect_evidence(self) -> dict[str, Any]:
        """Collect hotspot ranking evidence."""
        if not self.analysis_path.exists():
            return {"error": f"Analysis file not found: {self.analysis_path}"}

        analysis = self._load_analysis()

        # Collect all functions with their metrics
        all_functions = []
        for file_info in analysis.get("files", []):
            for func in file_info.get("functions", []):
                all_functions.append({
                    "file": file_info["path"],
                    "name": func["name"],
                    "ccn": func["ccn"],
                    "nloc": func["nloc"],
                    "params": func.get("parameter_count", 0),
                    "language": file_info.get("language", "unknown"),
                })

        # Sort by CCN descending to get hotspots
        sorted_by_ccn = sorted(all_functions, key=lambda x: x["ccn"], reverse=True)
        top_by_ccn = sorted_by_ccn[:10]

        # Sort by NLOC descending
        sorted_by_nloc = sorted(all_functions, key=lambda x: x["nloc"], reverse=True)
        top_by_nloc = sorted_by_nloc[:10]

        # Sort by parameter count descending
        sorted_by_params = sorted(all_functions, key=lambda x: x["params"], reverse=True)
        top_by_params = sorted_by_params[:5]

        # Compute thresholds
        summary = analysis.get("summary", {})
        ccn_dist = summary.get("ccn_distribution", {})

        threshold_10 = len([f for f in all_functions if f["ccn"] > 10])
        threshold_20 = len([f for f in all_functions if f["ccn"] > 20])

        # Directory-level hotspots
        dir_hotspots = []
        for dir_info in analysis.get("directories", []):
            rec = dir_info.get("recursive", {})
            if rec.get("function_count", 0) > 0:
                dir_hotspots.append({
                    "path": dir_info.get("path", ""),
                    "name": dir_info.get("name", ""),
                    "total_ccn": rec.get("ccn", 0),
                    "avg_ccn": rec.get("avg_ccn", 0),
                    "max_ccn": rec.get("max_ccn", 0),
                    "functions": rec.get("function_count", 0),
                    "over_threshold": rec.get("functions_over_threshold", 0),
                })

        # Sort directories by total CCN
        dir_hotspots = sorted(dir_hotspots, key=lambda x: x["total_ccn"], reverse=True)

        return {
            "top_functions_by_ccn": top_by_ccn,
            "top_functions_by_nloc": top_by_nloc,
            "top_functions_by_params": top_by_params,
            "functions_over_10": threshold_10,
            "functions_over_20": threshold_20,
            "total_functions": len(all_functions),
            "ccn_distribution": ccn_dist,
            "directory_hotspots": dir_hotspots[:5],
            "max_ccn_overall": ccn_dist.get("max", 0),
            "p95_ccn": ccn_dist.get("p95", 0),
        }

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Validate hotspot identification."""
        failures = []

        if not self.analysis_path.exists():
            failures.append(f"Analysis file not found: {self.analysis_path}")
            return False, failures

        try:
            analysis = self._load_analysis()
        except json.JSONDecodeError as e:
            failures.append(f"Invalid JSON: {e}")
            return False, failures

        # Collect all functions
        all_functions = []
        for file_info in analysis.get("files", []):
            for func in file_info.get("functions", []):
                all_functions.append({
                    "file": file_info["path"],
                    "name": func["name"],
                    "ccn": func["ccn"],
                })

        if not all_functions:
            failures.append("No functions found for hotspot analysis")
            return False, failures

        # Check that max CCN in distribution matches actual max
        ccn_dist = analysis.get("summary", {}).get("ccn_distribution", {})
        reported_max = ccn_dist.get("max", 0)
        actual_max = max(f["ccn"] for f in all_functions)

        if reported_max != actual_max:
            failures.append(
                f"Reported max CCN ({reported_max}) != actual max ({actual_max})"
            )

        # Check that we have some high-complexity functions (CCN > 10)
        high_ccn_count = len([f for f in all_functions if f["ccn"] > 10])
        if high_ccn_count == 0:
            # This is informational, not necessarily a failure
            pass

        # Check directory hotspots are consistent
        for dir_info in analysis.get("directories", []):
            rec = dir_info.get("recursive", {})
            reported_max_ccn = rec.get("max_ccn", 0)
            total_ccn = rec.get("ccn", 0)
            func_count = rec.get("function_count", 0)

            if func_count > 0 and reported_max_ccn > total_ccn:
                failures.append(
                    f"Dir {dir_info.get('path')}: max_ccn ({reported_max_ccn}) > "
                    f"total_ccn ({total_ccn})"
                )

        return len(failures) == 0, failures

    def get_default_prompt(self) -> str:
        return '''# Hotspot Ranking Judge

You are evaluating the **hotspot identification quality** of Lizard function analysis.

## Evaluation Dimension
**Hotspot Ranking (20% weight)**: Are high-complexity functions correctly identified as hotspots?

## Background
Hotspots are functions that may need refactoring due to:
- High cyclomatic complexity (CCN > 10 is concerning, > 20 is critical)
- Large size (high NLOC)
- Many parameters (> 5 is a code smell)

Good hotspot identification should:
1. Rank functions by complexity metrics
2. Flag functions exceeding thresholds
3. Identify directory-level complexity concentration

## Scoring Rubric
| Score | Criteria |
|-------|----------|
| 5 | Hotspots correctly identified, good ranking, clear thresholds |
| 4 | Minor ranking issues, thresholds mostly correct |
| 3 | Major hotspots identified, some ranking/threshold issues |
| 2 | Hotspot identification is incomplete or inconsistent |
| 1 | Hotspot identification is unreliable |

## Sub-Dimensions
1. **CCN Hotspots (40%)**: High-CCN functions identified
2. **Multi-Metric (30%)**: NLOC and parameter hotspots
3. **Directory-Level (30%)**: Complexity concentration identified

## Evidence to Evaluate

### Top Functions by CCN (Hotspots)
```json
{{ top_functions_by_ccn }}
```

### Top Functions by NLOC (Size)
```json
{{ top_functions_by_nloc }}
```

### Top Functions by Parameters
```json
{{ top_functions_by_params }}
```

### Threshold Violations
- Functions with CCN > 10: {{ functions_over_10 }}
- Functions with CCN > 20: {{ functions_over_20 }}
- Total functions: {{ total_functions }}

### CCN Distribution Reference
- Max CCN: {{ max_ccn_overall }}
- P95 CCN: {{ p95_ccn }}
```json
{{ ccn_distribution }}
```

### Directory-Level Hotspots
```json
{{ directory_hotspots }}
```

## Evaluation Questions
1. Are the highest-CCN functions correctly at the top?
2. Is there correlation between CCN hotspots and NLOC hotspots?
3. Are directory-level concentrations visible?
4. Do the threshold counts match the distribution data?

## Required Output Format
Respond with ONLY a JSON object:
```json
{
  "dimension": "hotspot_ranking",
  "score": <1-5>,
  "confidence": <0.0-1.0>,
  "reasoning": "detailed explanation of hotspot identification quality",
  "evidence_cited": ["specific hotspots examined"],
  "recommendations": ["improvements"],
  "sub_scores": {
    "ccn_hotspots": <1-5>,
    "multi_metric": <1-5>,
    "directory_level": <1-5>
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
