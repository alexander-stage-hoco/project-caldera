-- Complexity distribution statistics for Caldera
-- Resolves lizard run_pk from any tool's collection

WITH run_map AS (
    SELECT tr_tool.run_pk AS lizard_run_pk
    FROM lz_tool_runs tr_source
    LEFT JOIN lz_tool_runs tr_tool
        ON tr_tool.collection_run_id = tr_source.collection_run_id
        AND tr_tool.tool_name = 'lizard'
    WHERE tr_source.run_pk = {{ run_pk }}
)
SELECT
    'complexity' AS metric,
    SUM(value_count) AS total_files,
    AVG(value_count) AS avg_per_directory
FROM rollup_lizard_directory_recursive_distributions
WHERE run_pk = (SELECT lizard_run_pk FROM run_map)
  AND metric = 'total_ccn'
