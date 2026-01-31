"""Tests for the SonarQube API client."""

import pytest
from unittest.mock import Mock, patch

from scripts.api.client import (
    ApiConfig,
    SonarQubeClient,
    SonarQubeApiError,
    PageInfo,
)


class TestApiConfig:
    """Tests for ApiConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ApiConfig()

        assert config.base_url == "http://localhost:9000"
        assert config.token is None
        assert config.page_size == 500
        assert config.max_retries == 3
        assert config.timeout == 60
        assert config.metrics_chunk_size == 15

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ApiConfig(
            base_url="http://sonar.example.com:9000",
            token="my-token",
            page_size=100,
        )

        assert config.base_url == "http://sonar.example.com:9000"
        assert config.token == "my-token"
        assert config.page_size == 100


class TestPageInfo:
    """Tests for PageInfo."""

    def test_has_more_true(self):
        """Test has_more returns True when more pages exist."""
        page_info = PageInfo(page_index=1, page_size=100, total=250)
        assert page_info.has_more is True

    def test_has_more_false(self):
        """Test has_more returns False on last page."""
        page_info = PageInfo(page_index=3, page_size=100, total=250)
        assert page_info.has_more is False

    def test_has_more_exact_boundary(self):
        """Test has_more at exact page boundary."""
        page_info = PageInfo(page_index=2, page_size=100, total=200)
        assert page_info.has_more is False

    def test_from_response(self):
        """Test creating PageInfo from API response."""
        response = {
            "paging": {
                "pageIndex": 2,
                "pageSize": 50,
                "total": 150,
            }
        }

        page_info = PageInfo.from_response(response)

        assert page_info.page_index == 2
        assert page_info.page_size == 50
        assert page_info.total == 150

    def test_from_response_missing_paging(self):
        """Test PageInfo with missing paging data."""
        response = {}
        page_info = PageInfo.from_response(response)

        assert page_info.page_index == 1
        assert page_info.page_size == 100
        assert page_info.total == 0


class TestSonarQubeClient:
    """Tests for SonarQubeClient."""

    def test_context_manager(self):
        """Test client can be used as context manager."""
        config = ApiConfig()

        with SonarQubeClient(config) as client:
            assert client is not None

    @patch("httpx.Client")
    def test_get_request(self, mock_client_class):
        """Test GET request."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"result": "ok"}'
        mock_response.json.return_value = {"result": "ok"}
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client

        config = ApiConfig()
        client = SonarQubeClient(config)
        client._client = mock_client

        result = client.get("/api/test", {"param": "value"})

        assert result == {"result": "ok"}
        mock_client.request.assert_called_once()

    @patch("httpx.Client")
    def test_get_request_error(self, mock_client_class):
        """Test GET request with API error."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = '{"errors": [{"msg": "Bad request"}]}'
        mock_response.json.return_value = {"errors": [{"msg": "Bad request"}]}
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client

        config = ApiConfig()
        client = SonarQubeClient(config)
        client._client = mock_client

        with pytest.raises(SonarQubeApiError) as exc_info:
            client.get("/api/test")

        assert "Bad request" in str(exc_info.value)
        assert exc_info.value.status_code == 400


class TestSonarQubeApiError:
    """Tests for SonarQubeApiError."""

    def test_error_with_message(self):
        """Test error with message."""
        error = SonarQubeApiError("Test error")
        assert str(error) == "Test error"

    def test_error_with_status_code(self):
        """Test error with status code."""
        error = SonarQubeApiError("Test error", status_code=404)
        assert error.status_code == 404

    def test_error_with_errors_list(self):
        """Test error with errors list."""
        errors = [{"msg": "Error 1"}, {"msg": "Error 2"}]
        error = SonarQubeApiError("Test error", errors=errors)
        assert error.errors == errors
