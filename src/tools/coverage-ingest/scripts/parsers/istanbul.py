"""Istanbul JSON format parser for coverage reports.

Istanbul is a JSON format used by JavaScript/TypeScript coverage tools:
- nyc (Node.js)
- Jest
- Karma
- c8

Format structure (coverage-final.json):
{
  "/path/to/file.js": {
    "path": "/path/to/file.js",
    "statementMap": { "0": { "start": {...}, "end": {...} }, ... },
    "fnMap": { "0": { "name": "func", ... }, ... },
    "branchMap": { "0": { "type": "if", ... }, ... },
    "s": { "0": 5, "1": 0, ... },  // statement hit counts
    "f": { "0": 3, ... },           // function hit counts
    "b": { "0": [2, 1], ... }       // branch hit counts
  }
}

Note: Istanbul also has a summary format (coverage-summary.json) which
provides only aggregate numbers without file details.
"""
from __future__ import annotations

import json

from .base import BaseCoverageParser, FileCoverage, compute_coverage_pct


class IstanbulParser(BaseCoverageParser):
    """Parser for Istanbul JSON format coverage reports."""

    @property
    def format_name(self) -> str:
        return "istanbul"

    def detect(self, content: str | bytes) -> bool:
        """Detect Istanbul format by looking for characteristic JSON structure.

        Istanbul coverage-final.json files have path -> coverage data mapping
        with s/f/b keys for statements/functions/branches.
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")

        # Quick text-based detection
        if not content.strip().startswith("{"):
            return False

        # Look for Istanbul-specific keys
        has_s = '"s":' in content or '"s" :' in content
        has_path = '"path":' in content or '"path" :' in content

        # Must have 's' key (statement counts) - this is the core Istanbul identifier
        # Path is also common in Istanbul files
        return has_s and has_path

    def parse(self, content: str | bytes) -> list[FileCoverage]:
        """Parse Istanbul JSON format coverage data.

        Args:
            content: Istanbul JSON file content

        Returns:
            List of FileCoverage records

        Raises:
            ValueError: If the content is malformed
        """
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("Expected JSON object at root level")

        results: list[FileCoverage] = []

        for file_path, file_data in data.items():
            if not isinstance(file_data, dict):
                continue

            # Get the path from the data or use the key
            path = file_data.get("path", file_path)

            # Normalize path
            path = path.replace("\\", "/")
            if path.startswith("/"):
                path = path.lstrip("/")

            # Extract statement coverage from 's' map
            statements = file_data.get("s", {})
            statement_map = file_data.get("statementMap", {})
            lines_total = len(statements)
            lines_covered = sum(1 for hits in statements.values() if hits and hits > 0)
            lines_missed = lines_total - lines_covered

            # Extract uncovered line numbers from statementMap for uncovered statements
            uncovered_lines: list[int] = []
            for stmt_key, hits in statements.items():
                if not hits or hits == 0:
                    # Look up the line number from statementMap
                    stmt_info = statement_map.get(stmt_key, {})
                    if isinstance(stmt_info, dict):
                        start = stmt_info.get("start", {})
                        if isinstance(start, dict):
                            line_num = start.get("line")
                            if line_num is not None and isinstance(line_num, int):
                                uncovered_lines.append(line_num)

            line_pct = compute_coverage_pct(lines_covered, lines_total)

            # Extract branch coverage from 'b' map
            # Each branch key maps to an array of hit counts for each branch path
            branches = file_data.get("b", {})
            branches_total: int | None = None
            branches_covered: int | None = None
            branch_pct: float | None = None

            # Only compute branch coverage if there are actual branches
            if branches and len(branches) > 0:
                branches_total = 0
                branches_covered = 0
                for branch_hits in branches.values():
                    if isinstance(branch_hits, list):
                        for hits in branch_hits:
                            branches_total += 1
                            if hits and hits > 0:
                                branches_covered += 1

                branch_pct = compute_coverage_pct(branches_covered, branches_total)

            # Only include uncovered_lines if we have statementMap data
            final_uncovered: list[int] | None = None
            if uncovered_lines:
                # Deduplicate and sort (multiple statements can be on same line)
                final_uncovered = sorted(set(uncovered_lines))

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
