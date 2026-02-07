with unified as (
    select *
    from {{ ref('unified_file_metrics') }}
),
run_meta as (
    select
        run_pk,
        collection_run_id,
        repo_id,
        run_id
    from {{ source('lz', 'lz_tool_runs') }}
)
select
    u.run_pk,
    rm.collection_run_id,
    rm.repo_id,
    rm.run_id,
    count(*) as total_files,
    sum(u.loc_total) as total_loc,
    sum(u.loc_code) as total_code,
    sum(u.loc_comment) as total_comment,
    sum(u.loc_blank) as total_blank,
    sum(u.complexity_total_ccn) as total_ccn,
    avg(u.complexity_avg) as avg_ccn,
    max(u.complexity_max) as max_ccn,
    avg(u.nloc) as avg_nloc,
    sum(case when u.loc_total is not null then 1 else 0 end) as scc_file_count,
    sum(case when u.complexity_total_ccn is not null then 1 else 0 end) as lizard_file_count,
    -- Coverage metrics (dotCover)
    sum(u.coverage_covered_statements) as total_covered_statements,
    sum(u.coverage_total_statements) as total_statements,
    case
        when sum(u.coverage_total_statements) > 0
        then round(100.0 * sum(u.coverage_covered_statements) / sum(u.coverage_total_statements), 2)
        else null
    end as overall_coverage_pct,
    sum(u.coverage_type_count) as total_types_covered,
    sum(case when u.dotcover_run_pk is not null then 1 else 0 end) as dotcover_file_count
from unified u
left join run_meta rm
    on rm.run_pk = u.run_pk
group by
    u.run_pk,
    rm.collection_run_id,
    rm.repo_id,
    rm.run_id
