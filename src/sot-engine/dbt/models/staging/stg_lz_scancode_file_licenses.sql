select
    run_pk,
    file_id,
    directory_id,
    relative_path,
    spdx_id,
    category,
    confidence,
    match_type,
    line_number
from {{ source('lz', 'lz_scancode_file_licenses') }}
