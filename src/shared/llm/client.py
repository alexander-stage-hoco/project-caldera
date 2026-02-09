"""LLM client for invoking Claude via SDK or CLI.

This module provides a unified interface for invoking Claude models,
preferring the Anthropic SDK when available and falling back to the
Claude Code CLI.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable

try:
    import anthropic  # type: ignore
    HAS_ANTHROPIC_SDK = True
except Exception:
    anthropic = None
    HAS_ANTHROPIC_SDK = False


# Model name to API ID mapping (for SDK/logging)
MODEL_MAP = {
    "sonnet": "claude-sonnet-4-20250514",
    "opus": "claude-opus-4-20250514",
    "opus-4.5": "claude-opus-4-5-20250514",
    "haiku": "claude-haiku-4-20250514",
}

# Model name to CLI alias mapping (CLI doesn't understand "opus-4.5")
CLI_MODEL_MAP = {
    "opus-4.5": "opus",  # CLI uses "opus" for latest Opus model
}


def validate_claude_cli() -> tuple[bool, str]:
    """Check if Claude CLI is available and executable.

    Returns:
        Tuple of (is_valid, message). If valid, message contains the path.
        If invalid, message contains the error reason.
    """
    claude_path = shutil.which("claude")
    if not claude_path:
        return False, "Claude CLI not found in PATH"

    if not os.access(claude_path, os.X_OK):
        return False, f"Claude CLI at {claude_path} is not executable"

    return True, claude_path


class LLMClient:
    """Client for invoking Claude via SDK or CLI.

    This class provides a unified interface for making LLM calls,
    automatically selecting the best available method (SDK preferred,
    CLI fallback).

    Example:
        client = LLMClient(model="opus-4.5", timeout=120)
        response = client.invoke("What is 2+2?")
    """

    def __init__(
        self,
        model: str = "opus-4.5",
        timeout: int = 120,
        working_dir: Path | None = None,
        logger: Callable[[str, str, str, Any], None] | None = None,
        system_prompt: str | None = None,
    ):
        """Initialize the LLM client.

        Args:
            model: Model name ("sonnet", "opus", "opus-4.5", "haiku") or full API ID
            timeout: Timeout in seconds for LLM invocation
            working_dir: Working directory for CLI invocation
            logger: Optional callback for logging (signature: logger(event, data, ...))
            system_prompt: Default system prompt for CLI invocations
        """
        self.model = model
        self.timeout = timeout
        self.working_dir = working_dir or Path.cwd()
        self._logger = logger
        self._system_prompt = system_prompt or (
            "You are an LLM judge performing automated code quality evaluation. "
            "Analyze the evidence provided and return a JSON response with score, "
            "confidence, reasoning, evidence_cited, and recommendations fields. "
            "Follow the scoring rubric exactly. Return ONLY valid JSON."
        )

    @property
    def model_id(self) -> str:
        """Get the API model ID for the configured model."""
        return MODEL_MAP.get(self.model, self.model)

    @property
    def cli_model(self) -> str:
        """Get the CLI-compatible model alias."""
        return CLI_MODEL_MAP.get(self.model, self.model)

    def _invoke_via_sdk(self, prompt: str, system_prompt: str | None = None) -> str | None:
        """Invoke Claude via Anthropic SDK when available.

        Args:
            prompt: The prompt to send
            system_prompt: Optional system prompt (not used by SDK messages API)

        Returns:
            Response text if successful, None if SDK unavailable or error
        """
        if not HAS_ANTHROPIC_SDK:
            return None
        if os.environ.get("USE_ANTHROPIC_SDK") != "1":
            return None
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=self.model_id,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        content = getattr(response, "content", []) or []
        return "".join(getattr(block, "text", "") for block in content)

    def _invoke_via_cli(self, prompt: str, system_prompt: str | None = None) -> str:
        """Invoke Claude Code in headless mode via CLI.

        Args:
            prompt: The prompt to send
            system_prompt: Optional system prompt override

        Returns:
            Response text or error message
        """
        claude_path = shutil.which("claude")
        if not claude_path:
            # Provide diagnostic information about PATH
            path_dirs = os.environ.get("PATH", "").split(os.pathsep)[:5]
            return f"Error: Claude CLI not found in PATH. Searched: {path_dirs}"

        # Verify the binary is executable
        if not os.access(claude_path, os.X_OK):
            return f"Error: Claude CLI at {claude_path} is not executable"

        try:
            max_turns = os.getenv("CLAUDE_MAX_TURNS", "5")
            effective_system_prompt = system_prompt or self._system_prompt

            # Use stdin (-) instead of @file to avoid Claude misinterpreting file content
            cmd = [
                "claude",
                "--print", "-",
                "--model", self.cli_model,
                "--output-format", "text",
                "--max-turns", str(max_turns),
                "--setting-sources", "user",
                "--system-prompt", effective_system_prompt,
            ]

            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(self.working_dir),
            )

            if result.returncode != 0:
                stderr = result.stderr.strip()
                stdout = result.stdout.strip()

                # Build detailed error message
                error_details = []
                error_details.append(f"exit_code={result.returncode}")
                error_details.append(f"claude_path={claude_path}")
                error_details.append(f"working_dir={self.working_dir}")
                error_details.append(f"model={self.cli_model}")

                if stderr:
                    error_details.append(f"stderr={stderr[:200]}")
                if stdout:
                    error_details.append(f"stdout={stdout[:200]}")

                # Check for common error patterns
                combined_output = f"{stderr} {stdout}".lower()
                if "eperm" in combined_output or "permission" in combined_output:
                    return f"Error: Permission denied executing Claude CLI ({'; '.join(error_details)})"
                elif "enoent" in combined_output:
                    return f"Error: Claude CLI not found ({'; '.join(error_details)})"
                elif "api key" in combined_output or "authentication" in combined_output:
                    return f"Error: Authentication failed - check ANTHROPIC_API_KEY ({'; '.join(error_details)})"
                elif "rate limit" in combined_output:
                    return f"Error: Rate limited by API ({'; '.join(error_details)})"
                elif not stderr and not stdout:
                    # No output at all
                    return (
                        f"Error (exit {result.returncode}): CLI returned no output. "
                        f"Diagnostics: {'; '.join(error_details)}. "
                        f"Check: 1) ANTHROPIC_API_KEY is set, 2) claude CLI version, "
                        f"3) network connectivity"
                    )

                return f"Error (exit {result.returncode}): {'; '.join(error_details)}"

            stdout = result.stdout.strip()
            if not stdout:
                return "Error: Claude returned empty response (exit 0 but no output)"
            return stdout

        except subprocess.TimeoutExpired:
            return f"Error: Claude invocation timed out after {self.timeout}s"
        except PermissionError as e:
            return f"Error: Permission denied - {e}"
        except FileNotFoundError:
            return f"Error: Claude CLI not found (FileNotFoundError for {claude_path})"
        except OSError as e:
            return f"Error: OS error - {e} (claude_path={claude_path})"
        except Exception as e:
            return f"Error: Unexpected - {type(e).__name__}: {e}"

    def invoke(self, prompt: str, system_prompt: str | None = None) -> str:
        """Invoke Claude, preferring SDK and falling back to CLI.

        Args:
            prompt: The prompt to send
            system_prompt: Optional system prompt (used by CLI invocation)

        Returns:
            Response text
        """
        # Try SDK first
        sdk_response = self._invoke_via_sdk(prompt, system_prompt)
        if sdk_response is not None:
            return sdk_response

        # Fall back to CLI
        return self._invoke_via_cli(prompt, system_prompt)

    def is_error_response(self, response: str) -> bool:
        """Check if a response indicates an error.

        Args:
            response: The response text to check

        Returns:
            True if the response starts with "Error"
        """
        return response.startswith("Error")

    def is_timeout_error(self, response: str) -> bool:
        """Check if a response indicates a timeout error.

        Args:
            response: The response text to check

        Returns:
            True if the response indicates a timeout
        """
        return self.is_error_response(response) and "timed out" in response.lower()
