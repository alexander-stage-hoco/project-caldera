import json
from pathlib import Path

from scripts.evaluate import load_output


def test_load_output_unwraps_envelope(tmp_path: Path) -> None:
    payload = {
        "metadata": {"tool_name": "layout-scanner"},
        "data": {"schema_version": "1.0.0", "tool": "layout-scanner"},
    }
    path = tmp_path / "output.json"
    path.write_text(json.dumps(payload))

    data = load_output(path)
    assert data == payload["data"]
