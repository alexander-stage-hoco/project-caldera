#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_git_repo(repo_path: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(repo_path), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def _git_branch(repo_path: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_path), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else "main"


def _git_commit(repo_path: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else "0" * 40


def _stable_repo_id_from_path(repo_path: Path) -> str:
    resolved = str(repo_path.resolve())
    digest = hashlib.sha1(resolved.encode(), usedforsecurity=False).hexdigest()[:10]
    return f"{repo_path.resolve().name}-{digest}"


def _find_tools(tools_root: Path) -> list[str]:
    tools: list[str] = []
    for entry in sorted(tools_root.iterdir()):
        if not entry.is_dir():
            continue
        if (entry / "Makefile").exists():
            tools.append(entry.name)
    return tools


@dataclass(frozen=True)
class ToolResult:
    name: str
    status: str
    duration_seconds: float
    output_json: str | None
    log_path: str | None


def _run_tool(
    tool_root: Path,
    tool_name: str,
    *,
    repo_path: Path,
    repo_id: str,
    run_id: str,
    branch: str,
    commit: str,
    bundle_root: Path,
) -> ToolResult:
    output_dir = bundle_root / tool_name / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "execution.log"

    env = os.environ.copy()
    env.update(
        {
            "REPO_PATH": str(repo_path),
            "REPO_NAME": repo_id,
            "RUN_ID": run_id,
            "REPO_ID": repo_id,
            "BRANCH": branch,
            "OUTPUT_DIR": str(output_dir),
            # Always export COMMIT (all-zeros sentinel for non-git repos) to avoid
            # Makefile fallbacks to the Caldera repo's git SHA.
            "COMMIT": commit,
        }
    )

    start = time.perf_counter()
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.run(
            ["make", "analyze"],
            cwd=str(tool_root),
            env=env,
            stdout=log,
            stderr=log,
            check=False,
        )
    duration = time.perf_counter() - start

    output_json_path = output_dir / "output.json"
    output_json_rel = (
        str(output_json_path.relative_to(bundle_root)) if output_json_path.exists() else None
    )

    return ToolResult(
        name=tool_name,
        status="success" if proc.returncode == 0 and output_json_rel else "failed",
        duration_seconds=round(duration, 3),
        output_json=output_json_rel,
        log_path=str(log_path.relative_to(bundle_root)),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect Caldera tool artifacts only (no DuckDB/dbt).")
    parser.add_argument("--repo-path", required=True)
    parser.add_argument("--output-dir", default="artifacts", help="Directory to write bundles into")
    parser.add_argument("--tools-root", default="src/tools")
    parser.add_argument("--skip-tools", default="", help="Comma-separated tool names to skip")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--repo-id", default=None)
    parser.add_argument("--tar", action="store_true", help="Also produce a .tar.gz bundle")
    args = parser.parse_args()

    repo_path = Path(args.repo_path).resolve()
    tools_root = Path(args.tools_root).resolve()
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    run_id = args.run_id or str(uuid.uuid4())
    repo_id = args.repo_id or _stable_repo_id_from_path(repo_path)

    is_git = _is_git_repo(repo_path)
    branch = _git_branch(repo_path) if is_git else "main"
    commit = _git_commit(repo_path) if is_git else ("0" * 40)

    skip = {t.strip() for t in args.skip_tools.split(",") if t.strip()}
    tools = [t for t in _find_tools(tools_root) if t not in skip]

    bundle_root = out_dir / repo_id / run_id
    if bundle_root.exists():
        shutil.rmtree(bundle_root)
    bundle_root.mkdir(parents=True, exist_ok=True)

    results: list[ToolResult] = []
    for idx, tool_name in enumerate(tools, 1):
        print(f"[{idx}/{len(tools)}] {tool_name}")
        tool_root = tools_root / tool_name
        results.append(
            _run_tool(
                tool_root,
                tool_name,
                repo_path=repo_path,
                repo_id=repo_id,
                run_id=run_id,
                branch=branch,
                commit=commit,
                bundle_root=bundle_root,
            )
        )

    manifest = {
        "schema_version": 1,
        "created_at": _utc_now_iso(),
        "bundle_root": str(bundle_root),
        "repo": {
            "repo_id": repo_id,
            "repo_path": str(repo_path),
            "is_git": is_git,
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

    tar_path: Path | None = None
    if args.tar:
        tar_path = bundle_root.with_suffix(".tar.gz")
        with tarfile.open(tar_path, "w:gz") as tf:
            tf.add(bundle_root, arcname=bundle_root.name)

    success = sum(1 for r in results if r.status == "success")
    print("")
    print("Bundle ready:")
    print(f"  repo_id: {repo_id}")
    print(f"  run_id:  {run_id}")
    print(f"  root:    {bundle_root}")
    print(f"  tools:   {success}/{len(results)} succeeded")
    if tar_path:
        print(f"  tar:     {tar_path}")

    return 0 if success == len(results) else 2


if __name__ == "__main__":
    raise SystemExit(main())

