"""
Accuracy Checks (AC-1 to AC-8).

Validates counts, paths, and structural accuracy against ground truth.
"""

from typing import Any, Dict, List, Optional

from . import CheckCategory, CheckResult, register_check


def run_accuracy_checks(
    output: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]] = None,
) -> List[CheckResult]:
    """Run all accuracy checks."""
    checks = []

    checks.append(check_file_count(output, ground_truth))
    checks.append(check_directory_count(output, ground_truth))
    checks.append(check_path_normalization(output))
    checks.append(check_size_accuracy(output))
    checks.append(check_depth_calculation(output))
    checks.append(check_parent_links(output))
    checks.append(check_child_lists(output))
    checks.append(check_recursive_counts(output))

    return checks


@register_check("AC-1")
def check_file_count(
    output: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]] = None,
) -> CheckResult:
    """AC-1: Total files matches ground truth (if provided) or is reasonable."""
    files = output.get("files", {})
    stats = output.get("statistics", {})
    actual_count = len(files)
    stats_count = stats.get("total_files", 0)

    if actual_count != stats_count:
        return CheckResult(
            check_id="AC-1",
            name="File Count",
            category=CheckCategory.ACCURACY,
            passed=False,
            score=0.0,
            message=f"File count mismatch: files={actual_count}, stats={stats_count}",
        )

    if ground_truth:
        expected = ground_truth.get("expected", {}).get("total_files")
        if expected is not None and expected != actual_count:
            tolerance = ground_truth.get("thresholds", {}).get("count_tolerance", 0)
            if abs(expected - actual_count) > tolerance:
                return CheckResult(
                    check_id="AC-1",
                    name="File Count",
                    category=CheckCategory.ACCURACY,
                    passed=False,
                    score=0.5,
                    message=f"File count differs from ground truth: expected={expected}, actual={actual_count}",
                    evidence={"expected": expected, "actual": actual_count},
                )

    return CheckResult(
        check_id="AC-1",
        name="File Count",
        category=CheckCategory.ACCURACY,
        passed=True,
        score=1.0,
        message=f"File count accurate: {actual_count}",
        evidence={"count": actual_count},
    )


@register_check("AC-2")
def check_directory_count(
    output: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]] = None,
) -> CheckResult:
    """AC-2: Total directories matches ground truth (if provided)."""
    directories = output.get("directories", {})
    stats = output.get("statistics", {})
    actual_count = len(directories)
    stats_count = stats.get("total_directories", 0)

    if actual_count != stats_count:
        return CheckResult(
            check_id="AC-2",
            name="Directory Count",
            category=CheckCategory.ACCURACY,
            passed=False,
            score=0.0,
            message=f"Directory count mismatch: dirs={actual_count}, stats={stats_count}",
        )

    if ground_truth:
        expected = ground_truth.get("expected", {}).get("total_directories")
        if expected is not None and expected != actual_count:
            tolerance = ground_truth.get("thresholds", {}).get("count_tolerance", 0)
            if abs(expected - actual_count) > tolerance:
                return CheckResult(
                    check_id="AC-2",
                    name="Directory Count",
                    category=CheckCategory.ACCURACY,
                    passed=False,
                    score=0.5,
                    message=f"Directory count differs from ground truth: expected={expected}, actual={actual_count}",
                    evidence={"expected": expected, "actual": actual_count},
                )

    return CheckResult(
        check_id="AC-2",
        name="Directory Count",
        category=CheckCategory.ACCURACY,
        passed=True,
        score=1.0,
        message=f"Directory count accurate: {actual_count}",
        evidence={"count": actual_count},
    )


@register_check("AC-3")
def check_path_normalization(output: Dict[str, Any]) -> CheckResult:
    """AC-3: Paths are normalized correctly (no ./, \\, leading /)."""
    files = output.get("files", {})
    directories = output.get("directories", {})

    invalid_paths = []

    for path in files.keys():
        if path.startswith("./") or path.startswith("/") or "\\" in path:
            invalid_paths.append({"type": "file", "path": path})

    for path in directories.keys():
        if path and (path.startswith("./") or path.startswith("/") or "\\" in path):
            invalid_paths.append({"type": "directory", "path": path})

    if invalid_paths:
        return CheckResult(
            check_id="AC-3",
            name="Path Normalization",
            category=CheckCategory.ACCURACY,
            passed=False,
            score=0.5,
            message=f"{len(invalid_paths)} paths not properly normalized",
            evidence={"invalid_paths": invalid_paths[:10]},
        )

    return CheckResult(
        check_id="AC-3",
        name="Path Normalization",
        category=CheckCategory.ACCURACY,
        passed=True,
        score=1.0,
        message="All paths properly normalized",
    )


@register_check("AC-4")
def check_size_accuracy(output: Dict[str, Any]) -> CheckResult:
    """AC-4: File sizes are non-negative and total matches."""
    files = output.get("files", {})
    stats = output.get("statistics", {})

    negative_sizes = []
    total_size = 0

    for path, file_obj in files.items():
        size = file_obj.get("size_bytes", 0)
        if size < 0:
            negative_sizes.append({"path": path, "size": size})
        total_size += size

    if negative_sizes:
        return CheckResult(
            check_id="AC-4",
            name="Size Accuracy",
            category=CheckCategory.ACCURACY,
            passed=False,
            score=0.0,
            message=f"{len(negative_sizes)} files have negative size",
            evidence={"negative_sizes": negative_sizes[:5]},
        )

    stats_size = stats.get("total_size_bytes", 0)
    if total_size != stats_size:
        return CheckResult(
            check_id="AC-4",
            name="Size Accuracy",
            category=CheckCategory.ACCURACY,
            passed=False,
            score=0.5,
            message=f"Total size mismatch: computed={total_size}, stats={stats_size}",
        )

    return CheckResult(
        check_id="AC-4",
        name="Size Accuracy",
        category=CheckCategory.ACCURACY,
        passed=True,
        score=1.0,
        message=f"Size calculations accurate: {total_size} bytes total",
    )


@register_check("AC-5")
def check_depth_calculation(output: Dict[str, Any]) -> CheckResult:
    """AC-5: Depth values are correct based on path."""
    files = output.get("files", {})
    directories = output.get("directories", {})

    incorrect_depths = []

    for path, file_obj in files.items():
        expected_depth = path.count("/") if path else 0
        actual_depth = file_obj.get("depth", 0)
        if expected_depth != actual_depth:
            incorrect_depths.append({
                "path": path,
                "expected": expected_depth,
                "actual": actual_depth,
            })

    for path, dir_obj in directories.items():
        if path:  # Skip root
            expected_depth = path.count("/")
            actual_depth = dir_obj.get("depth", 0)
            if expected_depth != actual_depth:
                incorrect_depths.append({
                    "path": path,
                    "expected": expected_depth,
                    "actual": actual_depth,
                })

    if incorrect_depths:
        return CheckResult(
            check_id="AC-5",
            name="Depth Calculation",
            category=CheckCategory.ACCURACY,
            passed=False,
            score=0.5,
            message=f"{len(incorrect_depths)} items have incorrect depth",
            evidence={"incorrect_depths": incorrect_depths[:10]},
        )

    return CheckResult(
        check_id="AC-5",
        name="Depth Calculation",
        category=CheckCategory.ACCURACY,
        passed=True,
        score=1.0,
        message="All depth values correct",
    )


@register_check("AC-6")
def check_parent_links(output: Dict[str, Any]) -> CheckResult:
    """AC-6: Every file has valid parent_directory_id."""
    files = output.get("files", {})
    directories = output.get("directories", {})

    # Build set of valid directory IDs
    valid_dir_ids = {d.get("id") for d in directories.values()}

    missing_parents = []
    invalid_parents = []

    for path, file_obj in files.items():
        parent_id = file_obj.get("parent_directory_id")
        if not parent_id:
            missing_parents.append(path)
        elif parent_id not in valid_dir_ids:
            invalid_parents.append({"path": path, "parent_id": parent_id})

    if missing_parents or invalid_parents:
        return CheckResult(
            check_id="AC-6",
            name="Parent Links",
            category=CheckCategory.ACCURACY,
            passed=False,
            score=0.5,
            message=f"{len(missing_parents)} missing, {len(invalid_parents)} invalid parent links",
            evidence={
                "missing_parents": missing_parents[:5],
                "invalid_parents": invalid_parents[:5],
            },
        )

    return CheckResult(
        check_id="AC-6",
        name="Parent Links",
        category=CheckCategory.ACCURACY,
        passed=True,
        score=1.0,
        message="All parent links valid",
    )


@register_check("AC-7")
def check_child_lists(output: Dict[str, Any]) -> CheckResult:
    """AC-7: Directory children lists match actual contents."""
    files = output.get("files", {})
    directories = output.get("directories", {})

    errors = []

    for dir_path, dir_obj in directories.items():
        dir_id = dir_obj.get("id")
        child_file_ids = set(dir_obj.get("child_file_ids", []))
        child_dir_ids = set(dir_obj.get("child_directory_ids", []))

        # Find actual children
        actual_file_ids = set()
        for file_obj in files.values():
            if file_obj.get("parent_directory_id") == dir_id:
                actual_file_ids.add(file_obj.get("id"))

        actual_dir_ids = set()
        for sub_dir_obj in directories.values():
            if sub_dir_obj.get("parent_directory_id") == dir_id:
                actual_dir_ids.add(sub_dir_obj.get("id"))

        if child_file_ids != actual_file_ids:
            errors.append({
                "dir_path": dir_path,
                "issue": "file_mismatch",
                "listed": len(child_file_ids),
                "actual": len(actual_file_ids),
            })

        if child_dir_ids != actual_dir_ids:
            errors.append({
                "dir_path": dir_path,
                "issue": "dir_mismatch",
                "listed": len(child_dir_ids),
                "actual": len(actual_dir_ids),
            })

    if errors:
        return CheckResult(
            check_id="AC-7",
            name="Child Lists",
            category=CheckCategory.ACCURACY,
            passed=False,
            score=0.5,
            message=f"{len(errors)} directories have incorrect child lists",
            evidence={"errors": errors[:10]},
        )

    return CheckResult(
        check_id="AC-7",
        name="Child Lists",
        category=CheckCategory.ACCURACY,
        passed=True,
        score=1.0,
        message="All child lists correct",
    )


@register_check("AC-8")
def check_recursive_counts(output: Dict[str, Any]) -> CheckResult:
    """AC-8: Recursive counts sum correctly."""
    directories = output.get("directories", {})

    errors = []

    for dir_path, dir_obj in directories.items():
        direct_files = dir_obj.get("direct_file_count", 0)
        direct_dirs = dir_obj.get("direct_directory_count", 0)
        recursive_files = dir_obj.get("recursive_file_count", 0)
        recursive_dirs = dir_obj.get("recursive_directory_count", 0)

        # Recursive counts should be >= direct counts
        if recursive_files < direct_files:
            errors.append({
                "dir_path": dir_path,
                "issue": "recursive_files < direct_files",
                "recursive": recursive_files,
                "direct": direct_files,
            })

        if recursive_dirs < direct_dirs:
            errors.append({
                "dir_path": dir_path,
                "issue": "recursive_dirs < direct_dirs",
                "recursive": recursive_dirs,
                "direct": direct_dirs,
            })

    if errors:
        return CheckResult(
            check_id="AC-8",
            name="Recursive Counts",
            category=CheckCategory.ACCURACY,
            passed=False,
            score=0.5,
            message=f"{len(errors)} directories have invalid recursive counts",
            evidence={"errors": errors[:10]},
        )

    return CheckResult(
        check_id="AC-8",
        name="Recursive Counts",
        category=CheckCategory.ACCURACY,
        passed=True,
        score=1.0,
        message="All recursive counts valid",
    )
