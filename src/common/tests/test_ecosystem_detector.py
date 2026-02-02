"""Tests for ecosystem_detector module."""

from __future__ import annotations

import pytest

from ..ecosystem_detector import (
    ECOSYSTEM_PATTERNS,
    DependencyFile,
    EcosystemDetectionResult,
    EcosystemStatus,
    classify_dependency_file,
    detect_ecosystems,
    format_ecosystem_completeness,
    get_ecosystem_summary,
)


class TestEcosystemPatterns:
    """Tests for ECOSYSTEM_PATTERNS definitions."""

    def test_all_ecosystems_have_manifests(self):
        """Every ecosystem should have at least one manifest pattern."""
        for name, pattern in ECOSYSTEM_PATTERNS.items():
            assert (
                pattern.manifests or pattern.manifest_patterns
            ), f"Ecosystem {name} has no manifest patterns"

    def test_npm_patterns(self):
        """Test npm ecosystem patterns."""
        npm = ECOSYSTEM_PATTERNS["npm"]
        assert "package.json" in npm.manifests
        assert "package-lock.json" in npm.lockfiles
        assert "yarn.lock" in npm.lockfiles
        assert "pnpm-lock.yaml" in npm.lockfiles

    def test_python_ecosystems(self):
        """Test Python ecosystem patterns."""
        pip = ECOSYSTEM_PATTERNS["pip"]
        assert "requirements.txt" in pip.manifests
        assert pip.lockfile_expected is False

        poetry = ECOSYSTEM_PATTERNS["poetry"]
        assert "pyproject.toml" in poetry.manifests
        assert "poetry.lock" in poetry.lockfiles

        pipenv = ECOSYSTEM_PATTERNS["pipenv"]
        assert "Pipfile" in pipenv.manifests
        assert "Pipfile.lock" in pipenv.lockfiles

    def test_go_patterns(self):
        """Test Go ecosystem patterns."""
        go = ECOSYSTEM_PATTERNS["go"]
        assert "go.mod" in go.manifests
        assert "go.sum" in go.lockfiles

    def test_rust_patterns(self):
        """Test Rust ecosystem patterns."""
        rust = ECOSYSTEM_PATTERNS["rust"]
        assert "Cargo.toml" in rust.manifests
        assert "Cargo.lock" in rust.lockfiles

    def test_nuget_patterns(self):
        """Test NuGet ecosystem patterns with glob patterns."""
        nuget = ECOSYSTEM_PATTERNS["nuget"]
        assert "packages.config" in nuget.manifests
        assert "*.csproj" in nuget.manifest_patterns
        assert "packages.lock.json" in nuget.lockfiles


class TestClassifyDependencyFile:
    """Tests for classify_dependency_file function."""

    def test_classify_package_json(self):
        """Test classifying npm package.json."""
        result = classify_dependency_file("package.json")
        assert result is not None
        assert result.ecosystem == "npm"
        assert result.file_type == "manifest"
        assert result.filename == "package.json"

    def test_classify_nested_package_json(self):
        """Test classifying nested npm package.json."""
        result = classify_dependency_file("packages/core/package.json")
        assert result is not None
        assert result.ecosystem == "npm"
        assert result.path == "packages/core/package.json"

    def test_classify_package_lock(self):
        """Test classifying npm package-lock.json."""
        result = classify_dependency_file("package-lock.json")
        assert result is not None
        assert result.ecosystem == "npm"
        assert result.file_type == "lockfile"

    def test_classify_yarn_lock(self):
        """Test classifying yarn.lock."""
        result = classify_dependency_file("yarn.lock")
        assert result is not None
        assert result.ecosystem == "npm"
        assert result.file_type == "lockfile"

    def test_classify_requirements_txt(self):
        """Test classifying requirements.txt."""
        result = classify_dependency_file("requirements.txt")
        assert result is not None
        assert result.ecosystem == "pip"
        assert result.file_type == "manifest"

    def test_classify_go_mod(self):
        """Test classifying go.mod."""
        result = classify_dependency_file("go.mod")
        assert result is not None
        assert result.ecosystem == "go"
        assert result.file_type == "manifest"

    def test_classify_go_sum(self):
        """Test classifying go.sum."""
        result = classify_dependency_file("go.sum")
        assert result is not None
        assert result.ecosystem == "go"
        assert result.file_type == "lockfile"

    def test_classify_cargo_toml(self):
        """Test classifying Cargo.toml."""
        result = classify_dependency_file("Cargo.toml")
        assert result is not None
        assert result.ecosystem == "rust"
        assert result.file_type == "manifest"

    def test_classify_csproj(self):
        """Test classifying .csproj files."""
        result = classify_dependency_file("src/MyProject/MyProject.csproj")
        assert result is not None
        assert result.ecosystem == "nuget"
        assert result.file_type == "manifest"

    def test_classify_pyproject_with_poetry_lock(self):
        """Test classifying pyproject.toml when poetry.lock exists."""
        file_paths = {"pyproject.toml", "poetry.lock", "README.md"}
        result = classify_dependency_file("pyproject.toml", file_paths)
        assert result is not None
        assert result.ecosystem == "poetry"
        assert result.file_type == "manifest"

    def test_classify_nested_pyproject_with_poetry_lock(self):
        """Test classifying nested pyproject.toml with poetry.lock."""
        file_paths = {"packages/lib/pyproject.toml", "packages/lib/poetry.lock"}
        result = classify_dependency_file("packages/lib/pyproject.toml", file_paths)
        assert result is not None
        assert result.ecosystem == "poetry"

    def test_classify_unknown_file(self):
        """Test classifying non-dependency file returns None."""
        result = classify_dependency_file("src/main.py")
        assert result is None

    def test_classify_readme(self):
        """Test that README is not classified as dependency file."""
        result = classify_dependency_file("README.md")
        assert result is None


class TestDetectEcosystems:
    """Tests for detect_ecosystems function."""

    def test_detect_npm_complete(self):
        """Test detecting complete npm ecosystem."""
        files = ["package.json", "package-lock.json", "src/index.js"]
        result = detect_ecosystems(files)

        assert "npm" in result.ecosystems
        assert result.ecosystems["npm"].is_complete
        assert len(result.incomplete_ecosystems) == 0

    def test_detect_npm_incomplete(self):
        """Test detecting incomplete npm ecosystem (no lockfile)."""
        files = ["package.json", "src/index.js"]
        result = detect_ecosystems(files)

        assert "npm" in result.ecosystems
        assert not result.ecosystems["npm"].is_complete
        assert "npm" in result.incomplete_ecosystems

    def test_detect_pip_no_lockfile_expected(self):
        """Test that pip ecosystem is complete without lockfile."""
        files = ["requirements.txt", "src/main.py"]
        result = detect_ecosystems(files)

        assert "pip" in result.ecosystems
        assert result.ecosystems["pip"].is_complete
        assert "pip" not in result.incomplete_ecosystems

    def test_detect_multiple_ecosystems(self):
        """Test detecting multiple ecosystems."""
        files = [
            "package.json",
            "package-lock.json",
            "requirements.txt",
            "go.mod",
            "go.sum",
        ]
        result = detect_ecosystems(files)

        assert len(result.ecosystems) == 3
        assert "npm" in result.ecosystems
        assert "pip" in result.ecosystems
        assert "go" in result.ecosystems

    def test_detect_rust_incomplete(self):
        """Test detecting incomplete Rust ecosystem."""
        files = ["Cargo.toml", "src/lib.rs"]
        result = detect_ecosystems(files)

        assert "rust" in result.ecosystems
        assert not result.ecosystems["rust"].is_complete
        assert "rust" in result.incomplete_ecosystems

    def test_detect_rust_complete(self):
        """Test detecting complete Rust ecosystem."""
        files = ["Cargo.toml", "Cargo.lock", "src/lib.rs"]
        result = detect_ecosystems(files)

        assert "rust" in result.ecosystems
        assert result.ecosystems["rust"].is_complete

    def test_detect_monorepo(self):
        """Test detecting ecosystems in monorepo structure."""
        files = [
            "package.json",
            "yarn.lock",
            "packages/frontend/package.json",
            "packages/backend/package.json",
            "services/api/go.mod",
            "services/api/go.sum",
        ]
        result = detect_ecosystems(files)

        assert "npm" in result.ecosystems
        assert len(result.ecosystems["npm"].manifests) == 3
        assert "go" in result.ecosystems

    def test_dependency_files_list(self):
        """Test that dependency_files list is populated correctly."""
        files = ["package.json", "package-lock.json"]
        result = detect_ecosystems(files)

        assert len(result.dependency_files) == 2
        paths = [df.path for df in result.dependency_files]
        assert "package.json" in paths
        assert "package-lock.json" in paths

    def test_empty_file_list(self):
        """Test detection with empty file list."""
        result = detect_ecosystems([])

        assert len(result.ecosystems) == 0
        assert len(result.dependency_files) == 0
        assert len(result.incomplete_ecosystems) == 0


class TestEcosystemStatus:
    """Tests for EcosystemStatus class."""

    def test_is_complete_with_lockfile(self):
        """Test is_complete when lockfile exists."""
        status = EcosystemStatus(
            manifests=["package.json"],
            lockfiles=["package-lock.json"],
            lockfile_expected=True,
        )
        assert status.is_complete

    def test_is_complete_without_lockfile_expected(self):
        """Test is_complete when lockfile not expected."""
        status = EcosystemStatus(
            manifests=["requirements.txt"],
            lockfiles=[],
            lockfile_expected=False,
        )
        assert status.is_complete

    def test_not_complete_missing_lockfile(self):
        """Test not complete when lockfile expected but missing."""
        status = EcosystemStatus(
            manifests=["Cargo.toml"],
            lockfiles=[],
            lockfile_expected=True,
        )
        assert not status.is_complete

    def test_not_complete_no_manifest(self):
        """Test not complete when no manifest."""
        status = EcosystemStatus(
            manifests=[],
            lockfiles=["package-lock.json"],
            lockfile_expected=True,
        )
        assert not status.is_complete


class TestEcosystemDetectionResult:
    """Tests for EcosystemDetectionResult class."""

    def test_get_warnings(self):
        """Test warning message generation."""
        result = EcosystemDetectionResult()
        result.ecosystems["rust"] = EcosystemStatus(
            manifests=["Cargo.toml"],
            lockfiles=[],
            lockfile_expected=True,
        )
        result.ecosystems["npm"] = EcosystemStatus(
            manifests=["package.json"],
            lockfiles=["yarn.lock"],
            lockfile_expected=True,
        )

        warnings = result.get_warnings()
        assert len(warnings) == 1
        assert "rust" in warnings[0]
        assert "Cargo.toml" in warnings[0]
        assert "Trivy analysis may be incomplete" in warnings[0]

    def test_detected_ecosystem_names(self):
        """Test getting list of detected ecosystem names."""
        result = EcosystemDetectionResult()
        result.ecosystems["npm"] = EcosystemStatus(manifests=["package.json"])
        result.ecosystems["go"] = EcosystemStatus(manifests=["go.mod"])

        names = result.detected_ecosystem_names
        assert "npm" in names
        assert "go" in names


class TestGetEcosystemSummary:
    """Tests for get_ecosystem_summary function."""

    def test_summary_counts(self):
        """Test that summary counts total files per ecosystem."""
        files = [
            "package.json",
            "package-lock.json",
            "packages/a/package.json",
            "go.mod",
            "go.sum",
        ]
        result = detect_ecosystems(files)
        summary = get_ecosystem_summary(result)

        assert summary["npm"] == 3  # 2 manifests + 1 lockfile
        assert summary["go"] == 2  # 1 manifest + 1 lockfile


class TestFormatEcosystemCompleteness:
    """Tests for format_ecosystem_completeness function."""

    def test_format_complete_ecosystem(self):
        """Test formatting complete ecosystem."""
        files = ["package.json", "package-lock.json"]
        result = detect_ecosystems(files)
        formatted = format_ecosystem_completeness(result)

        assert len(formatted["dependency_files"]) == 2
        assert formatted["ecosystems"]["npm"]["is_complete"] is True
        assert len(formatted["warnings"]) == 0

    def test_format_incomplete_ecosystem(self):
        """Test formatting incomplete ecosystem."""
        files = ["Cargo.toml"]
        result = detect_ecosystems(files)
        formatted = format_ecosystem_completeness(result)

        assert formatted["ecosystems"]["rust"]["is_complete"] is False
        assert len(formatted["warnings"]) == 1
        assert "rust" in formatted["warnings"][0]

    def test_format_dependency_file_structure(self):
        """Test dependency file structure in formatted output."""
        files = ["package.json"]
        result = detect_ecosystems(files)
        formatted = format_ecosystem_completeness(result)

        dep_file = formatted["dependency_files"][0]
        assert dep_file["path"] == "package.json"
        assert dep_file["ecosystem"] == "npm"
        assert dep_file["type"] == "manifest"
