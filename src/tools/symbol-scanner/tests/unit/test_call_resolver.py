"""Unit tests for CallResolver."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from extractors.base import ExtractedCall, ExtractedImport, ExtractedSymbol
from extractors.call_resolver import (
    BUILTIN_FUNCTIONS,
    STDLIB_MODULES,
    CallResolver,
)


class TestCallResolver:
    """Tests for CallResolver."""

    @pytest.fixture
    def simple_symbols(self):
        """Symbols from a simple two-file repo."""
        return [
            ExtractedSymbol(
                path="utils.py",
                symbol_name="validate",
                symbol_type="function",
                line_start=1,
                line_end=3,
                is_exported=True,
                parameters=1,
                parent_symbol=None,
                docstring=None,
            ),
            ExtractedSymbol(
                path="utils.py",
                symbol_name="sanitize",
                symbol_type="function",
                line_start=5,
                line_end=7,
                is_exported=True,
                parameters=1,
                parent_symbol=None,
                docstring=None,
            ),
            ExtractedSymbol(
                path="main.py",
                symbol_name="process",
                symbol_type="function",
                line_start=4,
                line_end=8,
                is_exported=True,
                parameters=1,
                parent_symbol=None,
                docstring=None,
            ),
        ]

    @pytest.fixture
    def simple_imports(self):
        """Imports for the simple two-file repo."""
        return [
            ExtractedImport(
                file="main.py",
                imported_path="utils",
                imported_symbols="validate,sanitize",
                import_type="static",
                line_number=1,
            ),
        ]

    def test_resolve_direct_import(self, simple_symbols, simple_imports, temp_dir):
        """Test resolution of from x import y style imports."""
        # Create the files so the resolver can verify they exist
        (temp_dir / "utils.py").write_text("")
        (temp_dir / "main.py").write_text("")

        resolver = CallResolver(temp_dir, simple_symbols, simple_imports)

        calls = [
            ExtractedCall(
                caller_file="main.py",
                caller_symbol="process",
                callee_symbol="validate",
                callee_file=None,
                line_number=5,
                call_type="direct",
            ),
        ]

        resolved = resolver.resolve(calls)

        assert len(resolved) == 1
        assert resolved[0].callee_file == "utils.py"
        assert resolver.stats.resolved_cross_file == 1

    def test_resolve_module_import(self, temp_dir):
        """Test resolution of import x + x.func() style calls."""
        (temp_dir / "utils.py").write_text("")
        (temp_dir / "main.py").write_text("")

        symbols = [
            ExtractedSymbol(
                path="utils.py",
                symbol_name="validate",
                symbol_type="function",
                line_start=1,
                line_end=3,
                is_exported=True,
                parameters=1,
                parent_symbol=None,
                docstring=None,
            ),
            ExtractedSymbol(
                path="main.py",
                symbol_name="process",
                symbol_type="function",
                line_start=3,
                line_end=5,
                is_exported=True,
                parameters=0,
                parent_symbol=None,
                docstring=None,
            ),
        ]

        imports = [
            ExtractedImport(
                file="main.py",
                imported_path="utils",
                imported_symbols=None,  # Full module import
                import_type="static",
                line_number=1,
            ),
        ]

        resolver = CallResolver(temp_dir, symbols, imports)

        # Note: Dynamic calls like utils.validate() won't resolve the function
        # because we store the module alias, not individual function bindings
        # This is expected behavior - we'd need type inference to resolve this

    def test_resolve_relative_import(self, temp_dir):
        """Test resolution of relative imports (from . import helper)."""
        pkg_dir = temp_dir / "pkg"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "helper.py").write_text("")
        (pkg_dir / "main.py").write_text("")

        symbols = [
            ExtractedSymbol(
                path="pkg/helper.py",
                symbol_name="help_func",
                symbol_type="function",
                line_start=1,
                line_end=2,
                is_exported=True,
                parameters=0,
                parent_symbol=None,
                docstring=None,
            ),
            ExtractedSymbol(
                path="pkg/main.py",
                symbol_name="main",
                symbol_type="function",
                line_start=3,
                line_end=5,
                is_exported=True,
                parameters=0,
                parent_symbol=None,
                docstring=None,
            ),
        ]

        imports = [
            ExtractedImport(
                file="pkg/main.py",
                imported_path=".helper",
                imported_symbols="help_func",
                import_type="static",
                line_number=1,
            ),
        ]

        resolver = CallResolver(temp_dir, symbols, imports)

        calls = [
            ExtractedCall(
                caller_file="pkg/main.py",
                caller_symbol="main",
                callee_symbol="help_func",
                callee_file=None,
                line_number=4,
                call_type="direct",
            ),
        ]

        resolved = resolver.resolve(calls)

        assert len(resolved) == 1
        assert resolved[0].callee_file == "pkg/helper.py"

    def test_stdlib_unresolved(self, temp_dir):
        """Test that stdlib module calls remain unresolved."""
        (temp_dir / "main.py").write_text("")

        symbols = [
            ExtractedSymbol(
                path="main.py",
                symbol_name="main",
                symbol_type="function",
                line_start=3,
                line_end=5,
                is_exported=True,
                parameters=0,
                parent_symbol=None,
                docstring=None,
            ),
        ]

        imports = [
            ExtractedImport(
                file="main.py",
                imported_path="json",
                imported_symbols="loads",
                import_type="static",
                line_number=1,
            ),
        ]

        resolver = CallResolver(temp_dir, symbols, imports)

        calls = [
            ExtractedCall(
                caller_file="main.py",
                caller_symbol="main",
                callee_symbol="loads",
                callee_file=None,
                line_number=4,
                call_type="direct",
            ),
        ]

        resolved = resolver.resolve(calls)

        assert len(resolved) == 1
        assert resolved[0].callee_file is None
        # loads imported from json (stdlib) should remain unresolved
        assert resolver.stats.unresolved_external == 1

    def test_builtin_unresolved(self, temp_dir):
        """Test that builtin function calls remain unresolved."""
        (temp_dir / "main.py").write_text("")

        symbols = [
            ExtractedSymbol(
                path="main.py",
                symbol_name="main",
                symbol_type="function",
                line_start=1,
                line_end=3,
                is_exported=True,
                parameters=0,
                parent_symbol=None,
                docstring=None,
            ),
        ]

        resolver = CallResolver(temp_dir, symbols, [])

        calls = [
            ExtractedCall(
                caller_file="main.py",
                caller_symbol="main",
                callee_symbol="print",
                callee_file=None,
                line_number=2,
                call_type="direct",
            ),
            ExtractedCall(
                caller_file="main.py",
                caller_symbol="main",
                callee_symbol="len",
                callee_file=None,
                line_number=2,
                call_type="direct",
            ),
        ]

        resolved = resolver.resolve(calls)

        assert len(resolved) == 2
        assert resolved[0].callee_file is None
        assert resolved[1].callee_file is None
        assert resolver.stats.unresolved_builtin == 2

    def test_same_file_resolution(self, temp_dir):
        """Test that calls to local functions resolve to the same file."""
        (temp_dir / "main.py").write_text("")

        symbols = [
            ExtractedSymbol(
                path="main.py",
                symbol_name="helper",
                symbol_type="function",
                line_start=1,
                line_end=2,
                is_exported=True,
                parameters=0,
                parent_symbol=None,
                docstring=None,
            ),
            ExtractedSymbol(
                path="main.py",
                symbol_name="main",
                symbol_type="function",
                line_start=4,
                line_end=6,
                is_exported=True,
                parameters=0,
                parent_symbol=None,
                docstring=None,
            ),
        ]

        resolver = CallResolver(temp_dir, symbols, [])

        calls = [
            ExtractedCall(
                caller_file="main.py",
                caller_symbol="main",
                callee_symbol="helper",
                callee_file=None,
                line_number=5,
                call_type="direct",
            ),
        ]

        resolved = resolver.resolve(calls)

        assert len(resolved) == 1
        assert resolved[0].callee_file == "main.py"
        assert resolver.stats.resolved_same_file == 1

    def test_star_import_resolution(self, temp_dir):
        """Test resolution through star imports (from x import *)."""
        (temp_dir / "utils.py").write_text("")
        (temp_dir / "main.py").write_text("")

        symbols = [
            ExtractedSymbol(
                path="utils.py",
                symbol_name="validate",
                symbol_type="function",
                line_start=1,
                line_end=2,
                is_exported=True,
                parameters=1,
                parent_symbol=None,
                docstring=None,
            ),
            ExtractedSymbol(
                path="main.py",
                symbol_name="main",
                symbol_type="function",
                line_start=3,
                line_end=5,
                is_exported=True,
                parameters=0,
                parent_symbol=None,
                docstring=None,
            ),
        ]

        imports = [
            ExtractedImport(
                file="main.py",
                imported_path="utils",
                imported_symbols="*",
                import_type="static",
                line_number=1,
            ),
        ]

        resolver = CallResolver(temp_dir, symbols, imports)

        calls = [
            ExtractedCall(
                caller_file="main.py",
                caller_symbol="main",
                callee_symbol="validate",
                callee_file=None,
                line_number=4,
                call_type="direct",
            ),
        ]

        resolved = resolver.resolve(calls)

        assert len(resolved) == 1
        assert resolved[0].callee_file == "utils.py"
        assert resolver.stats.resolved_cross_file == 1

    def test_aliased_import_resolution(self, temp_dir):
        """Test resolution of aliased imports (from x import foo as f)."""
        (temp_dir / "utils.py").write_text("")
        (temp_dir / "main.py").write_text("")

        symbols = [
            ExtractedSymbol(
                path="utils.py",
                symbol_name="validate",
                symbol_type="function",
                line_start=1,
                line_end=2,
                is_exported=True,
                parameters=1,
                parent_symbol=None,
                docstring=None,
            ),
            ExtractedSymbol(
                path="main.py",
                symbol_name="main",
                symbol_type="function",
                line_start=3,
                line_end=5,
                is_exported=True,
                parameters=0,
                parent_symbol=None,
                docstring=None,
            ),
        ]

        imports = [
            ExtractedImport(
                file="main.py",
                imported_path="utils",
                imported_symbols="validate as v",
                import_type="static",
                line_number=1,
            ),
        ]

        resolver = CallResolver(temp_dir, symbols, imports)

        calls = [
            ExtractedCall(
                caller_file="main.py",
                caller_symbol="main",
                callee_symbol="v",  # Using the alias
                callee_file=None,
                line_number=4,
                call_type="direct",
            ),
        ]

        resolved = resolver.resolve(calls)

        assert len(resolved) == 1
        assert resolved[0].callee_file == "utils.py"
        assert resolver.stats.resolved_cross_file == 1

    def test_dynamic_call_unresolved(self, temp_dir):
        """Test that dynamic calls (method calls) are tracked separately."""
        (temp_dir / "main.py").write_text("")

        symbols = [
            ExtractedSymbol(
                path="main.py",
                symbol_name="main",
                symbol_type="function",
                line_start=1,
                line_end=3,
                is_exported=True,
                parameters=0,
                parent_symbol=None,
                docstring=None,
            ),
        ]

        resolver = CallResolver(temp_dir, symbols, [])

        calls = [
            ExtractedCall(
                caller_file="main.py",
                caller_symbol="main",
                callee_symbol="strip",  # obj.strip() - can't resolve without type info
                callee_file=None,
                line_number=2,
                call_type="dynamic",
            ),
        ]

        resolved = resolver.resolve(calls)

        assert len(resolved) == 1
        assert resolved[0].callee_file is None
        assert resolver.stats.unresolved_dynamic == 1

    def test_package_import_resolution(self, temp_dir):
        """Test resolution of package imports (pkg/__init__.py)."""
        pkg_dir = temp_dir / "mypackage"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        (temp_dir / "main.py").write_text("")

        symbols = [
            ExtractedSymbol(
                path="mypackage/__init__.py",
                symbol_name="package_func",
                symbol_type="function",
                line_start=1,
                line_end=2,
                is_exported=True,
                parameters=0,
                parent_symbol=None,
                docstring=None,
            ),
            ExtractedSymbol(
                path="main.py",
                symbol_name="main",
                symbol_type="function",
                line_start=3,
                line_end=5,
                is_exported=True,
                parameters=0,
                parent_symbol=None,
                docstring=None,
            ),
        ]

        imports = [
            ExtractedImport(
                file="main.py",
                imported_path="mypackage",
                imported_symbols="package_func",
                import_type="static",
                line_number=1,
            ),
        ]

        resolver = CallResolver(temp_dir, symbols, imports)

        calls = [
            ExtractedCall(
                caller_file="main.py",
                caller_symbol="main",
                callee_symbol="package_func",
                callee_file=None,
                line_number=4,
                call_type="direct",
            ),
        ]

        resolved = resolver.resolve(calls)

        assert len(resolved) == 1
        assert resolved[0].callee_file == "mypackage/__init__.py"

    def test_parent_relative_import(self, temp_dir):
        """Test resolution of parent-level relative imports (from .. import x)."""
        pkg_dir = temp_dir / "pkg"
        sub_dir = pkg_dir / "subpkg"
        pkg_dir.mkdir()
        sub_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "utils.py").write_text("")
        (sub_dir / "__init__.py").write_text("")
        (sub_dir / "main.py").write_text("")

        symbols = [
            ExtractedSymbol(
                path="pkg/utils.py",
                symbol_name="helper",
                symbol_type="function",
                line_start=1,
                line_end=2,
                is_exported=True,
                parameters=0,
                parent_symbol=None,
                docstring=None,
            ),
            ExtractedSymbol(
                path="pkg/subpkg/main.py",
                symbol_name="main",
                symbol_type="function",
                line_start=3,
                line_end=5,
                is_exported=True,
                parameters=0,
                parent_symbol=None,
                docstring=None,
            ),
        ]

        imports = [
            ExtractedImport(
                file="pkg/subpkg/main.py",
                imported_path="..utils",
                imported_symbols="helper",
                import_type="static",
                line_number=1,
            ),
        ]

        resolver = CallResolver(temp_dir, symbols, imports)

        calls = [
            ExtractedCall(
                caller_file="pkg/subpkg/main.py",
                caller_symbol="main",
                callee_symbol="helper",
                callee_file=None,
                line_number=4,
                call_type="direct",
            ),
        ]

        resolved = resolver.resolve(calls)

        assert len(resolved) == 1
        assert resolved[0].callee_file == "pkg/utils.py"


class TestBuiltinsAndStdlib:
    """Tests for builtin and stdlib detection."""

    def test_builtin_functions_comprehensive(self):
        """Verify common builtins are in the set."""
        common_builtins = [
            "print", "len", "range", "str", "int", "float", "list", "dict",
            "set", "tuple", "bool", "open", "type", "isinstance", "hasattr",
            "getattr", "setattr", "sum", "min", "max", "sorted", "enumerate",
            "zip", "map", "filter", "any", "all", "abs", "round", "input",
        ]
        for builtin in common_builtins:
            assert builtin in BUILTIN_FUNCTIONS, f"Missing builtin: {builtin}"

    def test_stdlib_modules_comprehensive(self):
        """Verify common stdlib modules are in the set."""
        common_stdlib = [
            "os", "sys", "json", "re", "datetime", "pathlib", "collections",
            "itertools", "functools", "typing", "dataclasses", "abc",
            "subprocess", "threading", "multiprocessing", "asyncio",
            "unittest", "logging", "argparse", "math", "random", "time",
            "copy", "pickle", "hashlib", "base64", "urllib", "http",
        ]
        for module in common_stdlib:
            assert module in STDLIB_MODULES, f"Missing stdlib module: {module}"


class TestResolutionStats:
    """Tests for resolution statistics."""

    def test_stats_tracking(self, temp_dir):
        """Test that stats are properly tracked."""
        (temp_dir / "utils.py").write_text("")
        (temp_dir / "main.py").write_text("")

        symbols = [
            ExtractedSymbol(
                path="utils.py",
                symbol_name="validate",
                symbol_type="function",
                line_start=1,
                line_end=2,
                is_exported=True,
                parameters=1,
                parent_symbol=None,
                docstring=None,
            ),
            ExtractedSymbol(
                path="main.py",
                symbol_name="helper",
                symbol_type="function",
                line_start=1,
                line_end=2,
                is_exported=True,
                parameters=0,
                parent_symbol=None,
                docstring=None,
            ),
            ExtractedSymbol(
                path="main.py",
                symbol_name="main",
                symbol_type="function",
                line_start=4,
                line_end=10,
                is_exported=True,
                parameters=0,
                parent_symbol=None,
                docstring=None,
            ),
        ]

        imports = [
            ExtractedImport(
                file="main.py",
                imported_path="utils",
                imported_symbols="validate",
                import_type="static",
                line_number=1,
            ),
        ]

        resolver = CallResolver(temp_dir, symbols, imports)

        calls = [
            # Cross-file call
            ExtractedCall(
                caller_file="main.py",
                caller_symbol="main",
                callee_symbol="validate",
                callee_file=None,
                line_number=5,
                call_type="direct",
            ),
            # Same-file call
            ExtractedCall(
                caller_file="main.py",
                caller_symbol="main",
                callee_symbol="helper",
                callee_file=None,
                line_number=6,
                call_type="direct",
            ),
            # Builtin call
            ExtractedCall(
                caller_file="main.py",
                caller_symbol="main",
                callee_symbol="print",
                callee_file=None,
                line_number=7,
                call_type="direct",
            ),
            # Dynamic call
            ExtractedCall(
                caller_file="main.py",
                caller_symbol="main",
                callee_symbol="strip",
                callee_file=None,
                line_number=8,
                call_type="dynamic",
            ),
        ]

        resolved = resolver.resolve(calls)

        assert resolver.stats.total_calls == 4
        assert resolver.stats.resolved_cross_file == 1
        assert resolver.stats.resolved_same_file == 1
        assert resolver.stats.unresolved_builtin == 1
        assert resolver.stats.unresolved_dynamic == 1
        assert resolver.stats.total_resolved == 2
        assert resolver.stats.total_unresolved == 2

    def test_stats_to_dict(self, temp_dir):
        """Test stats can be converted to dict."""
        resolver = CallResolver(temp_dir, [], [])
        resolver.resolve([])

        stats_dict = resolver.stats.to_dict()

        assert "total_calls" in stats_dict
        assert "resolved_same_file" in stats_dict
        assert "resolved_cross_file" in stats_dict
        assert "resolved_module_attr" in stats_dict
        assert "total_resolved" in stats_dict
        assert "total_unresolved" in stats_dict


class TestModuleAttributeResolution:
    """Tests for module.function() call resolution."""

    def test_module_import_resolution(self, temp_dir):
        """Test resolution of import x; x.func() pattern."""
        (temp_dir / "utils.py").write_text("")
        (temp_dir / "main.py").write_text("")

        symbols = [
            ExtractedSymbol(
                path="utils.py",
                symbol_name="validate",
                symbol_type="function",
                line_start=1,
                line_end=3,
                is_exported=True,
                parameters=1,
                parent_symbol=None,
                docstring=None,
            ),
            ExtractedSymbol(
                path="main.py",
                symbol_name="process",
                symbol_type="function",
                line_start=3,
                line_end=5,
                is_exported=True,
                parameters=0,
                parent_symbol=None,
                docstring=None,
            ),
        ]

        imports = [
            ExtractedImport(
                file="main.py",
                imported_path="utils",
                imported_symbols=None,  # Full module import
                import_type="static",
                line_number=1,
            ),
        ]

        resolver = CallResolver(temp_dir, symbols, imports)

        calls = [
            ExtractedCall(
                caller_file="main.py",
                caller_symbol="process",
                callee_symbol="validate",
                callee_file=None,
                line_number=4,
                call_type="dynamic",
                callee_object="utils",  # utils.validate()
            ),
        ]

        resolved = resolver.resolve(calls)

        assert len(resolved) == 1
        assert resolved[0].callee_file == "utils.py"
        assert resolver.stats.resolved_module_attr == 1

    def test_aliased_module_import_resolution(self, temp_dir):
        """Test resolution of import x as y; y.func() pattern."""
        (temp_dir / "utils.py").write_text("")
        (temp_dir / "main.py").write_text("")

        symbols = [
            ExtractedSymbol(
                path="utils.py",
                symbol_name="validate",
                symbol_type="function",
                line_start=1,
                line_end=3,
                is_exported=True,
                parameters=1,
                parent_symbol=None,
                docstring=None,
            ),
            ExtractedSymbol(
                path="main.py",
                symbol_name="process",
                symbol_type="function",
                line_start=3,
                line_end=5,
                is_exported=True,
                parameters=0,
                parent_symbol=None,
                docstring=None,
            ),
        ]

        imports = [
            ExtractedImport(
                file="main.py",
                imported_path="utils",
                imported_symbols=None,
                import_type="static",
                line_number=1,
                module_alias="u",  # import utils as u
            ),
        ]

        resolver = CallResolver(temp_dir, symbols, imports)

        calls = [
            ExtractedCall(
                caller_file="main.py",
                caller_symbol="process",
                callee_symbol="validate",
                callee_file=None,
                line_number=4,
                call_type="dynamic",
                callee_object="u",  # u.validate()
            ),
        ]

        resolved = resolver.resolve(calls)

        assert len(resolved) == 1
        assert resolved[0].callee_file == "utils.py"
        assert resolver.stats.resolved_module_attr == 1

    def test_stdlib_module_stays_unresolved(self, temp_dir):
        """Test that stdlib module.func() calls remain unresolved."""
        (temp_dir / "main.py").write_text("")

        symbols = [
            ExtractedSymbol(
                path="main.py",
                symbol_name="main",
                symbol_type="function",
                line_start=3,
                line_end=5,
                is_exported=True,
                parameters=0,
                parent_symbol=None,
                docstring=None,
            ),
        ]

        imports = [
            ExtractedImport(
                file="main.py",
                imported_path="json",
                imported_symbols=None,  # import json
                import_type="static",
                line_number=1,
            ),
        ]

        resolver = CallResolver(temp_dir, symbols, imports)

        calls = [
            ExtractedCall(
                caller_file="main.py",
                caller_symbol="main",
                callee_symbol="loads",
                callee_file=None,
                line_number=4,
                call_type="dynamic",
                callee_object="json",  # json.loads()
            ),
        ]

        resolved = resolver.resolve(calls)

        assert len(resolved) == 1
        assert resolved[0].callee_file is None
        # Should be unresolved_dynamic since json is stdlib (not in repo)
        assert resolver.stats.unresolved_dynamic == 1
        assert resolver.stats.resolved_module_attr == 0

    def test_self_cls_not_treated_as_modules(self, temp_dir):
        """Test that self.method() and cls.method() remain unresolved dynamic."""
        (temp_dir / "main.py").write_text("")

        symbols = [
            ExtractedSymbol(
                path="main.py",
                symbol_name="MyClass",
                symbol_type="class",
                line_start=1,
                line_end=10,
                is_exported=True,
                parameters=None,
                parent_symbol=None,
                docstring=None,
            ),
            ExtractedSymbol(
                path="main.py",
                symbol_name="do_something",
                symbol_type="method",
                line_start=3,
                line_end=5,
                is_exported=True,
                parameters=0,
                parent_symbol="MyClass",
                docstring=None,
            ),
            ExtractedSymbol(
                path="main.py",
                symbol_name="another_method",
                symbol_type="method",
                line_start=7,
                line_end=9,
                is_exported=True,
                parameters=0,
                parent_symbol="MyClass",
                docstring=None,
            ),
        ]

        resolver = CallResolver(temp_dir, symbols, [])

        calls = [
            ExtractedCall(
                caller_file="main.py",
                caller_symbol="another_method",
                callee_symbol="do_something",
                callee_file=None,
                line_number=8,
                call_type="dynamic",
                callee_object="self",  # self.do_something()
            ),
            ExtractedCall(
                caller_file="main.py",
                caller_symbol="another_method",
                callee_symbol="class_method",
                callee_file=None,
                line_number=9,
                call_type="dynamic",
                callee_object="cls",  # cls.class_method()
            ),
        ]

        resolved = resolver.resolve(calls)

        assert len(resolved) == 2
        assert resolved[0].callee_file is None
        assert resolved[1].callee_file is None
        assert resolver.stats.unresolved_dynamic == 2
        assert resolver.stats.resolved_module_attr == 0

    def test_nonexistent_function_in_module(self, temp_dir):
        """Test that module.nonexistent_func() remains unresolved."""
        (temp_dir / "utils.py").write_text("")
        (temp_dir / "main.py").write_text("")

        symbols = [
            ExtractedSymbol(
                path="utils.py",
                symbol_name="validate",
                symbol_type="function",
                line_start=1,
                line_end=3,
                is_exported=True,
                parameters=1,
                parent_symbol=None,
                docstring=None,
            ),
            ExtractedSymbol(
                path="main.py",
                symbol_name="process",
                symbol_type="function",
                line_start=3,
                line_end=5,
                is_exported=True,
                parameters=0,
                parent_symbol=None,
                docstring=None,
            ),
        ]

        imports = [
            ExtractedImport(
                file="main.py",
                imported_path="utils",
                imported_symbols=None,
                import_type="static",
                line_number=1,
            ),
        ]

        resolver = CallResolver(temp_dir, symbols, imports)

        calls = [
            ExtractedCall(
                caller_file="main.py",
                caller_symbol="process",
                callee_symbol="nonexistent",  # Function doesn't exist in utils.py
                callee_file=None,
                line_number=4,
                call_type="dynamic",
                callee_object="utils",
            ),
        ]

        resolved = resolver.resolve(calls)

        assert len(resolved) == 1
        assert resolved[0].callee_file is None
        assert resolver.stats.unresolved_dynamic == 1
        assert resolver.stats.resolved_module_attr == 0
