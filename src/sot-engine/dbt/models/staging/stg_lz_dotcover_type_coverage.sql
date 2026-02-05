select
    run_pk,
    file_id,
    directory_id,
    relative_path,
    assembly_name,
    namespace,
    type_name,
    covered_statements,
    total_statements,
    statement_coverage_pct
from {{ source('lz', 'lz_dotcover_type_coverage') }}
