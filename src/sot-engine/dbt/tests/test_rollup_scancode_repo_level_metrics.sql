-- scancode provides repository-level license summaries (no file-level rollups needed)
-- This test validates the summary table has valid data
-- Returns rows only if invalid data exists (should be empty = pass)

select
    run_pk,
    files_with_licenses,
    overall_risk
from {{ ref('stg_lz_scancode_summary') }}
where files_with_licenses < 0
   or overall_risk not in ('low', 'medium', 'high', 'critical', 'unknown')
