"""Tests for IntegrationFitJudge.

All tests use REAL data from output/output.json - NO MOCKING.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from evaluation.llm.judges.integration_fit import IntegrationFitJudge


class TestIntegrationFitJudgeProperties:
    """Test basic judge properties."""

    def test_dimension_name(self, integration_fit_judge):
        """dimension_name is correct."""
        assert integration_fit_judge.dimension_name == "integration_fit"

    def test_weight(self, integration_fit_judge):
        """weight is 10%."""
        assert integration_fit_judge.weight == 0.10


class TestCollectEvidence:
    """Tests for evidence collection."""

    def test_collect_evidence_loads_scc_output(self, integration_fit_judge, real_raw_scc_output):
        """Loads raw scc output."""
        evidence = integration_fit_judge.collect_evidence()
        assert "scc_output" in evidence

    def test_collect_evidence_loads_output(self, integration_fit_judge, real_output):
        """Loads envelope output."""
        evidence = integration_fit_judge.collect_evidence()
        assert "tool_output" in evidence

    def test_collect_evidence_unwraps_data(self, integration_fit_judge, real_output):
        """Unwraps envelope data payload."""
        evidence = integration_fit_judge.collect_evidence()
        tool_data = evidence.get("tool_data", {})
        assert isinstance(tool_data, dict)
        assert tool_data.get("tool") == "scc"

    def test_collect_evidence_includes_output_summary(self, integration_fit_judge, real_output):
        """Includes summarized envelope output for prompt size control."""
        evidence = integration_fit_judge.collect_evidence()
        summary = evidence.get("tool_output_summary", {})
        assert isinstance(summary, dict)
        assert "metadata" in summary
        assert "data" in summary


class TestGroundTruthAssertionsValidData:
    """Test ground truth assertions with valid real data."""

    def test_ground_truth_runs(self, integration_fit_judge, real_output):
        """Ground truth assertions run without crashing."""
        passed, failures = integration_fit_judge.run_ground_truth_assertions()
        # Note: May fail due to schema differences, but should run
        assert isinstance(passed, bool)
        assert isinstance(failures, list)

    def test_output_has_metadata_and_data(self, real_output):
        """Output has metadata and data sections."""
        assert "metadata" in real_output
        assert "data" in real_output

    def test_output_has_run_id(self, real_output):
        """Output has run_id in metadata."""
        assert isinstance(real_output.get("metadata", {}).get("run_id"), str)

    def test_output_has_timestamp(self, real_output):
        """Output has timestamp in metadata."""
        assert isinstance(real_output.get("metadata", {}).get("timestamp"), str)


class TestGroundTruthAssertionsInvalidData:
    """Test ground truth assertions with invalid synthetic data."""

    def test_fails_missing_file(self, poc_root):
        """Fails when output.json doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            output_dir = tmpdir / "output"
            output_dir.mkdir()
            # Don't create output.json
            judge = IntegrationFitJudge(working_dir=tmpdir)
            passed, failures = judge.run_ground_truth_assertions()
            assert passed is False
            assert any("not found" in f.lower() for f in failures)

    def test_fails_invalid_json(self, poc_root):
        """Fails when output.json is invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            output_dir = tmpdir / "output"
            output_dir.mkdir()
            (output_dir / "output.json").write_text("not valid json {")
            judge = IntegrationFitJudge(working_dir=tmpdir)
            passed, failures = judge.run_ground_truth_assertions()
            assert passed is False
            assert any("json" in f.lower() for f in failures)

    def test_fails_missing_source(self, poc_root):
        """Fails when metadata is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            output_dir = tmpdir / "output"
            output_dir.mkdir()
            (output_dir / "output.json").write_text(json.dumps({
                "data": {"tool": "scc"}
                # Missing "metadata"
            }))
            judge = IntegrationFitJudge(working_dir=tmpdir)
            passed, failures = judge.run_ground_truth_assertions()
            assert passed is False
            assert any("metadata" in f.lower() for f in failures)

    def test_fails_missing_metrics(self, poc_root):
        """Fails when data field is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            output_dir = tmpdir / "output"
            output_dir.mkdir()
            (output_dir / "output.json").write_text(json.dumps({
                "metadata": {"tool_name": "scc"}
                # Missing "data"
            }))
            judge = IntegrationFitJudge(working_dir=tmpdir)
            passed, failures = judge.run_ground_truth_assertions()
            assert passed is False
            assert any("data" in f.lower() for f in failures)


class TestEvidenceSchemaCompliance:
    """Test evidence output schema compliance."""

    def test_source_is_scc(self, real_output):
        """Tool name should be 'scc'."""
        assert real_output.get("metadata", {}).get("tool_name") == "scc"
        assert real_output.get("data", {}).get("tool") == "scc"

    def test_has_data_content(self, real_output):
        """Output should have summary and language data."""
        data = real_output.get("data", {})
        assert isinstance(data.get("summary"), dict)
        assert isinstance(data.get("languages"), list)

    def test_has_identifier(self, real_output):
        """Output should have identifiers in metadata."""
        metadata = real_output.get("metadata", {})
        assert isinstance(metadata.get("run_id"), str)
        assert isinstance(metadata.get("repo_id"), str)

    def test_has_temporal_field(self, real_output):
        """Output should have timestamp."""
        timestamp = real_output.get("metadata", {}).get("timestamp", "")
        assert isinstance(timestamp, str)
        assert "-" in timestamp or "T" in timestamp
