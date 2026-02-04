"""Pytest configuration and shared fixtures for PMD CPD tests."""

import pytest
import sys
from pathlib import Path

# Add tool root to path for imports (enables: evaluation.llm.judges, scripts, etc.)
tool_root_path = Path(__file__).parent.parent
sys.path.insert(0, str(tool_root_path))

# Also add scripts directory for backward compatibility
scripts_dir = tool_root_path / "scripts"
sys.path.insert(0, str(scripts_dir))


@pytest.fixture
def tool_root():
    """Return the PMD CPD tool root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def ground_truth_dir(tool_root):
    """Return the ground truth directory path."""
    return tool_root / "evaluation" / "ground-truth"


@pytest.fixture
def synthetic_repos_dir(tool_root):
    """Return the synthetic test repos directory path."""
    return tool_root / "eval-repos" / "synthetic"


@pytest.fixture
def sample_analysis():
    """Provide a sample analysis result for testing."""
    return {
        "metadata": {
            "version": "1.0",
            "cpd_version": "7.0.0",
            "min_tokens": 100,
            "ignore_identifiers": False,
            "ignore_literals": False,
        },
        "summary": {
            "total_files": 10,
            "total_clones": 3,
            "duplication_percentage": 15.5,
            "cross_file_clones": 1,
        },
        "files": [
            {
                "path": "src/main.py",
                "total_lines": 100,
                "duplicate_lines": 20,
                "duplicate_blocks": 2,
                "duplication_percentage": 20.0,
                "language": "python",
            },
            {
                "path": "src/utils.py",
                "total_lines": 50,
                "duplicate_lines": 10,
                "duplicate_blocks": 1,
                "duplication_percentage": 20.0,
                "language": "python",
            },
        ],
        "duplications": [
            {
                "clone_id": "CPD-0001",
                "lines": 15,
                "tokens": 100,
                "occurrences": [
                    {"file": "src/main.py", "line_start": 10, "line_end": 24},
                    {"file": "src/main.py", "line_start": 50, "line_end": 64},
                ],
                "code_fragment": "def example():\n    pass",
            },
            {
                "clone_id": "CPD-0002",
                "lines": 10,
                "tokens": 75,
                "occurrences": [
                    {"file": "src/main.py", "line_start": 80, "line_end": 89},
                    {"file": "src/utils.py", "line_start": 20, "line_end": 29},
                ],
                "code_fragment": "def another():\n    pass",
            },
        ],
        "statistics": {
            "cross_file_clones": 1,
            "total_tokens": 175,
            "total_duplicate_lines": 25,
            "by_language": {
                "python": {"clone_count": 3, "total_lines": 25}
            },
        },
        "errors": [],
    }
