-- File-level aggregation of trivy findings (vulnerabilities + IaC misconfigs)
with targets as (
    select
        run_pk,
        file_id,
        directory_id,
        relative_path,
        vulnerability_count,
        critical_count as vuln_critical,
        high_count as vuln_high,
        medium_count as vuln_medium,
        low_count as vuln_low
    from {{ ref('stg_trivy_targets') }}
),
iac_misconfigs as (
    select
        run_pk,
        file_id,
        directory_id,
        relative_path,
        count(*) as iac_misconfig_count,
        count(case when severity = 'CRITICAL' then 1 end) as iac_critical,
        count(case when severity = 'HIGH' then 1 end) as iac_high,
        count(case when severity = 'MEDIUM' then 1 end) as iac_medium,
        count(case when severity = 'LOW' then 1 end) as iac_low
    from {{ ref('stg_trivy_iac_misconfigs') }}
    group by run_pk, file_id, directory_id, relative_path
),
combined as (
    select
        coalesce(t.run_pk, i.run_pk) as run_pk,
        coalesce(t.file_id, i.file_id) as file_id,
        coalesce(t.directory_id, i.directory_id) as directory_id,
        coalesce(t.relative_path, i.relative_path) as relative_path,
        coalesce(t.vulnerability_count, 0) as vulnerability_count,
        coalesce(t.vuln_critical, 0) as vuln_critical,
        coalesce(t.vuln_high, 0) as vuln_high,
        coalesce(t.vuln_medium, 0) as vuln_medium,
        coalesce(t.vuln_low, 0) as vuln_low,
        coalesce(i.iac_misconfig_count, 0) as iac_misconfig_count,
        coalesce(i.iac_critical, 0) as iac_critical,
        coalesce(i.iac_high, 0) as iac_high,
        coalesce(i.iac_medium, 0) as iac_medium,
        coalesce(i.iac_low, 0) as iac_low
    from targets t
    full outer join iac_misconfigs i
        on t.run_pk = i.run_pk
        and t.file_id = i.file_id
)
select
    run_pk,
    file_id,
    directory_id,
    relative_path,
    vulnerability_count,
    vuln_critical,
    vuln_high,
    vuln_medium,
    vuln_low,
    iac_misconfig_count,
    iac_critical,
    iac_high,
    iac_medium,
    iac_low,
    vulnerability_count + iac_misconfig_count as total_finding_count,
    vuln_critical + iac_critical as total_critical,
    vuln_high + iac_high as total_high,
    vuln_medium + iac_medium as total_medium,
    vuln_low + iac_low as total_low,
    (vuln_critical + iac_critical) + (vuln_high + iac_high) as severity_high_plus
from combined
