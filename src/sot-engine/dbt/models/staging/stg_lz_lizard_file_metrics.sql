select
    run_pk,
    file_id,
    relative_path,
    language,
    nloc,
    function_count,
    total_ccn,
    avg_ccn,
    max_ccn
from {{ source('lz', 'lz_lizard_file_metrics') }}
