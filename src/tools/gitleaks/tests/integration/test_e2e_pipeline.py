"""End-to-end integration test for gitleaks analysis."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from secret_analyzer import analyze_repository, to_output_format


@pytest.mark.integration
def test_gitleaks_analysis_output_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    tool_root = Path(__file__).parents[2]
    gitleaks_bin = tool_root / "bin" / "gitleaks"
    if not gitleaks_bin.exists():
        pytest.skip("gitleaks binary not available (run make setup)")

    repo_path = tool_root / "eval-repos" / "synthetic" / "no-secrets"
    if not repo_path.exists():
        pytest.skip("synthetic repos missing (run make build-repos)")

    analysis = analyze_repository(
        gitleaks_path=gitleaks_bin,
        repo_path=repo_path,
        config_path=None,
        baseline_path=None,
        repo_name_override="no-secrets",
    )
    payload = to_output_format(analysis)

    schema_path = tool_root / "schemas" / "output.schema.json"
    schema = json.loads(schema_path.read_text())
    jsonschema.validate(payload, schema)

    data = payload.get("data", {})
    assert data.get("tool") == "gitleaks"
    assert "findings" in data
