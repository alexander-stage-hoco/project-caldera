-- Aggregates semgrep smell counts across all files in directory subtrees (recursive)

with recursive semgrep_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name = 'semgrep'
),
layout_runs as (
    select run_pk, collection_run_id
    from {{ source('lz', 'lz_tool_runs') }}
    where tool_name in ('layout', 'layout-scanner')
),
run_map as (
    select
        sr.run_pk as semgrep_run_pk,
        lr.run_pk as layout_run_pk,
        sr.collection_run_id
    from semgrep_runs sr
    join layout_runs lr
        on lr.collection_run_id = sr.collection_run_id
),
dir_tree as (
    -- Base case: each directory is its own ancestor
    select
        rm.semgrep_run_pk,
        rm.layout_run_pk,
        ld.directory_id as ancestor_id,
        ld.directory_id as descendant_id
    from {{ source('lz', 'lz_layout_directories') }} ld
    join run_map rm
        on rm.layout_run_pk = ld.run_pk

    union all

    -- Recursive case: parent inherits children
    select
        parent.semgrep_run_pk,
        parent.layout_run_pk,
        parent.ancestor_id,
        child.directory_id as descendant_id
    from dir_tree parent
    join {{ source('lz', 'lz_layout_directories') }} child
        on child.run_pk = parent.layout_run_pk
        and child.parent_id = parent.descendant_id
),
files_with_ancestor as (
    select
        dt.semgrep_run_pk,
        dt.layout_run_pk,
        lf.file_id,
        dt.ancestor_id as directory_id
    from {{ source('lz', 'lz_layout_files') }} lf
    join dir_tree dt
        on dt.layout_run_pk = lf.run_pk
        and dt.descendant_id = lf.directory_id
),
file_metrics as (
    select
        fa.semgrep_run_pk as run_pk,
        fa.layout_run_pk,
        fa.directory_id,
        m.smell_count,
        m.severity_critical,
        m.severity_high,
        m.severity_medium,
        m.severity_low,
        m.severity_info,
        m.severity_high_plus,
        m.cat_error_handling,
        m.cat_resource_management,
        m.cat_dependency,
        m.cat_security,
        m.cat_dead_code,
        m.cat_refactoring,
        m.cat_api_design,
        m.cat_async_patterns,
        m.cat_nullability
    from files_with_ancestor fa
    join {{ ref('stg_semgrep_file_metrics') }} m
        on m.run_pk = fa.semgrep_run_pk
        and m.file_id = fa.file_id
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
        count(case when smell_count > 0 then 1 end) as files_with_smells,
        sum(smell_count) as total_smell_count,
        -- Severity totals
        sum(severity_critical) as severity_critical,
        sum(severity_high) as severity_high,
        sum(severity_medium) as severity_medium,
        sum(severity_low) as severity_low,
        sum(severity_info) as severity_info,
        sum(severity_high_plus) as severity_high_plus,
        -- Category totals
        sum(cat_error_handling) as cat_error_handling,
        sum(cat_resource_management) as cat_resource_management,
        sum(cat_dependency) as cat_dependency,
        sum(cat_security) as cat_security,
        sum(cat_dead_code) as cat_dead_code,
        sum(cat_refactoring) as cat_refactoring,
        sum(cat_api_design) as cat_api_design,
        sum(cat_async_patterns) as cat_async_patterns,
        sum(cat_nullability) as cat_nullability
    from file_metrics
    group by run_pk, layout_run_pk, directory_id
)
select
    a.run_pk,
    a.directory_id,
    dp.relative_path as directory_path,
    a.file_count,
    a.files_with_smells,
    a.total_smell_count,
    a.severity_critical,
    a.severity_high,
    a.severity_medium,
    a.severity_low,
    a.severity_info,
    a.severity_high_plus,
    a.cat_error_handling,
    a.cat_resource_management,
    a.cat_dependency,
    a.cat_security,
    a.cat_dead_code,
    a.cat_refactoring,
    a.cat_api_design,
    a.cat_async_patterns,
    a.cat_nullability
from aggregated a
join directory_paths dp
    on dp.run_pk = a.layout_run_pk
    and dp.directory_id = a.directory_id
