"""Cobertura XML format parser for coverage reports.

Cobertura is an XML format commonly used by:
- coverage.py (Python)
- Istanbul (JavaScript, with reporters)
- Gradle JaCoCo (with Cobertura report type)
- Many CI/CD platforms

Format structure:
    <coverage line-rate="0.85" branch-rate="0.72">
        <packages>
            <package name="com.example">
                <classes>
                    <class name="MyClass" filename="src/MyClass.java" line-rate="0.9">
                        <lines>
                            <line number="1" hits="5"/>
                            <line number="2" hits="0"/>
                        </lines>
                    </class>
                </classes>
            </package>
        </packages>
    </coverage>
"""
from __future__ import annotations

import defusedxml.ElementTree as ET

from .base import BaseCoverageParser, FileCoverage, compute_coverage_pct


class CoberturaParser(BaseCoverageParser):
    """Parser for Cobertura XML format coverage reports."""

    @property
    def format_name(self) -> str:
        return "cobertura"

    def detect(self, content: str | bytes) -> bool:
        """Detect Cobertura format by looking for characteristic XML structure.

        Cobertura files have a <coverage> root element with line-rate attribute.
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")

        # Quick text-based detection before XML parsing
        has_coverage_tag = "<coverage" in content
        has_line_rate = "line-rate=" in content
        has_packages = "<packages" in content.lower() or "<package" in content.lower()

        return has_coverage_tag and has_line_rate and has_packages

    def parse(self, content: str | bytes) -> list[FileCoverage]:
        """Parse Cobertura XML format coverage data.

        Args:
            content: Cobertura XML file content

        Returns:
            List of FileCoverage records

        Raises:
            ValueError: If the content is malformed
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")

        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML: {e}") from e

        if root.tag != "coverage":
            raise ValueError(f"Expected <coverage> root element, got <{root.tag}>")

        results: list[FileCoverage] = []

        # Find all class elements (they contain the filename and coverage data)
        for cls in root.iter("class"):
            filename = cls.get("filename")
            if not filename:
                continue

            # Normalize path
            path = filename.replace("\\", "/")
            if path.startswith("/"):
                path = path.lstrip("/")

            # Get line-rate and branch-rate from class attributes
            line_rate_str = cls.get("line-rate", "0")
            branch_rate_str = cls.get("branch-rate")

            try:
                line_rate = float(line_rate_str)
            except ValueError:
                line_rate = 0.0

            branch_rate: float | None = None
            if branch_rate_str:
                try:
                    branch_rate = float(branch_rate_str)
                except ValueError:
                    pass

            # Count lines from <lines> element and track uncovered lines
            lines_elem = cls.find("lines")
            lines_total = 0
            lines_covered = 0
            uncovered_lines: list[int] = []

            if lines_elem is not None:
                for line in lines_elem.findall("line"):
                    lines_total += 1
                    line_num_str = line.get("number", "0")
                    hits_str = line.get("hits", "0")
                    try:
                        line_num = int(line_num_str)
                        hits = int(hits_str)
                        if hits > 0:
                            lines_covered += 1
                        else:
                            uncovered_lines.append(line_num)
                    except ValueError:
                        pass

            # If no lines found, try to use line-rate to estimate
            # (some Cobertura reports only include rates, not individual lines)
            if lines_total == 0:
                # Can't compute meaningful coverage without line data
                lines_missed = 0
                line_pct = round(line_rate * 100, 2) if line_rate else None
            else:
                lines_missed = lines_total - lines_covered
                line_pct = compute_coverage_pct(lines_covered, lines_total)

            # Branch coverage - Cobertura typically only provides rate
            branch_pct: float | None = None
            branches_total: int | None = None
            branches_covered: int | None = None

            # Branch coverage is only meaningful with actual counts.
            # Cobertura branch-rate="0" without counts means "no branch data tracked",
            # so we leave branch_pct as None for consistency.

            # Only include uncovered_lines if we have line data
            final_uncovered: list[int] | None = None
            if uncovered_lines:
                final_uncovered = sorted(uncovered_lines)

            results.append(
                FileCoverage(
                    relative_path=path,
                    line_coverage_pct=line_pct,
                    branch_coverage_pct=branch_pct,
                    lines_total=lines_total,
                    lines_covered=lines_covered,
                    lines_missed=lines_missed,
                    branches_total=branches_total,
                    branches_covered=branches_covered,
                    uncovered_lines=final_uncovered,
                )
            )

        return results
