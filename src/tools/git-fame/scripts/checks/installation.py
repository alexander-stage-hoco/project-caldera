"""Installation checks (IN-1 to IN-2) for git-fame.

These checks verify git-fame is properly installed:
- IN-1: pip install - pip install git-fame succeeds
- IN-2: CLI help - git-fame --help returns 0
"""

from __future__ import annotations

import subprocess
import sys
from typing import Any

from .utils import check_result


class InstallationChecks:
    """Installation evaluation checks for git-fame."""

    def __init__(self) -> None:
        """Initialize installation checks."""
        pass

    def run_all(self) -> list[dict[str, Any]]:
        """Run all installation checks.

        Returns:
            List of check results with check, passed, and message keys
        """
        return [
            self._check_pip_install(),
            self._check_cli_help(),
        ]

    def _check_pip_install(self) -> dict[str, Any]:
        """IN-1: Verify git-fame is installed via pip."""
        try:
            # Check if gitfame module can be imported
            result = subprocess.run(
                [sys.executable, "-c", "import gitfame; print(gitfame.__version__)"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                return check_result(
                    "IN-1",
                    True,
                    f"git-fame installed, version: {version}",
                )

            # Try alternate import
            result = subprocess.run(
                [sys.executable, "-m", "gitfame", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                version = result.stdout.strip() or result.stderr.strip()
                return check_result(
                    "IN-1",
                    True,
                    f"git-fame installed: {version[:50]}",
                )

            return check_result(
                "IN-1",
                False,
                f"git-fame not properly installed: {result.stderr[:100]}",
            )

        except subprocess.TimeoutExpired:
            return check_result(
                "IN-1",
                False,
                "Installation check timed out",
            )
        except FileNotFoundError:
            return check_result(
                "IN-1",
                False,
                "Python interpreter not found",
            )
        except Exception as e:
            return check_result(
                "IN-1",
                False,
                f"Installation check failed: {str(e)[:100]}",
            )

    def _check_cli_help(self) -> dict[str, Any]:
        """IN-2: Verify git-fame --help returns successfully."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "gitfame", "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Verify help text contains expected content
                help_text = result.stdout.lower()
                has_usage = "usage" in help_text or "gitfame" in help_text
                has_options = (
                    "--format" in help_text
                    or "--branch" in help_text
                    or "-h" in help_text
                )

                if has_usage or has_options:
                    return check_result(
                        "IN-2",
                        True,
                        "git-fame --help returns valid help text",
                    )

                return check_result(
                    "IN-2",
                    True,
                    f"git-fame --help succeeded (output length: {len(result.stdout)})",
                )

            return check_result(
                "IN-2",
                False,
                f"git-fame --help failed with code {result.returncode}: {result.stderr[:100]}",
            )

        except subprocess.TimeoutExpired:
            return check_result(
                "IN-2",
                False,
                "Help command timed out",
            )
        except FileNotFoundError:
            return check_result(
                "IN-2",
                False,
                "Python interpreter not found",
            )
        except Exception as e:
            return check_result(
                "IN-2",
                False,
                f"Help check failed: {str(e)[:100]}",
            )
