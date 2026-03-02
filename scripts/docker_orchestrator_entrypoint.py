#!/usr/bin/env python3
"""Orchestrator entrypoint for the dockerized pipeline.

Reads ``LATEST.json`` written by the runner, then delegates to
``analyze_bundle.py`` for ingestion (orchestrator + dbt + report).
Optionally exports results to a git results repository.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    workspace = Path(os.environ.get("WORKSPACE", "/workspace"))
    db_path = Path(os.environ.get("DB_PATH", "/workspace/db/caldera_sot.duckdb"))
    results_dir = Path(os.environ.get("RESULTS_DIR", "/workspace/results"))
    pipeline_llm = os.environ.get("PIPELINE_LLM", "0")
    results_repo = os.environ.get("RESULTS_REPO", "")

    # ── Read LATEST.json ─────────────────────────────────────────────────
    latest_path = workspace / "artifacts" / "LATEST.json"
    if not latest_path.exists():
        print(f"ERROR: LATEST.json not found at {latest_path}", file=sys.stderr)
        return 1

    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    bundle_root = Path(latest["bundle_root"])
    repo_id = latest["repo_id"]

    if not bundle_root.exists():
        print(f"ERROR: bundle_root does not exist: {bundle_root}", file=sys.stderr)
        return 1

    print(f"Repo ID:     {repo_id}")
    print(f"Run ID:      {latest['run_id']}")
    print(f"Bundle:      {bundle_root}")
    print(f"DB:          {db_path}")
    print(f"Results:     {results_dir}")
    print(f"LLM:         {pipeline_llm}")
    print()

    # ── Ensure output dirs exist ─────────────────────────────────────────
    db_path.parent.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    report_out = results_dir / "report.html"

    # ── Determine repo path ──────────────────────────────────────────────
    # The runner clones the repo into /workspace/repo
    repo_path = workspace / "repo"
    if not repo_path.is_dir():
        # Fallback: use bundle_root parent as repo path
        repo_path = bundle_root
        print(f"WARNING: /workspace/repo not found, using {repo_path}")

    # ── Run analyze_bundle.py ────────────────────────────────────────────
    cmd = [
        sys.executable,
        "scripts/analyze_bundle.py",
        "--repo-path", str(repo_path),
        "--bundle", str(bundle_root),
        "--db-path", str(db_path),
        "--report-out", str(report_out),
        "--llm", str(pipeline_llm),
    ]

    print("=== Running analyze_bundle.py ===")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print(f"ERROR: analyze_bundle.py exited with code {result.returncode}", file=sys.stderr)
        return result.returncode

    # ── Copy LLM observability logs if present ───────────────────────────
    llm_logs_src = workspace / "src" / "output" / "llm_logs"
    if llm_logs_src.is_dir() and any(llm_logs_src.iterdir()):
        import shutil
        shutil.copytree(llm_logs_src, results_dir / "llm_logs", dirs_exist_ok=True)
        print(f"  LLM logs: {results_dir / 'llm_logs'}")

    # ── Optional: export to results repo ─────────────────────────────────
    if results_repo:
        run_dir = report_out.parent
        export_cmd = [
            sys.executable,
            "scripts/export_results.py",
            "--run-dir", str(run_dir),
            "--db", str(db_path),
            "--results-repo", results_repo,
            "--push",
        ]
        print()
        print("=== Exporting to results repo ===")
        export_result = subprocess.run(export_cmd, check=False)
        if export_result.returncode != 0:
            print(f"WARNING: export_results.py exited with code {export_result.returncode}", file=sys.stderr)

    print()
    print("=== Orchestrator complete ===")
    print(f"  Report: {report_out}")
    print(f"  DB:     {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
