"""Call resolution for JavaScript/TypeScript cross-module function calls."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path, PurePosixPath

from .base import ExtractedCall, ExtractedImport, ExtractedSymbol
from .call_resolver import ResolvedNamespace, ResolutionStats


# Node.js built-in modules (not requiring npm install)
NODE_BUILTINS = frozenset({
    "assert", "assert/strict", "async_hooks", "buffer", "child_process",
    "cluster", "console", "constants", "crypto", "dgram", "diagnostics_channel",
    "dns", "dns/promises", "domain", "events", "fs", "fs/promises",
    "http", "http2", "https", "inspector", "module", "net", "os", "path",
    "path/posix", "path/win32", "perf_hooks", "process", "punycode",
    "querystring", "readline", "readline/promises", "repl", "stream",
    "stream/consumers", "stream/promises", "stream/web", "string_decoder",
    "sys", "test", "timers", "timers/promises", "tls", "trace_events",
    "tty", "url", "util", "v8", "vm", "wasi", "worker_threads", "zlib",
    # Also accept node: prefix-stripped versions
    "node:assert", "node:buffer", "node:child_process", "node:cluster",
    "node:console", "node:crypto", "node:dgram", "node:dns", "node:events",
    "node:fs", "node:http", "node:http2", "node:https", "node:inspector",
    "node:module", "node:net", "node:os", "node:path", "node:perf_hooks",
    "node:process", "node:querystring", "node:readline", "node:repl",
    "node:stream", "node:string_decoder", "node:timers", "node:tls",
    "node:tty", "node:url", "node:util", "node:v8", "node:vm",
    "node:worker_threads", "node:zlib",
})

# JavaScript global functions/objects (always available, no import needed)
JS_GLOBALS = frozenset({
    "console", "setTimeout", "setInterval", "clearTimeout", "clearInterval",
    "setImmediate", "clearImmediate", "queueMicrotask",
    "fetch", "parseInt", "parseFloat", "isNaN", "isFinite",
    "encodeURI", "encodeURIComponent", "decodeURI", "decodeURIComponent",
    "JSON", "Math", "Date", "RegExp", "Error", "TypeError", "RangeError",
    "SyntaxError", "ReferenceError", "URIError", "EvalError",
    "Promise", "Array", "Object", "String", "Number", "Boolean",
    "Symbol", "Map", "Set", "WeakMap", "WeakSet", "WeakRef",
    "Proxy", "Reflect", "globalThis", "Intl",
    "ArrayBuffer", "SharedArrayBuffer", "DataView",
    "Float32Array", "Float64Array", "Int8Array", "Int16Array", "Int32Array",
    "Uint8Array", "Uint16Array", "Uint32Array", "Uint8ClampedArray",
    "BigInt", "BigInt64Array", "BigUint64Array",
    "FinalizationRegistry", "AggregateError",
    "structuredClone", "atob", "btoa",
    "TextEncoder", "TextDecoder", "URL", "URLSearchParams",
    "AbortController", "AbortSignal",
    "EventTarget", "Event", "CustomEvent",
    "ReadableStream", "WritableStream", "TransformStream",
    "Blob", "File", "FormData", "Headers", "Request", "Response",
})

# File extensions to try when resolving JS/TS imports
_JS_EXTENSIONS = (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx")


class JSCallResolver:
    """Resolves callee_file for JavaScript/TypeScript cross-module calls."""

    def __init__(
        self,
        repo_root: Path,
        symbols: list[ExtractedSymbol],
        imports: list[ExtractedImport],
    ) -> None:
        self.repo_root = repo_root
        self._symbols_by_file = self._index_symbols_by_file(symbols)
        self._symbols_by_name = self._index_symbols_by_name(symbols)
        self._imports_by_file = self._group_imports_by_file(imports)
        self._namespace_cache: dict[str, ResolvedNamespace] = {}
        self._all_files = set(self._symbols_by_file.keys())
        self.stats = ResolutionStats()

    def _index_symbols_by_file(
        self, symbols: list[ExtractedSymbol],
    ) -> dict[str, set[str]]:
        index: dict[str, set[str]] = {}
        for symbol in symbols:
            if symbol.path not in index:
                index[symbol.path] = set()
            index[symbol.path].add(symbol.symbol_name)
        return index

    def _index_symbols_by_name(
        self, symbols: list[ExtractedSymbol],
    ) -> dict[str, list[str]]:
        index: dict[str, list[str]] = {}
        for symbol in symbols:
            if symbol.is_exported:
                if symbol.symbol_name not in index:
                    index[symbol.symbol_name] = []
                index[symbol.symbol_name].append(symbol.path)
        return index

    def _group_imports_by_file(
        self, imports: list[ExtractedImport],
    ) -> dict[str, list[ExtractedImport]]:
        grouped: dict[str, list[ExtractedImport]] = {}
        for imp in imports:
            if imp.file not in grouped:
                grouped[imp.file] = []
            grouped[imp.file].append(imp)
        return grouped

    def resolve(self, calls: list[ExtractedCall]) -> list[ExtractedCall]:
        """Resolve callee_file for all calls."""
        self.stats = ResolutionStats(total_calls=len(calls))
        resolved_calls = []

        for call in calls:
            resolved_file = self._resolve_call(call)
            if resolved_file != call.callee_file:
                resolved_calls.append(replace(call, callee_file=resolved_file))
            else:
                resolved_calls.append(call)

        return resolved_calls

    def _resolve_call(self, call: ExtractedCall) -> str | None:
        """Resolve a single call to its defining file."""
        callee = call.callee_symbol
        caller_file = call.caller_file

        # For dynamic calls on this/super, skip
        if call.call_type == "dynamic" and call.callee_object in ("this", "super"):
            self.stats.unresolved_dynamic += 1
            return None

        # 1. Check if defined in same file
        if caller_file in self._symbols_by_file:
            if callee in self._symbols_by_file[caller_file]:
                self.stats.resolved_same_file += 1
                return caller_file

        # 2. Check if it's a JS global
        if callee in JS_GLOBALS:
            self.stats.unresolved_builtin += 1
            return None

        # 3. For dynamic calls with callee_object, try module attribute resolution
        if call.call_type == "dynamic" and call.callee_object:
            resolved = self._resolve_module_attribute_call(call)
            if resolved:
                return resolved

        # 4. Build namespace and look up symbol
        namespace = self._get_or_build_namespace(caller_file)
        if namespace:
            if callee in namespace.bindings:
                self.stats.resolved_cross_file += 1
                return namespace.bindings[callee]

            for star_file in namespace.star_imports:
                if star_file in self._symbols_by_file:
                    if callee in self._symbols_by_file[star_file]:
                        self.stats.resolved_cross_file += 1
                        return star_file

        # 5. Unable to resolve
        if call.call_type == "dynamic":
            self.stats.unresolved_dynamic += 1
        else:
            self.stats.unresolved_external += 1
        return None

    def _resolve_module_attribute_call(self, call: ExtractedCall) -> str | None:
        """Resolve module.function() calls using module_aliases."""
        callee_object = call.callee_object

        namespace = self._get_or_build_namespace(call.caller_file)
        if not namespace:
            return None

        if callee_object in namespace.module_aliases:
            module_file = namespace.module_aliases[callee_object]
            if module_file and module_file in self._symbols_by_file:
                if call.callee_symbol in self._symbols_by_file[module_file]:
                    self.stats.resolved_module_attr += 1
                    return module_file

        return None

    def _get_or_build_namespace(self, file_path: str) -> ResolvedNamespace | None:
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
            if imp.import_type == "dynamic":
                continue

            resolved_file = self._resolve_module_path(imp.imported_path, file_path)
            if resolved_file is None:
                continue

            if imp.imported_symbols is None:
                # Default import: import x from "./mod" -> alias is module_alias
                # or side_effect with no symbols
                if imp.module_alias:
                    module_aliases[imp.module_alias] = resolved_file
            elif imp.imported_symbols == "*":
                # import * as ns from "./mod"
                if imp.module_alias:
                    module_aliases[imp.module_alias] = resolved_file
                star_imports.append(resolved_file)
            else:
                # Named imports: import { a, b } from "./mod"
                symbols = imp.imported_symbols.split(",")
                for symbol in symbols:
                    symbol = symbol.strip()
                    if not symbol:
                        continue
                    if " as " in symbol:
                        _original, alias = symbol.split(" as ", 1)
                        bindings[alias.strip()] = resolved_file
                    else:
                        bindings[symbol] = resolved_file

        return ResolvedNamespace(
            bindings=bindings,
            module_aliases=module_aliases,
            star_imports=star_imports,
        )

    def _resolve_module_path(
        self, import_path: str, from_file: str,
    ) -> str | None:
        """Convert a JS/TS import path to a repo-relative file path."""
        # Handle node: protocol
        if import_path.startswith("node:"):
            return None

        # Node.js builtins
        root_module = import_path.split("/")[0]
        if root_module in NODE_BUILTINS:
            return None

        # Relative imports
        if import_path.startswith("."):
            return self._resolve_relative_import(import_path, from_file)

        # Bare specifiers (npm packages) -> external
        # These look like: "react", "lodash/fp", "@types/node"
        return None

    def _resolve_relative_import(
        self, import_path: str, from_file: str,
    ) -> str | None:
        """Resolve a relative JS/TS import path."""
        from_dir = str(PurePosixPath(from_file).parent)

        # Resolve the relative path
        if import_path.startswith("./"):
            target = import_path[2:]
        elif import_path.startswith("../"):
            # Walk up directories
            parts = import_path.split("/")
            dir_parts = from_dir.split("/") if from_dir != "." else []
            i = 0
            while i < len(parts) and parts[i] == "..":
                if dir_parts:
                    dir_parts.pop()
                i += 1
            remaining = "/".join(parts[i:])
            base_dir = "/".join(dir_parts) if dir_parts else ""
            target = f"{base_dir}/{remaining}" if base_dir else remaining
        else:
            target = import_path

        # Try exact match first
        if target in self._all_files:
            return target

        # Try with extensions
        for ext in _JS_EXTENSIONS:
            candidate = target + ext
            if candidate in self._all_files:
                return candidate

        # Try as directory with index file
        for ext in _JS_EXTENSIONS:
            candidate = f"{target}/index{ext}"
            if candidate in self._all_files:
                return candidate

        # Try with path from repo root if from_dir is not empty
        if from_dir and from_dir != ".":
            full_target = f"{from_dir}/{target}"
            if full_target in self._all_files:
                return full_target
            for ext in _JS_EXTENSIONS:
                candidate = full_target + ext
                if candidate in self._all_files:
                    return candidate
            for ext in _JS_EXTENSIONS:
                candidate = f"{full_target}/index{ext}"
                if candidate in self._all_files:
                    return candidate

        return None
