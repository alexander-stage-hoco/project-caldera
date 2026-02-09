"""Envelope handling for tool outputs.

This module provides utilities for wrapping and unwrapping tool outputs
in the standard envelope format used throughout Project Caldera.

Standard envelope format:
    {
        "metadata": {
            "repo_id": "...",
            "run_id": "...",
            "tool_name": "...",
            ...
        },
        "data": {
            // Tool-specific output data
        }
    }
"""

from __future__ import annotations

from typing import Any


def unwrap_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract data from standard envelope format.

    Handles both envelope format {"metadata": {...}, "data": {...}}
    and raw data format (returns as-is).

    Args:
        payload: The payload to unwrap, either in envelope format or raw data

    Returns:
        The unwrapped data dictionary. If the payload is in envelope format,
        returns the "data" field contents. Otherwise, returns the payload as-is.

    Example:
        >>> payload = {"metadata": {...}, "data": {"files": [...]}}
        >>> unwrap_envelope(payload)
        {"files": [...]}

        >>> payload = {"files": [...]}  # Raw format
        >>> unwrap_envelope(payload)
        {"files": [...]}
    """
    if isinstance(payload, dict) and "data" in payload:
        return payload.get("data") or {}
    return payload


def wrap_envelope(
    data: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Wrap data in standard envelope format.

    Args:
        data: The tool-specific data to wrap
        metadata: Metadata about the run (repo_id, run_id, tool_name, etc.)

    Returns:
        Dictionary in standard envelope format with "metadata" and "data" keys

    Example:
        >>> data = {"files": [...]}
        >>> metadata = {"repo_id": "my-repo", "tool_name": "scc"}
        >>> wrap_envelope(data, metadata)
        {"metadata": {"repo_id": "my-repo", "tool_name": "scc"}, "data": {"files": [...]}}
    """
    return {"metadata": metadata, "data": data}
