#!/usr/bin/env python3
"""Dockerized runner: clones repo, dispatches tool containers, writes bundle + LATEST.json.

This is the Docker equivalent of ``collect_artifacts.py``.  Instead of invoking
``make analyze`` natively, it runs each tool inside its pre-built
``caldera-tool-<name>`` container via ``docker run``, sharing the repo and
output directories through named Docker volumes.

The resulting bundle (manifest.json + per-tool outputs) is fully compatible with
``analyze_bundle.py`` for downstream ingestion.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


# ── Tool list (must match Makefile DOCKER_TOOLS) ─────────────────────────────

DOCKER_TOOLS: list[str] = [
    "layout-scanner",
    "scc",
    "lizard",
    "semgrep",
    "symbol-scanner",
    "scancode",
    "git-blame-scanner",
    "git-fame",
    "dependensee",
    "coverage-ingest",
    "trivy",
    "gitleaks",
    "git-sizer",
    "pmd-cpd",
    "roslyn-analyzers",
    "devskim",
    "dotcover",
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clone_repo(url: str, dest: Path, depth: int | None = None) -> tuple[str, str]:
    """Clone *url* into *dest* and return (branch, commit)."""
    cmd: list[str] = ["git", "clone"]
    if depth:
        cmd += ["--depth", str(depth)]
    cmd += [url, str(dest)]
    subprocess.run(cmd, check=True)
    branch = (
        subprocess.run(
            ["git", "-C", str(dest), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
        ).stdout.strip()
        or "main"
    )
    commit = (
        subprocess.run(
            ["git", "-C", str(dest), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
        ).stdout.strip()
        or "0" * 40
    )
    return branch, commit


def _git_info(repo_path: Path) -> tuple[str, str]:
    """Return (branch, commit) for a local repo path."""
    branch = (
        subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
        ).stdout.strip()
        or "main"
    )
    commit = (
        subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
        ).stdout.strip()
        or "0" * 40
    )
    return branch, commit


@dataclass(frozen=True)
class ToolResult:
    name: str
    status: str
    duration_seconds: float
    output_json: str | None
    log_path: str | None


# ── Tool dispatch ────────────────────────────────────────────────────────────

def _run_tool_container(
    tool_name: str,
    *,
    run_id: str,
    repo_id: str,
    branch: str,
    commit: str,
    network: str,
    repo_volume: str,
    artifacts_volume: str,
    bundle_root: Path,
) -> ToolResult:
    """Run a single tool container and return the result."""
    output_dir = bundle_root / tool_name / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "execution.log"

    # The tool container writes to /output; we bind the specific tool
    # subdirectory so each tool gets its own output path.
    cmd: list[str] = [
        "docker", "run", "--rm",
        "--network", network,
        "-v", f"{repo_volume}:/repo:ro",
        "-v", f"{output_dir}:/output",
        f"caldera-tool-{tool_name}",
        f"RUN_ID={run_id}",
        f"REPO_ID={repo_id}",
        f"REPO_NAME={repo_id}",
        f"BRANCH={branch}",
        f"COMMIT={commit}",
    ]

    start = time.perf_counter()
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.run(cmd, stdout=log, stderr=log, check=False)
    duration = time.perf_counter() - start

    output_json_path = output_dir / "output.json"
    output_json_rel: str | None = None
    if output_json_path.exists():
        try:
            json.loads(output_json_path.read_text(encoding="utf-8"))
            output_json_rel = str(output_json_path.relative_to(bundle_root))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"  WARNING: {tool_name}/output.json is invalid JSON: {e}")

    return ToolResult(
        name=tool_name,
        status="success" if proc.returncode == 0 and output_json_rel else "failed",
        duration_seconds=round(duration, 3),
        output_json=output_json_rel,
        log_path=str(log_path.relative_to(bundle_root)),
    )


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dockerized runner: clone repo, dispatch tool containers, write bundle."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--repo-url", help="Git URL to clone")
    group.add_argument("--repo-path", help="Local repo path (already mounted)")

    parser.add_argument("--workspace", default="/workspace", help="Workspace root (default: /workspace)")
    parser.add_argument("--skip-tools", default="", help="Comma-separated tool names to skip")
    parser.add_argument("--max-parallel", type=int, default=4, help="Max parallel tool containers")
    parser.add_argument("--clone-depth", type=int, default=None, help="Git clone depth")
    parser.add_argument("--network", default=os.environ.get("DOCKER_NETWORK", "caldera_default"))
    parser.add_argument("--repo-volume", default=os.environ.get("CALDERA_REPO_VOLUME", "caldera-repo"))
    parser.add_argument("--artifacts-volume", default=os.environ.get("CALDERA_ARTIFACTS_VOLUME", "caldera-artifacts"))
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--repo-id", default=None)
    args = parser.parse_args()

    workspace = Path(args.workspace)
    workspace.mkdir(parents=True, exist_ok=True)

    # ── Resolve repo ─────────────────────────────────────────────────────
    if args.repo_url:
        repo_path = workspace / "repo"
        if repo_path.exists():
            print(f"Repo already at {repo_path}, reusing.")
            branch, commit = _git_info(repo_path)
        else:
            print(f"Cloning {args.repo_url} ...")
            branch, commit = _clone_repo(args.repo_url, repo_path, depth=args.clone_depth)
        repo_name = args.repo_url.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")
    else:
        repo_path = Path(args.repo_path)
        if not repo_path.is_dir():
            print(f"ERROR: repo path does not exist: {repo_path}")
            return 1
        branch, commit = _git_info(repo_path)
        repo_name = repo_path.name

    run_id = args.run_id or str(uuid.uuid4())
    repo_id = args.repo_id or repo_name

    # ── Select tools ─────────────────────────────────────────────────────
    skip = {t.strip() for t in args.skip_tools.split(",") if t.strip()}
    # coverage-ingest needs an explicit coverage file; skip by default in Docker mode
    skip.add("coverage-ingest")
    tools = [t for t in DOCKER_TOOLS if t not in skip]

    print(f"Run ID:    {run_id}")
    print(f"Repo ID:   {repo_id}")
    print(f"Branch:    {branch}")
    print(f"Commit:    {commit}")
    print(f"Tools:     {len(tools)} (skipping: {', '.join(sorted(skip)) or 'none'})")
    print(f"Parallel:  {args.max_parallel}")
    print()

    # ── Dispatch tool containers ─────────────────────────────────────────
    artifacts_root = workspace / "artifacts"
    bundle_root = artifacts_root / repo_id / run_id
    bundle_root.mkdir(parents=True, exist_ok=True)

    results: list[ToolResult] = []

    if args.max_parallel <= 1:
        # Sequential
        for idx, tool_name in enumerate(tools, 1):
            print(f"[{idx}/{len(tools)}] {tool_name}")
            result = _run_tool_container(
                tool_name,
                run_id=run_id,
                repo_id=repo_id,
                branch=branch,
                commit=commit,
                network=args.network,
                repo_volume=args.repo_volume,
                artifacts_volume=args.artifacts_volume,
                bundle_root=bundle_root,
            )
            print(f"  {result.status} ({result.duration_seconds}s)")
            results.append(result)
    else:
        # Parallel
        with ThreadPoolExecutor(max_workers=args.max_parallel) as pool:
            future_to_tool = {
                pool.submit(
                    _run_tool_container,
                    tool_name,
                    run_id=run_id,
                    repo_id=repo_id,
                    branch=branch,
                    commit=commit,
                    network=args.network,
                    repo_volume=args.repo_volume,
                    artifacts_volume=args.artifacts_volume,
                    bundle_root=bundle_root,
                ): tool_name
                for tool_name in tools
            }
            for future in as_completed(future_to_tool):
                tool_name = future_to_tool[future]
                try:
                    result = future.result()
                except Exception as exc:
                    result = ToolResult(
                        name=tool_name,
                        status="failed",
                        duration_seconds=0.0,
                        output_json=None,
                        log_path=None,
                    )
                    print(f"  {tool_name}: EXCEPTION: {exc}")
                else:
                    print(f"  {tool_name}: {result.status} ({result.duration_seconds}s)")
                results.append(result)

    # Sort results to match tool order
    tool_order = {name: idx for idx, name in enumerate(tools)}
    results.sort(key=lambda r: tool_order.get(r.name, 999))

    # ── Write manifest ───────────────────────────────────────────────────
    manifest = {
        "schema_version": 1,
        "created_at": _utc_now_iso(),
        "bundle_root": str(bundle_root),
        "repo": {
            "repo_id": repo_id,
            "repo_path": str(repo_path),
            "is_git": True,
            "branch": branch,
            "commit": commit,
        },
        "run_id": run_id,
        "tools": [
            {
                "name": r.name,
                "status": r.status,
                "duration_seconds": r.duration_seconds,
                "output_json": r.output_json,
                "log_path": r.log_path,
            }
            for r in results
        ],
    }
    manifest_path = bundle_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # ── Write LATEST.json pointer ────────────────────────────────────────
    latest = {
        "repo_id": repo_id,
        "run_id": run_id,
        "bundle_root": str(bundle_root),
    }
    latest_path = artifacts_root / "LATEST.json"
    latest_path.write_text(json.dumps(latest, indent=2), encoding="utf-8")

    # ── Summary ──────────────────────────────────────────────────────────
    success = sum(1 for r in results if r.status == "success")
    print()
    print("Bundle ready:")
    print(f"  repo_id:  {repo_id}")
    print(f"  run_id:   {run_id}")
    print(f"  root:     {bundle_root}")
    print(f"  tools:    {success}/{len(results)} succeeded")
    print(f"  LATEST:   {latest_path}")

    return 0 if success == len(results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
