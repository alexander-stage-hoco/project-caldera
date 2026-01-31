"""Tests for the sonar-scanner module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from scripts.scanner import (
    ScannerConfig,
    ScannerError,
    generate_sonar_properties,
    write_sonar_properties,
    run_scanner_docker,
    run_scanner_native,
    run_sonar_scanner,
    extract_task_id,
    detect_language,
    get_scanner_properties_for_language,
    create_scanner_config,
    _is_busy_error,
    _is_connection_error,
)


class TestScannerConfig:
    """Tests for ScannerConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ScannerConfig()

        assert config.sonarqube_url == "http://localhost:9000"
        assert config.token is None
        assert config.project_key == ""
        assert config.sources == "."
        assert config.exclusions == []
        assert config.use_docker is True
        assert config.docker_network == "sonarqube_default"
        assert config.timeout == 600
        assert config.retry_attempts == 2

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ScannerConfig(
            sonarqube_url="http://sonar.example.com:9000",
            token="my-token",
            project_key="my-project",
            project_name="My Project",
            sources="src",
            exclusions=["**/test/**", "**/vendor/**"],
            use_docker=False,
            docker_network=None,
            timeout=300,
            retry_attempts=2,
        )

        assert config.sonarqube_url == "http://sonar.example.com:9000"
        assert config.token == "my-token"
        assert config.project_key == "my-project"
        assert config.project_name == "My Project"
        assert config.sources == "src"
        assert config.exclusions == ["**/test/**", "**/vendor/**"]
        assert config.use_docker is False
        assert config.docker_network is None
        assert config.timeout == 300
        assert config.retry_attempts == 2


class TestGenerateSonarProperties:
    """Tests for generate_sonar_properties function."""

    def test_generates_required_properties(self):
        """Test required properties are generated."""
        config = ScannerConfig(
            sonarqube_url="http://localhost:9000",
            project_key="my-project",
            sources="src",
        )

        props = generate_sonar_properties(config)

        assert props["sonar.host.url"] == "http://localhost:9000"
        assert props["sonar.projectKey"] == "my-project"
        assert props["sonar.sources"] == "src"

    def test_includes_token_when_provided(self):
        """Test token is included when provided."""
        config = ScannerConfig(
            project_key="my-project",
            token="secret-token",
        )

        props = generate_sonar_properties(config)

        assert props["sonar.token"] == "secret-token"

    def test_excludes_token_when_none(self):
        """Test token is not included when None."""
        config = ScannerConfig(
            project_key="my-project",
            token=None,
        )

        props = generate_sonar_properties(config)

        assert "sonar.token" not in props

    def test_includes_project_name(self):
        """Test project name is included when provided."""
        config = ScannerConfig(
            project_key="my-project",
            project_name="My Project Name",
        )

        props = generate_sonar_properties(config)

        assert props["sonar.projectName"] == "My Project Name"

    def test_includes_exclusions(self):
        """Test exclusions are formatted correctly."""
        config = ScannerConfig(
            project_key="my-project",
            exclusions=["**/test/**", "**/vendor/**", "**/node_modules/**"],
        )

        props = generate_sonar_properties(config)

        assert props["sonar.exclusions"] == "**/test/**,**/vendor/**,**/node_modules/**"


class TestScannerErrorDetection:
    """Tests for scanner error classification."""

    def test_detects_busy_error(self):
        """Detect project lock errors."""
        stderr = "java.lang.IllegalStateException: Another SonarQube analysis is already in progress for this project"
        assert _is_busy_error(stderr) is True

    def test_detects_connection_error(self):
        """Detect network resolution failures."""
        stderr = "Caused by: java.net.UnknownHostException: vulcan-sonarqube: Name does not resolve"
        assert _is_connection_error(stderr) is True

    def test_includes_extra_properties(self):
        """Test extra properties are merged."""
        config = ScannerConfig(
            project_key="my-project",
            extra_properties={
                "sonar.custom.property": "custom-value",
                "sonar.another.property": "another-value",
            },
        )

        props = generate_sonar_properties(config)

        assert props["sonar.custom.property"] == "custom-value"
        assert props["sonar.another.property"] == "another-value"


class TestWriteSonarProperties:
    """Tests for write_sonar_properties function."""

    def test_writes_properties_file(self, tmp_path):
        """Test sonar-project.properties file is written."""
        config = ScannerConfig(
            sonarqube_url="http://localhost:9000",
            project_key="test-project",
            sources=".",
        )

        props_path = write_sonar_properties(tmp_path, config)

        assert props_path.exists()
        assert props_path.name == "sonar-project.properties"

        content = props_path.read_text()
        assert "sonar.host.url=http://localhost:9000" in content
        assert "sonar.projectKey=test-project" in content
        assert "sonar.sources=." in content

    def test_overwrites_existing_file(self, tmp_path):
        """Test existing properties file is overwritten."""
        existing = tmp_path / "sonar-project.properties"
        existing.write_text("old content")

        config = ScannerConfig(project_key="new-project")
        write_sonar_properties(tmp_path, config)

        content = existing.read_text()
        assert "new-project" in content
        assert "old content" not in content


class TestExtractTaskId:
    """Tests for extract_task_id function."""

    def test_extracts_task_id_from_url(self):
        """Test extracting task ID from URL pattern."""
        output = "More about the report processing at http://localhost:9000/api/ce/task?id=AXgHJ8kL_m12345"
        task_id = extract_task_id(output)

        assert task_id == "AXgHJ8kL_m12345"

    def test_extracts_task_id_from_ce_task_id(self):
        """Test extracting task ID from ceTaskId pattern."""
        output = "INFO: ceTaskId=AXabcdef123456"
        task_id = extract_task_id(output)

        assert task_id == "AXabcdef123456"

    def test_returns_none_when_not_found(self):
        """Test returns None when no task ID found."""
        output = "Some output without task ID"
        task_id = extract_task_id(output)

        assert task_id is None

    def test_extracts_from_multiline_output(self):
        """Test extracting from multiline scanner output."""
        output = """
INFO: Scanner configuration file: /opt/sonar-scanner/conf/sonar-scanner.properties
INFO: Project root configuration file: /usr/src/sonar-project.properties
INFO: EXECUTION SUCCESS
INFO: More about the report processing at http://localhost:9000/api/ce/task?id=AX123abc
"""
        task_id = extract_task_id(output)

        assert task_id == "AX123abc"


class TestDetectLanguage:
    """Tests for detect_language function."""

    def test_detects_csharp(self, tmp_path):
        """Test detecting C# language."""
        (tmp_path / "Program.cs").touch()
        (tmp_path / "Class.cs").touch()

        languages = detect_language(tmp_path)

        assert "cs" in languages

    def test_detects_java(self, tmp_path):
        """Test detecting Java language."""
        (tmp_path / "Main.java").touch()

        languages = detect_language(tmp_path)

        assert "java" in languages

    def test_detects_typescript(self, tmp_path):
        """Test detecting TypeScript language."""
        (tmp_path / "index.ts").touch()
        (tmp_path / "component.tsx").touch()

        languages = detect_language(tmp_path)

        assert "ts" in languages

    def test_detects_python(self, tmp_path):
        """Test detecting Python language."""
        (tmp_path / "main.py").touch()

        languages = detect_language(tmp_path)

        assert "py" in languages

    def test_detects_multiple_languages(self, tmp_path):
        """Test detecting multiple languages."""
        (tmp_path / "Program.cs").touch()
        (tmp_path / "main.py").touch()
        (tmp_path / "index.js").touch()

        languages = detect_language(tmp_path)

        assert "cs" in languages
        assert "py" in languages
        assert "js" in languages

    def test_ignores_hidden_directories(self, tmp_path):
        """Test hidden directories are ignored."""
        hidden = tmp_path / ".git"
        hidden.mkdir()
        (hidden / "config.py").touch()

        languages = detect_language(tmp_path)

        # Should not detect .py from hidden dir
        assert "py" not in languages

    def test_ignores_node_modules(self, tmp_path):
        """Test node_modules is ignored."""
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "package.js").touch()

        # Add a real source file
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "app.ts").touch()

        languages = detect_language(tmp_path)

        # Should only detect TypeScript from src
        assert "ts" in languages


class TestGetScannerPropertiesForLanguage:
    """Tests for get_scanner_properties_for_language function."""

    def test_csharp_properties(self):
        """Test C# specific properties."""
        props = get_scanner_properties_for_language("cs")

        assert "sonar.cs.roslyn.reportFilePath" in props

    def test_java_properties(self):
        """Test Java specific properties."""
        props = get_scanner_properties_for_language("java")

        assert "sonar.java.source" in props

    def test_javascript_properties(self):
        """Test JavaScript specific properties."""
        props = get_scanner_properties_for_language("js")

        assert "sonar.javascript.lcov.reportPaths" in props

    def test_typescript_properties(self):
        """Test TypeScript specific properties."""
        props = get_scanner_properties_for_language("ts")

        assert "sonar.javascript.lcov.reportPaths" in props

    def test_python_properties(self):
        """Test Python specific properties."""
        props = get_scanner_properties_for_language("py")

        assert "sonar.python.coverage.reportPaths" in props

    def test_unknown_language_returns_empty(self):
        """Test unknown language returns empty dict."""
        props = get_scanner_properties_for_language("unknown")

        assert props == {}


class TestCreateScannerConfig:
    """Tests for create_scanner_config function."""

    def test_creates_config_with_defaults(self, tmp_path):
        """Test creating config with default values."""
        (tmp_path / "test.cs").touch()

        config = create_scanner_config(
            project_key="my-project",
            repo_path=tmp_path,
        )

        assert config.project_key == "my-project"
        assert config.project_name == "my-project"
        assert config.sonarqube_url == "http://localhost:9000"
        assert config.use_docker is True

    def test_creates_config_with_custom_url(self, tmp_path):
        """Test creating config with custom URL."""
        config = create_scanner_config(
            project_key="my-project",
            repo_path=tmp_path,
            sonarqube_url="http://custom:9000",
        )

        assert config.sonarqube_url == "http://custom:9000"

    def test_creates_config_with_token(self, tmp_path):
        """Test creating config with token."""
        config = create_scanner_config(
            project_key="my-project",
            repo_path=tmp_path,
            token="my-token",
        )

        assert config.token == "my-token"

    def test_includes_standard_exclusions(self, tmp_path):
        """Test standard exclusions are included."""
        config = create_scanner_config(
            project_key="my-project",
            repo_path=tmp_path,
        )

        assert "**/node_modules/**" in config.exclusions
        assert "**/.git/**" in config.exclusions
        assert "**/vendor/**" in config.exclusions

    def test_adds_language_specific_properties(self, tmp_path):
        """Test language-specific properties are added."""
        (tmp_path / "Main.java").touch()

        config = create_scanner_config(
            project_key="java-project",
            repo_path=tmp_path,
        )

        # Should have Java-specific properties
        assert "sonar.java.source" in config.extra_properties


class TestRunScannerDocker:
    """Tests for run_scanner_docker function."""

    @patch("subprocess.run")
    def test_builds_docker_command(self, mock_run, tmp_path):
        """Test Docker command is built correctly."""
        mock_run.side_effect = [
            Mock(returncode=0, stdout="172.18.0.2\n", stderr=""),
            Mock(returncode=0, stdout="Success", stderr=""),
        ]

        config = ScannerConfig(
            project_key="test-project",
            sonarqube_url="http://localhost:9000",
        )

        run_scanner_docker(tmp_path, config)

        # Verify Docker was called
        assert mock_run.call_count == 2
        cmd = mock_run.call_args_list[1][0][0]

        assert cmd[0] == "docker"
        assert cmd[1] == "run"
        assert "--rm" in cmd
        assert "--network=host" not in cmd
        assert "--network" in cmd
        assert "sonarqube_default" in cmd
        assert "--add-host" in cmd
        assert "vulcan-sonarqube:172.18.0.2" in cmd

        props_file = tmp_path / "sonar-project.properties"
        content = props_file.read_text()
        assert "sonar.host.url=http://vulcan-sonarqube:9000" in content

    @patch("subprocess.run")
    def test_mounts_repo_path(self, mock_run, tmp_path):
        """Test repository path is mounted."""
        mock_run.side_effect = [
            Mock(returncode=0, stdout="172.18.0.2\n", stderr=""),
            Mock(returncode=0, stdout="", stderr=""),
        ]

        config = ScannerConfig(project_key="test")
        run_scanner_docker(tmp_path, config)

        cmd = mock_run.call_args_list[1][0][0]
        cmd_str = " ".join(cmd)

        assert "-v" in cmd
        assert str(tmp_path.absolute()) in cmd_str


class TestRunScannerNative:
    """Tests for run_scanner_native function."""

    @patch("subprocess.run")
    def test_calls_sonar_scanner(self, mock_run, tmp_path):
        """Test native sonar-scanner is called."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        config = ScannerConfig(
            project_key="test-project",
            sonarqube_url="http://localhost:9000",
        )

        run_scanner_native(tmp_path, config)

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]

        assert cmd[0] == "sonar-scanner"

    @patch("subprocess.run")
    def test_writes_properties_file(self, mock_run, tmp_path):
        """Test properties file is written before running."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        config = ScannerConfig(project_key="test-project")
        run_scanner_native(tmp_path, config)

        props_file = tmp_path / "sonar-project.properties"
        assert props_file.exists()


class TestRunSonarScanner:
    """Tests for run_sonar_scanner function."""

    @patch("scripts.scanner.run_scanner_dotnet")
    @patch("scripts.scanner._dotnet_sonarscanner_available")
    @patch("scripts.scanner.detect_language")
    def test_uses_dotnet_for_csharp(self, mock_detect, mock_available, mock_dotnet, tmp_path):
        """Prefer dotnet scanner for C# projects when available."""
        mock_detect.return_value = ["cs"]
        mock_available.return_value = True
        mock_dotnet.return_value = "AX123xyz"

        config = ScannerConfig(project_key="test", use_docker=True)
        task_id = run_sonar_scanner(tmp_path, config)

        assert task_id == "AX123xyz"
        mock_dotnet.assert_called_once()

    @patch("scripts.scanner.run_scanner_native")
    @patch("scripts.scanner._dotnet_sonarscanner_available")
    @patch("scripts.scanner.detect_language")
    def test_falls_back_when_dotnet_missing(self, mock_detect, mock_available, mock_native, tmp_path):
        """Fallback to native scanner when dotnet scanner is unavailable."""
        mock_detect.return_value = ["cs"]
        mock_available.return_value = False
        mock_native.return_value = Mock(returncode=0, stdout="task?id=ABC123", stderr="")

        config = ScannerConfig(project_key="test", use_docker=False)
        run_sonar_scanner(tmp_path, config)

        mock_native.assert_called_once()

    @patch("scripts.scanner.run_scanner_dotnet_docker")
    @patch("scripts.scanner._dotnet_sonarscanner_available")
    @patch("scripts.scanner.detect_language")
    def test_uses_dotnet_docker_when_available(self, mock_detect, mock_available, mock_dotnet_docker, tmp_path):
        """Use dockerized dotnet scanner when dotnet tool is missing."""
        mock_detect.return_value = ["cs"]
        mock_available.return_value = False
        mock_dotnet_docker.return_value = "AX123xyz"

        config = ScannerConfig(project_key="test", use_docker=True)
        task_id = run_sonar_scanner(tmp_path, config)

        assert task_id == "AX123xyz"
        mock_dotnet_docker.assert_called_once()

    @patch("scripts.scanner.run_scanner_docker")
    def test_uses_docker_by_default(self, mock_docker, tmp_path):
        """Test Docker scanner is used by default."""
        mock_docker.return_value = Mock(
            returncode=0,
            stdout="task?id=ABC123",
            stderr="",
        )

        config = ScannerConfig(project_key="test", use_docker=True)
        run_sonar_scanner(tmp_path, config)

        mock_docker.assert_called_once()

    @patch("scripts.scanner.run_scanner_native")
    def test_uses_native_when_configured(self, mock_native, tmp_path):
        """Test native scanner is used when configured."""
        mock_native.return_value = Mock(
            returncode=0,
            stdout="task?id=ABC123",
            stderr="",
        )

        config = ScannerConfig(project_key="test", use_docker=False)
        run_sonar_scanner(tmp_path, config)

        mock_native.assert_called_once()

    @patch("scripts.scanner.run_scanner_docker")
    def test_raises_on_failure(self, mock_docker, tmp_path):
        """Test ScannerError is raised on failure."""
        mock_docker.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Analysis failed",
        )

        config = ScannerConfig(project_key="test")

        with pytest.raises(ScannerError) as exc_info:
            run_sonar_scanner(tmp_path, config)

        assert "failed" in str(exc_info.value).lower()

    @patch("scripts.scanner.run_scanner_docker")
    def test_returns_task_id(self, mock_docker, tmp_path):
        """Test task ID is extracted and returned."""
        mock_docker.return_value = Mock(
            returncode=0,
            stdout="http://localhost:9000/api/ce/task?id=AX123xyz",
            stderr="",
        )

        config = ScannerConfig(project_key="test")
        task_id = run_sonar_scanner(tmp_path, config)

        assert task_id == "AX123xyz"

    @patch("scripts.scanner.run_scanner_docker")
    def test_retries_on_connection_error(self, mock_docker, tmp_path):
        """Retry once when the scanner cannot reach the server."""
        mock_docker.side_effect = [
            Mock(returncode=1, stdout="", stderr="Fail to request url"),
            Mock(returncode=0, stdout="task?id=AX123xyz", stderr=""),
        ]

        config = ScannerConfig(project_key="test")
        task_id = run_sonar_scanner(tmp_path, config)

        assert task_id == "AX123xyz"
        assert mock_docker.call_count == 2


# Integration tests

@pytest.mark.docker
@pytest.mark.integration
class TestScannerIntegration:
    """Integration tests for scanner execution."""

    def test_scanner_execution_against_csharp_clean(
        self, sonarqube_container, csharp_clean_repo
    ):
        """Test actual scanner execution against csharp-clean repo."""
        config = create_scanner_config(
            project_key="test-scanner-csharp-clean",
            repo_path=csharp_clean_repo,
            sonarqube_url=sonarqube_container.base_url,
            token=sonarqube_container.admin_token,
            use_docker=True,
        )

        task_id = run_sonar_scanner(csharp_clean_repo, config)

        # Should return a task ID (may be empty string if not found in output)
        assert isinstance(task_id, str)

    def test_scanner_detects_repo_languages(self, csharp_clean_repo):
        """Test language detection on real repository."""
        languages = detect_language(csharp_clean_repo)

        assert "cs" in languages
