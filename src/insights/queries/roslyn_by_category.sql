-- Roslyn violations by category for Caldera
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
    'Security' AS category,
    SUM(cat_security) AS count
FROM stg_roslyn_file_metrics
WHERE run_pk = (SELECT roslyn_run_pk FROM run_map)
HAVING count > 0

UNION ALL

SELECT
    'Design' AS category,
    SUM(cat_design) AS count
FROM stg_roslyn_file_metrics
WHERE run_pk = (SELECT roslyn_run_pk FROM run_map)
HAVING count > 0

UNION ALL

SELECT
    'Resource' AS category,
    SUM(cat_resource) AS count
FROM stg_roslyn_file_metrics
WHERE run_pk = (SELECT roslyn_run_pk FROM run_map)
HAVING count > 0

UNION ALL

SELECT
    'Dead Code' AS category,
    SUM(cat_dead_code) AS count
FROM stg_roslyn_file_metrics
WHERE run_pk = (SELECT roslyn_run_pk FROM run_map)
HAVING count > 0

UNION ALL

SELECT
    'Performance' AS category,
    SUM(cat_performance) AS count
FROM stg_roslyn_file_metrics
WHERE run_pk = (SELECT roslyn_run_pk FROM run_map)
HAVING count > 0

ORDER BY count DESC
