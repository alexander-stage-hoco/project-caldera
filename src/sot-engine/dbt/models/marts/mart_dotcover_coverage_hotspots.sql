-- Low-coverage file hotspots for coverage improvement prioritization
-- Risk levels: critical (<20%), high (20-40%), medium (40-60%), low (60-80%), passing (80%+)
-- Target threshold: 80% statement coverage

with file_metrics as (
    select
        run_pk,
        file_id,
        directory_id,
        relative_path,
        type_count,
        covered_statements,
        total_statements,
        statement_coverage_pct
    from {{ ref('stg_dotcover_file_metrics') }}
    where total_statements > 0
),
run_stats as (
    select
        run_pk,
        percentile_cont(0.25) within group (order by statement_coverage_pct) as coverage_p25,
        percentile_cont(0.50) within group (order by statement_coverage_pct) as coverage_p50,
        percentile_cont(0.75) within group (order by statement_coverage_pct) as coverage_p75,
        percentile_cont(0.90) within group (order by statement_coverage_pct) as coverage_p90,
        percentile_cont(0.95) within group (order by statement_coverage_pct) as coverage_p95,
        avg(statement_coverage_pct) as coverage_avg,
        stddev(statement_coverage_pct) as coverage_stddev,
        count(*) as total_files
    from file_metrics
    group by run_pk
),
enriched_files as (
    select
        fm.run_pk,
        fm.file_id,
        fm.directory_id,
        fm.relative_path,
        fm.type_count,
        fm.covered_statements,
        fm.total_statements,
        fm.statement_coverage_pct,
        -- Gap to 80% target
        case
            when fm.statement_coverage_pct >= 80.0 then 0.0
            else 80.0 - fm.statement_coverage_pct
        end as gap_to_target_pct,
        -- Statements needed to reach 80% target
        case
            when fm.statement_coverage_pct >= 80.0 then 0
            else cast(ceil(0.8 * fm.total_statements - fm.covered_statements) as integer)
        end as statements_needed_for_target,
        -- Risk level based on coverage thresholds
        case
            when fm.statement_coverage_pct < 20.0 then 'critical'
            when fm.statement_coverage_pct < 40.0 then 'high'
            when fm.statement_coverage_pct < 60.0 then 'medium'
            when fm.statement_coverage_pct < 80.0 then 'low'
            else 'passing'
        end as risk_level,
        case
            when fm.statement_coverage_pct < 20.0 then 5
            when fm.statement_coverage_pct < 40.0 then 4
            when fm.statement_coverage_pct < 60.0 then 3
            when fm.statement_coverage_pct < 80.0 then 2
            else 1
        end as risk_level_numeric,
        -- Run-level statistics for context
        rs.coverage_avg,
        rs.coverage_stddev,
        rs.coverage_p25,
        rs.coverage_p50,
        rs.coverage_p75,
        rs.coverage_p90,
        rs.coverage_p95,
        rs.total_files,
        -- Z-score (negative = below mean = worse coverage)
        case
            when rs.coverage_stddev > 0 then round((fm.statement_coverage_pct - rs.coverage_avg) / rs.coverage_stddev, 2)
            else 0
        end as coverage_zscore,
        -- Relative position (low coverage = outlier)
        case
            when fm.statement_coverage_pct <= rs.coverage_p25 then 'p25_low_outlier'
            when fm.statement_coverage_pct <= rs.coverage_p50 then 'below_median'
            when fm.statement_coverage_pct <= rs.coverage_p75 then 'above_median'
            when fm.statement_coverage_pct <= rs.coverage_p90 then 'p90_high'
            else 'p90_plus_high'
        end as relative_position,
        fm.statement_coverage_pct < 80.0 as is_below_target,
        fm.statement_coverage_pct < 60.0 as is_medium_plus,
        fm.statement_coverage_pct < 40.0 as is_high_plus,
        fm.statement_coverage_pct < 20.0 as is_critical
    from file_metrics fm
    join run_stats rs on rs.run_pk = fm.run_pk
)
select
    run_pk,
    file_id,
    directory_id,
    relative_path,
    type_count,
    covered_statements,
    total_statements,
    statement_coverage_pct,
    gap_to_target_pct,
    statements_needed_for_target,
    risk_level,
    risk_level_numeric,
    relative_position,
    coverage_zscore,
    is_below_target,
    is_medium_plus,
    is_high_plus,
    is_critical,
    coverage_avg as run_coverage_avg,
    coverage_stddev as run_coverage_stddev,
    coverage_p25 as run_coverage_p25,
    coverage_p50 as run_coverage_p50,
    coverage_p75 as run_coverage_p75,
    coverage_p90 as run_coverage_p90,
    coverage_p95 as run_coverage_p95,
    total_files as run_total_files
from enriched_files
where statement_coverage_pct < 80.0 or coverage_zscore < -2.0
order by run_pk, statement_coverage_pct asc
