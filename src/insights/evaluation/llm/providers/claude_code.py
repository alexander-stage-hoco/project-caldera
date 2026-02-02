"""
Claude Code Headless provider using Opus 4.5.

This is the default and recommended provider for evaluation.
"""

import json
import subprocess
from pathlib import Path
from typing import Any

from . import LLMProvider, LLMResponse


class ClaudeCodeHeadlessProvider(LLMProvider):
    """Uses Claude Code in headless mode with Opus 4.5."""

    SUPPORTED_MODELS = [
        "claude-opus-4-5",
        "claude-sonnet-4",
        "claude-3-5-sonnet",
    ]

    def __init__(
        self,
        model: str = "claude-opus-4-5",
        timeout: int = 120,
        working_dir: Path | None = None,
    ):
        """
        Initialize Claude Code headless provider.

        Args:
            model: Model to use (default: claude-opus-4-5).
            timeout: Command timeout in seconds.
            working_dir: Working directory for Claude Code.
        """
        self._model = model
        self.timeout = timeout
        self.working_dir = working_dir or Path.cwd()

    @property
    def name(self) -> str:
        return "claude_code"

    @property
    def default_model(self) -> str:
        return "claude-opus-4-5"

    def supports_model(self, model: str) -> bool:
        return model in self.SUPPORTED_MODELS

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """
        Send a completion request via Claude Code CLI.

        Uses `claude -p` for headless operation.
        """
        effective_model = model or self._model

        # Build the command
        cmd = ["claude", "-p"]

        # Add model selection if not default
        if effective_model != self.default_model:
            cmd.extend(["--model", effective_model])

        # Combine system and user prompt
        full_prompt = prompt
        if system:
            full_prompt = f"System: {system}\n\nUser: {prompt}"

        # Execute Claude Code
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
                raise RuntimeError(f"Claude Code failed: {result.stderr}")

            return LLMResponse(
                content=result.stdout.strip(),
                model=effective_model,
                metadata={"provider": "claude_code"},
            )

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Claude Code timed out after {self.timeout}s")
        except FileNotFoundError:
            raise RuntimeError("Claude Code CLI not found. Install with: npm install -g @anthropic-ai/claude-code")


class ClaudeCodeMockProvider(ClaudeCodeHeadlessProvider):
    """Mock provider for testing without actual CLI calls."""

    def __init__(self, responses: dict[str, str] | None = None, **kwargs: Any):
        super().__init__(**kwargs)
        self.responses = responses or {}
        self.call_log: list[dict[str, Any]] = []

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Return mock response."""
        self.call_log.append({
            "prompt": prompt,
            "system": system,
            "model": model,
        })

        # Check for predefined response
        for key, response in self.responses.items():
            if key in prompt:
                return LLMResponse(
                    content=response,
                    model=model or self._model,
                    metadata={"provider": "claude_code_mock"},
                )

        # Default mock response
        return LLMResponse(
            content=json.dumps({
                "overall_score": 4.0,
                "sub_scores": {
                    "dimension_1": 4.0,
                    "dimension_2": 4.0,
                },
                "reasoning": "Mock evaluation response",
                "suggestions": [],
            }),
            model=model or self._model,
            metadata={"provider": "claude_code_mock"},
        )
