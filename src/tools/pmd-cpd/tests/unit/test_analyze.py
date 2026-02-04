"""Unit tests for PMD CPD analyze.py script."""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
# Add src directory to path for common imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent))

from analyze import (
    detect_language,
    generate_clone_id,
    DuplicationOccurrence,
    Duplication,
    FileMetrics,
    AnalysisResult,
)


class TestDetectLanguage:
    """Test language detection from file extension."""

    @pytest.mark.parametrize("path,expected", [
        ("main.py", "python"),
        ("app.js", "ecmascript"),
        ("component.jsx", "ecmascript"),
        ("app.ts", "typescript"),
        ("component.tsx", "typescript"),
        ("Program.cs", "cs"),
        ("Main.java", "java"),
        ("main.go", "go"),
        ("main.rs", "rust"),
        ("file.unknown", "unknown"),
    ])
    def test_language_detection(self, path, expected):
        """Test detecting language from various extensions."""
        assert detect_language(path) == expected


class TestGenerateCloneId:
    """Test clone ID generation."""

    def test_generates_padded_id(self):
        """Test that clone IDs are zero-padded."""
        assert generate_clone_id(0) == "CPD-0000"
        assert generate_clone_id(1) == "CPD-0001"
        assert generate_clone_id(42) == "CPD-0042"
        assert generate_clone_id(999) == "CPD-0999"
        assert generate_clone_id(1234) == "CPD-1234"


class TestDuplicationOccurrence:
    """Test DuplicationOccurrence dataclass."""

    def test_creation(self):
        """Test basic creation."""
        occ = DuplicationOccurrence(
            file="src/main.py",
            line_start=10,
            line_end=25,
            column_start=1,
            column_end=80,
        )

        assert occ.file == "src/main.py"
        assert occ.line_start == 10
        assert occ.line_end == 25

    def test_to_dict(self):
        """Test serialization."""
        occ = DuplicationOccurrence(
            file="src/main.py",
            line_start=10,
            line_end=25,
        )

        d = occ.to_dict()
        assert d["file"] == "src/main.py"
        assert d["line_start"] == 10
        assert d["line_end"] == 25


class TestDuplication:
    """Test Duplication dataclass."""

    def test_single_file_clone(self):
        """Test clone within single file."""
        dup = Duplication(
            clone_id="CPD-0001",
            lines=15,
            tokens=100,
            occurrences=[
                DuplicationOccurrence("src/main.py", 10, 24),
                DuplicationOccurrence("src/main.py", 50, 64),
            ],
        )

        assert dup.is_cross_file is False

    def test_cross_file_clone(self):
        """Test clone spanning multiple files."""
        dup = Duplication(
            clone_id="CPD-0002",
            lines=20,
            tokens=150,
            occurrences=[
                DuplicationOccurrence("src/a.py", 10, 29),
                DuplicationOccurrence("src/b.py", 5, 24),
            ],
        )

        assert dup.is_cross_file is True

    def test_to_dict_truncates_code_fragment(self):
        """Test that large code fragments are truncated."""
        long_code = "x" * 1000
        dup = Duplication(
            clone_id="CPD-0001",
            lines=10,
            tokens=50,
            code_fragment=long_code,
        )

        d = dup.to_dict()
        assert len(d["code_fragment"]) == 500


class TestFileMetrics:
    """Test FileMetrics dataclass."""

    def test_creation(self):
        """Test basic creation."""
        metrics = FileMetrics(
            path="src/main.py",
            total_lines=100,
            duplicate_lines=25,
            duplicate_blocks=3,
            duplication_percentage=25.0,
            language="python",
        )

        assert metrics.path == "src/main.py"
        assert metrics.total_lines == 100
        assert metrics.duplication_percentage == 25.0

    def test_to_dict_rounds_percentage(self):
        """Test that percentage is rounded in output."""
        metrics = FileMetrics(
            path="src/main.py",
            total_lines=100,
            duplicate_lines=33,
            duplication_percentage=33.3333333,
        )

        d = metrics.to_dict()
        assert d["duplication_percentage"] == 33.33


class TestAnalysisResult:
    """Test AnalysisResult serialization to Caldera envelope."""

    def test_to_caldera_envelope_includes_metadata(self):
        """Test that Caldera envelope includes correct metadata."""
        result = AnalysisResult(
            run_id="550e8400-e29b-41d4-a716-446655440000",
            repo_id="660e8400-e29b-41d4-a716-446655440000",
            branch="main",
            commit="a" * 40,
            timestamp="2026-01-22T00:00:00+00:00",
            tool_version="7.0.0",
            min_tokens=50,
            ignore_identifiers=False,
            ignore_literals=False,
            elapsed_seconds=1.5,
            summary={"total_files": 0, "total_clones": 0, "duplication_percentage": 0.0},
            files=[],
            duplications=[],
            statistics={},
            errors=[],
        )

        envelope = result.to_caldera_envelope()

        # Check metadata section
        assert envelope["metadata"]["tool_name"] == "pmd-cpd"
        assert envelope["metadata"]["tool_version"] == "7.0.0"
        assert envelope["metadata"]["run_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert envelope["metadata"]["repo_id"] == "660e8400-e29b-41d4-a716-446655440000"
        assert envelope["metadata"]["branch"] == "main"
        assert envelope["metadata"]["commit"] == "a" * 40
        assert envelope["metadata"]["schema_version"] == "1.0.0"

        # Check data section
        assert envelope["data"]["tool"] == "pmd-cpd"
        assert envelope["data"]["config"]["min_tokens"] == 50
        assert envelope["data"]["elapsed_seconds"] == 1.5
        assert "summary" in envelope["data"]
        assert "files" in envelope["data"]
        assert "duplications" in envelope["data"]

    def test_to_caldera_envelope_with_files_and_duplications(self):
        """Test envelope generation with actual data."""
        result = AnalysisResult(
            run_id="550e8400-e29b-41d4-a716-446655440000",
            repo_id="660e8400-e29b-41d4-a716-446655440000",
            branch="main",
            commit="a" * 40,
            timestamp="2026-01-22T00:00:00+00:00",
            tool_version="7.0.0",
            min_tokens=50,
            ignore_identifiers=True,
            ignore_literals=True,
            elapsed_seconds=2.5,
            summary={
                "total_files": 2,
                "total_clones": 1,
                "duplication_percentage": 10.0,
                "cross_file_clones": 1,
            },
            files=[
                FileMetrics(
                    path="src/a.py",
                    total_lines=100,
                    duplicate_lines=10,
                    duplicate_blocks=1,
                    duplication_percentage=10.0,
                    language="python",
                ),
            ],
            duplications=[
                Duplication(
                    clone_id="CPD-0000",
                    lines=10,
                    tokens=50,
                    occurrences=[
                        DuplicationOccurrence("src/a.py", 1, 10),
                        DuplicationOccurrence("src/b.py", 1, 10),
                    ],
                ),
            ],
            statistics={"cross_file_clones": 1},
            errors=[],
        )

        envelope = result.to_caldera_envelope()

        # Check config
        assert envelope["data"]["config"]["ignore_identifiers"] is True
        assert envelope["data"]["config"]["ignore_literals"] is True

        # Check files
        assert len(envelope["data"]["files"]) == 1
        assert envelope["data"]["files"][0]["path"] == "src/a.py"

        # Check duplications
        assert len(envelope["data"]["duplications"]) == 1
        assert envelope["data"]["duplications"][0]["clone_id"] == "CPD-0000"
        assert len(envelope["data"]["duplications"][0]["occurrences"]) == 2
