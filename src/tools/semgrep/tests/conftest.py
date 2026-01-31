"""Shared pytest configuration and fixtures for semgrep tests.

This file provides:
- Marker registration (llm, slow)
- Shared fixtures for LLM judge testing
- Helper utilities for test setup
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

import pytest

# Try to import LLM judge components
try:
    from evaluation.llm.judges.base import HAS_ANTHROPIC_SDK
except ImportError:
    HAS_ANTHROPIC_SDK = False


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "llm: marks tests that require LLM access (ANTHROPIC_API_KEY or claude CLI)"
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (may take >30s to complete)"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on markers and environment."""
    # Check if LLM is available
    llm_available = (
        (HAS_ANTHROPIC_SDK and os.environ.get("ANTHROPIC_API_KEY"))
        or shutil.which("claude") is not None
    )

    skip_llm = pytest.mark.skip(
        reason="LLM not available (need ANTHROPIC_API_KEY or claude CLI)"
    )
    skip_slow = pytest.mark.skip(reason="Slow tests disabled (use --run-slow to enable)")

    for item in items:
        # Skip LLM tests if LLM not available
        if "llm" in item.keywords and not llm_available:
            item.add_marker(skip_llm)

        # Skip slow tests unless explicitly enabled
        if "slow" in item.keywords and not config.getoption("--run-slow", default=False):
            item.add_marker(skip_slow)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow tests (LLM integration tests that may take >30s)"
    )


@pytest.fixture
def claude_cli_available() -> bool:
    """Check if Claude CLI is available."""
    return shutil.which("claude") is not None


@pytest.fixture
def anthropic_sdk_available() -> bool:
    """Check if Anthropic SDK is available with API key."""
    return HAS_ANTHROPIC_SDK and bool(os.environ.get("ANTHROPIC_API_KEY"))


@pytest.fixture
def llm_available(claude_cli_available: bool, anthropic_sdk_available: bool) -> bool:
    """Check if any LLM invocation method is available."""
    return claude_cli_available or anthropic_sdk_available


@pytest.fixture
def mock_claude_response() -> dict[str, Any]:
    """Return a valid mock Claude response for LLM judge tests."""
    return {
        "dimension": "smell_accuracy",
        "score": 4,
        "confidence": 0.85,
        "reasoning": "The smell detection shows good accuracy with most expected patterns correctly identified. Minor gaps in async pattern detection.",
        "evidence_cited": [
            "user_service.py correctly identified D1_EMPTY_CATCH at line 45",
            "helpers.py correctly identified I1_UNUSED_IMPORT at line 5",
            "test_no_smell_clean.py correctly has 0 smells",
        ],
        "recommendations": [
            "Add rules for async/await patterns in Python",
            "Consider adding more resource management rules",
        ],
        "sub_scores": {
            "true_positives": 4,
            "category_accuracy": 5,
            "location_accuracy": 4,
        },
    }


@pytest.fixture
def mock_claude_response_json(mock_claude_response: dict[str, Any]) -> str:
    """Return mock response as JSON string wrapped in markdown."""
    return f"""Based on my analysis of the evidence provided, here is my evaluation:

```json
{json.dumps(mock_claude_response, indent=2)}
```

This evaluation reflects the overall quality of smell detection observed in the analysis output."""


@pytest.fixture
def sample_analysis_data() -> dict[str, Any]:
    """Return sample analysis data for testing."""
    return {
        "files": [
            {
                "path": "src/main.py",
                "language": "python",
                "smell_count": 2,
                "smells": [
                    {
                        "rule_id": "DD-D1-EMPTY-CATCH-python",
                        "dd_smell_id": "D1_EMPTY_CATCH",
                        "dd_category": "error_handling",
                        "severity": "WARNING",
                        "line_start": 10,
                        "line_end": 12,
                        "message": "Empty catch block detected",
                    },
                    {
                        "rule_id": "DD-E2-ASYNC-VOID-python",
                        "dd_smell_id": "E2_ASYNC_VOID",
                        "dd_category": "async_concurrency",
                        "severity": "WARNING",
                        "line_start": 25,
                        "line_end": 30,
                        "message": "Async method returns void",
                    },
                ],
            },
            {
                "path": "tests/test_no_smell_clean.py",
                "language": "python",
                "smell_count": 0,
                "smells": [],
            },
        ],
        "summary": {
            "total_smells": 2,
            "total_files": 2,
            "files_with_smells": 1,
        },
    }


@pytest.fixture
def sample_ground_truth() -> dict[str, Any]:
    """Return sample ground truth data for testing."""
    return {
        "language": "python",
        "files": {
            "main.py": {
                "expected_smells": ["D1_EMPTY_CATCH", "E2_ASYNC_VOID"],
                "expected_count_min": 1,
                "expected_count_max": 5,
            },
            "test_no_smell_clean.py": {
                "expected_smells": [],
                "expected_count_min": 0,
                "expected_count_max": 0,
            },
        },
    }


@pytest.fixture
def temp_semgrep_output(
    tmp_path: Path,
    sample_analysis_data: dict[str, Any],
    sample_ground_truth: dict[str, Any],
) -> Path:
    """Create a temporary directory with analysis output and ground truth."""
    # Create output directory
    output_dir = tmp_path / "output" / "runs"
    output_dir.mkdir(parents=True)
    (output_dir / "test_repo.json").write_text(json.dumps(sample_analysis_data, indent=2))

    # Create ground truth directory
    gt_dir = tmp_path / "evaluation" / "ground-truth"
    gt_dir.mkdir(parents=True)
    (gt_dir / "python.json").write_text(json.dumps(sample_ground_truth, indent=2))

    return tmp_path
