"""Compare Docker vs native tool outputs, ignoring volatile fields.

Usage:
    .venv/bin/python scripts/compare_tool_outputs.py \
        --native outputs/native/output.json \
        --docker outputs/docker/output.json \
        --sort-arrays \
        --repo-name 2026-01-24-Project-Caldera \
        --output-json results/scc-parity.json
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
VOLATILE_METADATA_KEYS = {"run_id", "timestamp", "tool_run_id", "tool_version", "repo_path"}

# Data-level keys that are volatile (timing/performance fields at any depth)
VOLATILE_DATA_KEYS = {
    "scan_duration_ms",
    "scan_time_ms",
    "files_per_second",
    "analysis_duration_ms",
    "elapsed_ms",
    "duration_ms",
}

# Repo name placeholders used for normalization
_DOCKER_MOUNT_NAME = "repo"
_REPO_PLACEHOLDER = "<REPO>"


def _is_volatile_value(value: str) -> bool:
    """Return True if the string value looks like a UUID or ISO timestamp."""
    if not isinstance(value, str):
        return False
    return bool(UUID_V4_RE.match(value) or ISO_TIMESTAMP_RE.match(value))


def _normalize_repo_name(value: str, native_name: str) -> str:
    """Replace repo root directory names with a placeholder.

    Handles two cases:
    - Native root dir name (e.g. '2026-01-24-Project-Caldera') replaced anywhere
    - Docker mount '/repo' replaced only at path boundaries to avoid false positives
      (e.g. 'repository' should not be affected)
    """
    # Native name is typically unique enough to replace everywhere
    value = value.replace(native_name, _REPO_PLACEHOLDER)
    # Docker mount: replace '/repo/' prefix and standalone '/repo'
    value = re.sub(r"(?<=/)" + re.escape(_DOCKER_MOUNT_NAME) + r"(?=/|$)", _REPO_PLACEHOLDER, value)
    return value


def _strip_volatile(
    obj: object,
    path: str = "",
    native_name: str | None = None,
) -> object:
    """Recursively strip volatile fields from a JSON-like object."""
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            # Drop known volatile metadata keys
            if path == "metadata" and key in VOLATILE_METADATA_KEYS:
                continue
            # Drop volatile data keys (timing/perf) at any depth
            if key in VOLATILE_DATA_KEYS:
                continue
            # Drop run_id in data context (contains timestamps/repo names)
            if key == "run_id" and path.startswith("data"):
                continue
            stripped = _strip_volatile(value, current_path, native_name)
            result[key] = stripped
        return result
    if isinstance(obj, list):
        return [_strip_volatile(item, f"{path}[]", native_name) for item in obj]
    if isinstance(obj, str):
        if _is_volatile_value(obj):
            return "<VOLATILE>"
        if native_name:
            return _normalize_repo_name(obj, native_name)
    return obj


def _sort_key(item: object) -> str:
    """Generate a deterministic sort key for an array element."""
    if isinstance(item, dict):
        # Prefer common deterministic keys; fall back to full JSON repr
        for key in ("file_path", "path", "relative_path", "name", "id", "rule_id"):
            if key in item:
                return str(item[key])
        return json.dumps(item, sort_keys=True, default=str)
    return str(item)


def _sort_arrays(obj: object) -> object:
    """Recursively sort arrays by deterministic keys for order-independent comparison."""
    if isinstance(obj, dict):
        return {k: _sort_arrays(v) for k, v in obj.items()}
    if isinstance(obj, list):
        sorted_items = [_sort_arrays(item) for item in obj]
        try:
            sorted_items.sort(key=_sort_key)
        except TypeError:
            pass  # mixed types — keep original order
        return sorted_items
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
    parser.add_argument("--sort-arrays", action="store_true",
                        help="Sort arrays by deterministic key before comparison")
    parser.add_argument("--output-json", type=Path, default=None,
                        help="Write structured JSON result for batch aggregation")
    parser.add_argument("--tool", type=str, default="unknown",
                        help="Tool name (for JSON output metadata)")
    parser.add_argument("--repo-name", type=str, default=None,
                        help="Native repo directory name (e.g. 'my-project') for root-dir normalization")
    args = parser.parse_args()

    # Graceful handling of missing files
    missing = []
    if not args.native.exists():
        missing.append(f"native ({args.native})")
    if not args.docker.exists():
        missing.append(f"docker ({args.docker})")

    if missing:
        msg = f"ERROR: Output not found: {', '.join(missing)}"
        print(msg, file=sys.stderr)
        if args.output_json:
            result = {
                "tool": args.tool,
                "status": "error",
                "diff_count": 0,
                "diffs": [],
                "error": msg,
            }
            args.output_json.parent.mkdir(parents=True, exist_ok=True)
            args.output_json.write_text(json.dumps(result, indent=2) + "\n")
        return 1

    native_data = json.loads(args.native.read_text())
    docker_data = json.loads(args.docker.read_text())

    # Strip volatile fields before comparison
    native_clean = _strip_volatile(copy.deepcopy(native_data), native_name=args.repo_name)
    docker_clean = _strip_volatile(copy.deepcopy(docker_data), native_name=args.repo_name)

    # Optionally sort arrays for order-independent comparison
    if args.sort_arrays:
        native_clean = _sort_arrays(native_clean)
        docker_clean = _sort_arrays(docker_clean)

    diffs = _collect_diffs(native_clean, docker_clean)

    if not diffs:
        print("PASS: Docker and native outputs match (ignoring volatile fields).")
        status = "pass"
    else:
        print(f"FAIL: {len(diffs)} difference(s) found:\n")
        for diff in diffs[: args.max_diffs]:
            print(f"  {diff}")
        if len(diffs) > args.max_diffs:
            print(f"  ... and {len(diffs) - args.max_diffs} more")
        status = "fail"

    if args.output_json:
        result = {
            "tool": args.tool,
            "status": status,
            "diff_count": len(diffs),
            "diffs": diffs[: args.max_diffs],
        }
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, indent=2) + "\n")

    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
