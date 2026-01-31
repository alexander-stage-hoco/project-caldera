"""API integration tests for SonarQube client."""

import pytest

from scripts.api.client import (
    ApiConfig,
    SonarQubeClient,
    SonarQubeApiError,
    PageInfo,
)


@pytest.mark.docker
@pytest.mark.integration
class TestSystemEndpoints:
    """Tests for system-related API endpoints."""

    def test_system_status(self, sonarqube_client):
        """Test /api/system/status endpoint returns UP."""
        result = sonarqube_client.get("/api/system/status")

        assert result["status"] == "UP"
        assert "version" in result

    def test_system_health(self, sonarqube_client):
        """Test /api/system/health endpoint."""
        result = sonarqube_client.get("/api/system/health")

        assert "health" in result
        # Community edition should be GREEN
        assert result["health"] in ["GREEN", "YELLOW", "RED"]

    def test_system_info(self, sonarqube_client):
        """Test /api/system/info endpoint for basic system information."""
        # Note: This may require admin auth on some SonarQube setups
        try:
            result = sonarqube_client.get("/api/system/info")
            assert "System" in result or "sonarqube" in str(result).lower()
        except SonarQubeApiError as e:
            # 403 is expected without admin auth
            if e.status_code != 403:
                raise


@pytest.mark.docker
@pytest.mark.integration
class TestMetricsEndpoints:
    """Tests for metrics-related API endpoints."""

    def test_metrics_search_returns_metrics(self, sonarqube_client):
        """Test /api/metrics/search returns metric catalog."""
        result = sonarqube_client.get("/api/metrics/search")

        assert "metrics" in result
        assert len(result["metrics"]) > 0

        # Check structure of metrics
        first_metric = result["metrics"][0]
        assert "key" in first_metric
        assert "name" in first_metric
        assert "type" in first_metric

    def test_metrics_search_pagination(self, sonarqube_client):
        """Test pagination works for metrics endpoint."""
        # Get first page
        result1 = sonarqube_client.get("/api/metrics/search", params={"p": 1, "ps": 10})
        assert "metrics" in result1
        assert len(result1["metrics"]) <= 10

        # Get second page if available
        page_info = PageInfo.from_response(result1)
        if page_info.has_more:
            result2 = sonarqube_client.get("/api/metrics/search", params={"p": 2, "ps": 10})
            assert "metrics" in result2

            # Metrics should be different
            keys1 = {m["key"] for m in result1["metrics"]}
            keys2 = {m["key"] for m in result2["metrics"]}
            assert keys1 != keys2

    def test_common_metrics_exist(self, sonarqube_client):
        """Test that common metrics exist in the catalog."""
        result = sonarqube_client.get("/api/metrics/search", params={"ps": 500})

        metric_keys = {m["key"] for m in result["metrics"]}

        # These metrics should always exist
        expected_metrics = [
            "ncloc",
            "complexity",
            "bugs",
            "vulnerabilities",
            "code_smells",
            "coverage",
        ]

        for expected in expected_metrics:
            assert expected in metric_keys, f"Expected metric '{expected}' not found"


@pytest.mark.docker
@pytest.mark.integration
class TestProjectEndpoints:
    """Tests for project-related API endpoints."""

    def test_projects_search(self, sonarqube_client):
        """Test /api/projects/search endpoint."""
        result = sonarqube_client.get("/api/projects/search")

        # Response should have components array (even if empty)
        assert "components" in result or "paging" in result

    def test_qualityprofiles_search(self, sonarqube_client):
        """Test /api/qualityprofiles/search endpoint."""
        result = sonarqube_client.get("/api/qualityprofiles/search")

        assert "profiles" in result
        # Should have at least one default profile
        assert len(result["profiles"]) > 0

        # Check profile structure
        profile = result["profiles"][0]
        assert "key" in profile
        assert "name" in profile
        assert "language" in profile


@pytest.mark.docker
@pytest.mark.integration
class TestRulesEndpoints:
    """Tests for rules-related API endpoints."""

    def test_rules_search(self, sonarqube_client):
        """Test /api/rules/search endpoint."""
        result = sonarqube_client.get(
            "/api/rules/search",
            params={"ps": 10},  # Limit for speed
        )

        assert "rules" in result
        assert len(result["rules"]) > 0

        # Check rule structure
        rule = result["rules"][0]
        assert "key" in rule
        assert "name" in rule
        assert "type" in rule

    def test_rules_search_by_language(self, sonarqube_client):
        """Test filtering rules by language."""
        result = sonarqube_client.get(
            "/api/rules/search",
            params={"languages": "cs", "ps": 10},
        )

        assert "rules" in result
        # C# rules should exist
        if result["rules"]:
            for rule in result["rules"]:
                assert "cs" in rule.get("lang", "") or "cs" in rule.get("key", "")

    def test_rules_search_by_type(self, sonarqube_client):
        """Test filtering rules by type."""
        for rule_type in ["BUG", "VULNERABILITY", "CODE_SMELL"]:
            result = sonarqube_client.get(
                "/api/rules/search",
                params={"types": rule_type, "ps": 5},
            )

            assert "rules" in result
            for rule in result["rules"]:
                assert rule.get("type") == rule_type


@pytest.mark.docker
@pytest.mark.integration
class TestPagination:
    """Tests for API pagination functionality."""

    def test_get_paged_iterates_all_items(self, sonarqube_client):
        """Test get_paged iterator retrieves all items."""
        # Use metrics endpoint which has many items
        all_metrics = list(sonarqube_client.get_paged(
            "/api/metrics/search",
            items_key="metrics",
            page_size=10,  # Small page size to ensure pagination is exercised
        ))

        # Should have at least one page of metrics
        assert len(all_metrics) >= 10, "Expected at least one page of metrics"

        # Check we got unique items
        keys = [m["key"] for m in all_metrics]
        assert len(keys) == len(set(keys)), "Found duplicate metric keys"

    def test_get_all_returns_list(self, sonarqube_client):
        """Test get_all returns a complete list."""
        all_metrics = sonarqube_client.get_all(
            "/api/metrics/search",
            items_key="metrics",
            page_size=50,
        )

        assert isinstance(all_metrics, list)
        assert len(all_metrics) > 0

    def test_page_info_from_response(self, sonarqube_client):
        """Test PageInfo correctly parses response."""
        result = sonarqube_client.get(
            "/api/metrics/search",
            params={"p": 1, "ps": 10},
        )

        page_info = PageInfo.from_response(result)

        assert page_info.page_index == 1
        # API returns actual page size used, which may differ from requested
        assert page_info.page_size > 0
        assert page_info.total >= 0


@pytest.mark.docker
@pytest.mark.integration
class TestClientConfiguration:
    """Tests for client configuration and connection."""

    def test_client_timeout(self, sonarqube_url):
        """Test client handles timeout configuration."""
        config = ApiConfig(
            base_url=sonarqube_url,
            timeout=5,  # Short timeout
        )

        with SonarQubeClient(config) as client:
            # Should work with normal requests
            result = client.get("/api/system/status")
            assert result["status"] == "UP"

    def test_client_context_manager(self, sonarqube_url):
        """Test client works as context manager."""
        config = ApiConfig(base_url=sonarqube_url)

        with SonarQubeClient(config) as client:
            result = client.get("/api/system/status")
            assert result["status"] == "UP"

        # Client should be closed after context
        assert client._client is None

    def test_client_closes_properly(self, sonarqube_url):
        """Test client closes HTTP connection properly."""
        config = ApiConfig(base_url=sonarqube_url)
        client = SonarQubeClient(config)

        # Make a request to create connection
        client.get("/api/system/status")
        assert client._client is not None

        # Close should clean up
        client.close()
        assert client._client is None


@pytest.mark.docker
@pytest.mark.integration
class TestErrorHandling:
    """Tests for API error handling."""

    def test_404_raises_error(self, sonarqube_client):
        """Test 404 response raises SonarQubeApiError."""
        with pytest.raises(SonarQubeApiError) as exc_info:
            sonarqube_client.get("/api/nonexistent/endpoint")

        assert exc_info.value.status_code == 404

    def test_invalid_params_ignored(self, sonarqube_client):
        """Test that SonarQube ignores unknown parameters (doesn't error)."""
        # SonarQube silently ignores invalid/unknown params - verify this behavior
        result = sonarqube_client.get(
            "/api/projects/search",
            params={"invalidParam": "value"},
        )

        # Should succeed - unknown params are ignored
        assert "components" in result or "paging" in result


@pytest.mark.docker
@pytest.mark.integration
class TestAuthenticationOptional:
    """Tests for authentication handling.

    Note: SonarQube Community Edition allows anonymous access by default.
    These tests verify behavior with and without tokens.
    """

    def test_anonymous_access_works(self, sonarqube_url):
        """Test anonymous access works for public endpoints."""
        config = ApiConfig(base_url=sonarqube_url, token=None)

        with SonarQubeClient(config) as client:
            result = client.get("/api/system/status")
            assert result["status"] == "UP"

    def test_token_auth_format(self, sonarqube_url):
        """Test token authentication uses correct format."""
        # Even with an invalid token, we can verify the auth header format
        config = ApiConfig(
            base_url=sonarqube_url,
            token="test-token",  # Invalid token
        )

        client = SonarQubeClient(config)

        # Access the internal client to check auth setup
        http_client = client.client
        assert http_client.auth is not None
