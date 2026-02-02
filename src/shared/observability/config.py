"""
Configuration for LLM observability.

Controls logging behavior, storage paths, retention, and feature flags.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import os


@dataclass
class ObservabilityConfig:
    """
    Configuration for LLM observability features.

    Attributes:
        enabled: Master switch for observability (default: True)
        log_dir: Base directory for log files (default: output/llm_logs)
        log_to_console: Whether to also log to console via structlog (default: False)
        log_to_file: Whether to persist to JSON-Lines files (default: True)
        include_prompts: Whether to log full prompt text (default: True)
        include_responses: Whether to log full response text (default: True)
        max_prompt_length: Truncate prompts longer than this (default: None = no truncation)
        max_response_length: Truncate responses longer than this (default: None = no truncation)
        retention_days: Auto-cleanup logs older than this (default: 30, 0 = no cleanup)
        console_log_level: Log level for console output (default: INFO)
    """

    enabled: bool = True
    log_dir: Path = field(default_factory=lambda: Path("output/llm_logs"))
    log_to_console: bool = False
    log_to_file: bool = True
    include_prompts: bool = True
    include_responses: bool = True
    max_prompt_length: int | None = None
    max_response_length: int | None = None
    retention_days: int = 30
    console_log_level: str = "INFO"

    # Feature flags
    capture_token_usage: bool = True
    capture_parsed_results: bool = True
    enable_trace_correlation: bool = True

    def __post_init__(self) -> None:
        """Ensure log_dir is a Path object."""
        if isinstance(self.log_dir, str):
            self.log_dir = Path(self.log_dir)

    @classmethod
    def from_env(cls) -> "ObservabilityConfig":
        """
        Create config from environment variables.

        Environment variables:
            LLM_OBSERVABILITY_ENABLED: "true" or "false" (default: "true")
            LLM_OBSERVABILITY_LOG_DIR: Path to log directory
            LLM_OBSERVABILITY_CONSOLE: "true" to enable console logging
            LLM_OBSERVABILITY_INCLUDE_PROMPTS: "false" to disable prompt logging
            LLM_OBSERVABILITY_INCLUDE_RESPONSES: "false" to disable response logging
            LLM_OBSERVABILITY_RETENTION_DAYS: Number of days to retain logs
        """
        return cls(
            enabled=os.getenv("LLM_OBSERVABILITY_ENABLED", "true").lower() == "true",
            log_dir=Path(os.getenv("LLM_OBSERVABILITY_LOG_DIR", "output/llm_logs")),
            log_to_console=os.getenv("LLM_OBSERVABILITY_CONSOLE", "false").lower() == "true",
            include_prompts=os.getenv("LLM_OBSERVABILITY_INCLUDE_PROMPTS", "true").lower() == "true",
            include_responses=os.getenv("LLM_OBSERVABILITY_INCLUDE_RESPONSES", "true").lower() == "true",
            retention_days=int(os.getenv("LLM_OBSERVABILITY_RETENTION_DAYS", "30")),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enabled": self.enabled,
            "log_dir": str(self.log_dir),
            "log_to_console": self.log_to_console,
            "log_to_file": self.log_to_file,
            "include_prompts": self.include_prompts,
            "include_responses": self.include_responses,
            "max_prompt_length": self.max_prompt_length,
            "max_response_length": self.max_response_length,
            "retention_days": self.retention_days,
            "console_log_level": self.console_log_level,
            "capture_token_usage": self.capture_token_usage,
            "capture_parsed_results": self.capture_parsed_results,
            "enable_trace_correlation": self.enable_trace_correlation,
        }


# Global config instance (lazy-loaded)
_global_config: ObservabilityConfig | None = None


def get_config() -> ObservabilityConfig:
    """
    Get the global observability config.

    On first call, loads config from environment variables.
    Subsequent calls return the cached config.
    """
    global _global_config
    if _global_config is None:
        _global_config = ObservabilityConfig.from_env()
    return _global_config


def set_config(config: ObservabilityConfig) -> None:
    """
    Set the global observability config.

    Use this to override the default environment-based config.
    """
    global _global_config
    _global_config = config


def reset_config() -> None:
    """
    Reset the global config to None.

    Next call to get_config() will reload from environment.
    """
    global _global_config
    _global_config = None
