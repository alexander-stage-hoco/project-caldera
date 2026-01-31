-- Validates that recursive counts >= direct counts for each directory
-- This invariant must hold: a directory's recursive count includes all
-- files in its subtree, while direct only counts files directly in that directory.

select
    r.run_pk,
    r.directory_id,
    r.file_count as recursive_file_count,
    d.file_count as direct_file_count,
    r.total_nloc as recursive_total_nloc,
    d.total_nloc as direct_total_nloc,
    r.total_function_count as recursive_total_function_count,
    d.total_function_count as direct_total_function_count,
    r.total_ccn as recursive_total_ccn,
    d.total_ccn as direct_total_ccn
from {{ ref('rollup_lizard_directory_counts_recursive') }} r
join {{ ref('rollup_lizard_directory_counts_direct') }} d
    on d.run_pk = r.run_pk
    and d.directory_id = r.directory_id
where r.file_count < d.file_count
   or r.total_nloc < d.total_nloc
   or r.total_function_count < d.total_function_count
   or r.total_ccn < d.total_ccn
