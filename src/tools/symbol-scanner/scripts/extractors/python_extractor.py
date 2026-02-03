"""Python AST-based symbol extractor."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from .base import (
    BaseExtractor,
    ExtractedCall,
    ExtractedImport,
    ExtractedSymbol,
    ExtractionResult,
)


# Built-in functions that execute dynamic code
DYNAMIC_CODE_BUILTINS = frozenset({"eval", "exec", "compile"})


class PythonExtractor(BaseExtractor):
    """Extract symbols, calls, and imports from Python source files using AST."""

    @property
    def language(self) -> str:
        return "python"

    @property
    def file_extensions(self) -> tuple[str, ...]:
        return (".py",)

    def extract_file(self, file_path: Path, relative_path: str) -> ExtractionResult:
        """Extract symbols, calls, and imports from a Python file.

        Args:
            file_path: Absolute path to the file
            relative_path: Repo-relative path for output

        Returns:
            ExtractionResult containing extracted entities
        """
        result = ExtractionResult()

        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError as e:
            result.errors.append({
                "file": relative_path,
                "message": f"Syntax error: {e.msg} at line {e.lineno}",
                "code": "SYNTAX_ERROR",
                "recoverable": True,
            })
            return result
        except UnicodeDecodeError as e:
            result.errors.append({
                "file": relative_path,
                "message": f"Encoding error: {e}",
                "code": "ENCODING_ERROR",
                "recoverable": True,
            })
            return result

        # Extract symbols (functions, classes, methods)
        self._extract_symbols(tree, relative_path, result)

        # Extract module-level variables
        self._extract_module_variables(tree, relative_path, result)

        # Extract imports
        self._extract_imports(tree, relative_path, result)

        # Extract calls
        self._extract_calls(tree, relative_path, result)

        return result

    def _extract_symbols(
        self,
        tree: ast.AST,
        relative_path: str,
        result: ExtractionResult,
        parent_class: str | None = None,
    ) -> None:
        """Extract function and class definitions from AST.

        Args:
            tree: AST node to process
            relative_path: Repo-relative file path
            result: ExtractionResult to populate
            parent_class: Name of parent class (for method extraction)
        """
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                symbol_type = "method" if parent_class else "function"
                is_exported = not node.name.startswith("_")

                # Get parameter count (excluding self for methods)
                params = node.args
                param_count = (
                    len(params.args)
                    + len(params.posonlyargs)
                    + len(params.kwonlyargs)
                )
                # Don't count 'self' or 'cls' for methods
                if parent_class and params.args:
                    first_arg = params.args[0].arg
                    if first_arg in ("self", "cls"):
                        param_count -= 1

                # Get docstring
                docstring = ast.get_docstring(node)

                result.symbols.append(
                    ExtractedSymbol(
                        path=relative_path,
                        symbol_name=node.name,
                        symbol_type=symbol_type,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        is_exported=is_exported,
                        parameters=param_count,
                        parent_symbol=parent_class,
                        docstring=docstring,
                    )
                )

                # Recursively process nested definitions
                self._extract_symbols(node, relative_path, result, parent_class)

            elif isinstance(node, ast.ClassDef):
                is_exported = not node.name.startswith("_")
                docstring = ast.get_docstring(node)

                result.symbols.append(
                    ExtractedSymbol(
                        path=relative_path,
                        symbol_name=node.name,
                        symbol_type="class",
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        is_exported=is_exported,
                        parameters=None,
                        parent_symbol=parent_class,
                        docstring=docstring,
                    )
                )

                # Process class body for methods
                self._extract_symbols(node, relative_path, result, node.name)

    def _extract_module_variables(
        self,
        tree: ast.AST,
        relative_path: str,
        result: ExtractionResult,
    ) -> None:
        """Extract module-level variable assignments.

        Args:
            tree: AST node (module level)
            relative_path: Repo-relative file path
            result: ExtractionResult to populate
        """
        for node in ast.iter_child_nodes(tree):  # Only top-level nodes
            if isinstance(node, ast.Assign):
                # x = 1 or x, y = 1, 2
                for target in node.targets:
                    self._extract_assignment_targets(target, node, relative_path, result)
            elif isinstance(node, ast.AnnAssign) and node.target and node.value is not None:
                # x: int = 1 (only if there's an actual value assigned)
                # Skip `x: int` without value - that's just a type hint
                self._extract_assignment_targets(node.target, node, relative_path, result)

    def _extract_assignment_targets(
        self,
        target: ast.AST,
        node: ast.AST,
        relative_path: str,
        result: ExtractionResult,
    ) -> None:
        """Extract variable names from assignment target.

        Args:
            target: Assignment target node (Name, Tuple, or List)
            node: Parent assignment node (for line numbers)
            relative_path: Repo-relative file path
            result: ExtractionResult to populate
        """
        if isinstance(target, ast.Name):
            name = target.id
            # Skip dunder variables
            if name.startswith("__") and name.endswith("__"):
                return
            result.symbols.append(
                ExtractedSymbol(
                    path=relative_path,
                    symbol_name=name,
                    symbol_type="variable",
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    is_exported=not name.startswith("_"),
                    parameters=None,
                    parent_symbol=None,
                    docstring=None,
                )
            )
        elif isinstance(target, ast.Tuple | ast.List):
            # Handle unpacking: x, y = 1, 2
            for elt in target.elts:
                self._extract_assignment_targets(elt, node, relative_path, result)
        elif isinstance(target, ast.Starred):
            # Handle starred expression: first, *middle, last = range(10)
            self._extract_assignment_targets(target.value, node, relative_path, result)

    def _find_type_checking_ranges(self, tree: ast.AST) -> list[tuple[int, int]]:
        """Find line ranges for if TYPE_CHECKING: blocks.

        Args:
            tree: AST to search

        Returns:
            List of (start_line, end_line) tuples for TYPE_CHECKING blocks
        """
        ranges = []
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                test = node.test
                # Check: TYPE_CHECKING or typing.TYPE_CHECKING
                is_type_checking = False
                if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                    is_type_checking = True
                elif isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING":
                    is_type_checking = True
                if is_type_checking:
                    ranges.append((node.lineno, node.end_lineno or node.lineno))
        return ranges

    def _is_in_type_checking(
        self, line: int, ranges: list[tuple[int, int]]
    ) -> bool:
        """Check if a line is within any TYPE_CHECKING block.

        Args:
            line: Line number to check
            ranges: List of TYPE_CHECKING block ranges

        Returns:
            True if line is inside a TYPE_CHECKING block
        """
        return any(start <= line <= end for start, end in ranges)

    def _extract_imports(
        self,
        tree: ast.AST,
        relative_path: str,
        result: ExtractionResult,
    ) -> None:
        """Extract import statements from AST.

        Args:
            tree: AST node to process
            relative_path: Repo-relative file path
            result: ExtractionResult to populate
        """
        # Find TYPE_CHECKING block ranges for proper import type detection
        type_checking_ranges = self._find_type_checking_ranges(tree)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                # Determine import type based on whether inside TYPE_CHECKING block
                import_type = (
                    "type_checking"
                    if self._is_in_type_checking(node.lineno, type_checking_ranges)
                    else "static"
                )
                for alias in node.names:
                    result.imports.append(
                        ExtractedImport(
                            file=relative_path,
                            imported_path=alias.name,
                            imported_symbols=None,  # Full module import
                            import_type=import_type,
                            line_number=node.lineno,
                            module_alias=alias.asname,  # Capture alias for "import x as y"
                        )
                    )

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                # Handle relative imports
                if node.level > 0:
                    module = "." * node.level + module

                # Get imported symbols
                symbols = [alias.name for alias in node.names]
                symbols_str = ",".join(symbols) if symbols else None

                # Check for star import
                if symbols == ["*"]:
                    symbols_str = "*"

                # Determine import type based on whether inside TYPE_CHECKING block
                import_type = (
                    "type_checking"
                    if self._is_in_type_checking(node.lineno, type_checking_ranges)
                    else "static"
                )

                result.imports.append(
                    ExtractedImport(
                        file=relative_path,
                        imported_path=module,
                        imported_symbols=symbols_str,
                        import_type=import_type,
                        line_number=node.lineno,
                    )
                )

            elif isinstance(node, ast.Call):
                # Detect dynamic imports: __import__() or importlib.import_module()
                func = node.func
                if isinstance(func, ast.Name) and func.id == "__import__":
                    if node.args and isinstance(node.args[0], ast.Constant):
                        result.imports.append(
                            ExtractedImport(
                                file=relative_path,
                                imported_path=str(node.args[0].value),
                                imported_symbols=None,
                                import_type="dynamic",
                                line_number=node.lineno,
                            )
                        )
                elif isinstance(func, ast.Attribute):
                    if func.attr == "import_module":
                        # importlib.import_module("module")
                        if node.args and isinstance(node.args[0], ast.Constant):
                            result.imports.append(
                                ExtractedImport(
                                    file=relative_path,
                                    imported_path=str(node.args[0].value),
                                    imported_symbols=None,
                                    import_type="dynamic",
                                    line_number=node.lineno,
                                )
                            )

    def _extract_calls(
        self,
        tree: ast.AST,
        relative_path: str,
        result: ExtractionResult,
    ) -> None:
        """Extract function/method calls from AST.

        Args:
            tree: AST node to process
            relative_path: Repo-relative file path
            result: ExtractionResult to populate
        """
        # Build a map of functions/methods in this file for context
        symbol_map = self._build_symbol_map(tree)

        # Walk the AST to find all calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_info = self._analyze_call(node, symbol_map)
                if call_info:
                    callee_symbol, call_type, is_dynamic_code, callee_object = call_info

                    # Find the enclosing function/method
                    caller_symbol = self._find_enclosing_function(tree, node.lineno)

                    result.calls.append(
                        ExtractedCall(
                            caller_file=relative_path,
                            caller_symbol=caller_symbol or "<module>",
                            callee_symbol=callee_symbol,
                            callee_file=None,  # Phase 1: no resolution
                            line_number=node.lineno,
                            call_type=call_type,
                            is_dynamic_code_execution=is_dynamic_code,
                            callee_object=callee_object,
                        )
                    )

            elif isinstance(node, ast.Await):
                # Handle await expressions
                if isinstance(node.value, ast.Call):
                    call_info = self._analyze_call(node.value, symbol_map)
                    if call_info:
                        callee_symbol, _, is_dynamic_code, callee_object = call_info
                        caller_symbol = self._find_enclosing_function(tree, node.lineno)

                        result.calls.append(
                            ExtractedCall(
                                caller_file=relative_path,
                                caller_symbol=caller_symbol or "<module>",
                                callee_symbol=callee_symbol,
                                callee_file=None,
                                line_number=node.lineno,
                                call_type="async",
                                is_dynamic_code_execution=is_dynamic_code,
                                callee_object=callee_object,
                            )
                        )

    def _build_symbol_map(self, tree: ast.AST) -> dict[str, str]:
        """Build a map of symbol names to their types in the file.

        Args:
            tree: AST to analyze

        Returns:
            Dict mapping symbol names to their types
        """
        symbol_map: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                symbol_map[node.name] = "function"
            elif isinstance(node, ast.ClassDef):
                symbol_map[node.name] = "class"
        return symbol_map

    def _analyze_call(
        self,
        node: ast.Call,
        symbol_map: dict[str, str],
    ) -> tuple[str, str, bool, str | None] | None:
        """Analyze a call node to extract callee, call type, dynamic code flag, and callee object.

        Args:
            node: Call AST node
            symbol_map: Map of known symbols

        Returns:
            Tuple of (callee_symbol, call_type, is_dynamic_code_execution, callee_object) or None
        """
        func = node.func

        if isinstance(func, ast.Name):
            # Direct function call: foo()
            is_dynamic_code = func.id in DYNAMIC_CODE_BUILTINS
            return func.id, "direct", is_dynamic_code, None

        elif isinstance(func, ast.Attribute):
            # Method/attribute call: obj.method()
            callee_object = self._get_attribute_root_object(func)
            return func.attr, "dynamic", False, callee_object

        elif isinstance(func, ast.Subscript):
            # Subscript call: foo[0]() - rare but valid
            return None

        return None

    def _get_attribute_root_object(self, attr_node: ast.Attribute) -> str | None:
        """Get the root object name from an attribute chain.

        For `os.path.join()`, returns "os".
        For `self.method()`, returns "self".

        Args:
            attr_node: Attribute AST node

        Returns:
            Root object name or None if not a simple name
        """
        current = attr_node.value
        while isinstance(current, ast.Attribute):
            current = current.value
        if isinstance(current, ast.Name):
            return current.id
        return None

    def _find_enclosing_function(
        self,
        tree: ast.AST,
        target_line: int,
    ) -> str | None:
        """Find the innermost function/method containing a given line number.

        Args:
            tree: AST to search
            target_line: Line number to find enclosing function for

        Returns:
            Name of enclosing function/method, or None if at module level
        """
        # Collect all functions that contain the target line
        candidates: list[tuple[str, int, int]] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                start = node.lineno
                end = node.end_lineno or start
                if start <= target_line <= end:
                    candidates.append((node.name, start, end))

        if not candidates:
            return None

        # Return the innermost (smallest range) function
        # Sort by: 1) smallest range first, 2) latest start line (for tie-breaking)
        candidates.sort(key=lambda x: (x[2] - x[1], -x[1]))
        return candidates[0][0]
