"""Tests for tiered detail compression."""

from __future__ import annotations

import json

from shared.llm.tiered_detail import (
    DEFAULT_MAX_DATA_CHARS,
    _TRIM_LIST_LEN,
    _TRIM_STRING_LEN,
    fit_to_budget,
)


class TestFitToBudget:
    def test_small_data_returns_full(self):
        data = {"key": "value", "count": 42}
        result = fit_to_budget(data)
        assert result == data

    def test_medium_data_returns_trimmed(self):
        """Data that exceeds tier 1 but fits tier 2 → trimmed."""
        # Create data with long strings and long lists that compress well
        data = {
            "items": [{"desc": "x" * 500} for _ in range(50)],
            "long_string": "y" * 5000,
        }
        budget = 3000  # small enough to fail full, large enough for trimmed
        result = fit_to_budget(data, max_chars=budget)

        serialized = json.dumps(result, indent=2, default=str)
        assert len(serialized) <= budget
        # Should have trimmed list to 5 items + sentinel
        assert len(result["items"]) == _TRIM_LIST_LEN + 1
        assert result["items"][-1] == {"_truncated": 45}

    def test_large_data_returns_summary(self):
        """Data that exceeds tier 2 → summary."""
        data = {
            "items": [{"desc": "x" * 300} for _ in range(100)],
        }
        budget = 500  # very tight
        result = fit_to_budget(data, max_chars=budget)

        # Summary replaces lists with count+sample
        assert "_count" in result["items"]
        assert result["items"]["_count"] == 100
        assert len(result["items"]["_sample"]) == 1

    def test_tier_trimmed_truncates_strings(self):
        data = {"text": "a" * 500}
        result = fit_to_budget(data, max_chars=100)
        # Even if trimmed tier doesn't fit, summary will truncate further.
        # Test the trimmed tier directly by using a budget that fits trimmed.
        budget = _TRIM_STRING_LEN + 100  # enough for trimmed but not full
        result = fit_to_budget(data, max_chars=budget)
        assert len(result["text"]) <= _TRIM_STRING_LEN + len("…[trimmed]")
        assert result["text"].endswith("…[trimmed]") or result["text"].endswith("…[summarized]")

    def test_tier_trimmed_limits_lists(self):
        # Use strings large enough that full tier exceeds budget
        data = {"items": [f"item-{i}-{'x' * 50}" for i in range(20)]}
        raw = len(json.dumps(data, indent=2))
        # Budget: fits trimmed (5 items), not full (20 items)
        budget = raw // 3
        result = fit_to_budget(data, max_chars=budget)

        items = result["items"]
        if isinstance(items, list):
            # Trimmed tier
            assert items[-1] == {"_truncated": 15}
            assert len(items) == _TRIM_LIST_LEN + 1
        else:
            # Summary tier (if trimmed didn't fit either)
            assert "_count" in items

    def test_tier_summary_replaces_lists(self):
        data = {"items": [1, 2, 3, 4, 5]}
        result = fit_to_budget(data, max_chars=10)
        # Forced to summary
        assert isinstance(result["items"], dict)
        assert result["items"]["_count"] == 5
        assert result["items"]["_sample"] == [1]

    def test_tier_summary_preserves_scalars(self):
        data = {"count": 42, "rate": 3.14, "active": True, "value": None}
        result = fit_to_budget(data, max_chars=10)
        assert result["count"] == 42
        assert result["rate"] == 3.14
        assert result["active"] is True
        assert result["value"] is None

    def test_nested_dicts_handled(self):
        data = {
            "outer": {
                "inner": {
                    "items": list(range(20)),
                    "text": "z" * 500,
                }
            }
        }
        result = fit_to_budget(data, max_chars=10)
        inner = result["outer"]["inner"]
        # Summary should have transformed the list
        assert isinstance(inner["items"], dict) and "_count" in inner["items"]
        # And truncated the string
        assert inner["text"].endswith("…[summarized]")

    def test_original_not_mutated(self):
        data = {"items": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "text": "a" * 500}
        original_items = list(data["items"])
        original_text = data["text"]

        fit_to_budget(data, max_chars=100)

        assert data["items"] == original_items
        assert data["text"] == original_text
