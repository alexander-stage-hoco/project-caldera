"""Unit tests for git-sizer analyze module."""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add scripts and src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from scripts.analyze import (
    ThresholdViolation,
    RepositoryMetrics,
    RepositoryAnalysis,
    format_bytes,
    calculate_threshold_level,
    calculate_health_grade,
    build_analysis_data,
    TOOL_NAME,
    SCHEMA_VERSION,
)
from common.envelope_formatter import create_envelope


class TestThresholdViolation:
    """Tests for ThresholdViolation dataclass."""

    def test_to_dict_minimal(self):
        """Test to_dict with minimal fields."""
        violation = ThresholdViolation(
            metric="max_blob_size",
            value="",
            raw_value=0,
            level=2,
        )
        result = violation.to_dict()
        assert result == {
            "metric": "max_blob_size",
            "level": 2,
        }

    def test_to_dict_full(self):
        """Test to_dict with all fields."""
        violation = ThresholdViolation(
            metric="max_blob_size",
            value="10.5 MiB",
            raw_value=11010048,
            level=2,
            object_ref="abc123:path/to/file",
        )
        result = violation.to_dict()
        assert result == {
            "metric": "max_blob_size",
            "value": "10.5 MiB",
            "raw_value": 11010048,
            "level": 2,
            "object_ref": "abc123:path/to/file",
        }


class TestRepositoryMetrics:
    """Tests for RepositoryMetrics dataclass."""

    def test_to_dict(self):
        """Test to_dict produces all expected fields."""
        metrics = RepositoryMetrics(
            commit_count=100,
            blob_count=500,
            max_blob_size=1024000,
        )
        result = metrics.to_dict()
        assert result["commit_count"] == 100
        assert result["blob_count"] == 500
        assert result["max_blob_size"] == 1024000
        # Check defaults
        assert result["tree_count"] == 0
        assert result["max_path_depth"] == 0


class TestFormatBytes:
    """Tests for format_bytes function."""

    def test_bytes(self):
        """Test formatting small values in bytes."""
        assert format_bytes(500) == "500 B"
        assert format_bytes(1023) == "1023 B"

    def test_kibibytes(self):
        """Test formatting in KiB."""
        assert format_bytes(1024) == "1.0 KiB"
        assert format_bytes(5120) == "5.0 KiB"

    def test_mebibytes(self):
        """Test formatting in MiB."""
        assert format_bytes(1048576) == "1.0 MiB"
        assert format_bytes(10485760) == "10.0 MiB"

    def test_gibibytes(self):
        """Test formatting in GiB."""
        assert format_bytes(1073741824) == "1.00 GiB"


class TestCalculateThresholdLevel:
    """Tests for calculate_threshold_level function."""

    def test_max_blob_size_levels(self):
        """Test max_blob_size thresholds."""
        # Below threshold
        assert calculate_threshold_level("max_blob_size", 500000) == 0
        # Level 1 (>= 1 MiB)
        assert calculate_threshold_level("max_blob_size", 1048576) == 1
        # Level 2 (>= 10 MiB)
        assert calculate_threshold_level("max_blob_size", 10485760) == 2
        # Level 3 (>= 50 MiB)
        assert calculate_threshold_level("max_blob_size", 52428800) == 3
        # Level 4 (>= 100 MiB)
        assert calculate_threshold_level("max_blob_size", 104857600) == 4

    def test_unknown_metric(self):
        """Test unknown metric returns 0."""
        assert calculate_threshold_level("unknown_metric", 1000000) == 0

    def test_max_path_depth_levels(self):
        """Test max_path_depth thresholds."""
        assert calculate_threshold_level("max_path_depth", 5) == 0
        assert calculate_threshold_level("max_path_depth", 10) == 1
        assert calculate_threshold_level("max_path_depth", 15) == 2
        assert calculate_threshold_level("max_path_depth", 20) == 3
        assert calculate_threshold_level("max_path_depth", 35) == 4


class TestCalculateHealthGrade:
    """Tests for calculate_health_grade function."""

    def test_no_violations(self):
        """Test A grade with no violations."""
        assert calculate_health_grade([]) == "A"

    def test_level_4_violation(self):
        """Test F grade with level 4 violation."""
        violations = [ThresholdViolation("test", "", 0, 4)]
        assert calculate_health_grade(violations) == "F"

    def test_level_3_violations(self):
        """Test D/D+ grade with level 3 violations."""
        v1 = [ThresholdViolation("test", "", 0, 3)]
        assert calculate_health_grade(v1) == "D+"

        v3 = [ThresholdViolation("test", "", 0, 3) for _ in range(3)]
        assert calculate_health_grade(v3) == "D"

    def test_level_2_violations(self):
        """Test C/C+ grade with level 2 violations."""
        v1 = [ThresholdViolation("test", "", 0, 2)]
        assert calculate_health_grade(v1) == "C+"

    def test_level_1_violations(self):
        """Test B/B+ grade with level 1 violations."""
        v1 = [ThresholdViolation("test", "", 0, 1)]
        assert calculate_health_grade(v1) == "B+"


class TestBuildAnalysisData:
    """Tests for build_analysis_data function and envelope creation."""

    def _create_envelope(self, analysis, run_id, repo_id, repo_name, branch, commit):
        """Helper to create envelope using build_analysis_data and create_envelope."""
        data = build_analysis_data(analysis=analysis, repo_name=repo_name)
        return create_envelope(
            data,
            tool_name=TOOL_NAME,
            tool_version=analysis.git_sizer_version,
            run_id=run_id,
            repo_id=repo_id,
            branch=branch,
            commit=commit,
            schema_version=SCHEMA_VERSION,
            extra_metadata={"repo_name": repo_name},
        )

    def test_envelope_structure(self):
        """Test envelope has correct structure."""
        metrics = RepositoryMetrics(commit_count=100, blob_count=500)
        analysis = RepositoryAnalysis(
            git_sizer_version="1.5.0",
            duration_ms=150,
            metrics=metrics,
            health_grade="A",
            violations=[],
            lfs_candidates=[],
            raw_output={},
        )

        envelope = self._create_envelope(
            analysis=analysis,
            run_id="550e8400-e29b-41d4-a716-446655440000",
            repo_id="660e8400-e29b-41d4-a716-446655440001",
            repo_name="test-repo",
            branch="main",
            commit="a" * 40,
        )

        # Check top-level keys
        assert "metadata" in envelope
        assert "data" in envelope

        # Check metadata
        metadata = envelope["metadata"]
        assert metadata["tool_name"] == "git-sizer"
        assert metadata["tool_version"] == "1.5.0"
        assert metadata["run_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert metadata["repo_id"] == "660e8400-e29b-41d4-a716-446655440001"
        assert metadata["branch"] == "main"
        assert metadata["commit"] == "a" * 40
        assert metadata["schema_version"] == "1.0.0"
        assert "timestamp" in metadata

        # Check data
        data = envelope["data"]
        assert data["tool"] == "git-sizer"
        assert data["health_grade"] == "A"
        assert data["duration_ms"] == 150
        assert "metrics" in data
        assert data["metrics"]["commit_count"] == 100

    def test_envelope_with_violations(self):
        """Test envelope includes violations."""
        metrics = RepositoryMetrics()
        violations = [
            ThresholdViolation("max_blob_size", "10 MiB", 10485760, 2, "ref:path")
        ]
        analysis = RepositoryAnalysis(
            git_sizer_version="1.5.0",
            duration_ms=150,
            metrics=metrics,
            health_grade="C+",
            violations=violations,
            lfs_candidates=["large.bin"],
            raw_output={},
        )

        envelope = self._create_envelope(
            analysis=analysis,
            run_id="test-run",
            repo_id="test-repo",
            repo_name="test-repo",
            branch="main",
            commit="b" * 40,
        )

        data = envelope["data"]
        assert len(data["violations"]) == 1
        assert data["violations"][0]["metric"] == "max_blob_size"
        assert data["lfs_candidates"] == ["large.bin"]

    def test_envelope_is_json_serializable(self):
        """Test envelope can be serialized to JSON."""
        metrics = RepositoryMetrics()
        analysis = RepositoryAnalysis(
            git_sizer_version="1.5.0",
            duration_ms=150,
            metrics=metrics,
            health_grade="A",
            violations=[],
            lfs_candidates=[],
            raw_output={"some": "data"},
        )

        envelope = self._create_envelope(
            analysis=analysis,
            run_id="test",
            repo_id="test",
            repo_name="test-repo",
            branch="main",
            commit="c" * 40,
        )

        # Should not raise
        json_str = json.dumps(envelope, indent=2)
        assert json_str is not None

        # Should round-trip
        parsed = json.loads(json_str)
        assert parsed == envelope
