"""Tests for SonarQube analysis tool.

Test structure:
- Unit tests (tests/*.py): Fast tests with mocked dependencies
- Integration tests (tests/integration/*.py): Tests requiring Docker/SonarQube

Run unit tests only:
    pytest tests/ -m "not integration"

Run integration tests:
    pytest tests/ -m integration

Run all tests:
    pytest tests/
"""
