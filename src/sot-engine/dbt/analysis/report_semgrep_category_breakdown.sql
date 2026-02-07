{% set run_pk = var('run_pk') %}
{% set limit_dirs = var('limit', 5) %}

-- Semgrep category breakdown with directory-level hotspots
-- Shows smells by category (error_handling, resource_management, dependency, security,
-- dead_code, refactoring, api_design, async_patterns, nullability)
-- with top directories per category and severity breakdown

with run_summary as (
    select run_pk, collection_run_id
    from {{ ref('unified_run_summary') }}
    where run_pk = {{ run_pk }}
),
tool_runs as (
    select run_pk, collection_run_id, tool_name
    from {{ source('lz', 'lz_tool_runs') }}
),
tool_map as (
    select
        rs.collection_run_id,
        max(case when tr.tool_name = 'semgrep' then tr.run_pk end) as semgrep_run_pk,
        max(case when tr.tool_name in ('layout', 'layout-scanner') then tr.run_pk end) as layout_run_pk
    from run_summary rs
    left join tool_runs tr
        on tr.collection_run_id = rs.collection_run_id
    group by rs.collection_run_id
),
smells as (
    select
        dd_category,
        directory_id,
        severity,
        count(*) as smell_count
    from {{ ref('stg_lz_semgrep_smells') }}
    where run_pk = (select semgrep_run_pk from tool_map)
    group by dd_category, directory_id, severity
),
-- Category totals (repo-wide)
category_totals as (
    select
        dd_category,
        sum(smell_count) as total_count,
        count(distinct directory_id) as dir_count_with_smells
    from smells
    group by dd_category
),
-- File counts per category
file_counts as (
    select
        dd_category,
        count(distinct file_id) as file_count
    from {{ ref('stg_lz_semgrep_smells') }}
    where run_pk = (select semgrep_run_pk from tool_map)
    group by dd_category
),
-- Directory aggregations per category
dir_category_agg as (
    select
        s.dd_category,
        s.directory_id,
        sum(s.smell_count) as dir_total,
        sum(case when s.severity = 'critical' then s.smell_count else 0 end) as sev_critical,
        sum(case when s.severity = 'high' then s.smell_count else 0 end) as sev_high,
        sum(case when s.severity = 'medium' then s.smell_count else 0 end) as sev_medium,
        sum(case when s.severity = 'low' then s.smell_count else 0 end) as sev_low,
        sum(case when s.severity = 'info' then s.smell_count else 0 end) as sev_info
    from smells s
    group by s.dd_category, s.directory_id
),
-- Get directory paths from layout
layout_dirs as (
    select
        directory_id,
        relative_path as directory_path
    from {{ source('lz', 'lz_layout_directories') }}
    where run_pk = (select layout_run_pk from tool_map)
),
-- Rank directories within each category
dir_ranked as (
    select
        dca.dd_category,
        dca.directory_id,
        ld.directory_path,
        dca.dir_total,
        dca.sev_critical,
        dca.sev_high,
        dca.sev_medium,
        dca.sev_low,
        dca.sev_info,
        ct.total_count as category_total,
        fc.file_count,
        round(100.0 * dca.dir_total / ct.total_count, 1) as dir_pct,
        row_number() over (
            partition by dca.dd_category
            order by dca.dir_total desc, ld.directory_path
        ) as rank_in_category
    from dir_category_agg dca
    join category_totals ct on ct.dd_category = dca.dd_category
    join file_counts fc on fc.dd_category = dca.dd_category
    left join layout_dirs ld on ld.directory_id = dca.directory_id
)
select
    dd_category as category,
    category_total as total_count,
    file_count,
    directory_path,
    dir_total as dir_count,
    dir_pct,
    sev_critical,
    sev_high,
    sev_medium,
    sev_low,
    sev_info,
    rank_in_category
from dir_ranked
where rank_in_category <= {{ limit_dirs }}
order by category_total desc, dd_category, rank_in_category
