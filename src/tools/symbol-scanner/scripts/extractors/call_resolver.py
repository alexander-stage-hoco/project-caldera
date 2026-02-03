"""Call resolution for cross-module function calls."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath

from .base import ExtractedCall, ExtractedImport, ExtractedSymbol


# Python builtin functions (not requiring import)
BUILTIN_FUNCTIONS = frozenset({
    "abs", "aiter", "all", "anext", "any", "ascii",
    "bin", "bool", "breakpoint", "bytearray", "bytes",
    "callable", "chr", "classmethod", "compile", "complex",
    "delattr", "dict", "dir", "divmod",
    "enumerate", "eval", "exec",
    "filter", "float", "format", "frozenset",
    "getattr", "globals",
    "hasattr", "hash", "help", "hex",
    "id", "input", "int", "isinstance", "issubclass", "iter",
    "len", "list", "locals",
    "map", "max", "memoryview", "min",
    "next",
    "object", "oct", "open", "ord",
    "pow", "print", "property",
    "range", "repr", "reversed", "round",
    "set", "setattr", "slice", "sorted", "staticmethod", "str", "sum", "super",
    "tuple", "type",
    "vars",
    "zip",
    "__import__",
})

# Python standard library modules (Python 3.10+)
STDLIB_MODULES = frozenset({
    # Built-in
    "abc", "aifc", "argparse", "array", "ast", "asynchat", "asyncio", "asyncore",
    "atexit", "audioop",
    "base64", "bdb", "binascii", "binhex", "bisect", "builtins",
    "bz2",
    "calendar", "cgi", "cgitb", "chunk", "cmath", "cmd", "code", "codecs",
    "codeop", "collections", "colorsys", "compileall", "concurrent",
    "configparser", "contextlib", "contextvars", "copy", "copyreg", "cProfile",
    "crypt", "csv", "ctypes", "curses",
    "dataclasses", "datetime", "dbm", "decimal", "difflib", "dis", "distutils",
    "doctest",
    "email", "encodings", "enum", "errno",
    "faulthandler", "fcntl", "filecmp", "fileinput", "fnmatch", "fractions",
    "ftplib", "functools",
    "gc", "getopt", "getpass", "gettext", "glob", "graphlib", "grp", "gzip",
    "hashlib", "heapq", "hmac", "html", "http",
    "idlelib", "imaplib", "imghdr", "imp", "importlib", "inspect", "io",
    "ipaddress", "itertools",
    "json",
    "keyword",
    "lib2to3", "linecache", "locale", "logging", "lzma",
    "mailbox", "mailcap", "marshal", "math", "mimetypes", "mmap", "modulefinder",
    "multiprocessing",
    "netrc", "nis", "nntplib", "numbers",
    "operator", "optparse", "os", "ossaudiodev",
    "pathlib", "pdb", "pickle", "pickletools", "pipes", "pkgutil", "platform",
    "plistlib", "poplib", "posix", "posixpath", "pprint", "profile", "pstats",
    "pty", "pwd", "py_compile", "pyclbr", "pydoc",
    "queue", "quopri",
    "random", "re", "readline", "reprlib", "resource", "rlcompleter", "runpy",
    "sched", "secrets", "select", "selectors", "shelve", "shlex", "shutil",
    "signal", "site", "smtpd", "smtplib", "sndhdr", "socket", "socketserver",
    "spwd", "sqlite3", "ssl", "stat", "statistics", "string", "stringprep",
    "struct", "subprocess", "sunau", "symtable", "sys", "sysconfig", "syslog",
    "tabnanny", "tarfile", "telnetlib", "tempfile", "termios", "test", "textwrap",
    "threading", "time", "timeit", "tkinter", "token", "tokenize", "tomllib",
    "trace", "traceback", "tracemalloc", "tty", "turtle", "turtledemo", "types",
    "typing",
    "unicodedata", "unittest", "urllib", "uu", "uuid",
    "venv",
    "warnings", "wave", "weakref", "webbrowser", "winreg", "winsound", "wsgiref",
    "xdrlib", "xml", "xmlrpc",
    "zipapp", "zipfile", "zipimport", "zlib", "zoneinfo",
    # Common typing/annotation imports
    "_typeshed", "typing_extensions",
})


@dataclass
class ResolvedNamespace:
    """Namespace of resolved symbols for a file."""

    # Direct symbol bindings: symbol_name -> resolved_file_path
    bindings: dict[str, str]
    # Module alias bindings: alias -> module_file_path (for import x or import x as y)
    module_aliases: dict[str, str]
    # Star import sources: list of file paths to search for unbound symbols
    star_imports: list[str]


@dataclass
class ResolutionStats:
    """Statistics about call resolution."""

    total_calls: int = 0
    resolved_same_file: int = 0
    resolved_cross_file: int = 0
    resolved_module_attr: int = 0  # Resolved via module.function() pattern
    unresolved_builtin: int = 0
    unresolved_stdlib: int = 0
    unresolved_external: int = 0
    unresolved_dynamic: int = 0

    @property
    def total_resolved(self) -> int:
        return self.resolved_same_file + self.resolved_cross_file + self.resolved_module_attr

    @property
    def total_unresolved(self) -> int:
        return (
            self.unresolved_builtin
            + self.unresolved_stdlib
            + self.unresolved_external
            + self.unresolved_dynamic
        )

    def to_dict(self) -> dict:
        return {
            "total_calls": self.total_calls,
            "resolved_same_file": self.resolved_same_file,
            "resolved_cross_file": self.resolved_cross_file,
            "resolved_module_attr": self.resolved_module_attr,
            "unresolved_builtin": self.unresolved_builtin,
            "unresolved_stdlib": self.unresolved_stdlib,
            "unresolved_external": self.unresolved_external,
            "unresolved_dynamic": self.unresolved_dynamic,
            "total_resolved": self.total_resolved,
            "total_unresolved": self.total_unresolved,
        }


class CallResolver:
    """Resolves callee_file for cross-module function calls."""

    def __init__(
        self,
        repo_root: Path,
        symbols: list[ExtractedSymbol],
        imports: list[ExtractedImport],
    ) -> None:
        """Initialize the resolver.

        Args:
            repo_root: Root path of the repository being analyzed
            symbols: All extracted symbols from the repository
            imports: All extracted imports from the repository
        """
        self.repo_root = repo_root
        self._symbols_by_file = self._index_symbols_by_file(symbols)
        self._symbols_by_name = self._index_symbols_by_name(symbols)
        self._imports_by_file = self._group_imports_by_file(imports)
        self._namespace_cache: dict[str, ResolvedNamespace] = {}
        self._all_files = set(self._symbols_by_file.keys())
        self.stats = ResolutionStats()

    def _index_symbols_by_file(
        self, symbols: list[ExtractedSymbol]
    ) -> dict[str, set[str]]:
        """Index symbol names by their file path."""
        index: dict[str, set[str]] = {}
        for symbol in symbols:
            if symbol.path not in index:
                index[symbol.path] = set()
            index[symbol.path].add(symbol.symbol_name)
        return index

    def _index_symbols_by_name(
        self, symbols: list[ExtractedSymbol]
    ) -> dict[str, list[str]]:
        """Index file paths by symbol name (for star import lookup)."""
        index: dict[str, list[str]] = {}
        for symbol in symbols:
            # Only index exported symbols for cross-file resolution
            if symbol.is_exported:
                if symbol.symbol_name not in index:
                    index[symbol.symbol_name] = []
                index[symbol.symbol_name].append(symbol.path)
        return index

    def _group_imports_by_file(
        self, imports: list[ExtractedImport]
    ) -> dict[str, list[ExtractedImport]]:
        """Group imports by their source file."""
        grouped: dict[str, list[ExtractedImport]] = {}
        for imp in imports:
            if imp.file not in grouped:
                grouped[imp.file] = []
            grouped[imp.file].append(imp)
        return grouped

    def resolve(self, calls: list[ExtractedCall]) -> list[ExtractedCall]:
        """Resolve callee_file for all calls.

        Args:
            calls: List of calls to resolve

        Returns:
            New list of calls with callee_file populated where possible
        """
        self.stats = ResolutionStats(total_calls=len(calls))
        resolved_calls = []

        for call in calls:
            resolved_file = self._resolve_call(call)
            if resolved_file != call.callee_file:
                # Create a new call with updated callee_file
                resolved_calls.append(replace(call, callee_file=resolved_file))
            else:
                resolved_calls.append(call)

        return resolved_calls

    def _resolve_call(self, call: ExtractedCall) -> str | None:
        """Resolve a single call to its defining file.

        Returns:
            Resolved file path or None if unresolvable
        """
        callee = call.callee_symbol
        caller_file = call.caller_file

        # For dynamic calls with self/cls, we can't statically resolve
        # since we don't know the type - skip to unresolved_dynamic
        if call.call_type == "dynamic" and call.callee_object in ("self", "cls"):
            self.stats.unresolved_dynamic += 1
            return None

        # 1. Check if defined in same file FIRST (handles shadowed builtins)
        # This must come before the builtin check because local definitions
        # can shadow builtin names like list(), dict(), etc.
        if caller_file in self._symbols_by_file:
            if callee in self._symbols_by_file[caller_file]:
                self.stats.resolved_same_file += 1
                return caller_file

        # 2. THEN check if it's a Python builtin
        if callee in BUILTIN_FUNCTIONS:
            self.stats.unresolved_builtin += 1
            return None

        # 3. For dynamic calls with callee_object, try module attribute resolution
        # This handles patterns like: import utils; utils.validate()
        if call.call_type == "dynamic" and call.callee_object:
            resolved = self._resolve_module_attribute_call(call)
            if resolved:
                return resolved

        # 4. Build namespace and look up symbol
        namespace = self._get_or_build_namespace(caller_file)
        if namespace:
            # Check direct bindings
            if callee in namespace.bindings:
                self.stats.resolved_cross_file += 1
                return namespace.bindings[callee]

            # Check star imports
            for star_file in namespace.star_imports:
                if star_file in self._symbols_by_file:
                    if callee in self._symbols_by_file[star_file]:
                        self.stats.resolved_cross_file += 1
                        return star_file

        # 5. Unable to resolve - could be external, stdlib, or truly unresolved
        if call.call_type == "dynamic":
            self.stats.unresolved_dynamic += 1
        else:
            self.stats.unresolved_external += 1
        return None

    def _resolve_module_attribute_call(self, call: ExtractedCall) -> str | None:
        """Resolve module.function() calls using module_aliases.

        Args:
            call: Call with callee_object set (e.g., "utils" for utils.validate())

        Returns:
            Resolved file path or None if unresolvable
        """
        callee_object = call.callee_object
        # Note: self/cls are handled earlier in _resolve_call

        namespace = self._get_or_build_namespace(call.caller_file)
        if not namespace:
            return None

        # Check if callee_object is a known module alias
        if callee_object in namespace.module_aliases:
            module_file = namespace.module_aliases[callee_object]
            if module_file and module_file in self._symbols_by_file:
                # Check if the callee symbol exists in that module
                if call.callee_symbol in self._symbols_by_file[module_file]:
                    self.stats.resolved_module_attr += 1
                    return module_file

        return None

    def _get_or_build_namespace(self, file_path: str) -> ResolvedNamespace | None:
        """Get cached namespace or build it for a file."""
        if file_path in self._namespace_cache:
            return self._namespace_cache[file_path]

        namespace = self._build_namespace(file_path)
        self._namespace_cache[file_path] = namespace
        return namespace

    def _build_namespace(self, file_path: str) -> ResolvedNamespace:
        """Build the resolved namespace for a file based on its imports."""
        bindings: dict[str, str] = {}
        module_aliases: dict[str, str] = {}
        star_imports: list[str] = []

        imports = self._imports_by_file.get(file_path, [])

        for imp in imports:
            # Skip dynamic imports
            if imp.import_type == "dynamic":
                continue

            # Resolve the module path to a file
            resolved_file = self._resolve_module_path(imp.imported_path, file_path)

            if resolved_file is None:
                # Could be stdlib, third-party, or doesn't exist
                continue

            if imp.imported_symbols is None:
                # import x or import x as y
                # Creates a module alias - use explicit alias if provided, else last part of path
                alias = imp.module_alias or imp.imported_path.split(".")[-1]
                module_aliases[alias] = resolved_file
            elif imp.imported_symbols == "*":
                # from x import *
                star_imports.append(resolved_file)
            else:
                # from x import a, b, c or from x import a as b
                symbols = imp.imported_symbols.split(",")
                for symbol in symbols:
                    symbol = symbol.strip()
                    if not symbol:
                        continue
                    # Handle aliases: "foo as bar" binds bar -> resolved_file
                    if " as " in symbol:
                        original, alias = symbol.split(" as ", 1)
                        bindings[alias.strip()] = resolved_file
                    else:
                        bindings[symbol] = resolved_file

        return ResolvedNamespace(
            bindings=bindings,
            module_aliases=module_aliases,
            star_imports=star_imports,
        )

    def _resolve_module_path(
        self, import_path: str, from_file: str
    ) -> str | None:
        """Convert an import path to a repo-relative file path.

        Args:
            import_path: Import path (e.g., "utils", ".helper", "..utils.helpers")
            from_file: File containing the import (for relative imports)

        Returns:
            Repo-relative file path or None if not found/external
        """
        # Handle relative imports
        if import_path.startswith("."):
            return self._resolve_relative_import(import_path, from_file)

        # Check if it's a stdlib module
        root_module = import_path.split(".")[0]
        if root_module in STDLIB_MODULES:
            return None

        # Try to find the module in the repo
        # Convert dots to path separators
        path_parts = import_path.split(".")

        # Try as a direct file: utils -> utils.py
        file_path = "/".join(path_parts) + ".py"
        if file_path in self._all_files:
            return file_path

        # Try as a package: utils -> utils/__init__.py
        package_path = "/".join(path_parts) + "/__init__.py"
        if package_path in self._all_files:
            return package_path

        # Try nested: utils.helpers -> utils/helpers.py
        if len(path_parts) > 1:
            module_file = "/".join(path_parts[:-1]) + "/" + path_parts[-1] + ".py"
            if module_file in self._all_files:
                return module_file

        # Not found in repo (external package)
        return None

    def _resolve_relative_import(
        self, import_path: str, from_file: str
    ) -> str | None:
        """Resolve a relative import path.

        Args:
            import_path: Relative import (e.g., ".", ".helper", "..utils")
            from_file: File containing the import

        Returns:
            Repo-relative file path or None if not found
        """
        # Count leading dots
        level = 0
        for char in import_path:
            if char == ".":
                level += 1
            else:
                break

        module_part = import_path[level:]  # Part after dots

        # Get the directory of the importing file
        from_path = PurePosixPath(from_file)
        from_dir = from_path.parent

        # Go up directories based on level
        # level 1 (.) means current package
        # level 2 (..) means parent package
        target_dir = from_dir
        for _ in range(level - 1):
            target_dir = target_dir.parent
            if str(target_dir) == ".":
                # Can't go above repo root
                return None

        # Build the target path
        if module_part:
            parts = module_part.split(".")
            target_path = str(target_dir / "/".join(parts))
        else:
            target_path = str(target_dir)

        # Try as file
        file_path = target_path + ".py"
        if file_path in self._all_files:
            return file_path

        # Try as package
        package_path = target_path + "/__init__.py"
        if package_path in self._all_files:
            return package_path

        return None
