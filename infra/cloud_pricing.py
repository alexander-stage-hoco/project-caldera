"""Hetzner Cloud pricing utilities for Caldera cloud runs.

Loads server presets and pricing from ``server_presets.json`` and provides
helpers for cost estimation, preset resolution, and server info lookup.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

_PRESETS_PATH = Path(__file__).parent / "server_presets.json"


def load_presets() -> dict:
    """Load the full presets JSON from ``infra/server_presets.json``."""
    with open(_PRESETS_PATH) as f:
        return json.load(f)


def resolve_server_type(name_or_type: str) -> str:
    """Resolve a preset name (e.g. ``small``) or raw type (e.g. ``cx23``) to a Hetzner server type.

    Returns the server type string.  Raises ``ValueError`` if neither a
    known preset name nor a known server type.
    """
    data = load_presets()
    presets = data["presets"]
    pricing = data["pricing_eur_per_hour"]

    # Check if it's a preset name
    if name_or_type in presets:
        return presets[name_or_type]["server_type"]

    # Check if it's a raw server type
    if name_or_type in pricing:
        return name_or_type

    known = sorted(set(list(presets.keys()) + list(pricing.keys())))
    msg = f"Unknown preset or server type: {name_or_type!r}. Known: {', '.join(known)}"
    raise ValueError(msg)


def estimate_cost_eur(server_type: str, duration_seconds: int | float) -> dict:
    """Estimate the cost of a cloud run.

    Returns a dict with ``estimated_cost_eur``, ``pricing_eur_per_hour``,
    and ``billable_hours``.
    """
    data = load_presets()
    pricing = data["pricing_eur_per_hour"]
    increment = data.get("billing_increment_seconds", 3600)

    hourly_rate = pricing.get(server_type, 0.0)
    billable_hours = math.ceil(duration_seconds / increment) if duration_seconds > 0 else 0
    cost = round(billable_hours * hourly_rate, 4)

    return {
        "estimated_cost_eur": cost,
        "pricing_eur_per_hour": hourly_rate,
        "billable_hours": billable_hours,
    }


def get_preset_info(name: str) -> dict | None:
    """Return preset metadata for a given preset name, or ``None`` if not found."""
    data = load_presets()
    return data["presets"].get(name)
