"""Module B: Component tree extraction."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

from .client import SonarQubeClient

logger = structlog.get_logger(__name__)


class ComponentQualifier(Enum):
    """SonarQube component qualifiers."""

    PROJECT = "TRK"  # Project/root
    DIRECTORY = "DIR"  # Directory
    FILE = "FIL"  # File
    UNIT_TEST_FILE = "UTS"  # Unit test file
    MODULE = "BRC"  # Module (subproject)

    @classmethod
    def from_string(cls, value: str) -> "ComponentQualifier":
        """Convert string to qualifier enum."""
        for member in cls:
            if member.value == value:
                return member
        return cls.FILE  # Default to file


@dataclass
class Component:
    """Represents a SonarQube component (file, directory, or project)."""

    key: str
    name: str
    qualifier: ComponentQualifier
    path: str | None = None
    language: str | None = None
    measures: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api_response(cls, data: dict) -> "Component":
        """Create Component from API response."""
        return cls(
            key=data.get("key", ""),
            name=data.get("name", ""),
            qualifier=ComponentQualifier.from_string(data.get("qualifier", "FIL")),
            path=data.get("path"),
            language=data.get("language"),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        result = {
            "key": self.key,
            "name": self.name,
            "qualifier": self.qualifier.value,
        }
        if self.path:
            result["path"] = self.path
        if self.language:
            result["language"] = self.language
        if self.measures:
            result["measures"] = self.measures
        return result


@dataclass
class ComponentTree:
    """Hierarchical component tree for a project."""

    root: Component
    by_key: dict[str, Component] = field(default_factory=dict)
    children: dict[str, list[str]] = field(default_factory=dict)  # parent_key -> [child_keys]

    @property
    def files(self) -> list[Component]:
        """Get all file components."""
        return [c for c in self.by_key.values() if c.qualifier == ComponentQualifier.FILE]

    @property
    def directories(self) -> list[Component]:
        """Get all directory components."""
        return [c for c in self.by_key.values() if c.qualifier == ComponentQualifier.DIRECTORY]

    def get_children(self, parent_key: str) -> list[Component]:
        """Get child components for a parent."""
        child_keys = self.children.get(parent_key, [])
        return [self.by_key[k] for k in child_keys if k in self.by_key]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "root_key": self.root.key,
            "by_key": {k: v.to_dict() for k, v in self.by_key.items()},
            "children": self.children,
        }


def get_component(client: SonarQubeClient, component_key: str) -> Component:
    """Get a single component by key.

    Args:
        client: SonarQube API client
        component_key: Component key

    Returns:
        Component object
    """
    data = client.get("/api/components/show", {"component": component_key})
    return Component.from_api_response(data.get("component", {}))


def get_component_tree(
    client: SonarQubeClient,
    project_key: str,
    qualifiers: list[ComponentQualifier] | None = None,
    strategy: str = "all",
) -> ComponentTree:
    """Extract the complete component tree for a project.

    Args:
        client: SonarQube API client
        project_key: Project key
        qualifiers: Component types to include (default: all)
        strategy: Tree strategy: "all" (flat), "children" (direct children only), "leaves" (files only)

    Returns:
        ComponentTree with all components
    """
    logger.info("Extracting component tree", project_key=project_key)

    # Get root component
    root = get_component(client, project_key)

    # Build params
    params = {"component": project_key, "strategy": strategy}
    if qualifiers:
        params["qualifiers"] = ",".join(q.value for q in qualifiers)

    # Fetch all components
    by_key: dict[str, Component] = {root.key: root}
    children: dict[str, list[str]] = {}

    for item in client.get_paged("/api/components/tree", params, "components"):
        component = Component.from_api_response(item)
        by_key[component.key] = component

        # Build parent-child relationships from paths
        if component.path:
            parent_path = "/".join(component.path.split("/")[:-1])
            # Find parent by matching path
            for key, comp in by_key.items():
                if comp.path == parent_path or (not parent_path and key == root.key):
                    if key not in children:
                        children[key] = []
                    children[key].append(component.key)
                    break

    # Backfill directories based on file paths when SonarQube omits DIR nodes
    if not any(c.qualifier == ComponentQualifier.DIRECTORY for c in by_key.values()):
        root_path = root.path or ""
        root_dir_key = f"{root.key}:/"
        if root_dir_key not in by_key:
            by_key[root_dir_key] = Component(
                key=root_dir_key,
                name="/",
                qualifier=ComponentQualifier.DIRECTORY,
                path="",  # Empty string for root-level component (not absolute "/")
            )
        children.setdefault(root.key, [])
        if root_dir_key not in children[root.key]:
            children[root.key].append(root_dir_key)

        for comp in list(by_key.values()):
            if comp.qualifier != ComponentQualifier.FILE or not comp.path:
                continue
            parts = comp.path.split("/")[:-1]
            parent_key = root.key
            if not parts:
                children.setdefault(root_dir_key, [])
                if comp.key not in children[root_dir_key]:
                    children[root_dir_key].append(comp.key)
                continue
            for part in parts:
                dir_key = f"{root.key}:{part}" if parent_key == root.key else f"{parent_key}/{part}"
                if dir_key not in by_key:
                    parent_path = by_key[parent_key].path or root_path
                    by_key[dir_key] = Component(
                        key=dir_key,
                        name=part,
                        qualifier=ComponentQualifier.DIRECTORY,
                        path=part if not parent_path else f"{parent_path}/{part}",
                    )
                children.setdefault(parent_key, [])
                if dir_key not in children[parent_key]:
                    children[parent_key].append(dir_key)
                parent_key = dir_key
            children.setdefault(parent_key, [])
            if comp.key not in children[parent_key]:
                children[parent_key].append(comp.key)

    logger.info(
        "Component tree extracted",
        total_components=len(by_key),
        files=sum(1 for c in by_key.values() if c.qualifier == ComponentQualifier.FILE),
        directories=sum(1 for c in by_key.values() if c.qualifier == ComponentQualifier.DIRECTORY),
    )

    return ComponentTree(root=root, by_key=by_key, children=children)


def get_file_components(client: SonarQubeClient, project_key: str) -> list[Component]:
    """Get only file components for a project.

    Args:
        client: SonarQube API client
        project_key: Project key

    Returns:
        List of file components
    """
    params = {
        "component": project_key,
        "qualifiers": "FIL,UTS",
        "strategy": "leaves",
    }

    files = []
    for item in client.get_paged("/api/components/tree", params, "components"):
        files.append(Component.from_api_response(item))

    logger.info("Extracted file components", count=len(files))
    return files


def get_directory_components(client: SonarQubeClient, project_key: str) -> list[Component]:
    """Get only directory components for a project.

    Args:
        client: SonarQube API client
        project_key: Project key

    Returns:
        List of directory components
    """
    params = {
        "component": project_key,
        "qualifiers": "DIR",
    }

    dirs = []
    for item in client.get_paged("/api/components/tree", params, "components"):
        dirs.append(Component.from_api_response(item))

    logger.info("Extracted directory components", count=len(dirs))
    return dirs


def get_languages_in_project(client: SonarQubeClient, project_key: str) -> dict[str, int]:
    """Get language distribution for a project.

    Args:
        client: SonarQube API client
        project_key: Project key

    Returns:
        Dictionary mapping language code to file count
    """
    files = get_file_components(client, project_key)

    languages: dict[str, int] = {}
    for f in files:
        if f.language:
            languages[f.language] = languages.get(f.language, 0) + 1

    return languages
