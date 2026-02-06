-- Authorship summary: combines git-fame metrics with unified code metrics
-- Answers: "What is the authorship concentration and bus factor for this repo?"
-- Joins repo-level authorship with file-level metrics for correlation analysis

with git_fame as (
    select *
    from {{ ref('stg_lz_git_fame_summary') }}
),

run_summary as (
    select *
    from {{ ref('unified_run_summary') }}
)

select
    gf.run_pk,
    gf.collection_run_id,
    gf.repo_id,
    gf.branch,
    gf.commit,
    -- Authorship metrics
    gf.author_count,
    gf.total_loc,
    gf.hhi_index,
    gf.bus_factor,
    gf.top_author_pct,
    gf.top_two_pct,
    -- Code metrics from unified summary
    rs.total_files,
    rs.total_code,
    rs.total_ccn as total_complexity,
    rs.avg_ccn as avg_complexity,
    rs.max_ccn as max_complexity,
    -- Derived risk classifications
    case
        when gf.hhi_index >= 0.5 then 'high'
        when gf.hhi_index >= 0.25 then 'medium'
        else 'low'
    end as concentration_risk,
    case
        when gf.bus_factor <= 1 then 'critical'
        when gf.bus_factor <= 2 then 'warning'
        else 'healthy'
    end as bus_factor_risk,
    case
        when gf.top_author_pct >= 80.0 then true
        else false
    end as single_author_dominated
from git_fame gf
left join run_summary rs
    on gf.collection_run_id = rs.collection_run_id
