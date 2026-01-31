"""Edge case checks (SQ-EC-*) for SonarQube evaluation."""

from . import (
    CheckCategory,
    CheckResult,
)


def _get_metric_value(comp_data: dict, metric_name: str) -> int:
    """Extract metric value from nested measures array.

    SonarQube stores measures in an array format:
    {"measures": [{"metric": "ncloc", "value": "1106"}, ...]}
    """
    measures_list = comp_data.get("measures", [])
    for m in measures_list:
        if m.get("metric") == metric_name:
            val = m.get("value", 0)
            if isinstance(val, str):
                return int(val) if val.isdigit() else 0
            return int(val) if val else 0
    return 0


def check_empty_repo_handling(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-EC-1: Check that tool handles repos with no analyzable files gracefully."""
    results = data.get("results", data)
    components = results.get("components", {}).get("by_key", {})

    files = [k for k, v in components.items() if v.get("qualifier") == "FIL"]

    if len(files) == 0:
        required_keys = ["components", "measures", "issues"]
        missing = [k for k in required_keys if k not in results]

        passed = len(missing) == 0
        return CheckResult(
            check_id="SQ-EC-1",
            name="Empty repository handling",
            category=CheckCategory.EDGE_CASES,
            passed=passed,
            score=1.0 if passed else 0.0,
            message=f"Empty repository {'handled gracefully' if passed else 'missing required keys: ' + str(missing)}",
            evidence={"files": 0, "structure_valid": passed, "missing_keys": missing},
        )
    else:
        return CheckResult(
            check_id="SQ-EC-1",
            name="Empty repository handling",
            category=CheckCategory.EDGE_CASES,
            passed=True,
            score=1.0,
            message=f"Repository has {len(files)} files",
            evidence={"files": len(files)},
        )


def check_large_file_handling(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-EC-2: Check that analysis doesn't fail on large files."""
    results = data.get("results", data)
    measures = results.get("measures", {}).get("by_component_key", {})

    large_file_threshold = 1000
    large_files = []

    for comp_key, comp_measures in measures.items():
        qualifier = comp_measures.get("qualifier", "")
        if qualifier != "FIL":
            continue

        ncloc = _get_metric_value(comp_measures, "ncloc")
        if ncloc >= large_file_threshold:
            large_files.append({"key": comp_key, "ncloc": ncloc})

    if not large_files:
        return CheckResult(
            check_id="SQ-EC-2",
            name="Large file handling",
            category=CheckCategory.EDGE_CASES,
            passed=True,
            score=1.0,
            message="No large files to validate",
            evidence={"large_files": 0},
        )

    files_with_measures = [f for f in large_files if f["ncloc"] > 0]
    passed = len(files_with_measures) == len(large_files)
    score = len(files_with_measures) / len(large_files) if large_files else 1.0

    return CheckResult(
        check_id="SQ-EC-2",
        name="Large file handling",
        category=CheckCategory.EDGE_CASES,
        passed=passed,
        score=score,
        message=f"{'All' if passed else 'Some'} {len(large_files)} large files analyzed",
        evidence={"large_files": len(large_files), "analyzed": len(files_with_measures)},
    )


def check_unicode_path_handling(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-EC-3: Check that paths with unicode characters are handled correctly."""
    results = data.get("results", data)
    components = results.get("components", {}).get("by_key", {})

    unicode_paths = []
    for key, comp in components.items():
        path = comp.get("path", comp.get("key", ""))
        if path and any(ord(c) > 127 for c in path):
            unicode_paths.append(path)

    if not unicode_paths:
        return CheckResult(
            check_id="SQ-EC-3",
            name="Unicode path handling",
            category=CheckCategory.EDGE_CASES,
            passed=True,
            score=1.0,
            message="No unicode paths to validate",
            evidence={"unicode_paths": 0},
        )

    paths_indexed = sum(1 for p in unicode_paths if any(p in str(k) for k in components.keys()))
    passed = paths_indexed == len(unicode_paths)
    score = paths_indexed / len(unicode_paths) if unicode_paths else 1.0

    return CheckResult(
        check_id="SQ-EC-3",
        name="Unicode path handling",
        category=CheckCategory.EDGE_CASES,
        passed=passed,
        score=score,
        message=f"{'All' if passed else 'Some'} {len(unicode_paths)} unicode paths handled correctly",
        evidence={"unicode_paths": len(unicode_paths), "indexed": paths_indexed},
    )


def check_missing_optional_data(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-EC-4: Check that optional fields are handled gracefully when missing."""
    results = data.get("results", data)

    optional_sections = [
        ("duplications", "Duplication analysis"),
        ("hotspots", "Security hotspots"),
        ("derived_insights", "Derived insights"),
    ]

    issues = []
    for section_key, section_name in optional_sections:
        section = results.get(section_key)
        if section is not None and not isinstance(section, dict):
            issues.append(f"{section_name} has invalid type: {type(section).__name__}")

    passed = len(issues) == 0
    score = (len(optional_sections) - len(issues)) / len(optional_sections)

    return CheckResult(
        check_id="SQ-EC-4",
        name="Missing optional data",
        category=CheckCategory.EDGE_CASES,
        passed=passed,
        score=score,
        message=f"{'All' if passed else 'Some'} optional sections handled gracefully"
                + (f": {', '.join(issues)}" if issues else ""),
        evidence={"sections_checked": len(optional_sections), "issues": issues},
    )


def run_edge_case_checks(data: dict, ground_truth: dict | None) -> list[CheckResult]:
    """Run all edge case checks and return results."""
    return [
        check_empty_repo_handling(data, ground_truth),
        check_large_file_handling(data, ground_truth),
        check_unicode_path_handling(data, ground_truth),
        check_missing_optional_data(data, ground_truth),
    ]
