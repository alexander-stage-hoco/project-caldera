-- Run trust score: combines quality summary with collection run metadata
-- to produce a single trust signal per run.

with quality as (
    select *
    from {{ source('lz', 'lz_run_quality_summary') }}
),

runs as (
    select
        collection_run_id,
        repo_id,
        run_id,
        branch,
        commit,
        started_at,
        completed_at,
        status
    from {{ source('lz', 'lz_collection_runs') }}
)

select
    r.collection_run_id,
    r.repo_id,
    r.run_id,
    r.branch,
    r.commit,
    r.started_at,
    r.completed_at,
    r.status,
    q.tools_expected,
    q.tools_completed,
    q.tools_skipped,
    q.tools_failed,
    q.tools_empty,
    q.ingestion_errors,
    q.warning_count,
    q.trust_score,
    round(
        case when q.tools_expected > 0
            then 100.0 * q.tools_completed / q.tools_expected
            else 0
        end, 1
    ) as completeness_pct,
    case
        when q.trust_score >= 80 then 'high'
        when q.trust_score >= 50 then 'medium'
        else 'low'
    end as trust_level
from runs r
left join quality q
    on q.collection_run_id = r.collection_run_id
