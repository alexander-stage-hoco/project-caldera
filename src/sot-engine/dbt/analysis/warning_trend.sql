{% set repo_id = var('repo_id') %}
{% set limit_rows = var('limit', 20) %}

-- Warning trend across collection runs for a repository
-- Shows warning counts by category per run to detect escalating issues

with repo_runs as (
    select
        cr.collection_run_id,
        cr.repo_id,
        cr.commit,
        cr.started_at,
        row_number() over (order by cr.started_at desc) as run_rank
    from {{ source('lz', 'lz_collection_runs') }} cr
    where cr.repo_id = '{{ repo_id }}'
      and cr.status = 'completed'
),

warning_counts as (
    select
        w.collection_run_id,
        count(*) as total_warnings,
        count(case when w.category = 'expected_missing' then 1 end) as cnt_expected_missing,
        count(case when w.category = 'regression' then 1 end) as cnt_regression,
        count(case when w.category = 'degraded' then 1 end) as cnt_degraded
    from {{ ref('stg_warnings') }} w
    join repo_runs rr on rr.collection_run_id = w.collection_run_id
    group by w.collection_run_id
),

quality_summary as (
    select
        collection_run_id,
        budget_passed
    from {{ source('lz', 'lz_run_quality_summary') }}
)

select
    rr.collection_run_id,
    rr.repo_id,
    rr.commit as run_id,
    rr.started_at,
    coalesce(wc.cnt_expected_missing, 0) as cnt_expected_missing,
    coalesce(wc.cnt_regression, 0) as cnt_regression,
    coalesce(wc.cnt_degraded, 0) as cnt_degraded,
    coalesce(wc.total_warnings, 0) as total_warnings,
    coalesce(qs.budget_passed, true) as budget_passed
from repo_runs rr
left join warning_counts wc on wc.collection_run_id = rr.collection_run_id
left join quality_summary qs on qs.collection_run_id = rr.collection_run_id
order by rr.started_at desc
limit {{ limit_rows }}
