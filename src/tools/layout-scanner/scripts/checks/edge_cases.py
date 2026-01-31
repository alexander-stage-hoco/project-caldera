"""
Edge Case Checks (EC-1 to EC-6).

Validates handling of special cases like empty dirs, symlinks, unicode, etc.
"""

from typing import Any, Dict, List, Optional

from . import CheckCategory, CheckResult, register_check


def run_edge_case_checks(
    output: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]] = None,
) -> List[CheckResult]:
    """Run all edge case checks."""
    checks = []

    checks.append(check_empty_directories(output))
    checks.append(check_hidden_files(output))
    checks.append(check_symlinks(output))
    checks.append(check_unicode_paths(output))
    checks.append(check_deep_nesting(output))
    checks.append(check_special_characters(output))

    return checks


@register_check("EC-1")
def check_empty_directories(output: Dict[str, Any]) -> CheckResult:
    """EC-1: Empty directories are included with 0 counts."""
    directories = output.get("directories", {})

    empty_dirs = []
    invalid_empty_dirs = []

    for path, dir_obj in directories.items():
        direct_files = dir_obj.get("direct_file_count", 0)
        direct_dirs = dir_obj.get("direct_directory_count", 0)
        recursive_files = dir_obj.get("recursive_file_count", 0)
        recursive_dirs = dir_obj.get("recursive_directory_count", 0)

        # Empty directory has no direct children
        if direct_files == 0 and direct_dirs == 0:
            empty_dirs.append(path)

            # Recursive counts should also be 0 for truly empty
            if recursive_files != 0 or recursive_dirs != 0:
                invalid_empty_dirs.append({
                    "path": path,
                    "recursive_files": recursive_files,
                    "recursive_dirs": recursive_dirs,
                })

    if invalid_empty_dirs:
        return CheckResult(
            check_id="EC-1",
            name="Empty Directories",
            category=CheckCategory.EDGE_CASES,
            passed=False,
            score=0.5,
            message=f"{len(invalid_empty_dirs)} empty dirs have inconsistent counts",
            evidence={"invalid": invalid_empty_dirs[:5]},
        )

    return CheckResult(
        check_id="EC-1",
        name="Empty Directories",
        category=CheckCategory.EDGE_CASES,
        passed=True,
        score=1.0,
        message=f"{len(empty_dirs)} empty directories handled correctly",
        evidence={"empty_count": len(empty_dirs)},
    )


@register_check("EC-2")
def check_hidden_files(output: Dict[str, Any]) -> CheckResult:
    """EC-2: Hidden files (dotfiles) are handled correctly."""
    files = output.get("files", {})
    directories = output.get("directories", {})

    hidden_files = []
    hidden_dirs = []

    for path, file_obj in files.items():
        name = file_obj.get("name", "")
        if name.startswith("."):
            hidden_files.append(path)

    for path, dir_obj in directories.items():
        name = dir_obj.get("name", "")
        if name.startswith(".") and path:  # Exclude root
            hidden_dirs.append(path)

    # Check that hidden files have proper structure
    invalid_hidden = []

    for path in hidden_files:
        file_obj = files[path]
        if not file_obj.get("id") or not file_obj.get("parent_directory_id"):
            invalid_hidden.append(path)

    if invalid_hidden:
        return CheckResult(
            check_id="EC-2",
            name="Hidden Files",
            category=CheckCategory.EDGE_CASES,
            passed=False,
            score=0.5,
            message=f"{len(invalid_hidden)} hidden files have invalid structure",
            evidence={"invalid": invalid_hidden[:5]},
        )

    return CheckResult(
        check_id="EC-2",
        name="Hidden Files",
        category=CheckCategory.EDGE_CASES,
        passed=True,
        score=1.0,
        message=f"{len(hidden_files)} hidden files, {len(hidden_dirs)} hidden dirs handled",
        evidence={"hidden_files": len(hidden_files), "hidden_dirs": len(hidden_dirs)},
    )


@register_check("EC-3")
def check_symlinks(output: Dict[str, Any]) -> CheckResult:
    """EC-3: Symlinks are detected and marked correctly."""
    files = output.get("files", {})
    directories = output.get("directories", {})

    symlink_files = []
    symlink_dirs = []

    for path, file_obj in files.items():
        if file_obj.get("is_symlink"):
            symlink_files.append(path)

    for path, dir_obj in directories.items():
        if dir_obj.get("is_symlink"):
            symlink_dirs.append(path)

    # Check that symlinks have is_symlink field
    missing_field = []

    for path, file_obj in files.items():
        if "is_symlink" not in file_obj:
            missing_field.append({"type": "file", "path": path})

    for path, dir_obj in directories.items():
        if "is_symlink" not in dir_obj:
            missing_field.append({"type": "dir", "path": path})

    if missing_field:
        return CheckResult(
            check_id="EC-3",
            name="Symlinks",
            category=CheckCategory.EDGE_CASES,
            passed=False,
            score=0.5,
            message=f"{len(missing_field)} items missing is_symlink field",
            evidence={"missing": missing_field[:5]},
        )

    return CheckResult(
        check_id="EC-3",
        name="Symlinks",
        category=CheckCategory.EDGE_CASES,
        passed=True,
        score=1.0,
        message=f"{len(symlink_files)} file symlinks, {len(symlink_dirs)} dir symlinks detected",
        evidence={"symlink_files": len(symlink_files), "symlink_dirs": len(symlink_dirs)},
    )


@register_check("EC-4")
def check_unicode_paths(output: Dict[str, Any]) -> CheckResult:
    """EC-4: Unicode filenames are handled correctly."""
    files = output.get("files", {})
    directories = output.get("directories", {})

    unicode_files = []
    unicode_dirs = []

    for path in files.keys():
        # Check if path contains non-ASCII characters
        try:
            path.encode("ascii")
        except UnicodeEncodeError:
            unicode_files.append(path)

    for path in directories.keys():
        if path:  # Skip root
            try:
                path.encode("ascii")
            except UnicodeEncodeError:
                unicode_dirs.append(path)

    # If there are unicode paths, verify they're properly structured
    invalid_unicode = []

    for path in unicode_files:
        file_obj = files[path]
        if not file_obj.get("id") or not file_obj.get("name"):
            invalid_unicode.append(path)

    if invalid_unicode:
        return CheckResult(
            check_id="EC-4",
            name="Unicode Paths",
            category=CheckCategory.EDGE_CASES,
            passed=False,
            score=0.5,
            message=f"{len(invalid_unicode)} unicode paths have invalid structure",
            evidence={"invalid": invalid_unicode[:5]},
        )

    return CheckResult(
        check_id="EC-4",
        name="Unicode Paths",
        category=CheckCategory.EDGE_CASES,
        passed=True,
        score=1.0,
        message=f"{len(unicode_files)} unicode files, {len(unicode_dirs)} unicode dirs handled",
        evidence={"unicode_files": len(unicode_files), "unicode_dirs": len(unicode_dirs)},
    )


@register_check("EC-5")
def check_deep_nesting(output: Dict[str, Any]) -> CheckResult:
    """EC-5: Deep nesting (20+ levels) is handled correctly."""
    stats = output.get("statistics", {})
    hierarchy = output.get("hierarchy", {})
    directories = output.get("directories", {})

    max_depth = stats.get("max_depth", 0)
    hierarchy_max_depth = hierarchy.get("max_depth", 0)

    # Check consistency
    if max_depth != hierarchy_max_depth:
        return CheckResult(
            check_id="EC-5",
            name="Deep Nesting",
            category=CheckCategory.EDGE_CASES,
            passed=False,
            score=0.5,
            message=f"Max depth inconsistency: stats={max_depth}, hierarchy={hierarchy_max_depth}",
        )

    # Check depth distribution
    depth_dist = hierarchy.get("depth_distribution", {})

    # Verify directories at each depth
    dir_depths = {}
    for path, dir_obj in directories.items():
        depth = dir_obj.get("depth", 0)
        dir_depths[depth] = dir_depths.get(depth, 0) + 1

    # Check that deeply nested items have correct depth values
    deep_dirs = [
        path for path, dir_obj in directories.items()
        if dir_obj.get("depth", 0) >= 10
    ]

    for path in deep_dirs:
        dir_obj = directories[path]
        expected_depth = path.count("/") if path else 0
        actual_depth = dir_obj.get("depth", 0)

        if expected_depth != actual_depth:
            return CheckResult(
                check_id="EC-5",
                name="Deep Nesting",
                category=CheckCategory.EDGE_CASES,
                passed=False,
                score=0.5,
                message=f"Depth mismatch for deeply nested dir: {path}",
                evidence={"path": path, "expected": expected_depth, "actual": actual_depth},
            )

    return CheckResult(
        check_id="EC-5",
        name="Deep Nesting",
        category=CheckCategory.EDGE_CASES,
        passed=True,
        score=1.0,
        message=f"Max depth {max_depth} handled correctly",
        evidence={"max_depth": max_depth, "deep_dirs": len(deep_dirs)},
    )


@register_check("EC-6")
def check_special_characters(output: Dict[str, Any]) -> CheckResult:
    """EC-6: Spaces and special characters in paths are handled."""
    files = output.get("files", {})
    directories = output.get("directories", {})

    special_chars = [" ", "'", '"', "&", "(", ")", "[", "]", "{", "}", "$", "#", "@", "!"]

    special_files = []
    special_dirs = []

    for path in files.keys():
        for char in special_chars:
            if char in path:
                special_files.append(path)
                break

    for path in directories.keys():
        if path:  # Skip root
            for char in special_chars:
                if char in path:
                    special_dirs.append(path)
                    break

    # Check that special character paths are properly structured
    invalid_special = []

    for path in special_files:
        file_obj = files[path]
        if not file_obj.get("id") or not file_obj.get("parent_directory_id"):
            invalid_special.append(path)

    if invalid_special:
        return CheckResult(
            check_id="EC-6",
            name="Special Characters",
            category=CheckCategory.EDGE_CASES,
            passed=False,
            score=0.5,
            message=f"{len(invalid_special)} paths with special chars have invalid structure",
            evidence={"invalid": invalid_special[:5]},
        )

    return CheckResult(
        check_id="EC-6",
        name="Special Characters",
        category=CheckCategory.EDGE_CASES,
        passed=True,
        score=1.0,
        message=f"{len(special_files)} files, {len(special_dirs)} dirs with special chars handled",
        evidence={"special_files": len(special_files), "special_dirs": len(special_dirs)},
    )
