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
        priority=3,  # After executive summary, before tool-specific sections
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """Fetch delta summary and top file regressions."""
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
        return "delta_summary.html.j2"
