"""Tests for prompt_guard module."""

from __future__ import annotations

import warnings

import pytest

from shared.llm.prompt_guard import (
    CHARS_PER_TOKEN,
    DEFAULT_MAX_PROMPT_CHARS,
    check_prompt_size,
    estimate_tokens,
    guard_prompt,
)


class TestEstimateTokens:
    def test_basic_estimation(self):
        text = "a" * 350
        assert estimate_tokens(text) == int(350 / CHARS_PER_TOKEN)

    def test_empty_string(self):
        assert estimate_tokens("") == 0

    def test_returns_int(self):
        assert isinstance(estimate_tokens("hello world"), int)


class TestCheckPromptSize:
    def test_within_limit_returns_unchanged(self):
        prompt = "short prompt"
        result, was_truncated = check_prompt_size(prompt)
        assert result == prompt
        assert was_truncated is False

    def test_exceeds_limit_returns_truncated(self):
        prompt = "x" * 200
        result, was_truncated = check_prompt_size(prompt, max_chars=100)
        assert was_truncated is True
        assert len(result) <= 100  # result fits within max_chars
        assert "[INPUT TRUNCATED" in result

    def test_exact_limit_not_truncated(self):
        prompt = "x" * 100
        result, was_truncated = check_prompt_size(prompt, max_chars=100)
        assert result == prompt
        assert was_truncated is False

    def test_custom_limit(self):
        prompt = "x" * 50
        result, was_truncated = check_prompt_size(prompt, max_chars=30)
        assert was_truncated is True
        assert "[INPUT TRUNCATED" in result
        assert len(result) < len(prompt)  # strictly shorter than original

    def test_truncation_marker_content(self):
        prompt = "x" * 200
        result, _ = check_prompt_size(prompt, max_chars=100)
        assert "exceeded 100 chars" in result


class TestGuardPrompt:
    def test_within_limit_no_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = guard_prompt("short", max_chars=1000)
            assert result == "short"
            assert len(w) == 0

    def test_exceeds_limit_emits_warning(self):
        prompt = "x" * 200
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = guard_prompt(prompt, max_chars=100, context="TestCtx")
            assert "[INPUT TRUNCATED" in result
            assert len(w) == 1
            assert "TestCtx" in str(w[0].message)
            assert "200" in str(w[0].message)
            assert "100" in str(w[0].message)

    def test_none_max_chars_uses_default(self):
        # A prompt under the default limit should pass through
        prompt = "hello"
        result = guard_prompt(prompt, max_chars=None)
        assert result == prompt

    def test_default_max_is_100k(self):
        assert DEFAULT_MAX_PROMPT_CHARS == 100_000
