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
from typing import Callable

# Patterns for volatile values that should be ignored during comparison
UUID_V4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)
ISO_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
)

# Top-level metadata keys that are always volatile
VOLATILE_METADATA_KEYS = {"run_id", "timestamp", "tool_run_id", "tool_version", "repo_path"}

# Data-level keys that are volatile (timing/performance and version fields at any depth)
VOLATILE_DATA_KEYS = {
    "scan_duration_ms",
    "scan_time_ms",
    "files_per_second",
    "analysis_duration_ms",
    "elapsed_ms",
    "elapsed_seconds",
    "duration_ms",
    # Tool version strings differ between native (macOS) and Docker (Linux) installs
    "tool_version",
    "lizard_version",
    # Auto-generated IDs that are non-deterministic across platforms
    "clone_id",
    # Tool error/warning arrays contain environment-specific paths and messages
    "errors",
    "warnings",
}

# Directory-structure summary keys that are inherently path-depth-dependent.
# Native runs have deeper absolute paths than Docker's /repo mount, so directory
# counts, depths, and per-directory averages will always differ slightly.
VOLATILE_STRUCTURE_KEYS = {
    "total_directories",
    "directory_count",
    "avg_depth",
    "max_depth",
    "avg_files_per_directory",
    "leaf_directory_count",
    "depth",  # per-directory depth computed from absolute path
}

# Tool-specific volatile keys: stripped alongside VOLATILE_DATA_KEYS when --tool matches
TOOL_VOLATILE_KEYS: dict[str, set[str]] = {
    "trivy": {
        "references",       # Vuln reference URLs differ per DB version
        "description",      # Vuln descriptions differ per DB version
        "published_date",   # Date formatting varies
        "age_days",         # Computed from published_date
    },
    "gitleaks": {
        "fingerprint",      # Hash includes platform-specific path components
    },
    "scancode": {
        "detection_count",  # Varies with engine version
    },
    "roslyn-analyzers": {
        "message",          # Diagnostic messages vary per SDK version
    },
}

# Repo name placeholders used for normalization
_DOCKER_MOUNT_NAME = "repo"
_REPO_PLACEHOLDER = "<REPO>"

# ── Tool normalizer registry ─────────────────────────────────────────────────

_ToolNormalizer = Callable[
    [object, object, argparse.Namespace], tuple[object, object]
]
TOOL_NORMALIZERS: dict[str, _ToolNormalizer] = {}


def _register_normalizer(tool: str) -> Callable[[_ToolNormalizer], _ToolNormalizer]:
    """Decorator to register a tool-specific normalizer function."""
    def decorator(fn: _ToolNormalizer) -> _ToolNormalizer:
        TOOL_NORMALIZERS[tool] = fn
        return fn
    return decorator


# ── Trivy normalizer ─────────────────────────────────────────────────────────

# IaC target types that should be filtered out (Docker's misconfig analyzer
# crashes on ARM64, falls back to vuln-only — so misconfigs are absent)
_TRIVY_IAC_TARGET_TYPES = {
    "terraform", "dockerfile", "kubernetes", "cloudformation", "ansible", "helm",
}


def _recount_severity(data: object) -> None:
    """Recompute findings_summary.by_severity from the vulnerabilities array only."""
    if not isinstance(data, dict):
        return
    vulns = data.get("vulnerabilities")
    summary = data.get("findings_summary")
    if not isinstance(vulns, list) or not isinstance(summary, dict):
        return
    counts: dict[str, int] = {}
    for v in vulns:
        if isinstance(v, dict):
            sev = v.get("severity", "UNKNOWN")
            counts[sev] = counts.get(sev, 0) + 1
    summary["by_severity"] = counts
    summary["total_findings"] = sum(counts.values())


@_register_normalizer("trivy")
def _normalize_trivy(
    native: object, docker: object, args: argparse.Namespace,
) -> tuple[object, object]:
    """Normalize trivy output to remove IaC misconfig noise."""
    for data in (native, docker):
        if not isinstance(data, dict):
            continue
        d = data.get("data") if "data" in data else data

        if not isinstance(d, dict):
            continue

        # Remove iac_misconfigurations entirely
        d.pop("iac_misconfigurations", None)
        d.pop("total_misconfigurations", None)

        # Filter IaC targets
        targets = d.get("targets")
        if isinstance(targets, list):
            d["targets"] = [
                t for t in targets
                if not (
                    isinstance(t, dict)
                    and str(t.get("type", "")).lower() in _TRIVY_IAC_TARGET_TYPES
                )
            ]

        # Recount severity from vulnerabilities only
        _recount_severity(d)

    return native, docker


# ── Core helpers ──────────────────────────────────────────────────────────────

def _is_volatile_value(value: str) -> bool:
    """Return True if the string value looks like a UUID or ISO timestamp."""
    if not isinstance(value, str):
        return False
    return bool(UUID_V4_RE.match(value) or ISO_TIMESTAMP_RE.match(value))


def _normalize_repo_name(value: str, native_name: str) -> str:
    """Replace repo root directory names with a placeholder.

    Handles several cases:
    - Native root dir name (e.g. '2026-01-24-Project-Caldera') replaced anywhere
    - Any path prefix before the repo name is stripped (e.g. 'Users/foo/Projects/<REPO>' → '<REPO>')
    - Docker mount 'repo' replaced at path boundaries to avoid false positives
      (e.g. 'repository' should not be affected)
    """
    # Native name is typically unique enough to replace everywhere
    value = value.replace(native_name, _REPO_PLACEHOLDER)

    # Strip any path prefix before <REPO> (e.g. 'Users/foo/bar/<REPO>/src' → '<REPO>/src')
    value = re.sub(r"^[^<]*" + re.escape(_REPO_PLACEHOLDER), _REPO_PLACEHOLDER, value)

    # Docker mount: replace 'repo' at start of string or after '/' (boundary-safe)
    value = re.sub(
        r"(?:^|(?<=/))(" + re.escape(_DOCKER_MOUNT_NAME) + r")(?=/|$)",
        _REPO_PLACEHOLDER,
        value,
    )

    # Strip leading slashes (Docker absolute paths vs native relative paths)
    if _REPO_PLACEHOLDER in value:
        value = value.lstrip("/")

    return value


def _strip_volatile(
    obj: object,
    path: str = "",
    native_name: str | None = None,
    tool_volatile_keys: set[str] | None = None,
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
            # Drop directory-structure summary keys (path-depth-dependent)
            if key in VOLATILE_STRUCTURE_KEYS:
                continue
            # Drop tool-specific volatile keys
            if tool_volatile_keys and key in tool_volatile_keys:
                continue
            # Drop run_id in data context (contains timestamps/repo names)
            if key == "run_id" and path.startswith("data"):
                continue
            stripped = _strip_volatile(value, current_path, native_name, tool_volatile_keys)
            result[key] = stripped
        return result
    if isinstance(obj, list):
        return [_strip_volatile(item, f"{path}[]", native_name, tool_volatile_keys) for item in obj]
    if isinstance(obj, str):
        if _is_volatile_value(obj):
            return "<VOLATILE>"
        if native_name:
            return _normalize_repo_name(obj, native_name)
    return obj


def _filter_prefix_directories(obj: object) -> object:
    """Remove directory entries that are artifacts of the native host path prefix.

    After repo-name normalization, genuine directories start with '<REPO>/' or are
    exactly '<REPO>'.  Entries like 'Users', 'Users/alexander.stage', etc. are
    host-path artifacts that only appear in native runs and should be filtered out.
    """
    if not isinstance(obj, dict):
        return obj
    result = {}
    for key, value in obj.items():
        if key == "directories" and isinstance(value, list):
            filtered = []
            for item in value:
                if isinstance(item, dict) and "path" in item:
                    path = item["path"]
                    # Keep only entries rooted at the repo placeholder
                    if path == _REPO_PLACEHOLDER or path.startswith(_REPO_PLACEHOLDER + "/"):
                        filtered.append(_filter_prefix_directories(item))
                else:
                    filtered.append(_filter_prefix_directories(item))
            result[key] = filtered
        elif isinstance(value, (dict, list)):
            result[key] = _filter_prefix_directories(value)
        else:
            result[key] = value
    return result


def _find_disputed_languages(native: object, docker: object) -> set[str]:
    """Find language names affected by cross-platform classification differences.

    Returns the set of language names that appear as mismatches in file entries
    (e.g. one platform says 'Treetop', the other says 'TemplateToolkit').
    """
    disputed: set[str] = set()
    if not isinstance(native, dict) or not isinstance(docker, dict):
        return disputed

    for key in native:
        n_val = native[key]
        d_val = docker.get(key)
        if d_val is None:
            continue
        if isinstance(n_val, dict) and isinstance(d_val, dict):
            disputed |= _find_disputed_languages(n_val, d_val)
        elif isinstance(n_val, list) and isinstance(d_val, list):
            if n_val and isinstance(n_val[0], dict) and "language" in n_val[0]:
                path_key = None
                for pk in ("file_path", "path", "relative_path"):
                    if pk in n_val[0]:
                        path_key = pk
                        break
                if path_key:
                    n_by_path = {
                        item[path_key]: item
                        for item in n_val
                        if isinstance(item, dict) and path_key in item
                    }
                    d_by_path = {
                        item[path_key]: item
                        for item in d_val
                        if isinstance(item, dict) and path_key in item
                    }
                    for p in n_by_path:
                        if p in d_by_path:
                            n_lang = n_by_path[p].get("language")
                            d_lang = d_by_path[p].get("language")
                            if n_lang != d_lang:
                                if n_lang:
                                    disputed.add(n_lang)
                                if d_lang:
                                    disputed.add(d_lang)
    return disputed


def _apply_language_filter(
    native: object, docker: object, disputed: set[str],
) -> tuple[object, object]:
    """Recursively filter entries affected by disputed language classifications."""
    if not isinstance(native, dict) or not isinstance(docker, dict):
        return native, docker

    native = dict(native)
    docker = dict(docker)

    # Keys whose values are derived from language-dependent aggregations
    aggregate_keys = {"cocomo", "by_language"}

    for key in list(native):
        n_val = native[key]
        d_val = docker.get(key)

        if d_val is None:
            continue

        # Handle aggregate keys affected by language mismatches
        if key in aggregate_keys:
            if key == "by_language" and isinstance(n_val, dict) and isinstance(d_val, dict):
                native[key] = {k: v for k, v in n_val.items() if k not in disputed}
                docker[key] = {k: v for k, v in d_val.items() if k not in disputed}
            elif key == "cocomo":
                # COCOMO estimates derive from total code lines which change
                # when files are classified differently — mark as volatile
                native[key] = "<LANGUAGE_VOLATILE>"
                docker[key] = "<LANGUAGE_VOLATILE>"
            continue

        if isinstance(n_val, dict) and isinstance(d_val, dict):
            native[key], docker[key] = _apply_language_filter(n_val, d_val, disputed)
        elif (
            isinstance(n_val, list)
            and isinstance(d_val, list)
            and n_val
            and isinstance(n_val[0], dict)
            and "language" in n_val[0]
        ):
            first = n_val[0]
            # File array (has a path key): filter out files with disputed languages
            path_key = None
            for pk in ("file_path", "path", "relative_path"):
                if pk in first:
                    path_key = pk
                    break

            if path_key:
                native[key] = [
                    i for i in n_val
                    if not (isinstance(i, dict) and i.get("language") in disputed)
                ]
                docker[key] = [
                    i for i in d_val
                    if not (isinstance(i, dict) and i.get("language") in disputed)
                ]
            elif "name" in first:
                # Language-aggregate array: filter out disputed language entries
                native[key] = [
                    i for i in n_val
                    if not (isinstance(i, dict) and i.get("name") in disputed)
                ]
                docker[key] = [
                    i for i in d_val
                    if not (isinstance(i, dict) and i.get("name") in disputed)
                ]

    return native, docker


def _filter_language_mismatches(native: object, docker: object) -> tuple[object, object]:
    """Remove entries affected by cross-platform language classification differences.

    scc binaries on different platforms (macOS arm64 vs Linux x86_64) can classify
    ambiguous files into different languages, which cascades into all derived metrics
    including per-language aggregations, by_language summaries, and COCOMO estimates.
    """
    disputed = _find_disputed_languages(native, docker)
    if not disputed:
        return native, docker
    return _apply_language_filter(native, docker, disputed)


def _sort_key(item: object) -> str:
    """Generate a deterministic sort key for an array element."""
    if isinstance(item, dict):
        # Prefer common deterministic keys; fall back to full JSON repr
        for key in ("file_path", "path", "relative_path", "name", "id", "rule_id", "fingerprint"):
            if key in item:
                return str(item[key])
        # Composite key for findings/duplications that lack a single unique ID
        # (e.g. pmd-cpd duplications: sort by first occurrence file + line)
        if "occurrences" in item and isinstance(item["occurrences"], list) and item["occurrences"]:
            occ = item["occurrences"][0]
            if isinstance(occ, dict):
                return f"{occ.get('file', '')}:{occ.get('line_start', 0)}"
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
    *,
    numeric_tolerance: float = 0.0,
    array_length_tolerance: float = 0.0,
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
                _collect_diffs(
                    native[key], docker[key], child_path, diffs,
                    numeric_tolerance=numeric_tolerance,
                    array_length_tolerance=array_length_tolerance,
                )
        return diffs

    if isinstance(native, list):
        if len(native) != len(docker):
            # Check array length tolerance
            if array_length_tolerance > 0 and len(native) > 0 and len(docker) > 0:
                max_len = max(len(native), len(docker))
                diff_ratio = abs(len(native) - len(docker)) / max_len
                if diff_ratio <= array_length_tolerance:
                    # Within tolerance — compare by intersection
                    n_by_key = {_sort_key(item): item for item in native}
                    d_by_key = {_sort_key(item): item for item in docker}
                    common_keys = sorted(set(n_by_key) & set(d_by_key))
                    n_only = len(native) - len(common_keys)
                    d_only = len(docker) - len(common_keys)
                    if n_only > 0 or d_only > 0:
                        diffs.append(
                            f"{path}: array length {len(native)} vs {len(docker)} "
                            f"(within {array_length_tolerance:.0%} tolerance; "
                            f"{n_only} native-only, {d_only} docker-only)"
                        )
                    for i, ck in enumerate(common_keys):
                        _collect_diffs(
                            n_by_key[ck], d_by_key[ck], f"{path}[{i}]", diffs,
                            numeric_tolerance=numeric_tolerance,
                            array_length_tolerance=array_length_tolerance,
                        )
                    return diffs

            diffs.append(f"{path}: array length {len(native)} vs {len(docker)}")
            return diffs
        for i, (n_item, d_item) in enumerate(zip(native, docker)):
            _collect_diffs(
                n_item, d_item, f"{path}[{i}]", diffs,
                numeric_tolerance=numeric_tolerance,
                array_length_tolerance=array_length_tolerance,
            )
        return diffs

    if native != docker:
        # Numeric tolerance check
        if (
            numeric_tolerance > 0
            and isinstance(native, (int, float))
            and isinstance(docker, (int, float))
        ):
            denominator = max(abs(native), abs(docker), 1)
            if abs(native - docker) / denominator <= numeric_tolerance:
                return diffs  # close enough

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
                        help="Tool name (for JSON output metadata and tool-specific normalization)")
    parser.add_argument("--repo-name", type=str, default=None,
                        help="Native repo directory name (e.g. 'my-project') for root-dir normalization")
    parser.add_argument("--ignore-language-diffs", action="store_true",
                        help="Ignore files where language classification differs (platform-specific)")
    parser.add_argument("--numeric-tolerance", type=float, default=0.0,
                        help="Relative tolerance for numeric comparisons (e.g. 0.001 = 0.1%%)")
    parser.add_argument("--array-length-tolerance", type=float, default=0.0,
                        help="Relative tolerance for array length differences (e.g. 0.05 = 5%%)")
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

    # Resolve tool-specific volatile keys
    tool_volatile = TOOL_VOLATILE_KEYS.get(args.tool)

    # Strip volatile fields before comparison
    native_clean = _strip_volatile(
        copy.deepcopy(native_data), native_name=args.repo_name,
        tool_volatile_keys=tool_volatile,
    )
    docker_clean = _strip_volatile(
        copy.deepcopy(docker_data), native_name=args.repo_name,
        tool_volatile_keys=tool_volatile,
    )

    # Filter out host-path-prefix directory entries (native has extra levels)
    if args.repo_name:
        native_clean = _filter_prefix_directories(native_clean)
        docker_clean = _filter_prefix_directories(docker_clean)

    # Optionally ignore files where language classification differs across platforms
    if args.ignore_language_diffs:
        native_clean, docker_clean = _filter_language_mismatches(native_clean, docker_clean)

    # Apply tool-specific normalizer (after generic stripping, before diff collection)
    normalizer = TOOL_NORMALIZERS.get(args.tool)
    if normalizer:
        native_clean, docker_clean = normalizer(native_clean, docker_clean, args)

    # Optionally sort arrays for order-independent comparison
    if args.sort_arrays:
        native_clean = _sort_arrays(native_clean)
        docker_clean = _sort_arrays(docker_clean)

    diffs = _collect_diffs(
        native_clean, docker_clean,
        numeric_tolerance=args.numeric_tolerance,
        array_length_tolerance=args.array_length_tolerance,
    )

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
        result: dict[str, object] = {
            "tool": args.tool,
            "status": status,
            "diff_count": len(diffs),
            "diffs": diffs[: args.max_diffs],
            "normalizations_applied": {
                "tool_volatile_keys": sorted(tool_volatile) if tool_volatile else [],
                "tool_normalizer": args.tool if normalizer else None,
                "numeric_tolerance": args.numeric_tolerance,
                "array_length_tolerance": args.array_length_tolerance,
            },
        }
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(result, indent=2) + "\n")

    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
