import json
from pathlib import Path

import pytest
from jsonschema import validate, ValidationError


def test_output_schema_accepts_minimal_envelope():
    schema_path = Path(__file__).parents[2] / "schemas" / "output.schema.json"
    schema = json.loads(schema_path.read_text())

    output = {
        "metadata": {
            "tool_name": "lizard",
            "tool_version": "1.17.10",
            "run_id": "550e8400-e29b-41d4-a716-446655440000",
            "repo_id": "660e8400-e29b-41d4-a716-446655440001",
            "branch": "main",
            "commit": "abc123def456789012345678901234567890abcd",
            "timestamp": "2026-01-24T10:30:00Z",
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "lizard",
            "tool_version": "1.17.10",
            "run_id": "550e8400-e29b-41d4-a716-446655440000",
            "timestamp": "2026-01-24T10:30:00Z",
            "root_path": "src",
            "lizard_version": "lizard 1.17.10",
            "summary": {
                "total_files": 1,
                "total_functions": 1,
                "total_nloc": 10,
                "total_ccn": 1,
            },
            "directories": [
                {
                    "path": "src",
                    "direct": {"file_count": 1, "function_count": 1, "nloc": 10, "ccn": 1},
                    "recursive": {"file_count": 1, "function_count": 1, "nloc": 10, "ccn": 1},
                }
            ],
            "files": [
                {
                    "path": "src/main.py",
                    "language": "Python",
                    "nloc": 10,
                    "function_count": 1,
                    "total_ccn": 1,
                    "avg_ccn": 1.0,
                    "max_ccn": 1,
                }
            ],
        },
    }

    validate(instance=output, schema=schema)


def test_schema_accepts_excluded_files_array():
    """Test that schema accepts valid excluded_files array."""
    schema_path = Path(__file__).parents[2] / "schemas" / "output.schema.json"
    schema = json.loads(schema_path.read_text())

    output = {
        "metadata": {
            "tool_name": "lizard",
            "tool_version": "1.17.10",
            "run_id": "550e8400-e29b-41d4-a716-446655440000",
            "repo_id": "660e8400-e29b-41d4-a716-446655440001",
            "branch": "main",
            "commit": "abc123def456789012345678901234567890abcd",
            "timestamp": "2026-01-24T10:30:00Z",
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "lizard",
            "tool_version": "1.17.10",
            "run_id": "550e8400-e29b-41d4-a716-446655440000",
            "timestamp": "2026-01-24T10:30:00Z",
            "root_path": "src",
            "lizard_version": "lizard 1.17.10",
            "summary": {
                "total_files": 1,
                "total_functions": 1,
                "total_nloc": 10,
                "total_ccn": 1,
                "excluded_count": 2,
                "excluded_by_pattern": 1,
                "excluded_by_minified": 1,
                "excluded_by_size": 0,
                "excluded_by_language": 0,
            },
            "directories": [
                {
                    "path": "src",
                    "direct": {"file_count": 1, "function_count": 1, "nloc": 10, "ccn": 1},
                    "recursive": {"file_count": 1, "function_count": 1, "nloc": 10, "ccn": 1},
                }
            ],
            "files": [
                {
                    "path": "src/main.py",
                    "language": "Python",
                    "nloc": 10,
                    "function_count": 1,
                    "total_ccn": 1,
                    "avg_ccn": 1.0,
                    "max_ccn": 1,
                }
            ],
            "excluded_files": [
                {
                    "path": "vendor/jquery.min.js",
                    "reason": "pattern",
                    "language": "JavaScript",
                    "details": "*.min.js"
                },
                {
                    "path": "dist/bundle.js",
                    "reason": "minified",
                    "language": "JavaScript",
                    "details": "content-based detection"
                }
            ],
        },
    }

    # Should not raise
    validate(instance=output, schema=schema)


def test_schema_rejects_invalid_exclusion_reason():
    """Test that schema rejects excluded_files with invalid reason."""
    schema_path = Path(__file__).parents[2] / "schemas" / "output.schema.json"
    schema = json.loads(schema_path.read_text())

    output = {
        "metadata": {
            "tool_name": "lizard",
            "tool_version": "1.17.10",
            "run_id": "550e8400-e29b-41d4-a716-446655440000",
            "repo_id": "660e8400-e29b-41d4-a716-446655440001",
            "branch": "main",
            "commit": "abc123def456789012345678901234567890abcd",
            "timestamp": "2026-01-24T10:30:00Z",
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "lizard",
            "tool_version": "1.17.10",
            "summary": {"total_files": 0, "total_functions": 0, "total_nloc": 0, "total_ccn": 0},
            "directories": [],
            "files": [],
            "excluded_files": [
                {
                    "path": "vendor/file.js",
                    "reason": "invalid_reason",  # Not in enum
                    "language": "JavaScript",
                }
            ],
        },
    }

    with pytest.raises(ValidationError) as exc_info:
        validate(instance=output, schema=schema)
    assert "invalid_reason" in str(exc_info.value)


def test_schema_requires_excluded_file_path():
    """Test that schema requires path field in excluded_files entries."""
    schema_path = Path(__file__).parents[2] / "schemas" / "output.schema.json"
    schema = json.loads(schema_path.read_text())

    output = {
        "metadata": {
            "tool_name": "lizard",
            "tool_version": "1.17.10",
            "run_id": "550e8400-e29b-41d4-a716-446655440000",
            "repo_id": "660e8400-e29b-41d4-a716-446655440001",
            "branch": "main",
            "commit": "abc123def456789012345678901234567890abcd",
            "timestamp": "2026-01-24T10:30:00Z",
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "lizard",
            "tool_version": "1.17.10",
            "summary": {"total_files": 0, "total_functions": 0, "total_nloc": 0, "total_ccn": 0},
            "directories": [],
            "files": [],
            "excluded_files": [
                {
                    # Missing "path" field
                    "reason": "pattern",
                    "language": "JavaScript",
                }
            ],
        },
    }

    with pytest.raises(ValidationError) as exc_info:
        validate(instance=output, schema=schema)
    assert "path" in str(exc_info.value)


def test_summary_includes_exclusion_counts():
    """Test that summary can include all exclusion count fields."""
    schema_path = Path(__file__).parents[2] / "schemas" / "output.schema.json"
    schema = json.loads(schema_path.read_text())

    output = {
        "metadata": {
            "tool_name": "lizard",
            "tool_version": "1.17.10",
            "run_id": "550e8400-e29b-41d4-a716-446655440000",
            "repo_id": "660e8400-e29b-41d4-a716-446655440001",
            "branch": "main",
            "commit": "abc123def456789012345678901234567890abcd",
            "timestamp": "2026-01-24T10:30:00Z",
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "lizard",
            "tool_version": "1.17.10",
            "summary": {
                "total_files": 10,
                "total_functions": 50,
                "total_nloc": 500,
                "total_ccn": 100,
                "excluded_count": 15,
                "excluded_by_pattern": 5,
                "excluded_by_minified": 3,
                "excluded_by_size": 2,
                "excluded_by_language": 5,
            },
            "directories": [],
            "files": [],
        },
    }

    # Should not raise - all exclusion count fields are valid
    validate(instance=output, schema=schema)
