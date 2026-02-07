-- Project coupling hotspots for .NET architecture risk and dependency analysis
-- Coupling risk: critical (10+), high (5-9), medium (3-4), low (<3)
-- Instability zones: unstable (0.8+), flexible (0.5-0.8), stable (0.2-0.5), rigid (<0.2)
-- Coupling patterns: hub (both high), god_project (high fan-in), octopus (high fan-out)

with project_fan_out as (
    -- Count of projects each project references (outgoing dependencies)
    select
        pr.run_pk,
        pr.source_project_path as project_path,
        count(distinct pr.target_project_path) as fan_out
    from {{ ref('stg_dependensee_project_refs') }} pr
    group by pr.run_pk, pr.source_project_path
),
project_fan_in as (
    -- Count of projects that reference each project (incoming dependencies)
    select
        pr.run_pk,
        pr.target_project_path as project_path,
        count(distinct pr.source_project_path) as fan_in
    from {{ ref('stg_dependensee_project_refs') }} pr
    group by pr.run_pk, pr.target_project_path
),
coupling_metrics as (
    select
        p.run_pk,
        p.project_path,
        p.project_name,
        p.target_framework,
        p.project_reference_count,
        p.package_reference_count,
        coalesce(fo.fan_out, 0) as fan_out,
        coalesce(fi.fan_in, 0) as fan_in,
        coalesce(fo.fan_out, 0) + coalesce(fi.fan_in, 0) as total_coupling,
        case
            when coalesce(fo.fan_out, 0) + coalesce(fi.fan_in, 0) = 0 then 0.5
            else round(coalesce(fo.fan_out, 0)::numeric / (coalesce(fo.fan_out, 0) + coalesce(fi.fan_in, 0)), 2)
        end as instability
    from {{ ref('stg_dependensee_projects') }} p
    left join project_fan_out fo on fo.run_pk = p.run_pk and fo.project_path = p.project_path
    left join project_fan_in fi on fi.run_pk = p.run_pk and fi.project_path = p.project_path
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
        count(*) as total_projects
    from coupling_metrics
    group by run_pk
),
enriched_projects as (
    select
        cm.run_pk,
        cm.project_path,
        cm.project_name,
        cm.target_framework,
        cm.project_reference_count,
        cm.package_reference_count,
        cm.fan_out,
        cm.fan_in,
        cm.total_coupling,
        cm.instability,
        -- Coupling risk level (adjusted for project-level: 10+, 5-9, 3-4, <3)
        case
            when cm.total_coupling >= 10 then 'critical'
            when cm.total_coupling >= 5 then 'high'
            when cm.total_coupling >= 3 then 'medium'
            else 'low'
        end as coupling_risk,
        case
            when cm.total_coupling >= 10 then 4
            when cm.total_coupling >= 5 then 3
            when cm.total_coupling >= 3 then 2
            else 1
        end as coupling_risk_numeric,
        -- Instability zone
        case
            when cm.instability >= 0.8 then 'unstable'
            when cm.instability >= 0.5 then 'flexible'
            when cm.instability >= 0.2 then 'stable'
            else 'rigid'
        end as instability_zone,
        -- Coupling pattern detection (adjusted thresholds for project-level: 3/5)
        case
            when cm.fan_in > 3 and cm.fan_out > 3 then 'hub'
            when cm.fan_in > 5 and cm.fan_out <= 2 then 'god_project'
            when cm.fan_out > 5 and cm.fan_in <= 2 then 'octopus'
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
        rs.total_projects,
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
        cm.total_coupling >= 3 as is_medium_plus,
        cm.total_coupling >= 5 as is_high_plus,
        cm.total_coupling >= 10 as is_critical
    from coupling_metrics cm
    left join run_stats rs on rs.run_pk = cm.run_pk
)
select
    run_pk,
    project_path,
    project_name,
    target_framework,
    project_reference_count,
    package_reference_count,
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
    total_projects as run_total_projects
from enriched_projects
where total_coupling >= 3 or coupling_zscore > 2.0 or coupling_pattern != 'normal'
order by run_pk, total_coupling desc
