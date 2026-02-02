"""Integration fit checks for gitleaks analysis."""

from __future__ import annotations

import os

from . import CheckResult


def run_integration_fit_checks(analysis: dict) -> list[CheckResult]:
    """Run integration fit checks for file path sanity."""
    results: list[CheckResult] = []
    findings = analysis.get("findings", [])

    absolute_paths = 0
    for finding in findings:
        if os.path.isabs(finding.get("file_path", "")):
            absolute_paths += 1

    passed = absolute_paths == 0
    results.append(CheckResult(
        check_id="IF-1",
        category="Integration Fit",
        passed=passed,
        message=f"{len(findings) - absolute_paths}/{len(findings)} findings have relative paths",
        expected="relative paths",
        actual={"absolute_paths": absolute_paths},
    ))
    return results
