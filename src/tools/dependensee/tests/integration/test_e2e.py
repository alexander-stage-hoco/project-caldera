"""End-to-end integration tests for dependensee.

Tests the fallback parser path against the synthetic .NET repo
(no dotnet CLI required).
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.analyze import analyze_repo, find_project_files, parse_project_file


@pytest.fixture
def tool_root() -> Path:
    """Return the tool root directory."""
    return Path(__file__).parents[2]


@pytest.fixture
def synthetic_repo(tool_root: Path) -> Path:
    """Return the synthetic test repository path."""
    repo = tool_root / "eval-repos" / "synthetic"
    if not repo.exists() or not any(repo.iterdir()):
        pytest.skip("Synthetic repo is empty - add test files first")
    return repo


@pytest.mark.integration
def test_fallback_analysis_produces_envelope(synthetic_repo: Path):
    """Test that fallback parser produces a valid Caldera envelope."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)

        with patch("scripts.analyze.check_dotnet_available", return_value=False):
            result = analyze_repo(synthetic_repo.resolve(), temp_dir)

    # Envelope structure
    assert result["tool"] == "dependensee"
    assert result["tool_version"] == "fallback-parser"

    # Summary
    summary = result["summary"]
    assert summary["project_count"] >= 3  # MyApp, MyApp.Core, MyApp.Data at minimum
    assert summary["package_count"] >= 0
    assert summary["circular_dependency_count"] >= 0

    # Projects
    assert len(result["projects"]) == summary["project_count"]
    project_names = {p["name"] for p in result["projects"]}
    assert "MyApp" in project_names
    assert "MyApp.Core" in project_names


@pytest.mark.integration
def test_dependency_graph_structure(synthetic_repo: Path):
    """Test that the dependency graph has correct nodes and edges."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_dir = Path(tmpdir)

        with patch("scripts.analyze.check_dotnet_available", return_value=False):
            result = analyze_repo(synthetic_repo.resolve(), temp_dir)

    graph = result["dependency_graph"]
    assert "nodes" in graph
    assert "edges" in graph

    # Should have project nodes
    project_nodes = [n for n in graph["nodes"] if n["type"] == "project"]
    assert len(project_nodes) >= 3

    # Check node structure
    for node in graph["nodes"]:
        assert "id" in node
        assert "name" in node
        assert "type" in node
        assert node["type"] in ("project", "package")

    # Check edge structure
    for edge in graph["edges"]:
        assert "source" in edge
        assert "target" in edge
        assert "type" in edge
        assert edge["type"] in ("project_reference", "package_reference")


@pytest.mark.integration
def test_project_references_resolved(synthetic_repo: Path):
    """Test that project references are resolved to repo-relative paths."""
    project_files = find_project_files(synthetic_repo)
    assert len(project_files) >= 3

    projects = []
    for pf in project_files:
        info = parse_project_file(pf, synthetic_repo.resolve())
        if info:
            projects.append(info)

    # At least one project should have project references
    all_refs = [ref for p in projects for ref in p.project_references]
    assert len(all_refs) > 0, "Expected at least one project reference in synthetic repo"

    # All refs should be repo-relative (no leading / or ..)
    for ref in all_refs:
        assert not ref.startswith("/"), f"Absolute path in reference: {ref}"
        assert ".." not in ref.split("/"), f"Parent traversal in reference: {ref}"
