from __future__ import annotations
"""
Performance checks (PF-1 to PF-4) for Roslyn Analyzers evaluation.

These checks verify analysis performance characteristics.
"""

from . import CheckResult


def pf1_synthetic_analysis_speed(analysis: dict, ground_truth: dict) -> CheckResult:
    """PF-1: Synthetic analysis speed (<30 seconds for synthetic repo)."""
    metadata = analysis.get("metadata", {})
    duration_ms = metadata.get("analysis_duration_ms", 0)
    duration_seconds = duration_ms / 1000

    threshold_seconds = 30
    passed = duration_seconds < threshold_seconds
    score = max(0, 1.0 - (duration_seconds / threshold_seconds)) if duration_seconds < threshold_seconds else 0

    return CheckResult(
        check_id="PF-1",
        name="Synthetic Analysis Speed",
        category="performance",
        passed=passed,
        score=score,
        threshold=threshold_seconds * 1000,  # in ms
        actual_value=duration_ms,
        message=f"Analysis completed in {duration_seconds:.2f} seconds {'<' if passed else '>='} {threshold_seconds}s threshold",
        evidence={
            "duration_ms": duration_ms,
            "duration_seconds": duration_seconds,
            "threshold_seconds": threshold_seconds,
        }
    )


def pf2_per_file_efficiency(analysis: dict, ground_truth: dict) -> CheckResult:
    """PF-2: Per-file efficiency (<2000ms per file average)."""
    metadata = analysis.get("metadata", {})
    duration_ms = metadata.get("analysis_duration_ms", 0)
    files_analyzed = len(analysis.get("files", []))

    if files_analyzed == 0:
        return CheckResult(
            check_id="PF-2",
            name="Per-File Efficiency",
            category="performance",
            passed=False,
            score=0.0,
            threshold=2000,
            actual_value=0,
            message="No files analyzed",
            evidence={"files_analyzed": 0}
        )

    ms_per_file = duration_ms / files_analyzed
    threshold_ms = 2000
    passed = ms_per_file < threshold_ms
    score = max(0, 1.0 - (ms_per_file / threshold_ms)) if ms_per_file < threshold_ms else 0

    return CheckResult(
        check_id="PF-2",
        name="Per-File Efficiency",
        category="performance",
        passed=passed,
        score=score,
        threshold=threshold_ms,
        actual_value=ms_per_file,
        message=f"{ms_per_file:.0f}ms per file average {'<' if passed else '>='} {threshold_ms}ms threshold",
        evidence={
            "duration_ms": duration_ms,
            "files_analyzed": files_analyzed,
            "ms_per_file": ms_per_file,
            "threshold_ms": threshold_ms,
        }
    )


def pf3_throughput(analysis: dict, ground_truth: dict) -> CheckResult:
    """PF-3: Throughput (>=50 LOC/second)."""
    metadata = analysis.get("metadata", {})
    duration_ms = metadata.get("analysis_duration_ms", 0)
    duration_seconds = duration_ms / 1000

    if duration_seconds == 0:
        return CheckResult(
            check_id="PF-3",
            name="Throughput",
            category="performance",
            passed=True,
            score=1.0,
            threshold=50,
            actual_value=float("inf"),
            message="Instant analysis",
            evidence={"duration_seconds": 0}
        )

    # Calculate total LOC
    files_data = analysis.get("files", [])
    total_loc = sum(f.get("lines_of_code", 0) for f in files_data)

    loc_per_second = total_loc / duration_seconds
    threshold_loc = 50
    passed = loc_per_second >= threshold_loc
    score = min(1.0, loc_per_second / threshold_loc)

    return CheckResult(
        check_id="PF-3",
        name="Throughput",
        category="performance",
        passed=passed,
        score=score,
        threshold=threshold_loc,
        actual_value=loc_per_second,
        message=f"{loc_per_second:.0f} LOC/second {'>=' if passed else '<'} {threshold_loc} threshold",
        evidence={
            "total_loc": total_loc,
            "duration_seconds": duration_seconds,
            "loc_per_second": loc_per_second,
            "threshold_loc": threshold_loc,
        }
    )


def pf4_memory_usage(analysis: dict, ground_truth: dict) -> CheckResult:
    """PF-4: Memory usage (<500MB peak for synthetic repo)."""
    # Memory usage is harder to measure without instrumenting the process
    # For this PoC, we assume pass if analysis completed successfully
    # In a real evaluation, we'd use memory profiling

    metadata = analysis.get("metadata", {})
    completed = "timestamp" in metadata

    # Estimate memory as reasonable if analysis completed
    # This is a placeholder - real implementation would measure actual memory
    estimated_memory_mb = 200  # Conservative estimate for small project

    threshold_mb = 500
    passed = completed and estimated_memory_mb < threshold_mb
    score = 1.0 if passed else 0.0

    return CheckResult(
        check_id="PF-4",
        name="Memory Usage",
        category="performance",
        passed=passed,
        score=score,
        threshold=threshold_mb,
        actual_value=estimated_memory_mb,
        message=f"Estimated ~{estimated_memory_mb}MB (< {threshold_mb}MB threshold)",
        evidence={
            "estimated_memory_mb": estimated_memory_mb,
            "threshold_mb": threshold_mb,
            "note": "Memory not directly measured; estimate based on completion",
        }
    )


def run_all_performance_checks(analysis: dict, ground_truth: dict) -> list[CheckResult]:
    """Run all performance checks and return results."""
    return [
        pf1_synthetic_analysis_speed(analysis, ground_truth),
        pf2_per_file_efficiency(analysis, ground_truth),
        pf3_throughput(analysis, ground_truth),
        pf4_memory_usage(analysis, ground_truth),
    ]
