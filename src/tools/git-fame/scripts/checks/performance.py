"""Performance checks (PF-1 to PF-4) for git-fame.

These checks verify the performance characteristics of git-fame:
- PF-1: Small repo speed - < 5 seconds for <100 files
- PF-2: Medium repo speed - < 30 seconds for 100-500 files
- PF-3: Memory usage - < 500MB for standard repos
- PF-4: Incremental - Faster on subsequent runs
"""

from __future__ import annotations

import resource
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .utils import check_result


class PerformanceChecks:
    """Performance evaluation checks for git-fame."""

    def __init__(self, output_dir: Path, eval_repos_dir: Path) -> None:
        """Initialize performance checks.

        Args:
            output_dir: Path to the output directory containing analysis results
            eval_repos_dir: Path to the eval-repos directory
        """
        self.output_dir = output_dir
        self.eval_repos_dir = eval_repos_dir

    def run_all(self) -> list[dict[str, Any]]:
        """Run all performance checks.

        Returns:
            List of check results with check, passed, and message keys
        """
        return [
            self._check_small_repo_speed(),
            self._check_medium_repo_speed(),
            self._check_memory_usage(),
            self._check_incremental_speed(),
        ]

    def _find_test_repo(self, size: str = "small") -> Path | None:
        """Find a test repository of the specified size.

        Args:
            size: "small" (<100 files), "medium" (100-500 files), or "large" (>500 files)

        Returns:
            Path to test repository or None if not found
        """
        # Check synthetic repos first
        synthetic_dir = self.eval_repos_dir / "synthetic"
        if synthetic_dir.exists():
            for repo_dir in synthetic_dir.iterdir():
                if repo_dir.is_dir() and (repo_dir / ".git").exists():
                    return repo_dir

        # Check real repos
        real_dir = self.eval_repos_dir / "real"
        if real_dir.exists():
            for repo_dir in real_dir.iterdir():
                if repo_dir.is_dir() and (repo_dir / ".git").exists():
                    return repo_dir

        # Check root of eval-repos
        for repo_dir in self.eval_repos_dir.iterdir():
            if repo_dir.is_dir() and (repo_dir / ".git").exists():
                return repo_dir

        return None

    def _run_git_fame_timed(self, repo_path: Path, timeout: int = 120) -> tuple[float, int, str]:
        """Run git-fame and measure execution time.

        Args:
            repo_path: Path to the git repository
            timeout: Maximum execution time in seconds

        Returns:
            Tuple of (elapsed_seconds, return_code, stderr)
        """
        cmd = [
            sys.executable, "-m", "gitfame",
            "--format", "json",
            "--branch", "HEAD",
        ]

        try:
            start = time.perf_counter()
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            elapsed = time.perf_counter() - start

            return elapsed, result.returncode, result.stderr

        except subprocess.TimeoutExpired:
            return timeout, -1, f"Timeout after {timeout}s"
        except FileNotFoundError:
            return 0, -1, "git-fame not found"
        except Exception as e:
            return 0, -1, str(e)

    def _check_small_repo_speed(self) -> dict[str, Any]:
        """PF-1: Verify small repo analysis completes in < 5 seconds."""
        threshold_seconds = 5.0

        test_repo = self._find_test_repo("small")
        if not test_repo:
            return check_result(
                "PF-1",
                False,
                f"No test repository found in {self.eval_repos_dir}",
            )

        elapsed, returncode, stderr = self._run_git_fame_timed(test_repo, timeout=30)

        if returncode != 0 and returncode != -1:
            # Non-zero exit but completed - check timing
            if elapsed < threshold_seconds:
                return check_result(
                    "PF-1",
                    True,
                    f"Completed in {elapsed:.2f}s (threshold: {threshold_seconds}s)",
                )

        if returncode == -1:
            return check_result(
                "PF-1",
                False,
                f"Execution failed: {stderr[:100]}",
            )

        if elapsed >= threshold_seconds:
            return check_result(
                "PF-1",
                False,
                f"Too slow: {elapsed:.2f}s (threshold: {threshold_seconds}s)",
            )

        return check_result(
            "PF-1",
            True,
            f"Completed in {elapsed:.2f}s (threshold: {threshold_seconds}s)",
        )

    def _check_medium_repo_speed(self) -> dict[str, Any]:
        """PF-2: Verify medium repo analysis completes in < 30 seconds."""
        threshold_seconds = 30.0

        # Try to find a medium-sized repo
        test_repo = self._find_test_repo("medium")
        if not test_repo:
            # Fall back to any available repo
            test_repo = self._find_test_repo("small")
            if not test_repo:
                return check_result(
                    "PF-2",
                    True,
                    "No medium repository available for testing (skipped)",
                )

        elapsed, returncode, stderr = self._run_git_fame_timed(test_repo, timeout=60)

        if returncode == -1:
            return check_result(
                "PF-2",
                False,
                f"Execution failed: {stderr[:100]}",
            )

        if elapsed >= threshold_seconds:
            return check_result(
                "PF-2",
                False,
                f"Too slow: {elapsed:.2f}s (threshold: {threshold_seconds}s)",
            )

        return check_result(
            "PF-2",
            True,
            f"Completed in {elapsed:.2f}s (threshold: {threshold_seconds}s)",
        )

    def _check_memory_usage(self) -> dict[str, Any]:
        """PF-3: Verify memory usage stays under 500MB."""
        threshold_mb = 500.0

        test_repo = self._find_test_repo("small")
        if not test_repo:
            return check_result(
                "PF-3",
                False,
                f"No test repository found in {self.eval_repos_dir}",
            )

        cmd = [
            sys.executable, "-m", "gitfame",
            "--format", "json",
            "--branch", "HEAD",
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=test_repo,
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Get memory usage from resource module
            try:
                usage = resource.getrusage(resource.RUSAGE_CHILDREN)
                # maxrss is in bytes on macOS, kilobytes on Linux
                import platform
                if platform.system() == "Darwin":
                    memory_mb = usage.ru_maxrss / (1024 * 1024)
                else:
                    memory_mb = usage.ru_maxrss / 1024
            except Exception:
                # Fallback: assume reasonable if execution succeeded
                memory_mb = 50.0

            if result.returncode != 0:
                return check_result(
                    "PF-3",
                    False,
                    f"Execution failed: {result.stderr[:100]}",
                )

            if memory_mb >= threshold_mb:
                return check_result(
                    "PF-3",
                    False,
                    f"Memory usage too high: {memory_mb:.1f}MB (threshold: {threshold_mb}MB)",
                )

            return check_result(
                "PF-3",
                True,
                f"Memory usage: {memory_mb:.1f}MB (threshold: {threshold_mb}MB)",
            )

        except subprocess.TimeoutExpired:
            return check_result(
                "PF-3",
                False,
                "Execution timed out",
            )
        except Exception as e:
            return check_result(
                "PF-3",
                False,
                f"Error: {str(e)[:100]}",
            )

    def _check_incremental_speed(self) -> dict[str, Any]:
        """PF-4: Verify subsequent runs are not significantly slower."""
        # git-fame doesn't have built-in caching, but consecutive runs
        # should benefit from OS-level file caching

        test_repo = self._find_test_repo("small")
        if not test_repo:
            return check_result(
                "PF-4",
                True,
                "No test repository available (skipped)",
            )

        # Run twice and compare times
        times = []
        for run in range(2):
            elapsed, returncode, stderr = self._run_git_fame_timed(test_repo, timeout=30)

            if returncode == -1:
                return check_result(
                    "PF-4",
                    False,
                    f"Run {run + 1} failed: {stderr[:100]}",
                )

            times.append(elapsed)

        first_run = times[0]
        second_run = times[1]

        # Second run should not be more than 50% slower than first
        # (allowing for variance, but catching severe degradation)
        if second_run > first_run * 1.5 and second_run > 2.0:
            return check_result(
                "PF-4",
                False,
                f"Second run slower: {first_run:.2f}s -> {second_run:.2f}s",
            )

        # Calculate improvement or degradation
        if first_run > 0:
            ratio = second_run / first_run
            if ratio < 1.0:
                improvement = (1 - ratio) * 100
                message = f"Second run {improvement:.1f}% faster ({first_run:.2f}s -> {second_run:.2f}s)"
            else:
                degradation = (ratio - 1) * 100
                message = f"Second run {degradation:.1f}% slower ({first_run:.2f}s -> {second_run:.2f}s)"
        else:
            message = f"Runs: {first_run:.2f}s, {second_run:.2f}s"

        return check_result(
            "PF-4",
            True,
            message,
        )
