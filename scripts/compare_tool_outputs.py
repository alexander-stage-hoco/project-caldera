"""Compare Docker vs native tool outputs, ignoring volatile fields.

Usage:
    .venv/bin/python scripts/compare_tool_outputs.py \
        --native outputs/native/output.json \
        --docker outputs/docker/output.json
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

# Patterns for volatile values that should be ignored during comparison
UUID_V4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)
ISO_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
)

# Top-level metadata keys that are always volatile
VOLATILE_METADATA_KEYS = {"run_id", "timestamp", "tool_run_id"}


def _is_volatile_value(value: str) -> bool:
    """Return True if the string value looks like a UUID or ISO timestamp."""
    if not isinstance(value, str):
        return False
    return bool(UUID_V4_RE.match(value) or ISO_TIMESTAMP_RE.match(value))


def _strip_volatile(obj: object, path: str = "") -> object:
    """Recursively strip volatile fields from a JSON-like object."""
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            # Drop known volatile metadata keys
            if path == "metadata" and key in VOLATILE_METADATA_KEYS:
                continue
            stripped = _strip_volatile(value, current_path)
            result[key] = stripped
        return result
    if isinstance(obj, list):
        return [_strip_volatile(item, f"{path}[]") for item in obj]
    if isinstance(obj, str) and _is_volatile_value(obj):
        return "<VOLATILE>"
    return obj


def _collect_diffs(
    native: object,
    docker: object,
    path: str = "$",
    diffs: list[str] | None = None,
) -> list[str]:
    """Collect human-readable diff descriptions between two objects."""
    if diffs is None:
        diffs = []

    if type(native) is not type(docker):
        diffs.append(f"{path}: type mismatch: {type(native).__name__} vs {type(docker).__name__}")
        return diffs

    if isinstance(native, dict):
        all_keys = sorted(set(native) | set(docker))
        for key in all_keys:
            child_path = f"{path}.{key}"
            if key not in native:
                diffs.append(f"{child_path}: missing in native")
            elif key not in docker:
                diffs.append(f"{child_path}: missing in docker")
            else:
                _collect_diffs(native[key], docker[key], child_path, diffs)
        return diffs

    if isinstance(native, list):
        if len(native) != len(docker):
            diffs.append(f"{path}: array length {len(native)} vs {len(docker)}")
            return diffs
        for i, (n_item, d_item) in enumerate(zip(native, docker)):
            _collect_diffs(n_item, d_item, f"{path}[{i}]", diffs)
        return diffs

    if native != docker:
        n_repr = repr(native) if len(repr(native)) < 80 else repr(native)[:77] + "..."
        d_repr = repr(docker) if len(repr(docker)) < 80 else repr(docker)[:77] + "..."
        diffs.append(f"{path}: {n_repr} != {d_repr}")

    return diffs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare Docker vs native tool outputs (ignoring timestamps/UUIDs)."
    )
    parser.add_argument("--native", required=True, type=Path, help="Path to native output.json")
    parser.add_argument("--docker", required=True, type=Path, help="Path to Docker output.json")
    parser.add_argument("--max-diffs", type=int, default=20, help="Max diff lines to show")
    args = parser.parse_args()

    if not args.native.exists():
        print(f"ERROR: Native output not found: {args.native}", file=sys.stderr)
        return 1
    if not args.docker.exists():
        print(f"ERROR: Docker output not found: {args.docker}", file=sys.stderr)
        return 1

    native_data = json.loads(args.native.read_text())
    docker_data = json.loads(args.docker.read_text())

    # Strip volatile fields before comparison
    native_clean = _strip_volatile(copy.deepcopy(native_data))
    docker_clean = _strip_volatile(copy.deepcopy(docker_data))

    diffs = _collect_diffs(native_clean, docker_clean)

    if not diffs:
        print("PASS: Docker and native outputs match (ignoring volatile fields).")
        return 0

    print(f"FAIL: {len(diffs)} difference(s) found:\n")
    for diff in diffs[: args.max_diffs]:
        print(f"  {diff}")
    if len(diffs) > args.max_diffs:
        print(f"  ... and {len(diffs) - args.max_diffs} more")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
