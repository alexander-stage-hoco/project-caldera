from __future__ import annotations

import json
from pathlib import Path
import pytest

from persistence.adapters.scc_adapter import SccAdapter, SCHEMA_PATH as SCC_SCHEMA
from persistence.adapters.lizard_adapter import LizardAdapter, SCHEMA_PATH as LIZARD_SCHEMA
from persistence.adapters.layout_adapter import LayoutAdapter, SCHEMA_PATH as LAYOUT_SCHEMA
from persistence.adapters.semgrep_adapter import SemgrepAdapter, SCHEMA_PATH as SEMGREP_SCHEMA


def _load_payload(schema_path: Path) -> dict:
    schema = json.loads(schema_path.read_text())
    # Minimal invalid payload: missing required 'metadata'
    return {"data": {}, "metadata": {"tool_name": "x"}}


def test_scc_schema_validation_fails() -> None:
    adapter = SccAdapter(object(), object(), object(), Path("/tmp/repo"))
    payload = _load_payload(SCC_SCHEMA)
    with pytest.raises(ValueError):
        adapter.validate_schema(payload)


def test_lizard_schema_validation_fails() -> None:
    adapter = LizardAdapter(object(), object(), object(), Path("/tmp/repo"))
    payload = _load_payload(LIZARD_SCHEMA)
    with pytest.raises(ValueError):
        adapter.validate_schema(payload)


def test_layout_schema_validation_fails() -> None:
    adapter = LayoutAdapter(object(), object(), Path("/tmp/repo"))
    payload = _load_payload(LAYOUT_SCHEMA)
    with pytest.raises(ValueError):
        adapter.validate_schema(payload)


def test_semgrep_schema_validation_fails() -> None:
    adapter = SemgrepAdapter(object(), object(), object(), Path("/tmp/repo"))
    payload = _load_payload(SEMGREP_SCHEMA)
    with pytest.raises(ValueError):
        adapter.validate_schema(payload)
