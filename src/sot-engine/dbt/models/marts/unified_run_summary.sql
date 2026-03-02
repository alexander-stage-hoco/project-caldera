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
),
quality_summary as (
    select
        collection_run_id,
        trust_score,
        warning_count,
        warnings_expected_missing,
        warnings_regression,
        warnings_degraded,
        budget_passed,
        tools_expected,
        tools_failed,
        ingestion_errors
    from {{ source('lz', 'lz_run_quality_summary') }}
),
aggregated as (
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
        case
            when sum(u.lizard_function_count) > 0
            then round(cast(sum(u.complexity_total_ccn) as double) / sum(u.lizard_function_count), 2)
            else null
        end as avg_ccn,
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
)
select
    a.*,
    qs.trust_score,
    qs.warning_count,
    qs.warnings_expected_missing,
    qs.warnings_regression,
    qs.warnings_degraded,
    qs.budget_passed,
    qs.tools_expected,
    qs.tools_failed,
    qs.ingestion_errors
from aggregated a
left join quality_summary qs
    on qs.collection_run_id = a.collection_run_id
