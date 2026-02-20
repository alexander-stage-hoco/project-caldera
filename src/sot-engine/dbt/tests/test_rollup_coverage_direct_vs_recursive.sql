-- Validates that recursive counts >= direct counts for each directory
-- This invariant must hold: a directory's recursive count includes all
-- files in its subtree, while direct only counts files directly in that directory.

select
    r.run_pk,
    r.directory_id,
    r.total_lines_covered as recursive_lines_covered,
    d.total_lines_covered as direct_lines_covered,
    r.file_count as recursive_file_count,
    d.file_count as direct_file_count
from {{ ref('rollup_coverage_directory_counts_recursive') }} r
join {{ ref('rollup_coverage_directory_counts_direct') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
where r.total_lines_covered < d.total_lines_covered
   or r.file_count < d.file_count
   or r.total_lines_total < d.total_lines_total
