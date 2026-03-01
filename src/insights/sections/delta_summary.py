"""
Delta summary section — run-over-run regression detection.

Shows key metric deltas between the current run and the most recent
previous run for the same repository.
"""

from __future__ import annotations

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class DeltaSummarySection(BaseSection):
    """Run-over-run delta summary with regression flags."""

    config = SectionConfig(
        name="delta_summary",
        title="Run-over-Run Delta Summary",
        description="Key metric changes compared to the previous analysis run.",
        priority=1,  # "What changed" — lead actionable section after executive summary
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Assemble a run-over-run delta summary and the top file regressions for the specified run.
        
        Fetches delta summary and top file regressions via the provided DataFetcher, determines whether a previous run exists, extracts the latest summary row (or an empty dict), derives regression type flags (complexity, coverage, secrets, vulnerabilities), and returns the assembled payload.
        
        Parameters:
            fetcher (DataFetcher): Data retrieval helper used to fetch summary and regression data.
            run_pk (int): Primary key of the run to analyze.
        
        Returns:
            dict: A payload containing:
                - "has_previous_run" (bool): True if delta data for a previous run exists.
                - "summary" (dict): The latest delta summary row or an empty dict if none.
                - "regression_flags" (list[str]): Detected regression types among "complexity", "coverage", "secrets", "vulnerabilities".
                - "regression_count" (int): Number of detected regression types.
                - "top_regressions" (list[dict]): Up to the first 10 regression entries.
                - "total_regressed_files" (int): Total number of regression entries retrieved.
        """
        delta = self._safe_fetch(fetcher, "delta_summary", run_pk)
        regressions = self._safe_fetch(fetcher, "file_regressions_top", run_pk)

        has_previous_run = bool(delta)
        summary_row = delta[0] if delta else {}

        # Count regressions by type
        regression_flags = []
        if summary_row.get("regression_complexity"):
            regression_flags.append("complexity")
        if summary_row.get("regression_coverage"):
            regression_flags.append("coverage")
        if summary_row.get("regression_secrets"):
            regression_flags.append("secrets")
        if summary_row.get("regression_trivy"):
            regression_flags.append("vulnerabilities")

        return {
            "has_previous_run": has_previous_run,
            "summary": summary_row,
            "regression_flags": regression_flags,
            "regression_count": len(regression_flags),
            "top_regressions": regressions[:10],
            "total_regressed_files": len(regressions),
        }

    def get_template_name(self) -> str:
        """
        Provide the template filename used to render the run-over-run delta summary section.
        
        Returns:
            str: The template filename 'delta_summary.html.j2'.
        """
        return "delta_summary.html.j2"
