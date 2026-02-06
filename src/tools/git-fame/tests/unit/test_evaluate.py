"""Unit tests for git-fame evaluate script."""

from __future__ import annotations

import pytest


def test_calculate_dimension_score():
    """Test dimension score calculation."""
    from scripts.evaluate import calculate_dimension_score

    # All passed
    results = [{"passed": True}, {"passed": True}, {"passed": True}]
    assert calculate_dimension_score(results) == 5.0

    # Half passed
    results = [{"passed": True}, {"passed": False}]
    assert calculate_dimension_score(results) == 2.5

    # None passed
    results = [{"passed": False}, {"passed": False}]
    assert calculate_dimension_score(results) == 0.0

    # Empty list
    assert calculate_dimension_score([]) == 0.0


def test_classify_score():
    """Test score classification."""
    from scripts.evaluate import classify_score

    assert classify_score(5.0) == "STRONG_PASS"
    assert classify_score(4.5) == "STRONG_PASS"
    assert classify_score(4.0) == "PASS"
    assert classify_score(3.5) == "MARGINAL_PASS"
    assert classify_score(3.0) == "MARGINAL_FAIL"
    assert classify_score(2.5) == "FAIL"
