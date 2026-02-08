-- Layout structure hotspots
-- Identifies structural problem areas: deeply nested directories, oversized folders,
-- file concentration, and organization issues
-- Risk levels based on z-score and percentile thresholds

with layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
directories as (
    select
        lr.run_pk,
        lr.collection_run_id,
        ld.directory_id,
        ld.relative_path as directory_path,
        ld.parent_id,
        ld.depth,
        ld.file_count as direct_file_count,
        ld.total_size_bytes as direct_size_bytes
    from {{ source('lz', 'lz_layout_directories') }} ld
    join layout_runs lr
        on lr.run_pk = ld.run_pk
),
recursive_counts as (
    select
        run_pk,
        directory_id,
        directory_path,
        file_count as recursive_file_count,
        total_size_bytes as recursive_size_bytes,
        language_count,
        category_count
    from {{ ref('rollup_layout_directory_counts_recursive') }}
),
direct_counts as (
    select
        run_pk,
        directory_id,
        file_count as direct_file_count,
        total_size_bytes as direct_size_bytes
    from {{ ref('rollup_layout_directory_counts_direct') }}
),
size_distributions as (
    select
        run_pk,
        directory_id,
        gini_value as size_gini,
        palma_value as size_palma
    from {{ ref('rollup_layout_directory_recursive_distributions') }}
    where metric = 'size_bytes'
),
dir_metrics as (
    select
        d.run_pk,
        d.collection_run_id,
        d.directory_id,
        d.directory_path,
        d.parent_id,
        d.depth,
        coalesce(rc.recursive_file_count, 0) as file_count_recursive,
        coalesce(dc.direct_file_count, 0) as file_count_direct,
        coalesce(rc.recursive_size_bytes, 0) as total_size_bytes_recursive,
        coalesce(dc.direct_size_bytes, 0) as total_size_bytes_direct,
        coalesce(rc.language_count, 0) as language_count,
        coalesce(rc.category_count, 0) as category_count,
        coalesce(sd.size_gini, 0) as size_gini,
        coalesce(sd.size_palma, 0) as size_palma
    from directories d
    left join recursive_counts rc
        on rc.run_pk = d.run_pk
        and rc.directory_id = d.directory_id
    left join direct_counts dc
        on dc.run_pk = d.run_pk
        and dc.directory_id = d.directory_id
    left join size_distributions sd
        on sd.run_pk = d.run_pk
        and sd.directory_id = d.directory_id
),
run_stats as (
    select
        run_pk,
        -- Depth stats
        avg(depth) as depth_avg,
        stddev_pop(depth) as depth_stddev,
        percentile_cont(0.75) within group (order by depth) as depth_p75,
        percentile_cont(0.95) within group (order by depth) as depth_p95,
        percentile_cont(0.99) within group (order by depth) as depth_p99,
        -- File count stats (recursive)
        avg(file_count_recursive) as file_count_avg,
        stddev_pop(file_count_recursive) as file_count_stddev,
        percentile_cont(0.75) within group (order by file_count_recursive) as file_count_p75,
        percentile_cont(0.95) within group (order by file_count_recursive) as file_count_p95,
        percentile_cont(0.99) within group (order by file_count_recursive) as file_count_p99,
        -- Size stats (recursive)
        avg(total_size_bytes_recursive) as size_avg,
        stddev_pop(total_size_bytes_recursive) as size_stddev,
        percentile_cont(0.75) within group (order by total_size_bytes_recursive) as size_p75,
        percentile_cont(0.95) within group (order by total_size_bytes_recursive) as size_p95,
        percentile_cont(0.99) within group (order by total_size_bytes_recursive) as size_p99,
        count(*) as total_directories
    from dir_metrics
    group by run_pk
),
ranked_dirs as (
    select
        dm.*,
        rs.depth_avg,
        rs.depth_stddev,
        rs.depth_p75,
        rs.depth_p95,
        rs.depth_p99,
        rs.file_count_avg,
        rs.file_count_stddev,
        rs.file_count_p75,
        rs.file_count_p95,
        rs.file_count_p99,
        rs.size_avg,
        rs.size_stddev,
        rs.size_p75,
        rs.size_p95,
        rs.size_p99,
        rs.total_directories,
        -- Depth ranking and z-score
        row_number() over (partition by dm.run_pk order by dm.depth desc) as depth_rank,
        case
            when rs.depth_stddev > 0 then round((dm.depth - rs.depth_avg) / rs.depth_stddev, 2)
            else 0
        end as depth_zscore,
        -- File count ranking and z-score
        row_number() over (partition by dm.run_pk order by dm.file_count_recursive desc) as file_rank,
        case
            when rs.file_count_stddev > 0 then round((dm.file_count_recursive - rs.file_count_avg) / rs.file_count_stddev, 2)
            else 0
        end as file_zscore,
        -- Size ranking and z-score
        row_number() over (partition by dm.run_pk order by dm.total_size_bytes_recursive desc) as size_rank,
        case
            when rs.size_stddev > 0 then round((dm.total_size_bytes_recursive - rs.size_avg) / rs.size_stddev, 2)
            else 0
        end as size_zscore
    from dir_metrics dm
    join run_stats rs on rs.run_pk = dm.run_pk
),
with_risk as (
    select
        rd.*,
        -- Risk level based on z-scores and percentile thresholds
        case
            when rd.depth >= rd.depth_p99 or rd.depth_zscore > 3.0
                or rd.file_count_recursive >= rd.file_count_p99 or rd.file_zscore > 3.0
                or rd.total_size_bytes_recursive >= rd.size_p99 or rd.size_zscore > 3.0
            then 'critical'
            when rd.depth >= rd.depth_p95 or rd.depth_zscore > 2.0
                or rd.file_count_recursive >= rd.file_count_p95 or rd.file_zscore > 2.0
                or rd.total_size_bytes_recursive >= rd.size_p95 or rd.size_zscore > 2.0
            then 'high'
            when rd.depth >= rd.depth_p75 or rd.depth_zscore > 1.0
                or rd.file_count_recursive >= rd.file_count_p75 or rd.file_zscore > 1.0
                or rd.total_size_bytes_recursive >= rd.size_p75 or rd.size_zscore > 1.0
            then 'medium'
            else 'low'
        end as risk_level
    from ranked_dirs rd
)
select
    run_pk,
    collection_run_id,
    directory_id,
    directory_path,
    depth,
    file_count_recursive,
    file_count_direct,
    total_size_bytes_recursive,
    total_size_bytes_direct,
    language_count,
    category_count,
    size_gini,
    size_palma,
    depth_rank,
    depth_zscore,
    file_rank,
    file_zscore,
    size_rank,
    size_zscore,
    risk_level,
    case risk_level
        when 'critical' then 4
        when 'high' then 3
        when 'medium' then 2
        else 1
    end as risk_level_numeric,
    depth >= depth_p75 as is_deeply_nested,
    file_count_recursive >= file_count_p75 as is_file_heavy,
    total_size_bytes_recursive >= size_p75 as is_size_heavy,
    size_gini > 0.5 as has_size_concentration,
    total_directories as run_total_directories
from with_risk
where depth >= depth_p75
    or file_count_recursive >= file_count_p75
    or total_size_bytes_recursive >= size_p75
    or depth_zscore > 1.0
    or file_zscore > 1.0
    or size_zscore > 1.0
order by collection_run_id, risk_level_numeric desc, file_count_recursive desc
