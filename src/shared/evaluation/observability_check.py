"""Observability enforcement and validation functions.

This module provides functions to ensure LLM observability is enabled
and functioning correctly across all tool evaluations.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any


class ObservabilityDisabledError(Exception):
    """Raised when observability is required but disabled."""

    pass


def is_observability_enabled() -> bool:
    """Check if LLM observability is currently enabled.

    Returns:
        True if observability is enabled, False otherwise.
    """
    # Check environment variable first
    env_enabled = os.getenv("LLM_OBSERVABILITY_ENABLED", "true").lower()
    if env_enabled == "false":
        return False

    # Check if observability module is available
    try:
        from shared.observability import get_config

        config = get_config()
        return config.enabled
    except ImportError:
        return False


def require_observability() -> None:
    """Raise error if observability is disabled.

    Call this at the start of evaluation scripts to enforce observability.

    Raises:
        ObservabilityDisabledError: If observability is disabled or unavailable.
    """
    if not is_observability_enabled():
        raise ObservabilityDisabledError(
            "LLM observability is required but disabled. "
            "Set LLM_OBSERVABILITY_ENABLED=true or remove the environment variable."
        )


def verify_interactions_logged(
    trace_id: str,
    min_count: int = 1,
    date: datetime | None = None,
) -> bool:
    """Verify at least min_count interactions were logged for a trace.

    Args:
        trace_id: The trace ID to check.
        min_count: Minimum number of expected interactions.
        date: Date to search (defaults to today).

    Returns:
        True if at least min_count interactions were logged.
    """
    try:
        from shared.observability import FileStore, get_config

        config = get_config()
        store = FileStore(base_dir=config.log_dir)
        interactions = store.query_by_trace(trace_id, date)
        return len(interactions) >= min_count
    except ImportError:
        return False


def get_observability_summary(trace_id: str, date: datetime | None = None) -> dict[str, Any]:
    """Return summary of logged interactions for a trace.

    Args:
        trace_id: The trace ID to summarize.
        date: Date to search (defaults to today).

    Returns:
        Dictionary with summary information including:
        - interaction_count: Total number of interactions
        - success_count: Number of successful interactions
        - error_count: Number of failed interactions
        - timeout_count: Number of timed out interactions
        - judges: List of judge names that logged interactions
        - total_duration_ms: Sum of all interaction durations
        - avg_duration_ms: Average interaction duration
    """
    try:
        from shared.observability import FileStore, get_config

        config = get_config()
        store = FileStore(base_dir=config.log_dir)
        interactions = store.query_by_trace(trace_id, date)

        if not interactions:
            return {
                "trace_id": trace_id,
                "interaction_count": 0,
                "success_count": 0,
                "error_count": 0,
                "timeout_count": 0,
                "judges": [],
                "total_duration_ms": 0,
                "avg_duration_ms": 0.0,
            }

        success_count = sum(1 for i in interactions if i.status == "success")
        error_count = sum(1 for i in interactions if i.status == "error")
        timeout_count = sum(1 for i in interactions if i.status == "timeout")
        judges = list(set(i.judge_name for i in interactions if i.judge_name))
        total_duration = sum(i.duration_ms for i in interactions)
        avg_duration = total_duration / len(interactions) if interactions else 0.0

        return {
            "trace_id": trace_id,
            "interaction_count": len(interactions),
            "success_count": success_count,
            "error_count": error_count,
            "timeout_count": timeout_count,
            "judges": judges,
            "total_duration_ms": total_duration,
            "avg_duration_ms": round(avg_duration, 2),
        }

    except ImportError:
        return {
            "trace_id": trace_id,
            "interaction_count": 0,
            "error": "Observability module not available",
        }


def get_recent_interactions(
    hours: int = 24,
    judge_name: str | None = None,
) -> list[dict[str, Any]]:
    """Get recent interactions, optionally filtered by judge.

    Args:
        hours: Number of hours to look back.
        judge_name: Optional judge name to filter by.

    Returns:
        List of interaction dictionaries.
    """
    try:
        from shared.observability import FileStore, get_config

        config = get_config()
        store = FileStore(base_dir=config.log_dir)

        start_date = datetime.now() - timedelta(hours=hours)
        end_date = datetime.now()

        interactions = list(store.read_range(start_date, end_date))

        if judge_name:
            interactions = [i for i in interactions if i.judge_name == judge_name]

        return [i.to_dict() for i in interactions]

    except ImportError:
        return []
