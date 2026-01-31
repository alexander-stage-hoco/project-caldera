select
    run_pk,
    file_id,
    function_name,
    long_name,
    ccn,
    nloc,
    params,
    token_count,
    line_start,
    line_end
from {{ source('lz', 'lz_lizard_function_metrics') }}
