{% set run_pk = var('run_pk') %}

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
        max(case when tr.tool_name = 'semgrep' then tr.run_pk end) as semgrep_run_pk,
        max(case when tr.tool_name in ('roslyn', 'roslyn-analyzers') then tr.run_pk end) as roslyn_run_pk
    from run_summary rs
    left join tool_runs tr
        on tr.collection_run_id = rs.collection_run_id
    group by rs.collection_run_id
),
semgrep_totals as (
    select
        'semgrep' as tool,
        'severity' as category_type,
        'high_plus' as category,
        sum(severity_high_plus) as total_count
    from {{ ref('stg_semgrep_file_metrics') }}
    where run_pk = (select semgrep_run_pk from tool_map)
    union all
    select
        'semgrep',
        'severity',
        'total',
        sum(smell_count)
    from {{ ref('stg_semgrep_file_metrics') }}
    where run_pk = (select semgrep_run_pk from tool_map)
),
roslyn_totals as (
    select
        'roslyn' as tool,
        'severity' as category_type,
        'critical' as category,
        sum(severity_critical) as total_count
    from {{ ref('stg_roslyn_file_metrics') }}
    where run_pk = (select roslyn_run_pk from tool_map)
    union all
    select 'roslyn', 'severity', 'high', sum(severity_high)
    from {{ ref('stg_roslyn_file_metrics') }}
    where run_pk = (select roslyn_run_pk from tool_map)
    union all
    select 'roslyn', 'severity', 'medium', sum(severity_medium)
    from {{ ref('stg_roslyn_file_metrics') }}
    where run_pk = (select roslyn_run_pk from tool_map)
    union all
    select 'roslyn', 'severity', 'low', sum(severity_low)
    from {{ ref('stg_roslyn_file_metrics') }}
    where run_pk = (select roslyn_run_pk from tool_map)
    union all
    select 'roslyn', 'severity', 'info', sum(severity_info)
    from {{ ref('stg_roslyn_file_metrics') }}
    where run_pk = (select roslyn_run_pk from tool_map)
    union all
    select 'roslyn', 'category', 'security', sum(cat_security)
    from {{ ref('stg_roslyn_file_metrics') }}
    where run_pk = (select roslyn_run_pk from tool_map)
    union all
    select 'roslyn', 'category', 'design', sum(cat_design)
    from {{ ref('stg_roslyn_file_metrics') }}
    where run_pk = (select roslyn_run_pk from tool_map)
    union all
    select 'roslyn', 'category', 'resource', sum(cat_resource)
    from {{ ref('stg_roslyn_file_metrics') }}
    where run_pk = (select roslyn_run_pk from tool_map)
    union all
    select 'roslyn', 'category', 'dead_code', sum(cat_dead_code)
    from {{ ref('stg_roslyn_file_metrics') }}
    where run_pk = (select roslyn_run_pk from tool_map)
    union all
    select 'roslyn', 'category', 'performance', sum(cat_performance)
    from {{ ref('stg_roslyn_file_metrics') }}
    where run_pk = (select roslyn_run_pk from tool_map)
    union all
    select 'roslyn', 'category', 'other', sum(cat_other)
    from {{ ref('stg_roslyn_file_metrics') }}
    where run_pk = (select roslyn_run_pk from tool_map)
)
select *
from semgrep_totals
union all
select * from roslyn_totals
order by tool, category_type, category
