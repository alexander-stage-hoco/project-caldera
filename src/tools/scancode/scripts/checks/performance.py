"""Performance checks for license analysis (LP-1 to LP-4)."""

from . import CheckResult, check_in_range


def run_performance_checks(
    analysis: dict, ground_truth: dict
) -> list[CheckResult]:
    """Run all performance checks."""
    results = []
    thresholds = ground_truth.get("thresholds", {})

    scan_time_ms = analysis.get("scan_time_ms", 0)

    # LP-1: Scan completed within max time
    max_time_ms = thresholds.get("max_scan_time_ms", 5000)
    results.append(
        check_in_range(
            "LP-1",
            "Performance",
            "Scan time within limit",
            scan_time_ms,
            0,
            max_time_ms,
        )
    )

    # LP-2: Scan time is positive (actually ran)
    results.append(
        CheckResult(
            check_id="LP-2",
            category="Performance",
            passed=scan_time_ms > 0,
            message=f"Scan time positive: {scan_time_ms}ms > 0",
            expected="> 0ms",
            actual=f"{scan_time_ms}ms",
        )
    )

    # LP-3: Files per second reasonable (> 1 file/sec)
    total_files = analysis.get("total_files_scanned", 0)
    if scan_time_ms > 0 and total_files > 0:
        files_per_sec = total_files / (scan_time_ms / 1000)
        min_files_per_sec = thresholds.get("min_files_per_second", 1)
        results.append(
            CheckResult(
                check_id="LP-3",
                category="Performance",
                passed=files_per_sec >= min_files_per_sec,
                message=f"Processing rate: {files_per_sec:.1f} files/sec >= {min_files_per_sec}",
                expected=f">= {min_files_per_sec} files/sec",
                actual=f"{files_per_sec:.1f} files/sec",
            )
        )
    else:
        results.append(
            CheckResult(
                check_id="LP-3",
                category="Performance",
                passed=True,
                message="Processing rate: N/A (no files or zero time)",
                expected="N/A",
                actual="N/A",
            )
        )

    # LP-4: Analysis completed (validates scan finished successfully)
    results.append(
        CheckResult(
            check_id="LP-4",
            category="Performance",
            passed=scan_time_ms > 0,
            message=f"Analysis completed: scan_time_ms={scan_time_ms}",
            expected="scan_time_ms > 0",
            actual=f"scan_time_ms={scan_time_ms}",
        )
    )

    return results
