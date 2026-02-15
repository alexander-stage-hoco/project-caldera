"""Root conftest.py — per-tool sys.path / sys.modules isolation.

When ``pytest src/`` runs, tests from 18+ tools execute in the same process.
Many tools have identically-named top-level modules (``checks``, ``evaluate``,
``analyze``, …) under their ``scripts/`` directories.  Without isolation,
Python caches the first tool's ``checks`` module and returns it for every
subsequent tool.

This conftest wraps ``Module.collect()`` to flush and reimport at collection
time, caches each tool's module snapshot, and restores it at execution time
via ``pytest_runtest_setup``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

import _pytest.config
import _pytest.python

# ---------------------------------------------------------------------------
# Module names that are local to individual tools and must be flushed when
# the test runner crosses a tool boundary.  Add new names here if a tool
# introduces a top-level package that collides with another tool.
# ---------------------------------------------------------------------------
_TOOL_LOCAL_MODULES: set[str] = {
    "checks",
    "evaluation",
    "evaluate",
    "analyze",
    "build_repos",
    "transform",
    "validate",
    "scripts",
    # Tool-specific top-level modules
    "security_analyzer",
    "roslyn_analyzer",
    "license_analyzer",
    "directory_analyzer",
    "secret_analyzer",
    "blame_analyzer",
    "function_analyzer",
    # Additional tool modules that may collide
    "api",
    "docker_lifecycle",
    "config_loader",
    "classifier",
    "tree_walker",
    # architecture-review modules that shadow tool modules
    "models",
}

_PROJECT_ROOT = Path(__file__).resolve().parent
_TOOLS_ROOT = _PROJECT_ROOT / "src" / "tools"

# Track which tool owns the currently-running test/collector.
_current_tool: str | None = None

# Cache tool module snapshots so we can restore exact module objects.
# Key: tool name → dict of {module_name: module_object}.
_tool_module_cache: dict[str, dict[str, ModuleType]] = {}


def _tool_from_path(fspath: Path) -> str | None:
    """Return the tool name if *fspath* lives under ``src/tools/<name>/``."""
    try:
        resolved = fspath if fspath.is_absolute() else fspath.resolve()
        rel = resolved.relative_to(_TOOLS_ROOT)
    except (ValueError, OSError):
        return None
    return rel.parts[0] if rel.parts else None


def _get_tool_modules() -> dict[str, ModuleType]:
    """Return a snapshot of all tool-local modules currently in sys.modules."""
    return {
        name: mod
        for name, mod in sys.modules.items()
        if name.split(".")[0] in _TOOL_LOCAL_MODULES
    }


def _flush_tool_modules() -> None:
    """Remove cached tool-local modules from ``sys.modules``."""
    to_delete = [
        name
        for name in sys.modules
        if name.split(".")[0] in _TOOL_LOCAL_MODULES
    ]
    for name in to_delete:
        del sys.modules[name]


def _restore_tool_modules(snapshot: dict[str, ModuleType]) -> None:
    """Restore a tool module snapshot into ``sys.modules``.

    This replaces (not merges) — first flush, then restore.  This ensures
    the exact same module objects are in sys.modules, preserving identity
    for ``unittest.mock.patch`` targets.
    """
    _flush_tool_modules()
    sys.modules.update(snapshot)


def _reorder_sys_path(tool_dir: Path) -> None:
    """Ensure *tool_dir* and its ``scripts/`` sub-directory appear first.

    Also remove other tools' paths so stale entries don't shadow the
    current tool.
    """
    scripts_dir = tool_dir / "scripts"
    # Remove ALL tool paths from sys.path (not just current tool's).
    to_remove = [p for p in sys.path if _is_tool_path(p)]
    for p in to_remove:
        while p in sys.path:
            sys.path.remove(p)
    # Insert current tool paths at the beginning.
    if scripts_dir.is_dir():
        sys.path.insert(0, str(scripts_dir))
    sys.path.insert(0, str(tool_dir))


def _is_tool_path(p: str) -> bool:
    """Check if a sys.path entry belongs to any tool."""
    try:
        Path(p).relative_to(_TOOLS_ROOT)
        return True
    except ValueError:
        return False


def _switch_tool_for_collection(tool: str) -> None:
    """Flush + reimport isolation for collection phase."""
    global _current_tool
    if tool != _current_tool:
        # Save outgoing tool's modules before flushing.
        if _current_tool is not None:
            _tool_module_cache[_current_tool] = _get_tool_modules()
        _flush_tool_modules()
        _reorder_sys_path(_TOOLS_ROOT / tool)
        # If we've seen this tool before, restore its cached modules.
        if tool in _tool_module_cache:
            sys.modules.update(_tool_module_cache[tool])
        _current_tool = tool


def _switch_tool_for_execution(tool: str) -> None:
    """Restore cached module snapshot for execution phase.

    This preserves module object identity so ``mock.patch`` targets
    the same objects that test functions reference.
    """
    global _current_tool
    if tool != _current_tool:
        _reorder_sys_path(_TOOLS_ROOT / tool)
        if tool in _tool_module_cache:
            _restore_tool_modules(_tool_module_cache[tool])
        else:
            _flush_tool_modules()
        _current_tool = tool


# ---------------------------------------------------------------------------
# Monkeypatch conftest loading — ensures isolation *before* each tool's
# conftest.py is imported (needed for conftest files that import tool
# modules at load time, e.g. layout-scanner importing scripts.classifier).
# ---------------------------------------------------------------------------
_original_importconftest = _pytest.config.PytestPluginManager._importconftest


def _patched_importconftest(self, conftestpath, *args, **kwargs):
    tool = _tool_from_path(Path(str(conftestpath)))
    if tool is not None:
        _switch_tool_for_collection(tool)
    return _original_importconftest(self, conftestpath, *args, **kwargs)


_pytest.config.PytestPluginManager._importconftest = _patched_importconftest


# ---------------------------------------------------------------------------
# Monkeypatch Module.collect() — fires immediately before each test file is
# imported, ensuring the correct tool's modules are in sys.modules.
# ---------------------------------------------------------------------------
_original_module_collect = _pytest.python.Module.collect


def _patched_module_collect(self):
    fspath = getattr(self, "fspath", None) or getattr(self, "path", None)
    if fspath is not None:
        tool = _tool_from_path(Path(str(fspath)))
        if tool is not None:
            _switch_tool_for_collection(tool)
    result = _original_module_collect(self)
    # Snapshot after collection so we capture all modules loaded by this
    # tool's test files (including transitive imports).
    if fspath is not None:
        tool = _tool_from_path(Path(str(fspath)))
        if tool is not None:
            _tool_module_cache[tool] = _get_tool_modules()
    return result


_pytest.python.Module.collect = _patched_module_collect


# ---------------------------------------------------------------------------
# Pytest hook — restore the correct tool's modules at execution time.
# ---------------------------------------------------------------------------

def pytest_runtest_setup(item) -> None:
    """Restore the correct tool's module snapshot before each test."""
    fspath = getattr(item, "fspath", None) or getattr(item, "path", None)
    if fspath is None:
        return
    tool = _tool_from_path(Path(str(fspath)))
    if tool is not None:
        _switch_tool_for_execution(tool)
