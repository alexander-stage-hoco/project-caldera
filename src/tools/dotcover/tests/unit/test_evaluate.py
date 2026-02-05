"""Unit tests for dotcover evaluate script."""

from __future__ import annotations

import pytest


def test_check_loading():
    """Test that check modules load correctly."""
    from scripts.evaluate import load_checks
    checks = load_checks()
    assert len(checks) > 0


def test_summary_computation():
    """Test summary statistics computation."""
    from scripts.evaluate import compute_summary

    results = [
        {"check_id": "test.a", "status": "pass"},
        {"check_id": "test.b", "status": "fail"},
    ]
    summary = compute_summary(results)
    assert summary["total"] == 2
    assert summary["passed"] == 1
    assert summary["failed"] == 1
