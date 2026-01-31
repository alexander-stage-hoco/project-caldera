-- Aggregates Trivy vulnerability and IaC misconfiguration counts for files in each directory and all subdirectories (recursive)

with trivy_runs as (
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
        tr.run_pk as trivy_run_pk,
        lr.run_pk as layout_run_pk,
        tr.collection_run_id
    from trivy_runs tr
    join layout_runs lr
        on lr.collection_run_id = tr.collection_run_id
),
dir_hierarchy as (
    select
        run_pk,
        directory_id,
        relative_path
    from {{ source('lz', 'lz_layout_directories') }}
),
files_with_ancestors as (
    select
        rm.trivy_run_pk as run_pk,
        rm.layout_run_pk,
        lf.file_id,
        dh.directory_id as ancestor_directory_id
    from {{ source('lz', 'lz_layout_files') }} lf
    join run_map rm
        on rm.layout_run_pk = lf.run_pk
    join dir_hierarchy dh
        on dh.run_pk = lf.run_pk
       and (lf.directory_id = dh.directory_id
            or lf.relative_path like dh.relative_path || '/%')
),
-- Aggregate vulnerability counts from targets
vuln_metrics as (
    select
        fa.run_pk,
        fa.layout_run_pk,
        fa.ancestor_directory_id as directory_id,
        fa.file_id,
        coalesce(t.vulnerability_count, 0) as vulnerability_count,
        coalesce(t.critical_count, 0) as vuln_critical_count,
        coalesce(t.high_count, 0) as vuln_high_count,
        coalesce(t.medium_count, 0) as vuln_medium_count,
        coalesce(t.low_count, 0) as vuln_low_count,
        case when t.target_key is not null then 1 else 0 end as has_target
    from files_with_ancestors fa
    left join {{ source('lz', 'lz_trivy_targets') }} t
        on t.run_pk = fa.run_pk
        and t.file_id = fa.file_id
),
-- Aggregate IaC misconfig counts by severity
iac_metrics as (
    select
        fa.run_pk,
        fa.layout_run_pk,
        fa.ancestor_directory_id as directory_id,
        fa.file_id,
        count(*) as misconfig_count,
        count(case when m.severity = 'CRITICAL' then 1 end) as iac_critical_count,
        count(case when m.severity = 'HIGH' then 1 end) as iac_high_count,
        count(case when m.severity = 'MEDIUM' then 1 end) as iac_medium_count,
        count(case when m.severity = 'LOW' then 1 end) as iac_low_count
    from files_with_ancestors fa
    join {{ source('lz', 'lz_trivy_iac_misconfigs') }} m
        on m.run_pk = fa.run_pk
        and m.file_id = fa.file_id
    group by fa.run_pk, fa.layout_run_pk, fa.ancestor_directory_id, fa.file_id
),
-- Combine vuln and IaC metrics per file
combined_metrics as (
    select
        v.run_pk,
        v.layout_run_pk,
        v.directory_id,
        v.has_target,
        v.vulnerability_count,
        v.vuln_critical_count,
        v.vuln_high_count,
        v.vuln_medium_count,
        v.vuln_low_count,
        coalesce(i.misconfig_count, 0) as misconfig_count,
        coalesce(i.iac_critical_count, 0) as iac_critical_count,
        coalesce(i.iac_high_count, 0) as iac_high_count,
        coalesce(i.iac_medium_count, 0) as iac_medium_count,
        coalesce(i.iac_low_count, 0) as iac_low_count
    from vuln_metrics v
    left join iac_metrics i
        on i.run_pk = v.run_pk
        and i.directory_id = v.directory_id
        and i.file_id = v.file_id
),
aggregated as (
    select
        run_pk,
        layout_run_pk,
        directory_id,
        -- Target counts
        sum(has_target) as target_count,
        count(case when vulnerability_count > 0 then 1 end) as files_with_vulns,
        -- Vulnerability totals
        sum(vulnerability_count) as total_vulnerability_count,
        sum(vuln_critical_count) as vuln_critical_count,
        sum(vuln_high_count) as vuln_high_count,
        sum(vuln_medium_count) as vuln_medium_count,
        sum(vuln_low_count) as vuln_low_count,
        -- IaC misconfig totals
        count(case when misconfig_count > 0 then 1 end) as files_with_iac_misconfigs,
        sum(misconfig_count) as total_iac_misconfig_count,
        sum(iac_critical_count) as iac_critical_count,
        sum(iac_high_count) as iac_high_count,
        sum(iac_medium_count) as iac_medium_count,
        sum(iac_low_count) as iac_low_count
    from combined_metrics
    group by run_pk, layout_run_pk, directory_id
)
select
    a.run_pk,
    a.directory_id,
    dh.relative_path as directory_path,
    a.target_count,
    a.files_with_vulns,
    a.total_vulnerability_count,
    a.vuln_critical_count,
    a.vuln_high_count,
    a.vuln_medium_count,
    a.vuln_low_count,
    a.files_with_iac_misconfigs,
    a.total_iac_misconfig_count,
    a.iac_critical_count,
    a.iac_high_count,
    a.iac_medium_count,
    a.iac_low_count
from aggregated a
join dir_hierarchy dh
    on dh.run_pk = a.layout_run_pk
    and dh.directory_id = a.directory_id
