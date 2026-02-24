#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_index(results_dir: Path) -> dict:
    """Walk runs/ directory and build a catalog from run_manifest.json files."""
    runs_dir = results_dir / "runs"
    entries: list[dict] = []

    if runs_dir.is_dir():
        for manifest_path in sorted(runs_dir.rglob("run_manifest.json")):
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            cr = manifest.get("collection_run", {})
            entry = {
                "repo_id": cr.get("repo_id", ""),
                "collection_run_id": cr.get("collection_run_id", ""),
                "run_id": cr.get("run_id", ""),
                "commit": cr.get("commit", ""),
                "branch": cr.get("branch", ""),
                "status": cr.get("status", ""),
                "started_at": cr.get("started_at", ""),
                "completed_at": cr.get("completed_at"),
                "tool_count": len(manifest.get("tools", [])),
                "path": str(manifest_path.parent.relative_to(results_dir)) + "/",
            }
            entries.append(entry)

    # Sort by started_at descending (most recent first)
    entries.sort(key=lambda e: e.get("started_at", ""), reverse=True)

    return {
        "schema_version": 1,
        "updated_at": _utc_now_iso(),
        "total_runs": len(entries),
        "runs": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build index.json catalog from run manifests in a results directory."
    )
    parser.add_argument(
        "--results-dir",
        required=True,
        help="Path to the results repository root (must contain runs/ subdirectory)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output path for index.json (default: <results-dir>/index.json)",
    )
    args = parser.parse_args()

    results_dir = Path(args.results_dir).resolve()
    out_path = Path(args.out).resolve() if args.out else results_dir / "index.json"

    index = build_index(results_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

    print(f"Index written: {out_path} ({index['total_runs']} runs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
