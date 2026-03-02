"""Tests for evidence sampling helpers."""

from __future__ import annotations

from shared.evaluation.evidence_sampling import (
    sample_dict_values,
    sample_list,
    truncate_nested_strings,
)


class TestSampleDictValues:
    def test_under_limit(self):
        data = {"a": 1, "b": 2, "c": 3}
        result = sample_dict_values(data, max_entries=5)
        assert result == data
        assert "_sampled_from" not in result

    def test_over_limit(self):
        data = {f"key_{i}": i for i in range(50)}
        result = sample_dict_values(data, max_entries=10)
        # 10 data keys + 1 metadata key
        assert len(result) == 11
        assert result["_sampled_from"] == 50

    def test_deterministic(self):
        data = {f"key_{i}": i for i in range(50)}
        result1 = sample_dict_values(data, max_entries=10, seed=42)
        result2 = sample_dict_values(data, max_entries=10, seed=42)
        assert result1 == result2

    def test_different_seed(self):
        data = {f"key_{i}": i for i in range(50)}
        result1 = sample_dict_values(data, max_entries=10, seed=42)
        result2 = sample_dict_values(data, max_entries=10, seed=99)
        # Different seeds should (very likely) produce different samples
        keys1 = {k for k in result1 if k != "_sampled_from"}
        keys2 = {k for k in result2 if k != "_sampled_from"}
        assert keys1 != keys2


class TestSampleList:
    def test_under_limit(self):
        items = [1, 2, 3]
        result = sample_list(items, max_items=10)
        assert result == [1, 2, 3]

    def test_over_limit(self):
        items = list(range(100))
        result = sample_list(items, max_items=20)
        assert len(result) == 21  # 20 items + 1 sentinel
        assert result[-1] == {"_sampled_from": 100}

    def test_deterministic(self):
        items = list(range(100))
        result1 = sample_list(items, max_items=10, seed=42)
        result2 = sample_list(items, max_items=10, seed=42)
        assert result1 == result2


class TestTruncateNestedStrings:
    def test_deep_truncation(self):
        data = {
            "level1": {
                "level2": {
                    "text": "a" * 500,
                    "list": ["b" * 500, "short"],
                }
            }
        }
        result = truncate_nested_strings(data, max_str_len=100)

        inner = result["level1"]["level2"]
        assert len(inner["text"]) == 100 + len("…[trimmed]")
        assert inner["text"].endswith("…[trimmed]")
        assert len(inner["list"][0]) == 100 + len("…[trimmed]")
        assert inner["list"][1] == "short"

    def test_short_strings_unchanged(self):
        data = {"key": "hello"}
        result = truncate_nested_strings(data, max_str_len=300)
        assert result == {"key": "hello"}

    def test_scalars_preserved(self):
        data = {"count": 42, "rate": 3.14, "active": True, "empty": None}
        result = truncate_nested_strings(data)
        assert result == data

    def test_original_not_mutated(self):
        original_text = "x" * 500
        data = {"text": original_text, "nested": {"inner": "y" * 500}}
        truncate_nested_strings(data, max_str_len=100)
        assert data["text"] == original_text
        assert data["nested"]["inner"] == "y" * 500
