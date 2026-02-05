"""Standardized Caldera envelope formatter for tool output.

All tools produce output in the same envelope format:
{
    "metadata": {
        "tool_name": "...",
        "tool_version": "...",
        "run_id": "...",
        "repo_id": "...",
        "branch": "...",
        "commit": "...",
        "timestamp": "...",
        "schema_version": "1.0.0"
    },
    "data": { ... }
}

This module provides a single function to create this envelope consistently.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def get_current_timestamp() -> str:
    """Return current UTC timestamp in ISO format.

    Returns:
        ISO 8601 formatted timestamp string with timezone info.
    """
    return datetime.now(timezone.utc).isoformat()


def create_envelope(
    data: dict[str, Any],
    *,
    tool_name: str,
    tool_version: str,
    run_id: str,
    repo_id: str,
    branch: str,
    commit: str,
    schema_version: str = "1.0.0",
    timestamp: str | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a standardized Caldera envelope around tool output data.

    This function wraps tool-specific data in the standard Caldera envelope
    format with consistent metadata fields. All tools should use this function
    to ensure output format consistency.

    Args:
        data: The tool-specific output data to wrap.
        tool_name: Name of the analysis tool (e.g., "scc", "semgrep").
        tool_version: Version of the tool that produced the output.
        run_id: Unique identifier for this analysis run.
        repo_id: Unique identifier for the repository being analyzed.
        branch: Git branch being analyzed.
        commit: Git commit SHA (40 hex characters).
        schema_version: Version of the output schema (default: "1.0.0").
        timestamp: ISO format timestamp (auto-generated if not provided).
        extra_metadata: Additional metadata fields to include (optional).

    Returns:
        Dictionary in Caldera envelope format with metadata and data sections.

    Example:
        >>> envelope = create_envelope(
        ...     {"files": [], "summary": {}},
        ...     tool_name="scc",
        ...     tool_version="3.1.0",
        ...     run_id="abc123",
        ...     repo_id="def456",
        ...     branch="main",
        ...     commit="a" * 40,
        ... )
        >>> envelope["metadata"]["tool_name"]
        'scc'
    """
    if timestamp is None:
        timestamp = get_current_timestamp()

    metadata: dict[str, Any] = {
        "tool_name": tool_name,
        "tool_version": tool_version,
        "run_id": run_id,
        "repo_id": repo_id,
        "branch": branch,
        "commit": commit,
        "timestamp": timestamp,
        "schema_version": schema_version,
    }

    # Merge extra metadata if provided (preserves standard fields)
    if extra_metadata:
        for key, value in extra_metadata.items():
            if key not in metadata:
                metadata[key] = value

    return {
        "metadata": metadata,
        "data": data,
    }
