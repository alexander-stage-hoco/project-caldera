-- File-level aggregation of symbol coupling metrics
-- Aggregates fan-in, fan-out, and instability from symbol-level to file-level
-- Filters out external references (symbols with null file_id/directory_id)

with symbol_metrics as (
    select * from {{ ref('stg_symbol_coupling_metrics') }}
    where file_id is not null
      and directory_id is not null
),

file_aggregates as (
    select
        run_pk,
        file_id,
        directory_id,
        relative_path,
        count(*) as symbol_count,
        sum(fan_out) as total_fan_out,
        sum(fan_in) as total_fan_in,
        sum(total_coupling) as total_coupling,
        avg(instability) as avg_instability,
        max(instability) as max_instability
    from symbol_metrics
    group by run_pk, file_id, directory_id, relative_path
)

select * from file_aggregates
