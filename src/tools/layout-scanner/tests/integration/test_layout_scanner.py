"""
Integration tests for layout_scanner.py
"""

import json
import pytest
from pathlib import Path

from scripts.layout_scanner import scan_repository, main
from scripts.config_loader import ScannerConfig, IgnoreConfig, ClassificationConfig


class TestScanRepository:
    """Integration tests for scan_repository function."""

    def test_scan_empty_repo(self, tmp_path):
        """Should scan empty repository."""
        output, duration = scan_repository(tmp_path)

        assert output["schema_version"] == "1.0.0"
        assert output["statistics"]["total_files"] == 0
        assert output["statistics"]["total_directories"] == 1
        assert duration >= 0

    def test_scan_simple_repo(self, tmp_path):
        """Should scan simple repository structure."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hello')")
        (tmp_path / "README.md").write_text("# Test")

        output, duration = scan_repository(tmp_path)

        assert output["statistics"]["total_files"] == 2
        assert output["statistics"]["total_directories"] == 2
        assert "src/main.py" in output["files"]
        assert "README.md" in output["files"]
        assert "src" in output["directories"]

    def test_scan_with_classification(self, tmp_path):
        """Should classify files correctly."""
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()
        (tmp_path / "src" / "main.py").write_text("code")
        (tmp_path / "tests" / "test_main.py").write_text("tests")
        (tmp_path / "README.md").write_text("docs")

        output, _ = scan_repository(tmp_path)

        # Check file classifications
        assert output["files"]["src/main.py"]["classification"] == "source"
        assert output["files"]["tests/test_main.py"]["classification"] == "test"
        assert output["files"]["README.md"]["classification"] == "docs"

    def test_scan_with_language_detection(self, tmp_path):
        """Should detect languages correctly."""
        (tmp_path / "main.py").write_text("python")
        (tmp_path / "app.js").write_text("javascript")
        (tmp_path / "service.ts").write_text("typescript")

        output, _ = scan_repository(tmp_path)

        assert output["files"]["main.py"]["language"] == "python"
        assert output["files"]["app.js"]["language"] == "javascript"
        assert output["files"]["service.ts"]["language"] == "typescript"

    def test_scan_respects_gitignore(self, tmp_path):
        """Should respect .gitignore when scanning."""
        (tmp_path / "src").mkdir()
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "src" / "main.py").write_text("code")
        (tmp_path / "node_modules" / "pkg").mkdir()
        (tmp_path / "node_modules" / "pkg" / "index.js").write_text("module")
        (tmp_path / ".gitignore").write_text("node_modules/")

        output, _ = scan_repository(tmp_path)

        # src should be present
        assert "src/main.py" in output["files"]
        # node_modules should be ignored
        assert "node_modules/pkg/index.js" not in output["files"]

    def test_scan_with_custom_config(self, tmp_path):
        """Should use custom configuration."""
        (tmp_path / "myvendor").mkdir()
        (tmp_path / "myvendor" / "lib.py").write_text("vendor code")
        (tmp_path / "src" / "main.py").parents[0].mkdir()
        (tmp_path / "src" / "main.py").write_text("code")

        config = ScannerConfig(
            classification=ClassificationConfig(
                custom_path_rules={"vendor": ["myvendor/"]},
            )
        )

        output, _ = scan_repository(tmp_path, config=config)

        assert output["files"]["myvendor/lib.py"]["classification"] == "vendor"
        assert output["files"]["src/main.py"]["classification"] == "source"

    def test_scan_with_ignore_config(self, tmp_path):
        """Should respect ignore configuration."""
        (tmp_path / "src").mkdir()
        (tmp_path / "logs").mkdir()
        (tmp_path / "src" / "main.py").write_text("code")
        (tmp_path / "logs" / "app.log").write_text("logs")

        config = ScannerConfig(
            ignore=IgnoreConfig(additional_patterns=["logs/"])
        )

        output, _ = scan_repository(tmp_path, config=config)

        assert "src/main.py" in output["files"]
        assert "logs/app.log" not in output["files"]

    def test_scan_hierarchy_structure(self, tmp_path):
        """Should build correct hierarchy structure."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "lib").mkdir()
        (tmp_path / "src" / "main.py").write_text("code")
        (tmp_path / "src" / "lib" / "utils.py").write_text("utils")

        output, _ = scan_repository(tmp_path)

        hierarchy = output["hierarchy"]
        assert hierarchy["root_id"] == "d-000000000000"
        assert hierarchy["total_files"] == 2
        assert hierarchy["total_directories"] == 3

    def test_scan_statistics(self, tmp_path):
        """Should compute correct statistics."""
        (tmp_path / "a.py").write_text("x" * 100)
        (tmp_path / "b.py").write_text("x" * 200)
        (tmp_path / "c.js").write_text("x" * 50)

        output, _ = scan_repository(tmp_path)

        stats = output["statistics"]
        assert stats["total_files"] == 3
        assert stats["total_size_bytes"] == 350
        assert stats["by_language"]["python"] == 2
        assert stats["by_language"]["javascript"] == 1

    def test_scan_nonexistent_path_raises(self, tmp_path):
        """Should raise for nonexistent path."""
        with pytest.raises(ValueError):
            scan_repository(tmp_path / "nonexistent")

    def test_scan_output_valid_json(self, tmp_path):
        """Output should be valid JSON."""
        (tmp_path / "test.py").write_text("code")

        output, _ = scan_repository(tmp_path)

        # Should be serializable
        json_str = json.dumps(output)
        loaded = json.loads(json_str)
        assert loaded["statistics"]["total_files"] == 1


class TestScanRepositoryDirectoryClassification:
    """Tests for directory classification in scan_repository."""

    def test_directory_classification_majority(self, tmp_path):
        """Directories should be classified by majority vote."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "a.py").write_text("1")
        (tmp_path / "src" / "b.py").write_text("2")
        (tmp_path / "src" / "c.py").write_text("3")

        output, _ = scan_repository(tmp_path)

        # src should be classified as source (all .py files)
        assert output["directories"]["src"]["classification"] == "source"

    def test_empty_directory_classification(self, tmp_path):
        """Empty directories with unknown names should be classified as other."""
        (tmp_path / "empty").mkdir()

        output, _ = scan_repository(tmp_path)

        assert output["directories"]["empty"]["classification"] == "other"

    def test_empty_build_directory_classification(self, tmp_path):
        """Empty build/ directory should be classified as 'generated' based on name."""
        (tmp_path / "build").mkdir()

        output, _ = scan_repository(tmp_path)

        assert output["directories"]["build"]["classification"] == "generated"
        assert "directory_name" in output["directories"]["build"]["classification_reason"]

    def test_empty_out_directory_classification(self, tmp_path):
        """Empty out/ directory should be classified as 'generated' based on name."""
        (tmp_path / "out").mkdir()

        output, _ = scan_repository(tmp_path)

        assert output["directories"]["out"]["classification"] == "generated"
        assert "directory_name" in output["directories"]["out"]["classification_reason"]

    def test_empty_src_directory_classification(self, tmp_path):
        """Empty src/ directory should be classified as 'source' based on name."""
        (tmp_path / "src").mkdir()

        output, _ = scan_repository(tmp_path)

        assert output["directories"]["src"]["classification"] == "source"
        assert "directory_name" in output["directories"]["src"]["classification_reason"]

    def test_empty_tests_directory_classification(self, tmp_path):
        """Empty tests/ directory should be classified as 'test' based on name."""
        (tmp_path / "tests").mkdir()

        output, _ = scan_repository(tmp_path)

        assert output["directories"]["tests"]["classification"] == "test"
        assert "directory_name" in output["directories"]["tests"]["classification_reason"]


class TestMain:
    """Integration tests for main CLI function."""

    def test_main_basic(self, tmp_path, capsys):
        """Main should run successfully."""
        (tmp_path / "test.py").write_text("code")

        result = main([str(tmp_path)])

        assert result == 0
        captured = capsys.readouterr()
        # Should output JSON to stdout
        output = json.loads(captured.out)
        assert "statistics" in output

    def test_main_quiet_mode(self, tmp_path, capsys):
        """Quiet mode should suppress stderr."""
        (tmp_path / "test.py").write_text("code")

        result = main([str(tmp_path), "-q"])

        assert result == 0
        captured = capsys.readouterr()
        # stderr should be empty in quiet mode
        assert captured.err == ""

    def test_main_output_file(self, tmp_path):
        """Should write to output file."""
        (tmp_path / "test.py").write_text("code")
        output_path = tmp_path / "output.json"

        result = main([str(tmp_path), "-o", str(output_path), "-q"])

        assert result == 0
        assert output_path.exists()
        with open(output_path) as f:
            output = json.load(f)
        assert output["statistics"]["total_files"] == 1

    def test_main_with_ignore_flag(self, tmp_path, capsys):
        """Should respect --ignore flag."""
        (tmp_path / "src").mkdir()
        (tmp_path / "logs").mkdir()
        (tmp_path / "src" / "main.py").write_text("code")
        (tmp_path / "logs" / "app.log").write_text("logs")

        result = main([str(tmp_path), "--ignore", "logs/", "-q"])

        assert result == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "logs/app.log" not in output["files"]

    def test_main_no_gitignore_flag(self, tmp_path, capsys):
        """Should respect --no-gitignore flag."""
        (tmp_path / "test.pyc").write_text("bytecode")
        (tmp_path / ".gitignore").write_text("*.pyc")

        result = main([str(tmp_path), "--no-gitignore", "-q"])

        assert result == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        # Without gitignore, .pyc should be included
        assert "test.pyc" in output["files"]

    def test_main_with_config_file(self, tmp_path, capsys):
        """Should load config from file."""
        (tmp_path / "myvendor").mkdir()
        (tmp_path / "myvendor" / "lib.py").write_text("vendor")

        config = {
            "classification": {
                "custom_rules": {
                    "path": {"vendor": ["myvendor/"]}
                }
            }
        }
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config))

        result = main([str(tmp_path), "--config", str(config_path), "-q"])

        assert result == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["files"]["myvendor/lib.py"]["classification"] == "vendor"

    def test_main_nonexistent_path(self, tmp_path, capsys):
        """Should handle nonexistent path gracefully."""
        result = main([str(tmp_path / "nonexistent")])

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err

    def test_main_progress_output(self, tmp_path, capsys):
        """Should show progress without quiet mode."""
        (tmp_path / "test.py").write_text("code")

        result = main([str(tmp_path)])

        assert result == 0
        captured = capsys.readouterr()
        # Should show scanning message
        assert "Scanning" in captured.err
        # Should show summary
        assert "Scanned" in captured.err


class TestEndToEndScenarios:
    """End-to-end test scenarios."""

    def test_python_project(self, tmp_path):
        """Should scan Python project structure correctly."""
        # Create Python project structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "__init__.py").write_text("")
        (tmp_path / "src" / "main.py").write_text("def main(): pass")
        (tmp_path / "src" / "utils.py").write_text("def helper(): pass")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "__init__.py").write_text("")
        (tmp_path / "tests" / "test_main.py").write_text("def test_main(): pass")
        (tmp_path / "README.md").write_text("# Project")
        (tmp_path / "setup.py").write_text("setup()")
        (tmp_path / ".gitignore").write_text("__pycache__/\n*.pyc")

        output, _ = scan_repository(tmp_path)

        # Check file counts (8 files: 7 project files + .gitignore)
        assert output["statistics"]["total_files"] == 8

        # Check classifications
        assert output["files"]["src/main.py"]["classification"] == "source"
        assert output["files"]["tests/test_main.py"]["classification"] == "test"
        assert output["files"]["README.md"]["classification"] == "docs"

        # Check languages
        assert output["statistics"]["by_language"]["python"] >= 5

    def test_mixed_language_project(self, tmp_path):
        """Should handle mixed language project."""
        (tmp_path / "backend").mkdir()
        (tmp_path / "frontend").mkdir()
        (tmp_path / "backend" / "app.py").write_text("python")
        (tmp_path / "backend" / "utils.py").write_text("python")
        (tmp_path / "frontend" / "app.ts").write_text("typescript")
        (tmp_path / "frontend" / "utils.ts").write_text("typescript")
        (tmp_path / "frontend" / "styles.css").write_text("css")

        output, _ = scan_repository(tmp_path)

        langs = output["statistics"]["by_language"]
        assert langs["python"] == 2
        assert langs["typescript"] == 2
        assert langs["css"] == 1

    def test_deeply_nested_project(self, tmp_path):
        """Should handle deeply nested directories."""
        current = tmp_path
        for i in range(10):
            current = current / f"level{i}"
            current.mkdir()
            (current / f"file{i}.py").write_text(f"level {i}")

        output, _ = scan_repository(tmp_path)

        assert output["statistics"]["total_files"] == 10
        # Depth = path.count('/'), so deepest file at level0/.../level9/file9.py has depth 10
        assert output["hierarchy"]["max_depth"] == 10

    def test_unicode_files(self, tmp_path):
        """Should handle Unicode filenames."""
        (tmp_path / "日本語").mkdir()
        (tmp_path / "日本語" / "ファイル.py").write_text("# Japanese")
        (tmp_path / "über.py").write_text("# German")

        output, _ = scan_repository(tmp_path)

        assert "日本語/ファイル.py" in output["files"]
        assert "über.py" in output["files"]

    def test_large_file_count(self, tmp_path):
        """Should handle many files."""
        (tmp_path / "src").mkdir()
        for i in range(100):
            (tmp_path / "src" / f"file{i}.py").write_text(f"# file {i}")

        output, duration = scan_repository(tmp_path)

        assert output["statistics"]["total_files"] == 100
        assert output["statistics"]["files_per_second"] > 0
