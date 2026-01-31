"""Directory Analysis Judge - evaluates directory tree aggregation quality."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseJudge, JudgeResult


def find_directory_analysis_file(output_dir: Path) -> Path | None:
    """Find directory analysis file in multiple possible locations.

    Checks (in order):
    1. outputs/<run-id>/directory_analysis_eval.json
    2. outputs/<run-id>/directory_analysis.json
    3. output/directory_analysis.json (legacy)
    """
    candidates = [
        output_dir / "directory_analysis_eval.json",
        output_dir / "directory_analysis.json",
        output_dir / "runs" / "synthetic.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


class DirectoryAnalysisJudge(BaseJudge):
    """Evaluates the quality of directory tree analysis.

    Key distinction:
    - direct: Files ONLY in that specific directory (not subdirectories)
    - recursive: ALL files in the directory tree starting at that directory
    """

    @property
    def dimension_name(self) -> str:
        return "directory_analysis"

    @property
    def weight(self) -> float:
        return 0.14  # 14%

    def get_default_prompt(self) -> str:
        return """# Directory Analysis Judge

Evaluate directory tree analysis quality. Score 1-5:
- 5: Direct/recursive stats clearly distinguished, accurate rollups
- 4: Mostly accurate, useful for analysis
- 3: Basic stats but aggregation issues
- 2: Significant errors
- 1: Unusable

Sub-dimensions:
- Structural Integrity (30%)
- Statistical Validity (30%)
- Aggregation Correctness (20%)
- Output Interpretability (20%)

Respond with JSON including sub_scores.
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect directory analysis evidence."""
        output_dir = self._resolve_output_dir()

        # Load directory analysis
        full_data = {}
        dir_file = find_directory_analysis_file(output_dir)
        if dir_file is not None:
            raw_data = json.loads(dir_file.read_text())
            # Handle nested 'results' wrapper structure
            if "results" in raw_data and "directories" not in raw_data:
                full_data = raw_data["results"]
            else:
                full_data = raw_data

        # Compute invariants
        directories = full_data.get("directories", [])
        summary = full_data.get("summary", {})
        total_files = summary.get("total_files", 0)

        # Sum of direct file counts
        sum_direct_files = sum(d.get("direct", {}).get("file_count", 0) for d in directories)

        # Check recursive >= direct
        recursive_gte_direct = all(
            d.get("recursive", {}).get("file_count", 0) >= d.get("direct", {}).get("file_count", 0)
            for d in directories
        )

        # Check computed ratios are valid (non-negative)
        computed_ratios_valid = True
        for d in directories:
            recursive = d.get("recursive", {})
            if recursive.get("file_count", 0) > 0:
                if recursive.get("avg_complexity", 0) < 0:
                    computed_ratios_valid = False
                    break
                if recursive.get("dryness", 0) < 0:
                    computed_ratios_valid = False
                    break

        # Check percentile monotonicity
        percentiles_monotonic = True
        for d in directories:
            loc_dist = d.get("recursive", {}).get("loc_distribution")
            if loc_dist:
                p25 = loc_dist.get("p25", 0)
                median = loc_dist.get("median", 0)
                p75 = loc_dist.get("p75", 0)
                p90 = loc_dist.get("p90", 0)
                p95 = loc_dist.get("p95", 0)
                if not (p25 <= median <= p75 <= p90 <= p95):
                    percentiles_monotonic = False
                    break

        # v2.0 invariants
        inequality_metrics_valid = True
        classification_sum_matches = True
        lang_loc_sum_matches = True
        cocomo_ordered = True

        # Check inequality metrics in range
        for d in directories:
            for dist_name in ["loc_distribution", "complexity_distribution"]:
                dist = d.get("recursive", {}).get(dist_name) or {}
                gini = dist.get("gini")
                if gini is not None and (gini < 0 or gini > 1):
                    inequality_metrics_valid = False

        # Check classification sum
        fc = summary.get("file_classifications", {})
        class_sum = (fc.get("test_file_count", 0) + fc.get("config_file_count", 0) +
                     fc.get("docs_file_count", 0) + fc.get("build_file_count", 0) +
                     fc.get("ci_file_count", 0) + fc.get("source_file_count", 0))
        if class_sum != total_files:
            classification_sum_matches = False

        # Check language LOC sum
        by_lang = summary.get("languages", {}).get("by_loc", {})
        lang_sum = sum(by_lang.values()) if isinstance(by_lang, dict) else 0
        total_loc = summary.get("total_loc", 0)
        if lang_sum != total_loc:
            lang_loc_sum_matches = False

        # Check COCOMO ordering
        cocomo = summary.get("cocomo", {})
        if cocomo:
            efforts = [
                cocomo.get("early_startup", {}).get("effort", 0),
                cocomo.get("growth_startup", {}).get("effort", 0),
                cocomo.get("scale_up", {}).get("effort", 0),
                cocomo.get("sme", {}).get("effort", 0),
                cocomo.get("mid_market", {}).get("effort", 0),
                cocomo.get("large_enterprise", {}).get("effort", 0),
                cocomo.get("regulated", {}).get("effort", 0),
            ]
            cocomo_ordered = all(efforts[i] <= efforts[i+1] for i in range(len(efforts)-1))

        # Create focused sample (first 3 directories with their structure)
        sample_dirs = []
        for d in directories[:3]:
            sample_dirs.append({
                "path": d.get("path"),
                "depth": d.get("depth"),
                "is_leaf": d.get("is_leaf"),
                "child_count": d.get("child_count"),
                "direct": {
                    "file_count": d.get("direct", {}).get("file_count"),
                    "lines_code": d.get("direct", {}).get("lines_code"),
                },
                "recursive": {
                    "file_count": d.get("recursive", {}).get("file_count"),
                    "lines_code": d.get("recursive", {}).get("lines_code"),
                    "complexity_total": d.get("recursive", {}).get("complexity_total"),
                },
            })

        # Create focused analysis object (summary only, not full directories)
        directory_analysis = {
            "directory_count": len(directories),
            "sample_directories": sample_dirs,
            "summary": summary,
        }

        return {
            "directory_analysis": directory_analysis,
            "sum_direct_files": sum_direct_files,
            "total_files": total_files,
            "recursive_gte_direct": recursive_gte_direct,
            "computed_ratios_valid": computed_ratios_valid,
            "percentiles_monotonic": percentiles_monotonic,
            "inequality_metrics_valid": inequality_metrics_valid,
            "classification_sum_matches": classification_sum_matches,
            "lang_loc_sum_matches": lang_loc_sum_matches,
            "cocomo_ordered": cocomo_ordered,
        }

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run directory analysis ground truth assertions."""
        failures = []
        output_dir = self.working_dir / "output"

        dir_file = find_directory_analysis_file(output_dir)
        if dir_file is None:
            failures.append("No directory analysis file found (checked directory_analysis_eval.json, runs/synthetic.json, directory_analysis.json)")
            return False, failures

        try:
            raw_data = json.loads(dir_file.read_text())
            # Handle nested 'results' wrapper structure
            if "results" in raw_data and "directories" not in raw_data:
                data = raw_data["results"]
            else:
                data = raw_data
        except json.JSONDecodeError as e:
            failures.append(f"Invalid JSON: {e}")
            return False, failures

        # Schema assertions
        if "directories" not in data:
            failures.append("Missing 'directories' array")
        if "summary" not in data:
            failures.append("Missing 'summary' object")

        directories = data.get("directories", [])
        summary = data.get("summary", {})
        total_files = summary.get("total_files", 0)

        # Check each directory has required fields
        for i, d in enumerate(directories):
            if "path" not in d:
                failures.append(f"Directory {i}: missing 'path'")
            if "direct" not in d:
                failures.append(f"Directory {i}: missing 'direct'")
            if "recursive" not in d:
                failures.append(f"Directory {i}: missing 'recursive'")

        # Aggregation assertions
        sum_direct = sum(d.get("direct", {}).get("file_count", 0) for d in directories)
        if sum_direct != total_files:
            failures.append(f"Sum of direct file counts ({sum_direct}) != total_files ({total_files})")

        # Recursive >= direct for all
        for d in directories:
            direct_count = d.get("direct", {}).get("file_count", 0)
            recursive_count = d.get("recursive", {}).get("file_count", 0)
            if recursive_count < direct_count:
                failures.append(f"Directory '{d.get('path')}': recursive ({recursive_count}) < direct ({direct_count})")

        # Statistical assertions - percentile monotonicity
        for d in directories:
            loc_dist = d.get("recursive", {}).get("loc_distribution")
            if loc_dist and loc_dist.get("p25") is not None:
                p25 = loc_dist.get("p25", 0)
                median = loc_dist.get("median", 0)
                p75 = loc_dist.get("p75", 0)
                p90 = loc_dist.get("p90", 0)
                p95 = loc_dist.get("p95", 0)
                if not (p25 <= median <= p75 <= p90 <= p95):
                    failures.append(
                        f"Directory '{d.get('path')}': non-monotonic percentiles "
                        f"(p25={p25}, median={median}, p75={p75}, p90={p90}, p95={p95})"
                    )

        return len(failures) == 0, failures

    def evaluate(self) -> JudgeResult:
        """Run the evaluation pipeline.

        Delegates to base class implementation which:
        1. Collects evidence via collect_evidence()
        2. Builds prompt from template
        3. Invokes Claude for evaluation
        4. Parses response into JudgeResult
        """
        return super().evaluate()
