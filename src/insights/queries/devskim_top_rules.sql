-- Top DevSkim rules by severity score for Caldera
-- Resolves devskim run_pk from any tool's collection

WITH run_map AS (
    SELECT tr_tool.run_pk AS devskim_run_pk
    FROM lz_tool_runs tr_source
    LEFT JOIN lz_tool_runs tr_tool
        ON tr_tool.collection_run_id = tr_source.collection_run_id
        AND tr_tool.tool_name = 'devskim'
    WHERE tr_source.run_pk = {{ run_pk }}
)
SELECT
    rule_id,
    dd_category,
    sample_message,
    issue_count,
    files_affected,
    severity_score,
    risk_level
FROM mart_devskim_rule_hotspots
WHERE run_pk = (SELECT devskim_run_pk FROM run_map)
ORDER BY severity_score DESC
LIMIT {{ limit | default(20) }}
