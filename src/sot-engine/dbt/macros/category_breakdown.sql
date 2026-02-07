{% macro category_breakdown(tool_names, staging_model, entity_name) %}
{#
    Generates a category breakdown report with directory-level hotspots.
    Shows entities by category with top directories per category and severity breakdown.

    Args:
        tool_names: List of tool name filters (e.g., ['roslyn', 'roslyn-analyzers'] or ['semgrep'])
        staging_model: The staging model name for entities (e.g., 'stg_lz_roslyn_violations')
        entity_name: Singular name of the entity (e.g., 'violation' or 'smell')
                     Used to generate CTE name (violations/smells) and count column (violation_count/smell_count)

    Required dbt vars (set in calling analysis file):
        run_pk: The run primary key to filter on
        limit (optional, default 5): Number of top directories per category
#}

{% set entities_name = entity_name ~ 's' %}
{% set count_column = entity_name ~ '_count' %}
{% set tool_filter = "'" ~ tool_names | join("', '") ~ "'" %}
{% set run_pk = var('run_pk') %}
{% set limit_dirs = var('limit', 5) %}

with run_summary as (
    select run_pk, collection_run_id
    from {{ ref('unified_run_summary') }}
    where run_pk = {{ run_pk }}
),
tool_runs as (
    select run_pk, collection_run_id, tool_name
    from {{ source('lz', 'lz_tool_runs') }}
),
tool_map as (
    select
        rs.collection_run_id,
        max(case when tr.tool_name in ({{ tool_filter }}) then tr.run_pk end) as target_run_pk,
        max(case when tr.tool_name in ('layout', 'layout-scanner') then tr.run_pk end) as layout_run_pk
    from run_summary rs
    left join tool_runs tr
        on tr.collection_run_id = rs.collection_run_id
    group by rs.collection_run_id
),
{{ entities_name }} as (
    select
        dd_category,
        directory_id,
        severity,
        count(*) as {{ count_column }}
    from {{ ref(staging_model) }}
    where run_pk = (select target_run_pk from tool_map)
    group by dd_category, directory_id, severity
),
-- Category totals (repo-wide)
category_totals as (
    select
        dd_category,
        sum({{ count_column }}) as total_count,
        count(distinct directory_id) as dir_count_with_{{ entities_name }}
    from {{ entities_name }}
    group by dd_category
),
-- File counts per category
file_counts as (
    select
        dd_category,
        count(distinct file_id) as file_count
    from {{ ref(staging_model) }}
    where run_pk = (select target_run_pk from tool_map)
    group by dd_category
),
-- Directory aggregations per category
dir_category_agg as (
    select
        e.dd_category,
        e.directory_id,
        sum(e.{{ count_column }}) as dir_total,
        sum(case when e.severity = 'critical' then e.{{ count_column }} else 0 end) as sev_critical,
        sum(case when e.severity = 'high' then e.{{ count_column }} else 0 end) as sev_high,
        sum(case when e.severity = 'medium' then e.{{ count_column }} else 0 end) as sev_medium,
        sum(case when e.severity = 'low' then e.{{ count_column }} else 0 end) as sev_low,
        sum(case when e.severity = 'info' then e.{{ count_column }} else 0 end) as sev_info
    from {{ entities_name }} e
    group by e.dd_category, e.directory_id
),
-- Get directory paths from layout
layout_dirs as (
    select
        directory_id,
        relative_path as directory_path
    from {{ source('lz', 'lz_layout_directories') }}
    where run_pk = (select layout_run_pk from tool_map)
),
-- Rank directories within each category
dir_ranked as (
    select
        dca.dd_category,
        dca.directory_id,
        ld.directory_path,
        dca.dir_total,
        dca.sev_critical,
        dca.sev_high,
        dca.sev_medium,
        dca.sev_low,
        dca.sev_info,
        ct.total_count as category_total,
        fc.file_count,
        round(100.0 * dca.dir_total / ct.total_count, 1) as dir_pct,
        row_number() over (
            partition by dca.dd_category
            order by dca.dir_total desc, ld.directory_path
        ) as rank_in_category
    from dir_category_agg dca
    join category_totals ct on ct.dd_category = dca.dd_category
    join file_counts fc on fc.dd_category = dca.dd_category
    left join layout_dirs ld on ld.directory_id = dca.directory_id
)
select
    dd_category as category,
    category_total as total_count,
    file_count,
    directory_path,
    dir_total as dir_count,
    dir_pct,
    sev_critical,
    sev_high,
    sev_medium,
    sev_low,
    sev_info,
    rank_in_category
from dir_ranked
where rank_in_category <= {{ limit_dirs }}
order by category_total desc, dd_category, rank_in_category

{% endmacro %}
