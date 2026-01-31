#!/usr/bin/env python3
"""
Build Synthetic Test Repositories for Layout Scanner Evaluation.

Creates a set of test repositories with controlled characteristics
for evaluating classification accuracy, performance, and edge case handling.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional


# Base directory for synthetic repos
EVAL_REPOS_DIR = Path(__file__).parent.parent / "eval-repos" / "synthetic"
GROUND_TRUTH_DIR = Path(__file__).parent.parent / "evaluation" / "ground-truth"


def create_file(path: Path, content: str = "") -> None:
    """Create a file with given content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def create_repo(name: str, structure: Dict) -> Path:
    """
    Create a synthetic repository with given structure.

    Args:
        name: Repository name
        structure: Dict describing the repository structure

    Returns:
        Path to created repository
    """
    repo_path = EVAL_REPOS_DIR / name

    # Clean existing
    if repo_path.exists():
        shutil.rmtree(repo_path)

    repo_path.mkdir(parents=True, exist_ok=True)

    # Create files
    for file_path, content in structure.get("files", {}).items():
        create_file(repo_path / file_path, content or "")

    # Create empty directories
    for dir_path in structure.get("empty_dirs", []):
        (repo_path / dir_path).mkdir(parents=True, exist_ok=True)

    return repo_path


def build_small_clean() -> Dict:
    """Small clean repository with only source files."""
    files = {
        "src/main.py": "# Main entry point\nprint('Hello')\n",
        "src/utils.py": "# Utilities\ndef helper(): pass\n",
        "src/models/user.py": "class User: pass\n",
        "src/models/product.py": "class Product: pass\n",
        "src/services/auth.py": "class AuthService: pass\n",
        "README.md": "# Small Clean Repo\n\nA simple repository.\n",
    }

    return {
        "files": files,
        "empty_dirs": [],
        "ground_truth": {
            "repository": "small-clean",
            "description": "Small clean repository with only source files",
            "expected": {
                "total_files": 6,
                "total_directories": 4,  # root, src, src/models, src/services
                "max_depth": 3,
                "classifications": {
                    "source": 5,
                    "docs": 1,
                },
                "specific_files": {
                    "src/main.py": {"classification": "source", "language": "python"},
                    "README.md": {"classification": "docs", "language": "markdown"},
                },
            },
            "thresholds": {
                "classification_accuracy": 0.95,
                "count_tolerance": 0,
                "max_scan_time_seconds": 1.0,
            },
        },
    }


def build_mixed_types() -> Dict:
    """Repository with mixed file types for classification testing."""
    files = {
        # Source files
        "src/app.ts": "export const app = {};\n",
        "src/index.js": "module.exports = {};\n",
        "src/models/user.py": "class User: pass\n",
        "src/services/api.go": "package main\n",
        "src/core/engine.rs": "fn main() {}\n",

        # Test files
        "tests/test_app.py": "def test_app(): pass\n",
        "tests/app.test.ts": "describe('app', () => {});\n",
        "tests/api_test.go": "func TestAPI(t *testing.T) {}\n",
        "src/__tests__/user.test.js": "test('user', () => {});\n",

        # Config files
        "package.json": '{"name": "test"}\n',
        "tsconfig.json": '{"compilerOptions": {}}\n',
        "Makefile": "all:\n\techo hello\n",
        ".gitignore": "node_modules/\n*.pyc\n",
        ".eslintrc.json": '{"rules": {}}\n',
        "docker-compose.yml": "version: '3'\n",

        # Generated files
        "dist/bundle.min.js": "/* minified */\n",
        "src/generated/models.g.cs": "// Generated\npublic class Model {}\n",
        "package-lock.json": '{"lockfileVersion": 2}\n',

        # Docs
        "README.md": "# Mixed Types\n",
        "docs/api.md": "# API Docs\n",
        "CHANGELOG.md": "# Changelog\n",
        "LICENSE": "MIT License\n",
    }

    return {
        "files": files,
        "empty_dirs": ["build", "coverage"],
        "ground_truth": {
            "repository": "mixed-types",
            "description": "Repository with mixed file types for classification testing",
            "expected": {
                "total_files": 22,
                "total_directories": 12,  # root + src + src/models + src/services + src/core + src/__tests__ + src/generated + tests + dist + docs + build + coverage
                "max_depth": 3,
                "classifications": {
                    "source": 5,
                    "test": 4,
                    "config": 6,
                    "generated": 3,
                    "docs": 4,
                },
                "specific_files": {
                    "src/app.ts": {"classification": "source", "language": "typescript"},
                    "tests/test_app.py": {"classification": "test", "language": "python"},
                    "package.json": {"classification": "config", "language": "json"},
                    "dist/bundle.min.js": {"classification": "generated", "language": "javascript"},
                    "README.md": {"classification": "docs", "language": "markdown"},
                },
            },
            "thresholds": {
                "classification_accuracy": 0.90,
                "count_tolerance": 0,
                "max_scan_time_seconds": 1.0,
            },
        },
    }


def build_deep_nesting() -> Dict:
    """Repository with deep directory nesting."""
    files = {}

    # Create deeply nested structure
    deep_path = "level1/level2/level3/level4/level5/level6/level7/level8/level9/level10"
    for i in range(1, 11):
        path = "/".join([f"level{j}" for j in range(1, i + 1)])
        files[f"{path}/file_{i}.py"] = f"# Level {i}\n"

    # Add some regular files
    files["src/main.py"] = "# Main\n"
    files["README.md"] = "# Deep Nesting Test\n"

    return {
        "files": files,
        "empty_dirs": [f"{deep_path}/level11/level12/level13/level14/level15"],
        "ground_truth": {
            "repository": "deep-nesting",
            "description": "Repository with deep directory nesting (20+ levels)",
            "expected": {
                "total_files": 12,
                "total_directories": 17,  # 15 levels + src + root
                "max_depth": 15,
                "classifications": {
                    "source": 11,
                    "docs": 1,
                },
            },
            "thresholds": {
                "classification_accuracy": 0.95,
                "count_tolerance": 0,
                "max_scan_time_seconds": 1.0,
            },
        },
    }


def build_vendor_heavy() -> Dict:
    """Repository with heavy vendor/node_modules content."""
    files = {
        # Source files
        "src/index.js": "import lodash from 'lodash';\n",
        "src/app.js": "export default {};\n",

        # Vendor files (node_modules style)
        "node_modules/lodash/index.js": "module.exports = {};\n",
        "node_modules/lodash/package.json": '{"name": "lodash"}\n',
        "node_modules/lodash/lodash.min.js": "/* minified lodash */\n",
        "node_modules/react/index.js": "module.exports = {};\n",
        "node_modules/react/package.json": '{"name": "react"}\n',
        "node_modules/react/cjs/react.development.js": "/* react */\n",

        # Another vendor directory
        "vendor/jquery/jquery.js": "/* jQuery */\n",
        "vendor/jquery/package.json": '{"name": "jquery"}\n',

        # Third party
        "third_party/lib/helper.js": "// helper\n",

        # Regular files
        "package.json": '{"dependencies": {}}\n',
        "README.md": "# Vendor Heavy\n",
    }

    return {
        "files": files,
        "empty_dirs": [],
        "ground_truth": {
            "repository": "vendor-heavy",
            "description": "Repository with heavy vendor/node_modules content",
            "expected": {
                "total_files": 13,
                "total_directories": 10,  # root + src + node_modules + node_modules/lodash + node_modules/react + node_modules/react/cjs + vendor + vendor/jquery + third_party + third_party/lib
                "max_depth": 4,
                "classifications": {
                    "source": 2,
                    "vendor": 9,
                    "config": 1,
                    "docs": 1,
                },
                "specific_files": {
                    "node_modules/lodash/index.js": {"classification": "vendor", "language": "javascript"},
                    "vendor/jquery/jquery.js": {"classification": "vendor", "language": "javascript"},
                    "src/index.js": {"classification": "source", "language": "javascript"},
                },
            },
            "thresholds": {
                "classification_accuracy": 0.95,
                "count_tolerance": 0,
                "max_scan_time_seconds": 1.0,
            },
        },
    }


def build_generated_code() -> Dict:
    """Repository with various generated code patterns."""
    files = {
        # C# generated
        "src/Models.g.cs": "// <auto-generated/>\npublic class Model {}\n",
        "src/ViewModels.Designer.cs": "// Auto-generated\npartial class VM {}\n",

        # Protobuf generated
        "src/proto/message_pb2.py": "# Generated by protoc\n",
        "src/proto/message_pb2_grpc.py": "# Generated by gRPC\n",
        "src/proto/message.pb.go": "// Code generated by protoc-gen-go\n",

        # JS/TS generated
        "dist/app.bundle.js": "/* bundled */\n",
        "dist/styles.min.css": "/* minified */\n",
        "types/index.d.ts": "declare module 'app';\n",

        # Lock files
        "package-lock.json": '{"lockfileVersion": 2}\n',
        "yarn.lock": "# yarn lock\n",
        "Cargo.lock": "# cargo lock\n",
        "go.sum": "# go sum\n",

        # Source files
        "src/main.py": "# Main\n",
        "src/app.ts": "// App\n",
        "README.md": "# Generated Code\n",
    }

    return {
        "files": files,
        "empty_dirs": ["build", "out"],
        "ground_truth": {
            "repository": "generated-code",
            "description": "Repository with various generated code patterns",
            "expected": {
                "total_files": 15,
                "total_directories": 7,
                "max_depth": 3,
                "classifications": {
                    "source": 2,
                    "generated": 12,
                    "docs": 1,
                },
                "specific_files": {
                    "src/Models.g.cs": {"classification": "generated", "language": "csharp"},
                    "src/proto/message_pb2.py": {"classification": "generated", "language": "python"},
                    "package-lock.json": {"classification": "generated", "language": "json"},
                    "types/index.d.ts": {"classification": "generated", "language": "typescript"},
                },
            },
            "thresholds": {
                "classification_accuracy": 0.90,
                "count_tolerance": 0,
                "max_scan_time_seconds": 1.0,
            },
        },
    }


def build_edge_cases() -> Dict:
    """Repository with edge cases: unicode, special chars, symlinks, etc."""
    files = {
        # Unicode filenames
        "docs/日本語.md": "# Japanese\n",
        "docs/émojis_🎉.txt": "Celebration!\n",
        "src/über.py": "# German\n",

        # Special characters
        "src/file with spaces.py": "# Spaces\n",
        "src/file-with-dashes.py": "# Dashes\n",
        "src/file_with_underscores.py": "# Underscores\n",
        "config/app (copy).json": '{"copy": true}\n',
        "data/test[1].txt": "Test 1\n",

        # Hidden files
        ".env": "SECRET=value\n",
        ".env.local": "LOCAL=value\n",
        ".hidden/config.json": '{"hidden": true}\n',

        # Regular files
        "src/main.py": "# Main\n",
        "README.md": "# Edge Cases\n",
    }

    return {
        "files": files,
        "empty_dirs": ["empty", "also-empty/nested-empty"],
        "ground_truth": {
            "repository": "edge-cases",
            "description": "Repository with edge cases: unicode, special chars, etc.",
            "expected": {
                "total_files": 13,
                "total_directories": 9,  # root + src + docs + config + data + .hidden + empty + also-empty + also-empty/nested-empty
                "max_depth": 2,
                "classifications": {
                    "source": 5,
                    "docs": 3,
                    "config": 5,
                },
            },
            "thresholds": {
                "classification_accuracy": 0.85,
                "count_tolerance": 0,
                "max_scan_time_seconds": 1.0,
            },
        },
    }


def build_mixed_language() -> Dict:
    """Multi-language repository with Python, JavaScript, C#, Go, Rust."""
    files = {
        # Python source
        "src/python/main.py": "#!/usr/bin/env python3\n\ndef main():\n    print('Hello from Python')\n\nif __name__ == '__main__':\n    main()\n",
        "src/python/utils.py": "# Utility functions\n\ndef helper():\n    return 42\n",
        "src/python/__init__.py": "# Python package\n",

        # JavaScript source
        "src/javascript/index.js": "// Main entry point\nexport default function main() {\n    console.log('Hello from JS');\n}\n",
        "src/javascript/helper.mjs": "// ES Module helper\nexport const help = () => 'helping';\n",
        "src/javascript/types.d.ts": "// TypeScript declarations (generated)\ndeclare module 'app' {\n    export function main(): void;\n}\n",

        # C# source
        "src/csharp/Program.cs": "using System;\n\nnamespace App\n{\n    class Program\n    {\n        static void Main() => Console.WriteLine(\"Hello from C#\");\n    }\n}\n",
        "src/csharp/Models.cs": "namespace App.Models\n{\n    public class User { public string Name { get; set; } }\n}\n",
        "src/csharp/Service.g.cs": "// <auto-generated/>\n// Generated by a tool\nnamespace App.Generated { public class Service {} }\n",

        # Go source
        "src/go/main.go": "package main\n\nimport \"fmt\"\n\nfunc main() {\n    fmt.Println(\"Hello from Go\")\n}\n",
        "src/go/utils.go": "package main\n\nfunc Helper() int {\n    return 42\n}\n",

        # Rust source
        "src/rust/main.rs": "fn main() {\n    println!(\"Hello from Rust\");\n}\n",
        "src/rust/lib.rs": "pub fn helper() -> i32 {\n    42\n}\n",

        # Test files
        "tests/test_main.py": "import pytest\n\ndef test_main():\n    assert True\n",
        "tests/main.test.js": "describe('main', () => {\n    it('should work', () => {\n        expect(true).toBe(true);\n    });\n});\n",
        "tests/ProgramTests.cs": "using Xunit;\n\npublic class ProgramTests\n{\n    [Fact]\n    public void TestMain() => Assert.True(true);\n}\n",
        "tests/main_test.go": "package main\n\nimport \"testing\"\n\nfunc TestMain(t *testing.T) {\n    t.Log(\"Test passed\")\n}\n",

        # Config files
        "config/settings.json": '{\n    "debug": true,\n    "log_level": "info"\n}\n',
        "config/config.yaml": "app:\n  name: mixed-language\n  version: 1.0.0\n",
        "config/app.toml": "[app]\nname = \"mixed-language\"\nversion = \"1.0.0\"\n",

        # Project config files at root
        "package.json": '{\n    "name": "mixed-language",\n    "version": "1.0.0",\n    "scripts": {\n        "test": "jest"\n    }\n}\n',
        "go.mod": "module mixed-language\n\ngo 1.21\n",
        "Cargo.toml": "[package]\nname = \"mixed-language\"\nversion = \"0.1.0\"\nedition = \"2021\"\n",
        "project.csproj": "<Project Sdk=\"Microsoft.NET.Sdk\">\n    <PropertyGroup>\n        <OutputType>Exe</OutputType>\n        <TargetFramework>net8.0</TargetFramework>\n    </PropertyGroup>\n</Project>\n",
        "requirements.txt": "# Python dependencies\npytest>=7.0\n",
        "Makefile": ".PHONY: all test clean\n\nall:\n\t@echo \"Building...\"\n\ntest:\n\t@echo \"Testing...\"\n\nclean:\n\t@echo \"Cleaning...\"\n",

        # Docs
        "docs/api.md": "# API Documentation\n\n## Overview\n\nThis project demonstrates multi-language support.\n",
        "README.md": "# Mixed Language Repository\n\nA repository with Python, JavaScript, C#, Go, and Rust code.\n",
    }

    return {
        "files": files,
        "empty_dirs": [],
        "ground_truth": {
            "repository": "mixed-language",
            "description": "Multi-language repository with Python, JavaScript, C#, Go, Rust",
            "expected": {
                "total_files": 28,  # 11 source + 4 test + 2 generated + 9 config + 2 docs
                # Directories: root, src, src/python, src/javascript, src/csharp, src/go, src/rust,
                #              tests, config, docs = 10 directories
                "total_directories": 10,
                "max_depth": 3,
                "classifications": {
                    "source": 11,  # main.py, utils.py, __init__.py, index.js, helper.mjs, Program.cs, Models.cs, main.go, utils.go, main.rs, lib.rs
                    "test": 4,     # test_main.py, main.test.js, ProgramTests.cs, main_test.go
                    "config": 9,   # settings.json, config.yaml, app.toml, package.json, go.mod, Cargo.toml, project.csproj, requirements.txt, Makefile
                    "generated": 2,  # types.d.ts (declaration), Service.g.cs
                    "docs": 2,     # api.md, README.md
                },
                "specific_files": {
                    "src/python/main.py": {"classification": "source", "language": "python"},
                    "src/javascript/index.js": {"classification": "source", "language": "javascript"},
                    "src/csharp/Program.cs": {"classification": "source", "language": "csharp"},
                    "src/go/main.go": {"classification": "source", "language": "go"},
                    "src/rust/main.rs": {"classification": "source", "language": "rust"},
                    "tests/test_main.py": {"classification": "test", "language": "python"},
                    "src/csharp/Service.g.cs": {"classification": "generated", "language": "csharp"},
                    "package.json": {"classification": "config", "language": "json"},
                    "README.md": {"classification": "docs", "language": "markdown"},
                },
            },
            "thresholds": {
                "classification_accuracy": 0.90,
                "count_tolerance": 0,
                "max_scan_time_seconds": 2.0,
            },
        },
    }


def build_config_heavy() -> Dict:
    """Configuration-heavy repository with extensive config files."""
    files = {
        # IDE configs - VS Code
        ".vscode/settings.json": '{\n    "editor.formatOnSave": true,\n    "editor.tabSize": 4\n}\n',
        ".vscode/launch.json": '{\n    "version": "0.2.0",\n    "configurations": [\n        {\n            "type": "python",\n            "request": "launch",\n            "name": "Python: Current File"\n        }\n    ]\n}\n',
        ".vscode/extensions.json": '{\n    "recommendations": [\n        "ms-python.python",\n        "dbaeumer.vscode-eslint"\n    ]\n}\n',

        # CI/CD - GitHub Actions
        ".github/workflows/ci.yml": "name: CI\n\non: [push, pull_request]\n\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - name: Build\n        run: make build\n",
        ".github/workflows/release.yml": "name: Release\n\non:\n  push:\n    tags:\n      - 'v*'\n\njobs:\n  release:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n",
        ".github/workflows/codeql.yml": "name: CodeQL\n\non:\n  schedule:\n    - cron: '0 0 * * 0'\n\njobs:\n  analyze:\n    runs-on: ubuntu-latest\n",

        # Docker configs
        "docker/Dockerfile": "FROM python:3.12-slim\n\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt\n\nCMD [\"python\", \"src/app.py\"]\n",
        "docker/Dockerfile.dev": "FROM python:3.12\n\nWORKDIR /app\nRUN pip install -e .[dev]\n\nCMD [\"python\", \"-m\", \"pytest\"]\n",
        "docker/docker-compose.yml": "version: '3.8'\n\nservices:\n  app:\n    build: .\n    ports:\n      - \"8000:8000\"\n  db:\n    image: postgres:15\n",

        # Terraform/IaC
        "terraform/main.tf": "provider \"aws\" {\n  region = var.region\n}\n\nresource \"aws_s3_bucket\" \"main\" {\n  bucket = var.bucket_name\n}\n",
        "terraform/variables.tf": "variable \"region\" {\n  default = \"us-east-1\"\n}\n\nvariable \"bucket_name\" {\n  type = string\n}\n",
        "terraform/outputs.tf": "output \"bucket_arn\" {\n  value = aws_s3_bucket.main.arn\n}\n",

        # Kubernetes configs
        "kubernetes/deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: app\nspec:\n  replicas: 3\n  template:\n    spec:\n      containers:\n        - name: app\n          image: app:latest\n",
        "kubernetes/service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: app-service\nspec:\n  type: LoadBalancer\n  ports:\n    - port: 80\n",
        "kubernetes/ingress.yaml": "apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: app-ingress\nspec:\n  rules:\n    - host: app.example.com\n",

        # Environment configs
        "config/default.json": '{\n    "port": 3000,\n    "debug": false\n}\n',
        "config/production.json": '{\n    "port": 8000,\n    "debug": false,\n    "log_level": "error"\n}\n',
        "config/development.json": '{\n    "port": 3000,\n    "debug": true,\n    "log_level": "debug"\n}\n',
        "config/test.json": '{\n    "port": 3001,\n    "debug": true,\n    "log_level": "debug"\n}\n',

        # Minimal source file
        "src/app.py": "#!/usr/bin/env python3\n\ndef main():\n    print('App running')\n\nif __name__ == '__main__':\n    main()\n",

        # Root config files
        ".env.example": "# Environment variables\nDATABASE_URL=postgres://localhost/db\nSECRET_KEY=changeme\n",
        ".editorconfig": "[*]\nindent_style = space\nindent_size = 4\nend_of_line = lf\ncharset = utf-8\n",
        ".gitignore": "# Python\n*.pyc\n__pycache__/\n.venv/\n\n# Node\nnode_modules/\n\n# IDE\n.idea/\n",
        ".prettierrc": '{\n    "semi": true,\n    "singleQuote": true,\n    "tabWidth": 2\n}\n',
        ".eslintrc.json": '{\n    "extends": ["eslint:recommended"],\n    "env": {\n        "node": true\n    }\n}\n',
        "tsconfig.json": '{\n    "compilerOptions": {\n        "target": "ES2020",\n        "module": "commonjs",\n        "strict": true\n    }\n}\n',
        "babel.config.js": "module.exports = {\n    presets: [\n        ['@babel/preset-env', { targets: { node: 'current' } }]\n    ]\n};\n",
        "webpack.config.js": "const path = require('path');\n\nmodule.exports = {\n    entry: './src/index.js',\n    output: {\n        path: path.resolve(__dirname, 'dist'),\n        filename: 'bundle.js'\n    }\n};\n",
        "jest.config.js": "module.exports = {\n    testEnvironment: 'node',\n    coverageThreshold: {\n        global: {\n            branches: 80\n        }\n    }\n};\n",
        "package.json": '{\n    "name": "config-heavy",\n    "version": "1.0.0",\n    "scripts": {\n        "test": "jest",\n        "build": "webpack"\n    }\n}\n',
        "pyproject.toml": "[project]\nname = \"config-heavy\"\nversion = \"1.0.0\"\n\n[tool.pytest.ini_options]\ntestpaths = [\"tests\"]\n\n[tool.black]\nline-length = 100\n",
        "Makefile": ".PHONY: all build test deploy\n\nall: build test\n\nbuild:\n\t@echo \"Building...\"\n\ntest:\n\t@echo \"Testing...\"\n\ndeploy:\n\t@echo \"Deploying...\"\n",
        "Jenkinsfile": "pipeline {\n    agent any\n    stages {\n        stage('Build') {\n            steps {\n                sh 'make build'\n            }\n        }\n        stage('Test') {\n            steps {\n                sh 'make test'\n            }\n        }\n    }\n}\n",

        # Docs
        "README.md": "# Config Heavy Repository\n\nA repository demonstrating extensive configuration patterns.\n",
    }

    return {
        "files": files,
        "empty_dirs": [],
        "ground_truth": {
            "repository": "config-heavy",
            "description": "Configuration-heavy repository with extensive config files",
            "expected": {
                "total_files": 34,  # 1 source + 28 config + 4 ci + 1 docs
                # Directories: root, .vscode, .github, .github/workflows, docker, terraform,
                #              kubernetes, config, src = 9 directories
                "total_directories": 9,
                "max_depth": 3,
                "classifications": {
                    "source": 1,   # app.py only
                    "config": 28,  # IDE, docker, terraform, kubernetes, root configs
                    "ci": 4,       # GitHub workflows (3) + Jenkinsfile
                    "docs": 1,     # README.md
                },
                "specific_files": {
                    "src/app.py": {"classification": "source", "language": "python"},
                    ".vscode/settings.json": {"classification": "config", "language": "json"},
                    ".github/workflows/ci.yml": {"classification": "ci", "language": "yaml"},
                    "docker/Dockerfile": {"classification": "config"},
                    "terraform/main.tf": {"classification": "config", "language": "hcl"},
                    "kubernetes/deployment.yaml": {"classification": "config", "language": "yaml"},
                    "package.json": {"classification": "config", "language": "json"},
                    "Jenkinsfile": {"classification": "ci"},
                    "README.md": {"classification": "docs", "language": "markdown"},
                },
            },
            "thresholds": {
                "classification_accuracy": 0.85,
                "count_tolerance": 0,
                "max_scan_time_seconds": 2.0,
            },
        },
    }


def save_ground_truth(name: str, ground_truth: Dict) -> None:
    """Save ground truth to JSON file."""
    GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)
    path = GROUND_TRUTH_DIR / f"{name}.json"
    with open(path, "w") as f:
        json.dump(ground_truth, f, indent=2)
    print(f"  Ground truth: {path}")


def build_all_repos() -> None:
    """Build all synthetic test repositories."""
    print("Building synthetic test repositories...")

    repos = [
        ("small-clean", build_small_clean),
        ("mixed-types", build_mixed_types),
        ("deep-nesting", build_deep_nesting),
        ("vendor-heavy", build_vendor_heavy),
        ("generated-code", build_generated_code),
        ("edge-cases", build_edge_cases),
        ("mixed-language", build_mixed_language),
        ("config-heavy", build_config_heavy),
    ]

    for name, builder in repos:
        print(f"\nBuilding {name}...")
        spec = builder()
        repo_path = create_repo(name, spec)
        print(f"  Repository: {repo_path}")

        if "ground_truth" in spec:
            save_ground_truth(name, spec["ground_truth"])

    print("\nDone! Built", len(repos), "repositories.")


def main():
    """Main entry point."""
    build_all_repos()


if __name__ == "__main__":
    main()
