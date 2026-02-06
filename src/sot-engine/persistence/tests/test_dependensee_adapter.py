"""Tests for dependensee adapter.

Dependensee analyzes .NET project dependencies:
- Project-to-project references
- NuGet package dependencies
- Target framework information
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest

from persistence.adapters.dependensee_adapter import DependenseeAdapter, SCHEMA_PATH
from persistence.entities import (
    DependenseeProject,
    DependenseeProjectReference,
    DependenseePackageReference,
)
from persistence.repositories import (
    LayoutRepository,
    DependenseeRepository,
    ToolRunRepository,
)


@pytest.fixture
def dependensee_repo(duckdb_conn: duckdb.DuckDBPyConnection) -> DependenseeRepository:
    return DependenseeRepository(duckdb_conn)


def test_adapter_schema_path_exists():
    """Verify the schema path is correctly configured."""
    assert SCHEMA_PATH.exists(), f"Schema not found at {SCHEMA_PATH}"


def test_adapter_validate_quality_valid_data(
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    dependensee_repo: DependenseeRepository,
):
    """Test validate_quality accepts valid project data."""
    adapter = DependenseeAdapter(tool_run_repo, layout_repo, dependensee_repo)

    # Valid projects with repo-relative paths
    valid_projects = [
        {
            "name": "MyApp",
            "path": "src/MyApp/MyApp.csproj",
            "target_framework": "net8.0",
            "project_references": ["src/MyApp.Core/MyApp.Core.csproj"],
            "package_references": [{"name": "Newtonsoft.Json", "version": "13.0.3"}],
        }
    ]

    # Should not raise
    adapter.validate_quality(valid_projects)


def test_adapter_validate_quality_rejects_invalid_paths(
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    dependensee_repo: DependenseeRepository,
):
    """Test validate_quality rejects invalid paths after normalization."""
    adapter = DependenseeAdapter(tool_run_repo, layout_repo, dependensee_repo)

    # Paths starting with 'private/' are rejected per is_repo_relative_path
    invalid_projects = [
        {
            "name": "MyApp",
            "path": "/private/var/folders/MyApp.csproj",  # Invalid after normalization
            "project_references": [],
            "package_references": [],
        }
    ]

    with pytest.raises(ValueError, match="data quality validation failed"):
        adapter.validate_quality(invalid_projects)


def test_adapter_validate_quality_rejects_missing_name(
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    dependensee_repo: DependenseeRepository,
):
    """Test validate_quality rejects projects without name."""
    adapter = DependenseeAdapter(tool_run_repo, layout_repo, dependensee_repo)

    invalid_projects = [
        {
            "name": "",  # Invalid: empty name
            "path": "src/MyApp/MyApp.csproj",
            "project_references": [],
            "package_references": [],
        }
    ]

    with pytest.raises(ValueError, match="data quality validation failed"):
        adapter.validate_quality(invalid_projects)


def test_adapter_persist(
    duckdb_conn: duckdb.DuckDBPyConnection,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    dependensee_repo: DependenseeRepository,
):
    """Test persisting data through the adapter."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "dependensee_output.json"
    payload = json.loads(fixture_path.read_text())

    adapter = DependenseeAdapter(tool_run_repo, layout_repo, dependensee_repo)
    run_pk = adapter.persist(payload)

    # Verify projects were inserted
    projects = duckdb_conn.execute(
        """
        SELECT project_path, project_name, target_framework,
               project_reference_count, package_reference_count
        FROM lz_dependensee_projects
        WHERE run_pk = ?
        ORDER BY project_path
        """,
        [run_pk],
    ).fetchall()

    assert len(projects) == 2
    assert projects[0] == ("src/MyApp.Core/MyApp.Core.csproj", "MyApp.Core", "net8.0", 0, 1)
    assert projects[1] == ("src/MyApp/MyApp.csproj", "MyApp", "net8.0", 1, 2)


def test_adapter_persist_project_references(
    duckdb_conn: duckdb.DuckDBPyConnection,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    dependensee_repo: DependenseeRepository,
):
    """Test project references are persisted correctly."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "dependensee_output.json"
    payload = json.loads(fixture_path.read_text())

    adapter = DependenseeAdapter(tool_run_repo, layout_repo, dependensee_repo)
    run_pk = adapter.persist(payload)

    # Verify project references
    refs = duckdb_conn.execute(
        """
        SELECT source_project_path, target_project_path
        FROM lz_dependensee_project_refs
        WHERE run_pk = ?
        """,
        [run_pk],
    ).fetchall()

    assert len(refs) == 1
    assert refs[0] == ("src/MyApp/MyApp.csproj", "src/MyApp.Core/MyApp.Core.csproj")


def test_adapter_persist_package_references(
    duckdb_conn: duckdb.DuckDBPyConnection,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    dependensee_repo: DependenseeRepository,
):
    """Test package references are persisted correctly."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "dependensee_output.json"
    payload = json.loads(fixture_path.read_text())

    adapter = DependenseeAdapter(tool_run_repo, layout_repo, dependensee_repo)
    run_pk = adapter.persist(payload)

    # Verify package references
    packages = duckdb_conn.execute(
        """
        SELECT project_path, package_name, package_version
        FROM lz_dependensee_package_refs
        WHERE run_pk = ?
        ORDER BY project_path, package_name
        """,
        [run_pk],
    ).fetchall()

    assert len(packages) == 3
    # MyApp.Core has 1 package
    assert ("src/MyApp.Core/MyApp.Core.csproj", "Newtonsoft.Json", "13.0.3") in packages
    # MyApp has 2 packages
    assert ("src/MyApp/MyApp.csproj", "Microsoft.Extensions.Hosting", "8.0.0") in packages
    assert ("src/MyApp/MyApp.csproj", "Serilog", "3.1.1") in packages


def test_adapter_normalizes_paths(
    duckdb_conn: duckdb.DuckDBPyConnection,
    tool_run_repo: ToolRunRepository,
    layout_repo: LayoutRepository,
    dependensee_repo: DependenseeRepository,
):
    """Test that paths with repo root prefix are normalized."""
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "dependensee_output.json"
    payload = json.loads(fixture_path.read_text())

    # Prefix paths with repo root
    repo_root = Path("/tmp/demo")
    for project in payload["data"]["projects"]:
        project["path"] = f"{repo_root.as_posix().lstrip('/')}/{project['path']}"
        project["project_references"] = [
            f"{repo_root.as_posix().lstrip('/')}/{ref}"
            for ref in project.get("project_references", [])
        ]

    adapter = DependenseeAdapter(tool_run_repo, layout_repo, dependensee_repo, repo_root)
    run_pk = adapter.persist(payload)

    # Verify paths are normalized (repo root stripped)
    projects = duckdb_conn.execute(
        """
        SELECT project_path
        FROM lz_dependensee_projects
        WHERE run_pk = ?
        ORDER BY project_path
        """,
        [run_pk],
    ).fetchall()

    # Paths should not have the repo root prefix
    assert projects[0][0] == "src/MyApp.Core/MyApp.Core.csproj"
    assert projects[1][0] == "src/MyApp/MyApp.csproj"
