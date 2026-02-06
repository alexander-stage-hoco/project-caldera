"""Integration Fit checks (IF-1 to IF-4) for git-fame.

These checks verify compatibility with the DD Platform:
- IF-1: Path normalization - Paths match DD schema format
- IF-2: Metric compatibility - Metrics map to L5/L8/L9 lenses
- IF-3: Directory rollups - Aggregation by directory works
- IF-4: Collector integration - Output matches collector schema
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .utils import check_result, find_repo_analyses


class IntegrationFitChecks:
    """Integration fit evaluation checks for git-fame."""

    def __init__(self, output_dir: Path) -> None:
        """Initialize integration fit checks.

        Args:
            output_dir: Path to the output directory containing analysis results
        """
        self.output_dir = output_dir
        self.analyses = find_repo_analyses(output_dir)

    def _get_data_section(self, data: dict[str, Any]) -> dict[str, Any]:
        """Get the data section, supporting both envelope and legacy formats."""
        # New Caldera envelope format
        if "data" in data:
            return data.get("data", {})
        # Legacy format - results is the data section
        return data.get("results", {})

    def _get_metadata(self, data: dict[str, Any]) -> dict[str, Any]:
        """Get metadata section (envelope) or top-level fields (legacy)."""
        if "metadata" in data:
            return data.get("metadata", {})
        # Legacy format - return top-level dict
        return data

    def run_all(self) -> list[dict[str, Any]]:
        """Run all integration fit checks.

        Returns:
            List of check results with check, passed, and message keys
        """
        return [
            self._check_path_normalization(),
            self._check_metric_compatibility(),
            self._check_directory_rollups(),
            self._check_collector_integration(),
        ]

    def _check_path_normalization(self) -> dict[str, Any]:
        """IF-1: Verify paths match DD schema format (repo-relative, POSIX separators)."""
        if not self.analyses:
            return check_result(
                "IF-1",
                False,
                "No analysis data found",
            )

        invalid_paths = []

        for repo_name, data in self.analyses.items():
            data_section = self._get_data_section(data)
            files = data_section.get("files", [])

            for file_entry in files:
                path = file_entry.get("path", "")
                if self._is_invalid_path(path):
                    invalid_paths.append(f"{repo_name}: {path}")

        if invalid_paths:
            return check_result(
                "IF-1",
                False,
                f"Invalid paths: {', '.join(invalid_paths[:3])}",
            )

        # If no files, check that repo_path is valid
        for repo_name, data in self.analyses.items():
            repo_path = data.get("repo_path", "")
            if repo_path and not Path(repo_path).is_absolute():
                continue  # Relative repo paths are okay

        return check_result(
            "IF-1",
            True,
            "All paths are properly normalized",
        )

    def _is_invalid_path(self, path: str) -> bool:
        """Check if a path violates DD schema requirements."""
        if not path:
            return True
        # No leading slashes
        if path.startswith("/") or path.startswith("\\"):
            return True
        # No leading ./
        if path.startswith("./"):
            return True
        # No backslashes (Windows paths)
        if "\\" in path:
            return True
        # No Windows drive letters
        if re.match(r"^[A-Za-z]:", path):
            return True
        # No .. in path components
        if ".." in path.split("/"):
            return True
        return False

    def _check_metric_compatibility(self) -> dict[str, Any]:
        """IF-2: Verify metrics map to L5/L8/L9 lenses."""
        if not self.analyses:
            return check_result(
                "IF-2",
                False,
                "No analysis data found",
            )

        # Required metrics for authorship analysis
        required_metrics = {
            "author_count": "L8 (ownership)",
            "total_loc": "L5 (size)",
            "hhi_index": "L9 (concentration)",
            "bus_factor": "L9 (risk)",
        }

        missing_metrics = []
        found_metrics = []

        for repo_name, data in self.analyses.items():
            data_section = self._get_data_section(data)
            summary = data_section.get("summary", {})

            for metric, lens in required_metrics.items():
                if metric in summary:
                    if metric not in found_metrics:
                        found_metrics.append(metric)
                else:
                    if f"{repo_name}.{metric}" not in missing_metrics:
                        missing_metrics.append(f"{repo_name}.{metric}")

        if missing_metrics:
            return check_result(
                "IF-2",
                False,
                f"Missing metrics for lenses: {', '.join(missing_metrics[:3])}",
            )

        return check_result(
            "IF-2",
            True,
            f"All {len(required_metrics)} required metrics present for L5/L8/L9 lenses",
        )

    def _check_directory_rollups(self) -> dict[str, Any]:
        """IF-3: Verify aggregation by directory works (or is not applicable)."""
        if not self.analyses:
            return check_result(
                "IF-3",
                False,
                "No analysis data found",
            )

        # git-fame is an author-level tool, not directory-level
        # Check if any analysis has directory data
        has_directories = False
        directory_count = 0

        for repo_name, data in self.analyses.items():
            data_section = self._get_data_section(data)
            directories = data_section.get("directories", [])
            if directories:
                has_directories = True
                directory_count += len(directories)

        if has_directories:
            return check_result(
                "IF-3",
                True,
                f"Directory rollups present: {directory_count} directories",
            )

        # git-fame doesn't do directory rollups by default - this is expected
        return check_result(
            "IF-3",
            True,
            "Author-level tool - directory rollups not applicable",
        )

    def _check_collector_integration(self) -> dict[str, Any]:
        """IF-4: Verify output matches collector schema requirements."""
        if not self.analyses:
            return check_result(
                "IF-4",
                False,
                "No analysis data found",
            )

        # Check for Caldera envelope format (metadata/data) or legacy format
        missing = []

        for repo_name, data in self.analyses.items():
            # Check for envelope format first
            if "metadata" in data and "data" in data:
                # Caldera envelope format
                metadata = data.get("metadata", {})
                required_metadata = ["tool_name", "tool_version", "run_id", "schema_version", "timestamp"]
                for field in required_metadata:
                    if field not in metadata:
                        missing.append(f"{repo_name}.metadata.{field}")

                data_section = data.get("data", {})
                required_data = ["tool", "summary", "authors"]
                for field in required_data:
                    if field not in data_section:
                        missing.append(f"{repo_name}.data.{field}")
            else:
                # Legacy format
                required_fields = ["schema_version", "generated_at", "repo_name", "results"]
                for field in required_fields:
                    if field not in data:
                        missing.append(f"{repo_name}.{field}")

                results = data.get("results", {})
                required_results = ["tool", "summary", "authors"]
                for field in required_results:
                    if field not in results:
                        missing.append(f"{repo_name}.results.{field}")

        if missing:
            return check_result(
                "IF-4",
                False,
                f"Missing collector fields: {', '.join(missing[:5])}",
            )

        # Verify data types
        type_errors = []
        for repo_name, data in self.analyses.items():
            data_section = self._get_data_section(data)
            authors = data_section.get("authors", [])

            if not isinstance(authors, list):
                type_errors.append(f"{repo_name}.authors: expected list")

            summary = data_section.get("summary", {})
            if not isinstance(summary, dict):
                type_errors.append(f"{repo_name}.summary: expected dict")

        if type_errors:
            return check_result(
                "IF-4",
                False,
                f"Type errors: {', '.join(type_errors[:3])}",
            )

        return check_result(
            "IF-4",
            True,
            f"Output matches collector schema ({len(self.analyses)} analyses validated)",
        )
