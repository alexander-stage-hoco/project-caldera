-- Repository health summary combining git-sizer metrics with file-level aggregates
-- Note: git-sizer provides repo-level health grades; this joins with file metrics

with git_sizer as (
    select *
    from {{ ref('stg_lz_git_sizer_metrics') }}
),

violations as (
    select
        run_pk,
        count(*) as violation_count,
        max(level) as max_violation_level
    from {{ ref('stg_lz_git_sizer_violations') }}
    group by run_pk
),

lfs_candidates as (
    select
        run_pk,
        count(*) as lfs_candidate_count
    from {{ ref('stg_lz_git_sizer_lfs_candidates') }}
    group by run_pk
),

run_summary as (
    select *
    from {{ ref('unified_run_summary') }}
)

select
    gs.run_pk,
    gs.collection_run_id,
    gs.repo_id,
    gs.run_id,
    gs.branch,
    gs.commit,
    -- Health assessment
    gs.health_grade,
    coalesce(v.violation_count, 0) as violation_count,
    coalesce(v.max_violation_level, 0) as max_violation_level,
    coalesce(lfs.lfs_candidate_count, 0) as lfs_candidate_count,
    -- Repository structure metrics (commits)
    gs.commit_count,
    gs.commit_total_size,
    gs.max_commit_size,
    gs.max_history_depth,
    gs.max_parent_count,
    -- Repository structure metrics (trees)
    gs.tree_count,
    gs.tree_total_size,
    gs.tree_total_entries,
    gs.max_tree_entries,
    -- Repository structure metrics (blobs)
    gs.blob_count,
    gs.blob_total_size,
    gs.max_blob_size,
    -- Repository structure metrics (tags/refs)
    gs.tag_count,
    gs.max_tag_depth,
    gs.reference_count,
    gs.branch_count,
    -- Path metrics
    gs.max_path_depth,
    gs.max_path_length,
    -- Expanded checkout metrics
    gs.expanded_tree_count,
    gs.expanded_blob_count,
    gs.expanded_blob_size,
    -- File-level context (from other tools)
    rs.total_files,
    rs.total_loc,
    rs.total_code,
    rs.total_ccn,
    rs.avg_ccn,
    rs.max_ccn
from git_sizer gs
left join violations v on gs.run_pk = v.run_pk
left join lfs_candidates lfs on gs.run_pk = lfs.run_pk
left join run_summary rs on gs.collection_run_id = rs.collection_run_id
