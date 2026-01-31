{% macro calculate_distribution_stats(tool_name, scope, metrics_table, metrics, use_ref=false) %}
{#
    Generates distribution statistics for directory-level metric aggregations.

    Args:
        tool_name: The tool name filter (e.g., 'scc', 'lizard')
        scope: 'recursive' (all files in subtree) or 'direct' (files directly in directory)
        metrics_table: The source table for file metrics (e.g., 'lz_scc_file_metrics')
        metrics: List of metric column names to include in distribution calculations
        use_ref: If true, use ref(metrics_table) instead of source('lz', metrics_table)
#}

{% if scope == 'recursive' %}
with recursive tool_runs as (
{% else %}
with tool_runs as (
{% endif %}
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = '{{ tool_name }}'
),
layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
run_map as (
    select
        tr.run_pk as tool_run_pk,
        lr.run_pk as layout_run_pk,
        tr.collection_run_id
    from tool_runs tr
    join layout_runs lr
        on lr.collection_run_id = tr.collection_run_id
),
{% if scope == 'recursive' %}
dir_tree as (
    select
        rm.tool_run_pk,
        rm.layout_run_pk,
        directory_id as ancestor_id,
        directory_id as descendant_id
    from {{ source('lz', 'lz_layout_directories') }} ld
    join run_map rm
        on rm.layout_run_pk = ld.run_pk

    union all

    select
        parent.tool_run_pk,
        parent.layout_run_pk,
        parent.ancestor_id,
        child.directory_id as descendant_id
    from dir_tree parent
    join {{ source('lz', 'lz_layout_directories') }} child
        on child.run_pk = parent.layout_run_pk
        and child.parent_id = parent.descendant_id
),
files_with_ancestor as (
    select
        dt.tool_run_pk,
        dt.layout_run_pk,
        lf.file_id,
        dt.ancestor_id as directory_id
    from {{ source('lz', 'lz_layout_files') }} lf
    join dir_tree dt
        on dt.layout_run_pk = lf.run_pk
        and dt.descendant_id = lf.directory_id
),
file_metrics as (
    select
        fa.tool_run_pk as run_pk,
        fa.directory_id,
        {% for metric in metrics %}
        m.{{ metric }}{{ ',' if not loop.last else '' }}
        {% endfor %}
    from files_with_ancestor fa
    join {% if use_ref %}{{ ref(metrics_table) }}{% else %}{{ source('lz', metrics_table) }}{% endif %} m
        on m.run_pk = fa.tool_run_pk
        and m.file_id = fa.file_id
),
{% else %}
files_direct as (
    select
        rm.tool_run_pk as run_pk,
        lf.directory_id,
        lf.file_id
    from {{ source('lz', 'lz_layout_files') }} lf
    join run_map rm
        on rm.layout_run_pk = lf.run_pk
),
file_metrics as (
    select
        fd.run_pk,
        fd.directory_id,
        {% for metric in metrics %}
        m.{{ metric }}{{ ',' if not loop.last else '' }}
        {% endfor %}
    from files_direct fd
    join {% if use_ref %}{{ ref(metrics_table) }}{% else %}{{ source('lz', metrics_table) }}{% endif %} m
        on m.run_pk = fd.run_pk
        and m.file_id = fd.file_id
),
{% endif %}
directory_paths as (
    select
        run_pk,
        directory_id,
        relative_path
    from {{ source('lz', 'lz_layout_directories') }}
),
fm as (
    {% for metric in metrics %}
    select run_pk, directory_id, '{{ metric }}' as metric, cast({{ metric }} as double) as value
    from file_metrics where {{ metric }} is not null
    {{ 'union all' if not loop.last else '' }}
    {% endfor %}
),
stats as (
    select
        run_pk,
        directory_id,
        metric,
        count(*) as value_count,
        min(value) as min_value,
        max(value) as max_value,
        avg(value) as avg_value,
        stddev_pop(value) as stddev_value,
        quantile_cont(value, 0.25) as p25_value,
        quantile_cont(value, 0.50) as p50_value,
        quantile_cont(value, 0.75) as p75_value,
        quantile_cont(value, 0.90) as p90_value,
        quantile_cont(value, 0.95) as p95_value,
        quantile_cont(value, 0.99) as p99_value,
        skewness(value) as skewness_value,
        kurtosis(value) as kurtosis_value
    from fm
    group by run_pk, directory_id, metric
),
ranked as (
    select
        fm.*,
        row_number() over (
            partition by run_pk, directory_id, metric
            order by value
        ) as rn_asc,
        row_number() over (
            partition by run_pk, directory_id, metric
            order by value desc
        ) as rn_desc,
        count(*) over (
            partition by run_pk, directory_id, metric
        ) as value_count,
        sum(value) over (
            partition by run_pk, directory_id, metric
        ) as total_value,
        avg(value) over (
            partition by run_pk, directory_id, metric
        ) as mean_value
    from fm
),
shares as (
    select
        run_pk,
        directory_id,
        metric,
        max(value_count) as value_count,
        max(total_value) as total_value,
        max(mean_value) as mean_value,
        sum(rn_asc * value) as gini_sum,
        sum(case
            when rn_desc <= greatest(1, cast(floor(value_count * 0.10) as bigint))
            then value else 0 end
        ) as top_10_sum,
        sum(case
            when rn_desc <= greatest(1, cast(floor(value_count * 0.20) as bigint))
            then value else 0 end
        ) as top_20_sum,
        sum(case
            when rn_asc <= greatest(1, cast(floor(value_count * 0.50) as bigint))
            then value else 0 end
        ) as bottom_50_sum,
        sum(case
            when rn_asc <= greatest(1, cast(floor(value_count * 0.40) as bigint))
            then value else 0 end
        ) as bottom_40_sum,
        sum(abs(value - mean_value)) as abs_dev_sum,
        sum(case
            when value > 0 and mean_value > 0
            then (value / mean_value) * ln(value / mean_value)
            else 0 end
        ) as theil_sum
    from ranked
    group by run_pk, directory_id, metric
)
select
    stats.run_pk,
    stats.directory_id,
    dp.relative_path as directory_path,
    stats.metric,
    stats.value_count,
    stats.min_value,
    stats.max_value,
    stats.avg_value,
    stats.stddev_value,
    stats.p25_value,
    stats.p50_value,
    stats.p75_value,
    stats.p90_value,
    stats.p95_value,
    stats.p99_value,
    stats.p50_value as median_value,
    stats.skewness_value,
    stats.kurtosis_value,
    case
        when stats.avg_value > 0 then stats.stddev_value / stats.avg_value
        else 0 end as cv_value,
    stats.p75_value - stats.p25_value as iqr_value,
    case
        when shares.value_count < 2 or shares.total_value = 0 then 0
        else greatest(
            0,
            least(
                1,
                (2 * shares.gini_sum) / (shares.value_count * shares.total_value)
                - (shares.value_count + 1) / shares.value_count
            )
        )
        end as gini_value,
    case
        when shares.mean_value <= 0 or shares.value_count = 0 then 0
        else shares.theil_sum / shares.value_count end as theil_value,
    case
        when shares.total_value = 0 then 0
        else greatest(
            0,
            least(1, 0.5 * shares.abs_dev_sum / shares.total_value)
        ) end as hoover_value,
    case
        when shares.value_count < 10 then 0
        when shares.bottom_40_sum = 0 then 0
        else shares.top_10_sum / shares.bottom_40_sum end as palma_value,
    case
        when shares.total_value = 0 then 0
        else greatest(
            0,
            least(1, shares.top_10_sum / shares.total_value)
        ) end as top_10_pct_share,
    case
        when shares.total_value = 0 then 0
        else greatest(
            0,
            least(1, shares.top_20_sum / shares.total_value)
        ) end as top_20_pct_share,
    case
        when shares.total_value = 0 then 0
        else greatest(
            0,
            least(1, shares.bottom_50_sum / shares.total_value)
        ) end as bottom_50_pct_share
from stats
join shares
    on shares.run_pk = stats.run_pk
    and shares.directory_id = stats.directory_id
    and shares.metric = stats.metric
join directory_paths dp
    on dp.run_pk = (
        select layout_run_pk from run_map rm
        where rm.tool_run_pk = stats.run_pk
        limit 1
    )
    and dp.directory_id = stats.directory_id

{% endmacro %}
