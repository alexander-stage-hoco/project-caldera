-- Staging model for per-target trivy metrics
-- Aggregates vulnerability counts by target from lz_trivy_targets

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
    -- Severity weighted score: CRITICAL=10, HIGH=5, MEDIUM=2, LOW=1
    (t.critical_count * 10 + t.high_count * 5 + t.medium_count * 2 + t.low_count * 1) as severity_weighted_score,
    r.collection_run_id,
    r.repo_id,
    r.run_id,
    r.branch,
    r.commit
from {{ source('lz', 'lz_trivy_targets') }} t
join {{ source('lz', 'lz_tool_runs') }} r
    on t.run_pk = r.run_pk
