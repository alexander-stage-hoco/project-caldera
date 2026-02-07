-- Unified repository-level metrics combining git-sizer and git-fame
-- Single source of truth for repository health and authorship risk assessment

with git_sizer_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'git-sizer'
),

git_fame_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'git-fame'
),

violation_agg as (
    select
        v.run_pk,
        count(*) as violation_count,
        max(v.level) as max_violation_level
    from {{ ref('stg_lz_git_sizer_violations') }} v
    group by v.run_pk
),

lfs_agg as (
    select
        c.run_pk,
        count(*) as lfs_candidate_count
    from {{ ref('stg_lz_git_sizer_lfs_candidates') }} c
    group by c.run_pk
),

git_sizer_base as (
    select
        gsr.collection_run_id,
        m.run_pk as git_sizer_run_pk,
        m.health_grade,
        m.commit_count,
        m.blob_total_size,
        m.max_blob_size,
        m.branch_count,
        m.tag_count,
        m.max_path_depth,
        m.max_path_length,
        m.expanded_blob_size
    from {{ ref('stg_lz_git_sizer_metrics') }} m
    join git_sizer_runs gsr on gsr.run_pk = m.run_pk
),

git_fame_base as (
    select
        gfr.collection_run_id,
        s.run_pk as git_fame_run_pk,
        s.author_count,
        s.total_loc,
        s.hhi_index,
        s.bus_factor,
        s.top_author_pct,
        s.top_two_pct
    from {{ ref('stg_lz_git_fame_summary') }} s
    join git_fame_runs gfr on gfr.run_pk = s.run_pk
)

select
    coalesce(gs.collection_run_id, gf.collection_run_id) as collection_run_id,
    cr.repo_id,
    cr.commit,
    cr.branch,
    -- Git-Sizer Metrics
    gs.git_sizer_run_pk,
    gs.health_grade,
    gs.commit_count,
    gs.blob_total_size,
    gs.max_blob_size,
    gs.branch_count,
    gs.tag_count,
    gs.max_path_depth,
    gs.max_path_length,
    gs.expanded_blob_size,
    coalesce(va.violation_count, 0) as violation_count,
    va.max_violation_level,
    coalesce(la.lfs_candidate_count, 0) as lfs_candidate_count,
    -- Git-Fame Metrics
    gf.git_fame_run_pk,
    gf.author_count,
    gf.total_loc,
    gf.hhi_index,
    gf.bus_factor,
    gf.top_author_pct,
    gf.top_two_pct,
    -- Sources tracking
    concat_ws(
        ',',
        case when gs.git_sizer_run_pk is not null then 'git-sizer' end,
        case when gf.git_fame_run_pk is not null then 'git-fame' end
    ) as sources
from git_sizer_base gs
full outer join git_fame_base gf
    on gf.collection_run_id = gs.collection_run_id
left join violation_agg va
    on va.run_pk = gs.git_sizer_run_pk
left join lfs_agg la
    on la.run_pk = gs.git_sizer_run_pk
join {{ source('lz', 'lz_collection_runs') }} cr
    on cr.collection_run_id = coalesce(gs.collection_run_id, gf.collection_run_id)
