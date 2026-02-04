select
    run_pk,
    clone_id,
    lines,
    tokens,
    occurrence_count,
    is_cross_file,
    code_fragment
from {{ source('lz', 'lz_pmd_cpd_duplications') }}
