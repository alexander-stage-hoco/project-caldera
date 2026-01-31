"""Pytest fixtures for scc unit tests."""

import pytest
import sys
from pathlib import Path

# Add scripts to path for imports
scripts_path = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))


@pytest.fixture
def sample_scc_output():
    """Sample scc JSON output for testing."""
    return [
        {
            "Name": "Python",
            "Count": 3,
            "Lines": 100,
            "Code": 80,
            "Comment": 10,
            "Blank": 10,
            "Complexity": 5,
            "Bytes": 2500,
        },
        {
            "Name": "JavaScript",
            "Count": 2,
            "Lines": 50,
            "Code": 40,
            "Comment": 5,
            "Blank": 5,
            "Complexity": 3,
            "Bytes": 1200,
        },
    ]


@pytest.fixture
def sample_file_metrics():
    """Sample per-file metrics for testing."""
    return [
        {
            "path": "src/main.py",
            "language": "Python",
            "lines": 50,
            "code": 40,
            "comment": 5,
            "blank": 5,
            "complexity": 3,
        },
        {
            "path": "src/utils.py",
            "language": "Python",
            "lines": 30,
            "code": 25,
            "comment": 3,
            "blank": 2,
            "complexity": 2,
        },
        {
            "path": "tests/test_main.py",
            "language": "Python",
            "lines": 20,
            "code": 15,
            "comment": 2,
            "blank": 3,
            "complexity": 0,
        },
    ]


@pytest.fixture
def sample_directory_stats():
    """Sample directory statistics for testing."""
    return [
        {
            "path": "src",
            "direct": {
                "file_count": 2,
                "loc": 65,
                "complexity": 5,
            },
            "recursive": {
                "file_count": 2,
                "loc": 65,
                "complexity": 5,
            },
        },
        {
            "path": "tests",
            "direct": {
                "file_count": 1,
                "loc": 15,
                "complexity": 0,
            },
            "recursive": {
                "file_count": 1,
                "loc": 15,
                "complexity": 0,
            },
        },
    ]


@pytest.fixture
def sample_distribution_values():
    """Sample values for distribution statistics testing."""
    return [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
