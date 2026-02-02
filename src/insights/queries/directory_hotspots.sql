-- Directory hotspots by complexity for Caldera
-- Uses pre-computed rollup_lizard_directory_recursive_counts

SELECT
    rl.directory_path,
    rl.file_count,
    rl.total_nloc AS total_lines,
    rl.total_ccn,
    CASE WHEN rl.file_count > 0 THEN rl.total_ccn::FLOAT / rl.file_count ELSE 0 END AS avg_ccn,
    rl.total_function_count AS total_functions
FROM rollup_lizard_directory_counts_recursive rl
WHERE rl.run_pk = {{ run_pk }}
  AND rl.total_ccn > 0
ORDER BY rl.total_ccn DESC
LIMIT {{ limit | default(15) }}
