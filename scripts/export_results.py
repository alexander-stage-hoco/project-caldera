#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
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


def _sha256_file(path: Path) -> str:
    """
    Compute the SHA-256 hex digest of a file's contents.
    
    Returns:
        str: Hex-encoded SHA-256 digest of the file contents.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _generate_checksums(dest: Path) -> dict[str, str]:
    """
    Create SHA-256 checksums for all regular files under the given destination directory, excluding a file named `checksums.json`.
    
    Parameters:
        dest (Path): Root directory to walk; returned keys are file paths relative to this directory.
    
    Returns:
        dict[str, str]: Mapping from each file's relative path to its SHA-256 hex digest.
    """
    checksums: dict[str, str] = {}
    for file_path in sorted(dest.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.name == "checksums.json":
            continue
        rel = str(file_path.relative_to(dest))
        checksums[rel] = _sha256_file(file_path)
    return checksums


def _export_evidence(db_path: Path, collection_run_id: str, dest: Path) -> bool:
    """
    Export evidence tables from a DuckDB file into a single evidence.json in the destination directory.
    
    Attempts to read the lz_evidence, lz_claims, and lz_risks tables filtered by collection_run_id and writes a JSON object with those table arrays to dest/evidence.json when any table contains data. If the duckdb package is not available, if the database cannot be read, or if no rows are found in any table, nothing is written.
    
    Parameters:
        db_path (Path): Path to the DuckDB database file to read.
        collection_run_id (str): Collection run identifier used to filter rows in each table.
        dest (Path): Directory where evidence.json will be written.
    
    Returns:
        bool: `True` if evidence.json was written (at least one table contained data), `False` otherwise.
    """
    try:
        import duckdb
    except ImportError:
        print("  Warning: duckdb not available, skipping evidence export", file=sys.stderr)
        return False

    try:
        conn = duckdb.connect(str(db_path), read_only=True)
        evidence_data: dict[str, list[dict]] = {}

        for table in ("lz_evidence", "lz_claims", "lz_risks"):
            try:
                rows = conn.execute(
                    f"SELECT * FROM {table} WHERE collection_run_id = ?",
                    [collection_run_id],
                ).fetchdf()
                evidence_data[table] = json.loads(rows.to_json(orient="records", date_format="iso"))
            except Exception:
                evidence_data[table] = []

        conn.close()

        if any(evidence_data.values()):
            evidence_path = dest / "evidence.json"
            evidence_path.write_text(
                json.dumps(evidence_data, indent=2, default=str),
                encoding="utf-8",
            )
            return True
    except Exception as exc:
        print(f"  Warning: evidence export failed: {exc}", file=sys.stderr)

    return False


def main() -> int:
    """
    Export a pipeline run into a git-based results repository, optionally committing and pushing the export.
    
    Reads run_manifest.json from the provided run directory and the specified DuckDB file, validates identifiers, copies selected artifacts (manifest, report, DuckDB, optional evaluation/top3_insights, optional tool outputs, optional dbt artifacts, and optional exported evidence) into runs/<repo_id>/<run_id> in the target results repository (local or cloned remote). Generates checksums.json, rebuilds the repository index.json, stages and commits changes, and optionally pushes the commit to the remote. Exits non-zero on missing inputs, git repository errors, or push failures.
    
    @returns:
        `0` on success; `1` on error (validation failure, git/repository error, or push failure).
    """
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
    parser.add_argument(
        "--include-tool-outputs",
        action="store_true",
        default=False,
        help="Copy raw tool output.json files into the export directory",
    )
    parser.add_argument(
        "--include-dbt-artifacts",
        action="store_true",
        default=True,
        help="Include dbt manifest.json and run_results.json (default: on)",
    )
    parser.add_argument(
        "--no-dbt-artifacts",
        action="store_false",
        dest="include_dbt_artifacts",
        help="Skip dbt artifact inclusion",
    )
    parser.add_argument(
        "--include-evidence",
        action="store_true",
        default=False,
        help="Export lz_evidence/lz_claims/lz_risks as evidence.json",
    )
    parser.add_argument(
        "--artifacts-dir",
        default=None,
        help="Path to artifacts directory (default: artifacts/ in project root)",
    )
    parser.add_argument(
        "--dbt-target-dir",
        default=None,
        help="Path to dbt target directory (default: ~/.caldera/dbt_target)",
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
    collection_run_id = cr.get("collection_run_id", run_id)

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

    # Copy raw tool outputs if requested
    tool_outputs_included = False
    if args.include_tool_outputs:
        artifacts_root = (
            Path(args.artifacts_dir).resolve()
            if args.artifacts_dir
            else Path(__file__).resolve().parents[1] / "artifacts"
        )
        tool_output_src = artifacts_root / repo_id / run_id
        if tool_output_src.is_dir():
            tool_output_dest = dest / "tool_outputs"
            tool_count = 0
            for tool_dir in sorted(tool_output_src.iterdir()):
                if not tool_dir.is_dir():
                    continue
                output_json = tool_dir / "output.json"
                if output_json.exists():
                    target = tool_output_dest / tool_dir.name
                    target.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(output_json, target / "output.json")
                    tool_count += 1
            if tool_count > 0:
                tool_outputs_included = True
                copied_files.append(f"tool_outputs/ ({tool_count} tools)")
                print(f"  Included {tool_count} tool output files")
        else:
            print(f"  Warning: artifacts directory not found: {tool_output_src}")

    # Copy dbt artifacts if requested
    dbt_artifacts_included = False
    if args.include_dbt_artifacts:
        dbt_target_dir = (
            Path(args.dbt_target_dir).expanduser()
            if args.dbt_target_dir
            else Path("~/.caldera/dbt_target").expanduser()
        )
        dbt_dest = dest / "dbt"
        for artifact_name in ("manifest.json", "run_results.json"):
            src = dbt_target_dir / artifact_name
            if src.exists():
                dbt_dest.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dbt_dest / artifact_name)
                if not dbt_artifacts_included:
                    dbt_artifacts_included = True
                    copied_files.append("dbt/")
                print(f"  Included dbt {artifact_name}")
        if not dbt_artifacts_included:
            print(f"  Warning: dbt artifacts not found in {dbt_target_dir}")

    # Export evidence from DuckDB if requested
    evidence_included = False
    if args.include_evidence:
        evidence_included = _export_evidence(db_path, collection_run_id, dest)
        if evidence_included:
            copied_files.append("evidence.json")
            print("  Included evidence.json")

    # Generate checksums for tamper detection (must be last, after all copies)
    checksums = _generate_checksums(dest)
    checksums_path = dest / "checksums.json"
    checksums_path.write_text(
        json.dumps(checksums, indent=2) + "\n", encoding="utf-8",
    )
    copied_files.append("checksums.json")

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
    print(f"  dbt:       {'included' if dbt_artifacts_included else 'not found'}")
    print(f"  Evidence:  {'included' if evidence_included else 'not requested' if not args.include_evidence else 'empty'}")
    print(f"  Checksums: {len(checksums)} files hashed")
    print(f"  Commit:    {commit_sha}")
    print(f"  Pushed:    {'yes' if args.push else 'no'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
