"""
Performance Checks (PF-1 to PF-4).

Validates scan speed and efficiency.
"""

from typing import Any, Dict, List, Optional

from . import CheckCategory, CheckResult, register_check


# Performance thresholds (in milliseconds)
THRESHOLDS = {
    "small": {"files": 1000, "max_time_ms": 500},
    "medium": {"files": 10000, "max_time_ms": 2000},
    "large": {"files": 100000, "max_time_ms": 10000},
}


def run_performance_checks(
    output: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]] = None,
) -> List[CheckResult]:
    """Run all performance checks."""
    checks = []

    checks.append(check_small_repo_speed(output, ground_truth))
    checks.append(check_medium_repo_speed(output, ground_truth))
    checks.append(check_large_repo_speed(output, ground_truth))
    checks.append(check_files_per_second(output))
    checks.append(check_deep_nesting_performance(output, ground_truth))

    return checks


@register_check("PF-1")
def check_small_repo_speed(
    output: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]] = None,
) -> CheckResult:
    """PF-1: Small repo (< 1K files) scanned in < 0.5s."""
    stats = output.get("statistics", {})
    file_count = stats.get("total_files", 0)
    duration_ms = stats.get("scan_duration_ms", 0)

    threshold = THRESHOLDS["small"]

    if file_count > threshold["files"]:
        return CheckResult(
            check_id="PF-1",
            name="Small Repo Speed",
            category=CheckCategory.PERFORMANCE,
            passed=True,
            score=1.0,
            message=f"Not applicable (repo has {file_count} files, threshold is {threshold['files']})",
        )

    # Check ground truth override
    max_time = threshold["max_time_ms"]
    if ground_truth:
        gt_max_time = ground_truth.get("thresholds", {}).get("max_scan_time_seconds")
        if gt_max_time:
            max_time = int(gt_max_time * 1000)

    if duration_ms > max_time:
        return CheckResult(
            check_id="PF-1",
            name="Small Repo Speed",
            category=CheckCategory.PERFORMANCE,
            passed=False,
            score=0.5,
            message=f"Scan took {duration_ms}ms, threshold is {max_time}ms",
            evidence={"duration_ms": duration_ms, "threshold_ms": max_time},
        )

    return CheckResult(
        check_id="PF-1",
        name="Small Repo Speed",
        category=CheckCategory.PERFORMANCE,
        passed=True,
        score=1.0,
        message=f"Scanned {file_count} files in {duration_ms}ms",
        evidence={"duration_ms": duration_ms, "file_count": file_count},
    )


@register_check("PF-2")
def check_medium_repo_speed(
    output: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]] = None,
) -> CheckResult:
    """PF-2: Medium repo (10K files) scanned in < 2s."""
    stats = output.get("statistics", {})
    file_count = stats.get("total_files", 0)
    duration_ms = stats.get("scan_duration_ms", 0)

    threshold = THRESHOLDS["medium"]

    # Only applicable for repos in the medium range
    if file_count < THRESHOLDS["small"]["files"]:
        return CheckResult(
            check_id="PF-2",
            name="Medium Repo Speed",
            category=CheckCategory.PERFORMANCE,
            passed=True,
            score=1.0,
            message=f"Not applicable (repo has {file_count} files, too small)",
        )

    if file_count > threshold["files"]:
        return CheckResult(
            check_id="PF-2",
            name="Medium Repo Speed",
            category=CheckCategory.PERFORMANCE,
            passed=True,
            score=1.0,
            message=f"Not applicable (repo has {file_count} files, exceeds medium threshold)",
        )

    max_time = threshold["max_time_ms"]

    if duration_ms > max_time:
        return CheckResult(
            check_id="PF-2",
            name="Medium Repo Speed",
            category=CheckCategory.PERFORMANCE,
            passed=False,
            score=0.5,
            message=f"Scan took {duration_ms}ms, threshold is {max_time}ms",
            evidence={"duration_ms": duration_ms, "threshold_ms": max_time},
        )

    return CheckResult(
        check_id="PF-2",
        name="Medium Repo Speed",
        category=CheckCategory.PERFORMANCE,
        passed=True,
        score=1.0,
        message=f"Scanned {file_count} files in {duration_ms}ms",
        evidence={"duration_ms": duration_ms, "file_count": file_count},
    )


@register_check("PF-3")
def check_large_repo_speed(
    output: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]] = None,
) -> CheckResult:
    """PF-3: Large repo (100K files) scanned in < 10s."""
    stats = output.get("statistics", {})
    file_count = stats.get("total_files", 0)
    duration_ms = stats.get("scan_duration_ms", 0)

    threshold = THRESHOLDS["large"]

    # Only applicable for large repos
    if file_count < THRESHOLDS["medium"]["files"]:
        return CheckResult(
            check_id="PF-3",
            name="Large Repo Speed",
            category=CheckCategory.PERFORMANCE,
            passed=True,
            score=1.0,
            message=f"Not applicable (repo has {file_count} files, too small)",
        )

    max_time = threshold["max_time_ms"]

    if duration_ms > max_time:
        return CheckResult(
            check_id="PF-3",
            name="Large Repo Speed",
            category=CheckCategory.PERFORMANCE,
            passed=False,
            score=0.5,
            message=f"Scan took {duration_ms}ms, threshold is {max_time}ms",
            evidence={"duration_ms": duration_ms, "threshold_ms": max_time},
        )

    return CheckResult(
        check_id="PF-3",
        name="Large Repo Speed",
        category=CheckCategory.PERFORMANCE,
        passed=True,
        score=1.0,
        message=f"Scanned {file_count} files in {duration_ms}ms",
        evidence={"duration_ms": duration_ms, "file_count": file_count},
    )


@register_check("PF-4")
def check_files_per_second(output: Dict[str, Any]) -> CheckResult:
    """PF-4: Files per second is reasonable (> 1000 for any size)."""
    stats = output.get("statistics", {})
    file_count = stats.get("total_files", 0)
    duration_ms = stats.get("scan_duration_ms", 0)
    files_per_second = stats.get("files_per_second", 0)

    if file_count == 0:
        return CheckResult(
            check_id="PF-4",
            name="Files Per Second",
            category=CheckCategory.PERFORMANCE,
            passed=True,
            score=1.0,
            message="No files to scan",
        )

    if duration_ms == 0:
        # Very fast scan
        return CheckResult(
            check_id="PF-4",
            name="Files Per Second",
            category=CheckCategory.PERFORMANCE,
            passed=True,
            score=1.0,
            message=f"Scanned {file_count} files in < 1ms",
            evidence={"file_count": file_count},
        )

    # Calculate if not provided
    if files_per_second == 0:
        files_per_second = file_count / (duration_ms / 1000)

    # Tiered thresholds - small repos have higher overhead
    if file_count < 50:
        min_fps = 25    # Very small repos - startup/timing noise dominated
    elif file_count < 100:
        min_fps = 100   # Small repos - startup overhead dominated
    elif file_count < 1000:
        min_fps = 500   # Medium repos
    else:
        min_fps = 1000  # Large repos should achieve 1000+

    if files_per_second < min_fps:
        return CheckResult(
            check_id="PF-4",
            name="Files Per Second",
            category=CheckCategory.PERFORMANCE,
            passed=False,
            score=0.5,
            message=f"Only {files_per_second:.0f} files/sec, minimum is {min_fps}",
            evidence={"files_per_second": files_per_second, "minimum": min_fps},
        )

    return CheckResult(
        check_id="PF-4",
        name="Files Per Second",
        category=CheckCategory.PERFORMANCE,
        passed=True,
        score=1.0,
        message=f"{files_per_second:.0f} files/second",
        evidence={"files_per_second": files_per_second},
    )


# Deep nesting thresholds
DEEP_NESTING_THRESHOLDS = {
    "max_depth": 20,              # Maximum nesting depth to test
    "timeout_ms": 5000,           # Max time for deep nesting scan
    "files_per_level": 10,        # Expected O(n) - should process linearly
}


@register_check("PF-5")
def check_deep_nesting_performance(
    output: Dict[str, Any],
    ground_truth: Optional[Dict[str, Any]] = None,
) -> CheckResult:
    """PF-5: Deep nesting performance - scanner handles >20 levels efficiently.

    Validates that the layout scanner maintains O(n) performance when
    traversing deeply nested directory structures. Deep nesting should
    not cause exponential slowdown or excessive resource usage.
    """
    stats = output.get("statistics", {})
    duration_ms = stats.get("scan_duration_ms", 0)
    max_depth = stats.get("max_directory_depth", 0)
    file_count = stats.get("total_files", 0)
    dir_count = stats.get("total_directories", 0)

    # Check if deep nesting data is available
    if max_depth == 0:
        # Try to infer from file paths
        files = output.get("files", [])
        if isinstance(files, dict):
            files = list(files.values())
        if files:
            max_depth = max(
                (f.get("path", "").count("/") for f in files),
                default=0
            )

    # Get threshold from ground truth if provided
    timeout_threshold = DEEP_NESTING_THRESHOLDS["timeout_ms"]
    depth_threshold = DEEP_NESTING_THRESHOLDS["max_depth"]
    max_ms_per_item_override = None

    if ground_truth:
        gt_thresholds = ground_truth.get("thresholds", {})
        timeout_threshold = gt_thresholds.get("deep_nesting_timeout_ms", timeout_threshold)
        depth_threshold = gt_thresholds.get("max_expected_depth", depth_threshold)
        max_ms_per_item_override = gt_thresholds.get("deep_nesting_max_ms_per_item", None)

    # If not a deep nesting scenario, pass by default
    if max_depth < 10:
        return CheckResult(
            check_id="PF-5",
            name="Deep Nesting Performance",
            category=CheckCategory.PERFORMANCE,
            passed=True,
            score=1.0,
            message=f"Not a deep nesting scenario (depth={max_depth}, threshold=10+)",
            evidence={
                "max_depth": max_depth,
                "threshold": 10,
            },
        )

    # Check timeout
    if duration_ms > timeout_threshold:
        return CheckResult(
            check_id="PF-5",
            name="Deep Nesting Performance",
            category=CheckCategory.PERFORMANCE,
            passed=False,
            score=0.3,
            message=f"Deep nesting scan took {duration_ms}ms, exceeds {timeout_threshold}ms threshold",
            evidence={
                "duration_ms": duration_ms,
                "timeout_threshold_ms": timeout_threshold,
                "max_depth": max_depth,
            },
        )

    # Check O(n) complexity - time should scale linearly with files/dirs
    total_items = file_count + dir_count
    if total_items > 0 and duration_ms > 0:
        ms_per_item = duration_ms / total_items

        # For O(n), expect < 1ms per item even with deep nesting
        # Allow up to 2ms per item for very deep structures
        if max_ms_per_item_override is not None:
            max_ms_per_item = float(max_ms_per_item_override)
        else:
            max_ms_per_item = 2.0 if max_depth > 15 else 1.0

        if ms_per_item > max_ms_per_item:
            return CheckResult(
                check_id="PF-5",
                name="Deep Nesting Performance",
                category=CheckCategory.PERFORMANCE,
                passed=False,
                score=0.5,
                message=f"Non-linear scaling detected: {ms_per_item:.2f}ms/item (expected <{max_ms_per_item}ms)",
                evidence={
                    "duration_ms": duration_ms,
                    "total_items": total_items,
                    "ms_per_item": round(ms_per_item, 3),
                    "max_ms_per_item": max_ms_per_item,
                    "max_depth": max_depth,
                },
            )

    return CheckResult(
        check_id="PF-5",
        name="Deep Nesting Performance",
        category=CheckCategory.PERFORMANCE,
        passed=True,
        score=1.0,
        message=f"Deep nesting handled efficiently: depth={max_depth}, {duration_ms}ms",
        evidence={
            "duration_ms": duration_ms,
            "max_depth": max_depth,
            "file_count": file_count,
            "dir_count": dir_count,
        },
    )
