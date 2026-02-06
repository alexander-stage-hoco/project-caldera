"""Authorship Accuracy checks (AA-1 to AA-8) for git-fame.

These checks verify the accuracy of authorship attribution:
- AA-1: Total LOC matches expected
- AA-2: Author count matches expected
- AA-3: Top author LOC within 90% of expected
- AA-4: Ownership percentages within 5% of expected per author
- AA-5: Bus factor matches expected
- AA-6: HHI index within 0.1 of expected
- AA-7: Top two percentage within 5% of expected
- AA-8: All files have author attribution
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .utils import check_result, find_repo_analyses, load_ground_truth


class AuthorshipAccuracyChecks:
    """Authorship accuracy evaluation checks for git-fame."""

    def __init__(self, output_dir: Path, ground_truth_file: Path) -> None:
        """Initialize authorship accuracy checks.

        Args:
            output_dir: Path to the output directory containing analysis results
            ground_truth_file: Path to the ground truth JSON file
        """
        self.output_dir = output_dir
        self.ground_truth_file = ground_truth_file
        self.analyses = find_repo_analyses(output_dir)
        self.ground_truth = load_ground_truth(ground_truth_file)

    def run_all(self) -> list[dict[str, Any]]:
        """Run all authorship accuracy checks.

        Returns:
            List of check results with check, passed, and message keys
        """
        return [
            self._check_total_loc(),
            self._check_author_count(),
            self._check_top_author_loc(),
            self._check_ownership_percentages(),
            self._check_bus_factor(),
            self._check_hhi_index(),
            self._check_top_two_percentage(),
            self._check_file_attribution(),
        ]

    def _get_data_section(self, data: dict[str, Any]) -> dict[str, Any]:
        """Get the data section, supporting both envelope and legacy formats."""
        # New Caldera envelope format
        if "data" in data:
            return data.get("data", {})
        # Legacy format - results is the data section
        return data.get("results", {})

    def _get_analysis_summary(self, repo_name: str) -> dict[str, Any]:
        """Get summary data for a repository."""
        analysis = self.analyses.get(repo_name, {})
        data_section = self._get_data_section(analysis)
        return data_section.get("summary", {})

    def _get_expected(self, repo_name: str) -> dict[str, Any]:
        """Get expected values from ground truth for a repository.

        Handles both flat structure (repo_name -> expected values)
        and nested structure (repo_name -> {expected: values, description: ...}).
        """
        repo_data = self.ground_truth.get(repo_name, {})
        # Handle nested structure with "expected" key
        if isinstance(repo_data, dict) and "expected" in repo_data:
            return repo_data["expected"]
        return repo_data

    def _check_total_loc(self) -> dict[str, Any]:
        """AA-1: Verify total LOC matches expected."""
        if not self.analyses:
            return check_result(
                "AA-1",
                False,
                "No analysis data found",
            )

        if not self.ground_truth:
            return check_result(
                "AA-1",
                True,
                "No ground truth available (skipped)",
            )

        mismatches = []
        checked = 0
        for repo_name in self.ground_truth:
            if repo_name.startswith("_"):
                continue

            expected = self._get_expected(repo_name)
            expected_loc = expected.get("expected_total_loc") or expected.get("total_loc")
            if expected_loc is None:
                continue

            checked += 1
            summary = self._get_analysis_summary(repo_name)
            actual_loc = summary.get("total_loc", 0)

            if actual_loc != expected_loc:
                mismatches.append(f"{repo_name}: expected {expected_loc}, got {actual_loc}")

        if not checked:
            return check_result(
                "AA-1",
                True,
                "No expected_total_loc in ground truth (skipped)",
            )

        if mismatches:
            return check_result(
                "AA-1",
                False,
                f"LOC mismatches: {', '.join(mismatches[:3])}",
            )

        return check_result(
            "AA-1",
            True,
            f"Total LOC matches for {checked} repositories",
        )

    def _check_author_count(self) -> dict[str, Any]:
        """AA-2: Verify author count matches expected."""
        if not self.analyses:
            return check_result(
                "AA-2",
                False,
                "No analysis data found",
            )

        if not self.ground_truth:
            return check_result(
                "AA-2",
                True,
                "No ground truth available (skipped)",
            )

        mismatches = []
        checked = 0
        for repo_name, expected in self.ground_truth.items():
            if repo_name.startswith("_"):
                continue

            expected_count = expected.get("expected_author_count")
            if expected_count is None:
                continue

            checked += 1
            summary = self._get_analysis_summary(repo_name)
            actual_count = summary.get("author_count", 0)

            if actual_count != expected_count:
                mismatches.append(f"{repo_name}: expected {expected_count}, got {actual_count}")

        if not checked:
            return check_result(
                "AA-2",
                True,
                "No expected_author_count in ground truth (skipped)",
            )

        if mismatches:
            return check_result(
                "AA-2",
                False,
                f"Author count mismatches: {', '.join(mismatches[:3])}",
            )

        return check_result(
            "AA-2",
            True,
            f"Author count matches for {checked} repositories",
        )

    def _check_top_author_loc(self) -> dict[str, Any]:
        """AA-3: Verify top author LOC is within 90% of expected."""
        if not self.analyses:
            return check_result(
                "AA-3",
                False,
                "No analysis data found",
            )

        if not self.ground_truth:
            return check_result(
                "AA-3",
                True,
                "No ground truth available (skipped)",
            )

        failures = []
        checked = 0
        for repo_name, expected in self.ground_truth.items():
            if repo_name.startswith("_"):
                continue

            expected_loc = expected.get("expected_top_author_loc")
            if expected_loc is None:
                continue

            checked += 1
            analysis = self.analyses.get(repo_name, {})
            data_section = self._get_data_section(analysis)
            authors = data_section.get("authors", [])

            if not authors:
                failures.append(f"{repo_name}: no authors found")
                continue

            actual_loc = authors[0].get("surviving_loc", 0)
            threshold = expected_loc * 0.9

            if actual_loc < threshold:
                failures.append(
                    f"{repo_name}: expected >= {threshold:.0f}, got {actual_loc}"
                )

        if not checked:
            return check_result(
                "AA-3",
                True,
                "No expected_top_author_loc in ground truth (skipped)",
            )

        if failures:
            return check_result(
                "AA-3",
                False,
                f"Top author LOC failures: {', '.join(failures[:3])}",
            )

        return check_result(
            "AA-3",
            True,
            f"Top author LOC within 90% for {checked} repositories",
        )

    def _check_ownership_percentages(self) -> dict[str, Any]:
        """AA-4: Verify ownership percentages within 5% of expected per author."""
        if not self.analyses:
            return check_result(
                "AA-4",
                False,
                "No analysis data found",
            )

        if not self.ground_truth:
            return check_result(
                "AA-4",
                True,
                "No ground truth available (skipped)",
            )

        failures = []
        checked = 0
        tolerance = 5.0  # 5% tolerance

        for repo_name, expected in self.ground_truth.items():
            if repo_name.startswith("_"):
                continue

            expected_authors = expected.get("expected_authors", {})
            if not expected_authors:
                continue

            checked += 1
            analysis = self.analyses.get(repo_name, {})
            data_section = self._get_data_section(analysis)
            authors = data_section.get("authors", [])

            # Build lookup by author name
            actual_by_name = {a["name"]: a for a in authors}

            for author_name, expected_pct in expected_authors.items():
                actual_author = actual_by_name.get(author_name)
                if not actual_author:
                    failures.append(f"{repo_name}/{author_name}: not found")
                    continue

                actual_pct = actual_author.get("ownership_pct", 0)
                if abs(actual_pct - expected_pct) > tolerance:
                    failures.append(
                        f"{repo_name}/{author_name}: expected {expected_pct}%, got {actual_pct}%"
                    )

        if not checked:
            return check_result(
                "AA-4",
                True,
                "No expected_authors in ground truth (skipped)",
            )

        if failures:
            return check_result(
                "AA-4",
                False,
                f"Ownership mismatches: {', '.join(failures[:3])}",
            )

        return check_result(
            "AA-4",
            True,
            f"Ownership percentages within {tolerance}% for {checked} repositories",
        )

    def _check_bus_factor(self) -> dict[str, Any]:
        """AA-5: Verify bus factor matches expected."""
        if not self.analyses:
            return check_result(
                "AA-5",
                False,
                "No analysis data found",
            )

        if not self.ground_truth:
            return check_result(
                "AA-5",
                True,
                "No ground truth available (skipped)",
            )

        mismatches = []
        checked = 0
        for repo_name, expected in self.ground_truth.items():
            if repo_name.startswith("_"):
                continue

            expected_bf = expected.get("expected_bus_factor")
            if expected_bf is None:
                continue

            checked += 1
            summary = self._get_analysis_summary(repo_name)
            actual_bf = summary.get("bus_factor", 0)

            if actual_bf != expected_bf:
                mismatches.append(f"{repo_name}: expected {expected_bf}, got {actual_bf}")

        if not checked:
            return check_result(
                "AA-5",
                True,
                "No expected_bus_factor in ground truth (skipped)",
            )

        if mismatches:
            return check_result(
                "AA-5",
                False,
                f"Bus factor mismatches: {', '.join(mismatches[:3])}",
            )

        return check_result(
            "AA-5",
            True,
            f"Bus factor matches for {checked} repositories",
        )

    def _check_hhi_index(self) -> dict[str, Any]:
        """AA-6: Verify HHI index within 0.1 of expected."""
        if not self.analyses:
            return check_result(
                "AA-6",
                False,
                "No analysis data found",
            )

        if not self.ground_truth:
            return check_result(
                "AA-6",
                True,
                "No ground truth available (skipped)",
            )

        failures = []
        checked = 0
        tolerance = 0.1

        for repo_name, expected in self.ground_truth.items():
            if repo_name.startswith("_"):
                continue

            expected_hhi = expected.get("expected_hhi")
            if expected_hhi is None:
                continue

            checked += 1
            summary = self._get_analysis_summary(repo_name)
            actual_hhi = summary.get("hhi_index", 0)

            if abs(actual_hhi - expected_hhi) > tolerance:
                failures.append(
                    f"{repo_name}: expected {expected_hhi:.2f}, got {actual_hhi:.2f}"
                )

        if not checked:
            return check_result(
                "AA-6",
                True,
                "No expected_hhi in ground truth (skipped)",
            )

        if failures:
            return check_result(
                "AA-6",
                False,
                f"HHI mismatches: {', '.join(failures[:3])}",
            )

        return check_result(
            "AA-6",
            True,
            f"HHI index within {tolerance} for {checked} repositories",
        )

    def _check_top_two_percentage(self) -> dict[str, Any]:
        """AA-7: Verify top two percentage within 5% of expected."""
        if not self.analyses:
            return check_result(
                "AA-7",
                False,
                "No analysis data found",
            )

        if not self.ground_truth:
            return check_result(
                "AA-7",
                True,
                "No ground truth available (skipped)",
            )

        failures = []
        checked = 0
        tolerance = 5.0

        for repo_name, expected in self.ground_truth.items():
            if repo_name.startswith("_"):
                continue

            expected_pct = expected.get("expected_top_two_pct")
            if expected_pct is None:
                continue

            checked += 1
            summary = self._get_analysis_summary(repo_name)
            actual_pct = summary.get("top_two_pct", 0)

            if abs(actual_pct - expected_pct) > tolerance:
                failures.append(
                    f"{repo_name}: expected {expected_pct}%, got {actual_pct}%"
                )

        if not checked:
            return check_result(
                "AA-7",
                True,
                "No expected_top_two_pct in ground truth (skipped)",
            )

        if failures:
            return check_result(
                "AA-7",
                False,
                f"Top two % mismatches: {', '.join(failures[:3])}",
            )

        return check_result(
            "AA-7",
            True,
            f"Top two % within {tolerance}% for {checked} repositories",
        )

    def _check_file_attribution(self) -> dict[str, Any]:
        """AA-8: Verify all files have author attribution."""
        if not self.analyses:
            return check_result(
                "AA-8",
                False,
                "No analysis data found",
            )

        missing_attribution = []
        total_files = 0
        has_files = False

        for repo_name, data in self.analyses.items():
            data_section = self._get_data_section(data)
            files = data_section.get("files", [])

            if files:
                has_files = True
                total_files += len(files)

                for i, file_entry in enumerate(files):
                    author = file_entry.get("author")
                    if not author:
                        missing_attribution.append(
                            f"{repo_name}.files[{i}]: {file_entry.get('path', 'unknown')}"
                        )

        if not has_files:
            # git-fame typically provides author-level, not file-level data
            # Check if authors exist instead
            for repo_name, data in self.analyses.items():
                data_section = self._get_data_section(data)
                authors = data_section.get("authors", [])
                if authors:
                    return check_result(
                        "AA-8",
                        True,
                        f"Author-level attribution present ({len(authors)} authors)",
                    )

            return check_result(
                "AA-8",
                False,
                "No author or file attribution data found",
            )

        if missing_attribution:
            return check_result(
                "AA-8",
                False,
                f"Missing attribution: {', '.join(missing_attribution[:3])}",
            )

        return check_result(
            "AA-8",
            True,
            f"All {total_files} files have author attribution",
        )
