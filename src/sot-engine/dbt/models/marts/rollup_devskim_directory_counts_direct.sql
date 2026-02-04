-- Aggregates devskim issue counts for files directly in each directory (non-recursive)

with devskim_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'devskim'
),
layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
run_map as (
    select
        dr.run_pk as devskim_run_pk,
        lr.run_pk as layout_run_pk,
        dr.collection_run_id
    from devskim_runs dr
    join layout_runs lr
        on lr.collection_run_id = dr.collection_run_id
),
files_direct as (
    select
        rm.devskim_run_pk as run_pk,
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
        m.issue_count,
        m.severity_critical,
        m.severity_high,
        m.severity_medium,
        m.severity_low,
        m.severity_high_plus,
        m.cat_sql_injection,
        m.cat_hardcoded_secret,
        m.cat_insecure_crypto,
        m.cat_xss,
        m.cat_command_injection,
        m.cat_path_traversal,
        m.cat_insecure_deserialization,
        m.cat_insecure_ssl_tls,
        m.cat_insecure_random,
        m.cat_insecure_file_handling,
        m.cat_information_disclosure,
        m.cat_authentication,
        m.cat_authorization,
        m.cat_xml_injection,
        m.cat_other
    from files_direct fd
    join {{ ref('stg_devskim_file_metrics') }} m
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
        count(case when issue_count > 0 then 1 end) as files_with_issues,
        sum(issue_count) as total_issue_count,
        -- Severity totals
        sum(severity_critical) as severity_critical,
        sum(severity_high) as severity_high,
        sum(severity_medium) as severity_medium,
        sum(severity_low) as severity_low,
        sum(severity_high_plus) as severity_high_plus,
        -- Category totals
        sum(cat_sql_injection) as cat_sql_injection,
        sum(cat_hardcoded_secret) as cat_hardcoded_secret,
        sum(cat_insecure_crypto) as cat_insecure_crypto,
        sum(cat_xss) as cat_xss,
        sum(cat_command_injection) as cat_command_injection,
        sum(cat_path_traversal) as cat_path_traversal,
        sum(cat_insecure_deserialization) as cat_insecure_deserialization,
        sum(cat_insecure_ssl_tls) as cat_insecure_ssl_tls,
        sum(cat_insecure_random) as cat_insecure_random,
        sum(cat_insecure_file_handling) as cat_insecure_file_handling,
        sum(cat_information_disclosure) as cat_information_disclosure,
        sum(cat_authentication) as cat_authentication,
        sum(cat_authorization) as cat_authorization,
        sum(cat_xml_injection) as cat_xml_injection,
        sum(cat_other) as cat_other
    from file_metrics
    group by run_pk, layout_run_pk, directory_id
)
select
    a.run_pk,
    a.directory_id,
    dp.relative_path as directory_path,
    a.file_count,
    a.files_with_issues,
    a.total_issue_count,
    a.severity_critical,
    a.severity_high,
    a.severity_medium,
    a.severity_low,
    a.severity_high_plus,
    a.cat_sql_injection,
    a.cat_hardcoded_secret,
    a.cat_insecure_crypto,
    a.cat_xss,
    a.cat_command_injection,
    a.cat_path_traversal,
    a.cat_insecure_deserialization,
    a.cat_insecure_ssl_tls,
    a.cat_insecure_random,
    a.cat_insecure_file_handling,
    a.cat_information_disclosure,
    a.cat_authentication,
    a.cat_authorization,
    a.cat_xml_injection,
    a.cat_other
from aggregated a
join directory_paths dp
    on dp.run_pk = a.layout_run_pk
    and dp.directory_id = a.directory_id
