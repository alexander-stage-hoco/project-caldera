select
    run_pk,
    caller_file_id,
    caller_directory_id,
    caller_file_path,
    caller_symbol,
    callee_symbol,
    callee_file_id,
    callee_file_path,
    line_number,
    call_type
from {{ source('lz', 'lz_symbol_calls') }}
