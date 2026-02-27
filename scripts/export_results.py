#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from common.identifier_validation import validate_safe_identifier

# Ensure sibling scripts are importable
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_results_index import build_index


def _run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def _is_local_path(repo: str) -> bool:
    return not repo.startswith("http://") and not repo.startswith("https://") and not repo.startswith("git@")


def _ensure_lfs(repo_dir: Path) -> None:
    """Initialize Git LFS and add *.duckdb tracking if not already configured."""
    gitattributes = repo_dir / ".gitattributes"
    needs_tracking = True
    if gitattributes.exists():
        content = gitattributes.read_text(encoding="utf-8")
        if "*.duckdb" in content:
            needs_tracking = False

    if needs_tracking:
        _run(["git", "lfs", "install"], cwd=repo_dir)
        _run(["git", "lfs", "track", "*.duckdb"], cwd=repo_dir)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export a pipeline run to a git results repository."
    )
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Pipeline run directory containing run_manifest.json",
    )
    parser.add_argument(
        "--db",
        required=True,
        help="Path to DuckDB file to include in export",
    )
    parser.add_argument(
        "--results-repo",
        required=True,
        help="Git URL or local path to the results repository",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        default=False,
        help="Push the commit to the remote after committing",
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Branch to use in the results repo (default: main)",
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    db_path = Path(args.db).expanduser().resolve()

    # Validate inputs
    manifest_path = run_dir / "run_manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: run_manifest.json not found in {run_dir}", file=sys.stderr)
        return 1

    if not db_path.exists():
        print(f"ERROR: DuckDB file not found: {db_path}", file=sys.stderr)
        return 1

    # Read manifest to get repo_id and run_id
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cr = manifest.get("collection_run", {})
    repo_id = cr.get("repo_id", "unknown")
    run_id = cr.get("run_id", cr.get("collection_run_id", "unknown"))
    commit = cr.get("commit", "")
    commit_short = commit[:7] if commit else "unknown"

    # Validate identifiers to prevent path traversal
    validate_safe_identifier(repo_id, "repo_id")
    validate_safe_identifier(run_id, "run_id")

    # Clone or open the results repo
    is_local = _is_local_path(args.results_repo)
    if is_local:
        results_dir = Path(args.results_repo).resolve()
        if not (results_dir / ".git").exists():
            print(f"ERROR: {results_dir} is not a git repository", file=sys.stderr)
            return 1
        tmp_dir = None
    else:
        tmp_dir = tempfile.mkdtemp(prefix="caldera-results-")
        results_dir = Path(tmp_dir)
        print(f"Cloning results repo to {results_dir}...")
        result = _run(
            ["git", "clone", "--branch", args.branch, args.results_repo, str(results_dir)],
            check=False,
        )
        if result.returncode != 0:
            # Branch might not exist yet — clone default and create it
            _run(["git", "clone", args.results_repo, str(results_dir)])
            _run(["git", "checkout", "-b", args.branch], cwd=results_dir, check=False)

    # Ensure LFS is set up for .duckdb files
    _ensure_lfs(results_dir)

    # Create the run directory in the results repo
    dest = results_dir / "runs" / repo_id / run_id
    # Safety: ensure dest is still under results_dir after resolution
    dest.resolve().relative_to(results_dir.resolve())
    dest.mkdir(parents=True, exist_ok=True)

    # Copy artifacts
    copied_files: list[str] = []

    # Always copy run_manifest.json
    shutil.copy2(manifest_path, dest / "run_manifest.json")
    copied_files.append("run_manifest.json")

    # Copy report.html if it exists
    report_src = run_dir / "report.html"
    if report_src.exists():
        shutil.copy2(report_src, dest / "report.html")
        copied_files.append("report.html")

    # Copy DuckDB
    shutil.copy2(db_path, dest / "caldera_sot.duckdb")
    copied_files.append("caldera_sot.duckdb")

    # Copy optional files
    for optional_name in ("evaluation.json", "top3_insights.json"):
        src = run_dir / optional_name
        if src.exists():
            shutil.copy2(src, dest / optional_name)
            copied_files.append(optional_name)

    print(f"Copied {len(copied_files)} files to {dest.relative_to(results_dir)}/")

    # Rebuild index.json
    index = build_index(results_dir)
    index_path = results_dir / "index.json"
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(f"Index updated: {index['total_runs']} total runs")

    # Git add + commit
    _run(["git", "add", "."], cwd=results_dir)

    # Check if there are changes to commit
    status = _run(["git", "status", "--porcelain"], cwd=results_dir)
    if not status.stdout.strip():
        print("No changes to commit (results already up to date).")
        return 0

    commit_msg = f"Add run {run_id} for {repo_id} ({commit_short})"
    _run(["git", "commit", "-m", commit_msg], cwd=results_dir)

    # Get the commit SHA
    sha_result = _run(["git", "rev-parse", "--short", "HEAD"], cwd=results_dir)
    commit_sha = sha_result.stdout.strip()

    print(f"Committed: {commit_sha} — {commit_msg}")

    # Push if requested
    if args.push:
        print("Pushing to remote...")
        push_result = _run(["git", "push"], cwd=results_dir, check=False)
        if push_result.returncode != 0:
            print(f"Push failed: {push_result.stderr}", file=sys.stderr)
            return 1
        print("Pushed successfully.")
    else:
        print("Commit only (use --push to push to remote).")

    # Summary
    print()
    print("=== Export Summary ===")
    print(f"  Repo ID:   {repo_id}")
    print(f"  Run ID:    {run_id}")
    print(f"  Files:     {', '.join(copied_files)}")
    print(f"  Commit:    {commit_sha}")
    print(f"  Pushed:    {'yes' if args.push else 'no'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
