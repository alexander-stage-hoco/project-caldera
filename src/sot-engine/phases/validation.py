from __future__ import annotations

import json
from pathlib import Path

from phases.utilities import _is_fallback_commit


def load_payload(path: Path) -> dict:
    return json.loads(path.read_text())


def validate_payload(
    metadata: dict,
    repo_id: str,
    run_id: str,
    *,
    expected_commit: str | None = None,
    expected_tool: str | None = None,
) -> None:
    if metadata.get("repo_id") != repo_id:
        raise ValueError("repo_id mismatch between orchestrator and payload")
    if metadata.get("run_id") != run_id:
        raise ValueError("run_id mismatch between orchestrator and payload")
    if expected_commit and not _is_fallback_commit(expected_commit):
        payload_commit = metadata.get("commit", "")
        if payload_commit and not _is_fallback_commit(payload_commit):
            if payload_commit != expected_commit:
                raise ValueError(
                    f"commit mismatch: orchestrator={expected_commit[:8]}… "
                    f"payload={payload_commit[:8]}…"
                )
    if expected_tool:
        payload_tool = metadata.get("tool_name", "")
        if payload_tool and payload_tool != expected_tool:
            raise ValueError(
                f"tool_name mismatch: expected={expected_tool} "
                f"payload={payload_tool}"
            )
