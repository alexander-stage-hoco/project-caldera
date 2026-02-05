-- Direct passthrough from lz_roslyn_violations
-- Individual violation records from Roslyn analyzers

select
    run_pk,
    file_id,
    directory_id,
    relative_path,
    rule_id,
    dd_category,
    severity,
    message,
    line_start,
    line_end,
    column_start,
    column_end,
    created_at
from {{ source('lz', 'lz_roslyn_violations') }}
