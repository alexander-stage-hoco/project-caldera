-- Aggregates gitleaks secret counts for files directly in each directory (non-recursive)

with gitleaks_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'gitleaks'
),
layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
run_map as (
    select
        gr.run_pk as gitleaks_run_pk,
        lr.run_pk as layout_run_pk,
        gr.collection_run_id
    from gitleaks_runs gr
    join layout_runs lr
        on lr.collection_run_id = gr.collection_run_id
),
files_direct as (
    select
        rm.gitleaks_run_pk as run_pk,
        rm.layout_run_pk,
        lf.directory_id,
        lf.file_id
    from {{ source('lz', 'lz_layout_files') }} lf
    join run_map rm
        on rm.layout_run_pk = lf.run_pk
),
file_metrics as (
    select
        fd.run_pk,
        fd.layout_run_pk,
        fd.directory_id,
        m.secret_count,
        m.severity_critical,
        m.severity_high,
        m.severity_medium,
        m.severity_low,
        m.severity_high_plus,
        m.secrets_in_head,
        m.secrets_in_history
    from files_direct fd
    join {{ ref('stg_gitleaks_secrets') }} m
        on m.run_pk = fd.run_pk
        and m.file_id = fd.file_id
),
directory_paths as (
    select
        run_pk,
        directory_id,
        relative_path
    from {{ source('lz', 'lz_layout_directories') }}
),
aggregated as (
    select
        run_pk,
        layout_run_pk,
        directory_id,
        count(*) as file_count,
        count(case when secret_count > 0 then 1 end) as files_with_secrets,
        sum(secret_count) as total_secret_count,
        -- Severity totals
        sum(severity_critical) as severity_critical,
        sum(severity_high) as severity_high,
        sum(severity_medium) as severity_medium,
        sum(severity_low) as severity_low,
        sum(severity_high_plus) as severity_high_plus,
        -- Location breakdown
        sum(secrets_in_head) as secrets_in_head,
        sum(secrets_in_history) as secrets_in_history
    from file_metrics
    group by run_pk, layout_run_pk, directory_id
)
select
    a.run_pk,
    a.directory_id,
    dp.relative_path as directory_path,
    a.file_count,
    a.files_with_secrets,
    a.total_secret_count,
    a.severity_critical,
    a.severity_high,
    a.severity_medium,
    a.severity_low,
    a.severity_high_plus,
    a.secrets_in_head,
    a.secrets_in_history
from aggregated a
join directory_paths dp
    on dp.run_pk = a.layout_run_pk
    and dp.directory_id = a.directory_id
