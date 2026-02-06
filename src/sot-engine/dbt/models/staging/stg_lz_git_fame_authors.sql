-- Staging model for git-fame author metrics
-- git-fame provides author-level metrics (not file-level)
-- Note: This view is named for consistency but contains author data

select
    a.run_pk,
    a.author_name,
    a.author_email,
    a.surviving_loc,
    a.ownership_pct,
    a.insertions_total,
    a.deletions_total,
    a.commit_count,
    a.files_touched,
    -- Context from tool run
    r.collection_run_id,
    r.run_id,
    r.repo_id,
    r.branch,
    r.commit
from {{ source('lz', 'lz_git_fame_authors') }} a
join {{ source('lz', 'lz_tool_runs') }} r
    on a.run_pk = r.run_pk
