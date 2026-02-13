-- Git-sizer LFS candidate files for Caldera
-- Resolves git-sizer run_pk from any tool's collection

WITH run_map AS (
    SELECT tr_tool.run_pk AS git_sizer_run_pk
    FROM lz_tool_runs tr_source
    LEFT JOIN lz_tool_runs tr_tool
        ON tr_tool.collection_run_id = tr_source.collection_run_id
        AND tr_tool.tool_name = 'git-sizer'
    WHERE tr_source.run_pk = {{ run_pk }}
)
SELECT
    file_path,
    file_size_bytes
FROM stg_git_sizer_lfs_file_metrics
WHERE run_pk = (SELECT git_sizer_run_pk FROM run_map)
ORDER BY file_size_bytes DESC NULLS LAST
LIMIT {{ limit | default(20) }}
