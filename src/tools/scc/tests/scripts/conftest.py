"""Fixtures for directory_analyzer tests.

All fixtures use REAL data - NO MOCKING.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from directory_analyzer import (
    COCOMO_PRESETS,
    MetricDistribution,
    analyze_directories,
    compute_cocomo,
    compute_directory_stats,
    compute_kurtosis,
    compute_skewness,
)


@pytest.fixture
def poc_root() -> Path:
    """Return the poc-scc root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def real_directory_analysis(poc_root) -> dict:
    """Load actual output/directory_analysis_eval.json."""
    outputs_root = poc_root / "outputs"
    candidates = []
    if outputs_root.exists():
        candidates.extend(outputs_root.glob("*/directory_analysis_eval.json"))
    candidates.append(poc_root / "output" / "directory_analysis_eval.json")

    for path in candidates:
        if path.exists():
            return json.loads(path.read_text())

    pytest.skip("Real output not found: run 'make analyze' first.")


@pytest.fixture
def all_directories(real_directory_analysis) -> list:
    """All directories from real output."""
    return real_directory_analysis.get("directories", [])


@pytest.fixture
def summary(real_directory_analysis) -> dict:
    """Summary from real output."""
    return real_directory_analysis.get("summary", {})


@pytest.fixture
def directories_with_distributions(all_directories) -> list:
    """Directories that have distribution stats."""
    return [
        d for d in all_directories
        if d.get("recursive", {}).get("loc_distribution")
    ]


def make_stats(
    file_count: int = 10,
    complexity_total: int = 50,
    lines_code: int = 1000,
    lines_total: int = 1200,
    lines_comment: int = 100,
    lines_blank: int = 100,
    bytes_total: int = 50000,
    uloc: int = 800,
    languages: dict = None,
    distribution: dict = None,
) -> dict:
    """Create a stats dict for testing compute_directory_stats."""
    return {
        "file_count": file_count,
        "lines_total": lines_total,
        "lines_code": lines_code,
        "lines_comment": lines_comment,
        "lines_blank": lines_blank,
        "bytes": bytes_total,
        "complexity_total": complexity_total,
        "uloc": uloc,
        "languages": languages or {"Python": file_count},
        "minified_count": 0,
        "generated_count": 0,
        "distribution": distribution,
    }


def make_file(
    location: str,
    code: int = 100,
    lines: int = 120,
    comment: int = 10,
    blank: int = 10,
    complexity: int = 5,
    language: str = "Python",
) -> dict:
    """Create a file dict for testing."""
    return {
        "Location": location,
        "Filename": Path(location).name,
        "Language": language,
        "Lines": lines,
        "Code": code,
        "Comment": comment,
        "Blank": blank,
        "Bytes": code * 50,
        "Complexity": complexity,
        "Uloc": int(code * 0.8),
        "Minified": False,
        "Generated": False,
    }


def generate_test_files(count: int = 20, max_depth: int = 3) -> list:
    """Generate test files with various directory depths."""
    files = []
    dirs = ["src", "src/utils", "src/utils/helpers", "src/core", "tests"]

    for i in range(count):
        dir_idx = i % len(dirs)
        parent = dirs[min(dir_idx, max_depth)]
        files.append(make_file(
            location=f"{parent}/file_{i}.py",
            code=50 + (i * 10),
            complexity=2 + (i % 10),
        ))

    return files
