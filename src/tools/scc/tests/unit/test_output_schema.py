import json
from pathlib import Path

from jsonschema import validate


def test_output_schema_accepts_minimal_envelope():
    schema_path = Path(__file__).parents[2] / "schemas" / "output.schema.json"
    schema = json.loads(schema_path.read_text())

    output = {
        "metadata": {
            "tool_name": "scc",
            "tool_version": "3.6.0",
            "run_id": "550e8400-e29b-41d4-a716-446655440000",
            "repo_id": "660e8400-e29b-41d4-a716-446655440001",
            "branch": "main",
            "commit": "abc123def456789012345678901234567890abcd",
            "timestamp": "2026-01-24T10:30:00Z",
            "schema_version": "1.0.0",
        },
        "data": {
            "tool": "scc",
            "tool_version": "3.6.0",
            "summary": {
                "total_files": 1,
                "total_loc": 10,
            },
            "files": [
                {
                    "path": "src/main.py",
                    "language": "Python",
                    "lines": 10,
                }
            ],
            "directories": [
                {
                    "path": "src",
                    "direct": {"file_count": 1, "loc": 10, "complexity": 1},
                    "recursive": {"file_count": 1, "loc": 10, "complexity": 1},
                }
            ],
        },
    }

    validate(instance=output, schema=schema)
