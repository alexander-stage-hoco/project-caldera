-- Aggregates lz_semgrep_smells to file-level metrics
-- Produces one row per file with smell counts by severity and category

with smells as (
    select
        run_pk,
        file_id,
        directory_id,
        relative_path,
        severity,
        dd_category
    from {{ ref('stg_lz_semgrep_smells') }}
),
file_metrics as (
    select
        run_pk,
        file_id,
        directory_id,
        min(relative_path) as relative_path,
        count(*) as smell_count,
        -- Severity counts
        count(case when severity = 'CRITICAL' then 1 end) as severity_critical,
        count(case when severity = 'HIGH' then 1 end) as severity_high,
        count(case when severity = 'MEDIUM' then 1 end) as severity_medium,
        count(case when severity = 'LOW' then 1 end) as severity_low,
        count(case when severity = 'INFO' then 1 end) as severity_info,
        -- Severity aggregates for distribution analysis
        count(case when severity in ('CRITICAL', 'HIGH') then 1 end) as severity_high_plus,
        -- Category counts
        count(case when dd_category = 'error_handling' then 1 end) as cat_error_handling,
        count(case when dd_category = 'resource_management' then 1 end) as cat_resource_management,
        count(case when dd_category = 'dependency' then 1 end) as cat_dependency,
        count(case when dd_category = 'security' then 1 end) as cat_security,
        count(case when dd_category = 'dead_code' then 1 end) as cat_dead_code,
        count(case when dd_category = 'refactoring' then 1 end) as cat_refactoring,
        count(case when dd_category = 'api_design' then 1 end) as cat_api_design,
        count(case when dd_category = 'async_patterns' then 1 end) as cat_async_patterns,
        count(case when dd_category = 'nullability' then 1 end) as cat_nullability
    from smells
    group by run_pk, file_id, directory_id
)
select * from file_metrics
