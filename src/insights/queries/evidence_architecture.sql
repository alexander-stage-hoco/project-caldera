-- Evidence: directory structure issues from layout-scanner data
-- Directories with high file counts or excessive depth

WITH dir_stats AS (
    SELECT
        directory_path,
        COUNT(*) AS file_count,
        LENGTH(directory_path) - LENGTH(REPLACE(directory_path, '/', '')) AS depth
    FROM lz_layout_files lf
    JOIN lz_tool_runs tr ON tr.run_pk = lf.run_pk AND tr.tool_name = 'layout-scanner'
    WHERE tr.collection_run_id = (
        SELECT collection_run_id FROM lz_tool_runs WHERE run_pk = {{ run_pk }}
    )
    GROUP BY directory_path
)
SELECT
    directory_path,
    file_count,
    depth
FROM dir_stats
WHERE file_count >= {{ min_files | default(20) }}
   OR depth >= {{ min_depth | default(6) }}
ORDER BY file_count DESC
LIMIT {{ limit | default(50) }}
