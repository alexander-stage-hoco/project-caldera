"""Statistics Quality Judge - evaluates distribution stats and hotspot detection."""

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


class StatisticsJudge(BaseJudge):
    """Evaluates distribution statistics and hotspot detection quality.

    Distribution fields: min, max, mean, median, stddev, p25, p75, p90, p95, skewness, kurtosis
    """

    @property
    def dimension_name(self) -> str:
        return "statistics"

    @property
    def weight(self) -> float:
        return 0.14  # 14%

    def get_default_prompt(self) -> str:
        return """# Statistics Quality Judge

Evaluate distribution statistics quality. Score 1-5:
- 5: Full distribution stats (13 fields including CV/IQR)
- 4: Most fields present, accurate statistics
- 3: Basic stats present
- 2: Incomplete stats
- 1: No meaningful distribution analysis

Sub-dimensions:
- Completeness (35%)
- Accuracy (35%)
- Interpretability (30%)

Respond with JSON including sub_scores.
"""

    def collect_evidence(self) -> dict[str, Any]:
        """Collect statistics evidence."""
        output_dir = self._resolve_output_dir()

        # Load directory analysis for distribution stats
        distribution_sample = {}
        hotspot_scores = []
        dir_file = find_directory_analysis_file(output_dir)
        if dir_file is not None:
            raw_data = json.loads(dir_file.read_text())
            # Handle nested 'results' wrapper structure
            if "results" in raw_data and "directories" not in raw_data:
                data = raw_data["results"]
            else:
                data = raw_data
            directories = data.get("directories", [])

            # Find a directory with distribution for sample
            for d in directories:
                loc_dist = d.get("recursive", {}).get("loc_distribution")
                if loc_dist:
                    distribution_sample = {
                        "path": d.get("path"),
                        "loc_distribution": loc_dist,
                        "complexity_distribution": d.get("recursive", {}).get("complexity_distribution"),
                    }
                    break

            # Collect hotspot scores (matching prompt placeholder)
            hotspot_scores = [
                {
                    "path": d.get("path"),
                    "hotspot_score": d.get("hotspot_score", 0),
                    "complexity_total": d.get("recursive", {}).get("complexity_total", 0),
                    "file_count": d.get("recursive", {}).get("file_count", 0),
                }
                for d in directories[:10]  # First 10 for review
            ]

        # Validation checks
        percentiles_valid = True
        means_valid = True
        stddevs_valid = True
        hotspots_valid = True

        if dir_file is not None:
            raw_data = json.loads(dir_file.read_text())
            # Handle nested 'results' wrapper structure
            if "results" in raw_data and "directories" not in raw_data:
                data = raw_data["results"]
            else:
                data = raw_data
            for d in data.get("directories", []):
                # Check hotspot scores are in [0, 1] range
                hotspot_score = d.get("hotspot_score", 0)
                if hotspot_score < 0 or hotspot_score > 1:
                    hotspots_valid = False

                # Check distribution validity
                for dist_name in ["loc_distribution", "complexity_distribution"]:
                    stats = d.get("recursive", {}).get(dist_name)
                    if stats:
                        # Percentile monotonicity
                        p25 = stats.get("p25", 0)
                        median = stats.get("median", 0)
                        p75 = stats.get("p75", 0)
                        p90 = stats.get("p90", 0)
                        p95 = stats.get("p95", 0)
                        if not (p25 <= median <= p75 <= p90 <= p95):
                            percentiles_valid = False

                        # Mean in range
                        mean = stats.get("mean", 0)
                        min_val = stats.get("min", 0)
                        max_val = stats.get("max", float("inf"))
                        if not (min_val <= mean <= max_val):
                            means_valid = False

                        # Stddev non-negative
                        stddev = stats.get("stddev", 0)
                        if stddev < 0:
                            stddevs_valid = False

        return {
            "distribution_sample": distribution_sample,
            "hotspot_scores": hotspot_scores,
            "percentiles_valid": percentiles_valid,
            "means_valid": means_valid,
            "stddevs_valid": stddevs_valid,
            "hotspots_valid": hotspots_valid,
        }

    def run_ground_truth_assertions(self) -> tuple[bool, list[str]]:
        """Run statistics ground truth assertions."""
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

        directories = data.get("directories", [])

        # Required distribution fields (now includes cv and iqr)
        required_fields = ["min", "max", "mean", "median", "stddev", "p25", "p75", "p90", "p95"]

        # Check at least one directory has complete distribution
        has_complete_dist = False
        for d in directories:
            loc_dist = d.get("recursive", {}).get("loc_distribution")
            if loc_dist:
                present = [f for f in required_fields if f in loc_dist]
                if len(present) >= 9:
                    has_complete_dist = True
                    break

        if not has_complete_dist:
            failures.append("No directory has complete distribution statistics")

        # Validate statistical properties
        for d in directories:
            for dist_name in ["loc_distribution", "complexity_distribution"]:
                stats = d.get("recursive", {}).get(dist_name)
                if not stats:
                    continue

                # Percentile monotonicity
                p25 = stats.get("p25", 0)
                median = stats.get("median", 0)
                p75 = stats.get("p75", 0)
                p90 = stats.get("p90", 0)
                p95 = stats.get("p95", 0)

                if not (p25 <= median <= p75 <= p90 <= p95):
                    failures.append(
                        f"Non-monotonic percentiles for {dist_name} in '{d.get('path')}': "
                        f"p25={p25}, median={median}, p75={p75}, p90={p90}, p95={p95}"
                    )

                # Mean in range
                mean = stats.get("mean", 0)
                min_val = stats.get("min", 0)
                max_val = stats.get("max", float("inf"))
                if mean < min_val or mean > max_val:
                    failures.append(
                        f"Mean out of range for {dist_name} in '{d.get('path')}': "
                        f"mean={mean}, min={min_val}, max={max_val}"
                    )

                # Stddev non-negative
                stddev = stats.get("stddev", 0)
                if stddev < 0:
                    failures.append(f"Negative stddev for {dist_name} in '{d.get('path')}': {stddev}")

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
