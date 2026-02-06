"""Output Quality checks (OQ-1 to OQ-6) for git-fame.

These checks verify the structure and format of git-fame output:
- OQ-1: Schema version present
- OQ-2: Valid ISO8601 timestamp
- OQ-3: All required summary fields present
- OQ-4: All author records have required fields
- OQ-5: All file records have required fields (if present)
- OQ-6: Output parses as valid JSON
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .utils import check_result, find_repo_analyses


class OutputQualityChecks:
    """Output quality evaluation checks for git-fame."""

    def __init__(self, output_dir: Path) -> None:
        """Initialize output quality checks.

        Args:
            output_dir: Path to the output directory containing analysis results
        """
        self.output_dir = output_dir
        self.analyses = find_repo_analyses(output_dir)

    def run_all(self) -> list[dict[str, Any]]:
        """Run all output quality checks.

        Returns:
            List of check results with check, passed, and message keys
        """
        return [
            self._check_schema_version(),
            self._check_timestamp_valid(),
            self._check_summary_fields(),
            self._check_author_fields(),
            self._check_file_fields(),
            self._check_json_validity(),
        ]

    def _get_schema_version(self, data: dict[str, Any]) -> str | None:
        """Get schema_version from data, supporting both envelope and legacy formats."""
        # New Caldera envelope format
        metadata = data.get("metadata", {})
        if metadata.get("schema_version"):
            return metadata.get("schema_version")
        # Legacy format
        return data.get("schema_version")

    def _get_timestamp(self, data: dict[str, Any]) -> str | None:
        """Get timestamp from data, supporting both envelope and legacy formats."""
        # New Caldera envelope format
        metadata = data.get("metadata", {})
        if metadata.get("timestamp"):
            return metadata.get("timestamp")
        # Legacy format
        return data.get("generated_at")

    def _get_data_section(self, data: dict[str, Any]) -> dict[str, Any]:
        """Get the data section, supporting both envelope and legacy formats."""
        # New Caldera envelope format
        if "data" in data:
            return data.get("data", {})
        # Legacy format - results is the data section
        return data.get("results", {})

    def _check_schema_version(self) -> dict[str, Any]:
        """OQ-1: Verify schema_version is present."""
        if not self.analyses:
            return check_result(
                "OQ-1",
                False,
                "No analysis data found",
            )

        missing = []
        for repo_name, data in self.analyses.items():
            if not self._get_schema_version(data):
                missing.append(repo_name)

        if missing:
            return check_result(
                "OQ-1",
                False,
                f"Missing schema_version in: {', '.join(missing[:3])}",
            )

        return check_result(
            "OQ-1",
            True,
            f"schema_version present in all {len(self.analyses)} analyses",
        )

    def _check_timestamp_valid(self) -> dict[str, Any]:
        """OQ-2: Verify timestamp is a valid ISO8601 timestamp."""
        if not self.analyses:
            return check_result(
                "OQ-2",
                False,
                "No analysis data found",
            )

        # ISO8601 pattern (flexible to accept common formats)
        iso8601_pattern = re.compile(
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$"
        )

        invalid = []
        for repo_name, data in self.analyses.items():
            timestamp = self._get_timestamp(data) or ""
            if not timestamp or not iso8601_pattern.match(timestamp):
                invalid.append(f"{repo_name}: {timestamp[:30] if timestamp else 'missing'}")

        if invalid:
            return check_result(
                "OQ-2",
                False,
                f"Invalid timestamps: {', '.join(invalid[:3])}",
            )

        return check_result(
            "OQ-2",
            True,
            f"Valid ISO8601 timestamps in all {len(self.analyses)} analyses",
        )

    def _check_summary_fields(self) -> dict[str, Any]:
        """OQ-3: Verify all required summary fields are present."""
        required_fields = [
            "author_count",
            "total_loc",
            "hhi_index",
            "bus_factor",
            "top_author_pct",
        ]

        if not self.analyses:
            return check_result(
                "OQ-3",
                False,
                "No analysis data found",
            )

        missing = []
        for repo_name, data in self.analyses.items():
            data_section = self._get_data_section(data)
            summary = data_section.get("summary", {})

            for field in required_fields:
                if field not in summary:
                    missing.append(f"{repo_name}.{field}")

        if missing:
            return check_result(
                "OQ-3",
                False,
                f"Missing summary fields: {', '.join(missing[:5])}",
            )

        return check_result(
            "OQ-3",
            True,
            f"All {len(required_fields)} required summary fields present",
        )

    def _check_author_fields(self) -> dict[str, Any]:
        """OQ-4: Verify all author records have required fields."""
        required_fields = [
            "name",
            "surviving_loc",
            "ownership_pct",
        ]

        if not self.analyses:
            return check_result(
                "OQ-4",
                False,
                "No analysis data found",
            )

        missing = []
        total_authors = 0
        for repo_name, data in self.analyses.items():
            data_section = self._get_data_section(data)
            authors = data_section.get("authors", [])
            total_authors += len(authors)

            for i, author in enumerate(authors):
                for field in required_fields:
                    if field not in author:
                        missing.append(f"{repo_name}.authors[{i}].{field}")

        if missing:
            return check_result(
                "OQ-4",
                False,
                f"Missing author fields: {', '.join(missing[:5])}",
            )

        return check_result(
            "OQ-4",
            True,
            f"All required fields present for {total_authors} authors",
        )

    def _check_file_fields(self) -> dict[str, Any]:
        """OQ-5: Verify all file records have required fields (if present)."""
        required_fields = [
            "path",
            "author",
            "loc",
        ]

        if not self.analyses:
            return check_result(
                "OQ-5",
                False,
                "No analysis data found",
            )

        missing = []
        total_files = 0
        has_files = False

        for repo_name, data in self.analyses.items():
            data_section = self._get_data_section(data)
            files = data_section.get("files", [])

            if files:
                has_files = True
                total_files += len(files)

                for i, file_entry in enumerate(files):
                    for field in required_fields:
                        if field not in file_entry:
                            missing.append(f"{repo_name}.files[{i}].{field}")

        if not has_files:
            return check_result(
                "OQ-5",
                True,
                "No file-level data present (author-level analysis only)",
            )

        if missing:
            return check_result(
                "OQ-5",
                False,
                f"Missing file fields: {', '.join(missing[:5])}",
            )

        return check_result(
            "OQ-5",
            True,
            f"All required fields present for {total_files} files",
        )

    def _check_json_validity(self) -> dict[str, Any]:
        """OQ-6: Verify output files parse as valid JSON."""
        if not self.output_dir.exists():
            return check_result(
                "OQ-6",
                False,
                f"Output directory not found: {self.output_dir}",
            )

        json_files = list(self.output_dir.glob("**/*.json"))
        if not json_files:
            return check_result(
                "OQ-6",
                False,
                "No JSON files found in output directory",
            )

        invalid = []
        for json_file in json_files:
            try:
                with open(json_file) as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                invalid.append(f"{json_file.name}: {str(e)[:50]}")

        if invalid:
            return check_result(
                "OQ-6",
                False,
                f"Invalid JSON files: {', '.join(invalid[:3])}",
            )

        return check_result(
            "OQ-6",
            True,
            f"All {len(json_files)} JSON files are valid",
        )
