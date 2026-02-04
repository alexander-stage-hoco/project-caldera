select
    run_pk,
    total_files_scanned,
    files_with_licenses,
    overall_risk,
    has_permissive,
    has_weak_copyleft,
    has_copyleft,
    has_unknown
from {{ source('lz', 'lz_scancode_summary') }}
