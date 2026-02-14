"""Unit tests for dependensee analyze script.

Covers: project file discovery, XML parsing, dependency graph building,
circular dependency detection, DependenSee subprocess calls, and
the top-level analyze_repo orchestrator.
"""

from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.analyze import (
    ProjectInfo,
    build_dependency_graph,
    check_dependensee_installed,
    check_dotnet_available,
    detect_circular_dependencies,
    find_project_files,
    find_solution_files,
    get_dependensee_version,
    install_dependensee,
    parse_project_file,
    run_dependensee,
    analyze_repo,
)


# ---------------------------------------------------------------------------
# Fixtures: synthetic .NET project files
# ---------------------------------------------------------------------------

SDK_CSPROJ = textwrap.dedent("""\
    <Project Sdk="Microsoft.NET.Sdk">
      <PropertyGroup>
        <TargetFramework>net8.0</TargetFramework>
      </PropertyGroup>
      <ItemGroup>
        <ProjectReference Include="../Core/Core.csproj" />
      </ItemGroup>
      <ItemGroup>
        <PackageReference Include="Newtonsoft.Json" Version="13.0.3" />
        <PackageReference Include="Serilog" Version="3.1.0" />
      </ItemGroup>
    </Project>
""")

CORE_CSPROJ = textwrap.dedent("""\
    <Project Sdk="Microsoft.NET.Sdk">
      <PropertyGroup>
        <TargetFramework>net8.0</TargetFramework>
      </PropertyGroup>
      <ItemGroup>
        <PackageReference Include="Newtonsoft.Json" Version="13.0.3" />
      </ItemGroup>
    </Project>
""")

LEGACY_CSPROJ = textwrap.dedent("""\
    <Project xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
      <PropertyGroup>
        <TargetFrameworks>net6.0;net8.0</TargetFrameworks>
      </PropertyGroup>
    </Project>
""")

FSPROJ_CONTENT = textwrap.dedent("""\
    <Project Sdk="Microsoft.NET.Sdk">
      <PropertyGroup>
        <TargetFramework>net7.0</TargetFramework>
      </PropertyGroup>
    </Project>
""")

INVALID_XML = "<<<not valid xml"


@pytest.fixture
def dotnet_repo(tmp_path: Path) -> Path:
    """Create a small synthetic .NET repo structure."""
    (tmp_path / "App").mkdir()
    (tmp_path / "Core").mkdir()
    (tmp_path / "App" / "App.csproj").write_text(SDK_CSPROJ)
    (tmp_path / "Core" / "Core.csproj").write_text(CORE_CSPROJ)
    return tmp_path


@pytest.fixture
def mixed_repo(tmp_path: Path) -> Path:
    """Repo with csproj, fsproj, vbproj, and sln files."""
    (tmp_path / "A").mkdir()
    (tmp_path / "B").mkdir()
    (tmp_path / "A" / "A.csproj").write_text(SDK_CSPROJ)
    (tmp_path / "B" / "B.fsproj").write_text(FSPROJ_CONTENT)
    (tmp_path / "Solution.sln").write_text("solution file stub")
    return tmp_path


# ---------------------------------------------------------------------------
# Discovery helpers
# ---------------------------------------------------------------------------

class TestFindSolutionFiles:
    def test_finds_sln(self, mixed_repo: Path) -> None:
        result = find_solution_files(mixed_repo)
        assert len(result) == 1
        assert result[0].name == "Solution.sln"

    def test_empty_repo(self, tmp_path: Path) -> None:
        assert find_solution_files(tmp_path) == []


class TestFindProjectFiles:
    def test_finds_csproj_and_fsproj(self, mixed_repo: Path) -> None:
        result = find_project_files(mixed_repo)
        names = {p.name for p in result}
        assert "A.csproj" in names
        assert "B.fsproj" in names

    def test_finds_vbproj(self, tmp_path: Path) -> None:
        (tmp_path / "X.vbproj").write_text("<Project />")
        result = find_project_files(tmp_path)
        assert len(result) == 1
        assert result[0].name == "X.vbproj"

    def test_empty_repo(self, tmp_path: Path) -> None:
        assert find_project_files(tmp_path) == []


# ---------------------------------------------------------------------------
# XML parsing
# ---------------------------------------------------------------------------

class TestParseProjectFile:
    def test_sdk_style_project(self, dotnet_repo: Path) -> None:
        proj = parse_project_file(
            dotnet_repo / "App" / "App.csproj", dotnet_repo
        )
        assert proj is not None
        assert proj.name == "App"
        assert proj.target_framework == "net8.0"
        assert len(proj.package_references) == 2
        pkg_names = {p["name"] for p in proj.package_references}
        assert "Newtonsoft.Json" in pkg_names
        assert "Serilog" in pkg_names

    def test_project_reference_resolved(self, dotnet_repo: Path) -> None:
        proj = parse_project_file(
            dotnet_repo / "App" / "App.csproj", dotnet_repo
        )
        assert proj is not None
        assert len(proj.project_references) == 1
        # Should be repo-relative, pointing to Core/Core.csproj
        assert "Core/Core.csproj" in proj.project_references[0]

    def test_legacy_project_with_namespace(self, tmp_path: Path) -> None:
        proj_file = tmp_path / "Legacy.csproj"
        proj_file.write_text(LEGACY_CSPROJ)
        proj = parse_project_file(proj_file, tmp_path)
        assert proj is not None
        assert proj.name == "Legacy"
        # TargetFrameworks (plural) should still be found
        assert proj.target_framework == "net6.0;net8.0"

    def test_no_target_framework(self, tmp_path: Path) -> None:
        proj_file = tmp_path / "Bare.csproj"
        proj_file.write_text("<Project Sdk='Microsoft.NET.Sdk'></Project>")
        proj = parse_project_file(proj_file, tmp_path)
        assert proj is not None
        assert proj.target_framework is None
        assert proj.project_references == []
        assert proj.package_references == []

    def test_invalid_xml_returns_none(self, tmp_path: Path) -> None:
        proj_file = tmp_path / "Bad.csproj"
        proj_file.write_text(INVALID_XML)
        assert parse_project_file(proj_file, tmp_path) is None

    def test_package_without_version(self, tmp_path: Path) -> None:
        proj_file = tmp_path / "NoVer.csproj"
        proj_file.write_text(textwrap.dedent("""\
            <Project Sdk="Microsoft.NET.Sdk">
              <ItemGroup>
                <PackageReference Include="SomeLib" />
              </ItemGroup>
            </Project>
        """))
        proj = parse_project_file(proj_file, tmp_path)
        assert proj is not None
        assert len(proj.package_references) == 1
        assert proj.package_references[0]["name"] == "SomeLib"
        assert "version" not in proj.package_references[0]

    def test_backslash_paths_normalised(self, tmp_path: Path) -> None:
        """ProjectReference with Windows backslash separators is normalised."""
        (tmp_path / "Lib").mkdir()
        (tmp_path / "Lib" / "Lib.csproj").write_text("<Project />")
        proj_file = tmp_path / "App.csproj"
        proj_file.write_text(textwrap.dedent("""\
            <Project Sdk="Microsoft.NET.Sdk">
              <ItemGroup>
                <ProjectReference Include="Lib\\Lib.csproj" />
              </ItemGroup>
            </Project>
        """))
        proj = parse_project_file(proj_file, tmp_path)
        assert proj is not None
        assert len(proj.project_references) == 1
        assert "\\" not in proj.project_references[0]

    def test_path_is_repo_relative(self, dotnet_repo: Path) -> None:
        proj = parse_project_file(
            dotnet_repo / "Core" / "Core.csproj", dotnet_repo
        )
        assert proj is not None
        assert not proj.path.startswith("/")
        assert not proj.path.startswith("./")


# ---------------------------------------------------------------------------
# Dependency graph building
# ---------------------------------------------------------------------------

class TestBuildDependencyGraph:
    def _make_projects(self) -> list[ProjectInfo]:
        return [
            ProjectInfo(
                name="App",
                path="src/App/App.csproj",
                target_framework="net8.0",
                project_references=["src/Core/Core.csproj"],
                package_references=[
                    {"name": "Newtonsoft.Json", "version": "13.0.3"},
                ],
            ),
            ProjectInfo(
                name="Core",
                path="src/Core/Core.csproj",
                target_framework="net8.0",
                project_references=[],
                package_references=[
                    {"name": "Newtonsoft.Json", "version": "13.0.3"},
                    {"name": "Serilog", "version": "3.1.0"},
                ],
            ),
        ]

    def test_project_nodes_present(self) -> None:
        graph = build_dependency_graph(self._make_projects())
        project_nodes = [n for n in graph["nodes"] if n["type"] == "project"]
        assert len(project_nodes) == 2

    def test_package_nodes_deduplicated(self) -> None:
        """Newtonsoft.Json is referenced by both projects but appears once."""
        graph = build_dependency_graph(self._make_projects())
        pkg_nodes = [n for n in graph["nodes"] if n["type"] == "package"]
        pkg_names = [n["name"] for n in pkg_nodes]
        assert pkg_names.count("Newtonsoft.Json") == 1

    def test_edge_types(self) -> None:
        graph = build_dependency_graph(self._make_projects())
        types = {e["type"] for e in graph["edges"]}
        assert "project_reference" in types
        assert "package_reference" in types

    def test_project_reference_edge(self) -> None:
        graph = build_dependency_graph(self._make_projects())
        proj_edges = [e for e in graph["edges"] if e["type"] == "project_reference"]
        assert len(proj_edges) == 1
        assert proj_edges[0]["source"] == "src/App/App.csproj"
        assert proj_edges[0]["target"] == "src/Core/Core.csproj"

    def test_empty_projects(self) -> None:
        graph = build_dependency_graph([])
        assert graph["nodes"] == []
        assert graph["edges"] == []

    def test_package_node_has_version(self) -> None:
        graph = build_dependency_graph(self._make_projects())
        pkg_nodes = [n for n in graph["nodes"] if n["type"] == "package"]
        versions = {n["name"]: n.get("version") for n in pkg_nodes}
        assert versions["Newtonsoft.Json"] == "13.0.3"


# ---------------------------------------------------------------------------
# Circular dependency detection
# ---------------------------------------------------------------------------

class TestDetectCircularDependencies:
    def test_no_cycles(self) -> None:
        projects = [
            ProjectInfo("A", "A.csproj", None, ["B.csproj"], []),
            ProjectInfo("B", "B.csproj", None, [], []),
        ]
        assert detect_circular_dependencies(projects) == []

    def test_simple_cycle(self) -> None:
        projects = [
            ProjectInfo("A", "A.csproj", None, ["B.csproj"], []),
            ProjectInfo("B", "B.csproj", None, ["A.csproj"], []),
        ]
        cycles = detect_circular_dependencies(projects)
        assert len(cycles) >= 1
        # The cycle should contain both A and B
        all_nodes = set()
        for c in cycles:
            all_nodes.update(c)
        assert "A.csproj" in all_nodes
        assert "B.csproj" in all_nodes

    def test_three_node_cycle(self) -> None:
        projects = [
            ProjectInfo("A", "A.csproj", None, ["B.csproj"], []),
            ProjectInfo("B", "B.csproj", None, ["C.csproj"], []),
            ProjectInfo("C", "C.csproj", None, ["A.csproj"], []),
        ]
        cycles = detect_circular_dependencies(projects)
        assert len(cycles) >= 1

    def test_self_reference_not_tracked_as_cycle(self) -> None:
        """A project referencing a non-existent project is ignored."""
        projects = [
            ProjectInfo("A", "A.csproj", None, ["nonexistent.csproj"], []),
        ]
        cycles = detect_circular_dependencies(projects)
        assert len(cycles) == 0

    def test_multiple_independent_cycles_deduplicated(self) -> None:
        projects = [
            ProjectInfo("A", "A.csproj", None, ["B.csproj"], []),
            ProjectInfo("B", "B.csproj", None, ["A.csproj"], []),
            ProjectInfo("C", "C.csproj", None, ["D.csproj"], []),
            ProjectInfo("D", "D.csproj", None, ["C.csproj"], []),
        ]
        cycles = detect_circular_dependencies(projects)
        # Should have exactly 2 distinct cycles
        cycle_sets = [frozenset(c) for c in cycles]
        unique = set(cycle_sets)
        assert len(unique) == 2

    def test_empty_projects(self) -> None:
        assert detect_circular_dependencies([]) == []


# ---------------------------------------------------------------------------
# Subprocess wrappers (mocked)
# ---------------------------------------------------------------------------

class TestCheckDotnetAvailable:
    @patch("scripts.analyze.shutil.which", return_value="/usr/local/bin/dotnet")
    def test_available(self, mock_which: MagicMock) -> None:
        assert check_dotnet_available() is True
        mock_which.assert_called_once_with("dotnet")

    @patch("scripts.analyze.shutil.which", return_value=None)
    def test_not_available(self, mock_which: MagicMock) -> None:
        assert check_dotnet_available() is False


class TestCheckDependenseeInstalled:
    @patch("scripts.analyze.subprocess.run")
    def test_installed(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(stdout="  dependensee   2.0.0\n", returncode=0)
        assert check_dependensee_installed() is True

    @patch("scripts.analyze.subprocess.run")
    def test_not_installed(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(stdout="other-tool  1.0.0\n", returncode=0)
        assert check_dependensee_installed() is False

    @patch("scripts.analyze.subprocess.run", side_effect=FileNotFoundError)
    def test_dotnet_missing(self, mock_run: MagicMock) -> None:
        assert check_dependensee_installed() is False

    @patch("scripts.analyze.subprocess.run", side_effect=subprocess.SubprocessError)
    def test_subprocess_error(self, mock_run: MagicMock) -> None:
        assert check_dependensee_installed() is False


class TestInstallDependensee:
    @patch("scripts.analyze.subprocess.run")
    def test_success(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0)
        assert install_dependensee() is True

    @patch("scripts.analyze.subprocess.run")
    def test_failure(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1)
        assert install_dependensee() is False

    @patch("scripts.analyze.subprocess.run", side_effect=subprocess.SubprocessError)
    def test_exception(self, mock_run: MagicMock) -> None:
        assert install_dependensee() is False


class TestGetDependenseeVersion:
    @patch("scripts.analyze.subprocess.run")
    def test_version_returned(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(
            returncode=0, stdout="DependenSee 2.1.0\n"
        )
        version = get_dependensee_version()
        assert "2.1.0" in version

    @patch("scripts.analyze.subprocess.run")
    def test_plain_version_string(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(
            returncode=0, stdout="3.0.0\n"
        )
        assert get_dependensee_version() == "3.0.0"

    @patch("scripts.analyze.subprocess.run")
    def test_failure_returns_unknown(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        assert get_dependensee_version() == "unknown"

    @patch("scripts.analyze.subprocess.run", side_effect=subprocess.SubprocessError)
    def test_exception_returns_unknown(self, mock_run: MagicMock) -> None:
        assert get_dependensee_version() == "unknown"

    @patch("scripts.analyze.subprocess.run")
    def test_no_digit_returns_full_line(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="unknown-version\n")
        # No part has digits, so returns whole line
        assert get_dependensee_version() == "unknown-version"


class TestRunDependensee:
    @patch("scripts.analyze.subprocess.run")
    def test_success(self, mock_run: MagicMock, tmp_path: Path) -> None:
        output_file = tmp_path / "output.json"
        payload = {"Projects": [{"Name": "App"}]}

        def fake_run(cmd, **kwargs):
            # Simulate DependenSee writing JSON
            output_file.write_text(json.dumps(payload))
            return MagicMock(returncode=0)

        mock_run.side_effect = fake_run
        result = run_dependensee(tmp_path, output_file)
        assert result == payload

    @patch("scripts.analyze.subprocess.run")
    def test_failure_returns_none(self, mock_run: MagicMock, tmp_path: Path) -> None:
        mock_run.return_value = MagicMock(returncode=1)
        output_file = tmp_path / "output.json"
        assert run_dependensee(tmp_path, output_file) is None

    @patch("scripts.analyze.subprocess.run", side_effect=subprocess.SubprocessError)
    def test_exception_returns_none(self, mock_run: MagicMock, tmp_path: Path) -> None:
        output_file = tmp_path / "output.json"
        assert run_dependensee(tmp_path, output_file) is None

    @patch("scripts.analyze.subprocess.run")
    def test_bad_json_returns_none(self, mock_run: MagicMock, tmp_path: Path) -> None:
        output_file = tmp_path / "output.json"

        def fake_run(cmd, **kwargs):
            output_file.write_text("NOT JSON")
            return MagicMock(returncode=0)

        mock_run.side_effect = fake_run
        assert run_dependensee(tmp_path, output_file) is None


# ---------------------------------------------------------------------------
# analyze_repo: integration of all pieces (subprocess mocked)
# ---------------------------------------------------------------------------

class TestAnalyzeRepo:
    @patch("scripts.analyze.check_dotnet_available", return_value=False)
    def test_no_dotnet_uses_fallback(
        self, mock_dotnet: MagicMock, dotnet_repo: Path, tmp_path: Path
    ) -> None:
        result = analyze_repo(dotnet_repo, tmp_path)
        assert result["tool_version"] == "fallback-parser"
        assert result["summary"]["project_count"] == 2
        assert len(result["projects"]) == 2

    @patch("scripts.analyze.check_dotnet_available", return_value=False)
    def test_empty_repo_returns_zeros(
        self, mock_dotnet: MagicMock, tmp_path: Path
    ) -> None:
        repo = tmp_path / "empty"
        repo.mkdir()
        result = analyze_repo(repo, tmp_path / "temp")
        assert result["summary"]["project_count"] == 0
        assert result["projects"] == []
        assert result["dependency_graph"]["nodes"] == []
        assert result["circular_dependencies"] == []

    @patch("scripts.analyze.check_dotnet_available", return_value=False)
    def test_graph_present(
        self, mock_dotnet: MagicMock, dotnet_repo: Path, tmp_path: Path
    ) -> None:
        result = analyze_repo(dotnet_repo, tmp_path)
        graph = result["dependency_graph"]
        assert len(graph["nodes"]) > 0
        assert len(graph["edges"]) > 0

    @patch("scripts.analyze.check_dotnet_available", return_value=False)
    def test_summary_counts_packages(
        self, mock_dotnet: MagicMock, dotnet_repo: Path, tmp_path: Path
    ) -> None:
        result = analyze_repo(dotnet_repo, tmp_path)
        summary = result["summary"]
        # App has Newtonsoft.Json + Serilog; Core has Newtonsoft.Json → 2 unique
        assert summary["package_count"] == 2
        # App references Core → 1 project reference
        assert summary["reference_count"] == 1
        assert summary["circular_dependency_count"] == 0

    @patch("scripts.analyze.check_dotnet_available", return_value=False)
    def test_circular_deps_detected(
        self, mock_dotnet: MagicMock, tmp_path: Path
    ) -> None:
        """Two projects that reference each other form a cycle."""
        (tmp_path / "A").mkdir()
        (tmp_path / "B").mkdir()
        (tmp_path / "A" / "A.csproj").write_text(textwrap.dedent("""\
            <Project Sdk="Microsoft.NET.Sdk">
              <ItemGroup>
                <ProjectReference Include="../B/B.csproj" />
              </ItemGroup>
            </Project>
        """))
        (tmp_path / "B" / "B.csproj").write_text(textwrap.dedent("""\
            <Project Sdk="Microsoft.NET.Sdk">
              <ItemGroup>
                <ProjectReference Include="../A/A.csproj" />
              </ItemGroup>
            </Project>
        """))
        result = analyze_repo(tmp_path, tmp_path / "temp")
        assert result["summary"]["circular_dependency_count"] >= 1
        assert len(result["circular_dependencies"]) >= 1

    @patch("scripts.analyze.check_dotnet_available", return_value=True)
    @patch("scripts.analyze.check_dependensee_installed", return_value=True)
    @patch("scripts.analyze.get_dependensee_version", return_value="2.0.0")
    @patch("scripts.analyze.find_solution_files", return_value=[])
    @patch("scripts.analyze.run_dependensee", return_value=None)
    def test_dependensee_available_sets_version(
        self,
        mock_run: MagicMock,
        mock_sln: MagicMock,
        mock_ver: MagicMock,
        mock_installed: MagicMock,
        mock_dotnet: MagicMock,
        dotnet_repo: Path,
        tmp_path: Path,
    ) -> None:
        result = analyze_repo(dotnet_repo, tmp_path)
        assert result["tool_version"] == "2.0.0"

    @patch("scripts.analyze.check_dotnet_available", return_value=True)
    @patch("scripts.analyze.check_dependensee_installed", side_effect=[False, False])
    @patch("scripts.analyze.install_dependensee", return_value=False)
    def test_install_failure_falls_back(
        self,
        mock_install: MagicMock,
        mock_installed: MagicMock,
        mock_dotnet: MagicMock,
        dotnet_repo: Path,
        tmp_path: Path,
    ) -> None:
        result = analyze_repo(dotnet_repo, tmp_path)
        assert result["tool_version"] == "fallback-parser"
        mock_install.assert_called_once()
