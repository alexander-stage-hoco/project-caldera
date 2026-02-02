"""
Ecosystem Detector - Shared module for detecting package ecosystems in repositories.

Identifies dependency files (manifests and lockfiles) and determines ecosystem
completeness for vulnerability scanning tools like Trivy.

Supported ecosystems:
- npm (package.json + package-lock.json/yarn.lock/pnpm-lock.yaml)
- pip (requirements.txt)
- poetry (pyproject.toml + poetry.lock)
- pipenv (Pipfile + Pipfile.lock)
- go (go.mod + go.sum)
- rust (Cargo.toml + Cargo.lock)
- ruby (Gemfile + Gemfile.lock)
- maven (pom.xml)
- gradle (build.gradle + gradle.lockfile)
- nuget (*.csproj/packages.config + packages.lock.json)
- composer (composer.json + composer.lock)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


DependencyFileType = Literal["manifest", "lockfile"]


@dataclass(frozen=True)
class EcosystemPattern:
    """Definition of an ecosystem's manifest and lockfile patterns."""

    name: str
    manifests: tuple[str, ...]
    lockfiles: tuple[str, ...]
    # Some manifests are patterns (e.g., *.csproj)
    manifest_patterns: tuple[str, ...] = ()
    # Whether a lockfile is typically expected/required
    lockfile_expected: bool = True


# Ecosystem pattern definitions
ECOSYSTEM_PATTERNS: dict[str, EcosystemPattern] = {
    "npm": EcosystemPattern(
        name="npm",
        manifests=("package.json",),
        lockfiles=("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb"),
    ),
    "pip": EcosystemPattern(
        name="pip",
        manifests=("requirements.txt", "requirements-dev.txt", "requirements-test.txt"),
        lockfiles=(),  # pip doesn't have a standard lockfile
        lockfile_expected=False,
    ),
    "poetry": EcosystemPattern(
        name="poetry",
        manifests=("pyproject.toml",),
        lockfiles=("poetry.lock",),
    ),
    "pipenv": EcosystemPattern(
        name="pipenv",
        manifests=("Pipfile",),
        lockfiles=("Pipfile.lock",),
    ),
    "go": EcosystemPattern(
        name="go",
        manifests=("go.mod",),
        lockfiles=("go.sum",),
    ),
    "rust": EcosystemPattern(
        name="rust",
        manifests=("Cargo.toml",),
        lockfiles=("Cargo.lock",),
    ),
    "ruby": EcosystemPattern(
        name="ruby",
        manifests=("Gemfile",),
        lockfiles=("Gemfile.lock",),
    ),
    "maven": EcosystemPattern(
        name="maven",
        manifests=("pom.xml",),
        lockfiles=(),  # Maven doesn't have a standard lockfile
        lockfile_expected=False,
    ),
    "gradle": EcosystemPattern(
        name="gradle",
        manifests=("build.gradle", "build.gradle.kts"),
        lockfiles=("gradle.lockfile",),
    ),
    "nuget": EcosystemPattern(
        name="nuget",
        manifests=("packages.config",),
        lockfiles=("packages.lock.json",),
        manifest_patterns=("*.csproj", "*.fsproj", "*.vbproj"),
    ),
    "composer": EcosystemPattern(
        name="composer",
        manifests=("composer.json",),
        lockfiles=("composer.lock",),
    ),
}


@dataclass(frozen=True)
class DependencyFile:
    """A detected dependency file."""

    path: str  # Repo-relative path
    ecosystem: str
    file_type: DependencyFileType
    filename: str


@dataclass
class EcosystemStatus:
    """Status of a detected ecosystem."""

    manifests: list[str] = field(default_factory=list)
    lockfiles: list[str] = field(default_factory=list)
    lockfile_expected: bool = True

    @property
    def is_complete(self) -> bool:
        """Check if the ecosystem has all expected files.

        An ecosystem is complete if:
        - It has at least one manifest AND
        - Either lockfiles are not expected, OR it has at least one lockfile
        """
        if not self.manifests:
            return False
        if not self.lockfile_expected:
            return True
        return len(self.lockfiles) > 0


@dataclass
class EcosystemDetectionResult:
    """Result of ecosystem detection across a repository."""

    dependency_files: list[DependencyFile] = field(default_factory=list)
    ecosystems: dict[str, EcosystemStatus] = field(default_factory=dict)

    @property
    def incomplete_ecosystems(self) -> list[str]:
        """List of ecosystems that have manifests but no lockfiles (when expected)."""
        return [
            name
            for name, status in self.ecosystems.items()
            if status.manifests and status.lockfile_expected and not status.lockfiles
        ]

    @property
    def detected_ecosystem_names(self) -> list[str]:
        """List of all detected ecosystem names."""
        return list(self.ecosystems.keys())

    def get_warnings(self) -> list[str]:
        """Generate warning messages for incomplete ecosystems."""
        warnings = []
        for ecosystem in self.incomplete_ecosystems:
            status = self.ecosystems[ecosystem]
            manifest_list = ", ".join(status.manifests[:3])
            if len(status.manifests) > 3:
                manifest_list += f" (+{len(status.manifests) - 3} more)"
            warnings.append(
                f"Ecosystem '{ecosystem}' has manifests ({manifest_list}) but no lockfile. "
                f"Trivy analysis may be incomplete."
            )
        return warnings


def _matches_pattern(filename: str, pattern: str) -> bool:
    """Check if a filename matches a glob-like pattern."""
    if pattern.startswith("*"):
        return filename.endswith(pattern[1:])
    return filename == pattern


def _is_pyproject_poetry(file_path: str, file_paths: set[str]) -> bool:
    """Check if pyproject.toml is a Poetry project.

    A pyproject.toml is considered a Poetry project if:
    - poetry.lock exists in the same directory, OR
    - We assume it could be poetry (conservative approach for detection)

    For more accurate detection, we'd need to read the file content.
    """
    # Check if poetry.lock exists alongside pyproject.toml
    directory = str(Path(file_path).parent)
    if directory == ".":
        return "poetry.lock" in file_paths
    return f"{directory}/poetry.lock" in file_paths


def classify_dependency_file(
    file_path: str, file_paths: set[str] | None = None
) -> DependencyFile | None:
    """Classify a single file as a dependency file if it matches known patterns.

    Args:
        file_path: Repo-relative path to the file
        file_paths: Optional set of all file paths for context (e.g., to detect poetry)

    Returns:
        DependencyFile if the file is a known dependency file, None otherwise
    """
    filename = Path(file_path).name
    file_paths_set = file_paths or set()

    for ecosystem_name, pattern in ECOSYSTEM_PATTERNS.items():
        # Check exact manifest matches
        if filename in pattern.manifests:
            # Special case: pyproject.toml could be poetry or just a Python project
            if filename == "pyproject.toml":
                if _is_pyproject_poetry(file_path, file_paths_set):
                    return DependencyFile(
                        path=file_path,
                        ecosystem="poetry",
                        file_type="manifest",
                        filename=filename,
                    )
                # If not clearly poetry, still report as poetry manifest
                # (conservative - let trivy figure it out)
                return DependencyFile(
                    path=file_path,
                    ecosystem="poetry",
                    file_type="manifest",
                    filename=filename,
                )
            return DependencyFile(
                path=file_path,
                ecosystem=ecosystem_name,
                file_type="manifest",
                filename=filename,
            )

        # Check manifest patterns (e.g., *.csproj)
        for manifest_pattern in pattern.manifest_patterns:
            if _matches_pattern(filename, manifest_pattern):
                return DependencyFile(
                    path=file_path,
                    ecosystem=ecosystem_name,
                    file_type="manifest",
                    filename=filename,
                )

        # Check exact lockfile matches
        if filename in pattern.lockfiles:
            return DependencyFile(
                path=file_path,
                ecosystem=ecosystem_name,
                file_type="lockfile",
                filename=filename,
            )

    return None


def detect_ecosystems(file_paths: list[str]) -> EcosystemDetectionResult:
    """Detect all package ecosystems present in a repository.

    Args:
        file_paths: List of repo-relative file paths

    Returns:
        EcosystemDetectionResult with detected dependency files and ecosystem status
    """
    result = EcosystemDetectionResult()
    file_paths_set = set(file_paths)

    for file_path in file_paths:
        dep_file = classify_dependency_file(file_path, file_paths_set)
        if dep_file:
            result.dependency_files.append(dep_file)

            # Update ecosystem status
            if dep_file.ecosystem not in result.ecosystems:
                pattern = ECOSYSTEM_PATTERNS.get(dep_file.ecosystem)
                result.ecosystems[dep_file.ecosystem] = EcosystemStatus(
                    lockfile_expected=pattern.lockfile_expected if pattern else True
                )

            status = result.ecosystems[dep_file.ecosystem]
            if dep_file.file_type == "manifest":
                status.manifests.append(dep_file.path)
            else:
                status.lockfiles.append(dep_file.path)

    return result


def detect_ecosystems_from_directory(repo_path: Path) -> EcosystemDetectionResult:
    """Detect ecosystems by walking a directory.

    Args:
        repo_path: Path to repository root

    Returns:
        EcosystemDetectionResult with detected dependency files and ecosystem status
    """
    file_paths: list[str] = []
    repo_path = repo_path.resolve()

    for item in repo_path.rglob("*"):
        if item.is_file():
            try:
                rel_path = item.relative_to(repo_path).as_posix()
                # Skip common non-source directories
                if any(
                    part in rel_path.split("/")
                    for part in ("node_modules", ".git", "vendor", "__pycache__")
                ):
                    continue
                file_paths.append(rel_path)
            except ValueError:
                continue

    return detect_ecosystems(file_paths)


def get_ecosystem_summary(result: EcosystemDetectionResult) -> dict[str, int]:
    """Get a summary of detected ecosystems with file counts.

    Args:
        result: EcosystemDetectionResult from detection

    Returns:
        Dictionary mapping ecosystem name to total dependency file count
    """
    summary: dict[str, int] = {}
    for ecosystem_name, status in result.ecosystems.items():
        summary[ecosystem_name] = len(status.manifests) + len(status.lockfiles)
    return summary


def format_ecosystem_completeness(result: EcosystemDetectionResult) -> dict:
    """Format ecosystem detection result for JSON output (Trivy format).

    Args:
        result: EcosystemDetectionResult from detection

    Returns:
        Dictionary suitable for JSON serialization in Trivy output
    """
    dependency_files = [
        {
            "path": df.path,
            "ecosystem": df.ecosystem,
            "type": df.file_type,
        }
        for df in result.dependency_files
    ]

    ecosystems = {
        name: {
            "manifests": status.manifests,
            "lockfiles": status.lockfiles,
            "is_complete": status.is_complete,
        }
        for name, status in result.ecosystems.items()
    }

    return {
        "dependency_files": dependency_files,
        "ecosystems": ecosystems,
        "warnings": result.get_warnings(),
    }
