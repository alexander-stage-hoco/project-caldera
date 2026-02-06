"""Accuracy checks for dependensee.

Validates that the tool correctly identifies:
- Project count
- Project references
- Package references
- Target frameworks
- Circular dependencies
"""

from __future__ import annotations


def check_project_count(output: dict, ground_truth: dict | None) -> dict:
    """Check if project count matches ground truth."""
    if ground_truth is None:
        return {
            "check_id": "accuracy.project_count",
            "status": "pass",
            "message": "No ground truth available (skipped)",
        }

    data = output.get("data", {})
    summary = data.get("summary", {})
    actual_count = summary.get("project_count", 0)
    expected = ground_truth.get("expected", {})
    expected_count = expected.get("project_count", 0)

    if actual_count == expected_count:
        return {
            "check_id": "accuracy.project_count",
            "status": "pass",
            "message": f"Project count matches: {actual_count}",
        }
    else:
        return {
            "check_id": "accuracy.project_count",
            "status": "fail",
            "message": f"Project count mismatch: expected {expected_count}, got {actual_count}",
        }


def check_project_paths(output: dict, ground_truth: dict | None) -> dict:
    """Check if all expected projects are found."""
    if ground_truth is None:
        return {
            "check_id": "accuracy.project_paths",
            "status": "pass",
            "message": "No ground truth available (skipped)",
        }

    data = output.get("data", {})
    projects = data.get("projects", [])
    actual_paths = {p.get("path") for p in projects}

    expected = ground_truth.get("expected", {})
    expected_projects = expected.get("projects", [])
    expected_paths = {p.get("path") for p in expected_projects}

    missing = expected_paths - actual_paths
    extra = actual_paths - expected_paths

    if not missing and not extra:
        return {
            "check_id": "accuracy.project_paths",
            "status": "pass",
            "message": f"All {len(expected_paths)} expected projects found",
        }

    issues = []
    if missing:
        issues.append(f"missing: {sorted(missing)}")
    if extra:
        issues.append(f"extra: {sorted(extra)}")

    return {
        "check_id": "accuracy.project_paths",
        "status": "fail",
        "message": f"Project path mismatch: {'; '.join(issues)}",
    }


def check_project_references(output: dict, ground_truth: dict | None) -> dict:
    """Check if project references are correctly identified."""
    if ground_truth is None:
        return {
            "check_id": "accuracy.project_references",
            "status": "pass",
            "message": "No ground truth available (skipped)",
        }

    data = output.get("data", {})
    projects = data.get("projects", [])
    actual_refs = {}
    for p in projects:
        actual_refs[p.get("path")] = set(p.get("project_references", []))

    expected = ground_truth.get("expected", {})
    expected_projects = expected.get("projects", [])
    expected_refs = {}
    for p in expected_projects:
        expected_refs[p.get("path")] = set(p.get("project_references", []))

    mismatches = []
    for path, expected_set in expected_refs.items():
        actual_set = actual_refs.get(path, set())
        if expected_set != actual_set:
            missing = expected_set - actual_set
            extra = actual_set - expected_set
            if missing or extra:
                mismatches.append(f"{path}: missing={list(missing)}, extra={list(extra)}")

    if not mismatches:
        total_refs = sum(len(r) for r in expected_refs.values())
        return {
            "check_id": "accuracy.project_references",
            "status": "pass",
            "message": f"All {total_refs} project references correctly identified",
        }

    return {
        "check_id": "accuracy.project_references",
        "status": "fail",
        "message": f"Project reference mismatches: {mismatches[:3]}",
    }


def check_package_references(output: dict, ground_truth: dict | None) -> dict:
    """Check if NuGet package references are correctly identified."""
    if ground_truth is None:
        return {
            "check_id": "accuracy.package_references",
            "status": "pass",
            "message": "No ground truth available (skipped)",
        }

    data = output.get("data", {})
    projects = data.get("projects", [])
    actual_pkgs = {}
    for p in projects:
        pkg_names = {pkg.get("name") for pkg in p.get("package_references", [])}
        actual_pkgs[p.get("path")] = pkg_names

    expected = ground_truth.get("expected", {})
    expected_projects = expected.get("projects", [])
    expected_pkgs = {}
    for p in expected_projects:
        pkg_names = {pkg.get("name") for pkg in p.get("package_references", [])}
        expected_pkgs[p.get("path")] = pkg_names

    mismatches = []
    for path, expected_set in expected_pkgs.items():
        actual_set = actual_pkgs.get(path, set())
        if expected_set != actual_set:
            missing = expected_set - actual_set
            extra = actual_set - expected_set
            if missing or extra:
                mismatches.append(f"{path}: missing={list(missing)}, extra={list(extra)}")

    if not mismatches:
        total_pkgs = sum(len(p) for p in expected_pkgs.values())
        return {
            "check_id": "accuracy.package_references",
            "status": "pass",
            "message": f"All {total_pkgs} package references correctly identified",
        }

    return {
        "check_id": "accuracy.package_references",
        "status": "fail",
        "message": f"Package reference mismatches: {mismatches[:3]}",
    }


def check_target_frameworks(output: dict, ground_truth: dict | None) -> dict:
    """Check if target frameworks are correctly identified."""
    if ground_truth is None:
        return {
            "check_id": "accuracy.target_frameworks",
            "status": "pass",
            "message": "No ground truth available (skipped)",
        }

    data = output.get("data", {})
    projects = data.get("projects", [])
    actual_tfs = {p.get("path"): p.get("target_framework") for p in projects}

    expected = ground_truth.get("expected", {})
    expected_projects = expected.get("projects", [])
    expected_tfs = {p.get("path"): p.get("target_framework") for p in expected_projects}

    mismatches = []
    for path, expected_tf in expected_tfs.items():
        actual_tf = actual_tfs.get(path)
        if expected_tf != actual_tf:
            mismatches.append(f"{path}: expected={expected_tf}, got={actual_tf}")

    if not mismatches:
        return {
            "check_id": "accuracy.target_frameworks",
            "status": "pass",
            "message": f"All target frameworks correctly identified",
        }

    return {
        "check_id": "accuracy.target_frameworks",
        "status": "fail",
        "message": f"Target framework mismatches: {mismatches[:3]}",
    }


def check_circular_dependencies(output: dict, ground_truth: dict | None) -> dict:
    """Check if circular dependencies are correctly detected."""
    if ground_truth is None:
        return {
            "check_id": "accuracy.circular_dependencies",
            "status": "pass",
            "message": "No ground truth available (skipped)",
        }

    data = output.get("data", {})
    actual_count = len(data.get("circular_dependencies", []))

    expected = ground_truth.get("expected", {})
    expected_count = expected.get("circular_dependency_count", 0)

    if actual_count == expected_count:
        return {
            "check_id": "accuracy.circular_dependencies",
            "status": "pass",
            "message": f"Circular dependency count matches: {actual_count}",
        }

    return {
        "check_id": "accuracy.circular_dependencies",
        "status": "fail",
        "message": f"Circular dependency count mismatch: expected {expected_count}, got {actual_count}",
    }
