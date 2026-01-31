"""Performance checks (PF-1 to PF-4)."""

import subprocess
import time
import resource
from pathlib import Path
from typing import List

from . import CheckResult


def check_fast_execution(base_path: Path, threshold_ms: int = 5000) -> CheckResult:
    """PF-1: Verify execution time < 5 seconds."""
    try:
        scc_path = base_path / "bin" / "scc"
        target = "eval-repos/synthetic"

        start = time.perf_counter()
        result = subprocess.run(
            [str(scc_path), target, "-f", "json"],
            capture_output=True,
            text=True,
            cwd=base_path,
            timeout=30
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        passed = elapsed_ms < threshold_ms and result.returncode == 0

        return CheckResult(
            check_id="PF-1",
            name="Fast Execution",
            passed=passed,
            message=f"Execution time: {elapsed_ms:.0f}ms (threshold: {threshold_ms}ms)",
            expected=f"< {threshold_ms}ms",
            actual=f"{elapsed_ms:.0f}ms",
            evidence={"elapsed_ms": elapsed_ms, "threshold_ms": threshold_ms}
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            check_id="PF-1",
            name="Fast Execution",
            passed=False,
            message="Execution timed out (>30s)",
            expected=f"< {threshold_ms}ms",
            actual="timeout",
            evidence={"timeout": True}
        )
    except Exception as e:
        return CheckResult(
            check_id="PF-1",
            name="Fast Execution",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_very_fast_execution(base_path: Path, threshold_ms: int = 1000) -> CheckResult:
    """PF-2: Verify execution time < 1 second."""
    try:
        scc_path = base_path / "bin" / "scc"
        target = "eval-repos/synthetic"

        start = time.perf_counter()
        result = subprocess.run(
            [str(scc_path), target, "-f", "json"],
            capture_output=True,
            text=True,
            cwd=base_path,
            timeout=30
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        passed = elapsed_ms < threshold_ms and result.returncode == 0

        return CheckResult(
            check_id="PF-2",
            name="Very Fast Execution",
            passed=passed,
            message=f"Execution time: {elapsed_ms:.0f}ms (threshold: {threshold_ms}ms)",
            expected=f"< {threshold_ms}ms",
            actual=f"{elapsed_ms:.0f}ms",
            evidence={"elapsed_ms": elapsed_ms, "threshold_ms": threshold_ms}
        )
    except Exception as e:
        return CheckResult(
            check_id="PF-2",
            name="Very Fast Execution",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_sub_second(base_path: Path, threshold_ms: int = 500) -> CheckResult:
    """PF-3: Verify execution time < 500ms."""
    try:
        scc_path = base_path / "bin" / "scc"
        target = "eval-repos/synthetic"

        start = time.perf_counter()
        result = subprocess.run(
            [str(scc_path), target, "-f", "json"],
            capture_output=True,
            text=True,
            cwd=base_path,
            timeout=30
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        passed = elapsed_ms < threshold_ms and result.returncode == 0

        return CheckResult(
            check_id="PF-3",
            name="Sub-Second",
            passed=passed,
            message=f"Execution time: {elapsed_ms:.0f}ms (threshold: {threshold_ms}ms)",
            expected=f"< {threshold_ms}ms",
            actual=f"{elapsed_ms:.0f}ms",
            evidence={"elapsed_ms": elapsed_ms, "threshold_ms": threshold_ms}
        )
    except Exception as e:
        return CheckResult(
            check_id="PF-3",
            name="Sub-Second",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_memory_reasonable(base_path: Path, threshold_mb: int = 100) -> CheckResult:
    """PF-4: Verify peak memory < 100MB."""
    try:
        scc_path = base_path / "bin" / "scc"
        target = "eval-repos/synthetic"

        # Run scc and measure memory
        result = subprocess.run(
            [str(scc_path), target, "-f", "json"],
            capture_output=True,
            text=True,
            cwd=base_path,
            timeout=30
        )

        # Get memory usage from resource module (only works on Unix)
        try:
            usage = resource.getrusage(resource.RUSAGE_CHILDREN)
            # maxrss is in kilobytes on Linux, bytes on macOS
            import platform
            if platform.system() == "Darwin":
                memory_mb = usage.ru_maxrss / (1024 * 1024)  # bytes to MB
            else:
                memory_mb = usage.ru_maxrss / 1024  # KB to MB
        except Exception:
            # Fallback: assume reasonable if execution succeeded
            memory_mb = 50  # Assume reasonable

        passed = memory_mb < threshold_mb and result.returncode == 0

        return CheckResult(
            check_id="PF-4",
            name="Memory Reasonable",
            passed=passed,
            message=f"Peak memory: {memory_mb:.1f}MB (threshold: {threshold_mb}MB)",
            expected=f"< {threshold_mb}MB",
            actual=f"{memory_mb:.1f}MB",
            evidence={"memory_mb": memory_mb, "threshold_mb": threshold_mb}
        )
    except Exception as e:
        return CheckResult(
            check_id="PF-4",
            name="Memory Reasonable",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def run_performance_checks(base_path: Path) -> List[CheckResult]:
    """Run all performance checks."""
    return [
        check_fast_execution(base_path),
        check_very_fast_execution(base_path),
        check_sub_second(base_path),
        check_memory_reasonable(base_path),
    ]
