"""
Unit tests for id_generator.py
"""

import pytest
from scripts.id_generator import (
    generate_id,
    generate_root_id,
    is_file_id,
    is_directory_id,
    extract_hash,
)


class TestGenerateId:
    """Tests for generate_id function."""

    def test_file_id_has_correct_prefix(self):
        """File IDs should start with 'f-'."""
        file_id = generate_id("src/main.py", "file")
        assert file_id.startswith("f-")

    def test_directory_id_has_correct_prefix(self):
        """Directory IDs should start with 'd-'."""
        dir_id = generate_id("src/models", "directory")
        assert dir_id.startswith("d-")

    def test_file_id_has_correct_length(self):
        """File IDs should be 14 chars (2 prefix + 12 hash)."""
        file_id = generate_id("src/main.py", "file")
        assert len(file_id) == 14

    def test_directory_id_has_correct_length(self):
        """Directory IDs should be 14 chars (2 prefix + 12 hash)."""
        dir_id = generate_id("src/models", "directory")
        assert len(dir_id) == 14

    def test_hash_portion_is_valid_hex(self):
        """The hash portion should be valid hexadecimal."""
        file_id = generate_id("test.py", "file")
        hash_part = file_id[2:]  # Skip 'f-'
        # Should not raise ValueError
        int(hash_part, 16)

    def test_deterministic_same_path(self):
        """Same path should always produce the same ID."""
        path = "src/services/auth.py"
        id1 = generate_id(path, "file")
        id2 = generate_id(path, "file")
        id3 = generate_id(path, "file")
        assert id1 == id2 == id3

    def test_different_paths_produce_different_ids(self):
        """Different paths should produce different IDs."""
        id1 = generate_id("src/main.py", "file")
        id2 = generate_id("src/utils.py", "file")
        id3 = generate_id("tests/test_main.py", "file")
        assert id1 != id2 != id3

    def test_same_path_different_kind_produces_different_ids(self):
        """Same path with different kind should produce different IDs."""
        file_id = generate_id("src", "file")
        dir_id = generate_id("src", "directory")
        # They differ only in prefix since hash is same
        assert file_id != dir_id
        assert file_id[2:] == dir_id[2:]  # Hash portion is same

    def test_empty_path(self):
        """Empty path should produce a valid ID."""
        file_id = generate_id("", "file")
        assert file_id.startswith("f-")
        assert len(file_id) == 14

    def test_unicode_path(self):
        """Unicode paths should produce valid IDs."""
        id1 = generate_id("docs/日本語.md", "file")
        id2 = generate_id("über/ファイル.py", "file")
        assert id1.startswith("f-")
        assert id2.startswith("f-")
        assert len(id1) == 14
        assert len(id2) == 14

    def test_special_characters_in_path(self):
        """Paths with special characters should produce valid IDs."""
        paths = [
            "file with spaces.py",
            "file-with-dashes.py",
            "file_with_underscores.py",
            "path/to/file (copy).txt",
            "data/test[1].json",
            "src/@types/index.d.ts",
        ]
        for path in paths:
            file_id = generate_id(path, "file")
            assert file_id.startswith("f-")
            assert len(file_id) == 14

    def test_long_path(self):
        """Very long paths should produce valid IDs."""
        long_path = "/".join([f"level{i}" for i in range(100)]) + "/file.py"
        file_id = generate_id(long_path, "file")
        assert file_id.startswith("f-")
        assert len(file_id) == 14

    def test_path_case_sensitivity(self):
        """Paths with different cases should produce different IDs."""
        id_lower = generate_id("readme.md", "file")
        id_upper = generate_id("README.md", "file")
        id_mixed = generate_id("ReadMe.md", "file")
        # All should be different
        assert id_lower != id_upper
        assert id_upper != id_mixed
        assert id_lower != id_mixed


class TestGenerateRootId:
    """Tests for generate_root_id function."""

    def test_root_id_value(self):
        """Root ID should be the special value 'd-000000000000'."""
        assert generate_root_id() == "d-000000000000"

    def test_root_id_is_directory_id(self):
        """Root ID should be recognized as a directory ID."""
        root_id = generate_root_id()
        assert is_directory_id(root_id)

    def test_root_id_not_file_id(self):
        """Root ID should not be recognized as a file ID."""
        root_id = generate_root_id()
        assert not is_file_id(root_id)

    def test_root_id_deterministic(self):
        """Root ID should always be the same."""
        assert generate_root_id() == generate_root_id() == generate_root_id()


class TestIsFileId:
    """Tests for is_file_id function."""

    def test_file_id_recognized(self):
        """Valid file IDs should be recognized."""
        assert is_file_id("f-123456789abc")
        assert is_file_id("f-000000000000")
        assert is_file_id("f-ffffffffffff")

    def test_directory_id_not_recognized(self):
        """Directory IDs should not be recognized as file IDs."""
        assert not is_file_id("d-123456789abc")
        assert not is_file_id(generate_root_id())

    def test_invalid_formats(self):
        """Invalid formats should not be recognized."""
        assert not is_file_id("")
        assert not is_file_id("f")
        assert not is_file_id("123456789abc")
        assert not is_file_id("x-123456789abc")
        assert not is_file_id("file-123456789abc")
        # Note: "f-" returns True because startswith("f-") is True
        # This is edge case behavior - prefix only check


class TestIsDirectoryId:
    """Tests for is_directory_id function."""

    def test_directory_id_recognized(self):
        """Valid directory IDs should be recognized."""
        assert is_directory_id("d-123456789abc")
        assert is_directory_id("d-000000000000")
        assert is_directory_id(generate_root_id())

    def test_file_id_not_recognized(self):
        """File IDs should not be recognized as directory IDs."""
        assert not is_directory_id("f-123456789abc")
        assert not is_directory_id(generate_id("test.py", "file"))

    def test_invalid_formats(self):
        """Invalid formats should not be recognized."""
        assert not is_directory_id("")
        assert not is_directory_id("d")
        assert not is_directory_id("123456789abc")
        assert not is_directory_id("x-123456789abc")
        assert not is_directory_id("dir-123456789abc")
        # Note: "d-" returns True because startswith("d-") is True
        # This is edge case behavior - prefix only check


class TestExtractHash:
    """Tests for extract_hash function."""

    def test_extract_from_file_id(self):
        """Should extract hash from file ID."""
        file_id = "f-123456789abc"
        assert extract_hash(file_id) == "123456789abc"

    def test_extract_from_directory_id(self):
        """Should extract hash from directory ID."""
        dir_id = "d-abcdef012345"
        assert extract_hash(dir_id) == "abcdef012345"

    def test_extract_from_root_id(self):
        """Should extract hash from root ID."""
        assert extract_hash(generate_root_id()) == "000000000000"

    def test_extract_preserves_hash(self):
        """Extracted hash should match original hash portion."""
        path = "src/main.py"
        file_id = generate_id(path, "file")
        dir_id = generate_id(path, "directory")
        # Same path produces same hash
        assert extract_hash(file_id) == extract_hash(dir_id)

    def test_extract_from_generated_id(self):
        """Should work with dynamically generated IDs."""
        file_id = generate_id("test/path/file.py", "file")
        hash_part = extract_hash(file_id)
        assert len(hash_part) == 12
        # Should be valid hex
        int(hash_part, 16)


class TestIdUniqueness:
    """Tests for ID uniqueness and collision resistance."""

    def test_many_unique_paths(self):
        """Many different paths should all produce unique IDs."""
        paths = [f"file{i}.py" for i in range(1000)]
        ids = [generate_id(p, "file") for p in paths]
        # All IDs should be unique
        assert len(ids) == len(set(ids))

    def test_similar_paths_produce_different_ids(self):
        """Similar paths should produce different IDs."""
        ids = [
            generate_id("test.py", "file"),
            generate_id("tests.py", "file"),
            generate_id("Test.py", "file"),
            generate_id("test.ppy", "file"),
            generate_id("atest.py", "file"),
        ]
        assert len(ids) == len(set(ids))

    def test_nested_paths_unique(self):
        """Nested paths at different levels should be unique."""
        ids = [
            generate_id("a/file.py", "file"),
            generate_id("a/b/file.py", "file"),
            generate_id("a/b/c/file.py", "file"),
            generate_id("b/file.py", "file"),
            generate_id("file.py", "file"),
        ]
        assert len(ids) == len(set(ids))
