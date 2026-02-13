-- Top IaC misconfigurations by severity for Caldera
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
    misconfig_id,
    severity,
    title,
    type AS iac_type,
    target_key AS file_path
FROM stg_trivy_iac_misconfigs
WHERE run_pk = (SELECT trivy_run_pk FROM run_map)
ORDER BY
    CASE severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'LOW' THEN 4
        ELSE 5
    END,
    misconfig_id
LIMIT {{ limit | default(20) }}
