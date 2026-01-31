"""Tests for the export module."""

import json
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import Mock

from scripts.export import (
    SCHEMA_VERSION,
    compute_hotspots,
    compute_directory_rollups,
    build_export_data,
    export_unified_json,
    validate_export,
    export_summary,
)
from scripts.api.module_b_components import ComponentTree, Component, ComponentQualifier
from scripts.api.module_c_catalog import MetricCatalog, Metric, MetricType
from scripts.api.module_d_measures import MeasuresResult, ComponentMeasures, Measure
from scripts.api.module_e_issues import IssuesResult, Issue, IssueSeverity, IssueType, IssueStatus, IssueRollups
from scripts.api.module_f_rules import RulesCache, Rule, RuleType, RuleSeverity, RuleStatus
from scripts.api.module_g_duplications import DuplicationsResult, DuplicationPolicy
from scripts.api.module_h_quality_gate import QualityGateResult, QualityGateStatus
from scripts.api.module_i_history import AnalysisHistory


class TestComputeHotspots:
    """Tests for compute_hotspots."""

    def test_empty_components(self):
        """Test with no components."""
        components = ComponentTree(
            root=Component(key="proj", name="Project", qualifier=ComponentQualifier.PROJECT)
        )
        measures = MeasuresResult()
        issues = IssuesResult()

        hotspots = compute_hotspots(components, measures, issues)

        assert hotspots == []

    def test_computes_hotspots(self):
        """Test hotspot computation with data."""
        # Create components
        root = Component(key="proj", name="Project", qualifier=ComponentQualifier.PROJECT)
        file1 = Component(
            key="proj:src/file1.py",
            name="file1.py",
            qualifier=ComponentQualifier.FILE,
            path="src/file1.py",
            language="py",
        )
        file2 = Component(
            key="proj:src/file2.py",
            name="file2.py",
            qualifier=ComponentQualifier.FILE,
            path="src/file2.py",
            language="py",
        )

        components = ComponentTree(
            root=root,
            by_key={
                "proj": root,
                "proj:src/file1.py": file1,
                "proj:src/file2.py": file2,
            },
        )

        # Create measures
        measures = MeasuresResult(
            by_component_key={
                "proj:src/file1.py": ComponentMeasures(
                    key="proj:src/file1.py",
                    name="file1.py",
                    qualifier="FIL",
                    path="src/file1.py",
                    language="py",
                    measures=[
                        Measure(metric="ncloc", value="100"),
                        Measure(metric="complexity", value="20"),
                        Measure(metric="cognitive_complexity", value="15"),
                    ],
                ),
                "proj:src/file2.py": ComponentMeasures(
                    key="proj:src/file2.py",
                    name="file2.py",
                    qualifier="FIL",
                    path="src/file2.py",
                    language="py",
                    measures=[
                        Measure(metric="ncloc", value="50"),
                        Measure(metric="complexity", value="5"),
                        Measure(metric="cognitive_complexity", value="3"),
                    ],
                ),
            }
        )

        # Create issues
        issues = IssuesResult(
            rollups=IssueRollups(
                by_file={"proj:src/file1.py": 10, "proj:src/file2.py": 2}
            )
        )

        hotspots = compute_hotspots(components, measures, issues, top_n=5)

        assert len(hotspots) == 2
        # file1 should have higher score (more complexity, more issues)
        assert hotspots[0]["path"] == "src/file1.py"
        assert hotspots[0]["score"] > hotspots[1]["score"]


class TestComputeDirectoryRollups:
    """Tests for compute_directory_rollups."""

    def test_empty_components(self):
        """Test with no components."""
        components = ComponentTree(
            root=Component(key="proj", name="Project", qualifier=ComponentQualifier.PROJECT)
        )
        measures = MeasuresResult()
        issues = IssuesResult()

        rollups = compute_directory_rollups(components, measures, issues)

        assert rollups == {}

    def test_computes_rollups(self):
        """Test directory rollup computation."""
        root = Component(key="proj", name="Project", qualifier=ComponentQualifier.PROJECT)
        file1 = Component(
            key="proj:src/utils/file1.py",
            name="file1.py",
            qualifier=ComponentQualifier.FILE,
            path="src/utils/file1.py",
        )
        file2 = Component(
            key="proj:src/utils/file2.py",
            name="file2.py",
            qualifier=ComponentQualifier.FILE,
            path="src/utils/file2.py",
        )

        components = ComponentTree(
            root=root,
            by_key={
                "proj": root,
                "proj:src/utils/file1.py": file1,
                "proj:src/utils/file2.py": file2,
            },
        )

        measures = MeasuresResult(
            by_component_key={
                "proj:src/utils/file1.py": ComponentMeasures(
                    key="proj:src/utils/file1.py",
                    name="file1.py",
                    qualifier="FIL",
                    path="src/utils/file1.py",
                    language="py",
                    measures=[Measure(metric="ncloc", value="100")],
                ),
                "proj:src/utils/file2.py": ComponentMeasures(
                    key="proj:src/utils/file2.py",
                    name="file2.py",
                    qualifier="FIL",
                    path="src/utils/file2.py",
                    language="py",
                    measures=[Measure(metric="ncloc", value="50")],
                ),
            }
        )

        issues = IssuesResult()

        rollups = compute_directory_rollups(components, measures, issues)

        assert "src/utils" in rollups
        assert rollups["src/utils"]["files"] == 2
        assert rollups["src/utils"]["ncloc"] == 150


class TestBuildExportData:
    """Tests for build_export_data."""

    def test_builds_complete_export(self):
        """Test building complete export data."""
        source = {
            "sonarqube_url": "http://localhost:9000",
            "project_key": "my-project",
            "analysis_id": "123",
            "revision": "abc123",
        }

        root = Component(key="proj", name="Project", qualifier=ComponentQualifier.PROJECT)
        components = ComponentTree(root=root, by_key={"proj": root})

        metric_catalog = MetricCatalog(metrics={})
        measures = MeasuresResult()
        issues = IssuesResult()
        rules = RulesCache()
        duplications = DuplicationsResult(policy=DuplicationPolicy())
        quality_gate = QualityGateResult(status=QualityGateStatus.OK)
        analyses = AnalysisHistory()

        data = build_export_data(
            source=source,
            metric_catalog=metric_catalog,
            components=components,
            measures=measures,
            issues=issues,
            rules=rules,
            duplications=duplications,
            quality_gate=quality_gate,
            analyses=analyses,
        )

        assert data["schema_version"] == SCHEMA_VERSION
        assert "generated_at" in data
        assert data["results"]["source"]["project_key"] == "my-project"
        assert "components" in data["results"]
        assert "measures" in data["results"]
        assert "issues" in data["results"]
        assert "quality_gate" in data["results"]
        assert "derived_insights" in data["results"]
        assert "limitations" in data["results"]

    def test_builds_export_with_metadata(self):
        """Test metadata inclusion in export data."""
        source = {
            "sonarqube_url": "http://localhost:9000",
            "project_key": "my-project",
            "repo_name": "my-project",
            "repo_path": "/tmp/my-project",
        }

        root = Component(key="proj", name="Project", qualifier=ComponentQualifier.PROJECT)
        components = ComponentTree(root=root, by_key={"proj": root})

        metadata = {
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-01-01T00:01:00Z",
            "duration_ms": 60000,
            "peak_memory_mb": 123.4,
            "total_api_time_ms": 1200.0,
            "api_calls": [
                {
                    "method": "GET",
                    "endpoint": "/api/test",
                    "duration_ms": 12.3,
                    "status_code": 200,
                }
            ],
        }

        data = build_export_data(
            source=source,
            metric_catalog=MetricCatalog(metrics={}),
            components=components,
            measures=MeasuresResult(),
            issues=IssuesResult(),
            rules=RulesCache(),
            duplications=DuplicationsResult(policy=DuplicationPolicy()),
            quality_gate=QualityGateResult(status=QualityGateStatus.OK),
            analyses=AnalysisHistory(),
            metadata=metadata,
        )

        assert data["metadata"]["duration_ms"] == 60000


class TestExportUnifiedJson:
    """Tests for export_unified_json."""

    def test_writes_json_file(self, tmp_path):
        """Test writing JSON to file."""
        output_path = tmp_path / "output.json"

        source = {
            "sonarqube_url": "http://localhost:9000",
            "project_key": "test-project",
        }

        root = Component(key="proj", name="Project", qualifier=ComponentQualifier.PROJECT)
        components = ComponentTree(root=root, by_key={"proj": root})

        result = export_unified_json(
            output_path=output_path,
            source=source,
            metric_catalog=MetricCatalog(metrics={}),
            components=components,
            measures=MeasuresResult(),
            issues=IssuesResult(),
            rules=RulesCache(),
            duplications=DuplicationsResult(policy=DuplicationPolicy()),
            quality_gate=QualityGateResult(status=QualityGateStatus.OK),
            analyses=AnalysisHistory(),
        )

        assert output_path.exists()
        assert result["schema_version"] == SCHEMA_VERSION

        # Verify it's valid JSON
        with open(output_path) as f:
            loaded = json.load(f)
        assert loaded["schema_version"] == SCHEMA_VERSION


class TestExportSummary:
    """Tests for export_summary."""

    def test_creates_summary(self):
        """Test creating a summary."""
        data = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": "2024-01-01T00:00:00Z",
            "results": {
                "source": {"project_key": "my-project"},
                "quality_gate": {"status": "OK"},
                "issues": {
                    "rollups": {
                        "total": 100,
                        "by_type": {
                            "BUG": 10,
                            "VULNERABILITY": 5,
                            "CODE_SMELL": 85,
                        },
                    },
                },
                "components": {
                    "by_key": {
                        "proj": {"qualifier": "TRK"},
                        "proj:file1.py": {"qualifier": "FIL"},
                        "proj:file2.py": {"qualifier": "FIL"},
                    },
                },
                "derived_insights": {
                    "hotspots": [{"path": "file1.py"}],
                },
            },
        }

        summary = export_summary(data)

        assert summary["project_key"] == "my-project"
        assert summary["quality_gate_status"] == "OK"
        assert summary["total_issues"] == 100
        assert summary["bugs"] == 10
        assert summary["vulnerabilities"] == 5
        assert summary["code_smells"] == 85
        assert summary["files"] == 2
        assert summary["hotspots_count"] == 1
