-- Aggregates lz_sonarqube_issues to file-level metrics
-- Produces one row per file with issue counts by type and severity

with issues as (
    select
        run_pk,
        file_id,
        directory_id,
        relative_path,
        issue_type,
        severity
    from {{ source('lz', 'lz_sonarqube_issues') }}
),
metrics as (
    select
        run_pk,
        file_id,
        directory_id,
        relative_path,
        ncloc,
        complexity,
        cognitive_complexity,
        duplicated_lines,
        duplicated_lines_density,
        code_smells,
        bugs,
        vulnerabilities
    from {{ source('lz', 'lz_sonarqube_metrics') }}
),
issue_counts as (
    select
        run_pk,
        file_id,
        directory_id,
        min(relative_path) as relative_path,
        count(*) as issue_count,
        -- Type counts
        count(case when issue_type = 'BUG' then 1 end) as type_bug,
        count(case when issue_type = 'VULNERABILITY' then 1 end) as type_vulnerability,
        count(case when issue_type = 'CODE_SMELL' then 1 end) as type_code_smell,
        count(case when issue_type = 'SECURITY_HOTSPOT' then 1 end) as type_security_hotspot,
        -- Severity counts
        count(case when severity = 'BLOCKER' then 1 end) as severity_blocker,
        count(case when severity = 'CRITICAL' then 1 end) as severity_critical,
        count(case when severity = 'MAJOR' then 1 end) as severity_major,
        count(case when severity = 'MINOR' then 1 end) as severity_minor,
        count(case when severity = 'INFO' then 1 end) as severity_info,
        -- Severity aggregates
        count(case when severity in ('BLOCKER', 'CRITICAL') then 1 end) as severity_high_plus
    from issues
    group by run_pk, file_id, directory_id
),
combined as (
    select
        coalesce(ic.run_pk, m.run_pk) as run_pk,
        coalesce(ic.file_id, m.file_id) as file_id,
        coalesce(ic.directory_id, m.directory_id) as directory_id,
        coalesce(ic.relative_path, m.relative_path) as relative_path,
        coalesce(ic.issue_count, 0) as issue_count,
        coalesce(ic.type_bug, 0) as type_bug,
        coalesce(ic.type_vulnerability, 0) as type_vulnerability,
        coalesce(ic.type_code_smell, 0) as type_code_smell,
        coalesce(ic.type_security_hotspot, 0) as type_security_hotspot,
        coalesce(ic.severity_blocker, 0) as severity_blocker,
        coalesce(ic.severity_critical, 0) as severity_critical,
        coalesce(ic.severity_major, 0) as severity_major,
        coalesce(ic.severity_minor, 0) as severity_minor,
        coalesce(ic.severity_info, 0) as severity_info,
        coalesce(ic.severity_high_plus, 0) as severity_high_plus,
        m.ncloc,
        m.complexity,
        m.cognitive_complexity,
        m.duplicated_lines,
        m.duplicated_lines_density,
        m.code_smells as sonar_code_smells,
        m.bugs as sonar_bugs,
        m.vulnerabilities as sonar_vulnerabilities
    from issue_counts ic
    full outer join metrics m
        on m.run_pk = ic.run_pk
       and m.file_id = ic.file_id
)
select * from combined
