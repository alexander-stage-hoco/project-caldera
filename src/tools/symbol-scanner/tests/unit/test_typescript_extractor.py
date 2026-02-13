"""Unit tests for TypeScript tree-sitter extractor."""

from __future__ import annotations

from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from extractors.typescript_treesitter_extractor import TypeScriptTreeSitterExtractor


class TestTypeScriptTreeSitterExtractor:
    """Tests for TypeScriptTreeSitterExtractor."""

    @pytest.fixture
    def extractor(self):
        return TypeScriptTreeSitterExtractor()

    # ============ Basic Properties ============

    def test_language_property(self, extractor):
        assert extractor.language == "typescript"

    def test_file_extensions(self, extractor):
        assert ".ts" in extractor.file_extensions
        assert ".tsx" in extractor.file_extensions

    # ============ Interface Extraction ============

    def test_extract_interface(self, extractor, temp_dir):
        """Test extraction of TypeScript interface."""
        code = """export interface User {
    id: string;
    name: string;
    email: string;
}
"""
        test_file = temp_dir / "test.ts"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.ts")

        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "User"
        assert classes[0].is_exported is True

    def test_extract_non_exported_interface(self, extractor, temp_dir):
        """Test extraction of non-exported interface."""
        code = "interface Internal {\n    value: number;\n}\n"
        test_file = temp_dir / "test.ts"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.ts")

        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "Internal"
        assert classes[0].is_exported is False

    # ============ Enum Extraction ============

    def test_extract_enum(self, extractor, temp_dir):
        """Test extraction of TypeScript enum."""
        code = """export enum Color {
    Red,
    Green,
    Blue,
}
"""
        test_file = temp_dir / "test.ts"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.ts")

        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "Color"
        assert classes[0].is_exported is True

    # ============ Type Alias Extraction ============

    def test_extract_type_alias(self, extractor, temp_dir):
        """Test extraction of TypeScript type alias."""
        code = 'export type StringOrNumber = string | number;\ntype Internal = { x: number };\n'
        test_file = temp_dir / "test.ts"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.ts")

        variables = [s for s in result.symbols if s.symbol_type == "variable"]
        assert len(variables) == 2

        exported = next(v for v in variables if v.symbol_name == "StringOrNumber")
        assert exported.is_exported is True

        internal = next(v for v in variables if v.symbol_name == "Internal")
        assert internal.is_exported is False

    # ============ Abstract Class ============

    def test_extract_abstract_class(self, extractor, temp_dir):
        """Test extraction of abstract class with abstract methods."""
        code = """export abstract class BaseService {
    abstract find(id: string): Promise<any>;

    log(message: string): void {
        console.log(message);
    }
}
"""
        test_file = temp_dir / "test.ts"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.ts")

        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "BaseService"
        assert classes[0].is_exported is True

        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = {m.symbol_name for m in methods}
        assert "find" in method_names
        assert "log" in method_names

        find_method = next(m for m in methods if m.symbol_name == "find")
        assert find_method.parameters == 1
        assert find_method.parent_symbol == "BaseService"

    # ============ Type-Only Imports ============

    def test_extract_type_import(self, extractor, temp_dir):
        """Test extraction of type-only import."""
        code = 'import type { User } from "./models";\nimport { Service } from "./services";\n'
        test_file = temp_dir / "test.ts"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.ts")

        assert len(result.imports) == 2

        type_import = next(i for i in result.imports if i.import_type == "type_checking")
        assert type_import.imported_path == "./models"
        assert type_import.imported_symbols == "User"

        static_import = next(i for i in result.imports if i.import_type == "static")
        assert static_import.imported_path == "./services"
        assert static_import.imported_symbols == "Service"

    # ============ Private Members ============

    def test_private_accessibility_modifier(self, extractor, temp_dir):
        """Test that private members are marked as non-exported."""
        code = """export class Foo {
    private secret: number = 42;
    public visible: string = "hi";
    normal: boolean = true;

    private hiddenMethod(): void {}
    public publicMethod(): void {}
}
"""
        test_file = temp_dir / "test.ts"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.ts")

        symbol_map = {s.symbol_name: s for s in result.symbols}
        assert symbol_map["secret"].is_exported is False
        assert symbol_map["visible"].is_exported is True
        assert symbol_map["normal"].is_exported is True
        assert symbol_map["hiddenMethod"].is_exported is False
        assert symbol_map["publicMethod"].is_exported is True

    # ============ Generic Class ============

    def test_extract_generic_class(self, extractor, temp_dir):
        """Test extraction of generic class."""
        code = """export class Repository<T> {
    private items: Map<string, T> = new Map();

    async find(id: string): Promise<T | undefined> {
        return this.items.get(id);
    }
}
"""
        test_file = temp_dir / "test.ts"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.ts")

        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert len(classes) == 1
        assert classes[0].symbol_name == "Repository"

        methods = [s for s in result.symbols if s.symbol_type == "method"]
        assert any(m.symbol_name == "find" for m in methods)

        fields = [s for s in result.symbols if s.symbol_type == "variable" and s.parent_symbol == "Repository"]
        assert any(f.symbol_name == "items" and f.is_exported is False for f in fields)

    # ============ TSX Support ============

    def test_extract_tsx_file(self, extractor, temp_dir):
        """Test extraction from .tsx file."""
        code = """import React from "react";

interface Props {
    name: string;
}

export function Greeting({ name }: Props) {
    return <div>Hello, {name}!</div>;
}
"""
        test_file = temp_dir / "test.tsx"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.tsx")

        # Should find the interface and the function
        symbols = result.symbols
        symbol_names = {s.symbol_name for s in symbols}
        assert "Props" in symbol_names
        assert "Greeting" in symbol_names

    # ============ Directory Extraction ============

    def test_extract_directory(self, extractor):
        """Test full directory extraction with call resolution."""
        repo = Path(__file__).resolve().parents[2] / "eval-repos" / "synthetic" / "ts-class-hierarchy"
        if not repo.exists():
            pytest.skip("ts-class-hierarchy eval repo not found")

        result = extractor.extract_directory(repo, repo)

        assert len(result.symbols) >= 15
        assert len(result.imports) >= 4

        # Check type_checking imports detected
        type_imports = [i for i in result.imports if i.import_type == "type_checking"]
        assert len(type_imports) >= 2

        # Check interfaces found
        interfaces = [
            s for s in result.symbols
            if s.symbol_type == "class" and s.symbol_name in ("Entity", "Serializable")
        ]
        assert len(interfaces) >= 2

    # ============ Decorator Handling ============

    def test_extract_decorated_class(self, extractor, temp_dir):
        """Test extraction of decorated TypeScript class."""
        code = """function Component(target: any) { return target; }

@Component
export class MyWidget {
    render(): string {
        return "widget";
    }
}
"""
        test_file = temp_dir / "test.ts"
        test_file.write_text(code)

        result = extractor.extract_file(test_file, "test.ts")

        classes = [s for s in result.symbols if s.symbol_type == "class"]
        assert any(c.symbol_name == "MyWidget" for c in classes)
