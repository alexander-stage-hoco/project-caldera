{% set run_pk = var('run_pk') %}
{% set limit_rows = var('limit', 10) %}

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
        max(case when tr.tool_name = 'scc' then tr.run_pk end) as scc_run_pk,
        max(case when tr.tool_name = 'lizard' then tr.run_pk end) as lizard_run_pk,
        max(case when tr.tool_name = 'semgrep' then tr.run_pk end) as semgrep_run_pk,
        max(case when tr.tool_name in ('roslyn', 'roslyn-analyzers') then tr.run_pk end) as roslyn_run_pk
    from run_summary rs
    left join tool_runs tr
        on tr.collection_run_id = rs.collection_run_id
    group by rs.collection_run_id
),
scc as (
    select *
    from {{ ref('rollup_scc_directory_recursive_distributions') }}
    where run_pk = (select scc_run_pk from tool_map)
      and metric = 'lines_total'
),
lizard as (
    select *
    from {{ ref('rollup_lizard_directory_recursive_distributions') }}
    where run_pk = (select lizard_run_pk from tool_map)
      and metric = 'total_ccn'
),
semgrep as (
    select *
    from {{ ref('rollup_semgrep_directory_recursive_distributions') }}
    where run_pk = (select semgrep_run_pk from tool_map)
      and metric = 'smell_count'
),
roslyn as (
    select *
    from {{ ref('rollup_roslyn_directory_recursive_distributions') }}
    where run_pk = (select roslyn_run_pk from tool_map)
      and metric = 'violation_count'
),
ranked as (
    select
        'loc_hotspot' as category,
        directory_path,
        value_count,
        avg_value,
        p95_value,
        p99_value,
        gini_value,
        hoover_value,
        top_20_pct_share,
        row_number() over (
            order by p95_value desc, avg_value desc, directory_path
        ) as rank_id
    from scc
    union all
    select
        'complexity_hotspot' as category,
        directory_path,
        value_count,
        avg_value,
        p95_value,
        p99_value,
        gini_value,
        hoover_value,
        top_20_pct_share,
        row_number() over (
            order by p95_value desc, avg_value desc, directory_path
        ) as rank_id
    from lizard
    union all
    select
        'semgrep_hotspot' as category,
        directory_path,
        value_count,
        avg_value,
        p95_value,
        p99_value,
        gini_value,
        hoover_value,
        top_20_pct_share,
        row_number() over (
            order by p95_value desc, avg_value desc, directory_path
        ) as rank_id
    from semgrep
    union all
    select
        'roslyn_hotspot' as category,
        directory_path,
        value_count,
        avg_value,
        p95_value,
        p99_value,
        gini_value,
        hoover_value,
        top_20_pct_share,
        row_number() over (
            order by p95_value desc, avg_value desc, directory_path
        ) as rank_id
    from roslyn
)
select *
from ranked
where rank_id <= {{ limit_rows }}
order by category, rank_id
