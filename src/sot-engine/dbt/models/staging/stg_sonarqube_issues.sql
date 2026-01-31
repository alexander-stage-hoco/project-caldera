-- Staging model for lz_sonarqube_issues
-- Joins with tool runs to get collection context

select
    i.run_pk,
    i.file_id,
    i.directory_id,
    i.relative_path,
    i.issue_key,
    i.rule_id,
    i.issue_type,
    i.severity,
    i.message,
    i.line_start,
    i.line_end,
    i.effort,
    i.status,
    i.tags,
    r.collection_run_id,
    r.repo_id,
    r.run_id,
    r.branch,
    r.commit
from {{ source('lz', 'lz_sonarqube_issues') }} i
join {{ source('lz', 'lz_tool_runs') }} r
    on i.run_pk = r.run_pk
