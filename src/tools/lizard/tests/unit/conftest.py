"""Pytest fixtures for lizard unit tests."""

import sys
from pathlib import Path

import pytest

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))


@pytest.fixture
def sample_ccn_values():
    """Sample CCN values for distribution testing."""
    return [1, 1, 1, 2, 3, 5, 8, 10, 15, 25]


@pytest.fixture
def equal_distribution_values():
    """Values representing perfect equality (all same)."""
    return [5, 5, 5, 5, 5]


@pytest.fixture
def unequal_distribution_values():
    """Values representing high inequality."""
    return [1, 1, 1, 1, 1, 1, 1, 1, 1, 100]


@pytest.fixture
def sample_function_info():
    """Sample FunctionInfo for testing."""
    from function_analyzer import FunctionInfo
    return FunctionInfo(
        name="process_data",
        long_name="DataProcessor.process_data",
        start_line=10,
        end_line=50,
        nloc=35,
        ccn=8,
        token_count=120,
        parameter_count=3,
        length=40,
    )


@pytest.fixture
def sample_file_info(sample_function_info):
    """Sample FileInfo for testing."""
    from function_analyzer import FileInfo, FunctionInfo

    functions = [
        sample_function_info,
        FunctionInfo(
            name="validate",
            long_name="DataProcessor.validate",
            start_line=55,
            end_line=70,
            nloc=12,
            ccn=4,
            token_count=45,
            parameter_count=1,
            length=15,
        ),
    ]

    return FileInfo(
        path="/src/processor.py",
        language="Python",
        nloc=47,
        functions=functions,
        function_count=2,
        total_ccn=12,
        avg_ccn=6.0,
        max_ccn=8,
    )


@pytest.fixture
def sample_analysis_result(sample_file_info):
    """Sample AnalysisResult for testing."""
    from function_analyzer import AnalysisResult, AnalysisSummary, Distribution

    return AnalysisResult(
        schema_version="2.0.0",
        run_id="test-run-001",
        timestamp="2026-01-20T12:00:00Z",
        root_path="/test/repo",
        files=[sample_file_info],
        summary=AnalysisSummary(
            total_files=1,
            total_functions=2,
            total_nloc=47,
            total_ccn=12,
            avg_ccn=6.0,
            max_ccn=8,
            functions_over_threshold=0,
            ccn_threshold=10,
        ),
        by_language={"Python": {"files": 1, "functions": 2, "nloc": 47, "ccn": 12}},
    )
