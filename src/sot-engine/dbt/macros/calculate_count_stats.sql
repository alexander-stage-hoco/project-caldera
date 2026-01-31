{% macro calculate_count_stats(tool_name, scope, staging_model, count_column, sum_columns, count_condition=none) %}
{#
    Generates directory-level count/sum aggregations for tools with similar structure.

    This macro handles tools that aggregate counts and sums from a staging model.
    For complex tools (Trivy, SonarQube) with multiple source tables or special logic,
    use custom SQL models instead.

    Args:
        tool_name: The tool name filter (e.g., 'roslyn-analyzers')
        scope: 'recursive' (all files in subtree) or 'direct' (files directly in directory)
        staging_model: The staging model name (e.g., 'stg_roslyn_file_metrics')
        count_column: The primary count column (e.g., 'violation_count')
        sum_columns: List of column names to sum (e.g., ['severity_high_plus', 'cat_security'])
        count_condition: Optional column name for counting files with issues (e.g., 'violation_count')
                        If provided, generates "files_with_X" count where X > 0
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
        lr.run_pk as layout_run_pk
    from tool_runs tr
    join layout_runs lr on lr.collection_run_id = tr.collection_run_id
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
file_metrics as (
    select
        dt.tool_run_pk as run_pk,
        dt.layout_run_pk,
        dt.ancestor_id as directory_id,
        m.file_id,
        m.{{ count_column }}
        {%- for col in sum_columns %},
        m.{{ col }}
        {%- endfor %}
    from {{ source('lz', 'lz_layout_files') }} lf
    join dir_tree dt
        on dt.layout_run_pk = lf.run_pk
        and dt.descendant_id = lf.directory_id
    join {{ ref(staging_model) }} m
        on m.run_pk = dt.tool_run_pk
        and m.file_id = lf.file_id
),
{% else %}
file_metrics as (
    select
        rm.tool_run_pk as run_pk,
        rm.layout_run_pk,
        lf.directory_id,
        m.file_id,
        m.{{ count_column }}
        {%- for col in sum_columns %},
        m.{{ col }}
        {%- endfor %}
    from {{ source('lz', 'lz_layout_files') }} lf
    join run_map rm
        on rm.layout_run_pk = lf.run_pk
    join {{ ref(staging_model) }} m
        on m.run_pk = rm.tool_run_pk
        and m.file_id = lf.file_id
),
{% endif %}
dir_files as (
    select
        fm.run_pk,
        fm.layout_run_pk,
        fm.directory_id,
        ld.relative_path as directory_path,
        fm.file_id,
        fm.{{ count_column }}
        {%- for col in sum_columns %},
        fm.{{ col }}
        {%- endfor %}
    from file_metrics fm
    join {{ source('lz', 'lz_layout_directories') }} ld
        on ld.run_pk = fm.layout_run_pk
        and ld.directory_id = fm.directory_id
)
select
    run_pk,
    directory_id,
    directory_path,
    count(distinct file_id) as file_count,
    {%- if count_condition %}
    count(case when {{ count_condition }} > 0 then 1 end) as files_with_issues,
    {%- endif %}
    sum({{ count_column }}) as total_{{ count_column }}
    {%- for col in sum_columns %},
    sum({{ col }}) as total_{{ col }}
    {%- endfor %}
from dir_files
group by run_pk, directory_id, directory_path

{% endmacro %}
