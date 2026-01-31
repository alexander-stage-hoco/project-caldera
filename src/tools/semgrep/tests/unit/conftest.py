"""Pytest fixtures for semgrep smell analyzer tests."""

import pytest
from dataclasses import dataclass, field
from typing import Any


@pytest.fixture
def sample_semgrep_finding() -> dict[str, Any]:
    """Sample Semgrep finding for testing."""
    return {
        "check_id": "DD-D1-EMPTY-CATCH-python",
        "path": "/tmp/test/src/main.py",
        "start": {"line": 10, "col": 5},
        "end": {"line": 12, "col": 10},
        "extra": {
            "severity": "WARNING",
            "message": "Empty catch block detected",
            "lines": "except Exception:\n    pass",
            "metadata": {
                "dd_smell_id": "D1_EMPTY_CATCH",
                "dd_category": "error_handling",
            },
        },
    }


@pytest.fixture
def sample_security_finding() -> dict[str, Any]:
    """Sample security-related Semgrep finding."""
    return {
        "check_id": "sql-injection-python",
        "path": "src/db/query.py",
        "start": {"line": 25, "col": 1},
        "end": {"line": 25, "col": 50},
        "extra": {
            "severity": "ERROR",
            "message": "Possible SQL injection vulnerability",
            "lines": 'cursor.execute(f"SELECT * FROM users WHERE id={user_id}")',
            "metadata": {},
        },
    }


@pytest.fixture
def sample_file_paths() -> list[str]:
    """Sample file paths for language detection testing."""
    return [
        "main.py",
        "app.js",
        "component.tsx",
        "Service.cs",
        "Handler.java",
        "main.go",
        "lib.rs",
        "script.rb",
        "index.php",
        "unknown.xyz",
    ]


@pytest.fixture
def sample_smell_counts() -> list[float]:
    """Sample smell counts for distribution testing."""
    return [0, 0, 1, 1, 2, 3, 5, 8, 13, 21]


@pytest.fixture
def uniform_smell_counts() -> list[float]:
    """Uniform smell counts for testing Gini = 0."""
    return [5.0, 5.0, 5.0, 5.0, 5.0]


@pytest.fixture
def concentrated_smell_counts() -> list[float]:
    """Highly concentrated smell counts for high Gini."""
    return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 100.0]


@pytest.fixture
def sample_dd_rules() -> list[str]:
    """Sample DD-prefixed rule IDs for mapping tests."""
    return [
        "DD-D1-EMPTY-CATCH-python",
        "DD-D2-CATCH-ALL-csharp",
        "DD-E2-ASYNC-VOID-csharp",
        "DD-F3-HTTPCLIENT-NEW-csharp",
        "DD-H4-BOOLEAN-BLINDNESS-java",
        "DD-I1-UNUSED-IMPORT-python",
    ]


@pytest.fixture
def sample_security_rules() -> list[str]:
    """Sample security rule IDs for mapping tests."""
    return [
        "sql-injection",
        "xss",
        "path-traversal",
        "hardcoded-secret",
        "command-injection",
        "SCS0002",  # SQL Injection
        "CA3001",  # SQL Injection
        "CWE-89",  # SQL Injection
    ]
