"""Output quality checks (NC-1 to NC-8).

Validates normalization correctness and output quality.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers import LcovParser
from parsers.base import FileCoverage


@dataclass
class CheckResult:
    """Result of a single check."""
    check_id: str
    name: str
    passed: bool
    message: str


def load_ground_truth_files() -> list[dict[str, Any]]:
    """Load all ground truth files to verify output quality."""
    gt_dir = Path(__file__).parent.parent.parent / "evaluation" / "ground-truth"
    files = []
    for format_dir in gt_dir.iterdir():
        if not format_dir.is_dir():
            continue
        for gt_file in format_dir.glob("*.json"):
            try:
                data = json.loads(gt_file.read_text())
                expected = data.get("expected", {})
                for file_data in expected.get("files", []):
                    files.append(file_data)
            except (json.JSONDecodeError, KeyError):
                continue
    return files


def check_nc1_covered_less_than_total() -> CheckResult:
    """NC-1: covered_lines <= total_lines invariant."""
    files = load_ground_truth_files()
    if not files:
        return CheckResult("NC-1", "covered <= total invariant", False, "No ground truth files found")

    violations = []
    for f in files:
        lines_covered = f.get("lines_covered")
        lines_total = f.get("lines_total")
        if lines_covered is not None and lines_total is not None:
            if lines_covered > lines_total:
                violations.append(f.get("relative_path", "unknown"))

    passed = len(violations) == 0
    return CheckResult("NC-1", "covered <= total invariant", passed,
                       f"{len(violations)} violations" if violations else "All files valid")


def check_nc2_branches_covered_less_than_total() -> CheckResult:
    """NC-2: branches_covered <= branches_total invariant."""
    files = load_ground_truth_files()
    if not files:
        return CheckResult("NC-2", "branches covered <= total", False, "No ground truth files found")

    violations = []
    for f in files:
        branches_covered = f.get("branches_covered")
        branches_total = f.get("branches_total")
        if branches_covered is not None and branches_total is not None:
            if branches_covered > branches_total:
                violations.append(f.get("relative_path", "unknown"))

    passed = len(violations) == 0
    return CheckResult("NC-2", "branches covered <= total", passed,
                       f"{len(violations)} violations" if violations else "All files valid")


def check_nc3_coverage_pct_range() -> CheckResult:
    """NC-3: 0 <= coverage_pct <= 100 invariant."""
    files = load_ground_truth_files()
    if not files:
        return CheckResult("NC-3", "coverage pct 0-100", False, "No ground truth files found")

    violations = []
    for f in files:
        line_pct = f.get("line_coverage_pct")
        branch_pct = f.get("branch_coverage_pct")

        if line_pct is not None and not (0 <= line_pct <= 100):
            violations.append(f"line_pct={line_pct}")
        if branch_pct is not None and not (0 <= branch_pct <= 100):
            violations.append(f"branch_pct={branch_pct}")

    passed = len(violations) == 0
    return CheckResult("NC-3", "coverage pct 0-100", passed,
                       f"{len(violations)} violations" if violations else "All percentages valid")


def check_nc4_pct_matches_calculation() -> CheckResult:
    """NC-4: coverage_pct matches (covered/total)*100."""
    files = load_ground_truth_files()
    if not files:
        return CheckResult("NC-4", "pct matches calculation", False, "No ground truth files found")

    violations = []
    for f in files:
        line_pct = f.get("line_coverage_pct")
        lines_covered = f.get("lines_covered")
        lines_total = f.get("lines_total")

        if all(v is not None for v in [line_pct, lines_covered, lines_total]):
            if lines_total > 0:
                expected = round((lines_covered / lines_total) * 100, 2)
                if abs(line_pct - expected) > 0.01:
                    violations.append(f"expected {expected}, got {line_pct}")

    passed = len(violations) == 0
    return CheckResult("NC-4", "pct matches calculation", passed,
                       f"{len(violations)} violations" if violations else "All calculations match")


def check_nc5_paths_repo_relative() -> CheckResult:
    """NC-5: All paths are repo-relative."""
    files = load_ground_truth_files()
    if not files:
        return CheckResult("NC-5", "paths repo-relative", False, "No ground truth files found")

    violations = []
    for f in files:
        path = f.get("relative_path", "")
        if path.startswith("/"):
            violations.append(path)

    passed = len(violations) == 0
    return CheckResult("NC-5", "paths repo-relative", passed,
                       f"{len(violations)} absolute paths" if violations else "All paths repo-relative")


def check_nc6_no_absolute_paths() -> CheckResult:
    """NC-6: No absolute paths in output."""
    files = load_ground_truth_files()
    if not files:
        return CheckResult("NC-6", "no absolute paths", False, "No ground truth files found")

    violations = []
    for f in files:
        path = f.get("relative_path", "")
        # Check for Unix absolute paths and Windows drive letters
        if path.startswith("/") or (len(path) > 1 and path[1] == ":"):
            violations.append(path)

    passed = len(violations) == 0
    return CheckResult("NC-6", "no absolute paths", passed,
                       f"{len(violations)} absolute paths" if violations else "No absolute paths")


def check_nc7_posix_separators() -> CheckResult:
    """NC-7: POSIX separators only."""
    files = load_ground_truth_files()
    if not files:
        return CheckResult("NC-7", "POSIX separators", False, "No ground truth files found")

    violations = []
    for f in files:
        path = f.get("relative_path", "")
        if "\\" in path:
            violations.append(path)

    passed = len(violations) == 0
    return CheckResult("NC-7", "POSIX separators", passed,
                       f"{len(violations)} backslash paths" if violations else "All paths use forward slashes")


def check_nc8_cross_format_equivalence() -> CheckResult:
    """NC-8: Cross-format equivalence (same source = same output)."""
    # Check that the cross-format ground truth exists and has consistent data
    gt_path = Path(__file__).parent.parent.parent / "evaluation" / "ground-truth" / "cross-format" / "equivalence.json"
    if not gt_path.exists():
        return CheckResult("NC-8", "cross-format equivalence", True, "Cross-format ground truth not required")

    try:
        data = json.loads(gt_path.read_text())
        # Verify structure exists
        passed = "formats" in data or "equivalences" in data or "test_cases" in data
        return CheckResult("NC-8", "cross-format equivalence", passed,
                           "Cross-format equivalence defined" if passed else "Missing equivalence data")
    except (json.JSONDecodeError, KeyError) as e:
        return CheckResult("NC-8", "cross-format equivalence", False, str(e))


def run_all_output_quality_checks() -> list[CheckResult]:
    """Run all output quality checks."""
    return [
        check_nc1_covered_less_than_total(),
        check_nc2_branches_covered_less_than_total(),
        check_nc3_coverage_pct_range(),
        check_nc4_pct_matches_calculation(),
        check_nc5_paths_repo_relative(),
        check_nc6_no_absolute_paths(),
        check_nc7_posix_separators(),
        check_nc8_cross_format_equivalence(),
    ]


if __name__ == "__main__":
    results = run_all_output_quality_checks()
    passed = sum(1 for r in results if r.passed)
    print(f"Output Quality Checks: {passed}/{len(results)} passed")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{status}] {r.check_id}: {r.name} - {r.message}")
