-- Secrets grouped by rule/type
-- Resolves gitleaks run_pk from any tool's collection

WITH run_map AS (
    SELECT tr_tool.run_pk AS gitleaks_run_pk
    FROM lz_tool_runs tr_source
    LEFT JOIN lz_tool_runs tr_tool
        ON tr_tool.collection_run_id = tr_source.collection_run_id
        AND tr_tool.tool_name = 'gitleaks'
    WHERE tr_source.run_pk = {{ run_pk }}
)
SELECT
    rule_id,
    secret_type,
    COUNT(*) AS count,
    COUNT(DISTINCT relative_path) AS file_count,
    MAX(severity) AS max_severity
FROM stg_lz_gitleaks_secrets
WHERE run_pk = (SELECT gitleaks_run_pk FROM run_map)
GROUP BY rule_id, secret_type
ORDER BY count DESC
LIMIT {{ limit | default(15) }}
