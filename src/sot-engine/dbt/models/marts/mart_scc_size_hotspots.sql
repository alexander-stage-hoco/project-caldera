-- File-level size and complexity hotspots from SCC
-- Identifies large files, high complexity density, and refactoring candidates
-- Risk levels: low, medium (>200 lines or >15 complexity), high (>500 lines or >30 complexity), critical (>1000 lines or >50 complexity)

with scc_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'scc'
),
layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
run_mapping as (
    select
        sr.run_pk as scc_run_pk,
        sr.collection_run_id,
        lyr.run_pk as layout_run_pk
    from scc_runs sr
    join layout_runs lyr on lyr.collection_run_id = sr.collection_run_id
),
file_metrics as (
    select
        rm.scc_run_pk,
        rm.collection_run_id,
        rm.layout_run_pk,
        fm.file_id,
        fm.directory_id,
        fm.language,
        fm.lines_total,
        fm.code_lines,
        fm.comment_lines,
        fm.blank_lines,
        fm.bytes,
        fm.complexity,
        fm.uloc,
        fm.comment_ratio,
        fm.code_ratio,
        fm.complexity_density,
        fm.bytes_per_loc,
        fm.is_minified,
        fm.is_generated
    from {{ source('lz', 'lz_scc_file_metrics') }} fm
    join run_mapping rm on rm.scc_run_pk = fm.run_pk
    where fm.is_minified = false and fm.is_generated = false
),
run_stats as (
    select
        collection_run_id,
        -- Lines statistics
        avg(lines_total) as lines_avg,
        stddev(lines_total) as lines_stddev,
        percentile_cont(0.50) within group (order by lines_total) as lines_p50,
        percentile_cont(0.75) within group (order by lines_total) as lines_p75,
        percentile_cont(0.90) within group (order by lines_total) as lines_p90,
        percentile_cont(0.95) within group (order by lines_total) as lines_p95,
        percentile_cont(0.99) within group (order by lines_total) as lines_p99,
        -- Complexity statistics
        avg(complexity) as complexity_avg,
        stddev(complexity) as complexity_stddev,
        percentile_cont(0.50) within group (order by complexity) as complexity_p50,
        percentile_cont(0.75) within group (order by complexity) as complexity_p75,
        percentile_cont(0.90) within group (order by complexity) as complexity_p90,
        percentile_cont(0.95) within group (order by complexity) as complexity_p95,
        percentile_cont(0.99) within group (order by complexity) as complexity_p99,
        -- Density statistics
        avg(complexity_density) as density_avg,
        stddev(complexity_density) as density_stddev,
        percentile_cont(0.50) within group (order by complexity_density) as density_p50,
        percentile_cont(0.75) within group (order by complexity_density) as density_p75,
        percentile_cont(0.90) within group (order by complexity_density) as density_p90,
        percentile_cont(0.95) within group (order by complexity_density) as density_p95,
        percentile_cont(0.99) within group (order by complexity_density) as density_p99,
        count(*) as total_files
    from file_metrics
    group by collection_run_id
),
enriched_files as (
    select
        fm.scc_run_pk as run_pk,
        fm.collection_run_id,
        fm.layout_run_pk,
        fm.file_id,
        fm.directory_id,
        lf.relative_path,
        fm.language,
        fm.lines_total,
        fm.code_lines,
        fm.comment_lines,
        fm.blank_lines,
        fm.bytes,
        fm.complexity,
        fm.complexity_density,
        fm.uloc,
        fm.comment_ratio,
        fm.code_ratio,
        fm.bytes_per_loc,
        fm.is_minified,
        fm.is_generated,
        -- Ranking
        rank() over (partition by fm.collection_run_id order by fm.lines_total desc) as lines_rank,
        rank() over (partition by fm.collection_run_id order by fm.complexity desc) as complexity_rank,
        rank() over (partition by fm.collection_run_id order by fm.complexity_density desc) as density_rank,
        -- Z-scores
        case when rs.lines_stddev > 0 then round((fm.lines_total - rs.lines_avg) / rs.lines_stddev, 2) else 0 end as lines_zscore,
        case when rs.complexity_stddev > 0 then round((fm.complexity - rs.complexity_avg) / rs.complexity_stddev, 2) else 0 end as complexity_zscore,
        case when rs.density_stddev > 0 then round((fm.complexity_density - rs.density_avg) / rs.density_stddev, 2) else 0 end as density_zscore,
        -- Absolute risk classification (primary)
        case
            when fm.lines_total > 1000 or fm.complexity > 50 or fm.complexity_density > 0.20 then 'critical'
            when fm.lines_total > 500 or fm.complexity > 30 or fm.complexity_density > 0.10 then 'high'
            when fm.lines_total > 200 or fm.complexity > 15 or fm.complexity_density > 0.05 then 'medium'
            else 'low'
        end as risk_level,
        case
            when fm.lines_total > 1000 or fm.complexity > 50 or fm.complexity_density > 0.20 then 4
            when fm.lines_total > 500 or fm.complexity > 30 or fm.complexity_density > 0.10 then 3
            when fm.lines_total > 200 or fm.complexity > 15 or fm.complexity_density > 0.05 then 2
            else 1
        end as risk_level_numeric,
        -- Relative position (percentile-based)
        case
            when fm.lines_total >= rs.lines_p99 or fm.complexity >= rs.complexity_p99 or fm.complexity_density >= rs.density_p99 then 'p99_outlier'
            when fm.lines_total >= rs.lines_p95 or fm.complexity >= rs.complexity_p95 or fm.complexity_density >= rs.density_p95 then 'p95_outlier'
            when fm.lines_total >= rs.lines_p90 or fm.complexity >= rs.complexity_p90 or fm.complexity_density >= rs.density_p90 then 'p90_outlier'
            when fm.lines_total >= rs.lines_p75 or fm.complexity >= rs.complexity_p75 or fm.complexity_density >= rs.density_p75 then 'above_median'
            else 'normal'
        end as relative_position,
        -- Boolean flags
        fm.lines_total > 200 or fm.complexity > 15 or fm.complexity_density > 0.05 as is_medium_plus,
        fm.lines_total > 500 or fm.complexity > 30 or fm.complexity_density > 0.10 as is_high_plus,
        fm.lines_total > 1000 or fm.complexity > 50 or fm.complexity_density > 0.20 as is_critical,
        -- Run-level context
        rs.lines_avg as run_lines_avg,
        rs.lines_stddev as run_lines_stddev,
        rs.lines_p50 as run_lines_p50,
        rs.lines_p75 as run_lines_p75,
        rs.lines_p90 as run_lines_p90,
        rs.lines_p95 as run_lines_p95,
        rs.lines_p99 as run_lines_p99,
        rs.total_files as run_total_files
    from file_metrics fm
    join {{ source('lz', 'lz_layout_files') }} lf
        on lf.run_pk = fm.layout_run_pk and lf.file_id = fm.file_id
    join run_stats rs on rs.collection_run_id = fm.collection_run_id
)
select
    run_pk,
    collection_run_id,
    file_id,
    directory_id,
    relative_path,
    language,
    lines_total,
    code_lines,
    comment_lines,
    blank_lines,
    bytes,
    complexity,
    complexity_density,
    uloc,
    comment_ratio,
    code_ratio,
    bytes_per_loc,
    is_minified,
    is_generated,
    lines_rank,
    lines_zscore,
    complexity_rank,
    complexity_zscore,
    density_rank,
    density_zscore,
    risk_level,
    risk_level_numeric,
    relative_position,
    is_medium_plus,
    is_high_plus,
    is_critical,
    run_lines_avg,
    run_lines_stddev,
    run_lines_p50,
    run_lines_p75,
    run_lines_p90,
    run_lines_p95,
    run_lines_p99,
    run_total_files
from enriched_files
where lines_total > 200 or complexity > 15 or complexity_density > 0.05 or lines_zscore > 2.0 or complexity_zscore > 2.0
order by collection_run_id, risk_level_numeric desc, lines_total desc
