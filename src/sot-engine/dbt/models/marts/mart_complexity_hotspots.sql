-- Function-level complexity hotspots
-- Identifies high-CCN functions as refactoring candidates using McCabe/NIST thresholds
-- Risk levels: low (1-10), medium (11-20), high (21-50), critical (51+)

with lizard_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'lizard'
),
layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
run_mapping as (
    select
        lr.run_pk as lizard_run_pk,
        lr.collection_run_id,
        lyr.run_pk as layout_run_pk
    from lizard_runs lr
    join layout_runs lyr on lyr.collection_run_id = lr.collection_run_id
),
function_metrics as (
    select
        rm.lizard_run_pk,
        rm.collection_run_id,
        rm.layout_run_pk,
        fm.file_id,
        fm.function_name,
        fm.long_name,
        fm.ccn,
        fm.nloc,
        fm.params,
        fm.token_count,
        fm.line_start,
        fm.line_end,
        (fm.line_end - fm.line_start + 1) as line_span
    from {{ source('lz', 'lz_lizard_function_metrics') }} fm
    join run_mapping rm on rm.lizard_run_pk = fm.run_pk
),
run_stats as (
    select
        collection_run_id,
        percentile_cont(0.50) within group (order by ccn) as ccn_p50,
        percentile_cont(0.75) within group (order by ccn) as ccn_p75,
        percentile_cont(0.90) within group (order by ccn) as ccn_p90,
        percentile_cont(0.95) within group (order by ccn) as ccn_p95,
        percentile_cont(0.99) within group (order by ccn) as ccn_p99,
        avg(ccn) as ccn_avg,
        stddev(ccn) as ccn_stddev,
        count(*) as total_functions
    from function_metrics
    group by collection_run_id
),
enriched_functions as (
    select
        fm.lizard_run_pk as run_pk,
        fm.collection_run_id,
        fm.layout_run_pk,
        fm.file_id,
        lf.relative_path,
        lf.directory_id,
        fm.function_name,
        fm.long_name,
        fm.ccn,
        fm.nloc,
        fm.params,
        fm.token_count,
        fm.line_start,
        fm.line_end,
        fm.line_span,
        case when fm.nloc > 0 then round(fm.ccn::double / fm.nloc, 4) else null end as complexity_density,
        rs.ccn_avg, rs.ccn_stddev, rs.ccn_p50, rs.ccn_p75, rs.ccn_p90, rs.ccn_p95, rs.ccn_p99, rs.total_functions,
        case
            when fm.ccn > 50 then 'critical'
            when fm.ccn > 20 then 'high'
            when fm.ccn > 10 then 'medium'
            else 'low'
        end as risk_level,
        case
            when fm.ccn > 50 then 4 when fm.ccn > 20 then 3 when fm.ccn > 10 then 2 else 1
        end as risk_level_numeric,
        case
            when fm.ccn >= rs.ccn_p99 then 'p99_outlier'
            when fm.ccn >= rs.ccn_p95 then 'p95_outlier'
            when fm.ccn >= rs.ccn_p90 then 'p90_outlier'
            when fm.ccn >= rs.ccn_p75 then 'above_median'
            else 'normal'
        end as relative_position,
        case when rs.ccn_stddev > 0 then round((fm.ccn - rs.ccn_avg) / rs.ccn_stddev, 2) else 0 end as ccn_zscore,
        fm.ccn > 10 as is_medium_plus,
        fm.ccn > 20 as is_high_plus,
        fm.ccn > 50 as is_critical
    from function_metrics fm
    join {{ source('lz', 'lz_layout_files') }} lf
        on lf.run_pk = fm.layout_run_pk and lf.file_id = fm.file_id
    join run_stats rs on rs.collection_run_id = fm.collection_run_id
)
select
    run_pk,
    collection_run_id,
    file_id,
    relative_path,
    directory_id,
    function_name,
    long_name,
    ccn,
    nloc,
    params,
    token_count,
    line_start,
    line_end,
    line_span,
    complexity_density,
    risk_level,
    risk_level_numeric,
    relative_position,
    ccn_zscore,
    is_medium_plus,
    is_high_plus,
    is_critical,
    ccn_avg as run_ccn_avg,
    ccn_stddev as run_ccn_stddev,
    ccn_p50 as run_ccn_p50,
    ccn_p75 as run_ccn_p75,
    ccn_p90 as run_ccn_p90,
    ccn_p95 as run_ccn_p95,
    ccn_p99 as run_ccn_p99,
    total_functions as run_total_functions
from enriched_functions
where ccn > 10 or ccn_zscore > 2.0
order by collection_run_id, ccn desc
