"""Performance checks (SP-1 to SP-4)."""

from __future__ import annotations

from . import CheckResult, check_at_most


def run_performance_checks(analysis: dict, ground_truth: dict) -> list[CheckResult]:
    """Run all performance checks."""
    check_results: list[CheckResult] = []
    # Thresholds can be at top level or inside expected (per ground truth schema)
    thresholds = ground_truth.get("expected", {}).get("thresholds", {})
    if not thresholds:
        # Fallback to top-level thresholds for backwards compatibility
        thresholds = ground_truth.get("thresholds", {})
    # Handle both old format (flat) and new format (with results wrapper)
    results = analysis.get("results", analysis)

    # SP-1: Total scan time within threshold
    max_time_ms = thresholds.get("max_scan_time_ms", 10000)
    actual_time = results.get("scan_time_ms", 0)
    check_results.append(
        check_at_most(
            "SP-1",
            "Performance",
            "Scan time (ms)",
            max_time_ms,
            actual_time,
        )
    )

    # SP-2: Scan time reasonable per commit
    # Assume 1 commit for small repos, calculate if we have commit count
    commits_with_secrets = results.get("commits_with_secrets", 1)
    if commits_with_secrets > 0:
        time_per_commit = actual_time / max(commits_with_secrets, 1)
        max_per_commit = thresholds.get("max_ms_per_commit", 1000)
        check_results.append(
            check_at_most(
                "SP-2",
                "Performance",
                "Time per commit (ms)",
                max_per_commit,
                time_per_commit,
            )
        )
    else:
        check_results.append(
            CheckResult(
                check_id="SP-2",
                category="Performance",
                passed=True,
                message="N/A - no commits with secrets",
                expected="N/A",
                actual="N/A",
            )
        )

    # SP-3: Scan time reasonable per finding
    total_secrets = results.get("total_secrets", 0)
    if total_secrets > 0:
        time_per_finding = actual_time / total_secrets
        max_per_finding = thresholds.get("max_ms_per_finding", 500)
        check_results.append(
            check_at_most(
                "SP-3",
                "Performance",
                "Time per finding (ms)",
                max_per_finding,
                time_per_finding,
            )
        )
    else:
        check_results.append(
            CheckResult(
                check_id="SP-3",
                category="Performance",
                passed=True,
                message="N/A - no secrets found",
                expected="N/A",
                actual="N/A",
            )
        )

    # SP-4: Memory usage reasonable (check if findings list is reasonable size)
    max_findings = thresholds.get("max_findings_for_test", 100)
    findings_count = len(results.get("findings", []))
    check_results.append(
        CheckResult(
            check_id="SP-4",
            category="Performance",
            passed=findings_count <= max_findings,
            message=f"Findings count: {findings_count} (max {max_findings})",
            expected=f"<= {max_findings}",
            actual=findings_count,
        )
    )

    return check_results
