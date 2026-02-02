-- Complexity distribution statistics for Caldera
-- Aggregates from rollup_lizard_directory_recursive_distributions

SELECT
    'complexity' AS metric,
    SUM(value_count) AS total_files,
    AVG(value_count) AS avg_per_directory
FROM rollup_lizard_directory_recursive_distributions
WHERE run_pk = {{ run_pk }}
  AND metric = 'total_ccn'
