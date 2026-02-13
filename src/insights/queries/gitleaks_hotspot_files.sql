-- Files with most secret findings
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
    relative_path,
    secret_count,
    severity_critical,
    severity_high,
    secrets_in_head,
    unique_rule_count
FROM stg_gitleaks_secrets
WHERE run_pk = (SELECT gitleaks_run_pk FROM run_map)
ORDER BY severity_critical DESC, severity_high DESC, secret_count DESC
LIMIT {{ limit | default(10) }}
