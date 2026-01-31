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
layout_run as (
    select tr.run_pk as layout_run_pk
    from tool_runs tr
    join run_summary rs
        on rs.collection_run_id = tr.collection_run_id
    where tr.tool_name in ('layout', 'layout-scanner')
    limit 1
)
select
    coalesce(language, 'unknown') as language,
    count(*) as file_count,
    sum(coalesce(line_count, 0)) as line_count,
    sum(coalesce(size_bytes, 0)) as size_bytes
from {{ source('lz', 'lz_layout_files') }}
where run_pk = (select layout_run_pk from layout_run)
group by coalesce(language, 'unknown')
order by line_count desc, file_count desc, language
