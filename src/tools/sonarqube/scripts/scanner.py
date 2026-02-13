"""Sonar Scanner wrapper for running SonarQube analysis."""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field, replace
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)
DOCKER_SONARQUBE_HOST = "vulcan-sonarqube"
DEFAULT_DOCKER_NETWORK = "sonarqube_default"


@dataclass
class ScannerConfig:
    """Configuration for sonar-scanner execution."""

    sonarqube_url: str = "http://localhost:9000"
    token: str | None = None
    project_key: str = ""
    project_name: str | None = None
    project_version: str | None = None
    sources: str = "."
    exclusions: list[str] = field(default_factory=list)
    java_binaries: str | None = None  # For Java projects
    coverage_report: str | None = None
    extra_properties: dict[str, str] = field(default_factory=dict)
    use_docker: bool = True  # Use dockerized scanner
    docker_image: str = "sonarsource/sonar-scanner-cli:5.0.1"  # Pinned version to prevent orphaned images
    docker_network: str | None = "sonarqube_default"
    timeout: int = 600  # 10 minutes
    retry_attempts: int = 2
    dotnet_sdk_version: str = "8.0"  # .NET SDK version for Docker builds


class ScannerError(Exception):
    """Raised when scanner execution fails."""


def generate_sonar_properties(config: ScannerConfig) -> dict[str, str]:
    """Generate sonar-project.properties content.

    Args:
        config: Scanner configuration

    Returns:
        Dictionary of property key-value pairs
    """
    props = {
        "sonar.host.url": config.sonarqube_url,
        "sonar.projectKey": config.project_key,
        "sonar.sources": config.sources,
    }

    if config.token:
        props["sonar.token"] = config.token

    if config.project_name:
        props["sonar.projectName"] = config.project_name

    if config.project_version:
        props["sonar.projectVersion"] = config.project_version

    if config.exclusions:
        props["sonar.exclusions"] = ",".join(config.exclusions)

    if config.java_binaries:
        props["sonar.java.binaries"] = config.java_binaries

    if config.coverage_report:
        props["sonar.coverage.jacoco.xmlReportPaths"] = config.coverage_report

    # Add extra properties
    props.update(config.extra_properties)

    return props


def write_sonar_properties(repo_path: Path, config: ScannerConfig) -> Path:
    """Write sonar-project.properties file.

    Args:
        repo_path: Path to repository
        config: Scanner configuration

    Returns:
        Path to the properties file
    """
    props = generate_sonar_properties(config)
    props_path = repo_path / "sonar-project.properties"

    with open(props_path, "w") as f:
        for key, value in props.items():
            f.write(f"{key}={value}\n")

    logger.info("Wrote sonar-project.properties", path=str(props_path))
    return props_path


def _get_container_ip(container_name: str) -> str | None:
    """Resolve a container IP address via docker inspect."""
    try:
        result = subprocess.run(
            [
                "docker",
                "inspect",
                "-f",
                "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
                container_name,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        ip_addr = result.stdout.strip()
        return ip_addr or None
    except subprocess.CalledProcessError as exc:
        logger.debug("Failed to resolve container IP", error=str(exc))
        return None


def run_scanner_docker(
    repo_path: Path,
    config: ScannerConfig,
) -> subprocess.CompletedProcess:
    """Run sonar-scanner using Docker container.

    Args:
        repo_path: Path to repository
        config: Scanner configuration

    Returns:
        Completed process result
    """
    # Rewrite localhost URL for Docker container reachability on compose network
    effective_config = config
    docker_network = config.docker_network
    add_host = None
    if config.sonarqube_url.startswith("http://localhost") or config.sonarqube_url.startswith("http://127.0.0.1"):
        effective_config = replace(
            config,
            sonarqube_url=f"http://{DOCKER_SONARQUBE_HOST}:9000",
        )
        docker_network = config.docker_network or DEFAULT_DOCKER_NETWORK
        container_ip = _get_container_ip(DOCKER_SONARQUBE_HOST)
        if container_ip:
            add_host = f"{DOCKER_SONARQUBE_HOST}:{container_ip}"

    # Write properties file to repo (scanner reads from /usr/src/sonar-project.properties)
    write_sonar_properties(repo_path, effective_config)

    # Build Docker command with explicit platform for ARM Mac compatibility
    cmd = [
        "docker",
        "run",
        "--rm",
        "--platform",
        "linux/amd64",  # Scanner image is amd64-only
    ]
    if docker_network:
        cmd.extend(["--network", docker_network])
    if add_host:
        cmd.extend(["--add-host", add_host])
    cmd.extend([
        "-v",
        f"{repo_path.absolute()}:/usr/src",
        "-w",
        "/usr/src",
        config.docker_image,
    ])

    logger.info(
        "Running sonar-scanner via Docker",
        repo_path=str(repo_path),
        project_key=config.project_key,
    )

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=config.timeout,
        cwd=str(repo_path),
    )


def _dotnet_available() -> bool:
    """Return True if dotnet CLI is available."""
    return shutil.which("dotnet") is not None


def _dotnet_sonarscanner_available() -> bool:
    """Return True if dotnet-sonarscanner tool is available."""
    if not _dotnet_available():
        return False
    try:
        result = subprocess.run(
            ["dotnet", "sonarscanner", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def _detect_target_framework(repo_path: Path) -> str | None:
    """Detect .NET target framework from .csproj or global.json files.

    Args:
        repo_path: Path to the repository

    Returns:
        Detected framework version (e.g., "10.0") or None if not detected
    """
    import json
    import re

    # Check global.json first (explicit SDK version)
    global_json = repo_path / "global.json"
    if global_json.exists():
        try:
            data = json.loads(global_json.read_text())
            version = data.get("sdk", {}).get("version", "")
            if version:
                # Extract major.minor (e.g., "10.0.100" -> "10.0")
                match = re.match(r"(\d+\.\d+)", version)
                if match:
                    return match.group(1)
        except (json.JSONDecodeError, KeyError):
            pass

    # Scan .csproj files for TargetFramework
    frameworks: set[str] = set()
    for csproj in repo_path.rglob("*.csproj"):
        # Skip common non-source directories
        if any(part in {"bin", "obj", ".git", ".idea", ".vs"} for part in csproj.parts):
            continue
        try:
            content = csproj.read_text()
            # Match <TargetFramework>net10.0</TargetFramework> or similar
            matches = re.findall(r"<TargetFramework>net(\d+\.\d+)", content)
            frameworks.update(matches)
        except Exception:
            continue

    if frameworks:
        # Return highest version found
        return max(frameworks, key=lambda v: tuple(map(int, v.split("."))))

    return None


def _find_dotnet_project(repo_path: Path) -> Path | None:
    """Find a dotnet project or solution file to build."""
    def _candidate_score(path: Path) -> tuple[int, int, str]:
        # Prefer solutions, then csproj. Prefer shallower paths.
        is_solution = 0 if path.suffix == ".sln" else 1
        depth = len(path.relative_to(repo_path).parts)
        return (is_solution, depth, str(path))

    for pattern in ("**/*.sln", "**/*.csproj"):
        matches = [
            p
            for p in repo_path.glob(pattern)
            if not any(part in {"bin", "obj", ".git", ".idea", ".vs"} for part in p.parts)
        ]
        if matches:
            return sorted(matches, key=_candidate_score)[0]
    return None


def run_scanner_dotnet(
    repo_path: Path,
    config: ScannerConfig,
) -> str:
    """Run SonarScanner for .NET on a repository."""
    logger.info(
        "Running SonarScanner for .NET",
        repo_path=str(repo_path),
        project_key=config.project_key,
    )

    props_path = repo_path / "sonar-project.properties"
    moved_props = None
    if props_path.exists():
        moved_props = props_path.with_suffix(".properties.bak")
        props_path.rename(moved_props)
        logger.info("Temporarily moved sonar-project.properties for dotnet scanner")

    begin_cmd = [
        "dotnet",
        "sonarscanner",
        "begin",
        f"/k:{config.project_key}",
        f"/n:{config.project_name or config.project_key}",
        f"/d:sonar.host.url={config.sonarqube_url}",
    ]
    if config.project_version:
        begin_cmd.append(f"/v:{config.project_version}")
    if config.token:
        begin_cmd.append(f"/d:sonar.login={config.token}")
    if config.exclusions:
        begin_cmd.append(f"/d:sonar.exclusions={','.join(config.exclusions)}")
    for key, value in config.extra_properties.items():
        begin_cmd.append(f"/d:{key}={value}")

    try:
        begin_result = subprocess.run(
            begin_cmd,
            capture_output=True,
            text=True,
            timeout=config.timeout,
            cwd=str(repo_path),
        )

        if begin_result.stdout:
            logger.debug("Scanner begin stdout", output=begin_result.stdout[-2000:])
        if begin_result.stderr:
            logger.debug("Scanner begin stderr", output=begin_result.stderr[-2000:])

        if begin_result.returncode != 0:
            raise ScannerError(
                f"Dotnet scanner begin failed with exit code {begin_result.returncode}: {begin_result.stderr}"
            )

        project_file = _find_dotnet_project(repo_path)
        build_cmd = ["dotnet", "build"]
        if project_file:
            build_cmd.append(str(project_file))

        build_result = subprocess.run(
            build_cmd,
            capture_output=True,
            text=True,
            timeout=config.timeout,
            cwd=str(repo_path),
        )

        if build_result.stdout:
            logger.debug("Dotnet build stdout", output=build_result.stdout[-2000:])
        if build_result.stderr:
            logger.debug("Dotnet build stderr", output=build_result.stderr[-2000:])

        if build_result.returncode != 0:
            raise ScannerError(
                f"Dotnet build failed with exit code {build_result.returncode}: {build_result.stderr}"
            )

        end_cmd = ["dotnet", "sonarscanner", "end"]
        if config.token:
            end_cmd.append(f"/d:sonar.login={config.token}")

        end_result = subprocess.run(
            end_cmd,
            capture_output=True,
            text=True,
            timeout=config.timeout,
            cwd=str(repo_path),
        )

        if end_result.stdout:
            logger.debug("Scanner end stdout", output=end_result.stdout[-2000:])
        if end_result.stderr:
            logger.debug("Scanner end stderr", output=end_result.stderr[-2000:])

        if end_result.returncode != 0:
            raise ScannerError(
                f"Dotnet scanner end failed with exit code {end_result.returncode}: {end_result.stderr}"
            )
    finally:
        if moved_props:
            moved_props.rename(props_path)
            logger.info("Restored sonar-project.properties after dotnet scanner")

    combined_output = (begin_result.stdout or "") + (begin_result.stderr or "") + (end_result.stdout or "") + (end_result.stderr or "")
    task_id = extract_task_id(combined_output)
    if task_id:
        logger.info("Scanner completed", task_id=task_id)
    else:
        logger.warning("Could not extract task ID from dotnet scanner output")
    return task_id or ""


def run_scanner_dotnet_docker(
    repo_path: Path,
    config: ScannerConfig,
) -> str:
    """Run SonarScanner for .NET using a Dockerized dotnet SDK."""
    logger.info(
        "Running SonarScanner for .NET via Docker",
        repo_path=str(repo_path),
        project_key=config.project_key,
    )

    docker_network = config.docker_network or DEFAULT_DOCKER_NETWORK
    effective_url = config.sonarqube_url
    add_host = None
    if config.sonarqube_url.startswith("http://localhost") or config.sonarqube_url.startswith("http://127.0.0.1"):
        effective_url = f"http://{DOCKER_SONARQUBE_HOST}:9000"
        container_ip = _get_container_ip(DOCKER_SONARQUBE_HOST)
        if container_ip:
            add_host = f"{DOCKER_SONARQUBE_HOST}:{container_ip}"

    project_file = _find_dotnet_project(repo_path)
    build_cmd = "dotnet build"
    if project_file:
        build_target = project_file.relative_to(repo_path)
        build_cmd = f"dotnet build {build_target}"

    exclusions = ",".join(config.exclusions) if config.exclusions else ""
    extra_props = " ".join(
        f"/d:{key}={value}" for key, value in config.extra_properties.items()
    )
    token_arg = f"/d:sonar.login={config.token}" if config.token else ""

    script = " && ".join(
        part
        for part in (
            "set -e",
            "mkdir -p /tmp/src",
            "cp -a /src/. /tmp/src",
            "cd /tmp/src",
            "find /tmp/src -name sonar-project.properties -delete",
            "dotnet tool install --tool-path /tmp/dotnet-tools dotnet-sonarscanner",
            "export PATH=/tmp/dotnet-tools:$PATH",
            f"dotnet sonarscanner begin /k:{config.project_key} /n:{config.project_name or config.project_key} /d:sonar.host.url={effective_url} /d:sonar.projectBaseDir=/tmp/src {token_arg} {extra_props} {'/d:sonar.exclusions=' + exclusions if exclusions else ''}",
            build_cmd,
            f"dotnet sonarscanner end {token_arg}",
        )
        if part
    )

    cmd = [
        "docker",
        "run",
        "--rm",
        "--platform",
        "linux/amd64",
    ]
    if docker_network:
        cmd.extend(["--network", docker_network])
    if add_host:
        cmd.extend(["--add-host", add_host])
    cmd.extend([
        "-e",
        "DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1",
        "-e",
        "DOTNET_CLI_TELEMETRY_OPTOUT=1",
        "-e",
        "LANG=C.UTF-8",
        "-e",
        "LC_ALL=C.UTF-8",
        "-e",
        "JAVA_TOOL_OPTIONS=-Dfile.encoding=UTF-8",
        "-v",
        f"{repo_path.absolute()}:/src",
        "-w",
        "/src",
        f"mcr.microsoft.com/dotnet/sdk:{config.dotnet_sdk_version}",
        "bash",
        "-lc",
        script,
    ])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=config.timeout,
        cwd=str(repo_path),
    )

    if result.stdout:
        logger.debug("Dotnet docker stdout", output=result.stdout[-2000:])
    if result.stderr:
        logger.debug("Dotnet docker stderr", output=result.stderr[-2000:])

    if result.returncode != 0:
        raise ScannerError(
            f"Dotnet docker scanner failed with exit code {result.returncode}: {result.stderr}"
        )

    task_id = extract_task_id(result.stdout + result.stderr)
    if task_id:
        logger.info("Scanner completed", task_id=task_id)
    else:
        logger.warning("Could not extract task ID from dotnet docker output")
    return task_id or ""


def run_scanner_native(
    repo_path: Path,
    config: ScannerConfig,
) -> subprocess.CompletedProcess:
    """Run sonar-scanner using native installation.

    Assumes sonar-scanner is available in PATH.

    Args:
        repo_path: Path to repository
        config: Scanner configuration

    Returns:
        Completed process result
    """
    # Write properties file
    write_sonar_properties(repo_path, config)

    cmd = ["sonar-scanner"]

    logger.info(
        "Running sonar-scanner native",
        repo_path=str(repo_path),
        project_key=config.project_key,
    )

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=config.timeout,
        cwd=str(repo_path),
    )


def run_sonar_scanner(
    repo_path: Path,
    config: ScannerConfig,
) -> str:
    """Run sonar-scanner against a repository.

    Args:
        repo_path: Path to repository
        config: Scanner configuration

    Returns:
        Task ID from scanner output

    Raises:
        ScannerError: If scanner execution fails
    """
    logger.info(
        "Starting sonar-scanner",
        repo_path=str(repo_path),
        project_key=config.project_key,
        use_docker=config.use_docker,
    )

    try:
        languages = detect_language(repo_path)
        if "cs" in languages and _dotnet_sonarscanner_available():
            logger.info("Using dotnet scanner for C# project", languages=languages)
            return run_scanner_dotnet(repo_path, config)
        if "cs" in languages and config.use_docker:
            logger.info("Using dockerized dotnet scanner for C# project", languages=languages)
            return run_scanner_dotnet_docker(repo_path, config)
        if "cs" in languages and not _dotnet_sonarscanner_available():
            logger.warning(
                "Dotnet SonarScanner not available, falling back to generic scanner",
                languages=languages,
            )

        if config.use_docker:
            candidates = _build_docker_candidates(config)
            for idx, candidate in enumerate(candidates, start=1):
                result = None
                for attempt in range(candidate.retry_attempts + 1):
                    result = run_scanner_docker(repo_path, candidate)

                    if result.stdout:
                        logger.debug("Scanner stdout", output=result.stdout[-2000:])
                    if result.stderr:
                        logger.debug("Scanner stderr", output=result.stderr[-2000:])

                    if result.returncode == 0:
                        task_id = extract_task_id(result.stdout + result.stderr)
                        if task_id:
                            logger.info("Scanner completed", task_id=task_id)
                        else:
                            logger.warning("Could not extract task ID from scanner output")
                        return task_id or ""

                    if _is_busy_error(result.stderr) and attempt < candidate.retry_attempts:
                        logger.warning(
                            "Scanner busy, retrying after delay",
                            attempt=attempt + 1,
                        )
                        time.sleep(15)
                        continue

                    if _is_connection_error(result.stderr) and attempt < candidate.retry_attempts:
                        logger.warning(
                            "Scanner connection failed, retrying",
                            attempt=attempt + 1,
                        )
                        time.sleep(5)
                        continue
                    break

                if result and _is_connection_error(result.stderr) and idx < len(candidates):
                    logger.warning("Scanner connection failed, retrying fallback", attempt=idx + 1)
                    continue

                raise ScannerError(
                    f"Scanner failed with exit code {result.returncode}: {result.stderr}"
                )
        else:
            result = run_scanner_native(repo_path, config)

            if result.stdout:
                logger.debug("Scanner stdout", output=result.stdout[-2000:])
            if result.stderr:
                logger.debug("Scanner stderr", output=result.stderr[-2000:])

            if result.returncode != 0:
                raise ScannerError(
                    f"Scanner failed with exit code {result.returncode}: {result.stderr}"
                )

            task_id = extract_task_id(result.stdout + result.stderr)
            if task_id:
                logger.info("Scanner completed", task_id=task_id)
            else:
                logger.warning("Could not extract task ID from scanner output")
            return task_id or ""

    except subprocess.TimeoutExpired:
        raise ScannerError(f"Scanner timed out after {config.timeout}s")


def _build_docker_candidates(config: ScannerConfig) -> list[ScannerConfig]:
    """Build scanner configs with optional fallback for local SonarQube."""
    if config.sonarqube_url.startswith("http://localhost") or config.sonarqube_url.startswith("http://127.0.0.1"):
        fallback = replace(config, sonarqube_url="http://host.docker.internal:9000")
        return [config, fallback]
    return [config]


def _is_connection_error(stderr: str) -> bool:
    """Detect connection-related scanner failures."""
    if not stderr:
        return False
    lowered = stderr.lower()
    return any(
        marker in lowered
        for marker in (
            "fail to request url",
            "failed to connect",
            "connection refused",
            "connect timed out",
            "sockettimeoutexception",
            "unknownhostexception",
            "name does not resolve",
        )
    )


def _is_busy_error(stderr: str) -> bool:
    """Detect SonarQube project lock errors."""
    if not stderr:
        return False
    lowered = stderr.lower()
    return "analysis is already in progress" in lowered or "projectlock" in lowered


def extract_task_id(output: str) -> str | None:
    """Extract CE task ID from scanner output.

    Args:
        output: Scanner stdout/stderr

    Returns:
        Task ID or None if not found
    """
    # Look for patterns like:
    # - "More about the report processing at http://localhost:9000/api/ce/task?id=AX..."
    # - "task?id=AX..."
    import re

    patterns = [
        r"task\?id=([A-Za-z0-9_-]+)",
        r"ceTaskId=([A-Za-z0-9_-]+)",
        r"ANALYSIS SUCCESSFUL, you can browse ([A-Za-z0-9_-]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, output)
        if match:
            return match.group(1)

    return None


def detect_language(repo_path: Path) -> list[str]:
    """Detect programming languages in a repository.

    Args:
        repo_path: Path to repository

    Returns:
        List of detected language codes
    """
    languages = set()

    extensions_map = {
        ".cs": "cs",
        ".java": "java",
        ".js": "js",
        ".jsx": "js",
        ".ts": "ts",
        ".tsx": "ts",
        ".py": "py",
        ".go": "go",
        ".kt": "kotlin",
        ".scala": "scala",
        ".rb": "ruby",
        ".php": "php",
    }

    for root, _, files in os.walk(repo_path):
        # Skip hidden directories and common non-source directories
        if any(part.startswith(".") for part in Path(root).parts):
            continue
        if any(part in ["node_modules", "vendor", "bin", "obj"] for part in Path(root).parts):
            continue

        for file in files:
            ext = Path(file).suffix.lower()
            if ext in extensions_map:
                languages.add(extensions_map[ext])

    return list(languages)


def _has_compiled_java(repo_path: Path) -> bool:
    """Return True if the repo contains compiled Java classes."""
    for path in repo_path.rglob("*.class"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        return True
    return False


def get_scanner_properties_for_language(language: str) -> dict[str, str]:
    """Get language-specific scanner properties.

    Args:
        language: Language code

    Returns:
        Dictionary of additional properties
    """
    props = {}

    if language == "cs":
        # C# needs special handling with SonarScanner for .NET
        props["sonar.cs.roslyn.reportFilePath"] = "**/*.json"
    elif language == "java":
        props["sonar.java.source"] = "11"
    elif language in ("js", "ts"):
        props["sonar.javascript.lcov.reportPaths"] = "coverage/lcov.info"
    elif language == "py":
        props["sonar.python.coverage.reportPaths"] = "coverage.xml"

    return props


def create_scanner_config(
    project_key: str,
    repo_path: Path,
    sonarqube_url: str = "http://localhost:9000",
    token: str | None = None,
    use_docker: bool = True,
) -> ScannerConfig:
    """Create scanner configuration with auto-detected settings.

    Args:
        project_key: SonarQube project key
        repo_path: Path to repository
        sonarqube_url: SonarQube server URL
        token: Authentication token
        use_docker: Whether to use Docker scanner

    Returns:
        ScannerConfig with detected settings
    """
    # Detect languages first for SDK version detection
    languages = detect_language(repo_path)

    # Detect .NET SDK version for C# projects
    dotnet_sdk_version = "8.0"  # Default to LTS
    if "cs" in languages:
        # Allow explicit override via environment
        env_version = os.environ.get("DOTNET_SDK_VERSION")
        if env_version:
            dotnet_sdk_version = env_version
            logger.info("Using .NET SDK version from environment", version=dotnet_sdk_version)
        else:
            detected_version = _detect_target_framework(repo_path)
            if detected_version:
                dotnet_sdk_version = detected_version
                logger.info("Detected .NET target framework", version=detected_version)

    config = ScannerConfig(
        sonarqube_url=sonarqube_url,
        token=token,
        project_key=project_key,
        project_name=project_key,
        sources=".",
        use_docker=use_docker,
        exclusions=[
            "**/node_modules/**",
            "**/vendor/**",
            "**/.git/**",
            "**/bin/**",
            "**/obj/**",
            "**/build/**",
            "**/dist/**",
        ],
        dotnet_sdk_version=dotnet_sdk_version,
    )

    # Add language-specific properties
    for lang in languages:
        config.extra_properties.update(get_scanner_properties_for_language(lang))

    if os.getenv("SONAR_EXCLUDE_JAVA") == "1" and "java" in languages:
        config.exclusions.extend(["**/*.java", "**/*.kt"])
        logger.warning(
            "Excluding Java sources per configuration",
            project_key=project_key,
        )
    elif (
        os.getenv("SONAR_EXCLUDE_JAVA_IF_NO_BINARIES") == "1"
        and "java" in languages
        and not _has_compiled_java(repo_path)
    ):
        config.exclusions.extend(["**/*.java", "**/*.kt"])
        logger.warning(
            "Excluding Java sources due to missing compiled classes",
            project_key=project_key,
        )

    logger.info(
        "Created scanner config",
        languages=languages,
        project_key=project_key,
        dotnet_sdk_version=dotnet_sdk_version,
    )
    return config
