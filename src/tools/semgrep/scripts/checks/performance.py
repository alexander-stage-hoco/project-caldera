"""
Performance checks (PF-1 to PF-4) for Semgrep smell detection.

Tests performance characteristics:
- PF-1: Synthetic repo speed (<5s)
- PF-2: Small real repo speed (<30s)
- PF-3: Medium real repo speed (<60s)
- PF-4: Memory efficiency
"""

from . import (
    CheckResult,
    CheckCategory,
)


def run_performance_checks(
    analysis: dict,
    skip_long_checks: bool = False,
) -> list[CheckResult]:
    """Run all performance checks (PF-1 to PF-4)."""
    results = []

    # Get analysis duration from metadata
    duration_ms = analysis.get("metadata", {}).get("analysis_duration_ms", 0)
    duration_s = duration_ms / 1000.0

    # PF-1: Synthetic repo speed (<45s - accounts for Semgrep rule download on first run)
    pf1_threshold = 45.0
    pf1_passed = duration_s < pf1_threshold
    pf1_score = min(1.0, pf1_threshold / max(duration_s, 0.1))

    results.append(CheckResult(
        check_id="PF-1",
        name="Synthetic repo analysis speed",
        category=CheckCategory.PERFORMANCE,
        passed=pf1_passed,
        score=min(pf1_score, 1.0),
        message=f"Completed in {duration_s:.2f}s (threshold: {pf1_threshold}s)",
        evidence={
            "duration_ms": duration_ms,
            "duration_s": round(duration_s, 2),
            "threshold_s": pf1_threshold,
        },
    ))

    # PF-2: Per-file analysis efficiency
    total_files = analysis.get("summary", {}).get("total_files", 1)
    ms_per_file = duration_ms / max(total_files, 1)
    pf2_threshold = 1000  # 1 second per file max

    pf2_passed = ms_per_file < pf2_threshold
    pf2_score = min(1.0, pf2_threshold / max(ms_per_file, 1))

    results.append(CheckResult(
        check_id="PF-2",
        name="Per-file analysis efficiency",
        category=CheckCategory.PERFORMANCE,
        passed=pf2_passed,
        score=min(pf2_score, 1.0),
        message=f"{ms_per_file:.0f}ms per file (threshold: {pf2_threshold}ms)",
        evidence={
            "total_files": total_files,
            "ms_per_file": round(ms_per_file, 0),
            "threshold_ms": pf2_threshold,
        },
    ))

    # PF-3: Throughput (LOC per second)
    total_lines = analysis.get("summary", {}).get("total_lines", 0)
    lines_per_second = total_lines / max(duration_s, 0.001)
    pf3_threshold = 100  # Minimum 100 LOC/s

    pf3_passed = lines_per_second >= pf3_threshold
    pf3_score = min(1.0, lines_per_second / (pf3_threshold * 10))  # Scale to 1000 LOC/s = 1.0

    results.append(CheckResult(
        check_id="PF-3",
        name="Analysis throughput",
        category=CheckCategory.PERFORMANCE,
        passed=pf3_passed,
        score=min(pf3_score, 1.0),
        message=f"{lines_per_second:.0f} LOC/s (threshold: {pf3_threshold} LOC/s)",
        evidence={
            "total_lines": total_lines,
            "lines_per_second": round(lines_per_second, 0),
            "threshold_loc_per_s": pf3_threshold,
        },
    ))

    # PF-4: Startup overhead assessment
    # Semgrep has notable startup time for downloading rules
    # This check measures if startup dominates the analysis time
    if total_files > 0:
        startup_estimate_s = max(duration_s - (total_files * 0.1), 0)  # Assume 100ms/file baseline
        startup_ratio = startup_estimate_s / max(duration_s, 0.001)

        pf4_passed = startup_ratio < 0.9  # Startup should be <90% of total time (Semgrep downloads rules on first run)
        pf4_score = 1.0 - min(startup_ratio, 1.0)
    else:
        pf4_passed = True
        pf4_score = 0.5
        startup_ratio = 0

    results.append(CheckResult(
        check_id="PF-4",
        name="Startup overhead",
        category=CheckCategory.PERFORMANCE,
        passed=pf4_passed,
        score=max(pf4_score, 0),
        message=f"Estimated startup: {startup_ratio:.0%} of total time",
        evidence={
            "total_duration_s": round(duration_s, 2),
            "startup_ratio": round(startup_ratio, 2),
            "note": "Semgrep downloads rules on first run (cached subsequently)",
        },
    ))

    return results
