select
    run_pk,
    clone_id,
    file_id,
    directory_id,
    relative_path,
    line_start,
    line_end,
    column_start,
    column_end
from {{ source('lz', 'lz_pmd_cpd_occurrences') }}
