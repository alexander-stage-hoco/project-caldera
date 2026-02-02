"""
Unit tests for LLM observability module.

Tests cover:
- Schema serialization/deserialization
- Config from environment
- Logger request/response lifecycle
- FileStore persistence and querying
- ObservableProvider wrapping
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from shared.observability import (
    LLMInteraction,
    EvaluationSpan,
    ObservabilityConfig,
    get_config,
    set_config,
    reset_config,
    LLMLogger,
    get_llm_logger,
    reset_llm_logger,
    FileStore,
)
from insights.evaluation.llm.observability import ObservableProvider
from insights.evaluation.llm.providers import LLMProvider, LLMResponse


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_interaction():
    """Create a sample LLMInteraction for testing."""
    now = datetime.now()
    return LLMInteraction(
        interaction_id="int-123",
        trace_id="trace-456",
        timestamp_start=now,
        timestamp_end=now + timedelta(seconds=2),
        duration_ms=2000,
        provider_name="claude_code",
        judge_name="clarity",
        model="claude-opus-4-5",
        system_prompt="You are a code reviewer.",
        user_prompt="Evaluate this report.",
        prompt_tokens=100,
        response_content='{"overall_score": 4.0, "reasoning": "Good report"}',
        completion_tokens=50,
        total_tokens=150,
        status="success",
        parsed_score=4.0,
        parsed_reasoning="Good report",
    )


@pytest.fixture
def mock_provider():
    """Create a mock LLM provider."""
    provider = MagicMock(spec=LLMProvider)
    provider.name = "mock_provider"
    provider.default_model = "mock-model"
    provider.supports_model.return_value = True
    provider.complete.return_value = LLMResponse(
        content='{"overall_score": 4.0, "reasoning": "Test response"}',
        model="mock-model",
        usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
    )
    return provider


@pytest.fixture
def clean_config():
    """Reset config before and after each test."""
    reset_config()
    reset_llm_logger()
    yield
    reset_config()
    reset_llm_logger()


# ============================================================================
# Schema Tests
# ============================================================================


class TestLLMInteraction:
    """Tests for LLMInteraction schema."""

    def test_to_dict(self, sample_interaction):
        """Test conversion to dictionary."""
        data = sample_interaction.to_dict()

        assert data["interaction_id"] == "int-123"
        assert data["trace_id"] == "trace-456"
        assert data["provider_name"] == "claude_code"
        assert data["judge_name"] == "clarity"
        assert data["status"] == "success"
        assert data["parsed_score"] == 4.0
        # Datetime should be ISO string
        assert isinstance(data["timestamp_start"], str)
        assert "T" in data["timestamp_start"]

    def test_to_json(self, sample_interaction):
        """Test JSON serialization."""
        json_str = sample_interaction.to_json()
        data = json.loads(json_str)

        assert data["interaction_id"] == "int-123"
        assert data["duration_ms"] == 2000

    def test_from_dict(self, sample_interaction):
        """Test creation from dictionary."""
        data = sample_interaction.to_dict()
        restored = LLMInteraction.from_dict(data)

        assert restored.interaction_id == sample_interaction.interaction_id
        assert restored.trace_id == sample_interaction.trace_id
        assert restored.provider_name == sample_interaction.provider_name
        assert restored.parsed_score == sample_interaction.parsed_score

    def test_roundtrip(self, sample_interaction):
        """Test JSON roundtrip preserves data."""
        json_str = sample_interaction.to_json()
        data = json.loads(json_str)
        restored = LLMInteraction.from_dict(data)

        assert restored.interaction_id == sample_interaction.interaction_id
        assert restored.status == sample_interaction.status


class TestEvaluationSpan:
    """Tests for EvaluationSpan schema."""

    def test_from_interactions(self, sample_interaction):
        """Test creating span from interactions."""
        interactions = [sample_interaction]
        span = EvaluationSpan.from_interactions(
            trace_id="trace-456",
            interactions=interactions,
            overall_score=4.0,
            pass_status="PASS",
        )

        assert span.trace_id == "trace-456"
        assert span.judge_count == 1
        assert span.successful_judges == 1
        assert span.failed_judges == 0
        assert span.overall_score == 4.0

    def test_from_empty_interactions(self):
        """Test creating span from empty list."""
        span = EvaluationSpan.from_interactions(
            trace_id="empty-trace",
            interactions=[],
        )

        assert span.trace_id == "empty-trace"
        assert span.judge_count == 0
        assert span.total_duration_ms == 0


# ============================================================================
# Config Tests
# ============================================================================


class TestObservabilityConfig:
    """Tests for ObservabilityConfig."""

    def test_defaults(self, clean_config):
        """Test default configuration values."""
        config = ObservabilityConfig()

        assert config.enabled is True
        assert config.log_to_file is True
        assert config.log_to_console is False
        assert config.include_prompts is True
        assert config.retention_days == 30

    def test_from_env(self, clean_config):
        """Test loading config from environment."""
        with patch.dict(os.environ, {
            "LLM_OBSERVABILITY_ENABLED": "false",
            "LLM_OBSERVABILITY_LOG_DIR": "/custom/logs",
            "LLM_OBSERVABILITY_CONSOLE": "true",
        }):
            config = ObservabilityConfig.from_env()

            assert config.enabled is False
            assert config.log_dir == Path("/custom/logs")
            assert config.log_to_console is True

    def test_global_config(self, clean_config):
        """Test global config singleton."""
        config1 = get_config()
        config2 = get_config()

        assert config1 is config2

    def test_set_config(self, clean_config):
        """Test setting custom config."""
        custom = ObservabilityConfig(enabled=False, retention_days=7)
        set_config(custom)

        config = get_config()
        assert config.enabled is False
        assert config.retention_days == 7


# ============================================================================
# Logger Tests
# ============================================================================


class TestLLMLogger:
    """Tests for LLMLogger."""

    def test_start_and_complete_interaction(self, temp_log_dir, clean_config):
        """Test full interaction lifecycle."""
        config = ObservabilityConfig(log_dir=temp_log_dir, log_to_console=False)
        store = FileStore(base_dir=temp_log_dir)
        logger = LLMLogger(config=config, store=store)

        # Start interaction
        interaction_id = logger.start_interaction(
            trace_id="test-trace",
            provider_name="test_provider",
            judge_name="clarity",
            model="test-model",
            system_prompt="System",
            user_prompt="User prompt",
        )

        assert interaction_id is not None
        assert logger.get_pending_count() == 1

        # Complete interaction
        interaction = logger.complete_interaction(
            interaction_id=interaction_id,
            response_content="Response content",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            status="success",
            parsed_score=4.5,
        )

        assert interaction is not None
        assert interaction.trace_id == "test-trace"
        assert interaction.status == "success"
        assert interaction.parsed_score == 4.5
        assert logger.get_pending_count() == 0

    def test_log_error(self, temp_log_dir, clean_config):
        """Test error logging."""
        config = ObservabilityConfig(log_dir=temp_log_dir)
        logger = LLMLogger(config=config)

        interaction_id = logger.start_interaction(
            provider_name="test",
            user_prompt="Test",
        )

        interaction = logger.log_error(interaction_id, Exception("Test error"))

        assert interaction is not None
        assert interaction.status == "error"
        assert "Test error" in interaction.error_message

    def test_log_timeout(self, temp_log_dir, clean_config):
        """Test timeout logging."""
        config = ObservabilityConfig(log_dir=temp_log_dir)
        logger = LLMLogger(config=config)

        interaction_id = logger.start_interaction(
            provider_name="test",
            user_prompt="Test",
        )

        interaction = logger.log_timeout(interaction_id, timeout_seconds=120)

        assert interaction is not None
        assert interaction.status == "timeout"
        assert "120" in interaction.error_message

    def test_disabled_logger(self, clean_config):
        """Test that disabled logger doesn't persist."""
        config = ObservabilityConfig(enabled=False)
        logger = LLMLogger(config=config)

        interaction_id = logger.start_interaction(
            provider_name="test",
            user_prompt="Test",
        )

        # Should still return an ID but not track
        assert interaction_id is not None

        result = logger.complete_interaction(interaction_id, response_content="Response")
        assert result is None

    def test_prompt_truncation(self, temp_log_dir, clean_config):
        """Test prompt truncation with max_prompt_length."""
        config = ObservabilityConfig(
            log_dir=temp_log_dir,
            max_prompt_length=50,
        )
        logger = LLMLogger(config=config)

        long_prompt = "A" * 100
        interaction_id = logger.start_interaction(
            provider_name="test",
            user_prompt=long_prompt,
        )

        interaction = logger.complete_interaction(
            interaction_id=interaction_id,
            response_content="Response",
        )

        assert len(interaction.user_prompt) < 100
        assert "[truncated]" in interaction.user_prompt


# ============================================================================
# FileStore Tests
# ============================================================================


class TestFileStore:
    """Tests for FileStore."""

    def test_append_and_read(self, temp_log_dir, sample_interaction):
        """Test appending and reading interactions."""
        store = FileStore(base_dir=temp_log_dir)

        store.append(sample_interaction)
        interactions = store.read_date()

        assert len(interactions) == 1
        assert interactions[0].interaction_id == sample_interaction.interaction_id

    def test_query_by_trace(self, temp_log_dir, sample_interaction):
        """Test querying by trace ID."""
        store = FileStore(base_dir=temp_log_dir)

        # Add multiple interactions with different traces
        store.append(sample_interaction)

        other = LLMInteraction(
            interaction_id="other-123",
            trace_id="other-trace",
            timestamp_start=datetime.now(),
            timestamp_end=datetime.now(),
            duration_ms=1000,
            provider_name="test",
            judge_name=None,
            model="test",
            system_prompt=None,
            user_prompt="Test",
        )
        store.append(other)

        results = store.query_by_trace("trace-456")
        assert len(results) == 1
        assert results[0].trace_id == "trace-456"

    def test_query_by_judge(self, temp_log_dir, sample_interaction):
        """Test querying by judge name."""
        store = FileStore(base_dir=temp_log_dir)
        store.append(sample_interaction)

        results = store.query_by_judge("clarity")
        assert len(results) == 1

        results = store.query_by_judge("actionability")
        assert len(results) == 0

    def test_query_by_status(self, temp_log_dir, sample_interaction):
        """Test querying by status."""
        store = FileStore(base_dir=temp_log_dir)
        store.append(sample_interaction)

        results = store.query_by_status("success")
        assert len(results) == 1

        results = store.query_by_status("error")
        assert len(results) == 0

    def test_get_stats(self, temp_log_dir, sample_interaction):
        """Test statistics calculation."""
        store = FileStore(base_dir=temp_log_dir)
        store.append(sample_interaction)

        stats = store.get_stats()

        assert stats["total_count"] == 1
        assert stats["success_count"] == 1
        assert stats["error_count"] == 0
        assert stats["unique_traces"] == 1
        assert "clarity" in stats["judges"]

    def test_get_evaluation_span(self, temp_log_dir, sample_interaction):
        """Test building evaluation span from interactions."""
        store = FileStore(base_dir=temp_log_dir)
        store.append(sample_interaction)

        span = store.get_evaluation_span("trace-456")

        assert span is not None
        assert span.trace_id == "trace-456"
        assert span.judge_count == 1

    def test_list_dates(self, temp_log_dir, sample_interaction):
        """Test listing available dates."""
        store = FileStore(base_dir=temp_log_dir)
        store.append(sample_interaction)

        dates = store.list_dates()
        assert len(dates) == 1
        assert dates[0].date() == datetime.now().date()

    def test_empty_store(self, temp_log_dir):
        """Test operations on empty store."""
        store = FileStore(base_dir=temp_log_dir)

        assert store.read_date() == []
        assert store.query_by_trace("nonexistent") == []
        assert store.list_dates() == []
        assert store.get_stats()["total_count"] == 0


# ============================================================================
# ObservableProvider Tests
# ============================================================================


class TestObservableProvider:
    """Tests for ObservableProvider wrapper."""

    def test_wraps_provider(self, mock_provider, temp_log_dir, clean_config):
        """Test that observable provider wraps underlying provider."""
        config = ObservabilityConfig(log_dir=temp_log_dir)
        set_config(config)

        observable = ObservableProvider(mock_provider, trace_id="test-trace")

        assert observable.name == "mock_provider"
        assert observable.default_model == "mock-model"
        assert observable.trace_id == "test-trace"

    def test_complete_logs_interaction(self, mock_provider, temp_log_dir, clean_config):
        """Test that complete() logs the interaction."""
        config = ObservabilityConfig(log_dir=temp_log_dir)
        set_config(config)

        observable = ObservableProvider(
            mock_provider,
            trace_id="test-trace",
            judge_name="clarity",
        )

        response = observable.complete(
            prompt="Test prompt",
            system="System prompt",
            model="test-model",
        )

        assert response.content == '{"overall_score": 4.0, "reasoning": "Test response"}'

        # Check that interaction was logged
        store = FileStore(base_dir=temp_log_dir)
        interactions = store.query_by_trace("test-trace")

        assert len(interactions) == 1
        assert interactions[0].judge_name == "clarity"
        assert interactions[0].status == "success"

    def test_complete_logs_error(self, mock_provider, temp_log_dir, clean_config):
        """Test that errors are logged."""
        config = ObservabilityConfig(log_dir=temp_log_dir)
        set_config(config)

        mock_provider.complete.side_effect = RuntimeError("API error")

        observable = ObservableProvider(mock_provider, trace_id="error-trace")

        with pytest.raises(RuntimeError):
            observable.complete(prompt="Test")

        # Check that error was logged
        store = FileStore(base_dir=temp_log_dir)
        interactions = store.query_by_trace("error-trace")

        assert len(interactions) == 1
        assert interactions[0].status == "error"
        assert "API error" in interactions[0].error_message

    def test_with_judge(self, mock_provider, temp_log_dir, clean_config):
        """Test with_judge creates new provider with judge name."""
        config = ObservabilityConfig(log_dir=temp_log_dir)
        set_config(config)

        observable = ObservableProvider(mock_provider, trace_id="shared-trace")
        clarity_provider = observable.with_judge("clarity")
        accuracy_provider = observable.with_judge("accuracy")

        # Same trace ID
        assert clarity_provider.trace_id == "shared-trace"
        assert accuracy_provider.trace_id == "shared-trace"

        # Different judge names
        assert clarity_provider.judge_name == "clarity"
        assert accuracy_provider.judge_name == "accuracy"

    def test_supports_model_delegation(self, mock_provider, clean_config):
        """Test that supports_model delegates to wrapped provider."""
        observable = ObservableProvider(mock_provider)

        result = observable.supports_model("some-model")
        assert result is True
        mock_provider.supports_model.assert_called_with("some-model")


# ============================================================================
# Integration Tests
# ============================================================================


class TestObservabilityIntegration:
    """Integration tests for the full observability flow."""

    def test_full_evaluation_flow(self, mock_provider, temp_log_dir, clean_config):
        """Test full evaluation with multiple judges."""
        config = ObservabilityConfig(log_dir=temp_log_dir)
        set_config(config)

        trace_id = "eval-integration-test"

        # Simulate what orchestrator does
        judges = ["clarity", "actionability", "accuracy"]
        for judge_name in judges:
            observable = ObservableProvider(
                mock_provider,
                trace_id=trace_id,
                judge_name=judge_name,
            )
            observable.complete(prompt=f"Evaluate for {judge_name}")

        # Query all interactions for this trace
        store = FileStore(base_dir=temp_log_dir)
        interactions = store.query_by_trace(trace_id)

        assert len(interactions) == 3
        judge_names = {i.judge_name for i in interactions}
        assert judge_names == {"clarity", "actionability", "accuracy"}

        # Build span
        span = store.get_evaluation_span(trace_id)
        assert span.judge_count == 3
        assert span.successful_judges == 3

    def test_stats_across_multiple_evaluations(self, mock_provider, temp_log_dir, clean_config):
        """Test statistics across multiple evaluation runs."""
        config = ObservabilityConfig(log_dir=temp_log_dir)
        set_config(config)

        # Run multiple evaluations
        for i in range(3):
            trace_id = f"eval-{i}"
            for judge in ["clarity", "actionability"]:
                observable = ObservableProvider(
                    mock_provider,
                    trace_id=trace_id,
                    judge_name=judge,
                )
                observable.complete(prompt="Test")

        store = FileStore(base_dir=temp_log_dir)
        stats = store.get_stats()

        assert stats["total_count"] == 6
        assert stats["unique_traces"] == 3
        assert stats["judges"]["clarity"] == 3
        assert stats["judges"]["actionability"] == 3
