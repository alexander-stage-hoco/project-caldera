-- Aggregates lz_roslyn_violations to file-level metrics
-- Produces one row per file with violation counts by severity and category

with violations as (
    select
        run_pk,
        file_id,
        directory_id,
        relative_path,
        severity,
        dd_category
    from {{ source('lz', 'lz_roslyn_violations') }}
),
file_metrics as (
    select
        run_pk,
        file_id,
        directory_id,
        min(relative_path) as relative_path,
        count(*) as violation_count,
        -- Severity counts
        count(case when severity = 'CRITICAL' then 1 end) as severity_critical,
        count(case when severity = 'HIGH' then 1 end) as severity_high,
        count(case when severity = 'MEDIUM' then 1 end) as severity_medium,
        count(case when severity = 'LOW' then 1 end) as severity_low,
        count(case when severity = 'INFO' then 1 end) as severity_info,
        -- Severity aggregates for distribution analysis
        count(case when severity in ('CRITICAL', 'HIGH') then 1 end) as severity_high_plus,
        -- Category counts (DD categories from roslyn)
        count(case when dd_category = 'security' then 1 end) as cat_security,
        count(case when dd_category = 'design' then 1 end) as cat_design,
        count(case when dd_category = 'resource' then 1 end) as cat_resource,
        count(case when dd_category = 'dead_code' then 1 end) as cat_dead_code,
        count(case when dd_category = 'performance' then 1 end) as cat_performance,
        count(case when dd_category not in ('security', 'design', 'resource', 'dead_code', 'performance') then 1 end) as cat_other
    from violations
    group by run_pk, file_id, directory_id
)
select * from file_metrics
