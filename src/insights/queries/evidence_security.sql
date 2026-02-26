-- Evidence: security findings
-- Finds critical/high CVEs from trivy + secrets from gitleaks
-- Used by EvidenceCollector to populate security evidence items

WITH run_map AS (
    SELECT
        tr_trivy.run_pk AS trivy_run_pk,
        tr_gitleaks.run_pk AS gitleaks_run_pk
    FROM lz_tool_runs tr_scc
    LEFT JOIN lz_tool_runs tr_trivy
        ON tr_trivy.collection_run_id = tr_scc.collection_run_id
        AND tr_trivy.tool_name = 'trivy'
    LEFT JOIN lz_tool_runs tr_gitleaks
        ON tr_gitleaks.collection_run_id = tr_scc.collection_run_id
        AND tr_gitleaks.tool_name = 'gitleaks'
    WHERE tr_scc.run_pk = {{ run_pk }}
),
trivy_findings AS (
    SELECT
        'cve' AS finding_type,
        COALESCE(tv.relative_path, tv.package_name) AS location,
        tv.vulnerability_id AS finding_id,
        tv.severity,
        tv.title AS description,
        tv.package_name,
        tv.installed_version,
        tv.fixed_version,
        (SELECT trivy_run_pk FROM run_map) AS tool_run_pk
    FROM stg_trivy_vulnerabilities tv
    WHERE tv.run_pk = (SELECT trivy_run_pk FROM run_map)
      AND tv.severity IN ('CRITICAL', 'HIGH')
    ORDER BY
        CASE tv.severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 END,
        tv.vulnerability_id
    LIMIT {{ limit | default(50) }}
),
gitleaks_findings AS (
    SELECT
        'secret' AS finding_type,
        gs.relative_path AS location,
        gs.rule_id AS finding_id,
        'CRITICAL' AS severity,
        gs.description,
        NULL AS package_name,
        NULL AS installed_version,
        NULL AS fixed_version,
        (SELECT gitleaks_run_pk FROM run_map) AS tool_run_pk
    FROM stg_lz_gitleaks_secrets gs
    WHERE gs.run_pk = (SELECT gitleaks_run_pk FROM run_map)
    LIMIT {{ limit | default(50) }}
)
SELECT * FROM trivy_findings
UNION ALL
SELECT * FROM gitleaks_findings
