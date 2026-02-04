select
    run_pk,
    file_id,
    directory_id,
    relative_path,
    language,
    total_lines,
    duplicate_lines,
    duplicate_blocks,
    duplication_percentage
from {{ source('lz', 'lz_pmd_cpd_file_metrics') }}
