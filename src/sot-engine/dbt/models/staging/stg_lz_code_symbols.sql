select
    run_pk,
    file_id,
    directory_id,
    relative_path,
    symbol_name,
    symbol_type,
    line_start,
    line_end,
    is_exported,
    parameters,
    parent_symbol,
    docstring
from {{ source('lz', 'lz_code_symbols') }}
