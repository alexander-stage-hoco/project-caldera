import json
from pathlib import Path

from jsonschema import validate


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
