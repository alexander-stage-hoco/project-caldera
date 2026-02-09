"""JaCoCo XML format parser for coverage reports.

JaCoCo is an XML format used by the Java Code Coverage library.
It uses instruction and branch counters rather than line rates.

Format structure:
    <report name="project">
        <package name="com/example">
            <sourcefile name="MyClass.java">
                <line nr="1" mi="0" ci="5" mb="0" cb="2"/>
                <counter type="LINE" missed="10" covered="90"/>
                <counter type="BRANCH" missed="5" covered="15"/>
            </sourcefile>
        </package>
    </report>

Counter types:
- INSTRUCTION: mi/ci (missed/covered instructions)
- BRANCH: mb/cb (missed/covered branches)
- LINE: missed/covered lines
- COMPLEXITY: missed/covered complexity
- METHOD: missed/covered methods
- CLASS: missed/covered classes
"""
from __future__ import annotations

import defusedxml.ElementTree as ET

from .base import BaseCoverageParser, FileCoverage, compute_coverage_pct


class JacocoParser(BaseCoverageParser):
    """Parser for JaCoCo XML format coverage reports."""

    @property
    def format_name(self) -> str:
        return "jacoco"

    def detect(self, content: str | bytes) -> bool:
        """Detect JaCoCo format by looking for characteristic XML structure.

        JaCoCo files have a <report> root element with <package> and <counter> elements.
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")

        # Quick text-based detection before XML parsing
        has_report_tag = "<report" in content
        has_counter = "<counter" in content
        has_type_attr = 'type="' in content

        # JaCoCo-specific: uses mi/ci for instruction counters
        has_mi_ci = " mi=" in content or " ci=" in content

        return has_report_tag and has_counter and (has_type_attr or has_mi_ci)

    def parse(self, content: str | bytes) -> list[FileCoverage]:
        """Parse JaCoCo XML format coverage data.

        Args:
            content: JaCoCo XML file content

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

        if root.tag != "report":
            raise ValueError(f"Expected <report> root element, got <{root.tag}>")

        results: list[FileCoverage] = []

        # JaCoCo structure: report > package > sourcefile
        for package in root.findall(".//package"):
            package_name = package.get("name", "").replace("/", ".")

            for sourcefile in package.findall("sourcefile"):
                filename = sourcefile.get("name")
                if not filename:
                    continue

                # Reconstruct path from package + filename
                if package_name:
                    # Convert package name back to path (com/example)
                    package_path = package.get("name", "").replace(".", "/")
                    path = f"{package_path}/{filename}"
                else:
                    path = filename

                # Normalize path
                path = path.replace("\\", "/")
                if path.startswith("/"):
                    path = path.lstrip("/")

                # Extract counters
                lines_missed = 0
                lines_covered = 0
                branches_missed: int | None = None
                branches_covered: int | None = None

                for counter in sourcefile.findall("counter"):
                    counter_type = counter.get("type")
                    missed = int(counter.get("missed", "0"))
                    covered = int(counter.get("covered", "0"))

                    if counter_type == "LINE":
                        lines_missed = missed
                        lines_covered = covered
                    elif counter_type == "BRANCH":
                        branches_missed = missed
                        branches_covered = covered

                # Extract uncovered lines from <line> elements
                # JaCoCo <line> has: nr (line number), mi (missed instructions), ci (covered instructions)
                # A line with mi > 0 and ci == 0 is uncovered
                uncovered_lines: list[int] = []
                for line_elem in sourcefile.findall("line"):
                    try:
                        line_nr = int(line_elem.get("nr", "0"))
                        mi = int(line_elem.get("mi", "0"))  # missed instructions
                        ci = int(line_elem.get("ci", "0"))  # covered instructions
                        if mi > 0 and ci == 0:
                            uncovered_lines.append(line_nr)
                    except ValueError:
                        pass

                lines_total = lines_missed + lines_covered
                line_pct = compute_coverage_pct(lines_covered, lines_total)

                branch_pct: float | None = None
                branches_total: int | None = None

                if branches_missed is not None and branches_covered is not None:
                    branches_total = branches_missed + branches_covered
                    branch_pct = compute_coverage_pct(branches_covered, branches_total)

                # Only include uncovered_lines if we found line elements
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
