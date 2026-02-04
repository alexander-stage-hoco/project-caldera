"""C# tree-sitter based symbol extractor.

Tree-sitter implementation for extracting symbols, calls, and imports from C# source files.
Provides good error recovery for malformed code.
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


# C# access modifiers that indicate exported/public visibility
PUBLIC_MODIFIERS = frozenset({"public", "internal", "protected"})
PRIVATE_MODIFIERS = frozenset({"private"})


class CSharpTreeSitterExtractor(BaseExtractor):
    """Extract symbols, calls, and imports from C# source files using tree-sitter."""

    def __init__(self) -> None:
        """Initialize the tree-sitter parser."""
        import tree_sitter_c_sharp as ts_csharp
        from tree_sitter import Language, Parser

        self._parser = Parser(Language(ts_csharp.language()))

    @property
    def language(self) -> str:
        return "csharp"

    @property
    def file_extensions(self) -> tuple[str, ...]:
        return (".cs",)

    def extract_file(self, file_path: Path, relative_path: str) -> ExtractionResult:
        """Extract symbols, calls, and imports from a C# file.

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
        namespace: str | None = None,
    ) -> None:
        """Recursively extract entities from a tree-sitter node.

        Args:
            node: Current tree-sitter node
            path: Repo-relative file path
            source: Source code bytes
            result: ExtractionResult to populate
            parent_class: Name of parent class (for method/property extraction)
            namespace: Current namespace context
        """
        # Handle namespace declarations
        if node.type == "namespace_declaration":
            ns_name = self._get_namespace_name(node, source)
            new_namespace = f"{namespace}.{ns_name}" if namespace else ns_name
            for child in node.children:
                self._extract_from_tree(child, path, source, result, parent_class, new_namespace)
            return

        # Handle file-scoped namespaces (C# 10+)
        if node.type == "file_scoped_namespace_declaration":
            ns_name = self._get_namespace_name(node, source)
            new_namespace = f"{namespace}.{ns_name}" if namespace else ns_name
            for child in node.children:
                self._extract_from_tree(child, path, source, result, parent_class, new_namespace)
            return

        # Type declarations
        if node.type in ("class_declaration", "struct_declaration", "interface_declaration", "record_declaration"):
            self._handle_type_declaration(node, path, source, result, parent_class, namespace)
            return

        # Enum declarations
        if node.type == "enum_declaration":
            self._handle_enum_declaration(node, path, source, result, parent_class, namespace)
            return

        # Method declarations
        if node.type == "method_declaration":
            self._handle_method(node, path, source, result, parent_class)

        # Constructor declarations
        elif node.type == "constructor_declaration":
            self._handle_constructor(node, path, source, result, parent_class)

        # Property declarations
        elif node.type == "property_declaration":
            self._handle_property(node, path, source, result, parent_class)

        # Field declarations
        elif node.type == "field_declaration":
            self._handle_field(node, path, source, result, parent_class)

        # Event declarations
        elif node.type == "event_declaration":
            self._handle_event(node, path, source, result, parent_class)

        # Event field declarations (e.g., public event EventHandler MyEvent;)
        elif node.type == "event_field_declaration":
            self._handle_event_field(node, path, source, result, parent_class)

        # Call expressions
        elif node.type == "invocation_expression":
            self._handle_invocation(node, path, source, result)
            # Continue recursion to find nested/chained calls

        # Object creation (new Foo())
        elif node.type == "object_creation_expression":
            self._handle_object_creation(node, path, source, result)
            # Continue recursion to find calls in arguments

        # Using directives (imports)
        elif node.type == "using_directive":
            self._handle_using_directive(node, path, source, result)

        # Extern alias directive
        elif node.type == "extern_alias_directive":
            self._handle_extern_alias(node, path, source, result)

        # Recurse into children for nodes that don't handle their own recursion
        if node.type not in (
            "class_declaration",
            "struct_declaration",
            "interface_declaration",
            "record_declaration",
            "enum_declaration",
            "namespace_declaration",
            "file_scoped_namespace_declaration",
            # These handle their own body traversal
            "method_declaration",
            "constructor_declaration",
            "property_declaration",
        ):
            for child in node.children:
                self._extract_from_tree(child, path, source, result, parent_class, namespace)

    def _handle_type_declaration(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        parent_class: str | None,
        namespace: str | None,
    ) -> None:
        """Handle class, struct, interface, or record declaration."""
        name_node = self._find_child_by_type(node, "identifier")
        if not name_node:
            return

        name = self._get_node_text(name_node, source)
        is_exported = self._is_exported(node, source)

        # Get XML doc comment if present
        docstring = self._get_xml_doc_comment(node, source)

        result.symbols.append(
            ExtractedSymbol(
                path=path,
                symbol_name=name,
                symbol_type="class",  # All type declarations map to "class"
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                is_exported=is_exported,
                parameters=None,
                parent_symbol=parent_class,
                docstring=docstring,
            )
        )

        # Process type body with this type as parent
        body_node = self._find_child_by_type(node, "declaration_list")
        if body_node:
            for child in body_node.children:
                self._extract_from_tree(child, path, source, result, name, namespace)

    def _handle_enum_declaration(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        parent_class: str | None,
        namespace: str | None,
    ) -> None:
        """Handle enum declaration."""
        name_node = self._find_child_by_type(node, "identifier")
        if not name_node:
            return

        name = self._get_node_text(name_node, source)
        is_exported = self._is_exported(node, source)
        docstring = self._get_xml_doc_comment(node, source)

        result.symbols.append(
            ExtractedSymbol(
                path=path,
                symbol_name=name,
                symbol_type="class",  # Enums map to "class" for consistency
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                is_exported=is_exported,
                parameters=None,
                parent_symbol=parent_class,
                docstring=docstring,
            )
        )

    def _handle_method(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        parent_class: str | None,
    ) -> None:
        """Handle method declaration."""
        # Method structure: [modifiers] return_type identifier parameter_list block
        # Find identifier AFTER return type (not from generic return type like Task<T>)
        name_node = None
        saw_type = False

        for child in node.children:
            if child.type in (
                "predefined_type",
                "generic_name",
                "qualified_name",
                "nullable_type",
                "array_type",
                "pointer_type",
                "tuple_type",
                "ref_type",
            ):
                saw_type = True
            elif child.type == "identifier":
                if saw_type:
                    name_node = child
                    break
                saw_type = True  # First identifier could be return type
            elif child.type == "parameter_list":
                break

        if not name_node:
            return

        name = self._get_node_text(name_node, source)
        is_exported = self._is_exported(node, source)

        # Get parameter count
        params_node = self._find_child_by_type(node, "parameter_list")
        param_count = self._count_parameters(params_node)

        docstring = self._get_xml_doc_comment(node, source)

        result.symbols.append(
            ExtractedSymbol(
                path=path,
                symbol_name=name,
                symbol_type="method",
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                is_exported=is_exported,
                parameters=param_count,
                parent_symbol=parent_class,
                docstring=docstring,
            )
        )

        # Process method body for calls
        body_node = self._find_child_by_type(node, "block")
        if body_node:
            for child in body_node.children:
                self._extract_from_tree(child, path, source, result, parent_class, None)

        # Process expression-bodied methods (e.g., public int Square(int x) => x * x;)
        arrow_clause = self._find_child_by_type(node, "arrow_expression_clause")
        if arrow_clause:
            for child in arrow_clause.children:
                self._extract_from_tree(child, path, source, result, parent_class, None)

    def _handle_constructor(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        parent_class: str | None,
    ) -> None:
        """Handle constructor declaration."""
        name_node = self._find_child_by_type(node, "identifier")
        if not name_node:
            return

        name = self._get_node_text(name_node, source)
        is_exported = self._is_exported(node, source)

        params_node = self._find_child_by_type(node, "parameter_list")
        param_count = self._count_parameters(params_node)

        docstring = self._get_xml_doc_comment(node, source)

        result.symbols.append(
            ExtractedSymbol(
                path=path,
                symbol_name=name,
                symbol_type="method",  # Constructors are methods
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                is_exported=is_exported,
                parameters=param_count,
                parent_symbol=parent_class,
                docstring=docstring,
            )
        )

        # Process constructor body for calls
        body_node = self._find_child_by_type(node, "block")
        if body_node:
            for child in body_node.children:
                self._extract_from_tree(child, path, source, result, parent_class, None)

    def _handle_property(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        parent_class: str | None,
    ) -> None:
        """Handle property declaration."""
        name_node = self._find_child_by_type(node, "identifier")
        if not name_node:
            return

        name = self._get_node_text(name_node, source)
        is_exported = self._is_exported(node, source)
        docstring = self._get_xml_doc_comment(node, source)

        result.symbols.append(
            ExtractedSymbol(
                path=path,
                symbol_name=name,
                symbol_type="property",
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                is_exported=is_exported,
                parameters=None,
                parent_symbol=parent_class,
                docstring=docstring,
            )
        )

        # Process accessor bodies for calls
        accessor_list = self._find_child_by_type(node, "accessor_list")
        if accessor_list:
            for child in accessor_list.children:
                self._extract_from_tree(child, path, source, result, parent_class, None)

        # Process expression-bodied properties (e.g., public int Value => _value;)
        arrow_clause = self._find_child_by_type(node, "arrow_expression_clause")
        if arrow_clause:
            for child in arrow_clause.children:
                self._extract_from_tree(child, path, source, result, parent_class, None)

    def _handle_field(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        parent_class: str | None,
    ) -> None:
        """Handle field declaration."""
        # Find variable declarator(s) in the field declaration
        var_decl = self._find_child_by_type(node, "variable_declaration")
        if not var_decl:
            return

        is_exported = self._is_exported(node, source)
        docstring = self._get_xml_doc_comment(node, source)

        for child in var_decl.children:
            if child.type == "variable_declarator":
                name_node = self._find_child_by_type(child, "identifier")
                if name_node:
                    name = self._get_node_text(name_node, source)
                    result.symbols.append(
                        ExtractedSymbol(
                            path=path,
                            symbol_name=name,
                            symbol_type="field",
                            line_start=node.start_point[0] + 1,
                            line_end=node.end_point[0] + 1,
                            is_exported=is_exported,
                            parameters=None,
                            parent_symbol=parent_class,
                            docstring=docstring,
                        )
                    )

    def _handle_event(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        parent_class: str | None,
    ) -> None:
        """Handle event declaration with accessor list."""
        name_node = self._find_child_by_type(node, "identifier")
        if not name_node:
            return

        name = self._get_node_text(name_node, source)
        is_exported = self._is_exported(node, source)
        docstring = self._get_xml_doc_comment(node, source)

        result.symbols.append(
            ExtractedSymbol(
                path=path,
                symbol_name=name,
                symbol_type="event",
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                is_exported=is_exported,
                parameters=None,
                parent_symbol=parent_class,
                docstring=docstring,
            )
        )

    def _handle_event_field(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        parent_class: str | None,
    ) -> None:
        """Handle event field declaration (e.g., public event EventHandler MyEvent;)."""
        # Find variable declarator in the event declaration
        var_decl = self._find_child_by_type(node, "variable_declaration")
        if not var_decl:
            return

        is_exported = self._is_exported(node, source)
        docstring = self._get_xml_doc_comment(node, source)

        for child in var_decl.children:
            if child.type == "variable_declarator":
                name_node = self._find_child_by_type(child, "identifier")
                if name_node:
                    name = self._get_node_text(name_node, source)
                    result.symbols.append(
                        ExtractedSymbol(
                            path=path,
                            symbol_name=name,
                            symbol_type="event",
                            line_start=node.start_point[0] + 1,
                            line_end=node.end_point[0] + 1,
                            is_exported=is_exported,
                            parameters=None,
                            parent_symbol=parent_class,
                            docstring=docstring,
                        )
                    )

    def _handle_invocation(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
    ) -> None:
        """Handle invocation expression (method calls)."""
        call_info = self._analyze_invocation(node, source)
        if call_info:
            callee_symbol, call_type, callee_object = call_info
            caller_symbol = self._find_enclosing_member(node, source)

            result.calls.append(
                ExtractedCall(
                    caller_file=path,
                    caller_symbol=caller_symbol or "<module>",
                    callee_symbol=callee_symbol,
                    callee_file=None,
                    line_number=node.start_point[0] + 1,
                    call_type=call_type,
                    is_dynamic_code_execution=False,
                    callee_object=callee_object,
                )
            )

        # Handle chained calls - the function part might be a member access on another invocation
        # e.g., col.Skip(1).FirstOrDefault() - we need to extract both Skip and FirstOrDefault
        func = node.children[0] if node.children else None
        if func and func.type == "member_access_expression":
            # Check if the object of the member access is itself an invocation
            for child in func.children:
                if child.type == "invocation_expression":
                    self._handle_invocation(child, path, source, result)

    def _handle_object_creation(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
    ) -> None:
        """Handle object creation expression (new Foo())."""
        # Get the type being instantiated
        type_node = self._find_child_by_type(node, "identifier")
        if not type_node:
            # Try generic_name for generic types
            type_node = self._find_child_by_type(node, "generic_name")
            if not type_node:
                return

        type_name = self._get_node_text(type_node, source)
        # For generic types, extract just the base name
        if "<" in type_name:
            type_name = type_name.split("<")[0]

        caller_symbol = self._find_enclosing_member(node, source)

        result.calls.append(
            ExtractedCall(
                caller_file=path,
                caller_symbol=caller_symbol or "<module>",
                callee_symbol=type_name,  # Constructor call
                callee_file=None,
                line_number=node.start_point[0] + 1,
                call_type="constructor",
                is_dynamic_code_execution=False,
                callee_object=None,
            )
        )

    def _handle_using_directive(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
    ) -> None:
        """Handle using directive (imports)."""
        # Check for static using
        is_static = any(
            child.type == "static" or self._get_node_text(child, source) == "static"
            for child in node.children
        )

        # Check for global using (C# 10+)
        is_global = any(
            child.type == "global" or self._get_node_text(child, source) == "global"
            for child in node.children
        )

        # Get the namespace/type being imported
        # For aliased using: using Alias = System.Text.StringBuilder;
        # AST structure: identifier (Alias), =, qualified_name (System.Text.StringBuilder)
        name_node = None
        alias = None
        has_equals = any(child.type == "=" for child in node.children)

        for child in node.children:
            if child.type == "qualified_name":
                name_node = child
            elif child.type == "identifier":
                if has_equals and alias is None:
                    # This is the alias (appears before =)
                    alias = self._get_node_text(child, source)
                elif name_node is None:
                    # Simple using with just an identifier (e.g., using System;)
                    name_node = child
            elif child.type == "name_equals":
                # Fallback for older tree-sitter versions that wrap alias in name_equals
                for eq_child in child.children:
                    if eq_child.type == "identifier":
                        alias = self._get_node_text(eq_child, source)
                        break

        if name_node:
            imported_path = self._get_node_text(name_node, source)

            import_type = "using_static" if is_static else "static"
            if is_global:
                import_type = "global"

            result.imports.append(
                ExtractedImport(
                    file=path,
                    imported_path=imported_path,
                    imported_symbols=None,  # C# imports entire namespace
                    import_type=import_type,
                    line_number=node.start_point[0] + 1,
                    module_alias=alias,
                )
            )

    def _handle_extern_alias(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
    ) -> None:
        """Handle extern alias directive."""
        name_node = self._find_child_by_type(node, "identifier")
        if name_node:
            alias_name = self._get_node_text(name_node, source)
            result.imports.append(
                ExtractedImport(
                    file=path,
                    imported_path=alias_name,
                    imported_symbols=None,
                    import_type="extern",
                    line_number=node.start_point[0] + 1,
                )
            )

    def _analyze_invocation(
        self,
        node: Node,
        source: bytes,
    ) -> tuple[str, str, str | None] | None:
        """Analyze an invocation expression to extract callee info.

        Args:
            node: Invocation expression node
            source: Source bytes

        Returns:
            Tuple of (callee_symbol, call_type, callee_object) or None
        """
        # Get the expression being called (first child)
        if not node.children:
            return None

        expr = node.children[0]

        if expr.type == "identifier":
            # Direct call: Method()
            callee = self._get_node_text(expr, source)
            return callee, "direct", None

        elif expr.type == "member_access_expression":
            # Member access: obj.Method()
            method_name = self._get_member_access_name(expr, source)
            obj_name = self._get_member_access_object(expr, source)
            if method_name:
                return method_name, "dynamic", obj_name

        elif expr.type == "conditional_access_expression":
            # Conditional access: obj?.Method() or event?.Invoke()
            # Check for ?.Invoke() pattern which indicates event/delegate invocation
            event_info = self._analyze_conditional_invoke(expr, source)
            if event_info:
                return event_info

        elif expr.type == "generic_name":
            # Generic method call: Method<T>()
            # Get identifier BEFORE type_argument_list (avoid type params like T)
            for child in expr.children:
                if child.type == "identifier":
                    callee = self._get_node_text(child, source)
                    return callee, "direct", None
                if child.type == "type_argument_list":
                    break  # Stop before type params

        return None

    def _analyze_conditional_invoke(
        self,
        node: Node,
        source: bytes,
    ) -> tuple[str, str, str | None] | None:
        """Analyze conditional access for event/delegate invocation patterns.

        Detects patterns like:
        - OnChanged?.Invoke(this, args) -> call_type="event"
        - handler?.Invoke(args) -> call_type="delegate"

        Args:
            node: conditional_access_expression node
            source: Source bytes

        Returns:
            Tuple of (callee_symbol, call_type, callee_object) or None
        """
        # Structure: conditional_access_expression has
        #   - expression (the object being accessed, e.g., OnChanged)
        #   - conditional_access_chain (?.Invoke part)
        target_name = None
        has_invoke = False

        for child in node.children:
            if child.type == "identifier":
                target_name = self._get_node_text(child, source)
            elif child.type == "member_binding_expression":
                # This is the ?.Member part - check if it's Invoke
                for binding_child in child.children:
                    if binding_child.type == "identifier":
                        member_name = self._get_node_text(binding_child, source)
                        if member_name == "Invoke":
                            has_invoke = True
                            break
            elif child.type == "invocation_expression":
                # Nested invocation - get the method being called
                for inv_child in child.children:
                    if inv_child.type == "member_binding_expression":
                        for binding_child in inv_child.children:
                            if binding_child.type == "identifier":
                                member_name = self._get_node_text(binding_child, source)
                                if member_name == "Invoke":
                                    has_invoke = True
                                    break

        if has_invoke and target_name:
            # Return the event/delegate name as the callee symbol
            # Use "event" as call_type since ?.Invoke() is the idiomatic event raise pattern
            return target_name, "event", None

        # Not an Invoke pattern, handle as regular conditional member access
        if target_name:
            # Find the method being called after ?.
            for child in node.children:
                if child.type == "member_binding_expression":
                    for binding_child in child.children:
                        if binding_child.type == "identifier":
                            method_name = self._get_node_text(binding_child, source)
                            return method_name, "dynamic", target_name

        return None

    def _get_member_access_name(self, node: Node, source: bytes) -> str | None:
        """Get the member name from a member access expression."""
        # Member access: expression.member
        # The member is typically the last identifier
        for child in reversed(node.children):
            if child.type == "identifier":
                return self._get_node_text(child, source)
            elif child.type == "generic_name":
                id_node = self._find_child_by_type(child, "identifier")
                if id_node:
                    return self._get_node_text(id_node, source)
        return None

    def _get_member_access_object(self, node: Node, source: bytes) -> str | None:
        """Get the object name from a member access expression."""
        for child in node.children:
            if child.type == "identifier":
                return self._get_node_text(child, source)
            elif child.type == "member_access_expression":
                # Nested access: get root object recursively
                return self._get_member_access_object(child, source)
            elif child.type == "this_expression":
                return "this"
            elif child.type == "base_expression":
                return "base"
            # Handle string literals (extension methods on strings)
            elif child.type in (
                "string_literal",
                "verbatim_string_literal",
                "interpolated_string_expression",
            ):
                return "<string>"
            # Handle numeric literals (extension methods on numbers)
            elif child.type in ("integer_literal", "real_literal"):
                return "<number>"
            # Handle type references (e.g., string.IsNullOrEmpty, Math.Sqrt)
            elif child.type == "predefined_type":
                return self._get_node_text(child, source)
            elif child.type == "generic_name":
                return self._get_node_text(child, source)
            # Handle invocation expressions (chained calls like col.Skip(1).First())
            elif child.type == "invocation_expression":
                return "<call>"
        return None

    def _find_enclosing_member(self, node: Node, source: bytes) -> str | None:
        """Find the name of the enclosing method/property/constructor."""
        current = node.parent
        while current:
            if current.type == "method_declaration":
                # For methods, we need to skip past the return type to find the actual name
                # Similar logic to _handle_method
                name_node = self._get_method_name_node(current, source)
                if name_node:
                    return self._get_node_text(name_node, source)
            elif current.type == "constructor_declaration":
                name_node = self._find_child_by_type(current, "identifier")
                if name_node:
                    return self._get_node_text(name_node, source)
            elif current.type == "property_declaration":
                name_node = self._find_child_by_type(current, "identifier")
                if name_node:
                    return self._get_node_text(name_node, source)
            elif current.type == "accessor_declaration":
                # get/set accessor - find parent property
                parent = current.parent
                while parent:
                    if parent.type == "property_declaration":
                        name_node = self._find_child_by_type(parent, "identifier")
                        if name_node:
                            accessor_type = self._get_accessor_type(current, source)
                            prop_name = self._get_node_text(name_node, source)
                            return f"{prop_name}.{accessor_type}" if accessor_type else prop_name
                    parent = parent.parent
            current = current.parent
        return None

    def _get_accessor_type(self, accessor_node: Node, source: bytes) -> str | None:
        """Get the accessor type (get, set, init) from an accessor declaration."""
        for child in accessor_node.children:
            text = self._get_node_text(child, source)
            if text in ("get", "set", "init"):
                return text
        return None

    def _is_exported(self, node: Node, source: bytes) -> bool:
        """Check if a declaration is exported (public/internal/protected)."""
        for child in node.children:
            if child.type == "modifier":
                modifier_text = self._get_node_text(child, source)
                if modifier_text in PRIVATE_MODIFIERS:
                    return False
                if modifier_text in PUBLIC_MODIFIERS:
                    return True
        # Default: internal (exported) for top-level, private for nested
        return True

    def _count_parameters(self, params_node: Node | None) -> int:
        """Count parameters in a parameter list."""
        if not params_node:
            return 0

        count = 0
        for child in params_node.children:
            if child.type == "parameter":
                count += 1
        return count

    def _get_namespace_name(self, node: Node, source: bytes) -> str:
        """Get the namespace name from a namespace declaration."""
        for child in node.children:
            if child.type == "qualified_name":
                return self._get_node_text(child, source)
            elif child.type == "identifier":
                return self._get_node_text(child, source)
        return ""

    def _get_xml_doc_comment(self, node: Node, source: bytes) -> str | None:
        """Extract XML documentation comment if present."""
        # Look for preceding comment nodes
        # In tree-sitter, comments are typically siblings
        if node.prev_sibling and node.prev_sibling.type == "comment":
            comment_text = self._get_node_text(node.prev_sibling, source)
            # Check if it's an XML doc comment (starts with ///)
            if comment_text.startswith("///"):
                # Extract summary content
                lines = comment_text.split("\n")
                summary_lines = []
                in_summary = False
                for line in lines:
                    line = line.strip()
                    if line.startswith("///"):
                        line = line[3:].strip()
                    if "<summary>" in line:
                        in_summary = True
                        line = line.replace("<summary>", "").strip()
                    if "</summary>" in line:
                        line = line.replace("</summary>", "").strip()
                        if line:
                            summary_lines.append(line)
                        break
                    if in_summary and line:
                        summary_lines.append(line)
                if summary_lines:
                    return " ".join(summary_lines)
        return None

    def _get_node_text(self, node: Node, source: bytes) -> str:
        """Get the text content of a node."""
        return source[node.start_byte:node.end_byte].decode("utf-8")

    def _find_child_by_type(self, node: Node, type_name: str) -> Node | None:
        """Find the first child with a given type."""
        for child in node.children:
            if child.type == type_name:
                return child
        return None

    def _get_method_name_node(self, node: Node, source: bytes) -> Node | None:
        """Get the method name identifier from a method declaration.

        For generic methods like `T SecondOrDefault<T>(...)`, this correctly
        identifies the method name (`SecondOrDefault`) rather than the type
        parameter (`T`).
        """
        # Method structure: [modifiers] return_type identifier parameter_list block
        # Find identifier AFTER return type (not from generic return type like Task<T>)
        saw_type = False

        for child in node.children:
            if child.type in (
                "predefined_type",
                "generic_name",
                "qualified_name",
                "nullable_type",
                "array_type",
                "pointer_type",
                "tuple_type",
                "ref_type",
            ):
                saw_type = True
            elif child.type == "identifier":
                if saw_type:
                    return child
                saw_type = True  # First identifier could be return type
            elif child.type == "parameter_list":
                break

        return None
