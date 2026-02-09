"""Base parser interface for coverage report parsing."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class FileCoverage:
    """Normalized coverage data for a single file.

    All coverage formats are normalized to this structure.
    """

    relative_path: str
    """Repo-relative file path (POSIX format, no leading /)."""

    line_coverage_pct: float | None
    """Line coverage percentage (0-100), or None if not available."""

    branch_coverage_pct: float | None
    """Branch coverage percentage (0-100), or None if not available."""

    lines_total: int
    """Total number of lines (coverable lines, not all lines)."""

    lines_covered: int
    """Number of lines covered by tests."""

    lines_missed: int
    """Number of lines not covered by tests."""

    branches_total: int | None
    """Total number of branches, or None if not tracked."""

    branches_covered: int | None
    """Number of branches covered, or None if not tracked."""

    uncovered_lines: list[int] | None = None
    """List of uncovered line numbers (1-indexed), or None if not tracked."""

    def __post_init__(self) -> None:
        """Validate coverage data invariants."""
        if self.lines_covered > self.lines_total:
            raise ValueError(
                f"lines_covered ({self.lines_covered}) > lines_total ({self.lines_total})"
            )
        if self.lines_missed != self.lines_total - self.lines_covered:
            raise ValueError(
                f"lines_missed ({self.lines_missed}) != lines_total - lines_covered "
                f"({self.lines_total - self.lines_covered})"
            )
        if self.branches_total is not None and self.branches_covered is not None:
            if self.branches_covered > self.branches_total:
                raise ValueError(
                    f"branches_covered ({self.branches_covered}) > "
                    f"branches_total ({self.branches_total})"
                )
        if self.line_coverage_pct is not None:
            if self.line_coverage_pct < 0 or self.line_coverage_pct > 100:
                raise ValueError(
                    f"line_coverage_pct ({self.line_coverage_pct}) must be 0-100"
                )
        if self.branch_coverage_pct is not None:
            if self.branch_coverage_pct < 0 or self.branch_coverage_pct > 100:
                raise ValueError(
                    f"branch_coverage_pct ({self.branch_coverage_pct}) must be 0-100"
                )
        if self.uncovered_lines is not None:
            # uncovered_lines count can be <= lines_missed because:
            # - Some formats count statements/instructions, not lines
            # - Multiple statements can exist on a single line
            # - We deduplicate line numbers in the output
            if len(self.uncovered_lines) > self.lines_missed:
                raise ValueError(
                    f"uncovered_lines length ({len(self.uncovered_lines)}) > "
                    f"lines_missed ({self.lines_missed})"
                )
            if any(ln < 1 for ln in self.uncovered_lines):
                raise ValueError("uncovered_lines must be 1-indexed (all values >= 1)")


def compute_coverage_pct(covered: int, total: int) -> float | None:
    """Compute coverage percentage, handling division by zero.

    Args:
        covered: Number of covered items
        total: Total number of items

    Returns:
        Coverage percentage (0-100), or None if total is 0
    """
    if total == 0:
        return None
    return round((covered / total) * 100, 2)


class BaseCoverageParser(ABC):
    """Abstract base class for coverage report parsers.

    Implementations should:
    1. Implement detect() to identify if content matches their format
    2. Implement parse() to extract FileCoverage records
    """

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return the format name (e.g., 'lcov', 'cobertura')."""
        ...

    @abstractmethod
    def detect(self, content: str | bytes) -> bool:
        """Check if the content matches this parser's format.

        Args:
            content: File content (text or bytes)

        Returns:
            True if this parser can handle the content
        """
        ...

    @abstractmethod
    def parse(self, content: str | bytes) -> list[FileCoverage]:
        """Parse coverage data from the content.

        Args:
            content: File content (text or bytes)

        Returns:
            List of FileCoverage records, one per file in the report

        Raises:
            ValueError: If the content is malformed
        """
        ...
