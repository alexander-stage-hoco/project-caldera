"""Python tree-sitter based symbol extractor.

Alternative implementation using tree-sitter for comparison with the AST-based extractor.
Tree-sitter provides better error recovery for malformed code and enables future
multi-language support.
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
    from tree_sitter import Node, Tree

# Built-in functions that execute dynamic code
DYNAMIC_CODE_BUILTINS = frozenset({"eval", "exec", "compile"})


class TreeSitterExtractor(BaseExtractor):
    """Extract symbols, calls, and imports from Python source files using tree-sitter."""

    def __init__(self) -> None:
        """Initialize the tree-sitter parser."""
        from tree_sitter_language_pack import get_parser

        self._parser = get_parser("python")

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
            source = file_path.read_bytes()
        except UnicodeDecodeError as e:
            result.errors.append({
                "file": relative_path,
                "message": f"Encoding error: {e}",
                "code": "ENCODING_ERROR",
                "recoverable": True,
            })
            return result

        tree = self._parser.parse(source)

        # Check for syntax errors (tree-sitter still produces partial AST)
        if tree.root_node.has_error:
            # Tree-sitter recovers from errors, so we continue extraction
            # but record that errors were encountered
            result.errors.append({
                "file": relative_path,
                "message": "Syntax errors detected (partial extraction performed)",
                "code": "SYNTAX_ERROR",
                "recoverable": True,
            })

        # Extract all entities from the tree
        self._extract_from_tree(tree.root_node, relative_path, source, result)

        return result

    def _extract_from_tree(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        parent_class: str | None = None,
    ) -> None:
        """Recursively extract entities from a tree-sitter node.

        Args:
            node: Current tree-sitter node
            path: Repo-relative file path
            source: Source code bytes
            result: ExtractionResult to populate
            parent_class: Name of parent class (for method extraction)
        """
        if node.type == "function_definition":
            self._handle_function(node, path, source, result, parent_class)
        elif node.type == "class_definition":
            self._handle_class(node, path, source, result, parent_class)
        elif node.type == "call":
            self._handle_call(node, path, source, result)
        elif node.type == "await":
            self._handle_await(node, path, source, result)
        elif node.type == "import_statement":
            self._handle_import(node, path, source, result)
        elif node.type == "import_from_statement":
            self._handle_import_from(node, path, source, result)
        elif node.type == "future_import_statement":
            self._handle_future_import(node, path, source, result)
        elif node.type == "assignment":
            # Only module-level (direct child of module, not inside any control flow)
            # Note: augmented_assignment (+=, -=, etc.) is intentionally excluded
            # because it doesn't create new variables, only modifies existing ones
            if parent_class is None and self._is_module_level(node):
                self._handle_assignment(node, path, source, result)
        elif node.type == "annotated_assignment":
            # Only module-level (direct child of module, not inside any control flow)
            if parent_class is None and self._is_module_level(node):
                self._handle_annotated_assignment(node, path, source, result)

        # Recurse into children (except for nodes that handle their own recursion)
        # - class_definition: handled by _handle_class
        # - function_definition: handled by _handle_function
        if node.type not in ("class_definition", "function_definition"):
            for child in node.children:
                self._extract_from_tree(child, path, source, result, parent_class)

    def _handle_function(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        parent_class: str | None,
    ) -> None:
        """Handle function_definition node."""
        # Skip functions that have parse errors in their definition
        if node.has_error:
            return

        # Skip functions with empty blocks (often malformed code)
        body_node = self._find_child_by_type(node, "block")
        if body_node:
            named_children = [c for c in body_node.children if c.is_named]
            if not named_children:
                return

        name_node = self._find_child_by_type(node, "identifier")
        if not name_node:
            return

        name = self._get_node_text(name_node, source)
        symbol_type = "method" if parent_class else "function"
        is_exported = not name.startswith("_")

        # Get parameters
        params_node = self._find_child_by_type(node, "parameters")
        param_count = self._count_parameters(params_node, source, parent_class is not None)

        # Get docstring
        docstring = self._get_docstring(node, source)

        result.symbols.append(
            ExtractedSymbol(
                path=path,
                symbol_name=name,
                symbol_type=symbol_type,
                line_start=node.start_point[0] + 1,  # tree-sitter is 0-indexed
                line_end=node.end_point[0] + 1,
                is_exported=is_exported,
                parameters=param_count,
                parent_symbol=parent_class,
                docstring=docstring,
            )
        )

        # Process nested definitions (but keep same parent_class context for nested functions)
        for child in node.children:
            self._extract_from_tree(child, path, source, result, parent_class)

    def _handle_class(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        parent_class: str | None,
    ) -> None:
        """Handle class_definition node."""
        name_node = self._find_child_by_type(node, "identifier")
        if not name_node:
            return

        name = self._get_node_text(name_node, source)
        is_exported = not name.startswith("_")

        # Get docstring
        docstring = self._get_docstring(node, source)

        result.symbols.append(
            ExtractedSymbol(
                path=path,
                symbol_name=name,
                symbol_type="class",
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                is_exported=is_exported,
                parameters=None,
                parent_symbol=parent_class,
                docstring=docstring,
            )
        )

        # Process class body with this class as parent
        body_node = self._find_child_by_type(node, "block")
        if body_node:
            for child in body_node.children:
                self._extract_from_tree(child, path, source, result, name)

    def _handle_call(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
    ) -> None:
        """Handle call node."""
        # Skip if this call is inside an await (handled separately)
        if node.parent and node.parent.type == "await":
            return

        call_info = self._analyze_call_node(node, source)
        if call_info:
            callee_symbol, call_type, is_dynamic_code, callee_object = call_info
            caller_symbol = self._find_enclosing_function(node, source)

            result.calls.append(
                ExtractedCall(
                    caller_file=path,
                    caller_symbol=caller_symbol or "<module>",
                    callee_symbol=callee_symbol,
                    callee_file=None,  # Phase 1: no resolution
                    line_number=node.start_point[0] + 1,
                    call_type=call_type,
                    is_dynamic_code_execution=is_dynamic_code,
                    callee_object=callee_object,
                )
            )

    def _handle_await(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
    ) -> None:
        """Handle await node (async calls)."""
        # Find the call node inside the await
        call_node = self._find_child_by_type(node, "call")
        if not call_node:
            return

        call_info = self._analyze_call_node(call_node, source)
        if call_info:
            callee_symbol, _, is_dynamic_code, callee_object = call_info
            caller_symbol = self._find_enclosing_function(node, source)

            result.calls.append(
                ExtractedCall(
                    caller_file=path,
                    caller_symbol=caller_symbol or "<module>",
                    callee_symbol=callee_symbol,
                    callee_file=None,
                    line_number=node.start_point[0] + 1,
                    call_type="async",
                    is_dynamic_code_execution=is_dynamic_code,
                    callee_object=callee_object,
                )
            )

    def _handle_import(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
    ) -> None:
        """Handle import_statement node (import x, import x as y)."""
        for child in node.children:
            if child.type == "dotted_name":
                module_name = self._get_node_text(child, source)
                result.imports.append(
                    ExtractedImport(
                        file=path,
                        imported_path=module_name,
                        imported_symbols=None,
                        import_type="static",
                        line_number=node.start_point[0] + 1,
                    )
                )
            elif child.type == "aliased_import":
                name_node = self._find_child_by_type(child, "dotted_name")
                alias_node = self._find_child_by_type(child, "identifier")
                if name_node:
                    module_name = self._get_node_text(name_node, source)
                    # Extract the alias (the identifier after 'as')
                    module_alias = None
                    if alias_node:
                        module_alias = self._get_node_text(alias_node, source)
                    result.imports.append(
                        ExtractedImport(
                            file=path,
                            imported_path=module_name,
                            imported_symbols=None,
                            import_type="static",
                            line_number=node.start_point[0] + 1,
                            module_alias=module_alias,
                        )
                    )

    def _handle_import_from(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
    ) -> None:
        """Handle import_from_statement node (from x import y)."""
        # Get module path
        module_name_node = self._find_child_by_type(node, "dotted_name")
        relative_import_node = self._find_child_by_type(node, "relative_import")

        module_path = ""
        if relative_import_node:
            module_path = self._get_node_text(relative_import_node, source)
        elif module_name_node:
            module_path = self._get_node_text(module_name_node, source)

        # Check for dynamic imports: __import__() or importlib.import_module()
        # These are handled separately in _handle_call

        # Get imported symbols
        symbols = []
        for child in node.children:
            if child.type == "wildcard_import":
                symbols = ["*"]
                break
            elif child.type == "import_prefix":
                # Handle leading dots for relative imports
                module_path = self._get_node_text(child, source) + module_path
            elif child.type in ("dotted_name", "identifier"):
                # Skip the module name itself
                if child == module_name_node:
                    continue
                symbols.append(self._get_node_text(child, source))
            elif child.type == "aliased_import":
                # Handle "x as y" imports
                name_node = child.children[0] if child.children else None
                if name_node:
                    symbols.append(self._get_node_text(name_node, source))

        # Build symbols string
        if symbols == ["*"]:
            symbols_str = "*"
        elif symbols:
            symbols_str = ",".join(symbols)
        else:
            symbols_str = None

        # Determine import type (type_checking if inside TYPE_CHECKING block)
        import_type = (
            "type_checking"
            if self._is_in_type_checking_block(node, source)
            else "static"
        )

        result.imports.append(
            ExtractedImport(
                file=path,
                imported_path=module_path,
                imported_symbols=symbols_str,
                import_type=import_type,
                line_number=node.start_point[0] + 1,
            )
        )

    def _handle_future_import(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
    ) -> None:
        """Handle future_import_statement node (from __future__ import x)."""
        # Get imported symbols from dotted_name children
        symbols = []
        for child in node.children:
            if child.type == "dotted_name":
                symbols.append(self._get_node_text(child, source))

        symbols_str = ",".join(symbols) if symbols else None

        result.imports.append(
            ExtractedImport(
                file=path,
                imported_path="__future__",
                imported_symbols=symbols_str,
                import_type="static",
                line_number=node.start_point[0] + 1,
            )
        )

    def _handle_assignment(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
    ) -> None:
        """Handle assignment node (x = 1, x = y = 1, x, y = 1, 2).

        Args:
            node: Assignment node
            path: Repo-relative file path
            source: Source bytes
            result: ExtractionResult to populate
        """
        # Check for type annotation without value (x: int)
        # In tree-sitter, this appears as: assignment -> identifier, ":", type
        # Skip these as they don't create runtime variables
        has_equals = any(child.type == "=" for child in node.children)
        if not has_equals:
            return

        # Find left-hand side targets
        for child in node.children:
            if child.type in ("identifier", "pattern_list", "tuple_pattern", "list_pattern"):
                self._extract_variable_targets(child, node, path, source, result)

    def _handle_annotated_assignment(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
    ) -> None:
        """Handle annotated_assignment node (x: int = 1).

        Args:
            node: Annotated assignment node
            path: Repo-relative file path
            source: Source bytes
            result: ExtractionResult to populate
        """
        # Find the identifier (target)
        for child in node.children:
            if child.type == "identifier":
                self._extract_variable_targets(child, node, path, source, result)
                break  # Only first identifier is the target

    def _extract_variable_targets(
        self,
        target: Node,
        assign_node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
    ) -> None:
        """Extract variable names from assignment target.

        Args:
            target: Target node (identifier, pattern_list, or tuple_pattern)
            assign_node: Parent assignment node (for line numbers)
            path: Repo-relative file path
            source: Source bytes
            result: ExtractionResult to populate
        """
        if target.type == "identifier":
            name = self._get_node_text(target, source)
            # Skip dunder variables
            if name.startswith("__") and name.endswith("__"):
                return
            result.symbols.append(
                ExtractedSymbol(
                    path=path,
                    symbol_name=name,
                    symbol_type="variable",
                    line_start=assign_node.start_point[0] + 1,
                    line_end=assign_node.end_point[0] + 1,
                    is_exported=not name.startswith("_"),
                    parameters=None,
                    parent_symbol=None,
                    docstring=None,
                )
            )
        elif target.type in ("pattern_list", "tuple_pattern", "list_pattern"):
            for child in target.children:
                if child.is_named:
                    self._extract_variable_targets(child, assign_node, path, source, result)
        elif target.type == "list_splat_pattern":
            # Handle starred expression: first, *middle, last = range(10)
            for child in target.children:
                if child.type == "identifier":
                    self._extract_variable_targets(child, assign_node, path, source, result)

    def _is_inside_function(self, node: Node) -> bool:
        """Check if a node is inside a function definition.

        Args:
            node: Node to check

        Returns:
            True if inside a function definition
        """
        current = node.parent
        while current:
            if current.type == "function_definition":
                return True
            current = current.parent
        return False

    def _is_module_level(self, node: Node) -> bool:
        """Check if a node is at module level (direct child of module).

        Args:
            node: Node to check

        Returns:
            True if the node is at module level (not inside any control flow, class, or function)
        """
        current = node.parent
        while current:
            # If we reach the module, we're at module level
            if current.type == "module":
                return True
            # If we're inside a function, class, or control flow, not module level
            if current.type in (
                "function_definition",
                "class_definition",
                "if_statement",
                "for_statement",
                "while_statement",
                "try_statement",
                "with_statement",
                "match_statement",
            ):
                return False
            current = current.parent
        return False

    def _analyze_call_node(
        self,
        node: Node,
        source: bytes,
    ) -> tuple[str, str, bool, str | None] | None:
        """Analyze a call node to extract callee, call type, dynamic code flag, and callee object.

        Args:
            node: Call node
            source: Source bytes

        Returns:
            Tuple of (callee_symbol, call_type, is_dynamic_code_execution, callee_object) or None
        """
        # Get the function being called (first child is typically the callable)
        func_node = node.children[0] if node.children else None
        if not func_node:
            return None

        if func_node.type == "identifier":
            # Direct call: func()
            callee = self._get_node_text(func_node, source)
            is_dynamic_code = callee in DYNAMIC_CODE_BUILTINS
            return callee, "direct", is_dynamic_code, None

        elif func_node.type == "attribute":
            # Method/attribute call: obj.method() or obj.nested.call()
            # The last identifier in the attribute chain is the method name
            method_name = self._get_attribute_method_name(func_node, source)
            callee_object = self._get_attribute_root_object(func_node, source)
            if method_name:
                return method_name, "dynamic", False, callee_object

        return None

    def _get_attribute_root_object(self, attr_node: Node, source: bytes) -> str | None:
        """Get the root object name from an attribute chain.

        For `os.path.join()`, returns "os".
        For `self.method()`, returns "self".

        Args:
            attr_node: Attribute node
            source: Source bytes

        Returns:
            Root object name or None if not a simple identifier
        """
        # Navigate to the leftmost part of the attribute chain
        current = attr_node
        while True:
            # In tree-sitter Python grammar, attribute structure is:
            # attribute: (object, ".", identifier)
            # Find the object (first named child that isn't an identifier after dot)
            children = [c for c in current.children if c.is_named]
            if not children:
                return None

            first_child = children[0]
            if first_child.type == "identifier":
                return self._get_node_text(first_child, source)
            elif first_child.type == "attribute":
                current = first_child
            else:
                # Complex expression (e.g., function call result)
                return None

    def _get_attribute_method_name(self, attr_node: Node, source: bytes) -> str | None:
        """Get the method name from an attribute node.

        For `obj.method`, returns "method".
        For `obj.nested.call`, returns "call".

        Args:
            attr_node: Attribute node
            source: Source bytes

        Returns:
            Method name or None
        """
        # In tree-sitter Python grammar, attribute structure is:
        # attribute: (object, ".", identifier)
        # For nested: attribute: (attribute, ".", identifier)
        # The last identifier child is always the method/attribute name
        identifiers = [
            child for child in attr_node.children
            if child.type == "identifier"
        ]
        if identifiers:
            # Return the last identifier (the one after the last dot)
            return self._get_node_text(identifiers[-1], source)
        return None

    def _find_enclosing_function(self, node: Node, source: bytes) -> str | None:
        """Find the name of the enclosing function/method.

        Args:
            node: Node to find enclosing function for
            source: Source bytes

        Returns:
            Name of enclosing function or None if at module level
        """
        current = node.parent
        while current:
            if current.type == "function_definition":
                name_node = self._find_child_by_type(current, "identifier")
                if name_node:
                    return self._get_node_text(name_node, source)
            current = current.parent
        return None

    def _count_parameters(
        self,
        params_node: Node | None,
        source: bytes,
        is_method: bool,
    ) -> int:
        """Count parameters in a parameter list.

        Args:
            params_node: Parameters node
            source: Source bytes
            is_method: Whether this is a method (to exclude self/cls)

        Returns:
            Parameter count
        """
        if not params_node:
            return 0

        count = 0
        first_param = True

        for child in params_node.children:
            # Note: We intentionally do NOT count *args (list_splat_pattern)
            # or **kwargs (dictionary_splat_pattern) to match AST behavior
            if child.type in (
                "identifier",  # Simple param
                "typed_parameter",  # param: type
                "default_parameter",  # param=value
                "typed_default_parameter",  # param: type = value
            ):
                # Skip typed varargs (*args: T, **kwargs: T) to match AST behavior
                if child.type == "typed_parameter":
                    if self._find_child_by_type(child, "list_splat_pattern"):
                        continue
                    if self._find_child_by_type(child, "dictionary_splat_pattern"):
                        continue

                # Skip self/cls for methods
                if first_param and is_method:
                    first_param = False
                    if child.type == "identifier":
                        param_name = self._get_node_text(child, source)
                        if param_name in ("self", "cls"):
                            continue
                    elif child.type == "typed_parameter":
                        name_node = self._find_child_by_type(child, "identifier")
                        if name_node:
                            param_name = self._get_node_text(name_node, source)
                            if param_name in ("self", "cls"):
                                continue

                count += 1
                first_param = False

        return count

    def _get_docstring(self, node: Node, source: bytes) -> str | None:
        """Extract docstring from a function or class definition.

        Args:
            node: Function or class definition node
            source: Source bytes

        Returns:
            Docstring text or None
        """
        body_node = self._find_child_by_type(node, "block")
        if not body_node:
            return None

        # Find first string in block (may be direct child or in expression_statement)
        for child in body_node.children:
            # Handle direct string node (newer tree-sitter)
            if child.type == "string":
                return self._extract_string_content(child, source)

            # Handle expression_statement wrapper (older tree-sitter)
            if child.type == "expression_statement":
                for subchild in child.children:
                    if subchild.type == "string":
                        return self._extract_string_content(subchild, source)
                break  # Only check first statement

            # Skip other statement types - docstring must be first
            if child.type not in ("string", "expression_statement"):
                # Skip newlines, indentation nodes, etc.
                if not child.is_named:
                    continue
                break

        return None

    def _extract_string_content(self, string_node: Node, source: bytes) -> str | None:
        """Extract the content from a string node.

        Args:
            string_node: A tree-sitter string node
            source: Source bytes

        Returns:
            String content without quotes, or None
        """
        # Look for string_content child (newer tree-sitter structure)
        for child in string_node.children:
            if child.type == "string_content":
                return self._get_node_text(child, source).strip()

        # Fallback: extract full text and remove quotes
        text = self._get_node_text(string_node, source)
        if text.startswith('"""') or text.startswith("'''"):
            return text[3:-3].strip()
        elif text.startswith('"') or text.startswith("'"):
            return text[1:-1].strip()

        return None

    def _get_node_text(self, node: Node, source: bytes) -> str:
        """Get the text content of a node.

        Args:
            node: Tree-sitter node
            source: Source bytes

        Returns:
            Text content as string
        """
        return source[node.start_byte:node.end_byte].decode("utf-8")

    def _find_child_by_type(self, node: Node, type_name: str) -> Node | None:
        """Find the first child with a given type.

        Args:
            node: Parent node
            type_name: Node type to find

        Returns:
            Child node or None
        """
        for child in node.children:
            if child.type == type_name:
                return child
        return None

    def _is_in_type_checking_block(self, node: Node, source: bytes) -> bool:
        """Check if node is inside an 'if TYPE_CHECKING:' block.

        Args:
            node: Node to check
            source: Source bytes

        Returns:
            True if inside TYPE_CHECKING block
        """
        current = node.parent
        while current:
            if current.type == "if_statement":
                # Check if condition is TYPE_CHECKING
                for child in current.children:
                    if child.type == "identifier":
                        if self._get_node_text(child, source) == "TYPE_CHECKING":
                            return True
                        break  # Condition checked, not TYPE_CHECKING
            current = current.parent
        return False
