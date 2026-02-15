#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import duckdb


def _load_manifest(bundle_root: Path) -> dict:
    manifest_path = bundle_root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest.json not found in bundle: {bundle_root}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _resolve_bundle_root(bundle: Path) -> Path:
    if bundle.is_dir():
        return bundle
    if bundle.suffixes[-2:] == [".tar", ".gz"] or bundle.suffix == ".tgz":
        tmp_dir = Path(tempfile.mkdtemp(prefix="caldera-bundle-"))
        subprocess.run(["tar", "-xzf", str(bundle), "-C", str(tmp_dir)], check=True)
        children = [p for p in tmp_dir.iterdir() if p.is_dir()]
        if len(children) != 1:
            raise RuntimeError(f"Expected 1 directory in extracted bundle, found {len(children)}")
        return children[0]
    raise ValueError(f"Unsupported bundle path: {bundle}")


def _get_run_pk(db_path: Path, run_id: str) -> int:
    conn = duckdb.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT run_pk FROM lz_tool_runs WHERE run_id = ? ORDER BY run_pk DESC LIMIT 1",
            [run_id],
        ).fetchone()
        if not row:
            raise RuntimeError(f"run_id not found in DB: {run_id}")
        return int(row[0])
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest a Caldera artifacts bundle and generate report.")
    parser.add_argument("--repo-path", required=True, help="Path to the repo that was analyzed")
    parser.add_argument("--bundle", required=True, help="Bundle directory or .tar.gz created by collect")
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--schema-path", default="src/sot-engine/persistence/schema.sql")
    parser.add_argument("--report-out", required=True)
    parser.add_argument("--llm", type=int, default=0, help="1 to run LLM eval + top3, 0 to skip")
    args = parser.parse_args()

    repo_path = Path(args.repo_path).resolve()
    bundle_path = Path(args.bundle).resolve()
    db_path = Path(args.db_path).expanduser().resolve()
    report_out = Path(args.report_out).resolve()
    report_out.parent.mkdir(parents=True, exist_ok=True)

    extracted_tmp: Path | None = None
    bundle_root = _resolve_bundle_root(bundle_path)
    if bundle_root.parent.name.startswith("caldera-bundle-"):
        extracted_tmp = bundle_root.parent

    manifest = _load_manifest(bundle_root)
    repo = manifest.get("repo", {})
    run_id = manifest["run_id"]
    repo_id = repo["repo_id"]
    branch = repo.get("branch", "main")
    commit = repo.get("commit", "0" * 40)

    try:
        subprocess.run(
            [
                ".venv/bin/python",
                "src/sot-engine/orchestrator.py",
                "--repo-path",
                str(repo_path),
                "--repo-id",
                str(repo_id),
                "--run-id",
                str(run_id),
                "--branch",
                str(branch),
                "--commit",
                str(commit),
                "--db-path",
                str(db_path),
                "--schema-path",
                str(args.schema_path),
                "--output-root",
                str(bundle_root),
                "--run-dbt",
                "--no-progress",
            ],
            check=True,
        )

        run_pk = _get_run_pk(db_path, run_id)

        # Generate report
        subprocess.run(
            [
                ".venv/bin/python",
                "-m",
                "insights",
                "generate",
                str(run_pk),
                "--db",
                str(db_path),
                "--format",
                "html",
                "--output",
                str(report_out),
            ],
            cwd="src/insights",
            check=True,
        )

        if int(args.llm) == 1:
            eval_out = report_out.parent / "evaluation.json"
            top3_out = report_out.parent / "top3_insights.json"
            subprocess.run(
                [
                    ".venv/bin/python",
                    "-m",
                    "insights.scripts.evaluate",
                    "evaluate",
                    str(report_out),
                    "--db",
                    str(db_path),
                    "--run-pk",
                    str(run_pk),
                    "--include-insight-quality",
                    "--output",
                    str(eval_out),
                ],
                cwd="src/insights",
                check=True,
            )
            subprocess.run(
                [
                    ".venv/bin/python",
                    "-m",
                    "insights.scripts.extract_top_insights",
                    "extract",
                    str(eval_out),
                    "--output",
                    str(top3_out),
                    "--format",
                    "rich",
                ],
                cwd="src/insights",
                check=True,
            )

        print(f"Report: {report_out}")
        return 0
    finally:
        if extracted_tmp and extracted_tmp.exists():
            shutil.rmtree(extracted_tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

