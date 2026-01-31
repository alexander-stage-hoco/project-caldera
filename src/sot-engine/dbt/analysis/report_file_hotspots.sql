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
        max(case when tr.tool_name in ('layout', 'layout-scanner') then tr.run_pk end) as layout_run_pk,
        max(case when tr.tool_name = 'scc' then tr.run_pk end) as scc_run_pk,
        max(case when tr.tool_name = 'lizard' then tr.run_pk end) as lizard_run_pk,
        max(case when tr.tool_name = 'semgrep' then tr.run_pk end) as semgrep_run_pk,
        max(case when tr.tool_name in ('roslyn', 'roslyn-analyzers') then tr.run_pk end) as roslyn_run_pk
    from run_summary rs
    left join tool_runs tr
        on tr.collection_run_id = rs.collection_run_id
    group by rs.collection_run_id
),
layout_files as (
    select
        file_id,
        directory_id,
        relative_path,
        filename,
        language
    from {{ source('lz', 'lz_layout_files') }}
    where run_pk = (select layout_run_pk from tool_map)
),
scc_ranked as (
    select
        'loc_file' as category,
        lf.relative_path as file_path,
        lf.language,
        sm.lines_total as metric_value,
        row_number() over (
            order by sm.lines_total desc, lf.relative_path
        ) as rank_id
    from {{ source('lz', 'lz_scc_file_metrics') }} sm
    join layout_files lf
        on lf.file_id = sm.file_id
    where sm.run_pk = (select scc_run_pk from tool_map)
),
lizard_ranked as (
    select
        'complexity_file' as category,
        lf.relative_path as file_path,
        lf.language,
        lm.total_ccn as metric_value,
        row_number() over (
            order by lm.total_ccn desc, lf.relative_path
        ) as rank_id
    from {{ source('lz', 'lz_lizard_file_metrics') }} lm
    join layout_files lf
        on lf.file_id = lm.file_id
    where lm.run_pk = (select lizard_run_pk from tool_map)
),
semgrep_ranked as (
    select
        'semgrep_file' as category,
        sf.relative_path as file_path,
        lf.language,
        sf.smell_count as metric_value,
        row_number() over (
            order by sf.smell_count desc, sf.relative_path
        ) as rank_id
    from {{ ref('stg_semgrep_file_metrics') }} sf
    join layout_files lf
        on lf.file_id = sf.file_id
    where sf.run_pk = (select semgrep_run_pk from tool_map)
),
roslyn_ranked as (
    select
        'roslyn_file' as category,
        rf.relative_path as file_path,
        lf.language,
        rf.violation_count as metric_value,
        row_number() over (
            order by rf.violation_count desc, rf.relative_path
        ) as rank_id
    from {{ ref('stg_roslyn_file_metrics') }} rf
    join layout_files lf
        on lf.file_id = rf.file_id
    where rf.run_pk = (select roslyn_run_pk from tool_map)
),
unioned as (
    select * from scc_ranked
    union all
    select * from lizard_ranked
    union all
    select * from semgrep_ranked
    union all
    select * from roslyn_ranked
)
select *
from unioned
where rank_id <= {{ limit_rows }}
order by category, rank_id
