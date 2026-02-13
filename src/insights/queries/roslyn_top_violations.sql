-- Top Roslyn violations by count for Caldera
-- Resolves roslyn-analyzers run_pk from any tool's collection

WITH run_map AS (
    SELECT tr_tool.run_pk AS roslyn_run_pk
    FROM lz_tool_runs tr_source
    LEFT JOIN lz_tool_runs tr_tool
        ON tr_tool.collection_run_id = tr_source.collection_run_id
        AND tr_tool.tool_name = 'roslyn-analyzers'
    WHERE tr_source.run_pk = {{ run_pk }}
)
SELECT
    rule_id,
    severity,
    category,
    COUNT(*) AS count,
    COUNT(DISTINCT file_id) AS affected_files
FROM lz_roslyn_violations
WHERE run_pk = (SELECT roslyn_run_pk FROM run_map)
GROUP BY rule_id, severity, category
ORDER BY
    CASE severity
        WHEN 'Error' THEN 1
        WHEN 'Warning' THEN 2
        WHEN 'Info' THEN 3
        ELSE 4
    END,
    count DESC
LIMIT {{ limit | default(20) }}
