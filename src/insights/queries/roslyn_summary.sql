-- Roslyn violations summary by severity for Caldera
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
    'Critical' AS severity,
    SUM(severity_critical) AS count
FROM stg_roslyn_file_metrics
WHERE run_pk = (SELECT roslyn_run_pk FROM run_map)
HAVING count > 0

UNION ALL

SELECT
    'High' AS severity,
    SUM(severity_high) AS count
FROM stg_roslyn_file_metrics
WHERE run_pk = (SELECT roslyn_run_pk FROM run_map)
HAVING count > 0

UNION ALL

SELECT
    'Medium' AS severity,
    SUM(severity_medium) AS count
FROM stg_roslyn_file_metrics
WHERE run_pk = (SELECT roslyn_run_pk FROM run_map)
HAVING count > 0

UNION ALL

SELECT
    'Low' AS severity,
    SUM(severity_low) AS count
FROM stg_roslyn_file_metrics
WHERE run_pk = (SELECT roslyn_run_pk FROM run_map)
HAVING count > 0

UNION ALL

SELECT
    'Info' AS severity,
    SUM(severity_info) AS count
FROM stg_roslyn_file_metrics
WHERE run_pk = (SELECT roslyn_run_pk FROM run_map)
HAVING count > 0

ORDER BY
    CASE severity
        WHEN 'Critical' THEN 1
        WHEN 'High' THEN 2
        WHEN 'Medium' THEN 3
        WHEN 'Low' THEN 4
        WHEN 'Info' THEN 5
    END
