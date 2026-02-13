-- Files with most Roslyn violations for Caldera
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
    rfm.relative_path,
    rfm.violation_count,
    rfm.severity_critical AS critical,
    rfm.severity_high AS high,
    rfm.severity_medium AS medium,
    rfm.cat_security AS security,
    rfm.cat_design AS design,
    rfm.cat_resource AS resource,
    rfm.cat_dead_code AS dead_code,
    rfm.cat_performance AS performance
FROM stg_roslyn_file_metrics rfm
WHERE rfm.run_pk = (SELECT roslyn_run_pk FROM run_map)
  AND rfm.violation_count > 0
ORDER BY rfm.violation_count DESC
LIMIT {{ limit | default(15) }}
