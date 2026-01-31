"""Docker lifecycle management for SonarQube container."""

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
import shutil

import httpx
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class DockerConfig:
    """Configuration for Docker lifecycle management."""

    compose_file: Path = Path(__file__).parent.parent / "docker-compose.yml"
    container_name: str = "vulcan-sonarqube"
    base_url: str = "http://localhost:9000"
    startup_timeout: int = 300  # 5 minutes
    health_check_interval: int = 5


class SonarQubeContainerError(Exception):
    """Raised when container operations fail."""


def start_sonarqube(config: DockerConfig | None = None) -> None:
    """Start the SonarQube container using docker-compose.

    Args:
        config: Docker configuration. Uses defaults if None.

    Raises:
        SonarQubeContainerError: If container fails to start.
    """
    config = config or DockerConfig()
    logger.info("Starting SonarQube container", compose_file=str(config.compose_file))

    def run_compose_up() -> None:
        result = subprocess.run(
            _compose_cmd() + ["-f", str(config.compose_file), "up", "-d", "--pull", "never"],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.debug("docker-compose up output", stdout=result.stdout, stderr=result.stderr)

    try:
        run_compose_up()
    except subprocess.CalledProcessError as e:
        stderr = e.stderr or ""
        if "No such container" in stderr:
            logger.warning(
                "Compose up failed due to missing container, retrying after cleanup",
                error=stderr,
            )
            try:
                subprocess.run(
                    _compose_cmd() + ["-f", str(config.compose_file), "down", "--remove-orphans"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
            except subprocess.CalledProcessError as cleanup_error:
                logger.warning("Cleanup before retry failed", error=str(cleanup_error))

            subprocess.run(
                ["docker", "rm", "-f", config.container_name],
                capture_output=True,
                text=True,
                check=False,
            )

            try:
                run_compose_up()
                return
            except subprocess.CalledProcessError as retry_error:
                raise SonarQubeContainerError(
                    f"Failed to start container after retry: {retry_error.stderr}"
                ) from retry_error

        raise SonarQubeContainerError(f"Failed to start container: {stderr}") from e


def stop_sonarqube(config: DockerConfig | None = None, remove_volumes: bool = False) -> None:
    """Stop the SonarQube container.

    Args:
        config: Docker configuration. Uses defaults if None.
        remove_volumes: Whether to remove volumes when stopping.
    """
    config = config or DockerConfig()
    logger.info("Stopping SonarQube container", remove_volumes=remove_volumes)

    cmd = _compose_cmd() + ["-f", str(config.compose_file), "down", "--remove-orphans"]
    if remove_volumes:
        cmd.append("-v")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.debug("docker-compose down output", stdout=result.stdout, stderr=result.stderr)
    except subprocess.CalledProcessError as e:
        logger.warning("Failed to stop container gracefully", error=str(e))

    # Ensure container is fully removed (handles edge cases where down doesn't clean up)
    try:
        subprocess.run(
            ["docker", "rm", "-f", config.container_name],
            capture_output=True,
            text=True,
            check=False,  # Ignore errors if container doesn't exist
        )
    except subprocess.SubprocessError:
        pass  # Container may already be removed


def is_container_running(config: DockerConfig | None = None) -> bool:
    """Check if the SonarQube container is running.

    Args:
        config: Docker configuration. Uses defaults if None.

    Returns:
        True if container is running, False otherwise.
    """
    config = config or DockerConfig()

    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={config.container_name}", "--format", "{{.Status}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return "Up" in result.stdout
    except subprocess.CalledProcessError:
        return False


def _compose_cmd() -> list[str]:
    """Return the preferred docker compose command."""
    if shutil.which("docker-compose"):
        return ["docker-compose"]
    return ["docker", "compose"]


def _docker_disabled() -> bool:
    """Return True when Docker lifecycle should be skipped."""
    return os.environ.get("SONARQUBE_SKIP_DOCKER") == "1" or os.environ.get("SONARQUBE_CONTAINER_RUNNING") == "1"


def _inspect_container_state(config: DockerConfig) -> dict | None:
    """Return container state from docker inspect, or None if unavailable."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{json .State}}", config.container_name],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return None

    try:
        return json.loads(result.stdout.strip() or "{}")
    except json.JSONDecodeError:
        return None


def _raise_if_container_oom(config: DockerConfig) -> None:
    """Raise a clear error when the container was OOM-killed."""
    state = _inspect_container_state(config)
    if not state:
        return

    if state.get("OOMKilled") or state.get("ExitCode") == 137:
        raise SonarQubeContainerError(
            "SonarQube container was OOM-killed (exit code 137). "
            "Increase Docker Desktop memory or reduce SonarQube JVM heap settings."
        )


def wait_for_healthy(config: DockerConfig | None = None) -> None:
    """Wait for SonarQube to become healthy and ready.

    Polls the /api/system/status endpoint until it returns UP.

    Args:
        config: Docker configuration. Uses defaults if None.

    Raises:
        SonarQubeContainerError: If container doesn't become healthy within timeout.
    """
    config = config or DockerConfig()
    logger.info("Waiting for SonarQube to become healthy", timeout=config.startup_timeout)

    start_time = time.time()
    last_status = None

    while time.time() - start_time < config.startup_timeout:
        if not _docker_disabled() and not is_container_running(config):
            _raise_if_container_oom(config)

        try:
            response = httpx.get(
                f"{config.base_url}/api/system/status",
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                if status != last_status:
                    logger.info("SonarQube status", status=status)
                    last_status = status
                if status == "UP":
                    logger.info("SonarQube is ready")
                    return
        except httpx.RequestError as e:
            logger.debug("Health check failed (expected during startup)", error=str(e))

        time.sleep(config.health_check_interval)

    raise SonarQubeContainerError(
        f"SonarQube did not become healthy within {config.startup_timeout}s"
    )


def ensure_sonarqube_running(config: DockerConfig | None = None) -> bool:
    """Ensure SonarQube is running, starting it if necessary.

    Args:
        config: Docker configuration. Uses defaults if None.

    Returns:
        True if container was already running, False if it was started.

    Raises:
        SonarQubeContainerError: If container fails to start or become healthy.
    """
    config = config or DockerConfig()

    if _docker_disabled():
        logger.info("Skipping Docker lifecycle; expecting external SonarQube")
        wait_for_healthy(config)
        return True

    if is_container_running(config):
        logger.info("SonarQube container already running")
        # Still wait for healthy in case it's starting up
        wait_for_healthy(config)
        return True

    start_sonarqube(config)
    wait_for_healthy(config)
    return False


def generate_sonarqube_token(
    base_url: str,
    token_name: str = "test-token",
    admin_user: str = "admin",
    admin_pass: str = "admin",
) -> str:
    """Generate a user token via SonarQube API.

    Uses default admin credentials (admin:admin) for fresh installations.
    SonarQube 10+ requires authentication for most API calls.

    Args:
        base_url: SonarQube server URL.
        token_name: Name for the generated token.
        admin_user: Admin username (default: admin).
        admin_pass: Admin password (default: admin).

    Returns:
        The generated token string.

    Raises:
        SonarQubeContainerError: If token generation fails.
    """
    # Check for environment variable override
    env_token = os.environ.get("SONAR_TOKEN")
    if env_token:
        logger.info("Using SONAR_TOKEN from environment")
        return env_token

    logger.info("Generating SonarQube user token", token_name=token_name)

    try:
        response = httpx.post(
            f"{base_url}/api/user_tokens/generate",
            params={"name": token_name},
            auth=(admin_user, admin_pass),
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            if token:
                logger.info("Successfully generated token", token_name=token_name)
                return token
            logger.error("Token generation response missing 'token' field", response_data=data)
            raise SonarQubeContainerError(
                f"Token generation response missing 'token' field. Response: {data}"
            )

        # Handle common error cases
        if response.status_code == 401:
            raise SonarQubeContainerError(
                f"Authentication failed with admin credentials. "
                f"Set SONAR_TOKEN env var or ensure default admin:admin credentials work."
            )
        if response.status_code == 400:
            # Token with this name might already exist
            error_msg = response.json().get("errors", [{}])[0].get("msg", "")
            if "already exists" in error_msg.lower():
                logger.warning("Token already exists, attempting to revoke and recreate", token_name=token_name)
                # Revoke existing token
                revoke_response = httpx.post(
                    f"{base_url}/api/user_tokens/revoke",
                    params={"name": token_name},
                    auth=(admin_user, admin_pass),
                    timeout=30,
                )
                if revoke_response.status_code in (200, 204):
                    # Retry generation
                    return generate_sonarqube_token(base_url, token_name, admin_user, admin_pass)
            raise SonarQubeContainerError(f"Token generation failed: {error_msg}")

        raise SonarQubeContainerError(
            f"Token generation failed with status {response.status_code}: {response.text}"
        )

    except httpx.RequestError as e:
        raise SonarQubeContainerError(f"Failed to connect to SonarQube for token generation: {e}") from e


class SonarQubeContainer:
    """Context manager for SonarQube container lifecycle.

    Example:
        with SonarQubeContainer() as container:
            # SonarQube is running and healthy
            client = SonarQubeClient(container.base_url)
            # ... do analysis ...
        # Container is stopped automatically
    """

    def __init__(
        self,
        config: DockerConfig | None = None,
        keep_running: bool = False,
        remove_volumes: bool = False,
    ):
        """Initialize the container manager.

        Args:
            config: Docker configuration. Uses defaults if None.
            keep_running: If True, don't stop container on exit.
            remove_volumes: If True, remove volumes when stopping.
        """
        self.config = config or DockerConfig()
        self.keep_running = keep_running
        self.remove_volumes = remove_volumes
        self._was_already_running = False
        self.admin_token: str | None = None

    @property
    def base_url(self) -> str:
        """Get the base URL for the SonarQube API."""
        return self.config.base_url

    def __enter__(self) -> "SonarQubeContainer":
        """Start the container, wait for healthy, and generate auth token."""
        self._was_already_running = ensure_sonarqube_running(self.config)
        # Generate token for authenticated access (required in SonarQube 10+)
        self.admin_token = generate_sonarqube_token(
            self.config.base_url,
            token_name=f"test-{int(time.time())}",
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop the container unless keep_running is True."""
        if self.keep_running:
            logger.info("Keeping SonarQube container running")
            return

        # Don't stop if it was already running before we started
        if self._was_already_running:
            logger.info("Container was already running, not stopping")
            return

        stop_sonarqube(self.config, remove_volumes=self.remove_volumes)


def cleanup_on_error(config: DockerConfig | None = None) -> None:
    """Force cleanup of container on error.

    This function should be called from signal handlers or error handlers
    to ensure the container is stopped even on unexpected termination.

    Args:
        config: Docker configuration. Uses defaults if None.
    """
    config = config or DockerConfig()
    logger.warning("Forcing container cleanup due to error")

    try:
        stop_sonarqube(config, remove_volumes=False)
    except Exception as e:
        logger.error("Failed to cleanup container", error=str(e))


if __name__ == "__main__":
    # Simple test/utility when run directly
    import sys

    structlog.configure(
        processors=[
            structlog.dev.ConsoleRenderer(),
        ],
    )

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "start":
            start_sonarqube()
            wait_for_healthy()
        elif cmd == "stop":
            stop_sonarqube()
        elif cmd == "status":
            if is_container_running():
                print("Container is running")
            else:
                print("Container is not running")
        else:
            print(f"Unknown command: {cmd}")
            sys.exit(1)
    else:
        print("Usage: python docker_lifecycle.py [start|stop|status]")
