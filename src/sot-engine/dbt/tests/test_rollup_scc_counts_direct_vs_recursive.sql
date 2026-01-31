-- Validates that recursive counts >= direct counts for each directory
-- This invariant must hold: a directory's recursive count includes all
-- files in its subtree, while direct only counts files directly in that directory.

select
    r.run_pk,
    r.directory_id,
    r.file_count as recursive_file_count,
    d.file_count as direct_file_count,
    r.total_lines as recursive_total_lines,
    d.total_lines as direct_total_lines,
    r.total_code_lines as recursive_total_code_lines,
    d.total_code_lines as direct_total_code_lines,
    r.total_complexity as recursive_total_complexity,
    d.total_complexity as direct_total_complexity
from {{ ref('rollup_scc_directory_counts_recursive') }} r
join {{ ref('rollup_scc_directory_counts_direct') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
where r.file_count < d.file_count
   or r.total_lines < d.total_lines
   or r.total_code_lines < d.total_code_lines
   or r.total_complexity < d.total_complexity
