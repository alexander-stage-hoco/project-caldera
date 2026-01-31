"""Installation checks (IN-1 to IN-4)."""

import subprocess
import os
from pathlib import Path
from typing import List

from . import CheckResult


def check_binary_exists(base_path: Path) -> CheckResult:
    """IN-1: Verify scc binary exists and is executable."""
    try:
        scc_path = base_path / "bin" / "scc"

        exists = scc_path.exists()
        executable = os.access(scc_path, os.X_OK) if exists else False

        passed = exists and executable

        return CheckResult(
            check_id="IN-1",
            name="Binary Exists",
            passed=passed,
            message=f"Binary exists: {exists}, executable: {executable}",
            expected="exists and executable",
            actual=f"exists={exists}, executable={executable}",
            evidence={"path": str(scc_path), "exists": exists, "executable": executable}
        )
    except Exception as e:
        return CheckResult(
            check_id="IN-1",
            name="Binary Exists",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_version(base_path: Path) -> CheckResult:
    """IN-2: Verify scc --version returns version string."""
    try:
        scc_path = base_path / "bin" / "scc"

        result = subprocess.run(
            [str(scc_path), "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Version should be in output
        has_version = result.returncode == 0 and (
            "scc" in result.stdout.lower() or
            "version" in result.stdout.lower() or
            len(result.stdout.strip()) > 0
        )

        return CheckResult(
            check_id="IN-2",
            name="Version Check",
            passed=has_version,
            message=f"Version output: {result.stdout.strip()[:50]}",
            expected="version string",
            actual=result.stdout.strip()[:100] if result.stdout else result.stderr[:100],
            evidence={"stdout": result.stdout.strip(), "returncode": result.returncode}
        )
    except Exception as e:
        return CheckResult(
            check_id="IN-2",
            name="Version Check",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_help_available(base_path: Path) -> CheckResult:
    """IN-3: Verify scc --help returns help text."""
    try:
        scc_path = base_path / "bin" / "scc"

        result = subprocess.run(
            [str(scc_path), "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Help should contain usage information
        has_help = result.returncode == 0 and (
            "usage" in result.stdout.lower() or
            "options" in result.stdout.lower() or
            "-f" in result.stdout or
            "--format" in result.stdout
        )

        return CheckResult(
            check_id="IN-3",
            name="Help Available",
            passed=has_help,
            message=f"Help available: {has_help}",
            expected="help text with usage/options",
            actual=f"has_help={has_help}, length={len(result.stdout)}",
            evidence={"has_help": has_help, "help_length": len(result.stdout)}
        )
    except Exception as e:
        return CheckResult(
            check_id="IN-3",
            name="Help Available",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def check_no_dependencies(base_path: Path) -> CheckResult:
    """IN-4: Verify scc runs without additional runtime dependencies."""
    try:
        scc_path = base_path / "bin" / "scc"

        # Try to run scc on a simple directory
        # If it works, no dependencies are missing
        result = subprocess.run(
            [str(scc_path), str(base_path / "scripts"), "-f", "json"],
            capture_output=True,
            text=True,
            timeout=10,
            env={"PATH": ""}  # Clear PATH to ensure no external deps
        )

        # Check for common dependency error messages
        has_dep_errors = any(msg in result.stderr.lower() for msg in [
            "library not found",
            "cannot open shared object",
            "dyld:",
            "not found",
            "missing"
        ])

        passed = result.returncode == 0 and not has_dep_errors

        return CheckResult(
            check_id="IN-4",
            name="No Dependencies",
            passed=passed,
            message="Runs without external dependencies" if passed else f"Dependency issue: {result.stderr[:100]}",
            expected="no dependency errors",
            actual=f"returncode={result.returncode}, has_errors={has_dep_errors}",
            evidence={"returncode": result.returncode, "stderr": result.stderr[:200] if result.stderr else ""}
        )
    except Exception as e:
        return CheckResult(
            check_id="IN-4",
            name="No Dependencies",
            passed=False,
            message=f"Error: {e}",
            evidence={"error": str(e)}
        )


def run_installation_checks(base_path: Path) -> List[CheckResult]:
    """Run all installation checks."""
    return [
        check_binary_exists(base_path),
        check_version(base_path),
        check_help_available(base_path),
        check_no_dependencies(base_path),
    ]
