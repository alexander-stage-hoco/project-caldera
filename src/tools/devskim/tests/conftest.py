"""Pytest configuration for DevSkim tests."""

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may require DevSkim binary)"
    )
