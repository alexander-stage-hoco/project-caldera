"""Tests for LLMClient."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from shared.llm.client import (
    LLMClient,
    MODEL_MAP,
    CLI_MODEL_MAP,
    HAS_ANTHROPIC_SDK,
    validate_claude_cli,
)


class TestModelMappings:
    """Tests for model name mappings."""

    def test_model_map_contains_expected_models(self):
        """MODEL_MAP should contain all expected model names."""
        assert "sonnet" in MODEL_MAP
        assert "opus" in MODEL_MAP
        assert "opus-4.5" in MODEL_MAP
        assert "haiku" in MODEL_MAP

    def test_cli_model_map_handles_opus_45(self):
        """CLI_MODEL_MAP should map opus-4.5 to opus."""
        assert CLI_MODEL_MAP.get("opus-4.5") == "opus"


class TestValidateClaude:
    """Tests for validate_claude_cli function."""

    def test_validate_claude_cli_found(self):
        """Should return True when claude is found and executable."""
        with patch("shutil.which", return_value="/usr/bin/claude"):
            with patch("os.access", return_value=True):
                is_valid, message = validate_claude_cli()
                assert is_valid is True
                assert message == "/usr/bin/claude"

    def test_validate_claude_cli_not_found(self):
        """Should return False when claude is not found."""
        with patch("shutil.which", return_value=None):
            is_valid, message = validate_claude_cli()
            assert is_valid is False
            assert "not found" in message.lower()

    def test_validate_claude_cli_not_executable(self):
        """Should return False when claude is not executable."""
        with patch("shutil.which", return_value="/usr/bin/claude"):
            with patch("os.access", return_value=False):
                is_valid, message = validate_claude_cli()
                assert is_valid is False
                assert "not executable" in message.lower()


class TestLLMClientInit:
    """Tests for LLMClient initialization."""

    def test_default_initialization(self, tmp_path):
        """LLMClient should initialize with defaults."""
        client = LLMClient()

        assert client.model == "opus-4.5"
        assert client.timeout == 120
        assert client.working_dir == Path.cwd()

    def test_custom_initialization(self, tmp_path):
        """LLMClient should accept custom parameters."""
        client = LLMClient(
            model="haiku",
            timeout=60,
            working_dir=tmp_path,
        )

        assert client.model == "haiku"
        assert client.timeout == 60
        assert client.working_dir == tmp_path

    def test_model_id_property(self):
        """model_id should return the API model ID."""
        client = LLMClient(model="sonnet")
        assert client.model_id == MODEL_MAP["sonnet"]

    def test_model_id_passthrough(self):
        """model_id should pass through unknown model names."""
        client = LLMClient(model="custom-model")
        assert client.model_id == "custom-model"

    def test_cli_model_property(self):
        """cli_model should return CLI-compatible alias."""
        client = LLMClient(model="opus-4.5")
        assert client.cli_model == "opus"

    def test_cli_model_passthrough(self):
        """cli_model should pass through when no mapping exists."""
        client = LLMClient(model="sonnet")
        assert client.cli_model == "sonnet"


class TestLLMClientInvoke:
    """Tests for LLMClient invoke methods."""

    def test_invoke_via_cli_success(self, tmp_path):
        """_invoke_via_cli should return stdout on success."""
        client = LLMClient(working_dir=tmp_path)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"score": 4}'

        with patch("shutil.which", return_value="/usr/bin/claude"):
            with patch("os.access", return_value=True):
                with patch("subprocess.run", return_value=mock_result):
                    result = client._invoke_via_cli("test prompt")
                    assert result == '{"score": 4}'

    def test_invoke_via_cli_not_found(self, tmp_path):
        """_invoke_via_cli should return error when CLI not found."""
        client = LLMClient(working_dir=tmp_path)

        with patch("shutil.which", return_value=None):
            result = client._invoke_via_cli("test prompt")
            assert "Error" in result
            assert "not found" in result.lower()

    def test_invoke_via_cli_timeout(self, tmp_path):
        """_invoke_via_cli should handle timeout."""
        client = LLMClient(working_dir=tmp_path, timeout=5)

        import subprocess
        with patch("shutil.which", return_value="/usr/bin/claude"):
            with patch("os.access", return_value=True):
                with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("claude", 5)):
                    result = client._invoke_via_cli("test prompt")
                    assert "Error" in result
                    assert "timed out" in result.lower()

    def test_invoke_prefers_sdk_when_available(self, tmp_path):
        """invoke should prefer SDK when available."""
        client = LLMClient(working_dir=tmp_path)

        with patch.object(client, "_invoke_via_sdk", return_value="SDK response") as mock_sdk:
            with patch.object(client, "_invoke_via_cli") as mock_cli:
                result = client.invoke("test prompt")

                assert result == "SDK response"
                mock_sdk.assert_called_once()
                mock_cli.assert_not_called()

    def test_invoke_falls_back_to_cli(self, tmp_path):
        """invoke should fall back to CLI when SDK returns None."""
        client = LLMClient(working_dir=tmp_path)

        with patch.object(client, "_invoke_via_sdk", return_value=None):
            with patch.object(client, "_invoke_via_cli", return_value="CLI response") as mock_cli:
                result = client.invoke("test prompt")

                assert result == "CLI response"
                mock_cli.assert_called_once()


class TestLLMClientErrorDetection:
    """Tests for error detection helpers."""

    def test_is_error_response_true(self):
        """is_error_response should return True for error responses."""
        client = LLMClient()
        assert client.is_error_response("Error: Something went wrong")
        assert client.is_error_response("Error (exit 1): failed")

    def test_is_error_response_false(self):
        """is_error_response should return False for success responses."""
        client = LLMClient()
        assert not client.is_error_response('{"score": 4}')
        assert not client.is_error_response("Success!")

    def test_is_timeout_error_true(self):
        """is_timeout_error should return True for timeout errors."""
        client = LLMClient()
        assert client.is_timeout_error("Error: Claude invocation timed out after 120s")

    def test_is_timeout_error_false(self):
        """is_timeout_error should return False for non-timeout errors."""
        client = LLMClient()
        assert not client.is_timeout_error("Error: CLI not found")
        assert not client.is_timeout_error('{"score": 4}')
