-- Evidence: dependency health issues from dependensee / trivy data
-- Vulnerable or outdated dependencies

SELECT
    tv.relative_path,
    tv.finding_id,
    tv.package_name,
    tv.installed_version,
    tv.fixed_version,
    tv.severity,
    tv.description,
    tv.tool_run_pk,
    'trivy' AS tool_source
FROM (
    SELECT
        stv.relative_path,
        stv.vulnerability_id AS finding_id,
        stv.pkg_name AS package_name,
        stv.installed_version,
        stv.fixed_version,
        stv.severity,
        stv.title AS description,
        stv.run_pk AS tool_run_pk
    FROM stg_trivy_vulnerabilities stv
    JOIN lz_tool_runs tr ON tr.run_pk = stv.run_pk AND tr.tool_name = 'trivy'
    WHERE tr.collection_run_id = (
        SELECT collection_run_id FROM lz_tool_runs WHERE run_pk = {{ run_pk }}
    )
      AND stv.severity IN ('CRITICAL', 'HIGH')
) tv
ORDER BY
    CASE tv.severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 ELSE 3 END,
    tv.package_name
LIMIT {{ limit | default(50) }}
