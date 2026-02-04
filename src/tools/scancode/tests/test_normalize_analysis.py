import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from evaluate import normalize_analysis


def test_normalize_analysis_unwraps_results():
    analysis = {
        "schema_version": "1.0.0",
        "generated_at": "2026-01-22T08:15:00Z",
        "repo_name": "mit-only",
        "repo_path": "/tmp/mit-only",
        "results": {
            "tool": "license-analyzer",
            "tool_version": "1.0.0",
            "scan_time_ms": 123.4,
            "total_files_scanned": 10,
            "files_with_licenses": 2,
            "license_files_found": 1,
            "licenses_found": ["MIT"],
            "license_counts": {"MIT": 2},
            "has_permissive": True,
            "has_weak_copyleft": False,
            "has_copyleft": False,
            "has_unknown": False,
            "overall_risk": "low",
            "risk_reasons": ["Only permissive licenses found"],
            "findings": [],
            "files": {},
            "directories": {"directory_count": 0, "directories": []},
        },
    }

    normalized = normalize_analysis(analysis)

    assert normalized["schema_version"] == "1.0.0"
    assert normalized["repository"] == "mit-only"
    assert normalized["timestamp"] == "2026-01-22T08:15:00Z"
    assert normalized["tool"] == "license-analyzer"
    assert normalized["tool_version"] == "1.0.0"
    assert normalized["license_files_found"] == 1


def test_output_schema_directories_shape():
    schema_path = Path(__file__).parent.parent / "schemas" / "output.schema.json"
    schema = json.loads(schema_path.read_text())
    # Schema now uses Caldera envelope format with metadata and data
    directories = schema["properties"]["data"]["properties"]["directories"]
    assert directories["type"] == "object"
    assert set(directories["required"]) == {"directory_count", "directories"}
