-- Staging model for lz_git_sizer_lfs_candidates
-- Files recommended for Git LFS migration

select
    c.run_pk,
    c.file_path,
    r.collection_run_id,
    r.repo_id,
    r.run_id,
    r.branch,
    r.commit
from {{ source('lz', 'lz_git_sizer_lfs_candidates') }} c
join {{ source('lz', 'lz_tool_runs') }} r
    on c.run_pk = r.run_pk
