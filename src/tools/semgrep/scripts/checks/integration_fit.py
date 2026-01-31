"""
Integration fit checks for Semgrep smell analysis.

Ensures outputs are compatible with the collector pipeline expectations.
"""

import os

from . import CheckResult, CheckCategory


def run_integration_fit_checks(analysis: dict) -> list[CheckResult]:
    """Run integration fit checks."""
    results = []

    root_path = analysis.get("metadata", {}).get("root_path", "")
    files = analysis.get("files", [])

    absolute_paths = 0
    embedded_root = 0
    for file_info in files:
        path = file_info.get("path", "")
        if os.path.isabs(path):
            absolute_paths += 1
        if root_path and root_path in path:
            embedded_root += 1

    total_files = len(files)
    path_score = 1.0 if total_files == 0 else max(0.0, 1.0 - ((absolute_paths + embedded_root) / total_files))
    results.append(CheckResult(
        check_id="IF-1",
        name="Relative file paths",
        category=CheckCategory.INTEGRATION_FIT,
        passed=absolute_paths == 0 and embedded_root == 0,
        score=path_score,
        message=f"{total_files - absolute_paths}/{total_files} files have relative paths",
        evidence={
            "absolute_paths": absolute_paths,
            "embedded_root": embedded_root,
            "root_path": root_path,
        },
    ))

    smells = [s for f in files for s in f.get("smells", [])]
    missing_fields = 0
    for smell in smells:
        for field in ("dd_smell_id", "dd_category", "line_start", "line_end", "severity"):
            if field not in smell:
                missing_fields += 1
                break

    total_smells = len(smells)
    smell_score = 1.0 if total_smells == 0 else max(0.0, 1.0 - (missing_fields / total_smells))
    results.append(CheckResult(
        check_id="IF-2",
        name="Smell entries include required fields",
        category=CheckCategory.INTEGRATION_FIT,
        passed=missing_fields == 0,
        score=smell_score,
        message=f"{total_smells - missing_fields}/{total_smells} smells include required fields",
        evidence={
            "total_smells": total_smells,
            "smells_missing_fields": missing_fields,
        },
    ))

    return results
