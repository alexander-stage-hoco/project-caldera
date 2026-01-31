"""
Shared fixtures for Layout Scanner tests.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pytest

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.classifier import ClassificationResult, LanguageResult
from scripts.tree_walker import DirectoryInfo, FileInfo, WalkResult
from scripts.config_loader import ScannerConfig, ClassificationConfig, IgnoreConfig, PerformanceConfig


# =============================================================================
# Path Fixtures
# =============================================================================

@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def scripts_dir(project_root) -> Path:
    """Return the scripts directory."""
    return project_root / "scripts"


@pytest.fixture
def synthetic_repos_dir(project_root) -> Path:
    """Return the synthetic repos directory."""
    return project_root / "eval-repos" / "synthetic"


@pytest.fixture
def schema_path(project_root) -> Path:
    """Return the path to the JSON schema."""
    return project_root / "schemas" / "layout.json"


# =============================================================================
# Temporary Repository Fixtures
# =============================================================================

@pytest.fixture
def temp_repo(tmp_path) -> Path:
    """Create a minimal temporary repository structure."""
    # Create basic structure
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "docs").mkdir()

    # Create files
    (tmp_path / "README.md").write_text("# Test Repo\n")
    (tmp_path / "src" / "main.py").write_text("# Main\nprint('hello')\n")
    (tmp_path / "src" / "utils.py").write_text("# Utils\ndef helper(): pass\n")
    (tmp_path / "tests" / "test_main.py").write_text("def test_main(): pass\n")
    (tmp_path / "docs" / "api.md").write_text("# API\n")

    return tmp_path


@pytest.fixture
def temp_repo_with_gitignore(tmp_path) -> Path:
    """Create a temporary repository with .gitignore."""
    # Create structure
    (tmp_path / "src").mkdir()
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "lodash").mkdir()

    # Create files
    (tmp_path / "src" / "main.py").write_text("# Main\n")
    (tmp_path / "node_modules" / "lodash" / "index.js").write_text("module.exports = {};\n")
    (tmp_path / ".gitignore").write_text("node_modules/\n*.pyc\n__pycache__/\n")

    return tmp_path


@pytest.fixture
def temp_repo_empty(tmp_path) -> Path:
    """Create an empty temporary repository."""
    return tmp_path


@pytest.fixture
def temp_repo_nested(tmp_path) -> Path:
    """Create a deeply nested repository structure."""
    # Create nested structure
    path = tmp_path
    for i in range(1, 6):
        path = path / f"level{i}"
        path.mkdir()
        (path / f"file{i}.py").write_text(f"# Level {i}\n")

    return tmp_path


@pytest.fixture
def temp_repo_unicode(tmp_path) -> Path:
    """Create a repository with unicode filenames."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "日本語").mkdir()

    (tmp_path / "README.md").write_text("# Unicode Test\n")
    (tmp_path / "docs" / "日本語.md").write_text("# Japanese\n")
    (tmp_path / "日本語" / "ファイル.py").write_text("# File\n")
    (tmp_path / "über.py").write_text("# German\n")

    return tmp_path


@pytest.fixture
def temp_repo_mixed_types(tmp_path) -> Path:
    """Create a repository with mixed file types."""
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "config").mkdir()
    (tmp_path / "dist").mkdir()

    # Source files
    (tmp_path / "src" / "main.py").write_text("# Main\n")
    (tmp_path / "src" / "app.ts").write_text("// App\n")

    # Test files
    (tmp_path / "tests" / "test_main.py").write_text("def test(): pass\n")
    (tmp_path / "tests" / "app.test.ts").write_text("test('app', () => {})\n")

    # Config files
    (tmp_path / "config" / "settings.json").write_text('{"key": "value"}\n')
    (tmp_path / "package.json").write_text('{"name": "test"}\n')
    (tmp_path / "tsconfig.json").write_text('{"compilerOptions": {}}\n')

    # Generated files
    (tmp_path / "dist" / "bundle.min.js").write_text("/* minified */\n")

    # Docs
    (tmp_path / "README.md").write_text("# Test\n")

    return tmp_path


# =============================================================================
# Config Fixtures
# =============================================================================

@pytest.fixture
def default_config() -> ScannerConfig:
    """Return a default scanner configuration."""
    return ScannerConfig(
        classification=ClassificationConfig(
            path_rules={},
            filename_rules={},
            extension_rules={},
        ),
        ignore=IgnoreConfig(
            respect_gitignore=True,
            additional_patterns=[],
        ),
        performance=PerformanceConfig(
            max_file_size_bytes=10_000_000,
            max_files=100_000,
        ),
    )


@pytest.fixture
def config_no_gitignore() -> ScannerConfig:
    """Return a configuration that ignores .gitignore."""
    return ScannerConfig(
        classification=ClassificationConfig(
            path_rules={},
            filename_rules={},
            extension_rules={},
        ),
        ignore=IgnoreConfig(
            respect_gitignore=False,
            additional_patterns=[],
        ),
        performance=PerformanceConfig(
            max_file_size_bytes=10_000_000,
            max_files=100_000,
        ),
    )


# =============================================================================
# Mock Data Fixtures
# =============================================================================

@pytest.fixture
def sample_file_info() -> FileInfo:
    """Return a sample FileInfo object."""
    from datetime import datetime, timezone
    return FileInfo(
        path="src/main.py",
        name="main.py",
        extension=".py",
        size_bytes=100,
        modified_time=datetime.now(timezone.utc),
        is_symlink=False,
    )


@pytest.fixture
def sample_directory_info() -> DirectoryInfo:
    """Return a sample DirectoryInfo object."""
    from datetime import datetime, timezone
    return DirectoryInfo(
        path="src",
        name="src",
        modified_time=datetime.now(timezone.utc),
        is_symlink=False,
    )


@pytest.fixture
def sample_walk_result(sample_file_info, sample_directory_info) -> WalkResult:
    """Return a sample WalkResult object."""
    return WalkResult(
        files=[sample_file_info],
        directories=[sample_directory_info],
        root_path=Path("/tmp/test"),
        errors=[],
    )


@pytest.fixture
def sample_classification_result() -> ClassificationResult:
    """Return a sample ClassificationResult."""
    return ClassificationResult(
        category="source",
        confidence=0.9,
        reason="extension:.py",
        signals={"extension": "source"},
    )


@pytest.fixture
def sample_language_result() -> LanguageResult:
    """Return a sample LanguageResult."""
    return LanguageResult(
        language="python",
        confidence=0.95,
    )


# =============================================================================
# Schema Fixtures
# =============================================================================

@pytest.fixture
def layout_schema(schema_path) -> Dict:
    """Load and return the JSON schema."""
    with open(schema_path) as f:
        return json.load(f)


# =============================================================================
# Synthetic Repo Fixtures
# =============================================================================

@pytest.fixture
def small_clean_repo_path(synthetic_repos_dir) -> Path:
    """Return path to small-clean synthetic repo."""
    path = synthetic_repos_dir / "small-clean"
    if not path.exists():
        pytest.skip("Synthetic repos not built. Run 'make build-repos' first.")
    return path


@pytest.fixture
def mixed_types_repo_path(synthetic_repos_dir) -> Path:
    """Return path to mixed-types synthetic repo."""
    path = synthetic_repos_dir / "mixed-types"
    if not path.exists():
        pytest.skip("Synthetic repos not built. Run 'make build-repos' first.")
    return path


@pytest.fixture
def vendor_heavy_repo_path(synthetic_repos_dir) -> Path:
    """Return path to vendor-heavy synthetic repo."""
    path = synthetic_repos_dir / "vendor-heavy"
    if not path.exists():
        pytest.skip("Synthetic repos not built. Run 'make build-repos' first.")
    return path


@pytest.fixture
def deep_nesting_repo_path(synthetic_repos_dir) -> Path:
    """Return path to deep-nesting synthetic repo."""
    path = synthetic_repos_dir / "deep-nesting"
    if not path.exists():
        pytest.skip("Synthetic repos not built. Run 'make build-repos' first.")
    return path


# =============================================================================
# Helper Functions
# =============================================================================

def create_files(base_path: Path, files: Dict[str, str]) -> None:
    """Helper to create multiple files from a dict."""
    for path, content in files.items():
        full_path = base_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
