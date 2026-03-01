{% set repo_id = var('repo_id') %}
{% set limit_rows = var('limit', 20) %}

-- Per-tool data quality score trend across collection runs
-- Shows which tools' data quality is improving or degrading over time

with repo_runs as (
    select
        cr.collection_run_id,
        cr.repo_id,
        cr.created_at as started_at,
        row_number() over (order by cr.created_at desc) as run_rank
    from {{ source('lz', 'lz_collection_runs') }} cr
    where cr.repo_id = '{{ repo_id }}'
      and cr.status = 'completed'
),

tool_scores as (
    select
        qc.collection_run_id,
        qc.tool_name,
        count(*) as checks_total,
        count(case when qc.passed then 1 end) as checks_passed,
        count(case when not qc.passed then 1 end) as checks_failed,
        min(qc.overall_score) as quality_score
    from {{ ref('stg_quality_checks') }} qc
    join repo_runs rr on rr.collection_run_id = qc.collection_run_id
    group by qc.collection_run_id, qc.tool_name
)

select
    rr.collection_run_id,
    rr.repo_id,
    rr.started_at,
    ts.tool_name,
    ts.checks_total,
    ts.checks_passed,
    ts.checks_failed,
    ts.quality_score
from repo_runs rr
join tool_scores ts on ts.collection_run_id = rr.collection_run_id
order by rr.started_at desc, ts.tool_name
limit {{ limit_rows }}
