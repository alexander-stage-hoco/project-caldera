"""Performance checks for Lizard function analysis (PF-1 to PF-4).

These checks validate that Lizard performs within acceptable time and
memory constraints for different repository sizes.
"""

import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import (
    CheckCategory,
    CheckResult,
    CheckSeverity,
    create_check_result,
    create_partial_check_result,
)


def _run_lizard_timed(
    target_path: Path, timeout: float = 60.0
) -> tuple[float, Optional[str]]:
    """Run lizard on a path and measure execution time.

    Returns:
        Tuple of (elapsed_seconds, error_message_or_none)
    """
    start_time = time.time()

    try:
        result = subprocess.run(
            [sys.executable, "-m", "lizard", str(target_path), "--xml"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.time() - start_time

        if result.returncode != 0:
            return elapsed, f"lizard exited with code {result.returncode}"

        return elapsed, None

    except subprocess.TimeoutExpired:
        return timeout, f"Timeout after {timeout} seconds"
    except FileNotFoundError:
        return 0.0, "lizard not found in PATH"
    except Exception as e:
        return 0.0, str(e)


def _get_memory_usage_mb() -> Optional[float]:
    """Get current process memory usage in MB.

    Returns None if unable to measure.
    """
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        # maxrss is in bytes on Linux, kilobytes on macOS
        import platform
        if platform.system() == "Darwin":
            return usage.ru_maxrss / (1024 * 1024)  # KB to MB
        else:
            return usage.ru_maxrss / 1024  # bytes to MB
    except Exception:
        return None


def check_pf1_synthetic_repo_speed(
    eval_repos_path: Optional[Path] = None,
) -> CheckResult:
    """PF-1: All synthetic repos analyzed in < 2 seconds total.

    Validates that the 7 synthetic language directories are fast to analyze.
    """
    if eval_repos_path is None:
        eval_repos_path = Path(__file__).parent.parent.parent / "eval-repos" / "synthetic"

    if not eval_repos_path.exists():
        return create_check_result(
            check_id="PF-1",
            name="Synthetic repo speed",
            category=CheckCategory.PERFORMANCE,
            severity=CheckSeverity.HIGH,
            passed=False,
            message=f"Synthetic repos path not found: {eval_repos_path}",
            evidence={"path": str(eval_repos_path)},
        )

    threshold_seconds = 2.0
    elapsed, error = _run_lizard_timed(eval_repos_path, timeout=10.0)

    if error:
        return create_check_result(
            check_id="PF-1",
            name="Synthetic repo speed",
            category=CheckCategory.PERFORMANCE,
            severity=CheckSeverity.HIGH,
            passed=False,
            message=f"Failed to run lizard: {error}",
            evidence={"error": error},
        )

    passed = elapsed <= threshold_seconds
    score = min(1.0, threshold_seconds / elapsed) if elapsed > 0 else 1.0

    return create_partial_check_result(
        check_id="PF-1",
        name="Synthetic repo speed",
        category=CheckCategory.PERFORMANCE,
        severity=CheckSeverity.HIGH,
        score=score,
        message=f"Synthetic repos analyzed in {elapsed:.2f}s (threshold: {threshold_seconds}s)",
        evidence={
            "elapsed_seconds": round(elapsed, 3),
            "threshold_seconds": threshold_seconds,
            "path": str(eval_repos_path),
        },
    )


def check_pf2_real_repo_click(
    eval_repos_path: Optional[Path] = None,
) -> CheckResult:
    """PF-2: Real repo 'click' analyzed in < 5 seconds.

    Click is a medium-sized Python project (~100 files).
    """
    if eval_repos_path is None:
        eval_repos_path = Path(__file__).parent.parent.parent / "eval-repos" / "real" / "click"

    if not eval_repos_path.exists():
        return create_check_result(
            check_id="PF-2",
            name="Real repo: click",
            category=CheckCategory.PERFORMANCE,
            severity=CheckSeverity.MEDIUM,
            passed=True,  # Skip if not available
            message=f"Click repo not found (skipped): {eval_repos_path}",
            evidence={"path": str(eval_repos_path), "skipped": True},
        )

    threshold_seconds = 5.0
    elapsed, error = _run_lizard_timed(eval_repos_path, timeout=30.0)

    if error:
        return create_check_result(
            check_id="PF-2",
            name="Real repo: click",
            category=CheckCategory.PERFORMANCE,
            severity=CheckSeverity.MEDIUM,
            passed=False,
            message=f"Failed to run lizard: {error}",
            evidence={"error": error},
        )

    passed = elapsed <= threshold_seconds
    score = min(1.0, threshold_seconds / elapsed) if elapsed > 0 else 1.0

    return create_partial_check_result(
        check_id="PF-2",
        name="Real repo: click",
        category=CheckCategory.PERFORMANCE,
        severity=CheckSeverity.MEDIUM,
        score=score,
        message=f"Click repo analyzed in {elapsed:.2f}s (threshold: {threshold_seconds}s)",
        evidence={
            "elapsed_seconds": round(elapsed, 3),
            "threshold_seconds": threshold_seconds,
            "path": str(eval_repos_path),
        },
    )


def check_pf3_real_repo_picocli(
    eval_repos_path: Optional[Path] = None,
) -> CheckResult:
    """PF-3: Real repo 'picocli' (src only) analyzed in < 30 seconds.

    Picocli is a large Java project. We analyze only src/ to avoid
    processing 1000+ documentation files.
    """
    if eval_repos_path is None:
        eval_repos_path = Path(__file__).parent.parent.parent / "eval-repos" / "real" / "picocli"

    # Analyze only src directory to avoid massive docs folder
    src_path = eval_repos_path / "src"
    if not src_path.exists():
        if not eval_repos_path.exists():
            return create_check_result(
                check_id="PF-3",
                name="Real repo: picocli",
                category=CheckCategory.PERFORMANCE,
                severity=CheckSeverity.MEDIUM,
                passed=True,  # Skip if not available
                message=f"Picocli repo not found (skipped): {eval_repos_path}",
                evidence={"path": str(eval_repos_path), "skipped": True},
            )
        src_path = eval_repos_path  # Fall back to root if no src

    threshold_seconds = 30.0
    elapsed, error = _run_lizard_timed(src_path, timeout=60.0)

    if error:
        return create_check_result(
            check_id="PF-3",
            name="Real repo: picocli",
            category=CheckCategory.PERFORMANCE,
            severity=CheckSeverity.MEDIUM,
            passed=False,
            message=f"Failed to run lizard: {error}",
            evidence={"error": error, "path": str(src_path)},
        )

    passed = elapsed <= threshold_seconds
    score = min(1.0, threshold_seconds / elapsed) if elapsed > 0 else 1.0

    return create_partial_check_result(
        check_id="PF-3",
        name="Real repo: picocli",
        category=CheckCategory.PERFORMANCE,
        severity=CheckSeverity.MEDIUM,
        score=score,
        message=f"Picocli src analyzed in {elapsed:.2f}s (threshold: {threshold_seconds}s)",
        evidence={
            "elapsed_seconds": round(elapsed, 3),
            "threshold_seconds": threshold_seconds,
            "path": str(src_path),
        },
    )


def check_pf4_memory_usage(
    analysis: Dict[str, Any],
) -> CheckResult:
    """PF-4: Memory usage < 500MB for analysis.

    Validates that memory usage is reasonable.
    """
    memory_mb = _get_memory_usage_mb()

    if memory_mb is None:
        return create_check_result(
            check_id="PF-4",
            name="Memory usage",
            category=CheckCategory.PERFORMANCE,
            severity=CheckSeverity.LOW,
            passed=True,
            message="Unable to measure memory usage (skipped)",
            evidence={"skipped": True},
        )

    threshold_mb = 500.0
    passed = memory_mb <= threshold_mb
    score = min(1.0, threshold_mb / memory_mb) if memory_mb > 0 else 1.0

    # Also check analysis size as a proxy
    total_functions = analysis.get("summary", {}).get("total_functions", 0)
    total_files = analysis.get("summary", {}).get("total_files", 0)

    return create_partial_check_result(
        check_id="PF-4",
        name="Memory usage",
        category=CheckCategory.PERFORMANCE,
        severity=CheckSeverity.LOW,
        score=score,
        message=f"Peak memory: {memory_mb:.1f}MB (threshold: {threshold_mb}MB)",
        evidence={
            "memory_mb": round(memory_mb, 1),
            "threshold_mb": threshold_mb,
            "total_files_analyzed": total_files,
            "total_functions_analyzed": total_functions,
        },
    )


def run_performance_checks(
    analysis: Dict[str, Any],
    eval_repos_path: Optional[Path] = None,
) -> List[CheckResult]:
    """Run all performance checks.

    Args:
        analysis: Parsed analysis JSON (for memory check)
        eval_repos_path: Base path for eval-repos (defaults to relative path)

    Returns:
        List of CheckResult objects
    """
    base_path = eval_repos_path or Path(__file__).parent.parent.parent / "eval-repos"

    return [
        check_pf1_synthetic_repo_speed(base_path / "synthetic"),
        check_pf2_real_repo_click(base_path / "real" / "click"),
        check_pf3_real_repo_picocli(base_path / "real" / "picocli"),
        check_pf4_memory_usage(analysis),
    ]
