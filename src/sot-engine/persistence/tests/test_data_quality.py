from __future__ import annotations

from pathlib import Path
import pytest

import json

from persistence.adapters.layout_adapter import LayoutAdapter
from persistence.adapters.lizard_adapter import LizardAdapter
from persistence.adapters.scc_adapter import SccAdapter
from persistence.adapters.semgrep_adapter import SemgrepAdapter


def _capture_logger() -> tuple[list[str], callable]:
    messages: list[str] = []
    return messages, messages.append


def test_scc_adapter_rejects_invalid_paths() -> None:
    messages, logger = _capture_logger()
    adapter = SccAdapter(object(), object(), object(), Path("/tmp/repo"), logger)
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "scc_output.json"
    payload = json.loads(fixture_path.read_text())
    payload["data"]["files"][0]["path"] = "/tmp/otherrepo/src/app.py"

    with pytest.raises(ValueError):
        adapter.validate_quality(payload["data"]["files"])

    assert any("DATA_QUALITY_ERROR" in msg for msg in messages)


def test_lizard_adapter_rejects_invalid_paths() -> None:
    messages, logger = _capture_logger()
    adapter = LizardAdapter(object(), object(), object(), Path("/tmp/repo"), logger)
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "lizard_output.json"
    payload = json.loads(fixture_path.read_text())
    payload["data"]["files"][0]["path"] = "/tmp/otherrepo/src/app.py"

    with pytest.raises(ValueError):
        adapter.validate_quality(payload["data"]["files"])

    assert any("DATA_QUALITY_ERROR" in msg for msg in messages)


def test_layout_adapter_rejects_invalid_paths() -> None:
    messages, logger = _capture_logger()
    adapter = LayoutAdapter(object(), object(), Path("/tmp/repo"), logger)
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "layout_output.json"
    payload = json.loads(fixture_path.read_text())
    payload["data"]["files"]["/tmp/otherrepo/src/app.py"] = payload["data"]["files"].pop("src/app.py")
    payload["data"]["files"]["/tmp/otherrepo/src/app.py"]["path"] = "/tmp/otherrepo/src/app.py"
    payload["data"]["directories"]["/tmp/otherrepo/src"] = payload["data"]["directories"].pop("src")
    payload["data"]["directories"]["/tmp/otherrepo/src"]["path"] = "/tmp/otherrepo/src"

    with pytest.raises(ValueError):
        adapter.validate_quality(payload["data"]["files"], payload["data"]["directories"])

    assert any("DATA_QUALITY_ERROR" in msg for msg in messages)


def test_semgrep_adapter_rejects_invalid_paths() -> None:
    messages, logger = _capture_logger()
    adapter = SemgrepAdapter(object(), object(), object(), Path("/tmp/repo"), logger)
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "semgrep_output.json"
    payload = json.loads(fixture_path.read_text())
    payload["data"]["files"][0]["path"] = "/tmp/otherrepo/src/app.py"

    with pytest.raises(ValueError):
        adapter.validate_quality(payload["data"]["files"])

    assert any("DATA_QUALITY_ERROR" in msg for msg in messages)
