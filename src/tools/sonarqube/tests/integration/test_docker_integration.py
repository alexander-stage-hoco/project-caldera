"""Docker integration tests for SonarQube container lifecycle."""

import subprocess
import time

import httpx
import pytest

from scripts.docker_lifecycle import (
    DockerConfig,
    SonarQubeContainer,
    SonarQubeContainerError,
    is_container_running,
    start_sonarqube,
    stop_sonarqube,
    wait_for_healthy,
    ensure_sonarqube_running,
    cleanup_on_error,
)


@pytest.mark.docker
@pytest.mark.integration
class TestDockerContainerLifecycle:
    """Tests for Docker container lifecycle management."""

    def test_container_starts_and_becomes_healthy(self, docker_available):
        """Test that SonarQube container starts and becomes healthy."""
        if not docker_available:
            pytest.skip("Docker is not available")

        config = DockerConfig(
            startup_timeout=300,
            health_check_interval=5,
        )

        try:
            # Start the container
            start_sonarqube(config)

            # Wait for it to become healthy
            wait_for_healthy(config)

            # Verify it's running
            assert is_container_running(config)

            # Verify the health endpoint responds
            response = httpx.get(f"{config.base_url}/api/system/status", timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "UP"

        finally:
            # Clean up
            stop_sonarqube(config)

    def test_container_stops_cleanly(self, docker_available):
        """Test that container stops without orphans."""
        if not docker_available:
            pytest.skip("Docker is not available")

        config = DockerConfig()

        # Ensure clean initial state
        stop_sonarqube(config)
        time.sleep(2)

        # Start the container
        start_sonarqube(config)
        wait_for_healthy(config)

        assert is_container_running(config)

        # Stop the container
        stop_sonarqube(config)

        # Give it a moment to fully stop
        time.sleep(5)

        # Verify it's no longer running
        assert not is_container_running(config)

    def test_is_container_running_when_not_running(self, docker_available):
        """Test is_container_running returns False when container is not running."""
        if not docker_available:
            pytest.skip("Docker is not available")

        config = DockerConfig()

        # Ensure container is stopped
        stop_sonarqube(config)
        time.sleep(1)

        # Should return False
        assert not is_container_running(config)

    def test_ensure_sonarqube_running_starts_if_needed(self, docker_available):
        """Test ensure_sonarqube_running starts container if not running."""
        if not docker_available:
            pytest.skip("Docker is not available")

        config = DockerConfig(startup_timeout=300)

        try:
            # Ensure container is stopped first
            stop_sonarqube(config)
            time.sleep(2)

            # This should start the container
            was_running = ensure_sonarqube_running(config)

            # It should have been started (not already running)
            assert not was_running

            # And now it should be running
            assert is_container_running(config)

        finally:
            stop_sonarqube(config)

    def test_ensure_sonarqube_running_returns_true_if_already_running(
        self, sonarqube_container
    ):
        """Test ensure_sonarqube_running returns True if already running."""
        config = sonarqube_container.config

        # Ensure container is running first (previous tests may have stopped it)
        ensure_sonarqube_running(config)

        # Now call again - should return True since it's already running
        was_running = ensure_sonarqube_running(config)

        # Should indicate it was already running
        assert was_running


@pytest.mark.docker
@pytest.mark.integration
class TestSonarQubeContainerContextManager:
    """Tests for SonarQubeContainer context manager."""

    @pytest.fixture(autouse=True)
    def ensure_container_running(self, sonarqube_container):
        """Ensure container is running before tests that use sonarqube_container fixture."""
        # Earlier tests may have stopped the container directly
        ensure_sonarqube_running(sonarqube_container.config)
        yield

    def test_context_manager_starts_and_stops(self, docker_available):
        """Test container lifecycle through context manager."""
        if not docker_available:
            pytest.skip("Docker is not available")

        config = DockerConfig(startup_timeout=300)

        # Ensure clean state
        stop_sonarqube(config)
        time.sleep(2)

        with SonarQubeContainer(config=config, keep_running=False) as container:
            # Should be running inside context
            assert is_container_running(config)
            assert container.base_url == config.base_url

        # Should be stopped after context
        time.sleep(2)
        assert not is_container_running(config)

    def test_context_manager_keep_running(self, docker_available):
        """Test container stays running with keep_running=True."""
        if not docker_available:
            pytest.skip("Docker is not available")

        config = DockerConfig(startup_timeout=300)

        try:
            with SonarQubeContainer(config=config, keep_running=True) as container:
                assert is_container_running(config)

            # Should still be running after context
            assert is_container_running(config)

        finally:
            # Clean up
            stop_sonarqube(config)

    def test_context_manager_respects_already_running(self, sonarqube_container):
        """Test context manager doesn't stop pre-existing container."""
        config = sonarqube_container.config

        # Container already running from fixture
        assert is_container_running(config)

        # Create a new context manager (not keep_running)
        with SonarQubeContainer(config=config, keep_running=False) as container:
            assert is_container_running(config)

        # Should still be running (was already running before)
        assert is_container_running(config)


@pytest.mark.docker
@pytest.mark.integration
class TestHealthCheck:
    """Tests for health check endpoint."""

    @pytest.fixture(autouse=True)
    def ensure_container_running(self, sonarqube_container):
        """Ensure container is running before health check tests."""
        # Earlier tests may have stopped the container directly
        ensure_sonarqube_running(sonarqube_container.config)
        yield

    def test_health_check_endpoint_responds(self, sonarqube_container):
        """Test /api/system/status returns UP status."""
        response = httpx.get(
            f"{sonarqube_container.base_url}/api/system/status",
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "UP"

    def test_health_check_includes_version(self, sonarqube_container):
        """Test health check includes SonarQube version."""
        response = httpx.get(
            f"{sonarqube_container.base_url}/api/system/status",
            timeout=10,
        )

        data = response.json()
        assert "version" in data
        # SonarQube version should be a semver-like string
        assert "." in data["version"]

    def test_wait_for_healthy_timeout(self, docker_available):
        """Test wait_for_healthy raises on timeout."""
        if not docker_available:
            pytest.skip("Docker is not available")

        # Use a very short timeout that will definitely fail
        config = DockerConfig(
            base_url="http://localhost:9999",  # Non-existent server
            startup_timeout=2,
            health_check_interval=1,
        )

        with pytest.raises(SonarQubeContainerError) as exc_info:
            wait_for_healthy(config)

        assert "did not become healthy" in str(exc_info.value)


@pytest.mark.docker
@pytest.mark.integration
class TestCleanupOnError:
    """Tests for error cleanup functionality."""

    def test_cleanup_on_error_stops_container(self, docker_available):
        """Test cleanup_on_error stops running container."""
        if not docker_available:
            pytest.skip("Docker is not available")

        config = DockerConfig(startup_timeout=300)

        try:
            # Start container
            start_sonarqube(config)
            wait_for_healthy(config)
            assert is_container_running(config)

            # Simulate error cleanup
            cleanup_on_error(config)

            # Should be stopped
            time.sleep(2)
            assert not is_container_running(config)

        finally:
            # Ensure cleanup
            stop_sonarqube(config)

    def test_cleanup_on_error_handles_not_running(self, docker_available):
        """Test cleanup_on_error handles non-running container gracefully."""
        if not docker_available:
            pytest.skip("Docker is not available")

        config = DockerConfig()

        # Ensure container is stopped
        stop_sonarqube(config)
        time.sleep(1)

        # Should not raise
        cleanup_on_error(config)


@pytest.mark.docker
@pytest.mark.integration
class TestDockerConfig:
    """Tests for Docker configuration."""

    def test_default_config_values(self):
        """Test default DockerConfig values."""
        config = DockerConfig()

        assert config.container_name == "vulcan-sonarqube"
        assert config.base_url == "http://localhost:9000"
        assert config.startup_timeout == 300
        assert config.health_check_interval == 5

    def test_custom_config_values(self):
        """Test custom DockerConfig values."""
        config = DockerConfig(
            container_name="test-sonar",
            base_url="http://localhost:9001",
            startup_timeout=600,
            health_check_interval=10,
        )

        assert config.container_name == "test-sonar"
        assert config.base_url == "http://localhost:9001"
        assert config.startup_timeout == 600
        assert config.health_check_interval == 10
