select
    run_pk,
    assembly_name,
    type_name,
    method_name,
    covered_statements,
    total_statements,
    statement_coverage_pct
from {{ source('lz', 'lz_dotcover_method_coverage') }}
