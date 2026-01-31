-- git-sizer provides repository-level metrics only (no file-level rollups needed)
-- This test validates the metrics table has expected structure and valid health grades
-- Returns rows only if invalid health grades exist (should be empty = pass)

select
    run_pk,
    repo_id,
    health_grade
from {{ ref('stg_lz_git_sizer_metrics') }}
where health_grade not in ('A', 'A+', 'B', 'B+', 'C', 'C+', 'D', 'D+', 'F')
