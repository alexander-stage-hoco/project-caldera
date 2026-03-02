"""Tiered detail compression for LLM prompt data.

Progressively compresses data dicts to fit within a character budget:
- Tier 1 (full): return as-is if under budget
- Tier 2 (trimmed): truncate long strings, limit list lengths
- Tier 3 (summary): replace lists with count+sample, aggressive string truncation
"""

from __future__ import annotations

import copy
import json

DEFAULT_MAX_DATA_CHARS = 30_000
_TRIM_STRING_LEN = 200
_TRIM_LIST_LEN = 5
_SUMMARY_STRING_LEN = 100


def fit_to_budget(data: dict, max_chars: int = DEFAULT_MAX_DATA_CHARS) -> dict:
    """Return the most detailed representation of *data* that fits *max_chars*.

    Tries tiers in order: full → trimmed → summary.
    If even summary exceeds the budget it is returned anyway (downstream
    guards P0/P1 will catch it).
    """
    serialized = json.dumps(data, indent=2, default=str)
    if len(serialized) <= max_chars:
        return data

    trimmed = _apply_trimmed(copy.deepcopy(data))
    serialized = json.dumps(trimmed, indent=2, default=str)
    if len(serialized) <= max_chars:
        return trimmed

    return _apply_summary(copy.deepcopy(data))


def _apply_trimmed(obj: object) -> object:
    """Tier 2: truncate strings > 200 chars, limit lists to 5 items."""
    if isinstance(obj, dict):
        return {k: _apply_trimmed(v) for k, v in obj.items()}
    if isinstance(obj, list):
        original_len = len(obj)
        items = [_apply_trimmed(item) for item in obj[:_TRIM_LIST_LEN]]
        if original_len > _TRIM_LIST_LEN:
            items.append({"_truncated": original_len - _TRIM_LIST_LEN})
        return items
    if isinstance(obj, str) and len(obj) > _TRIM_STRING_LEN:
        return obj[:_TRIM_STRING_LEN] + "…[trimmed]"
    return obj


def _apply_summary(obj: object) -> object:
    """Tier 3: replace lists with count+sample, aggressive string truncation."""
    if isinstance(obj, dict):
        return {k: _apply_summary(v) for k, v in obj.items()}
    if isinstance(obj, list):
        count = len(obj)
        sample = [_apply_summary(obj[0])] if count > 0 else []
        return {"_count": count, "_sample": sample}
    if isinstance(obj, str) and len(obj) > _SUMMARY_STRING_LEN:
        return obj[:_SUMMARY_STRING_LEN] + "…[summarized]"
    return obj
