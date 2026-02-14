"""Shared helpers for dbt pipeline E2E tests."""

from __future__ import annotations

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
SOT_ENGINE_DIR = Path(__file__).resolve().parents[1]
FIXTURES_DIR = SOT_ENGINE_DIR / "persistence" / "fixtures"
SCHEMA_PATH = SOT_ENGINE_DIR / "persistence" / "schema.sql"
DBT_PROJECT_DIR = SOT_ENGINE_DIR / "dbt"

# ---------------------------------------------------------------------------
# Fixture manifest: (filename, ingest_param_name)
# Order matters: layout must be first (other tools depend on it).
# ---------------------------------------------------------------------------
ALL_TOOL_FIXTURES: list[tuple[str, str]] = [
    ("layout_output.json", "layout_output"),
    ("scc_output.json", "scc_output"),
    ("lizard_output.json", "lizard_output"),
    ("roslyn_output.json", "roslyn_output"),
    ("semgrep_output.json", "semgrep_output"),
    ("sonarqube_output.json", "sonarqube_output"),
    ("trivy_output.json", "trivy_output"),
    ("gitleaks_output.json", "gitleaks_output"),
    ("symbol_scanner_output.json", "symbol_scanner_output"),
    ("scancode_output.json", "scancode_output"),
    ("pmd_cpd_output.json", "pmd_cpd_output"),
    ("devskim_output.json", "devskim_output"),
    ("dotcover_output.json", "dotcover_output"),
    ("git_fame_output.json", "git_fame_output"),
    ("git_sizer_output.json", "git_sizer_output"),
    ("git_blame_scanner_output.json", "git_blame_scanner_output"),
    ("dependensee_output.json", "dependensee_output"),
    ("coverage_output.json", "coverage_output"),
]

# Candidate locations for the dbt binary (most-specific first).
_DBT_BIN_CANDIDATES = [
    SOT_ENGINE_DIR / ".venv-dbt" / "bin" / "dbt",
    Path("/usr/local/bin/dbt"),
]


def find_dbt_binary() -> Path | None:
    """Return the first existing dbt binary, or *None*."""
    for candidate in _DBT_BIN_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def load_all_fixtures(
    tmp_dir: Path,
    repo_id: str,
    run_id: str,
    commit: str,
) -> dict[str, Path]:
    """Load all 18 fixtures, rewrite metadata, write to *tmp_dir*.

    Returns a mapping ``{ingest_param_name: Path}`` ready for
    ``ingest_outputs()``.
    """
    result: dict[str, Path] = {}
    for fixture_file, param_name in ALL_TOOL_FIXTURES:
        src = FIXTURES_DIR / fixture_file
        payload = json.loads(src.read_text())

        # Rewrite metadata for consistency
        meta = payload.get("metadata", {})
        meta["repo_id"] = repo_id
        meta["run_id"] = run_id
        meta["commit"] = commit
        payload["metadata"] = meta

        # Lizard has an extra run_id in the data section
        if fixture_file == "lizard_output.json":
            payload["data"]["run_id"] = run_id

        dest = tmp_dir / fixture_file
        dest.write_text(json.dumps(payload))
        result[param_name] = dest
    return result


def write_dbt_profile(tmp_path: Path, db_path: Path) -> Path:
    """Write a ``profiles.yml`` pointing at *db_path* and return the
    directory containing it (suitable for ``--profiles-dir``)."""
    profile_path = tmp_path / "profiles.yml"
    profile_path.write_text(
        "\n".join(
            [
                "caldera_sot:",
                "  target: dev",
                "  outputs:",
                "    dev:",
                "      type: duckdb",
                f"      path: {db_path}",
                "      threads: 2",
                "",
            ]
        )
    )
    return profile_path.parent
