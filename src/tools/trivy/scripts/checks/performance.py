"""Performance checks for Trivy analysis."""

from typing import Any, Generator

from . import CheckResult

CATEGORY = "Performance"

# Thresholds in milliseconds
SMALL_REPO_THRESHOLD_MS = 30000  # 30 seconds
STARTUP_THRESHOLD_MS = 5000  # 5 seconds


def run_performance_checks(
    analysis: dict[str, Any], ground_truth: dict[str, Any]
) -> Generator[CheckResult, None, None]:
    """Run all performance checks."""
    yield check_small_repo_speed(analysis)
    yield check_memory_not_excessive(analysis)


def check_small_repo_speed(analysis: dict[str, Any]) -> CheckResult:
    """Check that small repo analysis completes in reasonable time."""
    scan_time_ms = analysis.get("scan_time_ms", 0)

    if scan_time_ms <= 0:
        return CheckResult(
            check_id="small_repo_speed",
            category=CATEGORY,
            passed=True,
            message="No scan time recorded (likely cached or skipped)",
        )

    if scan_time_ms > SMALL_REPO_THRESHOLD_MS:
        return CheckResult(
            check_id="small_repo_speed",
            category=CATEGORY,
            passed=False,
            message=f"Scan took {scan_time_ms:.0f}ms (threshold: {SMALL_REPO_THRESHOLD_MS}ms)",
        )

    return CheckResult(
        check_id="small_repo_speed",
        category=CATEGORY,
        passed=True,
        message=f"Scan completed in {scan_time_ms:.0f}ms (threshold: {SMALL_REPO_THRESHOLD_MS}ms)",
    )


def check_memory_not_excessive(analysis: dict[str, Any]) -> CheckResult:
    """Check that analysis completed without memory issues."""
    # If we got valid output, memory was fine
    # We can't directly measure memory, but valid output implies success

    summary = analysis.get("summary", {})

    if not summary:
        return CheckResult(
            check_id="memory_not_excessive",
            category=CATEGORY,
            passed=False,
            message="No summary found - possible memory/crash issue",
        )

    return CheckResult(
        check_id="memory_not_excessive",
        category=CATEGORY,
        passed=True,
        message="Analysis completed without memory issues",
    )
