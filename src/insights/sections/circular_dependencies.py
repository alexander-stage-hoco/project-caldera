"""
Circular dependencies section - File-level import cycle detection.

Uses mart_circular_dependencies to surface import cycles (A->B->C->A)
that indicate tight coupling preventing clean module extraction.
This is distinct from dependency_health which covers project/package-level
cycles (e.g. NuGet references via dependensee).
"""

from typing import Any

from .base import BaseSection, SectionConfig
from ..data_fetcher import DataFetcher


class CircularDependenciesSection(BaseSection):
    """File-level circular dependency analysis using symbol-scanner data."""

    config = SectionConfig(
        name="circular_dependencies",
        title="Circular Dependencies",
        description="File-level import cycle detection identifying tightly coupled modules that resist clean extraction.",
        priority=6.9,
    )

    def fetch_data(self, fetcher: DataFetcher, run_pk: int) -> dict[str, Any]:
        """
        Fetch circular dependency data.

        Returns data including:
        - cycles: All detected import cycles ordered by severity
        - severity_counts: Count by severity level
        - multi_cycle_files: Files appearing in multiple cycles
        - summary: Total cycles, files involved, avg cycle length
        """
        try:
            cycles = fetcher.fetch("circular_dependencies", run_pk)
        except Exception:
            cycles = []

        # Count by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        files_in_cycles: dict[str, int] = {}
        cycle_lengths = []

        for c in cycles:
            severity = c.get("severity", "low")
            if severity in severity_counts:
                severity_counts[severity] += 1

            length = c.get("cycle_length", 0)
            if length:
                cycle_lengths.append(length)

            # Track files that appear in cycles
            start_file = c.get("start_file", "")
            if start_file:
                files_in_cycles[start_file] = files_in_cycles.get(start_file, 0) + 1

        # Files appearing in multiple cycles
        multi_cycle_files = sorted(
            [(f, count) for f, count in files_in_cycles.items() if count > 1],
            key=lambda x: x[1],
            reverse=True,
        )

        avg_cycle_length = round(sum(cycle_lengths) / len(cycle_lengths), 1) if cycle_lengths else 0

        summary = {
            "total_cycles": len(cycles),
            "critical_count": severity_counts["critical"],
            "high_count": severity_counts["high"],
            "medium_count": severity_counts["medium"],
            "low_count": severity_counts["low"],
            "files_involved": len(files_in_cycles),
            "avg_cycle_length": avg_cycle_length,
            "multi_cycle_file_count": len(multi_cycle_files),
        }

        return {
            "cycles": cycles,
            "severity_counts": severity_counts,
            "multi_cycle_files": multi_cycle_files,
            "summary": summary,
            "has_data": len(cycles) > 0,
            "has_critical_cycles": severity_counts["critical"] > 0,
            "has_multi_cycle_files": len(multi_cycle_files) > 0,
        }

    def get_template_name(self) -> str:
        """Return the HTML template file name."""
        return "circular_dependencies.html.j2"

    def validate_data(self, data: dict[str, Any]) -> list[str]:
        """Validate the fetched data."""
        errors = []
        if not data.get("has_data"):
            errors.append("No circular dependency data available - symbol-scanner tool may not have run or no cycles detected")
        return errors

    def get_fallback_data(self) -> dict[str, Any]:
        """Return fallback data when the section cannot be rendered."""
        return {
            "cycles": [],
            "severity_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "multi_cycle_files": [],
            "summary": {
                "total_cycles": 0,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "files_involved": 0,
                "avg_cycle_length": 0,
                "multi_cycle_file_count": 0,
            },
            "has_data": False,
            "has_critical_cycles": False,
            "has_multi_cycle_files": False,
        }
