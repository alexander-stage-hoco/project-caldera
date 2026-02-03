-- Aggregates stg_lz_code_symbols to file-level metrics
with symbols as (
    select run_pk, file_id, directory_id, relative_path, symbol_type, is_exported, parameters
    from {{ ref('stg_lz_code_symbols') }}
),
file_metrics as (
    select
        run_pk,
        file_id,
        directory_id,
        min(relative_path) as relative_path,
        count(*) as symbol_count,
        count(case when symbol_type = 'function' then 1 end) as function_count,
        count(case when symbol_type = 'class' then 1 end) as class_count,
        count(case when symbol_type = 'method' then 1 end) as method_count,
        count(case when symbol_type = 'variable' then 1 end) as variable_count,
        count(case when is_exported then 1 end) as exported_count,
        coalesce(avg(parameters), 0) as avg_parameters
    from symbols
    group by run_pk, file_id, directory_id
)
select * from file_metrics
