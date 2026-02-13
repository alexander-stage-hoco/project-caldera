-- Git-sizer repository health summary for Caldera
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
    health_grade,
    violation_count,
    lfs_candidate_count,
    commit_count,
    blob_count,
    blob_total_size,
    max_blob_size,
    tree_count,
    max_tree_entries,
    max_path_depth,
    max_path_length,
    branch_count,
    tag_count,
    expanded_blob_size
FROM repo_health_summary
WHERE run_pk = (SELECT git_sizer_run_pk FROM run_map)
