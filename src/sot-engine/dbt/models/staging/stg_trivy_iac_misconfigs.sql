-- Staging model for lz_trivy_iac_misconfigs
-- Joins with tool runs to get collection context

select
    m.run_pk,
    m.file_id,
    m.directory_id,
    m.relative_path,
    m.misconfig_id,
    m.severity,
    m.title,
    m.description,
    m.resolution,
    m.target_type,
    m.start_line,
    m.end_line,
    r.collection_run_id,
    r.repo_id,
    r.run_id,
    r.branch,
    r.commit
from {{ source('lz', 'lz_trivy_iac_misconfigs') }} m
join {{ source('lz', 'lz_tool_runs') }} r
    on m.run_pk = r.run_pk
