-- Aggregates SonarQube issue counts for files directly in each directory (non-recursive)

with sonarqube_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'sonarqube'
),
layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
run_map as (
    select
        sr.run_pk as sonarqube_run_pk,
        lr.run_pk as layout_run_pk,
        sr.collection_run_id
    from sonarqube_runs sr
    join layout_runs lr
        on lr.collection_run_id = sr.collection_run_id
),
files_direct as (
    select
        rm.sonarqube_run_pk as run_pk,
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
        m.type_bug,
        m.type_vulnerability,
        m.type_code_smell,
        m.type_security_hotspot,
        m.severity_blocker,
        m.severity_critical,
        m.severity_major,
        m.severity_minor,
        m.severity_info,
        m.severity_high_plus,
        m.ncloc,
        m.complexity,
        m.cognitive_complexity,
        m.duplicated_lines
    from files_direct fd
    join {{ ref('stg_sonarqube_file_metrics') }} m
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
        -- Type totals
        sum(type_bug) as type_bug,
        sum(type_vulnerability) as type_vulnerability,
        sum(type_code_smell) as type_code_smell,
        sum(type_security_hotspot) as type_security_hotspot,
        -- Severity totals
        sum(severity_blocker) as severity_blocker,
        sum(severity_critical) as severity_critical,
        sum(severity_major) as severity_major,
        sum(severity_minor) as severity_minor,
        sum(severity_info) as severity_info,
        sum(severity_high_plus) as severity_high_plus,
        -- Metrics totals
        sum(ncloc) as total_ncloc,
        sum(complexity) as total_complexity,
        sum(cognitive_complexity) as total_cognitive_complexity,
        sum(duplicated_lines) as total_duplicated_lines
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
    a.type_bug,
    a.type_vulnerability,
    a.type_code_smell,
    a.type_security_hotspot,
    a.severity_blocker,
    a.severity_critical,
    a.severity_major,
    a.severity_minor,
    a.severity_info,
    a.severity_high_plus,
    a.total_ncloc,
    a.total_complexity,
    a.total_cognitive_complexity,
    a.total_duplicated_lines
from aggregated a
join directory_paths dp
    on dp.run_pk = a.layout_run_pk
    and dp.directory_id = a.directory_id
