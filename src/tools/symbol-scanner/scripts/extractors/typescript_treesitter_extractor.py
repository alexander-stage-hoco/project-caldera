"""TypeScript tree-sitter based symbol extractor.

Extends the JavaScript extractor with TypeScript-specific node types:
interfaces, type aliases, enums, abstract classes, and type-only imports.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .base import (
    ExtractedSymbol,
    ExtractionResult,
)
from .javascript_treesitter_extractor import JavaScriptTreeSitterExtractor

if TYPE_CHECKING:
    from tree_sitter import Node


class TypeScriptTreeSitterExtractor(JavaScriptTreeSitterExtractor):
    """Extract symbols from TypeScript files using tree-sitter.

    Inherits all JavaScript extraction logic and adds handling for:
    - interface_declaration
    - type_alias_declaration
    - enum_declaration
    - abstract_class_declaration
    - abstract_method_signature
    - type-only imports (import type { T })
    """

    def __init__(self) -> None:
        """Initialize with TypeScript parser."""
        from tree_sitter_language_pack import get_parser

        self._parser = get_parser("typescript")
        self._tsx_parser = get_parser("tsx")

    @property
    def language(self) -> str:
        return "typescript"

    @property
    def file_extensions(self) -> tuple[str, ...]:
        return (".ts", ".tsx")

    def extract_file(self, file_path: Path, relative_path: str) -> ExtractionResult:
        """Extract symbols from a TypeScript file.

        Switches to TSX parser for .tsx files.
        """
        # Use TSX parser for .tsx files
        if file_path.suffix == ".tsx":
            original_parser = self._parser
            self._parser = self._tsx_parser
            try:
                return super().extract_file(file_path, relative_path)
            finally:
                self._parser = original_parser
        return super().extract_file(file_path, relative_path)

    def _extract_from_tree(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        parent_class: str | None = None,
        is_exported: bool = False,
    ) -> None:
        """Override to handle TypeScript-specific node types."""
        for child in node.children:
            node_type = child.type

            # Export statements wrap declarations
            if node_type == "export_statement":
                self._handle_export_statement(child, path, source, result, parent_class)

            # Standard JS declarations (inherited handlers)
            elif node_type == "function_declaration":
                self._handle_function_declaration(
                    child, path, source, result, is_exported=is_exported,
                )
            elif node_type == "generator_function_declaration":
                self._handle_function_declaration(
                    child, path, source, result, is_exported=is_exported,
                )
            elif node_type == "class_declaration":
                self._handle_class_declaration(
                    child, path, source, result, is_exported=is_exported,
                )
            elif node_type in ("lexical_declaration", "variable_declaration"):
                self._handle_variable_declaration(
                    child, path, source, result, parent_class=parent_class,
                    is_exported=is_exported,
                )
            elif node_type == "import_statement":
                self._handle_import_statement(child, path, source, result)

            # TypeScript-specific declarations
            elif node_type == "interface_declaration":
                self._handle_interface_declaration(
                    child, path, source, result, is_exported=is_exported,
                )
            elif node_type == "type_alias_declaration":
                self._handle_type_alias_declaration(
                    child, path, source, result, is_exported=is_exported,
                )
            elif node_type == "enum_declaration":
                self._handle_enum_declaration(
                    child, path, source, result, is_exported=is_exported,
                )
            elif node_type == "abstract_class_declaration":
                self._handle_class_declaration(
                    child, path, source, result, is_exported=is_exported,
                )

            # Expression statements
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
        """Handle export statement with TypeScript-specific types."""
        for child in node.children:
            if child.type == "function_declaration":
                self._handle_function_declaration(
                    child, path, source, result, is_exported=True,
                )
            elif child.type == "generator_function_declaration":
                self._handle_function_declaration(
                    child, path, source, result, is_exported=True,
                )
            elif child.type in ("class_declaration", "abstract_class_declaration"):
                self._handle_class_declaration(
                    child, path, source, result, is_exported=True,
                )
            elif child.type in ("lexical_declaration", "variable_declaration"):
                self._handle_variable_declaration(
                    child, path, source, result, parent_class=parent_class,
                    is_exported=True,
                )
            elif child.type == "interface_declaration":
                self._handle_interface_declaration(
                    child, path, source, result, is_exported=True,
                )
            elif child.type == "type_alias_declaration":
                self._handle_type_alias_declaration(
                    child, path, source, result, is_exported=True,
                )
            elif child.type == "enum_declaration":
                self._handle_enum_declaration(
                    child, path, source, result, is_exported=True,
                )

    def _handle_interface_declaration(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        is_exported: bool = False,
    ) -> None:
        """Handle TypeScript interface declaration."""
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

    def _handle_type_alias_declaration(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        is_exported: bool = False,
    ) -> None:
        """Handle TypeScript type alias declaration."""
        name_node = self._find_child_by_type(node, "type_identifier")
        if not name_node:
            return

        name = self._get_node_text(name_node, source)
        docstring = self._get_jsdoc_comment(node, source)

        result.symbols.append(ExtractedSymbol(
            path=path,
            symbol_name=name,
            symbol_type="variable",
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            is_exported=is_exported,
            parameters=None,
            parent_symbol=None,
            docstring=docstring,
        ))

    def _handle_enum_declaration(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        is_exported: bool = False,
    ) -> None:
        """Handle TypeScript enum declaration."""
        name_node = self._find_child_by_type(node, "identifier")
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

    def _extract_class_members(
        self,
        body: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        class_name: str,
    ) -> None:
        """Extract methods and fields from class body, including TS-specific nodes."""
        for child in body.children:
            if child.type == "method_definition":
                self._handle_method_definition(
                    child, path, source, result, class_name=class_name,
                )
            elif child.type in ("public_field_definition", "field_definition"):
                self._handle_class_field(
                    child, path, source, result, class_name=class_name,
                )
            elif child.type == "abstract_method_signature":
                self._handle_abstract_method_signature(
                    child, path, source, result, class_name=class_name,
                )

    def _is_private_member(self, node: Node, source: bytes) -> bool:
        """Check if a TS class member has private accessibility."""
        for child in node.children:
            if child.type == "accessibility_modifier":
                text = self._get_node_text(child, source)
                if text == "private":
                    return True
        return False

    def _handle_method_definition(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        class_name: str,
    ) -> None:
        """Override to check TS accessibility modifiers."""
        name_node = self._find_child_by_type(node, "property_identifier")
        if not name_node:
            name_node = self._find_child_by_type(node, "identifier")
        if not name_node:
            return

        name = self._get_node_text(name_node, source)
        is_private = name.startswith("#") or self._is_private_member(node, source)
        params = self._count_parameters(node)
        docstring = self._get_jsdoc_comment(node, source)

        result.symbols.append(ExtractedSymbol(
            path=path,
            symbol_name=name,
            symbol_type="method",
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            is_exported=not is_private,
            parameters=params,
            parent_symbol=class_name,
            docstring=docstring,
        ))

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
        """Override to check TS accessibility modifiers."""
        name_node = self._find_child_by_type(node, "property_identifier")
        if not name_node:
            return

        name = self._get_node_text(name_node, source)
        is_private = name.startswith("#") or self._is_private_member(node, source)

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

    def _handle_abstract_method_signature(
        self,
        node: Node,
        path: str,
        source: bytes,
        result: ExtractionResult,
        class_name: str,
    ) -> None:
        """Handle abstract method signature in abstract class."""
        name_node = self._find_child_by_type(node, "property_identifier")
        if not name_node:
            return

        name = self._get_node_text(name_node, source)
        params = self._count_parameters(node)

        result.symbols.append(ExtractedSymbol(
            path=path,
            symbol_name=name,
            symbol_type="method",
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            is_exported=True,
            parameters=params,
            parent_symbol=class_name,
            docstring=None,
        ))
