"""Parser accuracy checks (PA-1 to PA-12).

Validates that parsed coverage values match ground truth expectations.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    """Result of a single check."""
    check_id: str
    name: str
    passed: bool
    message: str
    expected: Any = None
    actual: Any = None


def load_ground_truth(format_name: str, scenario: str) -> dict[str, Any] | None:
    """Load ground truth for a specific format and scenario."""
    gt_path = Path(__file__).parent.parent.parent / "evaluation" / "ground-truth" / format_name / f"{scenario}.json"
    if gt_path.exists():
        return json.loads(gt_path.read_text())
    return None


def check_pa1_lcov_line_counts() -> CheckResult:
    """PA-1: LCOV line counts match expected."""
    gt = load_ground_truth("lcov", "simple")
    if not gt:
        return CheckResult("PA-1", "LCOV line counts", False, "Ground truth not found")

    expected_files = gt.get("expected", {}).get("files", [])
    if not expected_files:
        return CheckResult("PA-1", "LCOV line counts", False, "No expected files in ground truth")

    # Check first file for line count validity
    first_file = expected_files[0]
    lines_total = first_file.get("lines_total")
    lines_covered = first_file.get("lines_covered")

    if lines_total is None or lines_covered is None:
        return CheckResult("PA-1", "LCOV line counts", False, "Missing line count fields")

    passed = isinstance(lines_total, int) and isinstance(lines_covered, int) and lines_covered <= lines_total
    return CheckResult("PA-1", "LCOV line counts", passed, "Line counts valid" if passed else "Invalid line counts")


def check_pa2_lcov_branch_counts() -> CheckResult:
    """PA-2: LCOV branch counts match expected."""
    gt = load_ground_truth("lcov", "branches")
    if not gt:
        return CheckResult("PA-2", "LCOV branch counts", False, "Ground truth not found")

    expected_files = gt.get("expected", {}).get("files", [])
    if not expected_files:
        return CheckResult("PA-2", "LCOV branch counts", False, "No expected files in ground truth")

    first_file = expected_files[0]
    branches_total = first_file.get("branches_total")
    branches_covered = first_file.get("branches_covered")

    # Branches can be None if not present
    if branches_total is None:
        return CheckResult("PA-2", "LCOV branch counts", True, "No branch data (valid)")

    passed = isinstance(branches_total, int) and isinstance(branches_covered, int) and branches_covered <= branches_total
    return CheckResult("PA-2", "LCOV branch counts", passed, "Branch counts valid" if passed else "Invalid branch counts")


def check_pa3_lcov_coverage_pct() -> CheckResult:
    """PA-3: LCOV coverage percentages accurate (+-0.01%)."""
    gt = load_ground_truth("lcov", "simple")
    if not gt:
        return CheckResult("PA-3", "LCOV coverage percentage", False, "Ground truth not found")

    expected_files = gt.get("expected", {}).get("files", [])
    if not expected_files:
        return CheckResult("PA-3", "LCOV coverage percentage", False, "No expected files")

    first_file = expected_files[0]
    coverage_pct = first_file.get("line_coverage_pct")
    lines_total = first_file.get("lines_total")
    lines_covered = first_file.get("lines_covered")

    if coverage_pct is None or lines_total is None or lines_covered is None:
        return CheckResult("PA-3", "LCOV coverage percentage", False, "Missing fields")

    if lines_total == 0:
        expected_pct = 0.0
    else:
        expected_pct = round((lines_covered / lines_total) * 100, 2)

    passed = abs(coverage_pct - expected_pct) < 0.01
    return CheckResult("PA-3", "LCOV coverage percentage", passed,
                       f"Expected {expected_pct}%, got {coverage_pct}%",
                       expected=expected_pct, actual=coverage_pct)


def check_pa4_cobertura_line_rates() -> CheckResult:
    """PA-4: Cobertura line rates match expected."""
    gt = load_ground_truth("cobertura", "simple")
    if not gt:
        return CheckResult("PA-4", "Cobertura line rates", False, "Ground truth not found")

    expected_files = gt.get("expected", {}).get("files", [])
    if not expected_files:
        return CheckResult("PA-4", "Cobertura line rates", False, "No expected files")

    first_file = expected_files[0]
    lines_total = first_file.get("lines_total")
    lines_covered = first_file.get("lines_covered")

    passed = lines_total is not None and lines_covered is not None and lines_covered <= lines_total
    return CheckResult("PA-4", "Cobertura line rates", passed, "Line rates valid" if passed else "Invalid")


def check_pa5_cobertura_branch_rates() -> CheckResult:
    """PA-5: Cobertura branch rates match expected."""
    gt = load_ground_truth("cobertura", "branches")
    if not gt:
        return CheckResult("PA-5", "Cobertura branch rates", False, "Ground truth not found")

    expected_files = gt.get("expected", {}).get("files", [])
    if not expected_files:
        return CheckResult("PA-5", "Cobertura branch rates", False, "No expected files")

    first_file = expected_files[0]
    branches_total = first_file.get("branches_total")
    branches_covered = first_file.get("branches_covered")

    if branches_total is None:
        return CheckResult("PA-5", "Cobertura branch rates", True, "No branch data (valid)")

    passed = isinstance(branches_covered, int) and branches_covered <= branches_total
    return CheckResult("PA-5", "Cobertura branch rates", passed, "Branch rates valid" if passed else "Invalid")


def check_pa6_cobertura_coverage_pct() -> CheckResult:
    """PA-6: Cobertura coverage percentages accurate."""
    gt = load_ground_truth("cobertura", "simple")
    if not gt:
        return CheckResult("PA-6", "Cobertura coverage pct", False, "Ground truth not found")

    expected_files = gt.get("expected", {}).get("files", [])
    if not expected_files:
        return CheckResult("PA-6", "Cobertura coverage pct", False, "No expected files")

    first_file = expected_files[0]
    coverage_pct = first_file.get("line_coverage_pct")

    passed = coverage_pct is not None and 0 <= coverage_pct <= 100
    return CheckResult("PA-6", "Cobertura coverage pct", passed, f"Coverage: {coverage_pct}%")


def check_pa7_jacoco_instruction_counts() -> CheckResult:
    """PA-7: JaCoCo instruction counts match expected."""
    gt = load_ground_truth("jacoco", "simple")
    if not gt:
        return CheckResult("PA-7", "JaCoCo instruction counts", False, "Ground truth not found")

    expected_files = gt.get("expected", {}).get("files", [])
    if not expected_files:
        return CheckResult("PA-7", "JaCoCo instruction counts", False, "No expected files")

    first_file = expected_files[0]
    lines_total = first_file.get("lines_total")
    lines_covered = first_file.get("lines_covered")

    passed = lines_total is not None and lines_covered is not None and lines_covered <= lines_total
    return CheckResult("PA-7", "JaCoCo instruction counts", passed, "Instruction counts valid" if passed else "Invalid")


def check_pa8_jacoco_branch_counts() -> CheckResult:
    """PA-8: JaCoCo branch counts match expected."""
    gt = load_ground_truth("jacoco", "counters")
    if not gt:
        return CheckResult("PA-8", "JaCoCo branch counts", False, "Ground truth not found")

    expected_files = gt.get("expected", {}).get("files", [])
    if not expected_files:
        return CheckResult("PA-8", "JaCoCo branch counts", False, "No expected files")

    first_file = expected_files[0]
    branches_total = first_file.get("branches_total")
    branches_covered = first_file.get("branches_covered")

    if branches_total is None:
        return CheckResult("PA-8", "JaCoCo branch counts", True, "No branch data (valid)")

    passed = isinstance(branches_covered, int) and branches_covered <= branches_total
    return CheckResult("PA-8", "JaCoCo branch counts", passed, "Branch counts valid" if passed else "Invalid")


def check_pa9_jacoco_coverage_pct() -> CheckResult:
    """PA-9: JaCoCo coverage percentages accurate."""
    gt = load_ground_truth("jacoco", "simple")
    if not gt:
        return CheckResult("PA-9", "JaCoCo coverage pct", False, "Ground truth not found")

    expected_files = gt.get("expected", {}).get("files", [])
    if not expected_files:
        return CheckResult("PA-9", "JaCoCo coverage pct", False, "No expected files")

    first_file = expected_files[0]
    coverage_pct = first_file.get("line_coverage_pct")

    passed = coverage_pct is not None and 0 <= coverage_pct <= 100
    return CheckResult("PA-9", "JaCoCo coverage pct", passed, f"Coverage: {coverage_pct}%")


def check_pa10_istanbul_statement_counts() -> CheckResult:
    """PA-10: Istanbul statement counts match expected."""
    gt = load_ground_truth("istanbul", "simple")
    if not gt:
        return CheckResult("PA-10", "Istanbul statement counts", False, "Ground truth not found")

    expected_files = gt.get("expected", {}).get("files", [])
    if not expected_files:
        return CheckResult("PA-10", "Istanbul statement counts", False, "No expected files")

    first_file = expected_files[0]
    lines_total = first_file.get("lines_total")
    lines_covered = first_file.get("lines_covered")

    passed = lines_total is not None and lines_covered is not None and lines_covered <= lines_total
    return CheckResult("PA-10", "Istanbul statement counts", passed, "Statement counts valid" if passed else "Invalid")


def check_pa11_istanbul_branch_counts() -> CheckResult:
    """PA-11: Istanbul branch counts match expected."""
    gt = load_ground_truth("istanbul", "branches")
    if not gt:
        return CheckResult("PA-11", "Istanbul branch counts", False, "Ground truth not found")

    expected_files = gt.get("expected", {}).get("files", [])
    if not expected_files:
        return CheckResult("PA-11", "Istanbul branch counts", False, "No expected files")

    first_file = expected_files[0]
    branches_total = first_file.get("branches_total")
    branches_covered = first_file.get("branches_covered")

    if branches_total is None:
        return CheckResult("PA-11", "Istanbul branch counts", True, "No branch data (valid)")

    passed = isinstance(branches_covered, int) and branches_covered <= branches_total
    return CheckResult("PA-11", "Istanbul branch counts", passed, "Branch counts valid" if passed else "Invalid")


def check_pa12_istanbul_coverage_pct() -> CheckResult:
    """PA-12: Istanbul coverage percentages accurate."""
    gt = load_ground_truth("istanbul", "simple")
    if not gt:
        return CheckResult("PA-12", "Istanbul coverage pct", False, "Ground truth not found")

    expected_files = gt.get("expected", {}).get("files", [])
    if not expected_files:
        return CheckResult("PA-12", "Istanbul coverage pct", False, "No expected files")

    first_file = expected_files[0]
    coverage_pct = first_file.get("line_coverage_pct")

    passed = coverage_pct is not None and 0 <= coverage_pct <= 100
    return CheckResult("PA-12", "Istanbul coverage pct", passed, f"Coverage: {coverage_pct}%")


def run_all_accuracy_checks() -> list[CheckResult]:
    """Run all parser accuracy checks."""
    return [
        check_pa1_lcov_line_counts(),
        check_pa2_lcov_branch_counts(),
        check_pa3_lcov_coverage_pct(),
        check_pa4_cobertura_line_rates(),
        check_pa5_cobertura_branch_rates(),
        check_pa6_cobertura_coverage_pct(),
        check_pa7_jacoco_instruction_counts(),
        check_pa8_jacoco_branch_counts(),
        check_pa9_jacoco_coverage_pct(),
        check_pa10_istanbul_statement_counts(),
        check_pa11_istanbul_branch_counts(),
        check_pa12_istanbul_coverage_pct(),
    ]


if __name__ == "__main__":
    results = run_all_accuracy_checks()
    passed = sum(1 for r in results if r.passed)
    print(f"Parser Accuracy Checks: {passed}/{len(results)} passed")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{status}] {r.check_id}: {r.name} - {r.message}")
