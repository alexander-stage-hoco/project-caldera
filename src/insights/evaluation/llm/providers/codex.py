"""
Codex Headless provider for code-focused evaluation.
"""

import subprocess
from pathlib import Path
from typing import Any

from . import LLMProvider, LLMResponse


class CodexHeadlessProvider(LLMProvider):
    """Uses Codex in headless mode."""

    def __init__(
        self,
        model: str = "codex",
        timeout: int = 120,
        working_dir: Path | None = None,
    ):
        """
        Initialize Codex headless provider.

        Args:
            model: Model identifier.
            timeout: Command timeout in seconds.
            working_dir: Working directory for Codex.
        """
        self._model = model
        self.timeout = timeout
        self.working_dir = working_dir or Path.cwd()

    @property
    def name(self) -> str:
        return "codex"

    @property
    def default_model(self) -> str:
        return "codex"

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """
        Send a completion request via Codex CLI.

        Uses codex in headless mode.
        """
        effective_model = model or self._model

        # Build command - assuming codex CLI with similar interface
        cmd = ["codex", "-p"]

        # Combine system and user prompt
        full_prompt = prompt
        if system:
            full_prompt = f"System: {system}\n\nUser: {prompt}"

        try:
            result = subprocess.run(
                cmd,
                input=full_prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(self.working_dir),
            )

            if result.returncode != 0:
                raise RuntimeError(f"Codex failed: {result.stderr}")

            return LLMResponse(
                content=result.stdout.strip(),
                model=effective_model,
                metadata={"provider": "codex"},
            )

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Codex timed out after {self.timeout}s")
        except FileNotFoundError:
            raise RuntimeError("Codex CLI not found. Ensure codex is installed and in PATH.")
