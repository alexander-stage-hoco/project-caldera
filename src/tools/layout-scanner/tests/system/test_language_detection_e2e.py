"""End-to-end system tests for language detection.

Tests realistic repository structures and scenarios:
- Flask-like Python projects
- React/TypeScript projects
- .NET/C# projects
- Confidence scoring behavior
- Error recovery
"""

import pytest
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from classifier import detect_language, get_language_distribution, LanguageResult
from language_detector import (
    detect_language as ld_detect,
    is_binary_file,
    is_vendor_file,
    is_generated_file,
)


# =============================================================================
# Real-World Repository Structure Tests
# =============================================================================


class TestFlaskLikeRepository:
    """System tests using Flask-like Python project structure."""

    @pytest.fixture
    def flask_repo(self, tmp_path):
        """Create Flask-like Python project structure."""
        # app/
        (tmp_path / "app").mkdir()
        (tmp_path / "app" / "__init__.py").write_bytes(
            b'"""Flask application."""\nfrom flask import Flask\napp = Flask(__name__)'
        )
        (tmp_path / "app" / "models.py").write_bytes(
            b'"""Database models."""\nfrom app import db\nclass User(db.Model):\n    pass'
        )
        (tmp_path / "app" / "views.py").write_bytes(
            b'"""View functions."""\nfrom flask import render_template\n@app.route("/")\ndef index():\n    pass'
        )

        # tests/
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "__init__.py").write_bytes(b"")
        (tmp_path / "tests" / "test_models.py").write_bytes(
            b'"""Test models."""\nimport pytest\ndef test_user():\n    pass'
        )
        (tmp_path / "tests" / "conftest.py").write_bytes(
            b'"""Test fixtures."""\nimport pytest\n@pytest.fixture\ndef client():\n    pass'
        )

        # Root files
        (tmp_path / "setup.py").write_bytes(
            b'from setuptools import setup\nsetup(name="myapp")'
        )
        (tmp_path / "requirements.txt").write_bytes(
            b"flask>=2.0\npytest>=7.0"
        )
        (tmp_path / "Makefile").write_bytes(
            b"install:\n\tpip install -r requirements.txt\n\ntest:\n\tpytest"
        )

        # scripts/
        (tmp_path / "scripts").mkdir()
        (tmp_path / "scripts" / "deploy").write_bytes(
            b"#!/bin/bash\necho 'Deploying...'\ndocker-compose up -d"
        )
        (tmp_path / "scripts" / "migrate").write_bytes(
            b"#!/usr/bin/env python\nfrom app import db\ndb.create_all()"
        )

        return tmp_path

    def test_python_files_detected(self, flask_repo):
        """All Python files should be detected correctly."""
        python_files = [
            "app/__init__.py",
            "app/models.py",
            "app/views.py",
            "tests/test_models.py",
            "tests/conftest.py",
            "setup.py",
        ]

        for filepath in python_files:
            result = detect_language(Path(filepath).name, ".py")
            assert result.language == "python", f"{filepath} should be Python"
            assert result.confidence >= 0.9

    def test_shebang_scripts_detected(self, flask_repo):
        """Shebang scripts should be detected correctly."""
        # Bash script
        deploy_content = (flask_repo / "scripts" / "deploy").read_bytes()
        result = detect_language("deploy", "", content=deploy_content)
        assert result.language == "shell"

        # Python script without .py extension
        migrate_content = (flask_repo / "scripts" / "migrate").read_bytes()
        result = detect_language("migrate", "", content=migrate_content)
        assert result.language == "python"

    def test_makefile_detected(self, flask_repo):
        """Makefile should be detected correctly."""
        result = detect_language("Makefile", "")
        assert result.language == "makefile"

    def test_requirements_txt_is_text(self, flask_repo):
        """requirements.txt should not be binary."""
        content = (flask_repo / "requirements.txt").read_bytes()
        assert is_binary_file("requirements.txt", content) is False


class TestReactTypeScriptRepository:
    """System tests using React/TypeScript project structure."""

    @pytest.fixture
    def react_repo(self, tmp_path):
        """Create React-like TypeScript project structure."""
        # src/
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "App.tsx").write_bytes(
            b'import React from "react";\nexport const App = () => <div>Hello</div>;'
        )
        (tmp_path / "src" / "index.ts").write_bytes(
            b'import { App } from "./App";\nimport ReactDOM from "react-dom";'
        )

        # src/components/
        (tmp_path / "src" / "components").mkdir()
        (tmp_path / "src" / "components" / "Button.tsx").write_bytes(
            b'interface Props { label: string; }\nexport const Button = ({ label }: Props) => <button>{label}</button>;'
        )
        (tmp_path / "src" / "components" / "Button.test.tsx").write_bytes(
            b'import { render } from "@testing-library/react";\nimport { Button } from "./Button";'
        )

        # public/
        (tmp_path / "public").mkdir()
        (tmp_path / "public" / "index.html").write_bytes(
            b'<!DOCTYPE html>\n<html><head><title>App</title></head><body></body></html>'
        )

        # Config files
        (tmp_path / "package.json").write_bytes(
            b'{"name": "react-app", "dependencies": {"react": "^18.0"}}'
        )
        (tmp_path / "tsconfig.json").write_bytes(
            b'{"compilerOptions": {"target": "ES6", "jsx": "react"}}'
        )
        (tmp_path / ".eslintrc.json").write_bytes(
            b'{"extends": "react-app"}'
        )

        return tmp_path

    def test_typescript_files_detected(self, react_repo):
        """TypeScript files should be detected correctly."""
        ts_files = [
            ("App.tsx", ".tsx"),
            ("index.ts", ".ts"),
            ("Button.tsx", ".tsx"),
            ("Button.test.tsx", ".tsx"),
        ]

        for filename, ext in ts_files:
            result = detect_language(filename, ext)
            assert result.language == "typescript", f"{filename} should be TypeScript"
            assert result.confidence >= 0.9

    def test_html_detected(self, react_repo):
        """HTML files should be detected correctly."""
        result = detect_language("index.html", ".html")
        assert result.language == "html"

    def test_json_config_detected(self, react_repo):
        """JSON config files should be detected correctly."""
        json_files = ["package.json", "tsconfig.json", ".eslintrc.json"]

        for filename in json_files:
            result = detect_language(filename, ".json")
            assert result.language == "json", f"{filename} should be JSON"


class TestDotNetRepository:
    """System tests using .NET/C# project structure."""

    @pytest.fixture
    def dotnet_repo(self, tmp_path):
        """Create .NET/C# project structure."""
        # src/
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "Program.cs").write_bytes(
            b'namespace MyApp;\nclass Program { static void Main() { } }'
        )

        # src/Models/
        (tmp_path / "src" / "Models").mkdir()
        (tmp_path / "src" / "Models" / "User.cs").write_bytes(
            b'namespace MyApp.Models;\npublic class User { public string Name { get; set; } }'
        )

        # tests/
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "UserTests.cs").write_bytes(
            b'using Xunit;\nnamespace MyApp.Tests;\npublic class UserTests { [Fact] public void Test() { } }'
        )

        # Project files
        (tmp_path / "MyProject.csproj").write_bytes(
            b'<Project Sdk="Microsoft.NET.Sdk">\n  <PropertyGroup>\n    <TargetFramework>net8.0</TargetFramework>\n  </PropertyGroup>\n</Project>'
        )
        (tmp_path / "MyProject.sln").write_bytes(
            b'Microsoft Visual Studio Solution File, Format Version 12.00'
        )

        # Generated files
        (tmp_path / "src" / "Generated.g.cs").write_bytes(
            b'// Auto-generated\nnamespace MyApp.Generated;'
        )

        return tmp_path

    def test_csharp_files_detected(self, dotnet_repo):
        """C# files should be detected correctly as 'csharp'."""
        cs_files = [
            "Program.cs",
            "User.cs",
            "UserTests.cs",
            "Generated.g.cs",
        ]

        for filename in cs_files:
            result = detect_language(filename, ".cs")
            assert result.language == "csharp", f"{filename} should be csharp"
            assert result.confidence >= 0.9

    def test_generated_file_detection(self, dotnet_repo):
        """Generated .g.cs files should be detected as generated."""
        assert is_generated_file("Generated.g.cs") is True
        assert is_generated_file("Program.cs") is False

    def test_project_files_detected(self, dotnet_repo):
        """Project files should be detected appropriately."""
        csproj_result = detect_language("MyProject.csproj", ".csproj")
        # .csproj is MSBuild format
        assert csproj_result.language in ["msbuild", "MSBuild"]


# =============================================================================
# Confidence Scoring System Tests
# =============================================================================


class TestConfidenceScoring:
    """System tests for confidence score behavior."""

    def test_unambiguous_extensions_high_confidence(self):
        """Standard extensions should have confidence >= 0.9."""
        high_confidence_extensions = [
            ("test.py", ".py"),
            ("app.js", ".js"),
            ("main.ts", ".ts"),
            ("Program.cs", ".cs"),
            ("Main.java", ".java"),
            ("main.go", ".go"),
            ("lib.rs", ".rs"),
        ]

        for filename, ext in high_confidence_extensions:
            result = detect_language(filename, ext)
            assert result.confidence >= 0.9, f"{filename} should have high confidence"

    def test_ambiguous_extensions_lower_confidence(self):
        """Ambiguous extensions should have confidence < 0.9."""
        result = detect_language("header.h", ".h")
        assert result.confidence < 0.9, ".h files should have lower confidence"

    def test_unknown_extensions_zero_confidence(self):
        """Unknown extensions should have confidence 0.0."""
        result = detect_language("file.xyz123unknown", ".xyz123unknown")
        assert result.language == "unknown"
        assert result.confidence == 0.0

    def test_shebang_confidence_reasonable(self):
        """Shebang detection should have confidence >= 0.8."""
        test_cases = [
            b"#!/usr/bin/env python\ncode",
            b"#!/bin/bash\ncode",
            b"#!/usr/bin/env ruby\ncode",
        ]

        for content in test_cases:
            result = detect_language("script", "", content=content)
            assert result.confidence >= 0.8, f"Shebang detection should have good confidence"


# =============================================================================
# Error Recovery System Tests
# =============================================================================


class TestErrorRecovery:
    """System tests for error handling and recovery."""

    def test_corrupted_file_content_handled(self):
        """Detection shouldn't crash on binary garbage."""
        # Random binary data
        content = bytes([i % 256 for i in range(10000)])
        result = detect_language("test.bin", ".bin", content=content)
        assert isinstance(result, LanguageResult)
        # Should complete without exception

    def test_empty_file_handling(self):
        """Empty files should be handled gracefully."""
        result = detect_language("empty.py", ".py", content=b"")
        assert result.language == "python"
        assert result.confidence >= 0.9

    def test_null_bytes_in_content(self):
        """Content with null bytes should be handled."""
        content = b"normal text\x00more text"
        result = detect_language("file.txt", ".txt", content=content)
        assert isinstance(result, LanguageResult)

    def test_extremely_long_shebang(self):
        """Very long shebang lines should be handled."""
        # Create a very long path
        long_path = "/" + "/".join(["a" * 50] * 20) + "/python"
        content = f"#!{long_path}\nprint('hello')".encode()
        result = detect_language("script", "", content=content)
        # Should not crash
        assert isinstance(result, LanguageResult)

    def test_utf8_content_handling(self):
        """UTF-8 content should be handled correctly."""
        content = "#!/usr/bin/env python\n# -*- coding: utf-8 -*-\nprint('héllo wörld 你好')".encode('utf-8')
        result = detect_language("script", "", content=content)
        assert result.language == "python"

    def test_latin1_content_handling(self):
        """Latin-1 encoded content should be handled."""
        content = b"#!/usr/bin/env python\nprint('caf\xe9')"
        result = detect_language("script", "", content=content)
        assert result.language == "python"

    def test_mixed_line_endings(self):
        """Mixed line endings should be handled."""
        content = b"#!/usr/bin/env python\r\nprint('line1')\nprint('line2')\r\nprint('line3')"
        result = detect_language("script", "", content=content)
        assert result.language == "python"


# =============================================================================
# Large Repository Simulation Tests
# =============================================================================


class TestLargeRepositorySimulation:
    """Simulate large repository scenarios."""

    @pytest.fixture
    def many_files_repo(self, tmp_path):
        """Create a repo with many files in different languages."""
        # Create 100 Python files
        python_dir = tmp_path / "python_modules"
        python_dir.mkdir()
        for i in range(50):
            (python_dir / f"module_{i}.py").write_bytes(f"# Module {i}\nx = {i}".encode())

        # Create 50 JavaScript files
        js_dir = tmp_path / "js_modules"
        js_dir.mkdir()
        for i in range(30):
            (js_dir / f"module_{i}.js").write_bytes(f"// Module {i}\nconst x = {i};".encode())

        # Create 30 TypeScript files
        ts_dir = tmp_path / "ts_modules"
        ts_dir.mkdir()
        for i in range(20):
            (ts_dir / f"module_{i}.ts").write_bytes(f"// Module {i}\nconst x: number = {i};".encode())

        return tmp_path

    def test_many_files_performance(self, many_files_repo):
        """Detection should handle many files efficiently."""
        import time

        files_to_test = []
        for py_file in (many_files_repo / "python_modules").glob("*.py"):
            files_to_test.append((py_file.name, ".py"))
        for js_file in (many_files_repo / "js_modules").glob("*.js"):
            files_to_test.append((js_file.name, ".js"))

        start = time.time()
        results = []
        for filename, ext in files_to_test:
            result = detect_language(filename, ext)
            results.append(result)
        elapsed = time.time() - start

        # Should complete in reasonable time (< 1 second for ~80 files)
        assert elapsed < 2.0, f"Detection took too long: {elapsed}s"
        assert len(results) == len(files_to_test)

    def test_language_distribution_accuracy(self, many_files_repo):
        """Language distribution should be accurate for many files."""
        languages = []

        for py_file in (many_files_repo / "python_modules").glob("*.py"):
            result = detect_language(py_file.name, ".py")
            languages.append(result.language)

        for js_file in (many_files_repo / "js_modules").glob("*.js"):
            result = detect_language(js_file.name, ".js")
            languages.append(result.language)

        for ts_file in (many_files_repo / "ts_modules").glob("*.ts"):
            result = detect_language(ts_file.name, ".ts")
            languages.append(result.language)

        distribution = get_language_distribution(languages)

        assert distribution["python"] == 50
        assert distribution["javascript"] == 30
        assert distribution["typescript"] == 20


# =============================================================================
# Vendor and Generated Detection in Context
# =============================================================================


class TestVendorGeneratedInContext:
    """Test vendor and generated detection in realistic contexts."""

    @pytest.fixture
    def node_project(self, tmp_path):
        """Create a Node.js project with vendor files."""
        # Source
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "index.js").write_bytes(b"console.log('app');")

        # node_modules (vendor)
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "lodash").mkdir()
        (tmp_path / "node_modules" / "lodash" / "lodash.js").write_bytes(b"// lodash")

        # Lock file (generated)
        (tmp_path / "package-lock.json").write_bytes(b'{"lockfileVersion": 2}')

        # Minified (generated)
        (tmp_path / "dist").mkdir()
        (tmp_path / "dist" / "app.min.js").write_bytes(b"!function(){}")

        return tmp_path

    def test_vendor_files_detected(self, node_project):
        """Files in node_modules should be detected as vendor."""
        assert is_vendor_file("node_modules/lodash/lodash.js") is True
        assert is_vendor_file("src/index.js") is False

    def test_generated_files_detected(self, node_project):
        """Lock files and minified files should be detected as generated."""
        assert is_generated_file("package-lock.json") is True
        assert is_generated_file("app.min.js") is True
        assert is_generated_file("src/index.js") is False

    def test_vendor_language_still_detected(self, node_project):
        """Vendor files should still have language detected."""
        result = detect_language("lodash.js", ".js")
        assert result.language == "javascript"
