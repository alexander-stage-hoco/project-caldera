-- Files with most DevSkim findings for Caldera
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
    relative_path,
    issue_count,
    severity_critical,
    severity_high,
    severity_medium
FROM stg_devskim_file_metrics
WHERE run_pk = (SELECT devskim_run_pk FROM run_map)
  AND issue_count > 0
ORDER BY severity_critical DESC, severity_high DESC, issue_count DESC
LIMIT {{ limit | default(15) }}
