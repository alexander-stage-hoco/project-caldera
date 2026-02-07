"""Pytest configuration and shared fixtures for Lizard PoC tests."""

import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# Add lizard tool root, scripts, and shared src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))  # lizard tool root
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


@pytest.fixture
def sample_analysis() -> Dict[str, Any]:
    """Sample analysis result for testing."""
    return {
        "schema_version": "2.0.0",
        "run_id": "fn-20260104-120000",
        "timestamp": "2026-01-04T12:00:00Z",
        "root_path": "eval-repos/synthetic",
        "files": [
            {
                "path": "eval-repos/synthetic/python/simple.py",
                "language": "Python",
                "nloc": 100,
                "function_count": 5,
                "total_ccn": 8,
                "avg_ccn": 1.6,
                "max_ccn": 3,
                "functions": [
                    {"name": "greet", "ccn": 1, "nloc": 3, "parameter_count": 1, "start_line": 10, "end_line": 12},
                    {"name": "add", "ccn": 1, "nloc": 2, "parameter_count": 2, "start_line": 15, "end_line": 16},
                    {"name": "is_valid", "ccn": 3, "nloc": 5, "parameter_count": 1, "start_line": 20, "end_line": 24},
                    {"name": "User.greet", "ccn": 1, "nloc": 3, "parameter_count": 1, "start_line": 30, "end_line": 32},
                    {"name": "(anonymous)", "ccn": 2, "nloc": 3, "parameter_count": 0, "start_line": 40, "end_line": 42},
                ],
            },
            {
                "path": "eval-repos/synthetic/python/complex.py",
                "language": "Python",
                "nloc": 200,
                "function_count": 3,
                "total_ccn": 28,
                "avg_ccn": 9.3,
                "max_ccn": 15,
                "functions": [
                    {"name": "process_data", "ccn": 15, "nloc": 45, "parameter_count": 3, "start_line": 10, "end_line": 54},
                    {"name": "validate", "ccn": 8, "nloc": 20, "parameter_count": 2, "start_line": 60, "end_line": 79},
                    {"name": "helper", "ccn": 5, "nloc": 10, "parameter_count": 1, "start_line": 85, "end_line": 94},
                ],
            },
            {
                "path": "eval-repos/synthetic/python/edge_cases/empty.py",
                "language": "Python",
                "nloc": 0,
                "function_count": 0,
                "total_ccn": 0,
                "avg_ccn": 0,
                "max_ccn": 0,
                "functions": [],
            },
            {
                "path": "eval-repos/synthetic/csharp/simple.cs",
                "language": "C#",
                "nloc": 80,
                "function_count": 4,
                "total_ccn": 6,
                "avg_ccn": 1.5,
                "max_ccn": 2,
                "functions": [
                    {"name": "Greet", "ccn": 1, "nloc": 3, "parameter_count": 1, "start_line": 10, "end_line": 12},
                    {"name": "Add", "ccn": 1, "nloc": 2, "parameter_count": 2, "start_line": 15, "end_line": 16},
                    {"name": "IsValid", "ccn": 2, "nloc": 5, "parameter_count": 1, "start_line": 20, "end_line": 24},
                    {"name": "User.Greet", "ccn": 2, "nloc": 4, "parameter_count": 0, "start_line": 30, "end_line": 33},
                ],
            },
        ],
        "summary": {
            "total_files": 4,
            "total_functions": 12,
            "total_nloc": 380,
            "total_ccn": 42,
            "avg_ccn": 3.5,
            "max_ccn": 15,
            "functions_over_threshold": 1,
            "by_language": {
                "Python": {
                    "file_count": 3,
                    "function_count": 8,
                    "total_nloc": 300,
                    "total_ccn": 36,
                    "avg_ccn": 4.5,
                    "max_ccn": 15,
                },
                "C#": {
                    "file_count": 1,
                    "function_count": 4,
                    "total_nloc": 80,
                    "total_ccn": 6,
                    "avg_ccn": 1.5,
                    "max_ccn": 2,
                },
            },
        },
    }


@pytest.fixture
def sample_ground_truth() -> Dict[str, Any]:
    """Sample ground truth for testing."""
    return {
        "language": "python",
        "generated_at": "2026-01-04T12:00:00Z",
        "lizard_version": "lizard 1.19.0",
        "total_files": 3,
        "total_functions": 8,
        "total_ccn": 36,
        "files": {
            "simple.py": {
                "expected_functions": 5,
                "total_ccn": 8,
                "functions": {
                    "greet": {"ccn": 1, "nloc": 3, "params": 1, "start_line": 10, "end_line": 12},
                    "add": {"ccn": 1, "nloc": 2, "params": 2, "start_line": 15, "end_line": 16},
                    "is_valid": {"ccn": 3, "nloc": 5, "params": 1, "start_line": 20, "end_line": 24},
                    "User.greet": {"ccn": 1, "nloc": 3, "params": 1, "start_line": 30, "end_line": 32},
                    "(anonymous)": {"ccn": 2, "nloc": 3, "params": 0, "start_line": 40, "end_line": 42},
                },
            },
            "complex.py": {
                "expected_functions": 3,
                "total_ccn": 28,
                "functions": {
                    "process_data": {"ccn": 15, "nloc": 45, "params": 3, "start_line": 10, "end_line": 54},
                    "validate": {"ccn": 8, "nloc": 20, "params": 2, "start_line": 60, "end_line": 79},
                    "helper": {"ccn": 5, "nloc": 10, "params": 1, "start_line": 85, "end_line": 94},
                },
            },
            "edge_cases/empty.py": {
                "expected_functions": 0,
                "total_ccn": 0,
                "functions": {},
            },
        },
    }


@pytest.fixture
def multi_language_analysis(sample_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Analysis with all 7 languages represented."""
    analysis = sample_analysis.copy()

    # Add files for remaining languages
    extra_files = [
        {"path": "eval-repos/synthetic/java/simple.java", "language": "Java", "functions": [{"name": "main", "ccn": 1}]},
        {"path": "eval-repos/synthetic/javascript/simple.js", "language": "JavaScript", "functions": [{"name": "greet", "ccn": 1}]},
        {"path": "eval-repos/synthetic/typescript/simple.ts", "language": "TypeScript", "functions": [{"name": "greet", "ccn": 1}]},
        {"path": "eval-repos/synthetic/go/simple.go", "language": "Go", "functions": [{"name": "main", "ccn": 1}]},
        {"path": "eval-repos/synthetic/rust/simple.rs", "language": "Rust", "functions": [{"name": "main", "ccn": 1}]},
    ]

    analysis["files"].extend(extra_files)
    analysis["summary"]["by_language"].update({
        "Java": {"file_count": 1, "function_count": 1},
        "JavaScript": {"file_count": 1, "function_count": 1},
        "TypeScript": {"file_count": 1, "function_count": 1},
        "Go": {"file_count": 1, "function_count": 1},
        "Rust": {"file_count": 1, "function_count": 1},
    })

    return analysis
