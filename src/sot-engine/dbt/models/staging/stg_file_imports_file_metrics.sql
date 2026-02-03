-- Aggregates stg_lz_file_imports to file-level metrics
with imports as (
    select run_pk, file_id, directory_id, relative_path, imported_path, import_type
    from {{ ref('stg_lz_file_imports') }}
),
file_metrics as (
    select
        run_pk,
        file_id,
        directory_id,
        min(relative_path) as relative_path,
        count(*) as import_count,
        count(distinct imported_path) as unique_imports,
        count(case when import_type = 'static' then 1 end) as static_import_count,
        count(case when import_type = 'dynamic' then 1 end) as dynamic_import_count,
        count(case when import_type = 'side_effect' then 1 end) as side_effect_import_count
    from imports
    group by run_pk, file_id, directory_id
)
select * from file_metrics
