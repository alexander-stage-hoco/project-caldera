"""Tests for Docker lifecycle management."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import subprocess

from scripts.docker_lifecycle import (
    DockerConfig,
    SonarQubeContainerError,
    start_sonarqube,
    stop_sonarqube,
    is_container_running,
    wait_for_healthy,
    ensure_sonarqube_running,
    cleanup_on_error,
    SonarQubeContainer,
)


class TestDockerConfig:
    """Tests for DockerConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = DockerConfig()

        assert config.container_name == "vulcan-sonarqube"
        assert config.base_url == "http://localhost:9000"
        assert config.startup_timeout == 300
        assert config.health_check_interval == 5

    def test_compose_file_path(self):
        """Test compose file path is set."""
        config = DockerConfig()
        assert config.compose_file.name == "docker-compose.yml"


class TestStartSonarqube:
    """Tests for start_sonarqube."""

    @patch("subprocess.run")
    def test_start_success(self, mock_run):
        """Test successful container start."""
        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        start_sonarqube()

        mock_run.assert_called_once()
        args = mock_run.call_args
        assert "docker" in args[0][0] or "docker-compose" in args[0][0]
        if "docker" in args[0][0]:
            assert "compose" in args[0][0]
        assert "up" in args[0][0]
        assert "-d" in args[0][0]

    @patch("subprocess.run")
    def test_start_failure(self, mock_run):
        """Test container start failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="Error")

        with pytest.raises(SonarQubeContainerError) as exc_info:
            start_sonarqube()

        assert "Failed to start" in str(exc_info.value)

    @patch("subprocess.run")
    def test_start_retry_on_missing_container(self, mock_run):
        """Test retry behavior when compose reports missing container."""
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "cmd", stderr="No such container: abc"),
            Mock(stdout="", stderr="", returncode=0),
            Mock(stdout="", stderr="", returncode=0),
            Mock(stdout="", stderr="", returncode=0),
        ]

        start_sonarqube()

        assert mock_run.call_count == 4
        first_call = mock_run.call_args_list[0][0][0]
        second_call = mock_run.call_args_list[1][0][0]
        third_call = mock_run.call_args_list[2][0][0]
        fourth_call = mock_run.call_args_list[3][0][0]
        if first_call[0] == "docker-compose":
            assert first_call[:2] == ["docker-compose", "-f"]
        else:
            assert first_call[:3] == ["docker", "compose", "-f"]
        assert "up" in first_call
        if second_call[0] == "docker-compose":
            assert second_call[:2] == ["docker-compose", "-f"]
        else:
            assert second_call[:3] == ["docker", "compose", "-f"]
        assert "down" in second_call
        assert third_call[:2] == ["docker", "rm"]
        if fourth_call[0] == "docker-compose":
            assert fourth_call[:2] == ["docker-compose", "-f"]
        else:
            assert fourth_call[:3] == ["docker", "compose", "-f"]
        assert "up" in fourth_call


class TestStopSonarqube:
    """Tests for stop_sonarqube."""

    @patch("subprocess.run")
    def test_stop_success(self, mock_run):
        """Test successful container stop."""
        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        stop_sonarqube()

        assert mock_run.call_count == 2
        first_call = mock_run.call_args_list[0]
        assert "docker" in first_call[0][0] or "docker-compose" in first_call[0][0]
        if "docker" in first_call[0][0]:
            assert "compose" in first_call[0][0]
        assert "down" in first_call[0][0]

    @patch("subprocess.run")
    def test_stop_with_volumes(self, mock_run):
        """Test container stop with volume removal."""
        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)

        stop_sonarqube(remove_volumes=True)

        first_call = mock_run.call_args_list[0]
        assert "-v" in first_call[0][0]


class TestIsContainerRunning:
    """Tests for is_container_running."""

    @patch("subprocess.run")
    def test_running(self, mock_run):
        """Test detecting running container."""
        mock_run.return_value = Mock(stdout="Up 5 minutes", returncode=0)

        result = is_container_running()

        assert result is True

    @patch("subprocess.run")
    def test_not_running(self, mock_run):
        """Test detecting stopped container."""
        mock_run.return_value = Mock(stdout="", returncode=0)

        result = is_container_running()

        assert result is False


class TestWaitForHealthy:
    """Tests for wait_for_healthy."""

    @patch("httpx.get")
    @patch("time.sleep")
    def test_healthy_immediately(self, mock_sleep, mock_get):
        """Test when SonarQube is already healthy."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "UP"}
        mock_get.return_value = mock_response

        config = DockerConfig(startup_timeout=10)
        wait_for_healthy(config)

        # Should succeed without sleeping
        mock_sleep.assert_not_called()

    @patch("scripts.docker_lifecycle.httpx.get")
    @patch("time.sleep")
    @patch("time.time")
    def test_timeout(self, mock_time, mock_sleep, mock_get):
        """Test timeout waiting for healthy."""
        import httpx

        # Simulate timeout by making time.time() exceed timeout
        mock_time.side_effect = [0, 1, 100]  # Start, check, exceeded

        mock_get.side_effect = httpx.RequestError("Connection refused")

        config = DockerConfig(startup_timeout=5)

        with pytest.raises(SonarQubeContainerError) as exc_info:
            wait_for_healthy(config)

        assert "did not become healthy" in str(exc_info.value)

    @patch("scripts.docker_lifecycle.subprocess.run")
    @patch("scripts.docker_lifecycle.is_container_running")
    @patch("scripts.docker_lifecycle.httpx.get")
    def test_oom_killed_raises(self, mock_get, mock_running, mock_run, monkeypatch):
        """Raise a helpful error when container is OOM-killed."""
        monkeypatch.delenv("SONARQUBE_SKIP_DOCKER", raising=False)
        monkeypatch.delenv("SONARQUBE_CONTAINER_RUNNING", raising=False)

        mock_running.return_value = False
        mock_run.return_value = Mock(
            stdout='{"OOMKilled": true, "ExitCode": 137, "Status": "exited"}',
            returncode=0,
        )

        with pytest.raises(SonarQubeContainerError) as exc_info:
            wait_for_healthy(DockerConfig(startup_timeout=5))

        assert "OOM-killed" in str(exc_info.value)
        mock_get.assert_not_called()


class TestSonarQubeContainer:
    """Tests for SonarQubeContainer context manager."""

    @patch("scripts.docker_lifecycle.generate_sonarqube_token", return_value="token")
    @patch("scripts.docker_lifecycle.ensure_sonarqube_running")
    @patch("scripts.docker_lifecycle.stop_sonarqube")
    def test_context_manager_normal(self, mock_stop, mock_ensure, _mock_token):
        """Test normal context manager flow."""
        mock_ensure.return_value = False  # Was not already running

        with SonarQubeContainer() as container:
            assert container.base_url == "http://localhost:9000"

        mock_ensure.assert_called_once()
        mock_stop.assert_called_once()

    @patch("scripts.docker_lifecycle.generate_sonarqube_token", return_value="token")
    @patch("scripts.docker_lifecycle.ensure_sonarqube_running")
    @patch("scripts.docker_lifecycle.stop_sonarqube")
    def test_context_manager_keep_running(self, mock_stop, mock_ensure, _mock_token):
        """Test context manager with keep_running=True."""
        mock_ensure.return_value = False

        with SonarQubeContainer(keep_running=True) as container:
            pass

        mock_ensure.assert_called_once()
        mock_stop.assert_not_called()

    @patch("scripts.docker_lifecycle.generate_sonarqube_token", return_value="token")
    @patch("scripts.docker_lifecycle.ensure_sonarqube_running")
    @patch("scripts.docker_lifecycle.stop_sonarqube")
    def test_context_manager_already_running(self, mock_stop, mock_ensure, _mock_token):
        """Test context manager when container was already running."""
        mock_ensure.return_value = True  # Was already running

        with SonarQubeContainer() as container:
            pass

        mock_ensure.assert_called_once()
        mock_stop.assert_not_called()  # Don't stop if it was already running


class TestEnsureSonarQubeRunning:
    """Tests for ensure_sonarqube_running behavior."""

    @patch("scripts.docker_lifecycle.wait_for_healthy")
    @patch("scripts.docker_lifecycle.start_sonarqube")
    @patch("scripts.docker_lifecycle.is_container_running")
    def test_skip_docker_env(self, mock_running, mock_start, mock_wait, monkeypatch):
        """Skip Docker lifecycle when env flag is set."""
        monkeypatch.setenv("SONARQUBE_SKIP_DOCKER", "1")

        result = ensure_sonarqube_running()

        assert result is True
        mock_wait.assert_called_once()
        mock_start.assert_not_called()
        mock_running.assert_not_called()
