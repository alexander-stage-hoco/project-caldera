-- Aggregates lz_devskim_findings to file-level metrics
-- Produces one row per file with issue counts by severity and category

with findings as (
    select
        run_pk,
        file_id,
        directory_id,
        relative_path,
        severity,
        dd_category
    from {{ ref('stg_lz_devskim_findings') }}
),
file_metrics as (
    select
        run_pk,
        file_id,
        directory_id,
        min(relative_path) as relative_path,
        count(*) as issue_count,
        -- Severity counts
        count(case when severity = 'CRITICAL' then 1 end) as severity_critical,
        count(case when severity = 'HIGH' then 1 end) as severity_high,
        count(case when severity = 'MEDIUM' then 1 end) as severity_medium,
        count(case when severity = 'LOW' then 1 end) as severity_low,
        -- Severity aggregates for distribution analysis
        count(case when severity in ('CRITICAL', 'HIGH') then 1 end) as severity_high_plus,
        -- Security category counts (DevSkim specific categories)
        count(case when dd_category = 'sql_injection' then 1 end) as cat_sql_injection,
        count(case when dd_category = 'hardcoded_secret' then 1 end) as cat_hardcoded_secret,
        count(case when dd_category = 'insecure_crypto' then 1 end) as cat_insecure_crypto,
        count(case when dd_category = 'xss' then 1 end) as cat_xss,
        count(case when dd_category = 'command_injection' then 1 end) as cat_command_injection,
        count(case when dd_category = 'path_traversal' then 1 end) as cat_path_traversal,
        count(case when dd_category = 'insecure_deserialization' then 1 end) as cat_insecure_deserialization,
        count(case when dd_category = 'insecure_ssl_tls' then 1 end) as cat_insecure_ssl_tls,
        count(case when dd_category = 'insecure_random' then 1 end) as cat_insecure_random,
        count(case when dd_category = 'insecure_file_handling' then 1 end) as cat_insecure_file_handling,
        count(case when dd_category = 'information_disclosure' then 1 end) as cat_information_disclosure,
        count(case when dd_category = 'authentication' then 1 end) as cat_authentication,
        count(case when dd_category = 'authorization' then 1 end) as cat_authorization,
        count(case when dd_category = 'xml_injection' then 1 end) as cat_xml_injection,
        count(case when dd_category = 'other' then 1 end) as cat_other
    from findings
    group by run_pk, file_id, directory_id
)
select * from file_metrics
