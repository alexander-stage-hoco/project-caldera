-- Staging model for git-fame summary metrics
-- Repository-level authorship metrics from git-fame

select
    s.run_pk,
    s.repo_id,
    s.author_count,
    s.total_loc,
    s.hhi_index,
    s.bus_factor,
    s.top_author_pct,
    s.top_two_pct,
    -- Context from tool run
    r.collection_run_id,
    r.run_id,
    r.branch,
    r.commit
from {{ source('lz', 'lz_git_fame_summary') }} s
join {{ source('lz', 'lz_tool_runs') }} r
    on s.run_pk = r.run_pk
