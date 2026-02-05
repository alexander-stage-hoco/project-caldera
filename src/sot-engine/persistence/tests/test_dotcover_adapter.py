"""Tests for dotcover adapter.

For implementation examples, see:
- persistence/tests/test_scc_adapter.py
- persistence/tests/test_semgrep_adapter.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pytest

from persistence.adapters.dotcover_adapter import DotcoverAdapter, SCHEMA_PATH
from persistence.entities import (
    DotcoverAssemblyCoverage,
    DotcoverMethodCoverage,
    DotcoverTypeCoverage,
)
from persistence.repositories import (
    DotcoverRepository,
    LayoutRepository,
    ToolRunRepository,
)


@pytest.fixture
def in_memory_db():
    """Create in-memory DuckDB with schema."""
    conn = duckdb.connect(":memory:")
    schema_path = Path(__file__).resolve().parents[2] / "schema.sql"
    conn.execute(schema_path.read_text())
    return conn


@pytest.fixture
def sample_payload() -> dict:
    """Create a minimal valid payload for testing."""
    return {
        "metadata": {
            "tool_name": "dotcover",
            "tool_version": "2025.3.2",
            "run_id": "test-run-id",
            "repo_id": "test-repo-id",
            "branch": "main",
            "commit": "a" * 40,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "dotcover",
            "tool_version": "2025.3.2",
            "summary": {
                "total_assemblies": 1,
                "total_types": 2,
                "total_methods": 3,
                "covered_statements": 50,
                "total_statements": 100,
                "statement_coverage_pct": 50.0,
            },
            "assemblies": [
                {
                    "name": "MyApp.Services",
                    "covered_statements": 50,
                    "total_statements": 100,
                    "statement_coverage_pct": 50.0,
                },
            ],
            "types": [
                {
                    "assembly": "MyApp.Services",
                    "namespace": "MyApp.Services.Users",
                    "name": "UserService",
                    "file_path": None,
                    "covered_statements": 30,
                    "total_statements": 60,
                    "statement_coverage_pct": 50.0,
                },
                {
                    "assembly": "MyApp.Services",
                    "namespace": "MyApp.Services.Auth",
                    "name": "AuthService",
                    "file_path": None,
                    "covered_statements": 20,
                    "total_statements": 40,
                    "statement_coverage_pct": 50.0,
                },
            ],
            "methods": [
                {
                    "assembly": "MyApp.Services",
                    "type_name": "UserService",
                    "name": "GetUser(int)",
                    "covered_statements": 18,
                    "total_statements": 20,
                    "statement_coverage_pct": 90.0,
                },
                {
                    "assembly": "MyApp.Services",
                    "type_name": "UserService",
                    "name": "CreateUser(string)",
                    "covered_statements": 12,
                    "total_statements": 40,
                    "statement_coverage_pct": 30.0,
                },
                {
                    "assembly": "MyApp.Services",
                    "type_name": "AuthService",
                    "name": "Login(string, string)",
                    "covered_statements": 20,
                    "total_statements": 40,
                    "statement_coverage_pct": 50.0,
                },
            ],
        },
    }


def test_adapter_schema_path_exists():
    """Verify the schema path is correctly configured."""
    assert SCHEMA_PATH.exists(), f"Schema not found at {SCHEMA_PATH}"


def test_adapter_validate_quality_valid():
    """Test data quality validation with valid data."""
    adapter = DotcoverAdapter(
        run_repo=None,
        layout_repo=None,
        dotcover_repo=None,
    )

    # Should not raise
    adapter.validate_quality([
        {
            "name": "MyAssembly",
            "covered_statements": 50,
            "total_statements": 100,
            "statement_coverage_pct": 50.0,
        },
    ], "assembly")


def test_adapter_validate_quality_invalid_coverage():
    """Test validation catches covered > total."""
    adapter = DotcoverAdapter(
        run_repo=None,
        layout_repo=None,
        dotcover_repo=None,
    )

    with pytest.raises(ValueError, match="data quality validation failed"):
        adapter.validate_quality([
            {
                "name": "BadAssembly",
                "covered_statements": 150,  # > total
                "total_statements": 100,
                "statement_coverage_pct": 150.0,
            },
        ], "assembly")


def test_adapter_validate_quality_invalid_percentage():
    """Test validation catches invalid coverage percentage."""
    adapter = DotcoverAdapter(
        run_repo=None,
        layout_repo=None,
        dotcover_repo=None,
    )

    with pytest.raises(ValueError, match="data quality validation failed"):
        adapter.validate_quality([
            {
                "name": "BadAssembly",
                "covered_statements": 50,
                "total_statements": 100,
                "statement_coverage_pct": 150.0,  # > 100
            },
        ], "assembly")


def test_adapter_validate_quality_missing_required():
    """Test validation catches missing required fields."""
    adapter = DotcoverAdapter(
        run_repo=None,
        layout_repo=None,
        dotcover_repo=None,
    )

    with pytest.raises(ValueError, match="data quality validation failed"):
        adapter.validate_quality([
            {
                # Missing "name"
                "covered_statements": 50,
                "total_statements": 100,
                "statement_coverage_pct": 50.0,
            },
        ], "assembly")


def test_entity_validation():
    """Test entity validation for coverage invariants."""
    # Valid entity
    entity = DotcoverAssemblyCoverage(
        run_pk=1,
        assembly_name="MyApp",
        covered_statements=50,
        total_statements=100,
        statement_coverage_pct=50.0,
    )
    assert entity.assembly_name == "MyApp"

    # Invalid: covered > total (percentage in valid range)
    with pytest.raises(ValueError, match="covered_statements cannot exceed"):
        DotcoverAssemblyCoverage(
            run_pk=1,
            assembly_name="MyApp",
            covered_statements=150,
            total_statements=100,
            statement_coverage_pct=50.0,  # valid percentage to test coverage invariant
        )

    # Invalid: percentage out of range
    with pytest.raises(ValueError, match="statement_coverage_pct must be between"):
        DotcoverAssemblyCoverage(
            run_pk=1,
            assembly_name="MyApp",
            covered_statements=50,
            total_statements=100,
            statement_coverage_pct=150.0,
        )


def test_type_coverage_entity():
    """Test type coverage entity with optional file path."""
    # With file path
    entity = DotcoverTypeCoverage(
        run_pk=1,
        file_id="file-123",
        directory_id="dir-123",
        relative_path="src/Services/UserService.cs",
        assembly_name="MyApp.Services",
        namespace="MyApp.Services.Users",
        type_name="UserService",
        covered_statements=30,
        total_statements=60,
        statement_coverage_pct=50.0,
    )
    assert entity.relative_path == "src/Services/UserService.cs"

    # Without file path (None is valid)
    entity_no_file = DotcoverTypeCoverage(
        run_pk=1,
        file_id=None,
        directory_id=None,
        relative_path=None,
        assembly_name="MyApp.Services",
        namespace="MyApp.Services.Users",
        type_name="UserService",
        covered_statements=30,
        total_statements=60,
        statement_coverage_pct=50.0,
    )
    assert entity_no_file.file_id is None


def test_method_coverage_entity():
    """Test method coverage entity validation."""
    entity = DotcoverMethodCoverage(
        run_pk=1,
        assembly_name="MyApp.Services",
        type_name="UserService",
        method_name="GetUser(int)",
        covered_statements=18,
        total_statements=20,
        statement_coverage_pct=90.0,
    )
    assert entity.method_name == "GetUser(int)"
