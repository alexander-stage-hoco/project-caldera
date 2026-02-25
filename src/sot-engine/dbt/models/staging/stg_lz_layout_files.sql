select
    run_pk,
    file_id,
    relative_path,
    directory_id,
    filename,
    extension,
    language,
    category,
    size_bytes,
    line_count,
    is_binary,
    stable_fingerprint,
    created_at
from {{ source('lz', 'lz_layout_files') }}
