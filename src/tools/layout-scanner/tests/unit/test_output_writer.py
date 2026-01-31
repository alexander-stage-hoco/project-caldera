"""
Unit tests for output_writer.py
"""

import json
import pytest
from datetime import datetime
from pathlib import Path

from scripts.output_writer import (
    SCHEMA_VERSION,
    TOOL_VERSION,
    generate_run_id,
    format_file_object,
    format_directory_object,
    format_hierarchy_section,
    format_statistics,
    build_output,
    write_output,
    output_to_json,
)
from scripts.classifier import ClassificationResult, LanguageResult
from scripts.hierarchy_builder import DirectoryMetrics, HierarchyInfo
from scripts.tree_walker import FileInfo, DirectoryInfo, WalkResult


class TestConstants:
    """Tests for module constants."""

    def test_schema_version(self):
        """Schema version should be defined."""
        assert SCHEMA_VERSION == "1.0.0"

    def test_tool_version(self):
        """Tool version should be defined."""
        assert TOOL_VERSION == "1.0.0"


class TestGenerateRunId:
    """Tests for generate_run_id function."""

    def test_run_id_format(self):
        """Run ID should have expected format."""
        run_id = generate_run_id("my-repo")
        assert run_id.startswith("layout-")
        assert "my-repo" in run_id

    def test_run_id_contains_timestamp(self):
        """Run ID should contain timestamp."""
        run_id = generate_run_id("test")
        # Should contain date-like pattern
        parts = run_id.split("-")
        assert len(parts) >= 3
        # First part after "layout" should be date
        assert len(parts[1]) == 8  # YYYYMMDD

    def test_run_id_unique_per_call(self):
        """Different calls should potentially produce different IDs."""
        # Note: might be same if called within same second
        run_id1 = generate_run_id("repo")
        run_id2 = generate_run_id("repo")
        # At minimum, both should be valid format
        assert run_id1.startswith("layout-")
        assert run_id2.startswith("layout-")


class TestFormatFileObject:
    """Tests for format_file_object function."""

    def test_all_fields_present(self):
        """Formatted file object should have all required fields."""
        file_info = FileInfo(
            id="f-123456789abc",
            path="src/main.py",
            name="main.py",
            extension=".py",
            size_bytes=100,
            modified_time="2024-01-15T10:30:00Z",
            is_symlink=False,
            parent_directory_id="d-000000000000",
            depth=2,
        )
        classification = ClassificationResult(
            category="source",
            confidence=0.9,
            reason="extension:.py",
        )
        language = LanguageResult(language="python", confidence=0.95)

        result = format_file_object(file_info, classification, language)

        # Core fields
        assert result["id"] == "f-123456789abc"
        assert result["path"] == "src/main.py"
        assert result["name"] == "main.py"
        assert result["extension"] == ".py"
        assert result["size_bytes"] == 100
        assert result["modified_time"] == "2024-01-15T10:30:00Z"
        assert result["is_symlink"] is False
        assert result["parent_directory_id"] == "d-000000000000"
        assert result["depth"] == 2

        # Classification fields
        assert result["classification"] == "source"
        assert result["classification_confidence"] == 0.9
        assert result["classification_reason"] == "extension:.py"

        # Language
        assert result["language"] == "python"

        # Null fields for future passes
        assert result["first_commit_date"] is None
        assert result["last_commit_date"] is None
        assert result["content_hash"] is None

    def test_file_object_serializable(self):
        """Formatted file object should be JSON serializable."""
        file_info = FileInfo(
            id="f-123456789abc",
            path="test.py",
            name="test.py",
            extension=".py",
            size_bytes=50,
            modified_time="2024-01-15T10:30:00Z",
            is_symlink=False,
            parent_directory_id="d-000000000000",
            depth=1,
        )
        classification = ClassificationResult(category="test", confidence=0.8, reason="filename")
        language = LanguageResult(language="python", confidence=0.95)

        result = format_file_object(file_info, classification, language)

        # Should not raise
        json.dumps(result)


class TestFormatDirectoryObject:
    """Tests for format_directory_object function."""

    def test_all_fields_present(self):
        """Formatted directory object should have all required fields."""
        dir_info = DirectoryInfo(
            id="d-123456789abc",
            path="src",
            name="src",
            modified_time="2024-01-15T10:30:00Z",
            is_symlink=False,
            parent_directory_id="d-000000000000",
            depth=1,
            child_file_ids=["f-abc", "f-def"],
            child_directory_ids=["d-ghi"],
        )
        metrics = DirectoryMetrics(
            direct_file_count=2,
            direct_directory_count=1,
            recursive_file_count=5,
            recursive_directory_count=3,
            direct_size_bytes=1000,
            recursive_size_bytes=5000,
            classification_distribution={"source": 3, "test": 2},
            language_distribution={"python": 4, "javascript": 1},
        )

        result = format_directory_object(
            dir_info, metrics, "source", "majority source (60%)"
        )

        # Core fields
        assert result["id"] == "d-123456789abc"
        assert result["path"] == "src"
        assert result["name"] == "src"
        assert result["modified_time"] == "2024-01-15T10:30:00Z"
        assert result["is_symlink"] is False
        assert result["parent_directory_id"] == "d-000000000000"
        assert result["depth"] == 1

        # Children
        assert result["child_file_ids"] == ["f-abc", "f-def"]
        assert result["child_directory_ids"] == ["d-ghi"]

        # Metrics
        assert result["direct_file_count"] == 2
        assert result["recursive_file_count"] == 5
        assert result["direct_size_bytes"] == 1000
        assert result["recursive_size_bytes"] == 5000

        # Classification
        assert result["classification"] == "source"
        assert result["classification_reason"] == "majority source (60%)"

        # Distributions
        assert result["classification_distribution"]["source"] == 3
        assert result["language_distribution"]["python"] == 4


class TestFormatHierarchySection:
    """Tests for format_hierarchy_section function."""

    def test_all_fields_present(self):
        """Formatted hierarchy section should have all required fields."""
        hierarchy = HierarchyInfo(
            root_id="d-000000000000",
            max_depth=5,
            total_files=100,
            total_directories=20,
            total_size_bytes=50000,
            children={"d-000": ["d-001", "f-001"]},
            parents={"d-001": "d-000", "f-001": "d-000"},
            depth_distribution={0: 1, 1: 5, 2: 10, 3: 4},
        )

        result = format_hierarchy_section(hierarchy)

        assert result["root_id"] == "d-000000000000"
        assert result["max_depth"] == 5
        assert result["total_files"] == 100
        assert result["total_directories"] == 20
        assert result["total_size_bytes"] == 50000
        assert result["children"] == {"d-000": ["d-001", "f-001"]}
        assert result["parents"] == {"d-001": "d-000", "f-001": "d-000"}

    def test_depth_distribution_string_keys(self):
        """Depth distribution keys should be strings for JSON compatibility."""
        hierarchy = HierarchyInfo(
            root_id="d-000",
            max_depth=3,
            total_files=10,
            total_directories=5,
            total_size_bytes=1000,
            children={},
            parents={},
            depth_distribution={0: 1, 1: 2, 2: 5, 3: 7},
        )

        result = format_hierarchy_section(hierarchy)

        # Keys should be strings
        assert "0" in result["depth_distribution"]
        assert "1" in result["depth_distribution"]
        assert result["depth_distribution"]["0"] == 1


class TestFormatStatistics:
    """Tests for format_statistics function."""

    def test_basic_statistics(self):
        """Statistics should include basic counts."""
        walk_result = WalkResult(
            files={"a.py": None, "b.py": None, "c.js": None},
            directories={"": None, "src": None},
            root_path="/repo",
            max_depth=2,
            total_size_bytes=1500,
        )
        classifications = {"a.py": "source", "b.py": "source", "c.js": "source"}
        languages = {"a.py": "python", "b.py": "python", "c.js": "javascript"}

        result = format_statistics(walk_result, classifications, languages, 1000)

        assert result["total_files"] == 3
        assert result["total_directories"] == 2
        assert result["total_size_bytes"] == 1500
        assert result["max_depth"] == 2
        assert result["scan_duration_ms"] == 1000

    def test_classification_distribution(self):
        """Statistics should include classification distribution."""
        walk_result = WalkResult(
            files={"a.py": None, "b.py": None, "test.py": None, "README.md": None},
            directories={},
            root_path="/repo",
        )
        classifications = {
            "a.py": "source",
            "b.py": "source",
            "test.py": "test",
            "README.md": "docs",
        }

        result = format_statistics(walk_result, classifications, {}, 500)

        assert result["by_classification"]["source"] == 2
        assert result["by_classification"]["test"] == 1
        assert result["by_classification"]["docs"] == 1

    def test_language_distribution(self):
        """Statistics should include language distribution."""
        walk_result = WalkResult(
            files={"a.py": None, "b.py": None, "c.js": None},
            directories={},
            root_path="/repo",
        )
        languages = {"a.py": "python", "b.py": "python", "c.js": "javascript"}

        result = format_statistics(walk_result, {}, languages, 500)

        assert result["by_language"]["python"] == 2
        assert result["by_language"]["javascript"] == 1

    def test_unknown_language_included(self):
        """Unknown languages should be included for consistency with totals."""
        walk_result = WalkResult(
            files={"a.py": None, "data.xyz": None},
            directories={},
            root_path="/repo",
        )
        languages = {"a.py": "python", "data.xyz": "unknown"}

        result = format_statistics(walk_result, {}, languages, 500)

        # Unknown languages should be counted to ensure sum matches total_files
        assert "unknown" in result["by_language"]
        assert result["by_language"]["python"] == 1
        assert result["by_language"]["unknown"] == 1

    def test_files_per_second(self):
        """Files per second should be calculated correctly."""
        walk_result = WalkResult(
            files={f"file{i}.py": None for i in range(100)},
            directories={},
            root_path="/repo",
        )

        result = format_statistics(walk_result, {}, {}, 2000)  # 2 seconds

        assert result["files_per_second"] == 50.0

    def test_files_per_second_zero_duration(self):
        """Files per second should be 0 for zero duration."""
        walk_result = WalkResult(
            files={"a.py": None},
            directories={},
            root_path="/repo",
        )

        result = format_statistics(walk_result, {}, {}, 0)

        assert result["files_per_second"] == 0


class TestWriteOutput:
    """Tests for write_output function."""

    def test_creates_file(self, tmp_path):
        """Should create output file."""
        output = {"test": "data"}
        output_path = tmp_path / "output.json"

        write_output(output, output_path)

        assert output_path.exists()

    def test_creates_parent_dirs(self, tmp_path):
        """Should create parent directories."""
        output = {"test": "data"}
        output_path = tmp_path / "nested" / "dir" / "output.json"

        write_output(output, output_path)

        assert output_path.exists()

    def test_valid_json(self, tmp_path):
        """Should write valid JSON."""
        output = {
            "name": "test",
            "count": 42,
            "items": ["a", "b", "c"],
        }
        output_path = tmp_path / "output.json"

        write_output(output, output_path)

        with open(output_path) as f:
            loaded = json.load(f)

        assert loaded["name"] == "test"
        assert loaded["count"] == 42
        assert loaded["items"] == ["a", "b", "c"]

    def test_custom_indent(self, tmp_path):
        """Should respect custom indent."""
        output = {"key": "value"}
        output_path = tmp_path / "output.json"

        write_output(output, output_path, indent=4)

        content = output_path.read_text()
        # 4-space indent would have more spaces
        assert "    " in content

    def test_unicode_content(self, tmp_path):
        """Should handle Unicode content."""
        output = {
            "japanese": "日本語",
            "emoji": "🎉",
        }
        output_path = tmp_path / "output.json"

        write_output(output, output_path)

        with open(output_path, encoding="utf-8") as f:
            loaded = json.load(f)

        assert loaded["japanese"] == "日本語"
        assert loaded["emoji"] == "🎉"


class TestOutputToJson:
    """Tests for output_to_json function."""

    def test_returns_string(self):
        """Should return JSON string."""
        output = {"key": "value"}
        result = output_to_json(output)
        assert isinstance(result, str)

    def test_valid_json(self):
        """Should return valid JSON."""
        output = {"key": "value", "count": 42}
        result = output_to_json(output)
        loaded = json.loads(result)
        assert loaded["key"] == "value"
        assert loaded["count"] == 42

    def test_custom_indent(self):
        """Should respect custom indent."""
        output = {"key": "value"}
        result = output_to_json(output, indent=4)
        assert "    " in result

    def test_unicode_preserved(self):
        """Should preserve Unicode characters."""
        output = {"text": "日本語テスト"}
        result = output_to_json(output)
        assert "日本語テスト" in result


class TestBuildOutput:
    """Tests for build_output function."""

    def test_top_level_structure(self):
        """Built output should have all top-level fields."""
        walk_result = WalkResult(
            files={},
            directories={"": DirectoryInfo(
                id="d-000000000000",
                path="",
                name="repo",
                modified_time="2024-01-15T10:30:00Z",
                is_symlink=False,
                parent_directory_id=None,
                depth=0,
            )},
            root_path="/path/to/repo",
        )
        hierarchy = HierarchyInfo(
            root_id="d-000000000000",
            max_depth=0,
            total_files=0,
            total_directories=1,
            total_size_bytes=0,
            children={},
            parents={},
            depth_distribution={0: 1},
        )

        result = build_output(
            walk_result=walk_result,
            file_classifications={},
            file_languages={},
            dir_classifications={"": ("other", "empty directory")},
            dir_metrics={"": DirectoryMetrics()},
            hierarchy=hierarchy,
            repo_name="repo",
            repo_path="/path/to/repo",
            scan_duration_ms=100,
        )

        # Top-level fields
        assert result["schema_version"] == SCHEMA_VERSION
        assert result["tool"] == "layout-scanner"
        assert result["tool_version"] == TOOL_VERSION
        assert "run_id" in result
        assert "timestamp" in result
        assert result["repository"] == "repo"
        assert result["repository_path"] == "/path/to/repo"
        assert result["passes_completed"] == ["filesystem"]

        # Sections
        assert "statistics" in result
        assert "files" in result
        assert "directories" in result
        assert "hierarchy" in result

    def test_timestamp_iso_format(self):
        """Timestamp should be ISO 8601 format."""
        walk_result = WalkResult(
            files={},
            directories={"": DirectoryInfo(
                id="d-000000000000",
                path="",
                name="repo",
                modified_time="2024-01-15T10:30:00Z",
                is_symlink=False,
                parent_directory_id=None,
                depth=0,
            )},
            root_path="/repo",
        )
        hierarchy = HierarchyInfo(
            root_id="d-000000000000",
            max_depth=0,
            total_files=0,
            total_directories=1,
            total_size_bytes=0,
            children={},
            parents={},
            depth_distribution={},
        )

        result = build_output(
            walk_result=walk_result,
            file_classifications={},
            file_languages={},
            dir_classifications={"": ("other", "empty")},
            dir_metrics={"": DirectoryMetrics()},
            hierarchy=hierarchy,
            repo_name="repo",
            repo_path="/repo",
            scan_duration_ms=100,
        )

        timestamp = result["timestamp"]
        # Should end with Z (UTC)
        assert timestamp.endswith("Z")
        # Should have ISO format with T separator
        assert "T" in timestamp
