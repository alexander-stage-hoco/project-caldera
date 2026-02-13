-- Files with IaC misconfigurations for Caldera
-- Resolves trivy run_pk from any tool's collection

WITH run_map AS (
    SELECT tr_tool.run_pk AS trivy_run_pk
    FROM lz_tool_runs tr_source
    LEFT JOIN lz_tool_runs tr_tool
        ON tr_tool.collection_run_id = tr_source.collection_run_id
        AND tr_tool.tool_name = 'trivy'
    WHERE tr_source.run_pk = {{ run_pk }}
)
SELECT
    target_key AS file_path,
    type AS iac_type,
    COUNT(*) AS misconfig_count,
    SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) AS critical_count,
    SUM(CASE WHEN severity = 'HIGH' THEN 1 ELSE 0 END) AS high_count,
    SUM(CASE WHEN severity = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_count
FROM stg_trivy_iac_misconfigs
WHERE run_pk = (SELECT trivy_run_pk FROM run_map)
GROUP BY target_key, type
ORDER BY critical_count DESC, high_count DESC, misconfig_count DESC
LIMIT {{ limit | default(15) }}
