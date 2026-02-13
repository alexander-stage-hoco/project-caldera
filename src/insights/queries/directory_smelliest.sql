-- Directory ranking by code smells for Caldera
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
    rsg.directory_path,
    rsg.total_smell_count AS smell_count,
    rsg.file_count AS files_with_smells
FROM rollup_semgrep_directory_counts_recursive rsg
WHERE rsg.run_pk = (SELECT semgrep_run_pk FROM run_map)
  AND rsg.total_smell_count > 0
ORDER BY rsg.total_smell_count DESC
LIMIT {{ limit | default(15) }}
