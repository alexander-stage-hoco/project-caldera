-- Directory hotspots by complexity for Caldera
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
    rl.directory_path,
    rl.file_count,
    rl.total_nloc AS total_lines,
    rl.total_ccn,
    CASE WHEN rl.file_count > 0 THEN rl.total_ccn::FLOAT / rl.file_count ELSE 0 END AS avg_ccn,
    rl.total_function_count AS total_functions
FROM rollup_lizard_directory_counts_recursive rl
WHERE rl.run_pk = (SELECT lizard_run_pk FROM run_map)
  AND rl.total_ccn > 0
ORDER BY rl.total_ccn DESC
LIMIT {{ limit | default(15) }}
