"""Integration fit checks for DevSkim analysis."""

import os

from . import CheckResult, CheckCategory


def run_integration_fit_checks(analysis: dict) -> list[CheckResult]:
    """Run integration fit checks for file path sanity."""
    results: list[CheckResult] = []
    files = analysis.get("files", [])
    absolute_paths = 0

    for file_info in files:
        if os.path.isabs(file_info.get("path", "")):
            absolute_paths += 1

    total_files = len(files)
    passed = absolute_paths == 0
    score = 1.0 if total_files == 0 else max(0.0, 1.0 - (absolute_paths / total_files))
    results.append(CheckResult(
        check_id="IF-1",
        name="Relative file paths",
        category=CheckCategory.INTEGRATION_FIT,
        passed=passed,
        score=score,
        message=f"{total_files - absolute_paths}/{total_files} files have relative paths",
        evidence={"absolute_paths": absolute_paths},
    ))
    return results
