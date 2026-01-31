"""Pytest configuration for SonarQube tool tests."""

import sys
from pathlib import Path
from typing import Generator

# Add the scripts directory to the Python path for imports
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir.parent))


import pytest


# ============================================
# Pytest configuration hooks
# ============================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "docker: mark test as requiring Docker")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Skip integration tests by default unless explicitly requested."""
    if config.getoption("-m"):
        # User specified markers, respect their choice
        return

    skip_integration = pytest.mark.skip(reason="Integration tests require -m 'integration' or --run-integration")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests (requires Docker)",
    )
    parser.addoption(
        "--keep-container",
        action="store_true",
        default=False,
        help="Keep SonarQube container running after tests",
    )


# ============================================
# Integration test fixtures
# ============================================

@pytest.fixture(scope="session")
def docker_available() -> bool:
    """Check if Docker is available."""
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


@pytest.fixture(scope="session")
def sonarqube_container(request, docker_available):
    """Start SonarQube container for integration tests.

    This fixture is session-scoped, so the container is started once
    and shared across all integration tests in the session.
    """
    if not docker_available:
        pytest.skip("Docker is not available")

    from scripts.docker_lifecycle import SonarQubeContainer, DockerConfig

    keep_running = request.config.getoption("--keep-container", default=False)

    config = DockerConfig(
        startup_timeout=300,  # 5 minutes for SonarQube to start
        health_check_interval=5,
    )

    container = SonarQubeContainer(
        config=config,
        keep_running=keep_running,
        remove_volumes=True,  # Clean up after tests to prevent disk space accumulation
    )

    container.__enter__()
    yield container
    container.__exit__(None, None, None)


@pytest.fixture
def sonarqube_client(sonarqube_container):
    """Provide a configured API client connected to the test container."""
    from scripts.api.client import SonarQubeClient, ApiConfig

    config = ApiConfig(
        base_url=sonarqube_container.base_url,
        token=sonarqube_container.admin_token,  # Use auto-generated token
        timeout=60,
    )

    with SonarQubeClient(config) as client:
        yield client


@pytest.fixture
def sonarqube_token(sonarqube_container) -> str:
    """Get the generated SonarQube token for scanner use."""
    return sonarqube_container.admin_token


@pytest.fixture
def sonarqube_url(sonarqube_container) -> str:
    """Get the SonarQube base URL."""
    return sonarqube_container.base_url


# ============================================
# Path fixtures
# ============================================

@pytest.fixture
def project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def eval_repos_dir(project_root) -> Path:
    """Get the eval-repos/synthetic directory."""
    return project_root / "eval-repos" / "synthetic"


@pytest.fixture
def csharp_clean_repo(eval_repos_dir) -> Path:
    """Get the csharp-clean eval repo path."""
    return eval_repos_dir / "csharp-clean"


@pytest.fixture
def csharp_complex_repo(eval_repos_dir) -> Path:
    """Get the csharp-complex eval repo path."""
    return eval_repos_dir / "csharp-complex"


@pytest.fixture
def java_security_repo(eval_repos_dir) -> Path:
    """Get the java-security eval repo path."""
    return eval_repos_dir / "java-security"


@pytest.fixture
def typescript_duplication_repo(eval_repos_dir) -> Path:
    """Get the typescript-duplication eval repo path."""
    return eval_repos_dir / "typescript-duplication"


@pytest.fixture
def ground_truth_dir(project_root) -> Path:
    """Get the ground truth directory."""
    return project_root / "evaluation" / "ground-truth"


@pytest.fixture
def output_dir(tmp_path) -> Path:
    """Get a temporary output directory for test results."""
    output = tmp_path / "output"
    output.mkdir(parents=True, exist_ok=True)
    return output


@pytest.fixture
def schema_path(project_root) -> Path:
    """Get the JSON schema path."""
    return project_root / "schemas" / "sonar_export.schema.json"


@pytest.fixture
def sample_sonarqube_export():
    """Sample SonarQube export data for testing."""
    return {
        "schema_version": "1.2.0",
        "generated_at": "2024-01-01T00:00:00Z",
        "repo_name": "test-project",
        "repo_path": "/tmp/test-project",
        "results": {
            "tool": "sonarqube",
            "tool_version": "10.5.0",
            "source": {
                "sonarqube_url": "http://localhost:9000",
                "project_key": "test-project",
                "analysis_id": "AX123",
                "revision": "abc123def",
                "repo_name": "test-project",
                "repo_path": "/tmp/test-project",
            },
            "metric_catalog": [
                {
                    "key": "ncloc",
                    "name": "Lines of Code",
                    "type": "INT",
                    "domain": "Size",
                },
                {
                    "key": "complexity",
                    "name": "Cyclomatic Complexity",
                    "type": "INT",
                    "domain": "Complexity",
                },
            ],
            "components": {
                "root_key": "test-project",
                "by_key": {
                    "test-project": {
                        "key": "test-project",
                        "name": "Test Project",
                        "qualifier": "TRK",
                    },
                    "test-project:src": {
                        "key": "test-project:src",
                        "name": "src",
                        "qualifier": "DIR",
                        "path": "src",
                    },
                    "test-project:src/main.py": {
                        "key": "test-project:src/main.py",
                        "name": "main.py",
                        "qualifier": "FIL",
                        "path": "src/main.py",
                        "language": "py",
                    },
                },
                "children": {
                    "test-project": ["test-project:src"],
                    "test-project:src": ["test-project:src/main.py"],
                },
            },
            "measures": {
                "by_component_key": {
                    "test-project:src/main.py": {
                        "key": "test-project:src/main.py",
                        "name": "main.py",
                        "qualifier": "FIL",
                        "path": "src/main.py",
                        "language": "py",
                        "measures": [
                            {"metric": "ncloc", "value": "100"},
                            {"metric": "complexity", "value": "15"},
                        ],
                    },
                },
                "metrics_requested": ["ncloc", "complexity"],
            },
            "issues": {
                "items": [
                    {
                        "key": "issue-1",
                        "rule": "python:S1234",
                        "severity": "MAJOR",
                        "type": "CODE_SMELL",
                        "status": "OPEN",
                        "message": "Refactor this function",
                        "component": "test-project:src/main.py",
                        "project": "test-project",
                        "line": 10,
                    },
                    {
                        "key": "issue-2",
                        "rule": "python:S5678",
                        "severity": "CRITICAL",
                        "type": "VULNERABILITY",
                        "status": "OPEN",
                        "message": "Fix this security issue",
                        "component": "test-project:src/main.py",
                        "project": "test-project",
                        "line": 25,
                    },
                ],
                "rollups": {
                    "total": 2,
                    "by_severity": {"MAJOR": 1, "CRITICAL": 1},
                    "by_type": {"CODE_SMELL": 1, "VULNERABILITY": 1},
                    "by_rule": {"python:S1234": 1, "python:S5678": 1},
                    "by_file": {"test-project:src/main.py": 2},
                    "by_directory": {"src": 2},
                },
            },
            "rules": {
                "by_key": {
                    "python:S1234": {
                        "key": "python:S1234",
                        "name": "Function complexity",
                        "type": "CODE_SMELL",
                        "severity": "MAJOR",
                        "status": "READY",
                        "language": "py",
                    },
                    "python:S5678": {
                        "key": "python:S5678",
                        "name": "Security vulnerability",
                        "type": "VULNERABILITY",
                        "severity": "CRITICAL",
                        "status": "READY",
                        "language": "py",
                    },
                },
            },
            "duplications": {
                "policy": {"top_n": 200, "min_density": 0.0},
                "by_file_key": {},
                "project_summary": {
                    "duplicated_lines": 0,
                    "duplicated_lines_density": 0.0,
                },
            },
            "quality_gate": {
                "status": "OK",
                "name": "Sonar way",
                "conditions": [
                    {
                        "metric": "new_coverage",
                        "comparator": "LT",
                        "threshold": "80",
                        "status": "OK",
                        "actual_value": "85.5",
                    },
                ],
                "failed_count": 0,
                "warning_count": 0,
            },
            "analyses": [
                {
                    "key": "analysis-1",
                    "date": "2024-01-01T00:00:00Z",
                    "project_version": "1.0.0",
                    "revision": "abc123def",
                },
            ],
            "derived_insights": {
                "hotspots": [
                    {
                        "key": "test-project:src/main.py",
                        "path": "src/main.py",
                        "language": "py",
                        "score": 25.0,
                        "ncloc": 100,
                        "complexity": 15,
                        "cognitive_complexity": 10,
                        "issues": 2,
                    },
                ],
                "directory_rollups": {
                    "src": {
                        "files": 1,
                        "ncloc": 100,
                        "complexity": 15,
                        "issues": 2,
                        "bugs": 0,
                        "vulnerabilities": 1,
                        "code_smells": 1,
                    },
                },
            },
            "limitations": {
                "no_symbol_graph": True,
                "no_call_graph": True,
                "no_data_flow": True,
                "issues_may_be_truncated": False,
            },
        },
    }


@pytest.fixture
def sample_ground_truth():
    """Sample ground truth data for testing."""
    return {
        "id": "test-project",
        "language": "python",
        "expected_languages": ["py"],
        "expected_issues": {"min": 1, "max": 10},
        "expected_bugs": {"min": 0, "max": 5},
        "expected_vulnerabilities": {"min": 0, "max": 5},
        "expected_smells": {"min": 0, "max": 10},
        "quality_gate_expected": "OK",
    }
