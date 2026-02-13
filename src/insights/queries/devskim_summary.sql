-- DevSkim security findings summary for Caldera
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
    COUNT(*) AS total_files,
    SUM(issue_count) AS total_issues,
    SUM(severity_critical) AS severity_critical,
    SUM(severity_high) AS severity_high,
    SUM(severity_medium) AS severity_medium,
    SUM(severity_low) AS severity_low
FROM stg_devskim_file_metrics
WHERE run_pk = (SELECT devskim_run_pk FROM run_map)
