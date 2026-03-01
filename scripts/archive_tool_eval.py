#!/usr/bin/env python3
"""Archive tool evaluation results immutably.

Copies evaluation results to a timestamped history directory and updates
a per-tool eval_index.json manifest.

Usage::

    python scripts/archive_tool_eval.py <tool-name>
    python scripts/archive_tool_eval.py --all

Each archived run is stored at::

    src/tools/<tool>/evaluation/history/<timestamp>/
        ├── programmatic_results.json  (copied from results/)
        ├── llm_results.json           (copied from results/)
        └── eval_manifest.json         (generated)

The per-tool index is at::

    src/tools/<tool>/evaluation/eval_index.json
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True,
        ).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def archive_tool(tool_dir: Path, commit: str | None = None) -> dict | None:
    """Archive current evaluation results for a single tool.

    Returns the manifest dict if results were found, else None.
    """
    eval_dir = tool_dir / "evaluation"
    results_dir = eval_dir / "results"
    if not results_dir.is_dir():
        return None

    # Find result files
    result_files = sorted(results_dir.glob("*.json"))
    if not result_files:
        return None

    timestamp = _utc_now_iso()
    history_dir = eval_dir / "history" / timestamp
    history_dir.mkdir(parents=True, exist_ok=True)

    # Copy result files
    copied = []
    for f in result_files:
        dest = history_dir / f.name
        shutil.copy2(f, dest)
        copied.append(f.name)

    # Build manifest
    manifest = {
        "schema_version": 1,
        "tool": tool_dir.name,
        "timestamp": timestamp,
        "commit": commit or _git_commit(),
        "files": copied,
        "archived_at": datetime.now(timezone.utc).isoformat(),
    }

    # Try to extract scores from known result file patterns
    for f in result_files:
        try:
            data = json.loads(f.read_text())
            if isinstance(data, dict):
                if "overall_score" in data:
                    manifest.setdefault("scores", {})[f.stem] = data["overall_score"]
                elif "score" in data:
                    manifest.setdefault("scores", {})[f.stem] = data["score"]
        except Exception:
            pass

    manifest_path = history_dir / "eval_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Update per-tool index
    _update_index(eval_dir, manifest)

    return manifest


def _update_index(eval_dir: Path, manifest: dict) -> None:
    """Append entry to the tool's eval_index.json."""
    index_path = eval_dir / "eval_index.json"
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text())
        except Exception:
            index = {"entries": []}
    else:
        index = {"entries": []}

    # Add summary entry (without large file contents)
    entry = {
        "timestamp": manifest["timestamp"],
        "commit": manifest["commit"],
        "scores": manifest.get("scores", {}),
        "files": manifest["files"],
    }
    index["entries"].append(entry)
    index["last_updated"] = datetime.now(timezone.utc).isoformat()

    index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive tool evaluation results.")
    parser.add_argument("tool", nargs="?", help="Tool name to archive")
    parser.add_argument("--all", action="store_true", help="Archive all tools")
    parser.add_argument("--commit", default=None, help="Git commit SHA")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    tools_dir = repo_root / "src" / "tools"

    if args.all:
        tool_dirs = sorted(p for p in tools_dir.iterdir() if p.is_dir())
    elif args.tool:
        tool_dirs = [tools_dir / args.tool]
    else:
        parser.error("Provide a tool name or --all")
        return 1

    archived = 0
    for td in tool_dirs:
        if not td.is_dir():
            print(f"SKIP: {td.name} — directory not found")
            continue
        result = archive_tool(td, commit=args.commit)
        if result:
            print(f"OK: {td.name} → history/{result['timestamp']}/")
            archived += 1
        else:
            print(f"SKIP: {td.name} — no evaluation results")

    print(f"\nArchived {archived}/{len(tool_dirs)} tools.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
