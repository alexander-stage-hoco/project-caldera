select
    run_pk,
    file_id,
    directory_id,
    relative_path,
    rule_id,
    dd_category,
    severity,
    line_start,
    line_end,
    column_start,
    column_end,
    message,
    code_snippet,
    created_at
from {{ source('lz', 'lz_devskim_findings') }}
