-- Code smell distribution statistics for Caldera
-- Resolves semgrep run_pk from any tool's collection

WITH run_map AS (
    SELECT tr_tool.run_pk AS semgrep_run_pk
    FROM lz_tool_runs tr_source
    LEFT JOIN lz_tool_runs tr_tool
        ON tr_tool.collection_run_id = tr_source.collection_run_id
        AND tr_tool.tool_name = 'semgrep'
    WHERE tr_source.run_pk = {{ run_pk }}
)
SELECT
    'smells' AS metric,
    SUM(value_count) AS total_files,
    AVG(value_count) AS avg_per_directory
FROM rollup_semgrep_directory_recursive_distributions
WHERE run_pk = (SELECT semgrep_run_pk FROM run_map)
  AND metric = 'smell_count'
