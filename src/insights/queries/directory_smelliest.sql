-- Directory ranking by code smells for Caldera
-- Uses pre-computed rollup_semgrep_directory_recursive_counts

SELECT
    rsg.directory_path,
    rsg.total_smell_count AS smell_count,
    rsg.file_count AS files_with_smells
FROM rollup_semgrep_directory_counts_recursive rsg
WHERE rsg.run_pk = {{ run_pk }}
  AND rsg.total_smell_count > 0
ORDER BY rsg.total_smell_count DESC
LIMIT {{ limit | default(15) }}
