-- Staging model for coverage-ingest landing zone data
-- Normalizes coverage data from LCOV, Cobertura, JaCoCo, Istanbul formats

select
    run_pk,
    file_id,
    directory_id,
    relative_path,
    line_coverage_pct,
    branch_coverage_pct,
    lines_total,
    lines_covered,
    lines_missed,
    branches_total,
    branches_covered,
    source_format
from {{ source('lz', 'lz_coverage_summary') }}
