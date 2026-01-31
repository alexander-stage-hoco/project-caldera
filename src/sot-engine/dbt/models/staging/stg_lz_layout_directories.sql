select
    run_pk,
    directory_id,
    relative_path,
    parent_id,
    depth,
    file_count,
    total_size_bytes
from {{ source('lz', 'lz_layout_directories') }}
