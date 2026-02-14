"""Unit tests for dotcover analyze script.

Tests cover:
- Version detection (dotCover CLI, Coverlet/dotnet)
- Test project / solution discovery (glob patterns)
- Cobertura XML parsing (line counting, namespace extraction, source resolution)
- dotCover JSON extraction (recursive tree walking)
- run_dotcover / run_coverlet subprocess orchestration (mocked)
- Docker-based analysis (mocked)
- analyze_repo dispatch logic (backend selection, tool availability)
- Dataclass construction
- Envelope creation in main()
- Error / timeout / FileNotFoundError edge cases
"""

from __future__ import annotations

import json
import subprocess
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_output() -> dict:
    """Realistic dotCover output structure matching schemas/output.schema.json."""
    return {
        "metadata": {
            "tool_name": "dotcover",
            "tool_version": "2025.3.2",
            "run_id": "550e8400-e29b-41d4-a716-446655440000",
            "repo_id": "660e8400-e29b-41d4-a716-446655440000",
            "branch": "main",
            "commit": "a" * 40,
            "timestamp": "2025-01-01T00:00:00Z",
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "dotcover",
            "tool_version": "2025.3.2",
            "summary": {
                "total_assemblies": 1,
                "total_types": 2,
                "total_methods": 5,
                "covered_statements": 15,
                "total_statements": 20,
                "statement_coverage_pct": 75.0,
            },
            "assemblies": [
                {
                    "name": "CoverageDemo",
                    "covered_statements": 15,
                    "total_statements": 20,
                    "statement_coverage_pct": 75.0,
                },
            ],
            "types": [
                {
                    "assembly": "CoverageDemo",
                    "namespace": "CoverageDemo",
                    "name": "Calculator",
                    "file_path": "src/Calculator.cs",
                    "covered_statements": 12,
                    "total_statements": 16,
                    "statement_coverage_pct": 75.0,
                },
                {
                    "assembly": "CoverageDemo",
                    "namespace": "CoverageDemo",
                    "name": "StringUtils",
                    "file_path": "src/StringUtils.cs",
                    "covered_statements": 3,
                    "total_statements": 4,
                    "statement_coverage_pct": 75.0,
                },
            ],
            "methods": [
                {
                    "assembly": "CoverageDemo",
                    "type_name": "Calculator",
                    "name": "Add(int, int)",
                    "covered_statements": 3,
                    "total_statements": 3,
                    "statement_coverage_pct": 100.0,
                },
                {
                    "assembly": "CoverageDemo",
                    "type_name": "Calculator",
                    "name": "Subtract(int, int)",
                    "covered_statements": 3,
                    "total_statements": 3,
                    "statement_coverage_pct": 100.0,
                },
                {
                    "assembly": "CoverageDemo",
                    "type_name": "Calculator",
                    "name": "Multiply(int, int)",
                    "covered_statements": 3,
                    "total_statements": 5,
                    "statement_coverage_pct": 60.0,
                },
                {
                    "assembly": "CoverageDemo",
                    "type_name": "Calculator",
                    "name": "Divide(int, int)",
                    "covered_statements": 3,
                    "total_statements": 5,
                    "statement_coverage_pct": 60.0,
                },
                {
                    "assembly": "CoverageDemo",
                    "type_name": "StringUtils",
                    "name": "Reverse(string)",
                    "covered_statements": 3,
                    "total_statements": 4,
                    "statement_coverage_pct": 75.0,
                },
            ],
        },
    }


@pytest.fixture
def cobertura_xml(tmp_path: Path) -> Path:
    """Create a minimal but realistic Cobertura XML file."""
    xml_content = textwrap.dedent("""\
        <?xml version="1.0" encoding="utf-8"?>
        <coverage line-rate="0.75" branch-rate="0.5" lines-covered="15" lines-valid="20"
                  version="1.0" timestamp="1234567890">
          <sources>
            <source>/repo</source>
          </sources>
          <packages>
            <package name="MyAssembly" line-rate="0.75" complexity="0">
              <classes>
                <class name="MyNamespace.Calculator" filename="src/Calculator.cs"
                       line-rate="0.8" complexity="0">
                  <methods>
                    <method name="Add" line-rate="1.0">
                      <lines>
                        <line number="10" hits="1"/>
                        <line number="11" hits="1"/>
                      </lines>
                    </method>
                    <method name="Divide" line-rate="0.5">
                      <lines>
                        <line number="20" hits="1"/>
                        <line number="21" hits="0"/>
                      </lines>
                    </method>
                  </methods>
                  <lines>
                    <line number="10" hits="1"/>
                    <line number="11" hits="1"/>
                    <line number="20" hits="1"/>
                    <line number="21" hits="0"/>
                    <line number="22" hits="1"/>
                  </lines>
                </class>
                <class name="StringUtils" filename="src/StringUtils.cs"
                       line-rate="0.5" complexity="0">
                  <methods/>
                  <lines>
                    <line number="5" hits="1"/>
                    <line number="6" hits="0"/>
                  </lines>
                </class>
              </classes>
            </package>
          </packages>
        </coverage>
    """)
    xml_path = tmp_path / "coverage.cobertura.xml"
    xml_path.write_text(xml_content)
    return xml_path


@pytest.fixture
def dotcover_json_report() -> dict:
    """Realistic dotCover JSON report with assembly/namespace/type/method tree."""
    return {
        "CoveredStatements": 10,
        "TotalStatements": 20,
        "CoveragePercent": 50.0,
        "Children": [
            {
                "Kind": "Assembly",
                "Name": "MyApp",
                "CoveredStatements": 10,
                "TotalStatements": 20,
                "CoveragePercent": 50.0,
                "Children": [
                    {
                        "Kind": "Namespace",
                        "Name": "MyApp.Services",
                        "CoveredStatements": 10,
                        "TotalStatements": 20,
                        "CoveragePercent": 50.0,
                        "Children": [
                            {
                                "Kind": "Type",
                                "Name": "UserService",
                                "CoveredStatements": 7,
                                "TotalStatements": 12,
                                "CoveragePercent": 58.3,
                                "Children": [
                                    {
                                        "Kind": "Method",
                                        "Name": "GetUser",
                                        "CoveredStatements": 4,
                                        "TotalStatements": 6,
                                        "CoveragePercent": 66.7,
                                        "Children": [],
                                    },
                                    {
                                        "Kind": "Method",
                                        "Name": "DeleteUser",
                                        "CoveredStatements": 3,
                                        "TotalStatements": 6,
                                        "CoveragePercent": 50.0,
                                        "Children": [],
                                    },
                                ],
                            },
                            {
                                "Kind": "Type",
                                "Name": "EmailService",
                                "CoveredStatements": 3,
                                "TotalStatements": 8,
                                "CoveragePercent": 37.5,
                                "Children": [],
                            },
                        ],
                    },
                ],
            },
        ],
    }


# ---------------------------------------------------------------------------
# Existing structural tests on sample_output fixture
# ---------------------------------------------------------------------------

def test_analyze_output_structure(sample_output: dict):
    """Test that analyze produces valid output structure."""
    assert "metadata" in sample_output
    assert "data" in sample_output
    data = sample_output["data"]
    assert data["tool"] == "dotcover"
    assert isinstance(data["assemblies"], list)
    assert isinstance(data["types"], list)
    assert isinstance(data["methods"], list)
    assert "summary" in data


def test_analyze_metadata_fields(sample_output: dict):
    """Test that all required metadata fields are present."""
    required_fields = [
        "tool_name", "tool_version", "run_id", "repo_id",
        "branch", "commit", "timestamp", "schema_version",
    ]
    metadata = sample_output["metadata"]
    for field in required_fields:
        assert field in metadata, f"Missing required field: {field}"
        assert metadata[field], f"Field is empty: {field}"


def test_summary_fields(sample_output: dict):
    """Test that summary contains all required coverage fields."""
    required_fields = [
        "total_assemblies", "total_types", "total_methods",
        "covered_statements", "total_statements", "statement_coverage_pct",
    ]
    summary = sample_output["data"]["summary"]
    for field in required_fields:
        assert field in summary, f"Missing required summary field: {field}"


def test_assembly_structure(sample_output: dict):
    required_fields = ["name", "covered_statements", "total_statements", "statement_coverage_pct"]
    for assembly in sample_output["data"]["assemblies"]:
        for field in required_fields:
            assert field in assembly


def test_type_structure(sample_output: dict):
    required_fields = ["assembly", "name", "covered_statements", "total_statements", "statement_coverage_pct"]
    for type_entry in sample_output["data"]["types"]:
        for field in required_fields:
            assert field in type_entry


def test_method_structure(sample_output: dict):
    required_fields = ["assembly", "type_name", "name", "covered_statements", "total_statements", "statement_coverage_pct"]
    for method in sample_output["data"]["methods"]:
        for field in required_fields:
            assert field in method


def test_coverage_invariant_covered_lte_total(sample_output: dict):
    data = sample_output["data"]
    for assembly in data["assemblies"]:
        assert assembly["covered_statements"] <= assembly["total_statements"]
    for t in data["types"]:
        assert t["covered_statements"] <= t["total_statements"]
    for m in data["methods"]:
        assert m["covered_statements"] <= m["total_statements"]


def test_coverage_percentage_bounds(sample_output: dict):
    data = sample_output["data"]
    assert 0 <= data["summary"]["statement_coverage_pct"] <= 100
    for a in data["assemblies"]:
        assert 0 <= a["statement_coverage_pct"] <= 100
    for t in data["types"]:
        assert 0 <= t["statement_coverage_pct"] <= 100
    for m in data["methods"]:
        assert 0 <= m["statement_coverage_pct"] <= 100


def test_path_normalization(sample_output: dict):
    for t in sample_output["data"].get("types", []):
        path = t.get("file_path")
        if path is None:
            continue
        assert not path.startswith("/")
        assert not path.startswith("./")
        assert ".." not in path.split("/")
        assert "\\" not in path


def test_hierarchy_consistency(sample_output: dict):
    data = sample_output["data"]
    valid_types = {(t["assembly"], t["name"]) for t in data["types"]}
    for method in data["methods"]:
        key = (method["assembly"], method["type_name"])
        assert key in valid_types


def test_non_negative_counts(sample_output: dict):
    data = sample_output["data"]
    assert data["summary"]["covered_statements"] >= 0
    assert data["summary"]["total_statements"] >= 0
    for a in data["assemblies"]:
        assert a["covered_statements"] >= 0
        assert a["total_statements"] >= 0


def test_schema_validation(sample_output: dict):
    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema not installed")
    schema_path = Path(__file__).parents[2] / "schemas" / "output.schema.json"
    if not schema_path.exists():
        pytest.skip("Schema file not found")
    schema = json.loads(schema_path.read_text())
    jsonschema.validate(sample_output, schema)


# ===========================================================================
# NEW: Tests that exercise actual analyze.py functions
# ===========================================================================

# --- Dataclass construction -------------------------------------------------

class TestDataclasses:
    """Test dataclass creation for AssemblyCoverage, TypeCoverage, MethodCoverage."""

    def test_assembly_coverage(self):
        from scripts.analyze import AssemblyCoverage
        a = AssemblyCoverage(name="Lib", covered_statements=5, total_statements=10, coverage_pct=50.0)
        assert a.name == "Lib"
        assert a.coverage_pct == 50.0

    def test_type_coverage(self):
        from scripts.analyze import TypeCoverage
        t = TypeCoverage(
            assembly="Lib", namespace="Lib.Core", name="Foo",
            file_path="src/Foo.cs", covered_statements=3, total_statements=5,
            coverage_pct=60.0,
        )
        assert t.namespace == "Lib.Core"
        assert t.file_path == "src/Foo.cs"

    def test_type_coverage_nullable_fields(self):
        from scripts.analyze import TypeCoverage
        t = TypeCoverage(
            assembly="Lib", namespace=None, name="Bar",
            file_path=None, covered_statements=0, total_statements=0,
            coverage_pct=0.0,
        )
        assert t.namespace is None
        assert t.file_path is None

    def test_method_coverage(self):
        from scripts.analyze import MethodCoverage
        m = MethodCoverage(
            assembly="Lib", type_name="Foo", name="DoStuff",
            covered_statements=2, total_statements=4, coverage_pct=50.0,
        )
        assert m.type_name == "Foo"


# --- Version helpers --------------------------------------------------------

class TestGetDotcoverVersion:
    """Test get_dotcover_version with mocked subprocess."""

    def test_returns_parsed_version(self):
        from scripts.analyze import get_dotcover_version
        mock_result = MagicMock()
        mock_result.stdout = "JetBrains dotCover Command-Line Tools 2025.3.2\n"
        with patch("scripts.analyze.subprocess.run", return_value=mock_result):
            version = get_dotcover_version()
        assert version == "2025.3.2"

    def test_returns_unknown_on_error(self):
        from scripts.analyze import get_dotcover_version
        with patch("scripts.analyze.subprocess.run", side_effect=FileNotFoundError):
            assert get_dotcover_version() == "unknown"

    def test_returns_unknown_on_called_process_error(self):
        from scripts.analyze import get_dotcover_version
        with patch("scripts.analyze.subprocess.run", side_effect=subprocess.CalledProcessError(1, "dotCover")):
            assert get_dotcover_version() == "unknown"

    def test_returns_unknown_when_no_version_in_output(self):
        from scripts.analyze import get_dotcover_version
        mock_result = MagicMock()
        mock_result.stdout = "Some unrelated output\n"
        with patch("scripts.analyze.subprocess.run", return_value=mock_result):
            assert get_dotcover_version() == "unknown"


class TestGetCoverletVersion:
    """Test get_coverlet_version with mocked subprocess."""

    def test_returns_dotnet_version(self):
        from scripts.analyze import get_coverlet_version
        mock_result = MagicMock()
        mock_result.stdout = "9.0.100\n"
        with patch("scripts.analyze.subprocess.run", return_value=mock_result):
            version = get_coverlet_version()
        assert version == "coverlet (dotnet 9.0.100)"

    def test_returns_unknown_on_error(self):
        from scripts.analyze import get_coverlet_version
        with patch("scripts.analyze.subprocess.run", side_effect=FileNotFoundError):
            assert get_coverlet_version() == "coverlet (unknown)"


# --- Project / solution discovery -------------------------------------------

class TestFindTestProject:
    """Test find_test_project with real filesystem via tmp_path."""

    def test_finds_test_csproj(self, tmp_path: Path):
        from scripts.analyze import find_test_project
        test_dir = tmp_path / "tests" / "MyApp.Tests"
        test_dir.mkdir(parents=True)
        csproj = test_dir / "MyApp.Tests.csproj"
        csproj.write_text("<Project/>")
        result = find_test_project(tmp_path)
        assert result is not None
        assert result.name == "MyApp.Tests.csproj"

    def test_returns_none_when_no_test_project(self, tmp_path: Path):
        from scripts.analyze import find_test_project
        (tmp_path / "src" / "Lib").mkdir(parents=True)
        (tmp_path / "src" / "Lib" / "Lib.csproj").write_text("<Project/>")
        result = find_test_project(tmp_path)
        assert result is None

    def test_finds_tests_csproj_pattern(self, tmp_path: Path):
        from scripts.analyze import find_test_project
        d = tmp_path / "tests"
        d.mkdir()
        (d / "tests.csproj").write_text("<Project/>")
        result = find_test_project(tmp_path)
        assert result is not None

    def test_finds_test_star_pattern(self, tmp_path: Path):
        from scripts.analyze import find_test_project
        d = tmp_path / "tests"
        d.mkdir()
        (d / "FooTest.csproj").write_text("<Project/>")
        result = find_test_project(tmp_path)
        assert result is not None


class TestFindSolution:
    """Test find_solution with real filesystem via tmp_path."""

    def test_finds_sln_at_root(self, tmp_path: Path):
        from scripts.analyze import find_solution
        sln = tmp_path / "MyApp.sln"
        sln.write_text("sln content")
        result = find_solution(tmp_path)
        assert result == sln

    def test_prefers_root_sln(self, tmp_path: Path):
        from scripts.analyze import find_solution
        root_sln = tmp_path / "Root.sln"
        root_sln.write_text("root")
        nested_dir = tmp_path / "sub"
        nested_dir.mkdir()
        nested_sln = nested_dir / "Nested.sln"
        nested_sln.write_text("nested")
        result = find_solution(tmp_path)
        assert result == root_sln

    def test_returns_nested_when_no_root(self, tmp_path: Path):
        from scripts.analyze import find_solution
        nested_dir = tmp_path / "sub"
        nested_dir.mkdir()
        nested_sln = nested_dir / "Nested.sln"
        nested_sln.write_text("nested")
        result = find_solution(tmp_path)
        assert result == nested_sln

    def test_returns_none_when_no_sln(self, tmp_path: Path):
        from scripts.analyze import find_solution
        assert find_solution(tmp_path) is None


# --- Cobertura XML parsing --------------------------------------------------

class TestParseCobertura:
    """Test parse_cobertura_xml with real XML on disk."""

    def test_parses_assemblies(self, cobertura_xml: Path, tmp_path: Path):
        from scripts.analyze import parse_cobertura_xml
        result = parse_cobertura_xml(cobertura_xml, tmp_path)
        assert result is not None
        assert result["_coverlet_data"] is True
        assert len(result["assemblies"]) == 1
        assert result["assemblies"][0]["name"] == "MyAssembly"

    def test_parses_types(self, cobertura_xml: Path, tmp_path: Path):
        from scripts.analyze import parse_cobertura_xml
        result = parse_cobertura_xml(cobertura_xml, tmp_path)
        assert len(result["types"]) == 2
        # Check namespace extraction from dotted class name
        calc_type = next(t for t in result["types"] if t["name"] == "Calculator")
        assert calc_type["namespace"] == "MyNamespace"
        assert calc_type["assembly"] == "MyAssembly"
        # StringUtils has no dot -> no namespace
        su_type = next(t for t in result["types"] if t["name"] == "StringUtils")
        assert su_type["namespace"] is None

    def test_parses_methods(self, cobertura_xml: Path, tmp_path: Path):
        from scripts.analyze import parse_cobertura_xml
        result = parse_cobertura_xml(cobertura_xml, tmp_path)
        assert len(result["methods"]) == 2
        add_method = next(m for m in result["methods"] if m["name"] == "Add")
        assert add_method["covered_statements"] == 2
        assert add_method["total_statements"] == 2

    def test_line_counts(self, cobertura_xml: Path, tmp_path: Path):
        from scripts.analyze import parse_cobertura_xml
        result = parse_cobertura_xml(cobertura_xml, tmp_path)
        assert result["lines_covered"] == 15
        assert result["lines_valid"] == 20
        assert result["line_rate"] == 0.75

    def test_assembly_level_stats(self, cobertura_xml: Path, tmp_path: Path):
        from scripts.analyze import parse_cobertura_xml
        result = parse_cobertura_xml(cobertura_xml, tmp_path)
        asm = result["assemblies"][0]
        # Calculator: 4 covered of 5 total, StringUtils: 1 covered of 2 total
        assert asm["covered_statements"] == 5
        assert asm["total_statements"] == 7

    def test_handles_parse_error(self, tmp_path: Path):
        from scripts.analyze import parse_cobertura_xml
        bad_xml = tmp_path / "bad.xml"
        bad_xml.write_text("not xml at all <<>>")
        result = parse_cobertura_xml(bad_xml, tmp_path)
        assert result is None

    def test_handles_no_packages(self, tmp_path: Path):
        from scripts.analyze import parse_cobertura_xml
        xml_path = tmp_path / "empty.xml"
        xml_path.write_text('<?xml version="1.0"?><coverage line-rate="0" branch-rate="0" lines-covered="0" lines-valid="0"></coverage>')
        result = parse_cobertura_xml(xml_path, tmp_path)
        assert result is not None
        assert result["CoveredStatements"] == 0

    def test_source_dir_resolution(self, tmp_path: Path):
        """Test that source dirs are used to resolve file paths."""
        from scripts.analyze import parse_cobertura_xml
        # Create the actual file so the path resolution finds it
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "Foo.cs").write_text("// code")
        xml_content = textwrap.dedent(f"""\
            <?xml version="1.0"?>
            <coverage line-rate="1.0" branch-rate="0" lines-covered="1" lines-valid="1">
              <sources><source>{tmp_path}</source></sources>
              <packages>
                <package name="Asm" line-rate="1.0" complexity="0">
                  <classes>
                    <class name="Foo" filename="src/Foo.cs" line-rate="1.0" complexity="0">
                      <lines><line number="1" hits="1"/></lines>
                    </class>
                  </classes>
                </package>
              </packages>
            </coverage>
        """)
        xml_path = tmp_path / "cob.xml"
        xml_path.write_text(xml_content)
        result = parse_cobertura_xml(xml_path, tmp_path)
        assert result is not None
        t = result["types"][0]
        assert t["file_path"] is not None
        assert not t["file_path"].startswith("/")


# --- dotCover JSON extraction -----------------------------------------------

class TestExtractCoverageData:
    """Test extract_coverage_data from dotCover JSON tree."""

    def test_extracts_assemblies(self, dotcover_json_report: dict):
        from scripts.analyze import extract_coverage_data
        assemblies, types, methods = extract_coverage_data(dotcover_json_report)
        assert len(assemblies) == 1
        assert assemblies[0].name == "MyApp"
        assert assemblies[0].coverage_pct == 50.0

    def test_extracts_types(self, dotcover_json_report: dict):
        from scripts.analyze import extract_coverage_data
        _, types, _ = extract_coverage_data(dotcover_json_report)
        assert len(types) == 2
        names = {t.name for t in types}
        assert "UserService" in names
        assert "EmailService" in names

    def test_extracts_methods(self, dotcover_json_report: dict):
        from scripts.analyze import extract_coverage_data
        _, _, methods = extract_coverage_data(dotcover_json_report)
        assert len(methods) == 2
        assert methods[0].assembly == "MyApp"
        assert methods[0].type_name == "UserService"

    def test_namespace_propagation(self, dotcover_json_report: dict):
        from scripts.analyze import extract_coverage_data
        _, types, _ = extract_coverage_data(dotcover_json_report)
        for t in types:
            assert t.namespace == "MyApp.Services"

    def test_file_mapping_applied(self, dotcover_json_report: dict):
        from scripts.analyze import extract_coverage_data
        mapping = {"MyApp.UserService": "src/UserService.cs"}
        _, types, _ = extract_coverage_data(dotcover_json_report, mapping)
        us = next(t for t in types if t.name == "UserService")
        assert us.file_path == "src/UserService.cs"
        # EmailService not in mapping -> None
        es = next(t for t in types if t.name == "EmailService")
        assert es.file_path is None

    def test_empty_report(self):
        from scripts.analyze import extract_coverage_data
        assemblies, types, methods = extract_coverage_data({"Children": []})
        assert assemblies == []
        assert types == []
        assert methods == []

    def test_no_children_key(self):
        from scripts.analyze import extract_coverage_data
        assemblies, types, methods = extract_coverage_data({})
        assert assemblies == []


# --- parse_source_file_mapping (XML) ----------------------------------------

class TestParseSourceFileMapping:
    """Test parse_source_file_mapping from dotCover DetailedXML."""

    def test_parses_assembly_type_mapping(self, tmp_path: Path):
        from scripts.analyze import parse_source_file_mapping
        xml_content = textwrap.dedent("""\
            <?xml version="1.0"?>
            <Root>
              <Assembly Name="Lib">
                <Namespace Name="Lib.Core">
                  <Type Name="Calc" File="/repo/src/Calc.cs"/>
                </Namespace>
              </Assembly>
            </Root>
        """)
        xml_path = tmp_path / "detailed.xml"
        xml_path.write_text(xml_content)
        mapping = parse_source_file_mapping(xml_path, Path("/repo"))
        assert "Lib.Calc" in mapping

    def test_handles_parse_error(self, tmp_path: Path):
        from scripts.analyze import parse_source_file_mapping
        bad_path = tmp_path / "bad.xml"
        bad_path.write_text("<<<not xml>>>")
        mapping = parse_source_file_mapping(bad_path, tmp_path)
        assert mapping == {}

    def test_empty_xml(self, tmp_path: Path):
        from scripts.analyze import parse_source_file_mapping
        xml_path = tmp_path / "empty.xml"
        xml_path.write_text('<?xml version="1.0"?><Root/>')
        mapping = parse_source_file_mapping(xml_path, tmp_path)
        assert mapping == {}


# --- run_dotcover (subprocess orchestration) --------------------------------

class TestRunDotcover:
    """Test run_dotcover with fully mocked subprocess."""

    def test_successful_run(self, tmp_path: Path):
        from scripts.analyze import run_dotcover
        output_dir = tmp_path / "out"
        output_dir.mkdir()

        # Simulate: snapshot created, then JSON report created
        def fake_run(cmd, **kwargs):
            if "cover" in cmd:
                (output_dir / "coverage.dcvr").write_text("snapshot")
            elif "report" in cmd:
                (output_dir / "coverage.json").write_text('{"CoveredStatements": 5}')
            result = MagicMock()
            result.returncode = 0
            result.stderr = ""
            return result

        with patch("scripts.analyze.subprocess.run", side_effect=fake_run):
            report, xml_path = run_dotcover(tmp_path, output_dir)

        assert report is not None
        assert report["CoveredStatements"] == 5

    def test_timeout_on_cover(self, tmp_path: Path):
        from scripts.analyze import run_dotcover
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        with patch("scripts.analyze.subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 600)):
            report, xml_path = run_dotcover(tmp_path, output_dir)
        assert report is None

    def test_file_not_found(self, tmp_path: Path):
        from scripts.analyze import run_dotcover
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        with patch("scripts.analyze.subprocess.run", side_effect=FileNotFoundError):
            report, xml_path = run_dotcover(tmp_path, output_dir)
        assert report is None

    def test_no_snapshot_generated(self, tmp_path: Path):
        from scripts.analyze import run_dotcover
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        mock_result = MagicMock(returncode=0, stderr="")
        with patch("scripts.analyze.subprocess.run", return_value=mock_result):
            report, xml_path = run_dotcover(tmp_path, output_dir)
        assert report is None

    def test_report_timeout_returns_snapshot_only(self, tmp_path: Path):
        from scripts.analyze import run_dotcover
        output_dir = tmp_path / "out"
        output_dir.mkdir()

        call_count = 0

        def fake_run(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Cover step succeeds
                (output_dir / "coverage.dcvr").write_text("snapshot")
                result = MagicMock(returncode=0, stderr="")
                return result
            else:
                # Report step times out
                raise subprocess.TimeoutExpired("cmd", 120)

        with patch("scripts.analyze.subprocess.run", side_effect=fake_run):
            report, xml_path = run_dotcover(tmp_path, output_dir)

        assert report is not None
        assert report["_snapshot_only"] is True

    def test_nonzero_exit_continues(self, tmp_path: Path):
        from scripts.analyze import run_dotcover
        output_dir = tmp_path / "out"
        output_dir.mkdir()

        def fake_run(cmd, **kwargs):
            if "cover" in cmd:
                (output_dir / "coverage.dcvr").write_text("snapshot")
                return MagicMock(returncode=1, stderr="some warning")
            elif "report" in cmd:
                (output_dir / "coverage.json").write_text('{"CoveredStatements": 3}')
                return MagicMock(returncode=0, stderr="")
            return MagicMock(returncode=0, stderr="")

        with patch("scripts.analyze.subprocess.run", side_effect=fake_run):
            report, xml_path = run_dotcover(tmp_path, output_dir)
        assert report is not None
        assert report["CoveredStatements"] == 3

    def test_json_decode_error_returns_none(self, tmp_path: Path):
        from scripts.analyze import run_dotcover
        output_dir = tmp_path / "out"
        output_dir.mkdir()

        def fake_run(cmd, **kwargs):
            if "cover" in cmd:
                (output_dir / "coverage.dcvr").write_text("snapshot")
            elif "report" in cmd:
                (output_dir / "coverage.json").write_text("NOT JSON {{{{")
            return MagicMock(returncode=0, stderr="")

        with patch("scripts.analyze.subprocess.run", side_effect=fake_run):
            report, xml_path = run_dotcover(tmp_path, output_dir)
        assert report is None

    def test_report_file_not_found(self, tmp_path: Path):
        """FileNotFoundError on report step (should not happen but handled)."""
        from scripts.analyze import run_dotcover
        output_dir = tmp_path / "out"
        output_dir.mkdir()

        call_count = 0

        def fake_run(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                (output_dir / "coverage.dcvr").write_text("snapshot")
                return MagicMock(returncode=0, stderr="")
            else:
                raise FileNotFoundError

        with patch("scripts.analyze.subprocess.run", side_effect=fake_run):
            report, xml_path = run_dotcover(tmp_path, output_dir)
        assert report is None

    def test_with_test_project(self, tmp_path: Path):
        from scripts.analyze import run_dotcover
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        test_proj = tmp_path / "tests" / "MyApp.Tests.csproj"

        def fake_run(cmd, **kwargs):
            # Verify test project is passed in the cover command (not report)
            if "cover" in cmd:
                assert str(test_proj) in cmd
                (output_dir / "coverage.dcvr").write_text("snapshot")
            elif "report" in cmd:
                (output_dir / "coverage.json").write_text('{"ok": true}')
            return MagicMock(returncode=0, stderr="")

        with patch("scripts.analyze.subprocess.run", side_effect=fake_run):
            report, _ = run_dotcover(tmp_path, output_dir, test_project=test_proj)
        assert report is not None

    def test_xml_report_returned_when_exists(self, tmp_path: Path):
        from scripts.analyze import run_dotcover
        output_dir = tmp_path / "out"
        output_dir.mkdir()

        def fake_run(cmd, **kwargs):
            if "cover" in cmd:
                (output_dir / "coverage.dcvr").write_text("snapshot")
            elif "report" in cmd:
                (output_dir / "coverage.json").write_text('{"ok": true}')
                (output_dir / "coverage.xml").write_text("<xml/>")
            return MagicMock(returncode=0, stderr="")

        with patch("scripts.analyze.subprocess.run", side_effect=fake_run):
            report, xml_path = run_dotcover(tmp_path, output_dir)
        assert xml_path is not None
        assert xml_path.name == "coverage.xml"


# --- run_coverlet -----------------------------------------------------------

class TestRunCoverlet:
    """Test run_coverlet with fully mocked subprocess."""

    def test_successful_run(self, tmp_path: Path, cobertura_xml: Path):
        from scripts.analyze import run_coverlet
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        results_dir = output_dir / "TestResults"

        def fake_run(cmd, **kwargs):
            # Simulate coverlet creating the test results
            guid_dir = results_dir / "abc-123"
            guid_dir.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy(cobertura_xml, guid_dir / "coverage.cobertura.xml")
            return MagicMock(returncode=0, stderr="")

        with patch("scripts.analyze.subprocess.run", side_effect=fake_run):
            result, cob_path = run_coverlet(tmp_path, output_dir)

        assert result is not None
        assert result["_coverlet_data"] is True
        assert cob_path is not None

    def test_timeout(self, tmp_path: Path):
        from scripts.analyze import run_coverlet
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        with patch("scripts.analyze.subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 600)):
            result, path = run_coverlet(tmp_path, output_dir)
        assert result is None

    def test_file_not_found(self, tmp_path: Path):
        from scripts.analyze import run_coverlet
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        with patch("scripts.analyze.subprocess.run", side_effect=FileNotFoundError):
            result, path = run_coverlet(tmp_path, output_dir)
        assert result is None

    def test_no_cobertura_file_found(self, tmp_path: Path):
        from scripts.analyze import run_coverlet
        output_dir = tmp_path / "out"
        output_dir.mkdir()

        def fake_run(cmd, **kwargs):
            # Create TestResults but no coverage file
            (output_dir / "TestResults").mkdir(exist_ok=True)
            return MagicMock(returncode=0, stderr="")

        with patch("scripts.analyze.subprocess.run", side_effect=fake_run):
            result, path = run_coverlet(tmp_path, output_dir)
        assert result is None

    def test_with_test_project(self, tmp_path: Path, cobertura_xml: Path):
        from scripts.analyze import run_coverlet
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        test_proj = tmp_path / "tests" / "MyApp.Tests.csproj"

        def fake_run(cmd, **kwargs):
            assert str(test_proj) in cmd
            results_dir = output_dir / "TestResults" / "guid"
            results_dir.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy(cobertura_xml, results_dir / "coverage.cobertura.xml")
            return MagicMock(returncode=0, stderr="")

        with patch("scripts.analyze.subprocess.run", side_effect=fake_run):
            result, _ = run_coverlet(tmp_path, output_dir, test_project=test_proj)
        assert result is not None


# --- run_dotcover_docker ----------------------------------------------------

class TestRunDotcoverDocker:
    """Test Docker-based dotCover execution."""

    def test_successful_docker_run(self, tmp_path: Path):
        from scripts.analyze import run_dotcover_docker
        output_dir = tmp_path / "out"
        output_dir.mkdir()

        call_count = 0

        def fake_run(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Build step
                return MagicMock(returncode=0, stderr="")
            elif call_count == 2:
                # Cover step - create snapshot
                (output_dir / "coverage.dcvr").write_text("snapshot")
                return MagicMock(returncode=0, stderr="")
            else:
                # Report step - create JSON report
                (output_dir / "coverage.json").write_text('{"CoveredStatements": 7}')
                return MagicMock(returncode=0, stderr="")

        with patch("scripts.analyze.subprocess.run", side_effect=fake_run):
            report, xml_path = run_dotcover_docker(tmp_path, output_dir)

        assert report is not None
        assert report["CoveredStatements"] == 7

    def test_build_timeout(self, tmp_path: Path):
        from scripts.analyze import run_dotcover_docker
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        with patch("scripts.analyze.subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 300)):
            report, _ = run_dotcover_docker(tmp_path, output_dir)
        assert report is None

    def test_docker_not_found(self, tmp_path: Path):
        from scripts.analyze import run_dotcover_docker
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        with patch("scripts.analyze.subprocess.run", side_effect=FileNotFoundError):
            report, _ = run_dotcover_docker(tmp_path, output_dir)
        assert report is None

    def test_cover_timeout(self, tmp_path: Path):
        from scripts.analyze import run_dotcover_docker
        output_dir = tmp_path / "out"
        output_dir.mkdir()

        call_count = 0

        def fake_run(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(returncode=0, stderr="")
            raise subprocess.TimeoutExpired("cmd", 600)

        with patch("scripts.analyze.subprocess.run", side_effect=fake_run):
            report, _ = run_dotcover_docker(tmp_path, output_dir)
        assert report is None

    def test_no_snapshot_after_cover(self, tmp_path: Path):
        from scripts.analyze import run_dotcover_docker
        output_dir = tmp_path / "out"
        output_dir.mkdir()

        def fake_run(cmd, **kwargs):
            return MagicMock(returncode=0, stderr="")

        with patch("scripts.analyze.subprocess.run", side_effect=fake_run):
            report, _ = run_dotcover_docker(tmp_path, output_dir)
        assert report is None

    def test_report_timeout_returns_snapshot_only(self, tmp_path: Path):
        from scripts.analyze import run_dotcover_docker
        output_dir = tmp_path / "out"
        output_dir.mkdir()

        call_count = 0

        def fake_run(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                if call_count == 2:
                    (output_dir / "coverage.dcvr").write_text("snap")
                return MagicMock(returncode=0, stderr="")
            raise subprocess.TimeoutExpired("cmd", 300)

        with patch("scripts.analyze.subprocess.run", side_effect=fake_run):
            report, _ = run_dotcover_docker(tmp_path, output_dir)
        assert report is not None
        assert report["_snapshot_only"] is True

    def test_with_test_project(self, tmp_path: Path):
        from scripts.analyze import run_dotcover_docker
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        test_proj = tmp_path / "tests" / "Tests.csproj"

        call_count = 0

        def fake_run(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                (output_dir / "coverage.dcvr").write_text("snap")
            if call_count == 3:
                (output_dir / "coverage.json").write_text('{"ok": true}')
            return MagicMock(returncode=0, stderr="")

        with patch("scripts.analyze.subprocess.run", side_effect=fake_run):
            report, _ = run_dotcover_docker(tmp_path, output_dir, test_project=test_proj)
        assert report is not None

    def test_cover_file_not_found_in_docker(self, tmp_path: Path):
        """Docker not found on cover step (after build succeeds)."""
        from scripts.analyze import run_dotcover_docker
        output_dir = tmp_path / "out"
        output_dir.mkdir()

        call_count = 0

        def fake_run(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(returncode=0, stderr="")
            raise FileNotFoundError

        with patch("scripts.analyze.subprocess.run", side_effect=fake_run):
            report, _ = run_dotcover_docker(tmp_path, output_dir)
        assert report is None

    def test_report_file_not_found(self, tmp_path: Path):
        from scripts.analyze import run_dotcover_docker
        output_dir = tmp_path / "out"
        output_dir.mkdir()

        call_count = 0

        def fake_run(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(returncode=0, stderr="")
            if call_count == 2:
                (output_dir / "coverage.dcvr").write_text("snap")
                return MagicMock(returncode=0, stderr="")
            raise FileNotFoundError

        with patch("scripts.analyze.subprocess.run", side_effect=fake_run):
            report, _ = run_dotcover_docker(tmp_path, output_dir)
        assert report is None

    def test_build_nonzero_continues(self, tmp_path: Path):
        from scripts.analyze import run_dotcover_docker
        output_dir = tmp_path / "out"
        output_dir.mkdir()

        call_count = 0

        def fake_run(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(returncode=1, stderr="build warning")
            if call_count == 2:
                (output_dir / "coverage.dcvr").write_text("snap")
                return MagicMock(returncode=0, stderr="")
            if call_count == 3:
                (output_dir / "coverage.json").write_text('{"ok": true}')
                return MagicMock(returncode=0, stderr="")
            return MagicMock(returncode=0, stderr="")

        with patch("scripts.analyze.subprocess.run", side_effect=fake_run):
            report, _ = run_dotcover_docker(tmp_path, output_dir)
        assert report is not None

    def test_json_decode_error(self, tmp_path: Path):
        from scripts.analyze import run_dotcover_docker
        output_dir = tmp_path / "out"
        output_dir.mkdir()

        call_count = 0

        def fake_run(cmd, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                (output_dir / "coverage.dcvr").write_text("snap")
            if call_count == 3:
                (output_dir / "coverage.json").write_text("NOT JSON")
            return MagicMock(returncode=0, stderr="")

        with patch("scripts.analyze.subprocess.run", side_effect=fake_run):
            report, _ = run_dotcover_docker(tmp_path, output_dir)
        assert report is None


# --- analyze_repo dispatch --------------------------------------------------

class TestAnalyzeRepo:
    """Test analyze_repo dispatch and analyze_repo_dotcover / analyze_repo_coverlet."""

    def test_dispatches_to_coverlet(self, tmp_path: Path):
        from scripts.analyze import analyze_repo, BACKEND_COVERLET
        with patch("scripts.analyze.analyze_repo_coverlet", return_value={"tool": "dotcover"}) as mock:
            result = analyze_repo(tmp_path, tmp_path / "out", backend=BACKEND_COVERLET)
        mock.assert_called_once()
        assert result["tool"] == "dotcover"

    def test_dispatches_to_dotcover(self, tmp_path: Path):
        from scripts.analyze import analyze_repo, BACKEND_DOTCOVER
        with patch("scripts.analyze.analyze_repo_dotcover", return_value={"tool": "dotcover"}) as mock:
            result = analyze_repo(tmp_path, tmp_path / "out", backend=BACKEND_DOTCOVER)
        mock.assert_called_once()

    def test_finds_test_project_automatically(self, tmp_path: Path):
        from scripts.analyze import analyze_repo, BACKEND_DOTCOVER
        # Create a test project
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        (test_dir / "MyApp.Tests.csproj").write_text("<Project/>")

        with patch("scripts.analyze.analyze_repo_dotcover", return_value={"tool": "dotcover"}) as mock:
            analyze_repo(tmp_path, tmp_path / "out", backend=BACKEND_DOTCOVER)
        # test_project argument should be populated
        _, kwargs = mock.call_args
        # It's a positional arg
        call_args = mock.call_args[0]
        assert call_args[2] is not None  # test_project


class TestAnalyzeRepoDotcover:
    """Test analyze_repo_dotcover with tool availability mocking."""

    def test_returns_error_when_dotcover_not_installed(self, tmp_path: Path):
        from scripts.analyze import analyze_repo_dotcover
        with patch("scripts.analyze.get_dotcover_version", return_value="unknown"), \
             patch("scripts.analyze.shutil.which", return_value=None):
            result = analyze_repo_dotcover(tmp_path, tmp_path / "out")
        assert result["summary"]["error"] == "dotCover not installed"
        assert result["backend"] == "dotcover"

    def test_returns_error_when_no_report(self, tmp_path: Path):
        from scripts.analyze import analyze_repo_dotcover
        with patch("scripts.analyze.get_dotcover_version", return_value="1.0"), \
             patch("scripts.analyze.shutil.which", return_value="/usr/bin/dotCover"), \
             patch("scripts.analyze.run_dotcover", return_value=(None, None)):
            result = analyze_repo_dotcover(tmp_path, tmp_path / "out")
        assert result["summary"]["error"] == "No coverage data collected"

    def test_handles_snapshot_only(self, tmp_path: Path):
        from scripts.analyze import analyze_repo_dotcover
        snapshot_report = {"_snapshot_only": True, "_snapshot_path": "/tmp/snap.dcvr"}
        with patch("scripts.analyze.get_dotcover_version", return_value="1.0"), \
             patch("scripts.analyze.shutil.which", return_value="/usr/bin/dotCover"), \
             patch("scripts.analyze.run_dotcover", return_value=(snapshot_report, None)):
            result = analyze_repo_dotcover(tmp_path, tmp_path / "out")
        assert "warning" in result["summary"]
        assert result["summary"]["snapshot_path"] == "/tmp/snap.dcvr"

    def test_successful_analysis(self, tmp_path: Path, dotcover_json_report: dict):
        from scripts.analyze import analyze_repo_dotcover
        with patch("scripts.analyze.get_dotcover_version", return_value="2025.3.2"), \
             patch("scripts.analyze.shutil.which", return_value="/usr/bin/dotCover"), \
             patch("scripts.analyze.run_dotcover", return_value=(dotcover_json_report, None)):
            result = analyze_repo_dotcover(tmp_path, tmp_path / "out")
        assert result["summary"]["total_assemblies"] == 1
        assert result["summary"]["total_types"] == 2
        assert result["summary"]["total_methods"] == 2
        assert result["summary"]["statement_coverage_pct"] == 50.0

    def test_uses_docker_when_requested(self, tmp_path: Path, dotcover_json_report: dict):
        from scripts.analyze import analyze_repo_dotcover
        with patch("scripts.analyze.get_dotcover_version", return_value="1.0"), \
             patch("scripts.analyze.run_dotcover_docker", return_value=(dotcover_json_report, None)) as mock_docker:
            result = analyze_repo_dotcover(tmp_path, tmp_path / "out", use_docker=True)
        mock_docker.assert_called_once()
        assert result["summary"]["total_assemblies"] == 1

    def test_xml_path_triggers_file_mapping(self, tmp_path: Path, dotcover_json_report: dict):
        from scripts.analyze import analyze_repo_dotcover
        xml_path = tmp_path / "detailed.xml"
        xml_path.write_text('<?xml version="1.0"?><Root/>')
        with patch("scripts.analyze.get_dotcover_version", return_value="1.0"), \
             patch("scripts.analyze.shutil.which", return_value="/usr/bin/dotCover"), \
             patch("scripts.analyze.run_dotcover", return_value=(dotcover_json_report, xml_path)), \
             patch("scripts.analyze.parse_source_file_mapping", return_value={}) as mock_parse:
            result = analyze_repo_dotcover(tmp_path, tmp_path / "out")
        mock_parse.assert_called_once()


class TestAnalyzeRepoCoverlet:
    """Test analyze_repo_coverlet with tool availability mocking."""

    def test_returns_error_when_dotnet_not_installed(self, tmp_path: Path):
        from scripts.analyze import analyze_repo_coverlet
        with patch("scripts.analyze.get_coverlet_version", return_value="coverlet (unknown)"), \
             patch("scripts.analyze.shutil.which", return_value=None):
            result = analyze_repo_coverlet(tmp_path, tmp_path / "out")
        assert result["summary"]["error"] == "dotnet SDK not installed"
        assert result["backend"] == "coverlet"

    def test_returns_error_when_no_result(self, tmp_path: Path):
        from scripts.analyze import analyze_repo_coverlet
        with patch("scripts.analyze.get_coverlet_version", return_value="coverlet (9.0)"), \
             patch("scripts.analyze.shutil.which", return_value="/usr/bin/dotnet"), \
             patch("scripts.analyze.run_coverlet", return_value=(None, None)):
            result = analyze_repo_coverlet(tmp_path, tmp_path / "out")
        assert result["summary"]["error"] == "No coverage data collected"

    def test_successful_coverlet_analysis(self, tmp_path: Path):
        from scripts.analyze import analyze_repo_coverlet
        coverlet_data = {
            "_coverlet_data": True,
            "line_rate": 0.85,
            "branch_rate": 0.5,
            "lines_covered": 85,
            "lines_valid": 100,
            "assemblies": [
                {"name": "Lib", "covered_statements": 85, "total_statements": 100, "statement_coverage_pct": 85.0}
            ],
            "types": [
                {"assembly": "Lib", "namespace": None, "name": "Foo", "file_path": "src/Foo.cs",
                 "covered_statements": 85, "total_statements": 100, "statement_coverage_pct": 85.0}
            ],
            "methods": [],
        }
        with patch("scripts.analyze.get_coverlet_version", return_value="coverlet (9.0)"), \
             patch("scripts.analyze.shutil.which", return_value="/usr/bin/dotnet"), \
             patch("scripts.analyze.run_coverlet", return_value=(coverlet_data, Path("/tmp/cob.xml"))):
            result = analyze_repo_coverlet(tmp_path, tmp_path / "out")
        assert result["summary"]["total_assemblies"] == 1
        assert result["summary"]["statement_coverage_pct"] == 85.0
        assert result["backend"] == "coverlet"


# --- main() / CLI -----------------------------------------------------------

class TestMain:
    """Test main() entry point with mocked CLI args."""

    def test_main_returns_zero_on_success(self, tmp_path: Path):
        from scripts.analyze import main
        output_dir = tmp_path / "outputs" / "run-1"
        output_dir.mkdir(parents=True)
        output_path = output_dir / "output.json"

        fake_common = MagicMock()
        fake_common.repo_path = tmp_path
        fake_common.output_dir = output_dir
        fake_common.output_path = output_path
        fake_common.run_id = "run-1"
        fake_common.repo_id = "repo-1"
        fake_common.branch = "main"
        fake_common.commit = "a" * 40

        analysis_data = {
            "tool": "dotcover",
            "tool_version": "2025.3.2",
            "backend": "dotcover",
            "summary": {
                "total_assemblies": 0, "total_types": 0, "total_methods": 0,
                "covered_statements": 0, "total_statements": 0, "statement_coverage_pct": 0.0,
            },
            "assemblies": [], "types": [], "methods": [],
        }

        with patch("scripts.analyze.argparse.ArgumentParser") as mock_parser_cls, \
             patch("scripts.analyze.add_common_args"), \
             patch("scripts.analyze.validate_common_args", return_value=fake_common), \
             patch("scripts.analyze.analyze_repo", return_value=analysis_data), \
             patch("scripts.analyze.create_envelope", return_value={"metadata": {}, "data": analysis_data}):
            mock_parser = MagicMock()
            mock_parser.parse_args.return_value = MagicMock(
                test_project=None, docker=False, backend="dotcover",
            )
            mock_parser_cls.return_value = mock_parser
            result = main()

        assert result == 0
        assert output_path.exists()
