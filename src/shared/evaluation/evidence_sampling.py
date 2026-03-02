"""Evidence sampling helpers for BaseJudge collect_evidence() implementations.

Provides deterministic sampling and truncation to keep evidence payloads
within token budgets before they reach the LLM.
"""

from __future__ import annotations

import copy
import random


def sample_dict_values(
    data: dict,
    max_entries: int = 10,
    seed: int = 42,
) -> dict:
    """Return a deterministic random sample of dict entries.

    If *data* has fewer than *max_entries* keys, returns a shallow copy
    unchanged.  Otherwise returns *max_entries* randomly-selected entries
    plus a ``_sampled_from`` metadata key with the original count.
    """
    if len(data) <= max_entries:
        return dict(data)

    rng = random.Random(seed)
    keys = rng.sample(sorted(data.keys()), max_entries)
    result = {k: data[k] for k in keys}
    result["_sampled_from"] = len(data)
    return result


def sample_list(
    items: list,
    max_items: int = 20,
    seed: int = 42,
) -> list:
    """Return a deterministic random sample of list items.

    If *items* has fewer than *max_items* entries, returns a shallow copy
    unchanged.  Otherwise returns *max_items* randomly-selected items
    plus a ``{"_sampled_from": N}`` sentinel dict appended at the end.
    """
    if len(items) <= max_items:
        return list(items)

    rng = random.Random(seed)
    sampled = rng.sample(items, max_items)
    sampled.append({"_sampled_from": len(items)})
    return sampled


def truncate_nested_strings(
    data: object,
    max_str_len: int = 300,
) -> object:
    """Deep-walk *data* and truncate any string longer than *max_str_len*.

    Returns a deep copy — the original is never mutated.
    """
    return _truncate(copy.deepcopy(data), max_str_len)


def _truncate(obj: object, max_len: int) -> object:
    if isinstance(obj, dict):
        return {k: _truncate(v, max_len) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_truncate(item, max_len) for item in obj]
    if isinstance(obj, str) and len(obj) > max_len:
        return obj[:max_len] + "…[trimmed]"
    return obj
