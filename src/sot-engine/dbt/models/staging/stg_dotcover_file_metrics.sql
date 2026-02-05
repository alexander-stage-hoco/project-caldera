-- Aggregates lz_dotcover_type_coverage to file-level metrics
-- Only includes types that have file mappings (file_id is not null)

with types as (
    select
        run_pk,
        file_id,
        directory_id,
        relative_path,
        covered_statements,
        total_statements
    from {{ ref('stg_lz_dotcover_type_coverage') }}
    where file_id is not null
),
file_metrics as (
    select
        run_pk,
        file_id,
        directory_id,
        min(relative_path) as relative_path,
        count(*) as type_count,
        sum(covered_statements) as covered_statements,
        sum(total_statements) as total_statements,
        case
            when sum(total_statements) > 0
            then round(100.0 * sum(covered_statements) / sum(total_statements), 2)
            else 0
        end as statement_coverage_pct
    from types
    group by run_pk, file_id, directory_id
)
select * from file_metrics
