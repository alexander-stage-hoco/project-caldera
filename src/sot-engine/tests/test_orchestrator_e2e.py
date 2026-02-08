from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orchestrator import OrchestratorLogger, ingest_outputs, run_dbt
from persistence.entities import CollectionRun
from persistence.repositories import CollectionRunRepository


def _load_schema(conn: duckdb.DuckDBPyConnection) -> None:
    schema_path = Path(__file__).resolve().parents[1] / "persistence" / "schema.sql"
    conn.execute(schema_path.read_text())


def _write_profile(tmp_path: Path, db_path: Path) -> Path:
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


def test_orchestrator_end_to_end(tmp_path: Path) -> None:  # noqa: PLR0915
    dbt_bin = Path(
        "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/sot-engine/.venv-dbt/bin/dbt"
    )
    if not dbt_bin.exists():
        pytest.skip("dbt binary not available for e2e test")

    repo_root = tmp_path / "repo"
    (repo_root / "src" / "utils").mkdir(parents=True)
    (repo_root / "src" / "app.py").write_text("print('hi')\n")
    (repo_root / "src" / "utils" / "helpers.py").write_text("def helper():\n    pass\n")

    db_path = tmp_path / "caldera_sot.duckdb"
    conn = duckdb.connect(str(db_path))
    _load_schema(conn)

    # Load all 16 tool fixtures
    fixtures_dir = Path(__file__).resolve().parents[1] / "persistence" / "fixtures"
    layout_fixture = fixtures_dir / "layout_output.json"
    scc_fixture = fixtures_dir / "scc_output.json"
    lizard_fixture = fixtures_dir / "lizard_output.json"
    semgrep_fixture = fixtures_dir / "semgrep_output.json"
    sonarqube_fixture = fixtures_dir / "sonarqube_output.json"
    trivy_fixture = fixtures_dir / "trivy_output.json"
    gitleaks_fixture = fixtures_dir / "gitleaks_output.json"
    git_fame_fixture = fixtures_dir / "git_fame_output.json"
    dotcover_fixture = fixtures_dir / "dotcover_output.json"
    dependensee_fixture = fixtures_dir / "dependensee_output.json"
    git_sizer_fixture = fixtures_dir / "git_sizer_output.json"
    roslyn_fixture = fixtures_dir / "roslyn_output.json"
    symbol_scanner_fixture = fixtures_dir / "symbol_scanner_output.json"
    scancode_fixture = fixtures_dir / "scancode_output.json"
    pmd_cpd_fixture = fixtures_dir / "pmd_cpd_output.json"
    devskim_fixture = fixtures_dir / "devskim_output.json"

    # Load all payloads
    layout_payload = json.loads(layout_fixture.read_text())
    scc_payload = json.loads(scc_fixture.read_text())
    lizard_payload = json.loads(lizard_fixture.read_text())
    semgrep_payload = json.loads(semgrep_fixture.read_text())
    sonarqube_payload = json.loads(sonarqube_fixture.read_text())
    trivy_payload = json.loads(trivy_fixture.read_text())
    gitleaks_payload = json.loads(gitleaks_fixture.read_text())
    git_fame_payload = json.loads(git_fame_fixture.read_text())
    dotcover_payload = json.loads(dotcover_fixture.read_text())
    dependensee_payload = json.loads(dependensee_fixture.read_text())
    git_sizer_payload = json.loads(git_sizer_fixture.read_text())
    roslyn_payload = json.loads(roslyn_fixture.read_text())
    symbol_scanner_payload = json.loads(symbol_scanner_fixture.read_text())
    scancode_payload = json.loads(scancode_fixture.read_text())
    pmd_cpd_payload = json.loads(pmd_cpd_fixture.read_text())
    devskim_payload = json.loads(devskim_fixture.read_text())

    # Use consistent repo_id and run_id across all payloads
    repo_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    run_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    # Rewrite metadata for all tools (standard envelope format)
    all_payloads = [
        layout_payload, scc_payload, lizard_payload, semgrep_payload,
        sonarqube_payload, trivy_payload, gitleaks_payload, git_fame_payload,
        dotcover_payload, dependensee_payload, git_sizer_payload, roslyn_payload,
        symbol_scanner_payload, scancode_payload, pmd_cpd_payload, devskim_payload,
    ]
    for payload in all_payloads:
        payload["metadata"]["repo_id"] = repo_id
        payload["metadata"]["run_id"] = run_id

    # Lizard has additional run_id in data section
    lizard_payload["data"]["run_id"] = run_id

    # Write all fixtures to temp path
    layout_path = tmp_path / "layout.json"
    scc_path = tmp_path / "scc.json"
    lizard_path = tmp_path / "lizard.json"
    semgrep_path = tmp_path / "semgrep.json"
    sonarqube_path = tmp_path / "sonarqube.json"
    trivy_path = tmp_path / "trivy.json"
    gitleaks_path = tmp_path / "gitleaks.json"
    git_fame_path = tmp_path / "git_fame.json"
    dotcover_path = tmp_path / "dotcover.json"
    dependensee_path = tmp_path / "dependensee.json"
    git_sizer_path = tmp_path / "git_sizer.json"
    roslyn_path = tmp_path / "roslyn.json"
    symbol_scanner_path = tmp_path / "symbol_scanner.json"
    scancode_path = tmp_path / "scancode.json"
    pmd_cpd_path = tmp_path / "pmd_cpd.json"
    devskim_path = tmp_path / "devskim.json"

    layout_path.write_text(json.dumps(layout_payload))
    scc_path.write_text(json.dumps(scc_payload))
    lizard_path.write_text(json.dumps(lizard_payload))
    semgrep_path.write_text(json.dumps(semgrep_payload))
    sonarqube_path.write_text(json.dumps(sonarqube_payload))
    trivy_path.write_text(json.dumps(trivy_payload))
    gitleaks_path.write_text(json.dumps(gitleaks_payload))
    git_fame_path.write_text(json.dumps(git_fame_payload))
    dotcover_path.write_text(json.dumps(dotcover_payload))
    dependensee_path.write_text(json.dumps(dependensee_payload))
    git_sizer_path.write_text(json.dumps(git_sizer_payload))
    roslyn_path.write_text(json.dumps(roslyn_payload))
    symbol_scanner_path.write_text(json.dumps(symbol_scanner_payload))
    scancode_path.write_text(json.dumps(scancode_payload))
    pmd_cpd_path.write_text(json.dumps(pmd_cpd_payload))
    devskim_path.write_text(json.dumps(devskim_payload))

    # Create collection run record (required for FK relationship tests)
    collection_repo = CollectionRunRepository(conn)
    collection_run = CollectionRun(
        collection_run_id=run_id,
        repo_id=repo_id,
        run_id=run_id,
        branch="main",
        commit="a" * 40,
        started_at=datetime.now(timezone.utc),
        completed_at=None,
        status="running",
    )
    collection_repo.insert(collection_run)

    ingest_outputs(
        conn,
        repo_id=repo_id,
        collection_run_id=run_id,
        run_id=run_id,
        branch="main",
        commit="a" * 40,
        repo_path=repo_root,
        layout_output=layout_path,
        scc_output=scc_path,
        lizard_output=lizard_path,
        roslyn_output=roslyn_path,
        semgrep_output=semgrep_path,
        sonarqube_output=sonarqube_path,
        trivy_output=trivy_path,
        gitleaks_output=gitleaks_path,
        symbol_scanner_output=symbol_scanner_path,
        scancode_output=scancode_path,
        pmd_cpd_output=pmd_cpd_path,
        devskim_output=devskim_path,
        dotcover_output=dotcover_path,
        git_fame_output=git_fame_path,
        dependensee_output=dependensee_path,
        git_sizer_output=git_sizer_path,
        schema_path=Path(__file__).resolve().parents[1] / "persistence" / "schema.sql",
    )
    conn.close()

    profiles_dir = _write_profile(tmp_path, db_path)
    logger = OrchestratorLogger(tmp_path / "orchestrator.log")
    try:
        run_dbt(
            dbt_bin=dbt_bin,
            dbt_project_dir=Path(
                "/Users/alexander.stage/Projects/2026-01-24-Project-Caldera/src/sot-engine/dbt"
            ),
            profiles_dir=profiles_dir,
            logger=logger,
            target_path=str(tmp_path / "dbt_target"),
            log_path=str(tmp_path / "dbt_logs"),
        )
    finally:
        logger.close()

    conn = duckdb.connect(str(db_path))

    # ========== Original 6 tool assertions ==========

    rows = conn.execute(
        "SELECT count(*) FROM rollup_scc_directory_recursive_distributions"
    ).fetchone()[0]
    assert rows > 0

    # Verify semgrep smells were inserted
    semgrep_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_semgrep_smells"
    ).fetchone()[0]
    assert semgrep_rows == 2  # Fixture has 2 smells

    # Verify file_id join with layout works
    semgrep_join_rows = conn.execute(
        """
        SELECT ss.relative_path, lf.relative_path
        FROM lz_semgrep_smells ss
        JOIN lz_tool_runs tr_semgrep
          ON tr_semgrep.run_pk = ss.run_pk
        JOIN lz_tool_runs tr_layout
          ON tr_layout.collection_run_id = tr_semgrep.collection_run_id
         AND tr_layout.tool_name IN ('layout', 'layout-scanner')
        JOIN lz_layout_files lf
          ON lf.run_pk = tr_layout.run_pk
         AND lf.file_id = ss.file_id
        ORDER BY ss.relative_path
        """
    ).fetchall()
    assert semgrep_join_rows == [
        ("src/app.py", "src/app.py"),
        ("src/utils/helpers.py", "src/utils/helpers.py"),
    ]

    # Verify SonarQube issues were inserted
    sonarqube_issue_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_sonarqube_issues"
    ).fetchone()[0]
    assert sonarqube_issue_rows == 3  # Fixture has 3 issues

    # Verify SonarQube metrics were inserted
    sonarqube_metric_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_sonarqube_metrics"
    ).fetchone()[0]
    assert sonarqube_metric_rows == 2  # Fixture has 2 file metrics

    # Verify SonarQube file_id join with layout works
    sonarqube_join_rows = conn.execute(
        """
        SELECT si.relative_path, lf.relative_path, si.issue_type, si.severity
        FROM lz_sonarqube_issues si
        JOIN lz_tool_runs tr_sonarqube
          ON tr_sonarqube.run_pk = si.run_pk
        JOIN lz_tool_runs tr_layout
          ON tr_layout.collection_run_id = tr_sonarqube.collection_run_id
         AND tr_layout.tool_name IN ('layout', 'layout-scanner')
        JOIN lz_layout_files lf
          ON lf.run_pk = tr_layout.run_pk
         AND lf.file_id = si.file_id
        ORDER BY si.issue_key
        """
    ).fetchall()
    assert len(sonarqube_join_rows) == 3
    assert sonarqube_join_rows[0] == ("src/app.py", "src/app.py", "BUG", "MAJOR")
    assert sonarqube_join_rows[1] == (
        "src/utils/helpers.py", "src/utils/helpers.py", "VULNERABILITY", "CRITICAL"
    )
    assert sonarqube_join_rows[2] == ("src/app.py", "src/app.py", "CODE_SMELL", "MINOR")

    # Verify Trivy vulnerabilities were inserted
    trivy_vuln_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_trivy_vulnerabilities"
    ).fetchone()[0]
    assert trivy_vuln_rows == 4  # Fixture has 4 vulnerabilities

    # Verify Trivy targets were inserted
    trivy_target_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_trivy_targets"
    ).fetchone()[0]
    assert trivy_target_rows == 2  # Fixture has 2 targets

    # Verify Trivy IaC misconfigs were inserted
    trivy_iac_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_trivy_iac_misconfigs"
    ).fetchone()[0]
    assert trivy_iac_rows == 2  # Fixture has 2 IaC misconfigs

    # Verify Trivy target file_id join with layout works
    trivy_target_join_rows = conn.execute(
        """
        SELECT t.relative_path, lf.relative_path, t.target_type, t.vulnerability_count
        FROM lz_trivy_targets t
        JOIN lz_tool_runs tr_trivy
          ON tr_trivy.run_pk = t.run_pk
        JOIN lz_tool_runs tr_layout
          ON tr_layout.collection_run_id = tr_trivy.collection_run_id
         AND tr_layout.tool_name IN ('layout', 'layout-scanner')
        JOIN lz_layout_files lf
          ON lf.run_pk = tr_layout.run_pk
         AND lf.file_id = t.file_id
        ORDER BY t.relative_path
        """
    ).fetchall()
    assert len(trivy_target_join_rows) == 2
    assert trivy_target_join_rows[0] == (
        "package-lock.json", "package-lock.json", "npm", 3
    )
    assert trivy_target_join_rows[1] == ("requirements.txt", "requirements.txt", "pip", 1)

    # Verify Trivy IaC misconfig file_id join with layout works
    trivy_iac_join_rows = conn.execute(
        """
        SELECT m.relative_path, lf.relative_path, m.misconfig_id, m.severity
        FROM lz_trivy_iac_misconfigs m
        JOIN lz_tool_runs tr_trivy ON tr_trivy.run_pk = m.run_pk
        JOIN lz_tool_runs tr_layout
          ON tr_layout.collection_run_id = tr_trivy.collection_run_id
         AND tr_layout.tool_name IN ('layout', 'layout-scanner')
        JOIN lz_layout_files lf
          ON lf.run_pk = tr_layout.run_pk AND lf.file_id = m.file_id
        ORDER BY m.misconfig_id
        """
    ).fetchall()
    assert len(trivy_iac_join_rows) == 2
    assert trivy_iac_join_rows[0] == ("Dockerfile", "Dockerfile", "AVD-DS-0001", "HIGH")
    assert trivy_iac_join_rows[1] == ("Dockerfile", "Dockerfile", "AVD-DS-0002", "MEDIUM")

    recursive_count = conn.execute(
        """
        select value_count
        from rollup_scc_directory_recursive_distributions
        where directory_path = 'src' and metric = 'lines_total'
        """
    ).fetchone()
    direct_count = conn.execute(
        """
        select value_count
        from rollup_scc_directory_direct_distributions
        where directory_path = 'src' and metric = 'lines_total'
        """
    ).fetchone()
    assert recursive_count is not None
    assert direct_count is not None
    assert recursive_count[0] > direct_count[0]

    # Verify Trivy rollup models exist and have data
    trivy_rollup_direct_rows = conn.execute(
        "SELECT COUNT(*) FROM rollup_trivy_directory_counts_direct"
    ).fetchone()[0]
    assert trivy_rollup_direct_rows > 0, "Trivy direct rollup should have data"

    trivy_rollup_recursive_rows = conn.execute(
        "SELECT COUNT(*) FROM rollup_trivy_directory_counts_recursive"
    ).fetchone()[0]
    assert trivy_rollup_recursive_rows > 0, "Trivy recursive rollup should have data"

    # Verify Trivy rollup counts are correct for root directory
    trivy_recursive_root = conn.execute(
        """
        SELECT total_vulnerability_count, total_iac_misconfig_count,
               vuln_critical_count, vuln_high_count, vuln_medium_count, vuln_low_count,
               iac_critical_count, iac_high_count, iac_medium_count, iac_low_count
        FROM rollup_trivy_directory_counts_recursive
        WHERE directory_path = '.'
        """
    ).fetchone()
    assert trivy_recursive_root is not None, "Trivy recursive rollup should have root"
    # Fixture has 4 vulnerabilities total: 1 CRITICAL, 2 HIGH, 1 MEDIUM (across 2 targets)
    assert trivy_recursive_root[0] == 4
    # Fixture has 2 IaC misconfigs: 1 HIGH, 1 MEDIUM
    assert trivy_recursive_root[1] == 2

    # ========== New tool assertions (10 additional tools) ==========

    # Gitleaks assertions
    gitleaks_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_gitleaks_secrets"
    ).fetchone()[0]
    assert gitleaks_rows == 2

    # Git-fame assertions
    git_fame_author_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_git_fame_authors"
    ).fetchone()[0]
    assert git_fame_author_rows == 2

    git_fame_summary_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_git_fame_summary"
    ).fetchone()[0]
    assert git_fame_summary_rows == 1

    # Dotcover assertions
    dotcover_assembly_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_dotcover_assembly_coverage"
    ).fetchone()[0]
    assert dotcover_assembly_rows == 2

    dotcover_type_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_dotcover_type_coverage"
    ).fetchone()[0]
    assert dotcover_type_rows == 3

    dotcover_method_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_dotcover_method_coverage"
    ).fetchone()[0]
    assert dotcover_method_rows == 5

    # Dependensee assertions
    dependensee_project_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_dependensee_projects"
    ).fetchone()[0]
    assert dependensee_project_rows == 2

    dependensee_project_ref_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_dependensee_project_refs"
    ).fetchone()[0]
    assert dependensee_project_ref_rows == 1

    dependensee_package_ref_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_dependensee_package_refs"
    ).fetchone()[0]
    assert dependensee_package_ref_rows == 3

    # Git-sizer assertions
    git_sizer_metric_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_git_sizer_metrics"
    ).fetchone()[0]
    assert git_sizer_metric_rows == 1

    git_sizer_violation_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_git_sizer_violations"
    ).fetchone()[0]
    assert git_sizer_violation_rows == 1

    # Roslyn assertions
    roslyn_violation_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_roslyn_violations"
    ).fetchone()[0]
    assert roslyn_violation_rows == 3

    # Symbol-scanner assertions
    symbol_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_code_symbols"
    ).fetchone()[0]
    assert symbol_rows == 5

    symbol_call_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_symbol_calls"
    ).fetchone()[0]
    assert symbol_call_rows == 5

    file_import_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_file_imports"
    ).fetchone()[0]
    assert file_import_rows == 4

    # Scancode assertions
    scancode_license_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_scancode_file_licenses"
    ).fetchone()[0]
    assert scancode_license_rows == 2

    # PMD-CPD assertions
    pmd_cpd_file_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_pmd_cpd_file_metrics"
    ).fetchone()[0]
    assert pmd_cpd_file_rows == 3

    pmd_cpd_dup_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_pmd_cpd_duplications"
    ).fetchone()[0]
    assert pmd_cpd_dup_rows == 2

    # DevSkim assertions
    devskim_finding_rows = conn.execute(
        "SELECT COUNT(*) FROM lz_devskim_findings"
    ).fetchone()[0]
    assert devskim_finding_rows == 3

    # ========== unified_file_metrics assertions ==========

    # Verify row count (files with scc OR lizard data)
    unified_rows = conn.execute(
        "SELECT COUNT(*) FROM unified_file_metrics"
    ).fetchone()[0]
    assert unified_rows > 0, "unified_file_metrics should have rows"

    # Verify all run_pk references are valid
    run_pk_orphans = conn.execute(
        """
        SELECT COUNT(*) FROM unified_file_metrics ufm
        WHERE NOT EXISTS (
            SELECT 1 FROM lz_tool_runs tr WHERE tr.run_pk = ufm.run_pk
        )
        """
    ).fetchone()[0]
    assert run_pk_orphans == 0

    # Verify core metrics populated (from scc)
    core_metrics = conn.execute(
        """
        SELECT relative_path, loc_total, complexity_max
        FROM unified_file_metrics
        WHERE loc_total IS NOT NULL
        """
    ).fetchall()
    assert len(core_metrics) > 0, "Should have files with loc_total populated"

    # Verify file_id references are valid (join to layout via layout_run_pk and file_id)
    file_id_orphans = conn.execute(
        """
        SELECT COUNT(*) FROM unified_file_metrics ufm
        LEFT JOIN lz_layout_files lf
            ON lf.run_pk = ufm.layout_run_pk
           AND lf.file_id = ufm.file_id
        WHERE lf.file_id IS NULL
        """
    ).fetchone()[0]
    assert file_id_orphans == 0

    conn.close()
