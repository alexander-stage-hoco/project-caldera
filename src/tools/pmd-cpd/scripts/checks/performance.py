"""
Performance checks (PF-1 to PF-4) for PMD CPD evaluation.

These checks validate performance and resource usage.
"""

from . import (
    CheckResult,
    CheckCategory,
)


def run_performance_checks(analysis: dict, ground_truth_dir: str) -> list[CheckResult]:
    """Run all performance checks."""
    results = []

    results.append(_pf1_execution_time(analysis))
    results.append(_pf2_file_throughput(analysis))
    results.append(_pf3_memory_efficiency(analysis))
    results.append(_pf4_incremental_analysis_potential(analysis))

    return results


def _pf1_execution_time(analysis: dict) -> CheckResult:
    """PF-1: Analysis should complete within reasonable time."""
    metadata = analysis.get("metadata", {})
    elapsed = metadata.get("elapsed_seconds", 0)

    # Thresholds
    excellent_threshold = 30  # < 30s is excellent
    good_threshold = 120  # < 2 min is good
    acceptable_threshold = 300  # < 5 min is acceptable

    if elapsed <= excellent_threshold:
        score = 1.0
        message = f"Excellent: Analysis completed in {elapsed:.1f}s"
    elif elapsed <= good_threshold:
        score = 0.8
        message = f"Good: Analysis completed in {elapsed:.1f}s"
    elif elapsed <= acceptable_threshold:
        score = 0.6
        message = f"Acceptable: Analysis completed in {elapsed:.1f}s"
    else:
        score = 0.3
        message = f"Slow: Analysis took {elapsed:.1f}s"

    passed = elapsed <= acceptable_threshold

    return CheckResult(
        check_id="PF-1",
        name="Execution time",
        category=CheckCategory.PERFORMANCE,
        passed=passed,
        score=score,
        message=message,
        evidence={
            "elapsed_seconds": elapsed,
            "thresholds": {
                "excellent": excellent_threshold,
                "good": good_threshold,
                "acceptable": acceptable_threshold
            }
        }
    )


def _pf2_file_throughput(analysis: dict) -> CheckResult:
    """PF-2: Files per second should be reasonable."""
    metadata = analysis.get("metadata", {})
    summary = analysis.get("summary", {})

    elapsed = metadata.get("elapsed_seconds", 0)
    total_files = summary.get("total_files", 0)

    if elapsed <= 0 or total_files == 0:
        return CheckResult(
            check_id="PF-2",
            name="File throughput",
            category=CheckCategory.PERFORMANCE,
            passed=True,
            score=1.0,
            message="No files to measure throughput",
            evidence={}
        )

    files_per_second = total_files / elapsed

    # Thresholds
    excellent_threshold = 10  # > 10 files/sec is excellent
    good_threshold = 5  # > 5 files/sec is good
    acceptable_threshold = 1  # > 1 file/sec is acceptable

    if files_per_second >= excellent_threshold:
        score = 1.0
        message = f"Excellent: {files_per_second:.1f} files/second"
    elif files_per_second >= good_threshold:
        score = 0.8
        message = f"Good: {files_per_second:.1f} files/second"
    elif files_per_second >= acceptable_threshold:
        score = 0.6
        message = f"Acceptable: {files_per_second:.1f} files/second"
    else:
        score = 0.3
        message = f"Slow: {files_per_second:.2f} files/second"

    passed = files_per_second >= acceptable_threshold

    return CheckResult(
        check_id="PF-2",
        name="File throughput",
        category=CheckCategory.PERFORMANCE,
        passed=passed,
        score=score,
        message=message,
        evidence={
            "total_files": total_files,
            "elapsed_seconds": elapsed,
            "files_per_second": round(files_per_second, 2)
        }
    )


def _pf3_memory_efficiency(analysis: dict) -> CheckResult:
    """PF-3: Memory usage should be reasonable (proxy via output size)."""
    # We use output size as a proxy for memory efficiency
    # Large output with few files suggests inefficient data structures
    duplications = analysis.get("duplications", [])
    files = analysis.get("files", [])

    total_files = len(files)
    total_clones = len(duplications)

    if total_files == 0:
        return CheckResult(
            check_id="PF-3",
            name="Memory efficiency",
            category=CheckCategory.PERFORMANCE,
            passed=True,
            score=1.0,
            message="No files analyzed",
            evidence={}
        )

    # Calculate average occurrences per clone
    total_occurrences = sum(len(d.get("occurrences", [])) for d in duplications)
    avg_occurrences = total_occurrences / total_clones if total_clones > 0 else 0

    # Efficient detection should not have excessive occurrences
    # (indicates proper deduplication)
    if avg_occurrences <= 3:
        score = 1.0
        message = "Efficient clone representation"
    elif avg_occurrences <= 5:
        score = 0.8
        message = "Reasonable clone representation"
    else:
        score = 0.6
        message = f"High occurrence count per clone ({avg_occurrences:.1f})"

    passed = score >= 0.6

    return CheckResult(
        check_id="PF-3",
        name="Memory efficiency",
        category=CheckCategory.PERFORMANCE,
        passed=passed,
        score=score,
        message=message,
        evidence={
            "total_clones": total_clones,
            "total_occurrences": total_occurrences,
            "avg_occurrences_per_clone": round(avg_occurrences, 2)
        }
    )


def _pf4_incremental_analysis_potential(analysis: dict) -> CheckResult:
    """PF-4: Output structure should support incremental analysis."""
    # Check if the output has sufficient metadata for incremental analysis
    metadata = analysis.get("metadata", {})

    has_repo_path = "repo_path" in metadata
    has_timestamp = "analyzed_at" in metadata
    has_version = "version" in metadata

    required_fields = 3
    present_fields = sum([has_repo_path, has_timestamp, has_version])

    score = present_fields / required_fields
    passed = score >= 0.67  # At least 2/3 fields

    evidence = {
        "has_repo_path": has_repo_path,
        "has_timestamp": has_timestamp,
        "has_version": has_version,
    }

    if passed:
        message = "Output supports incremental analysis"
    else:
        missing = []
        if not has_repo_path:
            missing.append("repo_path")
        if not has_timestamp:
            missing.append("timestamp")
        if not has_version:
            missing.append("version")
        message = f"Missing metadata for incremental: {', '.join(missing)}"

    return CheckResult(
        check_id="PF-4",
        name="Incremental analysis support",
        category=CheckCategory.PERFORMANCE,
        passed=passed,
        score=score,
        message=message,
        evidence=evidence
    )
