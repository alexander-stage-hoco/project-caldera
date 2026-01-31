with scc_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'scc'
),
lizard_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'lizard'
),
layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
scc_map as (
    select
        sr.run_pk as tool_run_pk,
        lr.run_pk as layout_run_pk
    from scc_runs sr
    join layout_runs lr
        on lr.collection_run_id = sr.collection_run_id
),
lizard_map as (
    select
        lr.run_pk as tool_run_pk,
        lrn.run_pk as layout_run_pk
    from lizard_runs lr
    join layout_runs lrn
        on lrn.collection_run_id = lr.collection_run_id
),
scc_files as (
    select
        sm.run_pk,
        rm.layout_run_pk,
        sm.file_id,
        sm.lines_total,
        sm.code_lines,
        sm.comment_lines,
        sm.blank_lines,
        sm.complexity
    from {{ source('lz', 'lz_scc_file_metrics') }} sm
    join scc_map rm
        on rm.tool_run_pk = sm.run_pk
),
lizard_files as (
    select
        lm.run_pk,
        rm.layout_run_pk,
        lm.file_id,
        lm.nloc,
        lm.total_ccn as lizard_total_ccn,
        lm.avg_ccn,
        lm.max_ccn
    from {{ source('lz', 'lz_lizard_file_metrics') }} lm
    join lizard_map rm
        on rm.tool_run_pk = lm.run_pk
),
combined as (
    select
        coalesce(scc.run_pk, lizard.run_pk) as run_pk,
        coalesce(scc.layout_run_pk, lizard.layout_run_pk) as layout_run_pk,
        coalesce(scc.file_id, lizard.file_id) as file_id,
        scc.lines_total,
        scc.code_lines,
        scc.comment_lines,
        scc.blank_lines,
        scc.complexity as scc_complexity,
        lizard.nloc,
        lizard.lizard_total_ccn,
        lizard.avg_ccn,
        lizard.max_ccn,
        concat_ws(
            ',',
            case when scc.run_pk is not null then 'scc' end,
            case when lizard.run_pk is not null then 'lizard' end
        ) as sources
    from scc_files scc
    full outer join lizard_files lizard
        on lizard.layout_run_pk = scc.layout_run_pk
       and lizard.file_id = scc.file_id
)
select
    combined.run_pk,
    combined.file_id,
    lf.relative_path,
    lf.directory_id,
    combined.lines_total as loc_total,
    combined.code_lines as loc_code,
    combined.comment_lines as loc_comment,
    combined.blank_lines as loc_blank,
    combined.scc_complexity as complexity_total,
    combined.nloc,
    combined.lizard_total_ccn as complexity_total_ccn,
    combined.avg_ccn as complexity_avg,
    combined.max_ccn as complexity_max,
    combined.sources
from combined
join {{ source('lz', 'lz_layout_files') }} lf
    on lf.run_pk = combined.layout_run_pk
   and lf.file_id = combined.file_id
