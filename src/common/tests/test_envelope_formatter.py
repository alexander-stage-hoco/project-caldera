"""Tests for envelope_formatter module."""

from __future__ import annotations

import re
from datetime import datetime, timezone

import pytest

from common.envelope_formatter import create_envelope, get_current_timestamp


class TestGetCurrentTimestamp:
    """Tests for get_current_timestamp function."""

    def test_returns_valid_iso_format(self) -> None:
        """Timestamp should be valid ISO 8601 format."""
        timestamp = get_current_timestamp()

        # Should be parseable as ISO format
        parsed = datetime.fromisoformat(timestamp)
        assert parsed is not None

    def test_includes_timezone_info(self) -> None:
        """Timestamp should include UTC timezone."""
        timestamp = get_current_timestamp()

        # Should end with +00:00 for UTC
        assert timestamp.endswith("+00:00")

    def test_is_current_time(self) -> None:
        """Timestamp should be close to current time."""
        before = datetime.now(timezone.utc)
        timestamp = get_current_timestamp()
        after = datetime.now(timezone.utc)

        parsed = datetime.fromisoformat(timestamp)
        assert before <= parsed <= after


class TestCreateEnvelope:
    """Tests for create_envelope function."""

    @pytest.fixture
    def sample_data(self) -> dict:
        """Sample tool output data."""
        return {
            "files": [{"path": "src/main.py", "lines": 100}],
            "summary": {"total_files": 1, "total_lines": 100},
        }

    @pytest.fixture
    def sample_metadata(self) -> dict:
        """Sample metadata arguments."""
        return {
            "tool_name": "test-tool",
            "tool_version": "1.0.0",
            "run_id": "run-123",
            "repo_id": "repo-456",
            "branch": "main",
            "commit": "a" * 40,
        }

    def test_produces_correct_structure(
        self, sample_data: dict, sample_metadata: dict
    ) -> None:
        """Envelope should have metadata and data keys."""
        envelope = create_envelope(sample_data, **sample_metadata)

        assert "metadata" in envelope
        assert "data" in envelope
        assert len(envelope) == 2

    def test_includes_all_required_metadata_fields(
        self, sample_data: dict, sample_metadata: dict
    ) -> None:
        """Metadata should contain all required fields."""
        envelope = create_envelope(sample_data, **sample_metadata)
        metadata = envelope["metadata"]

        assert metadata["tool_name"] == "test-tool"
        assert metadata["tool_version"] == "1.0.0"
        assert metadata["run_id"] == "run-123"
        assert metadata["repo_id"] == "repo-456"
        assert metadata["branch"] == "main"
        assert metadata["commit"] == "a" * 40
        assert "timestamp" in metadata
        assert metadata["schema_version"] == "1.0.0"

    def test_data_preserved_unchanged(
        self, sample_data: dict, sample_metadata: dict
    ) -> None:
        """Data section should be the input data unchanged."""
        envelope = create_envelope(sample_data, **sample_metadata)

        assert envelope["data"] == sample_data
        assert envelope["data"]["files"][0]["path"] == "src/main.py"

    def test_auto_generates_timestamp_if_not_provided(
        self, sample_data: dict, sample_metadata: dict
    ) -> None:
        """Timestamp should be auto-generated when not provided."""
        before = datetime.now(timezone.utc)
        envelope = create_envelope(sample_data, **sample_metadata)
        after = datetime.now(timezone.utc)

        timestamp = envelope["metadata"]["timestamp"]
        parsed = datetime.fromisoformat(timestamp)
        assert before <= parsed <= after

    def test_respects_provided_timestamp(
        self, sample_data: dict, sample_metadata: dict
    ) -> None:
        """Should use provided timestamp instead of generating one."""
        custom_timestamp = "2024-01-15T10:30:00+00:00"
        envelope = create_envelope(
            sample_data, **sample_metadata, timestamp=custom_timestamp
        )

        assert envelope["metadata"]["timestamp"] == custom_timestamp

    def test_custom_schema_version(
        self, sample_data: dict, sample_metadata: dict
    ) -> None:
        """Should allow custom schema version."""
        envelope = create_envelope(
            sample_data, **sample_metadata, schema_version="2.0.0"
        )

        assert envelope["metadata"]["schema_version"] == "2.0.0"

    def test_merges_extra_metadata(
        self, sample_data: dict, sample_metadata: dict
    ) -> None:
        """Extra metadata should be merged into metadata section."""
        extra = {"repo_name": "my-repo", "repo_path": "/path/to/repo"}
        envelope = create_envelope(
            sample_data, **sample_metadata, extra_metadata=extra
        )

        assert envelope["metadata"]["repo_name"] == "my-repo"
        assert envelope["metadata"]["repo_path"] == "/path/to/repo"

    def test_extra_metadata_does_not_override_standard_fields(
        self, sample_data: dict, sample_metadata: dict
    ) -> None:
        """Extra metadata should not override standard fields."""
        extra = {"tool_name": "malicious-override", "custom_field": "allowed"}
        envelope = create_envelope(
            sample_data, **sample_metadata, extra_metadata=extra
        )

        # Standard field should not be overridden
        assert envelope["metadata"]["tool_name"] == "test-tool"
        # Custom field should be added
        assert envelope["metadata"]["custom_field"] == "allowed"

    def test_empty_data(self, sample_metadata: dict) -> None:
        """Should work with empty data dictionary."""
        envelope = create_envelope({}, **sample_metadata)

        assert envelope["data"] == {}
        assert "metadata" in envelope

    def test_nested_data_preserved(self, sample_metadata: dict) -> None:
        """Deeply nested data should be preserved."""
        nested_data = {
            "level1": {
                "level2": {
                    "level3": [1, 2, {"nested": True}],
                },
            },
        }
        envelope = create_envelope(nested_data, **sample_metadata)

        assert envelope["data"]["level1"]["level2"]["level3"][2]["nested"] is True


class TestEnvelopeConsistency:
    """Tests ensuring envelope format consistency across tools."""

    @pytest.mark.parametrize(
        "tool_name",
        [
            "scc",
            "semgrep",
            "devskim",
            "layout-scanner",
            "scancode",
            "sonarqube",
            "roslyn-analyzers",
            "trivy",
            "symbol-scanner",
        ],
    )
    def test_all_tools_produce_same_structure(self, tool_name: str) -> None:
        """All tools should produce identical envelope structure."""
        envelope = create_envelope(
            {"tool": tool_name},
            tool_name=tool_name,
            tool_version="1.0.0",
            run_id="test-run",
            repo_id="test-repo",
            branch="main",
            commit="b" * 40,
        )

        # Verify structure
        assert set(envelope.keys()) == {"metadata", "data"}
        assert set(envelope["metadata"].keys()) == {
            "tool_name",
            "tool_version",
            "run_id",
            "repo_id",
            "branch",
            "commit",
            "timestamp",
            "schema_version",
        }
