"""Performance checks (SQ-PF-*) for SonarQube evaluation."""

import json
from datetime import datetime

from . import (
    CheckCategory,
    CheckResult,
)


def check_analysis_timing(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-PF-1: Check that execution completed within expected time."""
    # Check inner data metadata first
    inner_data = data.get("data", data)
    metadata = inner_data.get("metadata", {})

    duration_ms = metadata.get("duration_ms")
    start_time = metadata.get("start_time")
    end_time = metadata.get("end_time")

    if duration_ms is None and start_time and end_time:
        try:
            start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            duration_ms = (end - start).total_seconds() * 1000
        except (ValueError, TypeError):
            duration_ms = None

    if duration_ms is None:
        return CheckResult(
            check_id="SQ-PF-1",
            name="Analysis timing",
            category=CheckCategory.PERFORMANCE,
            passed=True,
            score=0.5,
            message="No timing information available",
            evidence={"skipped": True},
        )

    max_duration_ms = 300000  # 5 minutes default
    if ground_truth:
        max_duration_ms = ground_truth.get("max_duration_ms", max_duration_ms)

    passed = duration_ms <= max_duration_ms
    score = min(max_duration_ms / duration_ms, 1.0) if duration_ms > 0 else 1.0

    return CheckResult(
        check_id="SQ-PF-1",
        name="Analysis timing",
        category=CheckCategory.PERFORMANCE,
        passed=passed,
        score=score,
        message=f"Analysis completed in {duration_ms:.0f}ms "
                f"({'within' if passed else 'exceeds'} limit: {max_duration_ms}ms)",
        evidence={"duration_ms": round(duration_ms, 2), "limit_ms": max_duration_ms},
    )


def check_output_size(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-PF-2: Check that JSON output size is reasonable."""
    try:
        serialized = json.dumps(data)
        size_bytes = len(serialized.encode("utf-8"))
        size_mb = size_bytes / (1024 * 1024)
    except (TypeError, ValueError) as e:
        return CheckResult(
            check_id="SQ-PF-2",
            name="Output size",
            category=CheckCategory.PERFORMANCE,
            passed=False,
            score=0.0,
            message=f"Failed to serialize output: {e}",
            evidence={"error": str(e)},
        )

    max_size_mb = 50.0  # 50MB default
    if ground_truth:
        max_size_mb = ground_truth.get("max_output_size_mb", max_size_mb)

    passed = size_mb <= max_size_mb
    score = min(max_size_mb / size_mb, 1.0) if size_mb > 0 else 1.0

    return CheckResult(
        check_id="SQ-PF-2",
        name="Output size",
        category=CheckCategory.PERFORMANCE,
        passed=passed,
        score=score,
        message=f"Output size {size_mb:.2f}MB "
                f"{'within' if passed else 'exceeds'} limit ({max_size_mb}MB)",
        evidence={"size_mb": round(size_mb, 2), "limit_mb": max_size_mb},
    )


def check_memory_footprint(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-PF-3: Check that analysis didn't exceed memory limits."""
    inner_data = data.get("data", data)
    metadata = inner_data.get("metadata", {})

    peak_memory_mb = metadata.get("peak_memory_mb")

    if peak_memory_mb is None:
        return CheckResult(
            check_id="SQ-PF-3",
            name="Memory footprint",
            category=CheckCategory.PERFORMANCE,
            passed=True,
            score=0.5,
            message="No memory usage information available",
            evidence={"skipped": True},
        )

    max_memory_mb = 2048  # 2GB default
    if ground_truth:
        max_memory_mb = ground_truth.get("max_memory_mb", max_memory_mb)

    passed = peak_memory_mb <= max_memory_mb
    score = min(max_memory_mb / peak_memory_mb, 1.0) if peak_memory_mb > 0 else 1.0

    return CheckResult(
        check_id="SQ-PF-3",
        name="Memory footprint",
        category=CheckCategory.PERFORMANCE,
        passed=passed,
        score=score,
        message=f"Peak memory {peak_memory_mb:.0f}MB "
                f"{'within' if passed else 'exceeds'} limit ({max_memory_mb}MB)",
        evidence={"peak_memory_mb": round(peak_memory_mb, 2), "limit_mb": max_memory_mb},
    )


def check_api_response_time(data: dict, ground_truth: dict | None) -> CheckResult:
    """SQ-PF-4: Check that data extraction was efficient."""
    inner_data = data.get("data", data)
    metadata = inner_data.get("metadata", {})

    api_calls = metadata.get("api_calls", [])
    total_api_time_ms = metadata.get("total_api_time_ms")

    if total_api_time_ms is None and api_calls:
        total_api_time_ms = sum(call.get("duration_ms", 0) for call in api_calls)

    if total_api_time_ms is None:
        results = inner_data.get("results", inner_data)
        components_count = len(results.get("components", {}).get("by_key", {}))
        issues_count = len(results.get("issues", {}).get("items", []))

        if components_count == 0 and issues_count == 0:
            return CheckResult(
                check_id="SQ-PF-4",
                name="API response time",
                category=CheckCategory.PERFORMANCE,
                passed=True,
                score=0.5,
                message="No API timing information available",
                evidence={"skipped": True},
            )

        return CheckResult(
            check_id="SQ-PF-4",
            name="API response time",
            category=CheckCategory.PERFORMANCE,
            passed=True,
            score=1.0,
            message=f"API data extraction successful ({components_count} components, {issues_count} issues)",
            evidence={"components": components_count, "issues": issues_count},
        )

    max_api_time_ms = 60000  # 60 seconds default
    if ground_truth:
        max_api_time_ms = ground_truth.get("max_api_time_ms", max_api_time_ms)

    passed = total_api_time_ms <= max_api_time_ms
    score = min(max_api_time_ms / total_api_time_ms, 1.0) if total_api_time_ms > 0 else 1.0

    return CheckResult(
        check_id="SQ-PF-4",
        name="API response time",
        category=CheckCategory.PERFORMANCE,
        passed=passed,
        score=score,
        message=f"API calls completed in {total_api_time_ms:.0f}ms "
                f"({'within' if passed else 'exceeds'} limit: {max_api_time_ms}ms)",
        evidence={"total_api_time_ms": round(total_api_time_ms, 2), "limit_ms": max_api_time_ms},
    )


def run_performance_checks(data: dict, ground_truth: dict | None, skip: bool = False) -> list[CheckResult]:
    """Run all performance checks and return results.

    Args:
        data: Analysis data
        ground_truth: Ground truth data
        skip: If True, skip performance checks (for quick evaluation)
    """
    if skip:
        return []

    return [
        check_analysis_timing(data, ground_truth),
        check_output_size(data, ground_truth),
        check_memory_footprint(data, ground_truth),
        check_api_response_time(data, ground_truth),
    ]
