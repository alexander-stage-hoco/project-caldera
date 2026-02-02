-- Code smell distribution statistics for Caldera
-- Aggregates from rollup_semgrep_directory_recursive_distributions

SELECT
    'smells' AS metric,
    SUM(value_count) AS total_files,
    AVG(value_count) AS avg_per_directory
FROM rollup_semgrep_directory_recursive_distributions
WHERE run_pk = {{ run_pk }}
  AND metric = 'smell_count'
