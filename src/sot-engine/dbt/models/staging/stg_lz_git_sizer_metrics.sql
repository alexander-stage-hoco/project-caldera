-- Staging model for lz_git_sizer_metrics
-- Repository-level health metrics from git-sizer
-- Note: git-sizer provides repo-level metrics, not file-level

select
    m.run_pk,
    m.repo_id,
    m.health_grade,
    m.duration_ms,
    -- Commit metrics
    m.commit_count,
    m.commit_total_size,
    m.max_commit_size,
    m.max_history_depth,
    m.max_parent_count,
    -- Tree metrics
    m.tree_count,
    m.tree_total_size,
    m.tree_total_entries,
    m.max_tree_entries,
    -- Blob metrics
    m.blob_count,
    m.blob_total_size,
    m.max_blob_size,
    -- Tag metrics
    m.tag_count,
    m.max_tag_depth,
    -- Reference metrics
    m.reference_count,
    m.branch_count,
    -- Path metrics
    m.max_path_depth,
    m.max_path_length,
    -- Expanded checkout metrics
    m.expanded_tree_count,
    m.expanded_blob_count,
    m.expanded_blob_size,
    -- Context from tool run
    r.collection_run_id,
    r.run_id,
    r.branch,
    r.commit
from {{ source('lz', 'lz_git_sizer_metrics') }} m
join {{ source('lz', 'lz_tool_runs') }} r
    on m.run_pk = r.run_pk
