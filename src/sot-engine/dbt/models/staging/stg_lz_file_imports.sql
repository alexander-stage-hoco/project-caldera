select
    run_pk,
    file_id,
    directory_id,
    relative_path,
    imported_path,
    imported_symbols,
    import_type,
    line_number
from {{ source('lz', 'lz_file_imports') }}
