"""Shared fixtures for LLM evaluation tests.

All fixtures use REAL data from the output/ directory - NO MOCKING.
LLM calls use mock responses in test mode unless explicitly disabled.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


# Path to the poc-scc root directory
POC_ROOT = Path(__file__).parent.parent.parent.parent


@pytest.fixture
def poc_root() -> Path:
    """Return the poc-scc root directory."""
    return POC_ROOT


@pytest.fixture
def output_dir(poc_root: Path) -> Path:
    """Return the output directory."""
    outputs_root = poc_root / "outputs"
    if outputs_root.exists():
        candidates = [
            p for p in outputs_root.iterdir()
            if p.is_dir() and (p / "output.json").exists()
        ]
        if candidates:
            return max(candidates, key=lambda p: p.stat().st_mtime)
    return poc_root / "output"


@pytest.fixture
def evaluation_dir(poc_root: Path) -> Path:
    """Return the evaluation directory."""
    return poc_root / "evaluation"


@pytest.fixture
def llm_eval_dir(evaluation_dir: Path) -> Path:
    """Return the LLM evaluation directory."""
    return evaluation_dir / "llm"


# Test mode fixtures for LLM invocation

@pytest.fixture(autouse=True)
def set_test_mode(monkeypatch):
    """Enable test mode for LLM judges to avoid real API calls in unit tests.

    This fixture is autouse=True so all tests automatically use mock Claude responses.
    For integration tests that should use real Claude, use the `real_claude_mode` fixture.
    """
    monkeypatch.setenv("SCC_TEST_MODE", "1")


@pytest.fixture
def real_claude_mode(monkeypatch):
    """Use real Claude for integration tests.

    Use this fixture when you need actual Claude API responses.
    Example:
        def test_real_evaluation(real_claude_mode, ...):
            # This test will call real Claude
            ...
    """
    monkeypatch.delenv("SCC_TEST_MODE", raising=False)


# Real JSON file fixtures - NO MOCKING

def find_directory_analysis_file(output_dir: Path) -> Path | None:
    """Find directory analysis file in multiple possible locations.

    Checks (in order):
    1. outputs/<run-id>/directory_analysis_eval.json
    2. outputs/<run-id>/directory_analysis.json
    3. output/directory_analysis.json (legacy)
    """
    candidates = [
        output_dir / "directory_analysis_eval.json",
        output_dir / "directory_analysis.json",
        output_dir / "runs" / "synthetic.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


@pytest.fixture
def real_directory_analysis(output_dir: Path) -> dict:
    """Load actual directory analysis from output/.

    This is REAL data from the actual scc analysis.
    Handles both flat and nested (results wrapper) structures.
    Looks for file in multiple locations.
    """
    path = find_directory_analysis_file(output_dir)
    if path is None:
        pytest.skip(
            f"No directory analysis file found in {output_dir}. "
            "Run 'make analyze' first."
        )
    data = json.loads(path.read_text())
    # Handle nested 'results' wrapper structure
    if "results" in data and "directories" not in data:
        return data["results"]
    return data


@pytest.fixture
def real_output(output_dir: Path) -> dict:
    """Load actual output.json from output/.

    This is REAL envelope tool output.
    """
    path = output_dir / "output.json"
    if not path.exists():
        pytest.skip(f"output.json not found at {path}. Run 'make analyze' first.")
    return json.loads(path.read_text())


@pytest.fixture
def real_raw_scc_output(output_dir: Path) -> list:
    """Load actual raw_scc_output.json from output/.

    This is REAL raw scc output.
    """
    path = output_dir / "raw_scc_output.json"
    if not path.exists():
        pytest.skip(f"raw_scc_output.json not found at {path}. Run 'make analyze' first.")
    return json.loads(path.read_text())


@pytest.fixture
def real_raw_scc_full(output_dir: Path) -> list:
    """Load actual raw_scc_full.json from output/.

    This is REAL per-file scc output.
    """
    candidates = [
        output_dir / "raw_scc_full.json",
        output_dir.parent / "raw_scc_full.json",
    ]
    for path in candidates:
        if path.exists():
            return json.loads(path.read_text())
    pytest.skip("raw_scc_full.json not found. Run 'make analyze-full' first.")


@pytest.fixture
def real_evaluation_results(evaluation_dir: Path) -> dict:
    """Load the latest evaluation results from evaluation/results/.

    This is REAL programmatic evaluation data.
    """
    results_dir = evaluation_dir / "results"
    if not results_dir.exists():
        pytest.skip(f"results directory not found at {results_dir}. Run 'make evaluate' first.")

    results_file = results_dir / "evaluation_report.json"
    if not results_file.exists():
        pytest.skip("No evaluation results found. Run 'make evaluate' first.")

    return json.loads(results_file.read_text())


# Extracted fixtures for specific test scenarios

@pytest.fixture
def all_directories(real_directory_analysis: dict) -> list[dict]:
    """Extract all directories from directory analysis."""
    return real_directory_analysis.get("directories", [])


@pytest.fixture
def summary(real_directory_analysis: dict) -> dict:
    """Extract summary from directory analysis."""
    return real_directory_analysis.get("summary", {})


@pytest.fixture
def directories_with_distributions(all_directories: list[dict]) -> list[dict]:
    """Filter directories that have distribution statistics."""
    return [
        d for d in all_directories
        if d.get("recursive", {}).get("loc_distribution")
    ]


@pytest.fixture
def high_complexity_directories(all_directories: list[dict]) -> list[dict]:
    """Filter directories with high average complexity (>15)."""
    return [
        d for d in all_directories
        if d.get("recursive", {}).get("avg_complexity", 0) > 15
    ]


@pytest.fixture
def leaf_directories(all_directories: list[dict]) -> list[dict]:
    """Filter leaf directories (direct == recursive file count)."""
    return [
        d for d in all_directories
        if d.get("direct", {}).get("file_count", 0) == d.get("recursive", {}).get("file_count", 0)
    ]


@pytest.fixture
def empty_directories(all_directories: list[dict]) -> list[dict]:
    """Filter directories with 0 direct files."""
    return [
        d for d in all_directories
        if d.get("direct", {}).get("file_count", 0) == 0
    ]


# Test data generators for edge cases

@pytest.fixture
def valid_directory_entry() -> dict:
    """A valid directory entry for testing."""
    return {
        "path": "test/path",
        "direct": {
            "file_count": 5,
            "lines_code": 500,
            "lines_comment": 50,
            "lines_blank": 30,
            "complexity_total": 25,
            "avg_complexity": 5.0,
            "comment_ratio": 0.0862,
            "dryness": 0.85,
            "complexity_density": 0.05
        },
        "recursive": {
            "file_count": 10,
            "lines_code": 1000,
            "lines_comment": 100,
            "lines_blank": 60,
            "complexity_total": 50,
            "avg_complexity": 5.0,
            "comment_ratio": 0.0862,
            "dryness": 0.85,
            "complexity_density": 0.05,
            "loc_distribution": {
                "min": 20,
                "max": 200,
                "mean": 100,
                "median": 90,
                "stddev": 45,
                "p25": 50,
                "p75": 140,
                "p90": 180,
                "p95": 195,
                "skewness": 0.5,
                "kurtosis": -0.2,
                "cv": 0.45,
                "iqr": 90
            }
        }
    }


@pytest.fixture
def invalid_directory_recursive_lt_direct() -> dict:
    """Invalid: recursive.file_count < direct.file_count."""
    return {
        "path": "invalid/path",
        "direct": {"file_count": 10, "lines_code": 1000},
        "recursive": {"file_count": 5, "lines_code": 500}  # Invalid!
    }


@pytest.fixture
def invalid_directory_negative_ratio() -> dict:
    """Invalid: negative computed ratio."""
    return {
        "path": "invalid/ratio",
        "direct": {"file_count": 5},
        "recursive": {
            "file_count": 10,
            "dryness": -0.5  # Invalid!
        }
    }


@pytest.fixture
def invalid_directory_percentiles() -> dict:
    """Invalid: non-monotonic percentiles."""
    return {
        "path": "invalid/percentiles",
        "direct": {"file_count": 5},
        "recursive": {
            "file_count": 10,
            "loc_distribution": {
                "min": 10,
                "max": 500,
                "mean": 120,
                "median": 85,
                "p25": 100,  # Invalid! > median
                "p75": 50,   # Invalid! < p25
                "p90": 300,
                "p95": 200   # Invalid! < p90
            }
        }
    }


# Marks for test categories

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "claude_api: marks tests that require Claude API access")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
