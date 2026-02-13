-- Summary of gitleaks secrets by severity
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
    severity,
    COUNT(*) AS count,
    COUNT(DISTINCT fingerprint) AS unique_count,
    SUM(CASE WHEN in_current_head THEN 1 ELSE 0 END) AS in_head_count
FROM stg_lz_gitleaks_secrets
WHERE run_pk = (SELECT gitleaks_run_pk FROM run_map)
GROUP BY severity
ORDER BY
    CASE severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'LOW' THEN 4
        ELSE 5
    END
