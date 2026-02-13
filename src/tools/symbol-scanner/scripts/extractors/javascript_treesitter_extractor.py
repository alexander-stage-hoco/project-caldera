"""JavaScript tree-sitter based symbol extractor.

Tree-sitter implementation for extracting symbols, calls, and imports from
JavaScript source files. Provides good error recovery for malformed code.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .base import (
    BaseExtractor,
    ExtractedCall,
    ExtractedImport,
    ExtractedSymbol,
    ExtractionResult,
)

if TYPE_CHECKING:
    from tree_sitter import Node


# Dynamic code execution functions in JS
DYNAMIC_EXEC_FUNCTIONS = frozenset({"eval", "Function"})


class JavaScriptTreeSitterExtractor(BaseExtractor):
    """Extract symbols, calls, and imports from JavaScript source files using tree-sitter."""

    def __init__(self) -> None:
        """Initialize the tree-sitter parser."""
        from tree_sitter_language_pack import get_parser

        self._parser = get_parser("javascript")

    @property
    def language(self) -> str:
        return "javascript"

    @property
    def file_extensions(self) -> tuple[str, ...]:
        return (".js", ".mjs", ".cjs", ".jsx")

    def extract_file(self, file_path: Path, relative_path: str) -> ExtractionResult:
        """Extract symbols, calls, and imports from a JavaScript file."""
        result = ExtractionResult()

        try:
            source = file_path.read_bytes()
        except (UnicodeDecodeError, OSError) as e:
            result.errors.append({
                "file": relative_path,
                "message": f"Read error: {e}",
                "code": "READ_ERROR",
                "recoverable": True,
            })
            return result

        tree = self._parser.parse(source)

        if tree.root_node.has_error:
            result.errors.append({
                "file": relative_path,
                "message": "Syntax errors detected (partial extraction performed)",
                "code": "SYNTAX_ERROR",
                "recoverable": True,
            })

        self._extract_from_tree(tree.root_node, relative_path, source, result)
        return result

    def _extract_from_tree(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        parent_class: str | None = None,
        is_exported: bool = False,
    ) -> None:
        """Recursively extract entities from a tree-sitter node."""
        for child in node.children:
            node_type = child.type

            # Export statements wrap declarations
            if node_type == "export_statement":
                self._handle_export_statement(child, path, source, result, parent_class)

            # Function declarations
            elif node_type == "function_declaration":
                self._handle_function_declaration(
                    child, path, source, result, is_exported=is_exported,
                )

            # Generator function declarations
            elif node_type == "generator_function_declaration":
                self._handle_function_declaration(
                    child, path, source, result, is_exported=is_exported,
                )

            # Class declarations
            elif node_type == "class_declaration":
                self._handle_class_declaration(
                    child, path, source, result, is_exported=is_exported,
                )

            # Variable declarations at module level (const/let/var)
            elif node_type in ("lexical_declaration", "variable_declaration"):
                self._handle_variable_declaration(
                    child, path, source, result, parent_class=parent_class,
                    is_exported=is_exported,
                )

            # Import statements
            elif node_type == "import_statement":
                self._handle_import_statement(child, path, source, result)

            # Expression statements (top-level calls, new expressions)
            elif node_type == "expression_statement":
                self._extract_calls_from_node(
                    child, path, source, result, parent_class=parent_class,
                )

    def _handle_export_statement(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        parent_class: str | None = None,
    ) -> None:
        """Handle export statement - extract the inner declaration as exported."""
        is_default = any(c.type == "default" for c in node.children)

        for child in node.children:
            if child.type == "function_declaration":
                self._handle_function_declaration(
                    child, path, source, result, is_exported=True,
                )
            elif child.type == "generator_function_declaration":
                self._handle_function_declaration(
                    child, path, source, result, is_exported=True,
                )
            elif child.type == "class_declaration":
                self._handle_class_declaration(
                    child, path, source, result, is_exported=True,
                )
            elif child.type in ("lexical_declaration", "variable_declaration"):
                self._handle_variable_declaration(
                    child, path, source, result, parent_class=parent_class,
                    is_exported=True,
                )

    def _handle_function_declaration(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        is_exported: bool = False,
    ) -> None:
        """Handle function or generator function declaration."""
        name_node = self._find_child_by_type(node, "identifier")
        if not name_node:
            return

        name = self._get_node_text(name_node, source)
        is_async = any(c.type == "async" for c in node.children)
        params = self._count_parameters(node)
        docstring = self._get_jsdoc_comment(node, source)

        result.symbols.append(ExtractedSymbol(
            path=path,
            symbol_name=name,
            symbol_type="function",
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            is_exported=is_exported,
            parameters=params,
            parent_symbol=None,
            docstring=docstring,
        ))

        # Extract calls from function body
        body = self._find_child_by_type(node, "statement_block")
        if body:
            self._extract_calls_from_node(body, path, source, result, enclosing_func=name)

    def _handle_class_declaration(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        is_exported: bool = False,
    ) -> None:
        """Handle class declaration."""
        name_node = self._find_child_by_type(node, "identifier")
        if not name_node:
            # TS uses type_identifier
            name_node = self._find_child_by_type(node, "type_identifier")
        if not name_node:
            return

        name = self._get_node_text(name_node, source)
        docstring = self._get_jsdoc_comment(node, source)

        result.symbols.append(ExtractedSymbol(
            path=path,
            symbol_name=name,
            symbol_type="class",
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            is_exported=is_exported,
            parameters=None,
            parent_symbol=None,
            docstring=docstring,
        ))

        # Process class body
        body = self._find_child_by_type(node, "class_body")
        if body:
            self._extract_class_members(body, path, source, result, class_name=name)

    def _extract_class_members(
        self,
        body: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        class_name: str,
    ) -> None:
        """Extract methods and fields from class body."""
        for child in body.children:
            if child.type == "method_definition":
                self._handle_method_definition(
                    child, path, source, result, class_name=class_name,
                )
            elif child.type in ("public_field_definition", "field_definition"):
                self._handle_class_field(
                    child, path, source, result, class_name=class_name,
                )

    def _handle_method_definition(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        class_name: str,
    ) -> None:
        """Handle method definition inside class body."""
        name_node = self._find_child_by_type(node, "property_identifier")
        if not name_node:
            name_node = self._find_child_by_type(node, "private_property_identifier")
        if not name_node:
            name_node = self._find_child_by_type(node, "identifier")
        if not name_node:
            # Could be computed property [expr]()
            return

        name = self._get_node_text(name_node, source)
        is_private = name.startswith("#")
        is_static = any(c.type == "static" for c in node.children)
        params = self._count_parameters(node)
        docstring = self._get_jsdoc_comment(node, source)

        # Special handling for constructor
        symbol_type = "method"

        result.symbols.append(ExtractedSymbol(
            path=path,
            symbol_name=name,
            symbol_type=symbol_type,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            is_exported=not is_private,
            parameters=params,
            parent_symbol=class_name,
            docstring=docstring,
        ))

        # Extract calls from method body
        body = self._find_child_by_type(node, "statement_block")
        if body:
            self._extract_calls_from_node(
                body, path, source, result, enclosing_func=name, parent_class=class_name,
            )

    def _handle_class_field(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        class_name: str,
    ) -> None:
        """Handle class field (public_field_definition)."""
        name_node = self._find_child_by_type(node, "property_identifier")
        if not name_node:
            return

        name = self._get_node_text(name_node, source)
        is_private = name.startswith("#")

        result.symbols.append(ExtractedSymbol(
            path=path,
            symbol_name=name,
            symbol_type="variable",
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            is_exported=not is_private,
            parameters=None,
            parent_symbol=class_name,
            docstring=None,
        ))

    def _handle_variable_declaration(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        parent_class: str | None = None,
        is_exported: bool = False,
    ) -> None:
        """Handle const/let/var declarations at module level."""
        for child in node.children:
            if child.type != "variable_declarator":
                continue

            name_node = self._find_child_by_type(child, "identifier")
            if not name_node:
                continue

            name = self._get_node_text(name_node, source)

            # Check if value is an arrow function or function expression
            value_node = None
            for vc in child.children:
                if vc.type in ("arrow_function", "function_expression",
                               "generator_function"):
                    value_node = vc
                    break

            if value_node:
                # This is a function assigned to a variable
                params = self._count_parameters(value_node)
                docstring = self._get_jsdoc_comment(node, source)

                result.symbols.append(ExtractedSymbol(
                    path=path,
                    symbol_name=name,
                    symbol_type="function",
                    line_start=node.start_point[0] + 1,
                    line_end=node.end_point[0] + 1,
                    is_exported=is_exported,
                    parameters=params,
                    parent_symbol=parent_class,
                    docstring=docstring,
                ))

                # Extract calls from function body
                body = self._find_child_by_type(value_node, "statement_block")
                if body:
                    self._extract_calls_from_node(
                        body, path, source, result, enclosing_func=name,
                    )
                else:
                    # Arrow function with expression body (no block)
                    self._extract_calls_from_node(
                        value_node, path, source, result, enclosing_func=name,
                    )
            else:
                # Regular variable
                result.symbols.append(ExtractedSymbol(
                    path=path,
                    symbol_name=name,
                    symbol_type="variable",
                    line_start=node.start_point[0] + 1,
                    line_end=node.end_point[0] + 1,
                    is_exported=is_exported,
                    parameters=None,
                    parent_symbol=parent_class,
                    docstring=None,
                ))

                # Extract calls from initializer
                self._extract_calls_from_node(
                    child, path, source, result,
                    enclosing_func="<module>",
                )

    # ========================================================================
    # Call extraction
    # ========================================================================

    def _extract_calls_from_node(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        enclosing_func: str = "<module>",
        parent_class: str | None = None,
    ) -> None:
        """Recursively extract call expressions from a node."""
        for child in node.children:
            if child.type == "call_expression":
                self._handle_call_expression(
                    child, path, source, result,
                    enclosing_func=enclosing_func,
                    parent_class=parent_class,
                )
            elif child.type == "new_expression":
                self._handle_new_expression(
                    child, path, source, result,
                    enclosing_func=enclosing_func,
                    parent_class=parent_class,
                )
            elif child.type == "await_expression":
                # Unwrap await to find the call inside
                self._handle_await_expression(
                    child, path, source, result,
                    enclosing_func=enclosing_func,
                    parent_class=parent_class,
                )
            else:
                # Recurse into other nodes to find nested calls
                self._extract_calls_from_node(
                    child, path, source, result,
                    enclosing_func=enclosing_func,
                    parent_class=parent_class,
                )

    def _handle_call_expression(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        enclosing_func: str = "<module>",
        parent_class: str | None = None,
    ) -> None:
        """Handle a call expression node."""
        if not node.children:
            return

        func_node = node.children[0]
        callee_symbol = None
        callee_object = None
        call_type = "direct"
        is_dynamic_exec = False

        if func_node.type == "identifier":
            # Simple call: foo()
            callee_symbol = self._get_node_text(func_node, source)
            if callee_symbol in DYNAMIC_EXEC_FUNCTIONS:
                is_dynamic_exec = True

        elif func_node.type == "member_expression":
            # Member call: obj.method()
            obj_node = self._find_child_by_type(func_node, "identifier")
            prop_node = self._find_child_by_type(func_node, "property_identifier")
            if prop_node:
                callee_symbol = self._get_node_text(prop_node, source)
                call_type = "dynamic"
                if obj_node:
                    callee_object = self._get_node_text(obj_node, source)
                else:
                    # Chained: a.b.c() -> get leftmost identifier
                    callee_object = self._get_leftmost_identifier(func_node, source)

        elif func_node.type == "import":
            # Dynamic import: import("./mod")
            args_node = self._find_child_by_type(node, "arguments")
            if args_node:
                for arg_child in args_node.children:
                    if arg_child.type == "string":
                        import_path = self._get_string_content(arg_child, source)
                        if import_path:
                            result.imports.append(ExtractedImport(
                                file=path,
                                imported_path=import_path,
                                imported_symbols=None,
                                import_type="dynamic",
                                line_number=node.start_point[0] + 1,
                            ))
            return  # Dynamic imports are handled as imports, not calls

        elif func_node.type == "optional_chain_expression":
            # Optional chaining: obj?.method()
            callee_symbol, callee_object = self._analyze_optional_chain(
                func_node, source,
            )
            if callee_symbol:
                call_type = "dynamic"

        if callee_symbol:
            # Check for require() - treat as dynamic import
            if callee_symbol == "require" and not callee_object:
                args_node = self._find_child_by_type(node, "arguments")
                if args_node:
                    for arg_child in args_node.children:
                        if arg_child.type == "string":
                            import_path = self._get_string_content(arg_child, source)
                            if import_path:
                                result.imports.append(ExtractedImport(
                                    file=path,
                                    imported_path=import_path,
                                    imported_symbols=None,
                                    import_type="dynamic",
                                    line_number=node.start_point[0] + 1,
                                ))
                return  # require() is an import, not a call

            result.calls.append(ExtractedCall(
                caller_file=path,
                caller_symbol=enclosing_func,
                callee_symbol=callee_symbol,
                callee_file=None,
                line_number=node.start_point[0] + 1,
                call_type=call_type,
                is_dynamic_code_execution=is_dynamic_exec,
                callee_object=callee_object,
            ))

        # Recurse into arguments for nested calls
        args_node = self._find_child_by_type(node, "arguments")
        if args_node:
            self._extract_calls_from_node(
                args_node, path, source, result,
                enclosing_func=enclosing_func,
                parent_class=parent_class,
            )

        # Recurse into chained calls: foo().bar()
        if func_node.type == "call_expression":
            self._handle_call_expression(
                func_node, path, source, result,
                enclosing_func=enclosing_func,
                parent_class=parent_class,
            )

    def _handle_new_expression(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        enclosing_func: str = "<module>",
        parent_class: str | None = None,
    ) -> None:
        """Handle new expression: new Foo(args)."""
        # Find the constructor name (first child after 'new')
        for child in node.children:
            if child.type == "identifier":
                callee_symbol = self._get_node_text(child, source)
                result.calls.append(ExtractedCall(
                    caller_file=path,
                    caller_symbol=enclosing_func,
                    callee_symbol=callee_symbol,
                    callee_file=None,
                    line_number=node.start_point[0] + 1,
                    call_type="constructor",
                ))
                break
            elif child.type == "member_expression":
                # new ns.Foo()
                prop_node = self._find_child_by_type(child, "property_identifier")
                if prop_node:
                    callee_symbol = self._get_node_text(prop_node, source)
                    obj_node = self._find_child_by_type(child, "identifier")
                    callee_object = (
                        self._get_node_text(obj_node, source) if obj_node else None
                    )
                    result.calls.append(ExtractedCall(
                        caller_file=path,
                        caller_symbol=enclosing_func,
                        callee_symbol=callee_symbol,
                        callee_file=None,
                        line_number=node.start_point[0] + 1,
                        call_type="constructor",
                        callee_object=callee_object,
                    ))
                break

        # Recurse into arguments
        args_node = self._find_child_by_type(node, "arguments")
        if args_node:
            self._extract_calls_from_node(
                args_node, path, source, result,
                enclosing_func=enclosing_func,
                parent_class=parent_class,
            )

    def _handle_await_expression(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        enclosing_func: str = "<module>",
        parent_class: str | None = None,
    ) -> None:
        """Handle await expression - mark inner call as async."""
        for child in node.children:
            if child.type == "call_expression":
                # Extract the call but mark it as async
                call_before = len(result.calls)
                self._handle_call_expression(
                    child, path, source, result,
                    enclosing_func=enclosing_func,
                    parent_class=parent_class,
                )
                # Mark newly added calls as async
                for i in range(call_before, len(result.calls)):
                    call = result.calls[i]
                    result.calls[i] = ExtractedCall(
                        caller_file=call.caller_file,
                        caller_symbol=call.caller_symbol,
                        callee_symbol=call.callee_symbol,
                        callee_file=call.callee_file,
                        line_number=call.line_number,
                        call_type="async",
                        is_dynamic_code_execution=call.is_dynamic_code_execution,
                        callee_object=call.callee_object,
                    )
            else:
                self._extract_calls_from_node(
                    child, path, source, result,
                    enclosing_func=enclosing_func,
                    parent_class=parent_class,
                )

    # ========================================================================
    # Import extraction
    # ========================================================================

    def _handle_import_statement(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
    ) -> None:
        """Handle import statement."""
        # Get the module path (string node)
        module_path = None
        for child in node.children:
            if child.type == "string":
                module_path = self._get_string_content(child, source)
                break

        if not module_path:
            return

        # Determine import type and symbols
        import_clause = self._find_child_by_type(node, "import_clause")
        is_type_import = self._is_type_import(node)

        if not import_clause:
            # Side-effect import: import "./styles.css"
            result.imports.append(ExtractedImport(
                file=path,
                imported_path=module_path,
                imported_symbols=None,
                import_type="side_effect",
                line_number=node.start_point[0] + 1,
            ))
            return

        import_type = "type_checking" if is_type_import else "static"

        for child in import_clause.children:
            if child.type == "identifier":
                # Default import: import x from "./mod"
                alias = self._get_node_text(child, source)
                result.imports.append(ExtractedImport(
                    file=path,
                    imported_path=module_path,
                    imported_symbols=None,
                    import_type=import_type,
                    line_number=node.start_point[0] + 1,
                    module_alias=alias,
                ))

            elif child.type == "named_imports":
                # Named imports: import { a, b } from "./mod"
                symbols = self._extract_named_imports(child, source)
                if symbols:
                    result.imports.append(ExtractedImport(
                        file=path,
                        imported_path=module_path,
                        imported_symbols=",".join(symbols),
                        import_type=import_type,
                        line_number=node.start_point[0] + 1,
                    ))

            elif child.type == "namespace_import":
                # Star import: import * as ns from "./mod"
                alias_node = self._find_child_by_type(child, "identifier")
                alias = self._get_node_text(alias_node, source) if alias_node else None
                result.imports.append(ExtractedImport(
                    file=path,
                    imported_path=module_path,
                    imported_symbols="*",
                    import_type=import_type,
                    line_number=node.start_point[0] + 1,
                    module_alias=alias,
                ))

    def _is_type_import(self, node: Node) -> bool:
        """Check if import has 'type' keyword (TS only)."""
        for child in node.children:
            if child.type == "type":
                return True
        return False

    def _extract_named_imports(self, node: Node, source: bytes) -> list[str]:
        """Extract symbol names from named_imports node."""
        symbols = []
        for child in node.children:
            if child.type == "import_specifier":
                # Get the imported name (may have alias)
                names = [
                    c for c in child.children
                    if c.type in ("identifier", "type_identifier")
                ]
                if len(names) >= 2:
                    # import { foo as bar } -> "foo as bar"
                    original = self._get_node_text(names[0], source)
                    alias = self._get_node_text(names[-1], source)
                    symbols.append(f"{original} as {alias}")
                elif names:
                    symbols.append(self._get_node_text(names[0], source))
        return symbols

    # ========================================================================
    # Helper methods
    # ========================================================================

    def _analyze_optional_chain(
        self, node: Node, source: bytes,
    ) -> tuple[str | None, str | None]:
        """Analyze optional chain expression for callee info."""
        # obj?.method() -> member_expression inside optional_chain_expression
        for child in node.children:
            if child.type == "member_expression":
                prop_node = self._find_child_by_type(child, "property_identifier")
                obj_node = self._find_child_by_type(child, "identifier")
                if prop_node:
                    callee = self._get_node_text(prop_node, source)
                    obj = self._get_node_text(obj_node, source) if obj_node else None
                    return callee, obj
        return None, None

    def _get_leftmost_identifier(self, node: Node, source: bytes) -> str | None:
        """Walk member_expression chain to find the leftmost identifier."""
        current = node
        while current:
            if current.type == "identifier":
                return self._get_node_text(current, source)
            obj_child = None
            for child in current.children:
                if child.type in ("identifier", "member_expression", "this"):
                    obj_child = child
                    break
            if obj_child and obj_child.type == "identifier":
                return self._get_node_text(obj_child, source)
            if obj_child and obj_child.type == "this":
                return "this"
            current = obj_child
        return None

    def _get_jsdoc_comment(self, node: Node, source: bytes) -> str | None:
        """Extract JSDoc comment preceding a node."""
        prev = node.prev_named_sibling
        if not prev:
            # Check parent (for export_statement wrapping)
            if node.parent and node.parent.type == "export_statement":
                prev = node.parent.prev_named_sibling

        if prev and prev.type == "comment":
            text = self._get_node_text(prev, source)
            if text.startswith("/**"):
                return self._parse_jsdoc(text)

        return None

    def _parse_jsdoc(self, text: str) -> str | None:
        """Parse JSDoc comment to extract description."""
        # Strip /** and */
        text = text.strip()
        if text.startswith("/**"):
            text = text[3:]
        if text.endswith("*/"):
            text = text[:-2]

        lines = []
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("*"):
                line = line[1:].strip()
            # Stop at first @tag
            if line.startswith("@"):
                break
            if line:
                lines.append(line)

        return " ".join(lines) if lines else None

    def _count_parameters(self, node: Node) -> int:
        """Count function/method parameters."""
        params_node = self._find_child_by_type(node, "formal_parameters")
        if not params_node:
            return 0

        count = 0
        for child in params_node.children:
            if child.type in (
                "identifier", "assignment_pattern", "rest_pattern",
                "object_pattern", "array_pattern",
                # TS-specific
                "required_parameter", "optional_parameter", "rest_parameter",
            ):
                count += 1
        return count

    def _get_string_content(self, node: Node, source: bytes) -> str | None:
        """Get the string content from a string node (without quotes)."""
        for child in node.children:
            if child.type == "string_fragment":
                return self._get_node_text(child, source)
        return None

    def _get_node_text(self, node: Node, source: bytes) -> str:
        """Get source text from a node."""
        return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

    def _find_child_by_type(self, node: Node, child_type: str) -> Node | None:
        """Find first child of a given type."""
        for child in node.children:
            if child.type == child_type:
                return child
        return None
