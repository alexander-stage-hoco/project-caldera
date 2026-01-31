-- Staging model for lz_trivy_vulnerabilities
-- Joins with tool runs to get collection context

select
    v.run_pk,
    v.target_key,
    v.vulnerability_id,
    v.package_name,
    v.installed_version,
    v.fixed_version,
    v.severity,
    v.cvss_score,
    v.title,
    v.published_date,
    v.age_days,
    v.fix_available,
    r.collection_run_id,
    r.repo_id,
    r.run_id,
    r.branch,
    r.commit
from {{ source('lz', 'lz_trivy_vulnerabilities') }} v
join {{ source('lz', 'lz_tool_runs') }} r
    on v.run_pk = r.run_pk
