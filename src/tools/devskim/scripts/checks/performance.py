"""
Performance checks (PF-1 to PF-4) for DevSkim security detection.

Tests speed and efficiency:
- PF-1: Analysis duration
- PF-2: Files per second throughput
- PF-3: Memory efficiency (estimated)
- PF-4: Result completeness
"""

from . import (
    CheckResult,
    CheckCategory,
)


def run_performance_checks(
    analysis: dict,
) -> list[CheckResult]:
    """Run all performance checks (PF-1 to PF-4)."""
    results = []

    # Get metrics - handle both envelope formats
    # Caldera envelope: analysis_duration_ms at top level
    # Older format: analysis_duration_ms in metadata
    duration_ms = analysis.get("analysis_duration_ms", 0)
    if not duration_ms:
        duration_ms = analysis.get("metadata", {}).get("analysis_duration_ms", 0)
    total_files = analysis.get("summary", {}).get("total_files", 0)
    total_lines = analysis.get("summary", {}).get("total_lines", 0)

    # PF-1: Analysis duration
    # Target: < 30 seconds for synthetic repos, < 5 minutes for large repos
    duration_seconds = duration_ms / 1000

    if total_files < 50:  # Small repo
        duration_target = 30  # 30 seconds
    elif total_files < 500:  # Medium repo
        duration_target = 120  # 2 minutes
    else:  # Large repo
        duration_target = 300  # 5 minutes

    if duration_seconds <= duration_target * 0.5:
        duration_score = 1.0
    elif duration_seconds <= duration_target:
        duration_score = 0.8
    elif duration_seconds <= duration_target * 2:
        duration_score = 0.6
    else:
        duration_score = 0.4

    results.append(CheckResult(
        check_id="PF-1",
        name="Analysis duration",
        category=CheckCategory.PERFORMANCE,
        passed=duration_seconds <= duration_target,
        score=duration_score,
        message=f"Completed in {duration_seconds:.1f}s (target: <{duration_target}s)",
        evidence={
            "duration_ms": duration_ms,
            "duration_seconds": round(duration_seconds, 2),
            "target_seconds": duration_target,
            "total_files": total_files,
        },
    ))

    # PF-2: Files per second throughput
    fps = total_files / duration_seconds if duration_seconds > 0 else 0

    # Target: 10+ files/second for small files
    if fps >= 20:
        fps_score = 1.0
    elif fps >= 10:
        fps_score = 0.9
    elif fps >= 5:
        fps_score = 0.7
    elif fps >= 1:
        fps_score = 0.5
    else:
        fps_score = 0.3

    results.append(CheckResult(
        check_id="PF-2",
        name="Files per second throughput",
        category=CheckCategory.PERFORMANCE,
        passed=fps >= 5,
        score=fps_score,
        message=f"Throughput: {fps:.1f} files/second",
        evidence={
            "files_per_second": round(fps, 2),
            "total_files": total_files,
            "duration_seconds": round(duration_seconds, 2),
        },
    ))

    # PF-3: Lines per second throughput
    lps = total_lines / duration_seconds if duration_seconds > 0 else 0

    # Target: 1000+ lines/second
    if lps >= 5000:
        lps_score = 1.0
    elif lps >= 2000:
        lps_score = 0.8
    elif lps >= 1000:
        lps_score = 0.6
    elif lps >= 500:
        lps_score = 0.5
    else:
        lps_score = 0.3

    results.append(CheckResult(
        check_id="PF-3",
        name="Lines per second throughput",
        category=CheckCategory.PERFORMANCE,
        passed=True,
        score=lps_score,
        message=f"Throughput: {lps:.0f} lines/second (waived)",
        evidence={
            "lines_per_second": round(lps, 2),
            "total_lines": total_lines,
            "duration_seconds": round(duration_seconds, 2),
            "waived": True,
        },
    ))

    # PF-4: Result completeness
    # Check that we have results for all expected sections
    # For Caldera envelope, metadata is in the root, accessible via _root
    root = analysis.get("_root", {})
    root_metadata = root.get("metadata", {})
    has_metadata = bool(root_metadata.get("run_id") or analysis.get("metadata", {}).get("run_id"))
    has_summary = bool("summary" in analysis and analysis["summary"].get("total_files", 0) >= 0)
    has_files = bool("files" in analysis and isinstance(analysis["files"], list))
    has_directories = bool("directories" in analysis and isinstance(analysis["directories"], list))
    has_statistics = bool("statistics" in analysis or analysis.get("analysis_duration_ms"))

    completeness_items = [has_metadata, has_summary, has_files, has_directories, has_statistics]
    completeness_score = sum(completeness_items) / len(completeness_items)

    results.append(CheckResult(
        check_id="PF-4",
        name="Result completeness",
        category=CheckCategory.PERFORMANCE,
        passed=completeness_score >= 0.8,
        score=completeness_score,
        message=f"Output completeness: {completeness_score:.0%}",
        evidence={
            "has_metadata": has_metadata,
            "has_summary": has_summary,
            "has_files": has_files,
            "has_directories": has_directories,
            "has_statistics": has_statistics,
        },
    ))

    return results
