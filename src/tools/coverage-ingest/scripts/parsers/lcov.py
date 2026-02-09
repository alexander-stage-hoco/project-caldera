"""LCOV format parser for coverage reports.

LCOV is a line-oriented text format commonly used by:
- lcov (C/C++)
- coverage.py (Python)
- go test -coverprofile (Go, after conversion)

Format example:
    TN:test_name
    SF:/path/to/file.py
    FN:10,function_name
    FNDA:5,function_name
    FNF:1
    FNH:1
    DA:10,5
    DA:11,0
    LF:2
    LH:1
    BRF:4
    BRH:2
    end_of_record
"""
from __future__ import annotations

from .base import BaseCoverageParser, FileCoverage, compute_coverage_pct


class LcovParser(BaseCoverageParser):
    """Parser for LCOV format coverage reports."""

    @property
    def format_name(self) -> str:
        return "lcov"

    def detect(self, content: str | bytes) -> bool:
        """Detect LCOV format by looking for characteristic markers.

        LCOV files typically contain SF: (source file) and end_of_record markers.
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")

        # Look for LCOV-specific markers
        has_sf = "SF:" in content
        has_end = "end_of_record" in content
        has_lf_lh = "LF:" in content or "LH:" in content

        return has_sf and (has_end or has_lf_lh)

    def parse(self, content: str | bytes) -> list[FileCoverage]:
        """Parse LCOV format coverage data.

        Args:
            content: LCOV format file content

        Returns:
            List of FileCoverage records

        Raises:
            ValueError: If the content is malformed
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")

        results: list[FileCoverage] = []
        current_file: str | None = None
        lines_found = 0
        lines_hit = 0
        branches_found: int | None = None
        branches_hit: int | None = None
        uncovered_lines: list[int] = []

        def _emit_record() -> None:
            """Emit the current file record if valid."""
            nonlocal current_file, lines_found, lines_hit
            nonlocal branches_found, branches_hit, uncovered_lines

            if current_file is None:
                return

            # Normalize path: remove leading / and convert to POSIX
            path = current_file
            if path.startswith("/"):
                # Try to make repo-relative by removing common prefixes
                # In practice, the adapter will handle full path normalization
                path = path.lstrip("/")
            path = path.replace("\\", "/")

            lines_missed = lines_found - lines_hit
            line_pct = compute_coverage_pct(lines_hit, lines_found)

            branch_pct: float | None = None
            if branches_found is not None and branches_hit is not None:
                branch_pct = compute_coverage_pct(branches_hit, branches_found)

            # Only include uncovered_lines if we tracked DA records
            final_uncovered: list[int] | None = None
            if uncovered_lines:
                final_uncovered = sorted(uncovered_lines)

            results.append(
                FileCoverage(
                    relative_path=path,
                    line_coverage_pct=line_pct,
                    branch_coverage_pct=branch_pct,
                    lines_total=lines_found,
                    lines_covered=lines_hit,
                    lines_missed=lines_missed,
                    branches_total=branches_found,
                    branches_covered=branches_hit,
                    uncovered_lines=final_uncovered,
                )
            )

            # Reset for next file
            current_file = None
            lines_found = 0
            lines_hit = 0
            branches_found = None
            branches_hit = None
            uncovered_lines = []

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue

            if line.startswith("SF:"):
                # New source file - emit previous record if any
                if current_file is not None:
                    _emit_record()
                current_file = line[3:]

            elif line.startswith("LF:"):
                # Lines found (total coverable lines)
                try:
                    lines_found = int(line[3:])
                except ValueError:
                    pass

            elif line.startswith("LH:"):
                # Lines hit (covered lines)
                try:
                    lines_hit = int(line[3:])
                except ValueError:
                    pass

            elif line.startswith("BRF:"):
                # Branches found
                try:
                    branches_found = int(line[4:])
                except ValueError:
                    pass

            elif line.startswith("BRH:"):
                # Branches hit
                try:
                    branches_hit = int(line[4:])
                except ValueError:
                    pass

            elif line.startswith("DA:"):
                # Line data: DA:<line number>,<hit count>
                try:
                    parts = line[3:].split(",")
                    if len(parts) >= 2:
                        line_num = int(parts[0])
                        hit_count = int(parts[1])
                        if hit_count == 0:
                            uncovered_lines.append(line_num)
                except ValueError:
                    pass

            elif line == "end_of_record":
                _emit_record()

        # Handle file without end_of_record at the end
        if current_file is not None:
            _emit_record()

        return results
