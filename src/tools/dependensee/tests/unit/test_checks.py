"""Unit tests for dependensee check modules.

Covers: accuracy, coverage, output_quality, and performance checks.
Each check function is tested with pass, fail, and edge-case inputs.
"""

from __future__ import annotations

import pytest

from scripts.checks.accuracy import (
    check_circular_dependencies,
    check_package_references,
    check_project_count,
    check_project_paths,
    check_project_references,
    check_target_frameworks,
)
from scripts.checks.coverage import (
    check_all_projects_have_path,
    check_graph_populated,
    check_projects_analyzed,
    check_summary_present,
)
from scripts.checks.output_quality import (
    check_envelope_present,
    check_graph_consistency,
    check_metadata_complete,
    check_paths_repo_relative,
    check_tool_name_correct,
)
from scripts.checks.performance import check_reasonable_output_size


# ---------------------------------------------------------------------------
# Helper: minimal valid output
# ---------------------------------------------------------------------------

def _make_output(
    *,
    projects: list[dict] | None = None,
    graph_nodes: list[dict] | None = None,
    graph_edges: list[dict] | None = None,
    summary: dict | None = None,
    circular_dependencies: list | None = None,
    metadata: dict | None = None,
) -> dict:
    """Build an output dict with sensible defaults."""
    if projects is None:
        projects = [
            {
                "name": "App",
                "path": "src/App/App.csproj",
                "target_framework": "net8.0",
                "project_references": ["src/Core/Core.csproj"],
                "package_references": [{"name": "Newtonsoft.Json", "version": "13.0.3"}],
            },
            {
                "name": "Core",
                "path": "src/Core/Core.csproj",
                "target_framework": "net8.0",
                "project_references": [],
                "package_references": [],
            },
        ]
    if graph_nodes is None:
        graph_nodes = [
            {"id": "src/App/App.csproj", "name": "App", "type": "project"},
            {"id": "src/Core/Core.csproj", "name": "Core", "type": "project"},
            {"id": "nuget:Newtonsoft.Json", "name": "Newtonsoft.Json", "type": "package"},
        ]
    if graph_edges is None:
        graph_edges = [
            {"source": "src/App/App.csproj", "target": "src/Core/Core.csproj", "type": "project_reference"},
            {"source": "src/App/App.csproj", "target": "nuget:Newtonsoft.Json", "type": "package_reference"},
        ]
    if summary is None:
        summary = {
            "project_count": len(projects),
            "package_count": 1,
            "reference_count": 1,
            "circular_dependency_count": 0,
        }
    if circular_dependencies is None:
        circular_dependencies = []
    if metadata is None:
        metadata = {
            "tool_name": "dependensee",
            "tool_version": "1.0.0",
            "run_id": "test-run",
            "repo_id": "test-repo",
            "branch": "main",
            "commit": "a" * 40,
            "timestamp": "2025-01-01T00:00:00Z",
            "schema_version": "1.0.0",
        }

    return {
        "metadata": metadata,
        "data": {
            "projects": projects,
            "dependency_graph": {"nodes": graph_nodes, "edges": graph_edges},
            "circular_dependencies": circular_dependencies,
            "summary": summary,
        },
    }


def _make_gt(
    *,
    project_count: int = 2,
    projects: list[dict] | None = None,
    circular_dependency_count: int = 0,
) -> dict:
    if projects is None:
        projects = [
            {
                "path": "src/App/App.csproj",
                "target_framework": "net8.0",
                "project_references": ["src/Core/Core.csproj"],
                "package_references": [{"name": "Newtonsoft.Json"}],
            },
            {
                "path": "src/Core/Core.csproj",
                "target_framework": "net8.0",
                "project_references": [],
                "package_references": [],
            },
        ]
    return {
        "expected": {
            "project_count": project_count,
            "projects": projects,
            "circular_dependency_count": circular_dependency_count,
        },
    }


# =========================================================================
# accuracy checks
# =========================================================================

class TestCheckProjectCount:
    def test_no_ground_truth_passes(self) -> None:
        r = check_project_count(_make_output(), None)
        assert r["status"] == "pass"

    def test_matching_count_passes(self) -> None:
        r = check_project_count(_make_output(), _make_gt(project_count=2))
        assert r["status"] == "pass"
        assert "2" in r["message"]

    def test_mismatched_count_fails(self) -> None:
        r = check_project_count(_make_output(), _make_gt(project_count=5))
        assert r["status"] == "fail"
        assert "expected 5" in r["message"]


class TestCheckProjectPaths:
    def test_no_ground_truth_passes(self) -> None:
        r = check_project_paths(_make_output(), None)
        assert r["status"] == "pass"

    def test_matching_paths_pass(self) -> None:
        r = check_project_paths(_make_output(), _make_gt())
        assert r["status"] == "pass"

    def test_missing_path_fails(self) -> None:
        gt = _make_gt(projects=[
            {"path": "src/App/App.csproj"},
            {"path": "src/Core/Core.csproj"},
            {"path": "src/Extra/Extra.csproj"},
        ])
        r = check_project_paths(_make_output(), gt)
        assert r["status"] == "fail"
        assert "missing" in r["message"]

    def test_extra_path_fails(self) -> None:
        gt = _make_gt(projects=[{"path": "src/App/App.csproj"}])
        r = check_project_paths(_make_output(), gt)
        assert r["status"] == "fail"
        assert "extra" in r["message"]


class TestCheckProjectReferences:
    def test_no_ground_truth_passes(self) -> None:
        r = check_project_references(_make_output(), None)
        assert r["status"] == "pass"

    def test_matching_refs_pass(self) -> None:
        r = check_project_references(_make_output(), _make_gt())
        assert r["status"] == "pass"

    def test_missing_ref_fails(self) -> None:
        gt = _make_gt(projects=[
            {
                "path": "src/App/App.csproj",
                "project_references": ["src/Core/Core.csproj", "src/Extra/Extra.csproj"],
            },
            {"path": "src/Core/Core.csproj", "project_references": []},
        ])
        r = check_project_references(_make_output(), gt)
        assert r["status"] == "fail"

    def test_extra_ref_fails(self) -> None:
        gt = _make_gt(projects=[
            {"path": "src/App/App.csproj", "project_references": []},
            {"path": "src/Core/Core.csproj", "project_references": []},
        ])
        r = check_project_references(_make_output(), gt)
        assert r["status"] == "fail"


class TestCheckPackageReferences:
    def test_no_ground_truth_passes(self) -> None:
        r = check_package_references(_make_output(), None)
        assert r["status"] == "pass"

    def test_matching_packages_pass(self) -> None:
        r = check_package_references(_make_output(), _make_gt())
        assert r["status"] == "pass"

    def test_missing_package_fails(self) -> None:
        gt = _make_gt(projects=[
            {
                "path": "src/App/App.csproj",
                "package_references": [{"name": "Newtonsoft.Json"}, {"name": "MissingPkg"}],
            },
            {"path": "src/Core/Core.csproj", "package_references": []},
        ])
        r = check_package_references(_make_output(), gt)
        assert r["status"] == "fail"


class TestCheckTargetFrameworks:
    def test_no_ground_truth_passes(self) -> None:
        r = check_target_frameworks(_make_output(), None)
        assert r["status"] == "pass"

    def test_matching_framework_passes(self) -> None:
        r = check_target_frameworks(_make_output(), _make_gt())
        assert r["status"] == "pass"

    def test_mismatched_framework_fails(self) -> None:
        gt = _make_gt(projects=[
            {"path": "src/App/App.csproj", "target_framework": "net6.0"},
            {"path": "src/Core/Core.csproj", "target_framework": "net8.0"},
        ])
        r = check_target_frameworks(_make_output(), gt)
        assert r["status"] == "fail"
        assert "expected=net6.0" in r["message"]


class TestCheckCircularDependencies:
    def test_no_ground_truth_passes(self) -> None:
        r = check_circular_dependencies(_make_output(), None)
        assert r["status"] == "pass"

    def test_matching_count_passes(self) -> None:
        r = check_circular_dependencies(
            _make_output(), _make_gt(circular_dependency_count=0)
        )
        assert r["status"] == "pass"

    def test_mismatched_count_fails(self) -> None:
        r = check_circular_dependencies(
            _make_output(), _make_gt(circular_dependency_count=3)
        )
        assert r["status"] == "fail"
        assert "expected 3" in r["message"]

    def test_actual_cycle_matches(self) -> None:
        output = _make_output(circular_dependencies=[["A", "B", "A"]])
        r = check_circular_dependencies(
            output, _make_gt(circular_dependency_count=1)
        )
        assert r["status"] == "pass"


# =========================================================================
# coverage checks
# =========================================================================

class TestCheckProjectsAnalyzed:
    def test_with_projects_passes(self) -> None:
        r = check_projects_analyzed(_make_output(), None)
        assert r["status"] == "pass"
        assert "2 projects" in r["message"]

    def test_no_projects_warns(self) -> None:
        r = check_projects_analyzed(_make_output(projects=[]), None)
        assert r["status"] == "warn"


class TestCheckGraphPopulated:
    def test_with_nodes_passes(self) -> None:
        r = check_graph_populated(_make_output(), None)
        assert r["status"] == "pass"

    def test_empty_graph_warns(self) -> None:
        r = check_graph_populated(
            _make_output(graph_nodes=[], graph_edges=[]), None
        )
        assert r["status"] == "warn"


class TestCheckSummaryPresent:
    def test_all_fields_present_passes(self) -> None:
        r = check_summary_present(_make_output(), None)
        assert r["status"] == "pass"

    def test_missing_field_fails(self) -> None:
        output = _make_output(summary={"project_count": 2})
        r = check_summary_present(output, None)
        assert r["status"] == "fail"
        assert "Missing summary fields" in r["message"]

    def test_empty_summary_fails(self) -> None:
        output = _make_output(summary={})
        r = check_summary_present(output, None)
        assert r["status"] == "fail"


class TestCheckAllProjectsHavePath:
    def test_all_have_paths_passes(self) -> None:
        r = check_all_projects_have_path(_make_output(), None)
        assert r["status"] == "pass"

    def test_missing_path_fails(self) -> None:
        output = _make_output(projects=[
            {"name": "A", "path": ""},
            {"name": "B", "path": "src/B.csproj"},
        ])
        r = check_all_projects_have_path(output, None)
        assert r["status"] == "fail"
        assert "project[0]" in r["message"]

    def test_no_projects_passes(self) -> None:
        r = check_all_projects_have_path(_make_output(projects=[]), None)
        assert r["status"] == "pass"
        assert "No projects" in r["message"]


# =========================================================================
# output_quality checks
# =========================================================================

class TestCheckEnvelopePresent:
    def test_valid_envelope_passes(self) -> None:
        r = check_envelope_present(_make_output(), None)
        assert r["status"] == "pass"

    def test_missing_metadata_fails(self) -> None:
        output = {"data": {}}
        r = check_envelope_present(output, None)
        assert r["status"] == "fail"
        assert "metadata" in r["message"]

    def test_missing_data_fails(self) -> None:
        output = {"metadata": {}}
        r = check_envelope_present(output, None)
        assert r["status"] == "fail"
        assert "data" in r["message"]


class TestCheckMetadataComplete:
    def test_complete_metadata_passes(self) -> None:
        r = check_metadata_complete(_make_output(), None)
        assert r["status"] == "pass"

    def test_missing_fields_fails(self) -> None:
        output = _make_output(metadata={"tool_name": "dependensee"})
        r = check_metadata_complete(output, None)
        assert r["status"] == "fail"
        assert "Missing metadata fields" in r["message"]

    def test_empty_metadata_fails(self) -> None:
        output = _make_output(metadata={})
        r = check_metadata_complete(output, None)
        assert r["status"] == "fail"


class TestCheckToolNameCorrect:
    def test_correct_name_passes(self) -> None:
        r = check_tool_name_correct(_make_output(), None)
        assert r["status"] == "pass"

    def test_wrong_name_fails(self) -> None:
        output = _make_output(metadata={
            "tool_name": "wrong-tool",
            "tool_version": "1.0.0",
            "run_id": "x",
            "repo_id": "x",
            "branch": "main",
            "commit": "a" * 40,
            "timestamp": "2025-01-01T00:00:00Z",
            "schema_version": "1.0.0",
        })
        r = check_tool_name_correct(output, None)
        assert r["status"] == "fail"
        assert "wrong-tool" in r["message"]


class TestCheckPathsRepoRelative:
    def test_relative_paths_pass(self) -> None:
        r = check_paths_repo_relative(_make_output(), None)
        assert r["status"] == "pass"

    def test_absolute_path_fails(self) -> None:
        output = _make_output(projects=[
            {"name": "A", "path": "/usr/src/A.csproj", "project_references": [], "package_references": []},
        ])
        r = check_paths_repo_relative(output, None)
        assert r["status"] == "fail"
        assert "/usr/src/A.csproj" in r["message"]

    def test_dot_slash_path_fails(self) -> None:
        output = _make_output(projects=[
            {"name": "A", "path": "./src/A.csproj", "project_references": [], "package_references": []},
        ])
        r = check_paths_repo_relative(output, None)
        assert r["status"] == "fail"

    def test_absolute_project_reference_fails(self) -> None:
        output = _make_output(projects=[
            {
                "name": "A",
                "path": "src/A.csproj",
                "project_references": ["/abs/Core.csproj"],
                "package_references": [],
            },
        ])
        r = check_paths_repo_relative(output, None)
        assert r["status"] == "fail"

    def test_no_projects_passes(self) -> None:
        r = check_paths_repo_relative(_make_output(projects=[]), None)
        assert r["status"] == "pass"


class TestCheckGraphConsistency:
    def test_consistent_graph_passes(self) -> None:
        r = check_graph_consistency(_make_output(), None)
        assert r["status"] == "pass"

    def test_missing_source_node_fails(self) -> None:
        output = _make_output(
            graph_nodes=[
                {"id": "src/Core/Core.csproj", "name": "Core", "type": "project"},
            ],
            graph_edges=[
                {"source": "nonexistent", "target": "src/Core/Core.csproj", "type": "project_reference"},
            ],
        )
        r = check_graph_consistency(output, None)
        assert r["status"] == "fail"
        assert "nonexistent" in r["message"]

    def test_missing_project_ref_target_fails(self) -> None:
        output = _make_output(
            graph_nodes=[
                {"id": "src/App/App.csproj", "name": "App", "type": "project"},
            ],
            graph_edges=[
                {"source": "src/App/App.csproj", "target": "missing.csproj", "type": "project_reference"},
            ],
        )
        r = check_graph_consistency(output, None)
        assert r["status"] == "fail"

    def test_package_ref_target_not_checked_against_nodes(self) -> None:
        """Package reference targets are allowed to be absent from nodes."""
        output = _make_output(
            graph_nodes=[
                {"id": "src/App/App.csproj", "name": "App", "type": "project"},
            ],
            graph_edges=[
                {"source": "src/App/App.csproj", "target": "nuget:SomePackage", "type": "package_reference"},
            ],
        )
        r = check_graph_consistency(output, None)
        assert r["status"] == "pass"

    def test_empty_graph_passes(self) -> None:
        r = check_graph_consistency(
            _make_output(graph_nodes=[], graph_edges=[]), None
        )
        assert r["status"] == "pass"


# =========================================================================
# performance checks
# =========================================================================

class TestCheckReasonableOutputSize:
    def test_reasonable_passes(self) -> None:
        r = check_reasonable_output_size(_make_output(), None)
        assert r["status"] == "pass"

    def test_fewer_nodes_than_projects_warns(self) -> None:
        output = _make_output(graph_nodes=[
            {"id": "src/App/App.csproj", "name": "App", "type": "project"},
        ])
        r = check_reasonable_output_size(output, None)
        assert r["status"] == "warn"
        assert "fewer nodes" in r["message"]

    def test_equal_counts_passes(self) -> None:
        output = _make_output(
            projects=[{"name": "A", "path": "A.csproj"}],
            graph_nodes=[{"id": "A.csproj", "name": "A", "type": "project"}],
            graph_edges=[],
        )
        r = check_reasonable_output_size(output, None)
        assert r["status"] == "pass"
