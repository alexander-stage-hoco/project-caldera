-- High coupling symbol hotspots for architectural risk and refactoring prioritization
-- Coupling risk: critical (20+), high (10-19), medium (5-9), low (<5)
-- Instability zones: unstable (0.8+), flexible (0.5-0.8), stable (0.2-0.5), rigid (<0.2)
-- Coupling patterns: god_object (high fan-in), octopus (high fan-out), hub (both high)

with coupling_metrics as (
    select
        run_pk,
        file_id,
        directory_id,
        relative_path,
        symbol_name,
        symbol_type,
        fan_out,
        fan_in,
        total_coupling,
        instability
    from {{ ref('stg_symbol_coupling_metrics') }}
),
run_stats as (
    select
        run_pk,
        avg(total_coupling) as coupling_avg,
        stddev(total_coupling) as coupling_stddev,
        percentile_cont(0.50) within group (order by total_coupling) as coupling_p50,
        percentile_cont(0.75) within group (order by total_coupling) as coupling_p75,
        percentile_cont(0.90) within group (order by total_coupling) as coupling_p90,
        percentile_cont(0.95) within group (order by total_coupling) as coupling_p95,
        percentile_cont(0.99) within group (order by total_coupling) as coupling_p99,
        avg(fan_in) as fan_in_avg,
        avg(fan_out) as fan_out_avg,
        percentile_cont(0.90) within group (order by fan_in) as fan_in_p90,
        percentile_cont(0.90) within group (order by fan_out) as fan_out_p90,
        count(*) as total_symbols
    from coupling_metrics
    where total_coupling > 0
    group by run_pk
),
enriched_symbols as (
    select
        cm.run_pk,
        cm.file_id,
        cm.directory_id,
        cm.relative_path,
        cm.symbol_name,
        cm.symbol_type,
        cm.fan_out,
        cm.fan_in,
        cm.total_coupling,
        cm.instability,
        -- Coupling risk level
        case
            when cm.total_coupling >= 20 then 'critical'
            when cm.total_coupling >= 10 then 'high'
            when cm.total_coupling >= 5 then 'medium'
            else 'low'
        end as coupling_risk,
        case
            when cm.total_coupling >= 20 then 4
            when cm.total_coupling >= 10 then 3
            when cm.total_coupling >= 5 then 2
            else 1
        end as coupling_risk_numeric,
        -- Instability zone
        case
            when cm.instability >= 0.8 then 'unstable'
            when cm.instability >= 0.5 then 'flexible'
            when cm.instability >= 0.2 then 'stable'
            else 'rigid'
        end as instability_zone,
        -- Coupling pattern detection
        case
            when cm.fan_in >= 10 and cm.fan_out >= 10 then 'hub'
            when cm.fan_in >= 10 and cm.fan_out < 5 then 'god_object'
            when cm.fan_out >= 10 and cm.fan_in < 5 then 'octopus'
            else 'normal'
        end as coupling_pattern,
        -- Run-level statistics
        rs.coupling_avg,
        rs.coupling_stddev,
        rs.coupling_p50,
        rs.coupling_p75,
        rs.coupling_p90,
        rs.coupling_p95,
        rs.coupling_p99,
        rs.fan_in_avg,
        rs.fan_out_avg,
        rs.fan_in_p90,
        rs.fan_out_p90,
        rs.total_symbols,
        -- Z-score for total coupling
        case
            when rs.coupling_stddev > 0 then round((cm.total_coupling - rs.coupling_avg) / rs.coupling_stddev, 2)
            else 0
        end as coupling_zscore,
        -- Relative position
        case
            when cm.total_coupling >= rs.coupling_p99 then 'p99_outlier'
            when cm.total_coupling >= rs.coupling_p95 then 'p95_outlier'
            when cm.total_coupling >= rs.coupling_p90 then 'p90_outlier'
            when cm.total_coupling >= rs.coupling_p75 then 'above_median'
            else 'normal'
        end as relative_position,
        -- Architectural smell flags
        cm.instability < 0.2 and cm.fan_in > 0 as is_rigid_dependency,
        cm.instability > 0.8 and cm.fan_out > 0 as is_unstable_dependency,
        cm.total_coupling >= 5 as is_medium_plus,
        cm.total_coupling >= 10 as is_high_plus,
        cm.total_coupling >= 20 as is_critical
    from coupling_metrics cm
    left join run_stats rs on rs.run_pk = cm.run_pk
)
select
    run_pk,
    file_id,
    directory_id,
    relative_path,
    symbol_name,
    symbol_type,
    fan_out,
    fan_in,
    total_coupling,
    instability,
    coupling_risk,
    coupling_risk_numeric,
    instability_zone,
    coupling_pattern,
    coupling_zscore,
    relative_position,
    is_rigid_dependency,
    is_unstable_dependency,
    is_medium_plus,
    is_high_plus,
    is_critical,
    coupling_avg as run_coupling_avg,
    coupling_stddev as run_coupling_stddev,
    coupling_p50 as run_coupling_p50,
    coupling_p75 as run_coupling_p75,
    coupling_p90 as run_coupling_p90,
    coupling_p95 as run_coupling_p95,
    coupling_p99 as run_coupling_p99,
    fan_in_avg as run_fan_in_avg,
    fan_out_avg as run_fan_out_avg,
    fan_in_p90 as run_fan_in_p90,
    fan_out_p90 as run_fan_out_p90,
    total_symbols as run_total_symbols
from enriched_symbols
where total_coupling >= 5 or coupling_zscore > 2.0 or coupling_pattern != 'normal'
order by run_pk, total_coupling desc
