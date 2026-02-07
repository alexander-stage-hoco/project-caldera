-- Aggregates combined Trivy file metrics (vulns + IaC misconfigs) for files in each directory and subdirectories
-- Uses stg_trivy_file_metrics which already merges vulnerabilities and IaC misconfigurations

with recursive trivy_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'trivy'
),
layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
run_map as (
    select
        tr.run_pk as tool_run_pk,
        lr.run_pk as layout_run_pk,
        tr.collection_run_id
    from trivy_runs tr
    join layout_runs lr on lr.collection_run_id = tr.collection_run_id
),
dir_tree as (
    select
        run_pk,
        directory_id as ancestor_id,
        directory_id as descendant_id
    from {{ source('lz', 'lz_layout_directories') }}
    union all
    select
        dt.run_pk,
        dt.ancestor_id,
        ld.directory_id as descendant_id
    from dir_tree dt
    join {{ source('lz', 'lz_layout_directories') }} ld
        on ld.run_pk = dt.run_pk
        and ld.parent_id = dt.descendant_id
),
files_recursive as (
    select
        rm.layout_run_pk,
        rm.tool_run_pk,
        dt.ancestor_id as directory_id,
        lf.file_id
    from run_map rm
    join dir_tree dt on dt.run_pk = rm.layout_run_pk
    join {{ source('lz', 'lz_layout_files') }} lf
        on lf.run_pk = rm.layout_run_pk
        and lf.directory_id = dt.descendant_id
),
file_metrics as (
    select
        fr.layout_run_pk,
        fr.tool_run_pk,
        fr.directory_id,
        tf.vulnerability_count,
        tf.vuln_critical,
        tf.vuln_high,
        tf.vuln_medium,
        tf.vuln_low,
        tf.iac_misconfig_count,
        tf.iac_critical,
        tf.iac_high,
        tf.iac_medium,
        tf.iac_low,
        tf.total_finding_count,
        tf.severity_high_plus
    from files_recursive fr
    join {{ ref('stg_trivy_file_metrics') }} tf
        on tf.run_pk = fr.tool_run_pk
        and tf.file_id = fr.file_id
),
directory_paths as (
    select run_pk, directory_id, relative_path
    from {{ source('lz', 'lz_layout_directories') }}
),
aggregated as (
    select
        fm.layout_run_pk as run_pk,
        fm.tool_run_pk,
        fm.directory_id,
        count(*) as file_count,
        count(case when fm.vulnerability_count > 0 then 1 end) as files_with_vulns,
        count(case when fm.iac_misconfig_count > 0 then 1 end) as files_with_iac_misconfigs,
        sum(fm.vulnerability_count) as total_vulnerability_count,
        sum(fm.vuln_critical) as total_vuln_critical,
        sum(fm.vuln_high) as total_vuln_high,
        sum(fm.vuln_medium) as total_vuln_medium,
        sum(fm.vuln_low) as total_vuln_low,
        sum(fm.iac_misconfig_count) as total_iac_misconfig_count,
        sum(fm.iac_critical) as total_iac_critical,
        sum(fm.iac_high) as total_iac_high,
        sum(fm.iac_medium) as total_iac_medium,
        sum(fm.iac_low) as total_iac_low,
        sum(fm.total_finding_count) as total_finding_count,
        sum(fm.severity_high_plus) as total_severity_high_plus
    from file_metrics fm
    group by fm.layout_run_pk, fm.tool_run_pk, fm.directory_id
)
select
    a.run_pk,
    a.tool_run_pk,
    a.directory_id,
    dp.relative_path as directory_path,
    a.file_count,
    a.files_with_vulns,
    a.files_with_iac_misconfigs,
    a.total_vulnerability_count,
    a.total_vuln_critical,
    a.total_vuln_high,
    a.total_vuln_medium,
    a.total_vuln_low,
    a.total_iac_misconfig_count,
    a.total_iac_critical,
    a.total_iac_high,
    a.total_iac_medium,
    a.total_iac_low,
    a.total_finding_count,
    a.total_severity_high_plus
from aggregated a
join directory_paths dp
    on dp.run_pk = a.run_pk
    and dp.directory_id = a.directory_id
