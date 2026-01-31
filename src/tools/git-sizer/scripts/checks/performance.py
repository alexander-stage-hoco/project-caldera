"""
Performance checks (PF-1 to PF-4) for git-sizer repository analysis.

Tests performance characteristics:
- PF-1: Synthetic repo analysis speed (<5s total)
- PF-2: Per-repo analysis speed (<2s per repo)
- PF-3: Large repo handling (<30s for 500+ commits)
- PF-4: Memory efficiency (raw output size reasonable)
"""

from . import (
    CheckResult,
    CheckCategory,
    get_repo_by_name,
)


def run_performance_checks(
    analysis: dict,
    skip_long_checks: bool = False,
) -> list[CheckResult]:
    """Run all performance checks (PF-1 to PF-4)."""
    results = []
    repos = analysis.get("repositories", [])
    summary = analysis.get("summary", {})

    # Calculate total duration from all repos
    total_duration = sum(repo.get("duration_ms", 0) for repo in repos)

    # PF-1: Total analysis speed (<5s for synthetic repos)
    pf1_threshold = 5000  # 5 seconds
    pf1_passed = total_duration < pf1_threshold
    pf1_score = min(1.0, pf1_threshold / max(total_duration, 1))

    results.append(CheckResult(
        check_id="PF-1",
        name="Total analysis speed",
        category=CheckCategory.PERFORMANCE,
        passed=pf1_passed,
        score=pf1_score,
        message=f"Total duration: {total_duration}ms (threshold: {pf1_threshold}ms)",
        evidence={"duration_ms": total_duration, "threshold_ms": pf1_threshold},
    ))

    # PF-2: Per-repo analysis speed (<2s per repo)
    pf2_threshold = 2000  # 2 seconds
    slow_repos = []
    fast_repos = 0

    for repo in repos:
        duration = repo.get("duration_ms", 0)
        if duration < pf2_threshold:
            fast_repos += 1
        else:
            slow_repos.append(repo.get("repository", "unknown"))

    pf2_score = fast_repos / len(repos) if repos else 0.0
    pf2_passed = pf2_score >= 0.75

    results.append(CheckResult(
        check_id="PF-2",
        name="Per-repo analysis speed",
        category=CheckCategory.PERFORMANCE,
        passed=pf2_passed,
        score=pf2_score,
        message=f"{fast_repos}/{len(repos)} repos under {pf2_threshold}ms",
        evidence={"fast_repos": fast_repos, "slow_repos": slow_repos, "threshold_ms": pf2_threshold},
    ))

    # PF-3: Large repo handling (deep-history with 500+ commits)
    deep_history = get_repo_by_name(analysis, "deep-history")
    pf3_threshold = 30000  # 30 seconds for large repo

    if deep_history:
        duration = deep_history.get("duration_ms", 0)
        pf3_passed = duration < pf3_threshold
        pf3_score = min(1.0, pf3_threshold / max(duration, 1))
    else:
        pf3_passed = False
        pf3_score = 0.0
        duration = 0

    results.append(CheckResult(
        check_id="PF-3",
        name="Large repo handling",
        category=CheckCategory.PERFORMANCE,
        passed=pf3_passed,
        score=pf3_score,
        message=f"Deep history: {duration}ms (threshold: {pf3_threshold}ms)",
        evidence={"duration_ms": duration, "threshold_ms": pf3_threshold},
    ))

    # PF-4: Memory efficiency (raw output size)
    # Check that raw output isn't excessively large
    total_raw_size = 0
    for repo in repos:
        raw = repo.get("raw_output", {})
        # Estimate size based on string representation
        total_raw_size += len(str(raw))

    pf4_threshold = 100000  # 100KB total raw output
    pf4_passed = total_raw_size < pf4_threshold
    pf4_score = min(1.0, pf4_threshold / max(total_raw_size, 1))

    results.append(CheckResult(
        check_id="PF-4",
        name="Output size efficiency",
        category=CheckCategory.PERFORMANCE,
        passed=pf4_passed,
        score=pf4_score,
        message=f"Raw output: {total_raw_size / 1024:.1f}KB (threshold: {pf4_threshold / 1024:.0f}KB)",
        evidence={"raw_size_bytes": total_raw_size, "threshold_bytes": pf4_threshold},
    ))

    return results
