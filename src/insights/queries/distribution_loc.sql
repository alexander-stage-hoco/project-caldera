-- Lines of code distribution statistics for Caldera
-- Aggregates from rollup_scc_directory_recursive_distributions

SELECT
    'loc' AS metric,
    SUM(value_count) AS total_files,
    AVG(value_count) AS avg_per_directory
FROM rollup_scc_directory_recursive_distributions
WHERE run_pk = {{ run_pk }}
  AND metric = 'lines_total'
