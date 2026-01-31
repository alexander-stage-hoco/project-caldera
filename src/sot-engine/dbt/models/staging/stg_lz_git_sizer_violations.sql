-- Staging model for lz_git_sizer_violations
-- Threshold violations detected by git-sizer
-- Level 1-4 indicates severity (4 being most severe)

select
    v.run_pk,
    v.metric,
    v.value_display,
    v.raw_value,
    v.level,
    v.object_ref,
    r.collection_run_id,
    r.repo_id,
    r.run_id,
    r.branch,
    r.commit
from {{ source('lz', 'lz_git_sizer_violations') }} v
join {{ source('lz', 'lz_tool_runs') }} r
    on v.run_pk = r.run_pk
