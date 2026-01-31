-- Staging model for lz_trivy_targets
-- Joins with tool runs to get collection context

select
    t.run_pk,
    t.target_key,
    t.file_id,
    t.directory_id,
    t.relative_path,
    t.target_type,
    t.vulnerability_count,
    t.critical_count,
    t.high_count,
    t.medium_count,
    t.low_count,
    r.collection_run_id,
    r.repo_id,
    r.run_id,
    r.branch,
    r.commit
from {{ source('lz', 'lz_trivy_targets') }} t
join {{ source('lz', 'lz_tool_runs') }} r
    on t.run_pk = r.run_pk
